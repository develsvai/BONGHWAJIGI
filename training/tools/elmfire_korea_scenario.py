#!/usr/bin/env python3
"""Fixed Korean-terrain ELMFIRE research scenarios, never personal-risk probabilities.

Requires a successful pinned synthetic probe, verified terrain, and seven verified
hourly point forecasts. Assumed ignition, fuel and moisture remain explicit.
No services, models, live user data, or system packages are changed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.warp import transform as reproject_points

SOURCE_SHA = "f4927b7ce68cb74eb0eb117085cc920782c8644e"
FUEL_SCENARIOS = (181, 183, 185)
TREE_CLASSES = (50, 60, 61, 62, 70, 71, 72, 80, 81, 82, 90, 151, 160, 170)
KNOWN_CLASSES = (
    10,
    11,
    12,
    20,
    30,
    40,
    50,
    60,
    61,
    62,
    70,
    71,
    72,
    80,
    81,
    82,
    90,
    100,
    110,
    120,
    121,
    122,
    130,
    140,
    150,
    151,
    152,
    153,
    160,
    170,
    180,
    190,
    200,
    201,
    202,
    210,
    220,
)
HORIZONS = {"1h": 3600, "3h": 10800, "6h": 21600}
FLAGS = {"simulation_only": True, "operational_use": False, "probability": None}
RASTERS = (
    "elevation_m.tif",
    "slope_deg.tif",
    "aspect_deg.tif",
    "landcover_class.tif",
    "forest_mask.tif",
    "water_mask.tif",
    "unknown_mask.tif",
    "flat_mask.tif",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp requires an explicit timezone")
    return parsed.astimezone(UTC)


def artifact_path(base: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def verify_file(base: Path, record: dict, key: str = "artifact_path") -> Path:
    path = artifact_path(base, record[key])
    if sha256(path) != record["sha256"]:
        raise ValueError(f"Artifact SHA256 mismatch: {path.name}")
    return path


def verify_weather(path: Path) -> dict:
    data = json.loads(path.read_text())
    source_contract = (data.get("schema_version"), data.get("source"))
    kma = source_contract == ("elmfire_kma_point_weather_v1", "KMA_APIHub_KIML")
    open_meteo = source_contract == ("elmfire_open_meteo_point_weather_v1", "OpenMeteo_GFS")
    if not kma and not open_meteo:
        raise ValueError("Unsupported weather source contract")
    required = {
        "wind_axis_basis_verified": True,
        "wind_direction_basis": "true_north_clockwise_from",
        "wind_height_m": 10,
        "wind_speed_unit": "m/s",
        "wind_direction_unit": "degree",
    }
    if any(data.get(key) != value for key, value in required.items()):
        raise ValueError("Unverified wind axis, height, units or weather schema")
    if data.get("wind_axis_basis_verified") is not True:
        raise ValueError("Wind axis verification must be boolean true")
    point = data["point"]
    if not np.allclose([point["longitude"], point["latitude"]], [129.3, 37.0], rtol=0, atol=1e-6):
        raise ValueError("Point forecast must match the fixed study center")
    start = timestamp(data["simulation_start_time_utc"])
    issue = None
    if kma:
        issue = timestamp(data["forecast_issue_time_utc"])
        if issue >= start:
            raise ValueError("Forecast issue must precede the assumed ignition")
    elif (
        data.get("forecast_issue_time_utc") is not None
        or data.get("forecast_issue_time_known") is not False
        or not data.get("issue_time_note")
    ):
        raise ValueError("Open-Meteo issue time must remain explicitly unknown, not retrieval time")
    provenance = data["provenance"]
    if not provenance:
        raise ValueError("Weather source artifacts are required")
    verified = set()
    for record in provenance:
        retrieved = timestamp(record["retrieved_at_utc"])
        if retrieved >= start or (issue is not None and retrieved < issue):
            raise ValueError("Every source lookup must follow issue and precede simulation start")
        if not record.get("role"):
            raise ValueError("Every weather source requires a role")
        verified.add(str(verify_file(path.parent, record)))
    evidence = data["axis_verification"]
    if not evidence.get("method") or str(verify_file(path.parent, evidence)) not in verified:
        raise ValueError("Axis evidence must be a timestamped verified provenance artifact")
    hours = data["hours"]
    if len(hours) != 7:
        raise ValueError("Seven hourly knots t0 through t6 are required")
    for index, hour in enumerate(hours):
        if timestamp(hour["valid_time_utc"]) != start + timedelta(hours=index):
            raise ValueError("Weather valid times must be ordered hourly t0 through t6")
        speed, direction = hour["wind_speed_m_s"], hour["wind_direction_deg"]
        if not np.isfinite([speed, direction]).all() or not (
            0 <= speed <= 100 and 0 <= direction <= 360
        ):
            raise ValueError("Nonfinite or out-of-range wind")
    if open_meteo:
        raw_records = [record for record in provenance if record["role"] == "open_meteo_response"]
        if len(raw_records) != 1:
            raise ValueError("Exactly one original Open-Meteo response is required")
        raw = json.loads(verify_file(path.parent, raw_records[0]).read_text())
        units = raw["hourly_units"]
        if (
            raw.get("utc_offset_seconds") != 0
            or units.get("time") != "iso8601"
            or units.get("wind_speed_10m") != "m/s"
            or units.get("wind_direction_10m") != "°"
        ):
            raise ValueError("Original Open-Meteo units or timezone disagree")
        hourly = raw["hourly"]
        raw_times = [
            timestamp(value if value.endswith("Z") or "+" in value else value + "Z")
            for value in hourly["time"]
        ]
        if (
            len(set(raw_times)) != len(raw_times)
            or len(hourly["wind_speed_10m"]) != len(raw_times)
            or len(hourly["wind_direction_10m"]) != len(raw_times)
        ):
            raise ValueError("Malformed original Open-Meteo hourly arrays")
        for hour in hours:
            try:
                index = raw_times.index(timestamp(hour["valid_time_utc"]))
            except ValueError as error:
                raise ValueError(
                    "Normalized weather time missing from original response"
                ) from error
            if not np.allclose(
                [hour["wind_speed_m_s"], hour["wind_direction_deg"]],
                [hourly["wind_speed_10m"][index], hourly["wind_direction_10m"][index]],
                rtol=0,
                atol=1e-6,
            ):
                raise ValueError("Normalized weather values differ from original response")
    return data


def verify_terrain(path: Path) -> tuple[dict, dict, dict]:
    manifest = json.loads(path.read_text())
    if (
        manifest.get("status") != "ready"
        or manifest.get("crs") != "EPSG:32652"
        or manifest.get("shape") != [100, 100]
        or manifest.get("pixel_size_m") != 100
        or manifest.get("aspect_reference") != "grid_north_clockwise_downslope"
    ):
        raise ValueError("Requires the fixed 100x100, 100m, grid-north Korean terrain")
    if not np.allclose(
        manifest["requested_center_longitude_latitude"], [129.3, 37.0], rtol=0, atol=1e-6
    ):
        raise ValueError("Terrain center differs from the predeclared study center")
    arrays, profile = {}, None
    expected = Affine(*manifest["transform"])
    if expected.a != 100 or expected.e != -100 or expected.b != 0 or expected.d != 0:
        raise ValueError("Terrain must use an unrotated north-up 100m grid")
    center_x, center_y = expected * (50, 50)
    lon, lat = reproject_points("EPSG:32652", "EPSG:4326", [center_x], [center_y])
    if not np.allclose([lon[0], lat[0]], [129.3, 37.0], rtol=0, atol=1e-6):
        raise ValueError("Actual terrain grid center differs from the fixed study center")
    for name in RASTERS:
        source = verify_file(path.parent, manifest["outputs"][name], "path")
        with rasterio.open(source) as raster:
            if (
                raster.count != 1
                or raster.shape != (100, 100)
                or raster.crs.to_epsg() != 32652
                or raster.transform != expected
            ):
                raise ValueError(f"Terrain grids disagree: {name}")
            values = raster.read(1, masked=True)
            if np.ma.getmaskarray(values).any() or not np.isfinite(values.data).all():
                raise ValueError(f"Unknown, masked or nonfinite terrain input: {name}")
            arrays[name] = values.data
            if profile is None:
                profile = raster.profile.copy()
    lc, forest, water = [
        arrays[name] for name in ("landcover_class.tif", "forest_mask.tif", "water_mask.tif")
    ]
    if arrays["unknown_mask.tif"].any() or not np.isin(lc, KNOWN_CLASSES).all():
        raise ValueError("Unknown landcover cannot be assigned a fuel or exclusion")
    if not np.array_equal(forest, np.isin(lc, TREE_CLASSES).astype("uint8")):
        raise ValueError("Forest mask must preserve the explicit CCI tree-class contract")
    if not np.array_equal(water, (lc == 210).astype("uint8")):
        raise ValueError("Water mask must explicitly identify CCI210")
    for name, lower, upper in (("slope_deg.tif", 0, 90), ("aspect_deg.tif", 0, 360)):
        if np.any((arrays[name] < lower) | (arrays[name] > upper)):
            raise ValueError(f"Out-of-range terrain angles: {name}")
    if not np.isin(arrays["flat_mask.tif"], [0, 1]).all():
        raise ValueError("Invalid flat-terrain mask")
    if np.any(np.abs(arrays["elevation_m.tif"]) > 32000):
        raise ValueError("Elevation cannot be represented safely in Int16 landscape")
    return manifest, arrays, profile


def verify_source(path: Path) -> tuple[dict, Path]:
    receipt = json.loads(path.read_text())
    if (
        receipt.get("status") != "synthetic_probe_passed"
        or receipt.get("source_commit") != SOURCE_SHA
        or receipt.get("simulation_only") is not True
        or receipt.get("operational_use") is not False
    ):
        raise ValueError("Requires the successful pinned research-only synthetic probe")
    binary = Path(receipt["binary_path"]).resolve()
    if sha256(binary) != receipt["binary_sha256"]:
        raise ValueError("ELMFIRE binary differs from its successful probe")
    licenses = receipt["license_sha256"]
    if set(licenses) != {"LICENSE.md", "COMMERCIAL_LICENSE.md"}:
        raise ValueError("Both pinned license receipts are required")
    for name, expected in licenses.items():
        if sha256(path.parent / name) != expected:
            raise ValueError(f"License receipt changed: {name}")
    inputs = path.parent / "tutorials/01-constant-wind/inputs"
    for name, expected in receipt["input_sha256"].items():
        if sha256(inputs / name) != expected:
            raise ValueError(f"Original successful probe input changed: {name}")
    return receipt, binary


def grid_rotation(profile: dict) -> np.ndarray:
    """True-north bearing in grid coordinates (minus meridian convergence)."""
    rows, columns = np.indices((profile["height"], profile["width"]))
    affine = profile["transform"]
    xs, ys = affine * (columns + 0.5, rows + 0.5)
    lon, lat = reproject_points(profile["crs"], "EPSG:4326", xs.ravel(), ys.ravel())
    north_x, north_y = reproject_points(
        "EPSG:4326", profile["crs"], lon, [value + 0.0001 for value in lat]
    )
    angle = np.degrees(
        np.arctan2(np.asarray(north_x) - xs.ravel(), np.asarray(north_y) - ys.ravel())
    )
    if not np.isfinite(angle).all() or np.max(np.abs(angle)) > 5:
        raise ValueError("Unexpected true-to-grid wind rotation in Korean UTM zone52")
    return angle.reshape(xs.shape).astype("float32")


def select_probes(arrays: dict, profile: dict) -> list[dict]:
    forest = arrays["forest_mask.tif"] == 1
    rows, columns = np.indices(forest.shape)
    # Distance to geometric domain center; stable row-major tie-breaking.
    distance2 = ((rows + 0.5 - 50) * 100) ** 2 + ((columns + 0.5 - 50) * 100) ** 2
    candidates = forest & (distance2 <= 500**2)
    if not candidates.any():
        raise ValueError("No explicit forest ignition cell within the fixed 500m center radius")
    ignition = np.unravel_index(np.where(candidates, distance2, np.inf).argmin(), forest.shape)
    offsets = (
        ("assumed_ignition", 0, 0),
        ("north_1000m", -10, 0),
        ("east_1000m", 0, 10),
        ("south_1000m", 10, 0),
        ("west_1000m", 0, -10),
    )
    probes = []
    for name, dr, dc in offsets:
        row, column = int(ignition[0] + dr), int(ignition[1] + dc)
        x, y = profile["transform"] * (column + 0.5, row + 0.5)
        lon, lat = reproject_points(profile["crs"], "EPSG:4326", [x], [y])
        eligibility = (
            "included_forest"
            if forest[row, column]
            else "excluded_water"
            if arrays["water_mask.tif"][row, column]
            else "excluded_nonforest"
        )
        probes.append(
            {
                "id": name,
                "row": row,
                "column": column,
                "xy_m": [x, y],
                "longitude_latitude": [lon[0], lat[0]],
                "eligibility": eligibility,
                "actual_user_location": False,
            }
        )
    return probes


def landscape(arrays: dict, fuel: int) -> np.ndarray:
    if fuel not in FUEL_SCENARIOS:
        raise ValueError("Fuel scenario was not predeclared")
    result = np.zeros((8, *arrays["forest_mask.tif"].shape), dtype="int16")
    result[0] = np.rint(arrays["elevation_m.tif"]).astype("int16")
    result[1] = np.rint(arrays["slope_deg.tif"]).astype("int16")
    result[2] = np.rint(arrays["aspect_deg.tif"]).astype("int16") % 360
    result[3] = np.where(
        arrays["forest_mask.tif"] == 1, fuel, np.where(arrays["water_mask.tif"] == 1, 98, 99)
    )
    return result


def save_raster(
    path: Path,
    data: np.ndarray,
    profile: dict,
    descriptions: list[str] | None = None,
    *,
    nodata: int | float | None = None,
) -> None:
    if data.ndim == 2:
        data = data[None]
    settings = profile | {
        "driver": "GTiff",
        "count": data.shape[0],
        "dtype": data.dtype.name,
        "nodata": nodata,
        "compress": "deflate",
    }
    with rasterio.open(path, "w", **settings) as output:
        output.write(data)
        if descriptions:
            for index, description in enumerate(descriptions, 1):
                output.set_band_description(index, description)


def namelist(ignition: dict) -> str:
    return f"""&INPUTS
FUELS_AND_TOPOGRAPHY_DIRECTORY = './inputs'
LANDSCAPE_FILENAME = 'landscape'
ADJ_FILENAME = 'adj'
PHI_FILENAME = 'phi'
WEATHER_DIRECTORY = './inputs'
WS_FILENAME = 'ws'
WD_FILENAME = 'wd'
M1_FILENAME = 'm1'
M10_FILENAME = 'm10'
M100_FILENAME = 'm100'
DT_METEOROLOGY = 3600.0
WS_AT_10M = .TRUE.
WS_IN_KPH = .TRUE.
DEAD_MC_IN_PERCENT = .TRUE.
LIVE_MC_IN_PERCENT = .TRUE.
USE_CONSTANT_LH = .TRUE.
USE_CONSTANT_LW = .TRUE.
USE_CONSTANT_FMC = .TRUE.
LH_MOISTURE_CONTENT = 60.0
LW_MOISTURE_CONTENT = 90.0
FOLIAR_MOISTURE_CONTENT = 90.0
CC_IN_PERCENT = .TRUE.
CH_TIMES_10 = .TRUE.
CBH_TIMES_10 = .TRUE.
CBD_TIMES_100 = .TRUE.
GRID_DECLINATION = 0.0
ROTATE_ASP = .FALSE.
ROTATE_WD = .FALSE.
SURFACE_SPREAD_MODEL = 'ROTHERMEL'
/
&OUTPUTS
OUTPUTS_DIRECTORY = './outputs'
DTDUMP = 3600.0
DUMP_TIME_OF_ARRIVAL = .TRUE.
CONVERT_TO_GEOTIFF = .FALSE.
/
&TIME_CONTROL
SIMULATION_DT = 5.0
SIMULATION_TSTART = 0.0
SIMULATION_TSTOP = 21600.0
TARGET_CFL = 0.2
/
&MONTE_CARLO
NUM_METEOROLOGY_TIMES = 7
/
&SIMULATOR
NUM_IGNITIONS = 1
X_IGN(1) = {ignition["xy_m"][0]:.8f}
Y_IGN(1) = {ignition["xy_m"][1]:.8f}
T_IGN(1) = 0.0
CROWN_FIRE_MODEL = 0
FEEDBACK_LEVEL = 3
WX_BILINEAR_INTERPOLATION = .TRUE.
/
&SPOTTING
ENABLE_SPOTTING = .FALSE.
ENABLE_SURFACE_FIRE_SPOTTING = .FALSE.
/
&SUPPRESSION
ENABLE_INITIAL_ATTACK = .FALSE.
ENABLE_EXTENDED_ATTACK = .FALSE.
/
&MISCELLANEOUS
PATH_TO_GDAL = 'auto'
SCRATCH = './scratch'
/
"""


def prepare_case(
    case: Path,
    arrays: dict,
    profile: dict,
    weather: dict,
    fuel: int,
    rotation: np.ndarray,
    probes: list[dict],
) -> dict:
    inputs = case / "inputs"
    inputs.mkdir(parents=True)
    (case / "scratch").mkdir()
    (case / "outputs").mkdir()
    save_raster(
        inputs / "landscape.tif",
        landscape(arrays, fuel),
        profile,
        [
            "elevation_m",
            "slope_degree",
            "aspect_grid_downhill_degree",
            "fuel_model",
            "canopy_cover_percent_assumed_zero",
            "canopy_height_m_x10_assumed_zero",
            "canopy_base_height_m_x10_assumed_zero",
            "canopy_bulk_density_kg_m3_x100_assumed_zero",
        ],
        nodata=-9999,
    )
    ones = np.ones((profile["height"], profile["width"]), dtype="float32")
    for name in ("adj", "phi"):
        save_raster(inputs / f"{name}.tif", ones, profile, nodata=-9999)
    descriptions = [hour["valid_time_utc"] for hour in weather["hours"]]
    ws = np.stack([ones * hour["wind_speed_m_s"] * 3.6 for hour in weather["hours"]])
    wd = np.stack([(rotation + hour["wind_direction_deg"]) % 360 for hour in weather["hours"]])
    save_raster(inputs / "ws.tif", ws.astype("float32"), profile, descriptions, nodata=-9999)
    save_raster(inputs / "wd.tif", wd.astype("float32"), profile, descriptions, nodata=-9999)
    for name, value in (("m1", 6), ("m10", 7), ("m100", 8)):
        save_raster(
            inputs / f"{name}.tif",
            np.stack([ones * value] * 7),
            profile,
            descriptions,
            nodata=-9999,
        )
    (inputs / "elmfire.data").write_text(namelist(probes[0]))
    return {path.name: sha256(path) for path in sorted(inputs.iterdir())}


def run_command(command: list[str], case: Path, env: dict, timeout: int) -> None:
    with (case / "run.log").open("a") as log:
        log.write(json.dumps({"argv": command}) + "\n")
        log.flush()
        process = subprocess.Popen(
            command, cwd=case, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
        )
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise
    if code:
        raise RuntimeError(f"Command exited {code}; inspect {case.name}/run.log")


def inspect_arrival(path: Path, arrays: dict, profile: dict, probes: list[dict]) -> dict:
    with rasterio.open(path) as source:
        if source.nodata is None or not np.isfinite(source.nodata) or source.nodata >= 0:
            raise ValueError("Arrival nodata must be negative and distinct from valid initial zero")
        nodata = source.nodata
        actual, expected = source.transform, profile["transform"]
        if (
            source.count != 1
            or source.shape != (profile["height"], profile["width"])
            or source.crs != profile["crs"]
            or (actual.a, actual.b, actual.d, actual.e)
            != (expected.a, expected.b, expected.d, expected.e)
            or not np.allclose([actual.c, actual.f], [expected.c, expected.f], rtol=0, atol=0.3)
        ):
            raise ValueError("Arrival raster grid differs from its input")
        data = source.read(1, masked=True)
        output_transform = list(source.transform)[:6]
        raw = data.filled(np.nan)
        valid = ~np.ma.getmaskarray(data)
    if np.any(valid & ~np.isfinite(raw)):
        raise ValueError("Nonfinite unmasked arrival output")
    reached = valid & (raw >= 0)
    if not reached.any() or np.any(raw[reached] > 21600.1):
        raise ValueError("Empty or out-of-horizon arrival output")
    if np.any(reached & (arrays["forest_mask.tif"] != 1)):
        raise ValueError("Engine reached an explicitly excluded input cell")
    ignition = probes[0]
    if (
        not reached[ignition["row"], ignition["column"]]
        or raw[ignition["row"], ignition["column"]] != 0
    ):
        raise ValueError("Assumed ignition center must have an initial arrival of zero")
    observations = []
    for point in probes:
        row, column = point["row"], point["column"]
        value = float(raw[row, column]) if reached[row, column] else None
        state = (
            point["eligibility"]
            if point["eligibility"] != "included_forest"
            else "unreached_within_horizon"
            if value is None
            else "initially_reached"
            if value == 0
            else "future_arrival"
        )
        observations.append(point | {"arrival_seconds": value, "state": state})
    edge = np.zeros(reached.shape, dtype=bool)
    edge[[0, -1], :] = True
    edge[:, [0, -1]] = True
    return {
        "probes": observations,
        "arrival_path": str(path),
        "arrival_sha256": sha256(path),
        "arrival_unit": "seconds_since_assumed_ignition",
        "arrival_nodata": nodata,
        "output_transform": output_transform,
        "coordinate_rounding_note": (
            "Pinned engine uses single-precision map coordinates and F12.2 headers; "
            "up to 0.3m origin roundoff is accepted, without shifting cell indices"
        ),
        "reached_cells": int(reached.sum()),
        "initial_cells": int((reached & (raw == 0)).sum()),
        "reached_boundary_cells": int((reached & edge).sum()),
        "boundary_note": "Extent-censored study; outside-domain arrival is not evaluated",
        "future_reached_area_ha": {
            key: int((reached & (raw > 0) & (raw <= value)).sum())
            for key, value in HORIZONS.items()
        },
        "maximum_arrival_seconds": float(raw[reached].max()),
    }


def inspect_coverage(case: Path) -> dict:
    """Final output time can be fast-forwarded after solver exit; audit actual stop."""
    stats_path = case / "outputs/fire_size_stats.csv"
    with stats_path.open(newline="") as stream:
        rows = [
            {key.strip(): value.strip() for key, value in row.items()}
            for row in csv.DictReader(stream)
        ]
    if len(rows) != 1 or int(rows[0]["Meteorology band"]) != 1:
        raise ValueError("Expected one ignition case starting at weather band1")
    stats_stop = float(rows[0]["tstop (h)"]) * 3600
    if not np.isfinite(stats_stop) or not 0 <= stats_stop <= 21636:
        raise ValueError("Invalid solver stop time in fire_size_stats")
    log = (case / "run.log").read_text(errors="replace")
    stop = re.search(r"STOPPING:[^\r\n]*", log)
    early = stats_stop < 21600 or stop is not None
    lower = min(stats_stop, 21600)
    method = "stats confirms full planned horizon without early-stop message"
    stop_step = None
    if early:
        # CSV tstop is F8.2 hours: its rounding interval has half-width18s.
        lower = max(0, min(stats_stop - 18, 21600))
        method = "conservative lower bound from tstop CSV rounded to0.01h"
        if stop is not None:
            steps = re.findall(r"Current Timestep:\s*([0-9.]+)\s+of", log[: stop.start()])
            if steps:
                stop_step = float(steps[-1])
                if not np.isfinite(stop_step) or abs(stop_step - stats_stop) > 18.1:
                    raise ValueError("Logged solver stop step disagrees with tstop CSV")
                # Progress log is F0.1 seconds. Do not claim more temporal precision.
                lower = max(0, min(stop_step - 0.05, 21600))
                method = "last solver step before STOPPING;0.1s log lower bound"
    return {
        "full_horizon_completed": not early,
        "early_stop_detected": early,
        "early_stop_reason": stop.group(0).strip()
        if stop
        else "earlier_tstop_in_stats_without_logged_reason"
        if early
        else None,
        "stats_tstop_seconds_rounded": stats_stop,
        "logged_stop_step_seconds_rounded": stop_step,
        "covered_until_seconds_lower_bound": lower,
        "coverage_time_method": method,
        "horizon_completed": {key: lower >= seconds for key, seconds in HORIZONS.items()},
        "stats_sha256": sha256(stats_path),
        "run_log_sha256": sha256(case / "run.log"),
        "note": (
            "Early solver termination does not evaluate later weather or establish no later spread"
        ),
    }


def aggregate(cases: list[dict], probes: list[dict], *, integrity_ok: bool = True) -> list[dict]:
    successful = [case for case in cases if case["status"] in {"complete", "censored"}]
    complete = (
        len(cases) == len(FUEL_SCENARIOS)
        and len(successful) == len(FUEL_SCENARIOS)
        and {case["fuel_model"] for case in cases} == set(FUEL_SCENARIOS)
    )
    results = []
    for point in probes:
        observed = [
            next(p for p in case["probes"] if p["id"] == point["id"]) for case in successful
        ]
        initial = sum(p["state"] == "initially_reached" for p in observed)
        reason = (
            "study_integrity_failure"
            if not integrity_ok
            else point["eligibility"]
            if point["eligibility"] != "included_forest"
            else "partial_or_failed_ensemble"
            if not complete
            else "initial_exposure_not_future_arrival"
            if initial
            else None
        )
        counts = {
            key: sum(
                p["state"] == "future_arrival" and 0 < p["arrival_seconds"] <= horizon
                for p in observed
            )
            for key, horizon in HORIZONS.items()
        }
        unavailable = {
            key: reason
            if reason is not None
            else "solver_stopped_before_horizon"
            if not all(
                case.get("coverage", {}).get("horizon_completed", {}).get(key, False)
                for case in successful
            )
            else None
            for key in HORIZONS
        }
        results.append(
            point
            | FLAGS
            | {
                "completed_scenarios": len(successful),
                "planned_scenarios": 3,
                "initially_reached_scenarios": initial,
                "future_arrival_counts": counts,
                "scenario_fraction": {
                    key: count / 3 if unavailable[key] is None else None
                    for key, count in counts.items()
                },
                "horizon_unavailable_reason": unavailable,
                "unavailable_reason": reason,
            }
        )
    return results


def geojson(probes: list[dict]) -> dict:
    return {
        "type": "FeatureCollection",
        **FLAGS,
        "interpretation": "Fixed assumed-fuel scenario sensitivity; not calibrated risk",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": point["longitude_latitude"]},
                "properties": point,
            }
            for point in probes
        ],
    }


def execute(
    probe_path: Path,
    terrain_path: Path,
    weather_path: Path,
    output: Path,
    timeout: int,
    prepare_only: bool = False,
) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    report = FLAGS | {"status": "preflight", "cases": [], "probes": [], "stage": "preflight"}
    started, probes = time.monotonic(), []
    try:
        receipt, binary = verify_source(probe_path)
        weather = verify_weather(weather_path)
        terrain, arrays, profile = verify_terrain(terrain_path)
        # Static source acquisition also predates the hypothetical prediction window.
        start = timestamp(weather["simulation_start_time_utc"])
        if timestamp(terrain["created_at_utc"]) >= start:
            raise ValueError("Static terrain preparation must precede simulation start")
        for record in terrain["sources"]["dem"]:
            if timestamp(record["retrieved_at_utc"]) >= start:
                raise ValueError("Terrain source was retrieved after simulation start")
        probes = select_probes(arrays, profile)
        rotation = grid_rotation(profile)
        references = {
            "probe": (probe_path, sha256(probe_path)),
            "terrain": (terrain_path, sha256(terrain_path)),
            "weather": (weather_path, sha256(weather_path)),
        }
        plan = FLAGS | {
            "study": "korea_terrain_fixed_fuel_sensitivity_v1",
            "created_at_utc": datetime.now(UTC).isoformat(),
            "source_commit": SOURCE_SHA,
            "binary_sha256": receipt["binary_sha256"],
            "license": receipt["license"],
            "license_scope": receipt["license_scope"],
            "license_sha256": receipt["license_sha256"],
            "references": {
                name: {"path": str(path), "sha256": digest}
                for name, (path, digest) in references.items()
            },
            "grid": {key: terrain[key] for key in ("crs", "shape", "pixel_size_m", "transform")},
            "source_terrain_limitations": terrain.get("limitations", []),
            "simulation_start_time_utc": weather["simulation_start_time_utc"],
            "weather_source": weather["source"],
            "forecast_issue_time_utc": weather["forecast_issue_time_utc"],
            "forecast_issue_time_known": weather.get("forecast_issue_time_known", True),
            "issue_time_note": weather.get("issue_time_note"),
            "wind_axis_verification_method": weather["axis_verification"]["method"],
            "horizon_seconds": HORIZONS,
            "weather_band_count": 7,
            "dt_meteorology_seconds": 3600,
            "engine_raster_nodata": -9999,
            "initial_state_encoding": (
                "Arrival 0 seconds is valid assumed ignition; negative nodata denotes "
                "no arrival in this simulation. Input sentinel prevents engine default0 collision."
            ),
            "scenario_plan": [
                {"id": f"fuel_{fuel}", "fuel_model": fuel} for fuel in FUEL_SCENARIOS
            ],
            "scenario_interpretation": (
                "Three fixed assumed fuels, not an uncertainty distribution "
                "or calibrated probability"
            ),
            "ignition_rule": (
                "Nearest explicit forest cell to domain center within 500m; "
                "row-major ties; actual cell center"
            ),
            "static_data_acquisition_upper_bound_utc": terrain["created_at_utc"],
            "static_data_time_note": (
                "DEM individual retrieval times verified. CCI download timestamp unavailable; "
                "the hash-linked derived manifest creation is its acquisition upper bound"
            ),
            "ignition_observed": False,
            "probe_locations": probes,
            "assumptions": {
                "canopy_cover_height_base_density": [0, 0, 0, 0],
                "dead_moisture_percent_m1_m10_m100": [6, 7, 8],
                "live_herb_woody_foliar_moisture_percent": [60, 90, 90],
                "surface_only": True,
                "spotting": False,
                "suppression": False,
                "fuel_calibrated_for_korea": False,
                "spatial_point_wind_uniform": True,
            },
            "mask_semantics": {
                "included_forest_cells": int((arrays["forest_mask.tif"] == 1).sum()),
                "excluded_water_cells": int((arrays["water_mask.tif"] == 1).sum()),
                "excluded_known_nonforest_cells": int(
                    ((arrays["forest_mask.tif"] == 0) & (arrays["water_mask.tif"] == 0)).sum()
                ),
                "unknown_cells": 0,
                "excluded_is_safe": False,
                "codes": (
                    "fuel98 water; fuel99 other known nonforest; exclusion is a study boundary"
                ),
            },
            "wind_conversion": {
                "input": "10m m/s true-north clockwise FROM",
                "raster": "10m km/h grid-north clockwise FROM",
                "engine": "kph *0.621 to mph; 10m *0.87 to20ft then fuel wind-adjustment",
                "rotation": "per-cell projected true-north vector; WDgrid=WDtrue+rotation",
                "rotation_min_max_deg": [float(rotation.min()), float(rotation.max())],
            },
            "cpu_threads_per_case": 1,
            "feedback_level": 3,
            "coverage_rule": (
                "Audit solver stop via fire_size_stats and STOPPING log; final raster filename "
                "does not prove full-horizon integration. Beyond solver coverage remains null."
            ),
            "case_timeout_seconds": timeout,
            "validation": (
                "Input/execution consistency only; no observed perimeter, "
                "Korean validation or personal safety inference"
            ),
        }
        write_json(output / "plan.json", plan)
        report.update(
            {
                "plan_sha256": sha256(output / "plan.json"),
                "stage": "prepare_inputs",
                "plan": plan,
                "status": "running",
            }
        )
        write_json(output / "report.json", report)
        save_raster(output / "true_north_grid_bearing_deg.tif", rotation, profile)
        for name in (
            "forest_mask.tif",
            "water_mask.tif",
            "unknown_mask.tif",
            "landcover_class.tif",
        ):
            save_raster(output / name, arrays[name], profile)
        prefix = binary.parent.parent / "env"
        env = os.environ.copy() | {
            "PATH": str(prefix / "bin") + os.pathsep + os.environ.get("PATH", ""),
            "CONDA_PREFIX": str(prefix),
            "GDAL_DATA": str(prefix / "share/gdal"),
            "PROJ_DATA": str(prefix / "share/proj"),
            "CUDA_VISIBLE_DEVICES": "",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
        }
        translate = prefix / "bin/gdal_translate"
        if not prepare_only and not translate.is_file():
            raise ValueError("Successful probe's isolated GDAL executable is missing")
        for scenario in plan["scenario_plan"]:
            case = output / scenario["id"]
            item = scenario | FLAGS | {"status": "preparing"}
            report["cases"].append(item)
            case_start = time.monotonic()
            try:
                item["input_sha256"] = prepare_case(
                    case, arrays, profile, weather, scenario["fuel_model"], rotation, probes
                )
                if prepare_only:
                    item["status"] = "prepared"
                else:
                    report["stage"] = "simulate"
                    run_command(
                        ["nice", "-n", "10", str(binary), "./inputs/elmfire.data"],
                        case,
                        env,
                        timeout,
                    )
                    if "End of simulation reached successfully" not in (case / "run.log").read_text(
                        errors="replace"
                    ):
                        raise ValueError("Engine did not report successful completion")
                    bils = list((case / "outputs").glob("time_of_arrival*.bil"))
                    if len(bils) != 1:
                        raise ValueError("Expected exactly one final arrival raster")
                    target = bils[0].with_suffix(".tif")
                    run_command(
                        [
                            str(translate),
                            "-a_srs",
                            "EPSG:32652",
                            "-co",
                            "COMPRESS=DEFLATE",
                            str(bils[0]),
                            str(target),
                        ],
                        case,
                        env,
                        60,
                    )
                    item.update(inspect_arrival(target, arrays, profile, probes))
                    coverage = inspect_coverage(case)
                    item["coverage"] = coverage
                    item["observed_future_reached_area_ha"] = item["future_reached_area_ha"].copy()
                    item["future_reached_area_ha"] = {
                        key: value if coverage["horizon_completed"][key] else None
                        for key, value in item["future_reached_area_ha"].items()
                    }
                    if not coverage["full_horizon_completed"]:
                        for point in item["probes"]:
                            if point["state"] == "unreached_within_horizon":
                                point["state"] = "unreached_within_simulated_coverage"
                    # Input files may be supplemented by engine-generated tables but never mutated.
                    for name, digest in item["input_sha256"].items():
                        if sha256(case / "inputs" / name) != digest:
                            raise ValueError(f"Scenario input changed during simulation: {name}")
                    item["status"] = (
                        "complete" if coverage["full_horizon_completed"] else "censored"
                    )
            except Exception as error:
                item.update(
                    {"status": "failed", "error_type": type(error).__name__, "error": str(error)}
                )
            item["elapsed_seconds"] = round(time.monotonic() - case_start, 3)
            report["probes"] = aggregate(report["cases"], probes)
            write_json(output / "report.json", report)
            print(f"{scenario['id']}: {item['status']}", flush=True)
        report["stage"] = "final_integrity"
        for path, digest in references.values():
            if sha256(path) != digest:
                raise ValueError("A source manifest changed during this study")
        verify_source(probe_path)
        verify_weather(weather_path)
        verify_terrain(terrain_path)
        target_status = "prepared" if prepare_only else "complete"
        if all(case["status"] == target_status for case in report["cases"]):
            report["status"] = target_status
        elif not prepare_only and all(
            case["status"] in {"complete", "censored"} for case in report["cases"]
        ):
            report["status"] = "censored"
        else:
            report["status"] = "partial_failure"
    except Exception as error:
        report.update({"status": "failed", "error_type": type(error).__name__, "error": str(error)})
        report["probes"] = aggregate(report["cases"], probes, integrity_ok=False)
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["finished_at_utc"] = datetime.now(UTC).isoformat()
    write_json(output / "probes.geojson", geojson(report["probes"]))
    write_json(output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-report", type=Path, required=True)
    parser.add_argument("--terrain-manifest", type=Path, required=True)
    parser.add_argument("--weather", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case-timeout", type=int, default=300)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.case_timeout <= 900:
        parser.error("--case-timeout must be1..900 seconds")
    report = execute(
        args.probe_report.resolve(),
        args.terrain_manifest.resolve(),
        args.weather.resolve(),
        args.output.resolve(),
        args.case_timeout,
        args.prepare_only,
    )
    print(f"Korean-terrain research study {report['status']}: {args.output / 'report.json'}")
    return 0 if report["status"] in {"complete", "censored", "prepared"} else 1


if __name__ == "__main__":
    sys.exit(main())
