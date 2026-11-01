#!/usr/bin/env python3
"""One frozen training-event GOFER perimeter hindcast; no operational risk output.

The three moisture cases finish and an immutable-result receipt is written before
future reconstructed-perimeter labels are opened. The Korean runner is unchanged.
Uses its existing integrity, bounded-command, and solver-coverage helpers only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import elmfire_korea_scenario as common
import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.warp import transform as transform_points

EVENT = "walker_2019"
START = "2019-09-04T22:00:00Z"
ISSUE = "2019-09-04T20:00:00Z"
SHAPE = (419, 411)
TRANSFORM = Affine(100, 0, 677100, 0, -100, 4456400)
HORIZONS = {"1h": 3600, "3h": 10800, "6h": 21600}
MOISTURES = ((3, 4, 5), (6, 7, 8), (9, 10, 11))
FLAGS = {
    "simulation_only": True,
    "operational_use": False,
    "probability": None,
    "retrospective_proxy_only": True,
    "source_asof_verified": False,
    "final_evaluation": False,
    "split": "train",
}
FUELS = set(range(101, 110)) | set(range(121, 125)) | set(range(141, 150))
FUELS |= set(range(161, 166)) | set(range(181, 190)) | set(range(201, 205))
NONBURNABLE = {91, 92, 93, 98, 99}
TERRAIN_FILES = (
    "elevation_m.tif",
    "slope_deg.tif",
    "aspect_deg.tif",
    "fuel_model.tif",
    "initial_perimeter_mask.tif",
    "study_domain_mask.tif",
    "unknown_mask.tif",
)


def verified_raster(base: Path, record: dict, count: int = 1) -> tuple[np.ndarray, dict]:
    path = common.verify_file(base, record, "path")
    with rasterio.open(path) as source:
        if (
            source.shape != SHAPE
            or source.count != count
            or source.crs is None
            or source.crs.to_epsg() != 32610
            or source.transform != TRANSFORM
        ):
            raise ValueError(f"Raster differs from the frozen Walker grid: {path.name}")
        values = source.read(masked=True)
        return values, source.profile.copy()


def verify_terrain(path: Path) -> tuple[dict, dict, dict]:
    manifest = json.loads(path.read_text())
    if (
        manifest.get("status") != "ready"
        or manifest.get("event_id") != EVENT
        or common.timestamp(manifest["initial_time_utc"]) != common.timestamp(START)
        or manifest.get("split") != "train"
        or manifest.get("crs") != "EPSG:32610"
        or manifest.get("shape") != list(SHAPE)
        or manifest.get("pixel_size_m") != 100
        or Affine(*manifest["transform"]) != TRANSFORM
        or manifest.get("aspect_reference") != "grid_north_clockwise_downslope"
        or manifest.get("retrospective_proxy_only") is not True
        or manifest.get("source_asof_verified") is not False
    ):
        raise ValueError("Terrain is not the frozen Walker training-event proxy contract")
    archive_sha = manifest.get("sources", {}).get("gofer", {}).get("archive_sha256")
    if not isinstance(archive_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", archive_sha):
        raise ValueError("Terrain requires the source GOFER archive SHA256")
    initial_geometry = manifest["initial_geometry"]
    if initial_geometry.get("source_archive_sha256") != archive_sha:
        raise ValueError("Initial geometry and terrain refer to different GOFER archives")
    common.verify_file(path.parent, initial_geometry, "path")
    values, profile = {}, None
    for name in TERRAIN_FILES:
        data, current_profile = verified_raster(path.parent, manifest["outputs"][name])
        values[name] = data[0]
        profile = current_profile if profile is None else profile
    for name in ("initial_perimeter_mask.tif", "study_domain_mask.tif", "unknown_mask.tif"):
        value = values[name]
        if np.ma.getmaskarray(value).any() or not np.isin(value.data, [0, 1]).all():
            raise ValueError(f"Binary input mask has missing or invalid values: {name}")
    domain = values["study_domain_mask.tif"].data.astype(bool)
    initial = values["initial_perimeter_mask.tif"].data.astype(bool)
    if not domain.any() or not initial.any() or np.any(initial & ~domain):
        raise ValueError("Initial perimeter must be nonempty and fully inside the study domain")
    if np.any(values["unknown_mask.tif"].data.astype(bool) & domain):
        raise ValueError("Unknown terrain or fuels inside study domain")
    arrays = {}
    for name, value in values.items():
        missing = np.ma.getmaskarray(value) | ~np.isfinite(value.data)
        if np.any(missing & domain):
            raise ValueError(f"Missing input inside study domain: {name}")
        arrays[name] = np.where(missing, 0, value.data)
    fuel = arrays["fuel_model.tif"]
    if not np.isin(fuel[domain], sorted(FUELS | NONBURNABLE)).all():
        raise ValueError("Unrecognized LANDFIRE FBFM40 code; no automatic fuel remapping")
    if np.any(np.abs(arrays["elevation_m.tif"][domain]) > 32000):
        raise ValueError("Elevation outside Int16 landscape range")
    for name, maximum in (("slope_deg.tif", 90), ("aspect_deg.tif", 360)):
        data = arrays[name][domain]
        if np.any((data < 0) | (data > maximum)):
            raise ValueError(f"Invalid angle range: {name}")
    if np.any(initial & domain_edge(domain)):
        raise ValueError("Initial perimeter reaches study boundary")
    return manifest, arrays, profile


def verify_weather(path: Path, domain: np.ndarray) -> tuple[dict, dict]:
    manifest = json.loads(path.read_text())
    expected = {
        "schema_version": "elmfire_hrrr_gridded_weather_v1",
        "source": "NOAA_HRRR",
        "historical_forecast_cycle_verified": True,
        "operational_availability_verified": False,
        "wind_axis_basis_verified": True,
        "wind_direction_basis": "true_north_clockwise_from",
        "wind_height_m": 10,
        "wind_speed_unit": "m/s",
        "wind_direction_unit": "degree",
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("Unverified historical forecast cycle, wind axis, height, units or source")
    for key in ("historical_forecast_cycle_verified", "wind_axis_basis_verified"):
        if manifest[key] is not True:
            raise ValueError("Forecast and wind verification must be boolean true")
    if manifest["operational_availability_verified"] is not False:
        raise ValueError("Historical release availability must remain explicitly unverified")
    if common.timestamp(manifest["forecast_issue_time_utc"]) != common.timestamp(
        ISSUE
    ) or common.timestamp(manifest["simulation_start_time_utc"]) != common.timestamp(START):
        raise ValueError("Weather cycle or simulation start differs from the frozen case")
    hours = manifest["hours"]
    if len(hours) != 7 or any(
        common.timestamp(hour["valid_time_utc"]) != common.timestamp(START) + timedelta(hours=i)
        for i, hour in enumerate(hours)
    ):
        raise ValueError("Requires seven hourly forecast knots from t0 through t6")
    provenance = manifest["provenance"]
    if not provenance:
        raise ValueError("Original forecast and axis evidence artifacts are required")
    paths = set()
    for record in provenance:
        common.timestamp(record["retrieved_at_utc"])
        if not record.get("role"):
            raise ValueError("Forecast provenance role missing")
        paths.add(common.verify_file(path.parent, record))
    axis = manifest["axis_verification"]
    if not axis.get("method") or common.verify_file(path.parent, axis) not in paths:
        raise ValueError("Wind-axis evidence must be part of verified provenance")
    arrays = {}
    for name in ("wind_speed_m_s.tif", "wind_direction_true_deg.tif"):
        data, _ = verified_raster(path.parent, manifest["outputs"][name], 7)
        mask = np.ma.getmaskarray(data) | ~np.isfinite(data.data)
        if np.any(mask[:, domain]):
            raise ValueError(f"Missing forecast in study domain: {name}")
        arrays[name] = np.where(mask, 0, data.data).astype("float32")
    speed = arrays["wind_speed_m_s.tif"][:, domain]
    direction = arrays["wind_direction_true_deg.tif"][:, domain]
    if np.any((speed < 0) | (speed > 100)) or np.any((direction < 0) | (direction > 360)):
        raise ValueError("Invalid HRRR wind magnitude or direction")
    return manifest, arrays


def domain_edge(domain: np.ndarray) -> np.ndarray:
    padded = np.pad(domain, 1, constant_values=False)
    interior = domain.copy()
    for dy in range(3):
        for dx in range(3):
            interior &= padded[dy : dy + domain.shape[0], dx : dx + domain.shape[1]]
    return domain & ~interior


def rotation(profile: dict) -> np.ndarray:
    rows, columns = np.indices(SHAPE)
    x, y = profile["transform"] * (columns + 0.5, rows + 0.5)
    lon, lat = transform_points(profile["crs"], "EPSG:4326", x.ravel(), y.ravel())
    nx, ny = transform_points("EPSG:4326", profile["crs"], lon, [v + 0.0001 for v in lat])
    result = np.degrees(np.arctan2(np.asarray(nx) - x.ravel(), np.asarray(ny) - y.ravel()))
    if not np.isfinite(result).all() or np.max(np.abs(result)) > 5:
        raise ValueError("Unexpected UTM10 true-north rotation")
    return result.reshape(SHAPE).astype("float32")


def phi_mask(initial: np.ndarray) -> np.ndarray:
    if initial.dtype != bool or not initial.any() or initial.all():
        raise ValueError(
            "Initial PHI requires a nonempty boolean perimeter with unburned surroundings"
        )
    return np.where(initial, -1.0, 1.0).astype("float32")


def namelist(moisture: tuple[int, int, int]) -> str:
    # Start from the already source-verified namelist, replacing only the ignition
    # declaration and adding a numerical step ceiling; no Korean data is consumed.
    text = common.namelist({"xy_m": [0, 0]})
    text = text.replace("NUM_IGNITIONS = 1", "NUM_IGNITIONS = 0")
    text = (
        "\n".join(
            line
            for line in text.splitlines()
            if not line.startswith(("X_IGN(", "Y_IGN(", "T_IGN("))
        )
        + "\n"
    )
    text = text.replace("SIMULATION_DT = 5.0", "SIMULATION_DT = 5.0\nSIMULATION_DTMAX = 30.0")
    text = text.replace(
        "NUM_METEOROLOGY_TIMES = 7", "NUM_METEOROLOGY_TIMES = 7\nRANDOM_IGNITIONS = .FALSE."
    )
    if moisture not in MOISTURES:
        raise ValueError("Moisture case was not frozen before evaluation")
    return text


def prepare_case(
    case: Path,
    arrays: dict,
    profile: dict,
    weather: dict,
    wind: dict,
    moisture: tuple[int, int, int],
    grid_rotation: np.ndarray,
) -> dict:
    inputs = case / "inputs"
    inputs.mkdir(parents=True)
    (case / "outputs").mkdir()
    (case / "scratch").mkdir()
    domain = arrays["study_domain_mask.tif"].astype(bool)
    initial = arrays["initial_perimeter_mask.tif"].astype(bool)
    land = np.zeros((8, *SHAPE), dtype="int16")
    for i, name in enumerate(("elevation_m.tif", "slope_deg.tif", "aspect_deg.tif")):
        land[i] = np.rint(arrays[name]).astype("int16")
    land[2] %= 360
    land[3] = np.where(domain, arrays["fuel_model.tif"], 99)
    common.save_raster(inputs / "landscape.tif", land, profile, nodata=-9999)
    common.save_raster(inputs / "phi.tif", phi_mask(initial), profile, nodata=-9999)
    ones = np.ones(SHAPE, dtype="float32")
    common.save_raster(inputs / "adj.tif", ones, profile, nodata=-9999)
    descriptions = [hour["valid_time_utc"] for hour in weather["hours"]]
    common.save_raster(
        inputs / "ws.tif", wind["wind_speed_m_s.tif"] * 3.6, profile, descriptions, nodata=-9999
    )
    directions = (wind["wind_direction_true_deg.tif"] + grid_rotation[None]) % 360
    common.save_raster(
        inputs / "wd.tif", directions.astype("float32"), profile, descriptions, nodata=-9999
    )
    for name, value in zip(("m1", "m10", "m100"), moisture, strict=True):
        common.save_raster(
            inputs / f"{name}.tif",
            np.stack([ones * value] * 7),
            profile,
            descriptions,
            nodata=-9999,
        )
    (inputs / "elmfire.data").write_text(namelist(moisture))
    return {path.name: common.sha256(path) for path in sorted(inputs.iterdir())}


def inspect_arrival(path: Path, arrays: dict, coverage: dict) -> tuple[dict, np.ndarray]:
    initial = arrays["initial_perimeter_mask.tif"].astype(bool)
    domain = arrays["study_domain_mask.tif"].astype(bool)
    with rasterio.open(path) as source:
        affine = source.transform
        if (
            source.shape != SHAPE
            or source.count != 1
            or source.crs.to_epsg() != 32610
            or (affine.a, affine.b, affine.d, affine.e) != (100, 0, 0, -100)
            or not np.allclose([affine.c, affine.f], [TRANSFORM.c, TRANSFORM.f], rtol=0, atol=0.3)
            or source.nodata is None
            or source.nodata >= 0
            or not np.isfinite(source.nodata)
        ):
            raise ValueError("Arrival grid or negative nodata contract is invalid")
        data = source.read(1, masked=True)
        valid = ~np.ma.getmaskarray(data)
        raw = data.filled(np.nan)
    if np.any(valid & ~np.isfinite(raw)):
        raise ValueError("Nonfinite unmasked arrival")
    if np.any(valid & (raw < 0)):
        raise ValueError(
            "Unmasked negative arrival is invalid; missing must use the declared nodata"
        )
    reached = valid & (raw >= 0)
    if not np.array_equal(reached & (raw == 0), initial):
        raise ValueError("Every initial perimeter cell, and no other cell, must have arrival zero")
    if np.any(reached & ~domain) or np.any(raw[reached] > 21630.1):
        raise ValueError("Arrival outside study domain or simulated window")
    # dtmax30 can cross final tstop; arrivals after exact6h remain outside all6h metrics.
    edge = domain_edge(domain)
    edges = {key: int((reached & (raw <= h) & edge).sum()) for key, h in HORIZONS.items()}
    availability = {
        key: bool(coverage["horizon_completed"][key]) and edges[key] == 0 for key in HORIZONS
    }
    counts = {
        key: int((reached & ~initial & (raw > 0) & (raw <= h)).sum()) for key, h in HORIZONS.items()
    }
    return {
        "arrival_path": str(path),
        "arrival_sha256": common.sha256(path),
        "arrival_unit": "seconds_since_initial_reconstructed_perimeter",
        "initial_cells": int(initial.sum()),
        "reached_cells": int(reached.sum()),
        "simulated_future_reached_area_ha": counts,
        "future_reached_area_ha": {
            key: counts[key] if availability[key] else None for key in HORIZONS
        },
        "boundary_reached_cells": edges,
        "horizon_available": availability,
        "maximum_arrival_seconds": float(raw[reached].max()),
        "initial_nonburnable_cells": int(
            (initial & np.isin(arrays["fuel_model.tif"], list(NONBURNABLE))).sum()
        ),
    }, raw


def score_masks(
    predicted: np.ndarray, observed: np.ndarray, initial: np.ndarray, domain: np.ndarray
) -> dict:
    """Increment metrics exclude already burned area; undefined denominators stay null."""
    predicted_new = predicted & domain & ~initial
    observed_new = observed & domain & ~initial
    tp = int((predicted_new & observed_new).sum())
    fp = int((predicted_new & ~observed_new).sum())
    fn = int((~predicted_new & observed_new).sum())
    union = tp + fp + fn
    total_union = int(((predicted | observed) & domain).sum())
    return {
        "new_growth_iou": tp / union if union else None,
        "new_growth_precision": tp / (tp + fp) if tp + fp else None,
        "new_growth_recall": tp / (tp + fn) if tp + fn else None,
        "undefined": {
            "new_growth_iou": "empty_growth_union" if not union else None,
            "new_growth_precision": "no_predicted_growth" if not tp + fp else None,
            "new_growth_recall": "no_observed_growth" if not tp + fn else None,
        },
        "new_growth_tp_cells": tp,
        "new_growth_fp_cells": fp,
        "new_growth_fn_cells": fn,
        "predicted_new_area_ha": int(predicted_new.sum()),
        "observed_new_area_ha": int(observed_new.sum()),
        "signed_new_area_error_ha": int(predicted_new.sum()) - int(observed_new.sum()),
        "total_iou_secondary": int((predicted & observed & domain).sum()) / total_union
        if total_union
        else None,
        "grid_cell_area_ha": 1,
    }


def load_truth(path: Path, arrays: dict, fit_receipt: Path) -> tuple[dict, dict]:
    if not fit_receipt.is_file():
        raise ValueError("Fit receipt must exist before future reconstructed labels are opened")
    receipt = json.loads(fit_receipt.read_text())
    if receipt.get("future_labels_read") is not False or receipt.get("cases_attempted") != 3:
        raise ValueError("Incomplete or invalid pre-evaluation receipt")
    data = json.loads(path.read_text())
    for key in ("input_manifest_sha256", "source_archive_sha256"):
        expected = receipt.get(key)
        if (
            not isinstance(expected, str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected)
            or data.get(key) != expected
        ):
            raise ValueError(f"Truth does not match the frozen fit input: {key}")
    if (
        data.get("event_id") != EVENT
        or data.get("split") != "train"
        or common.timestamp(data["initial_time_utc"]) != common.timestamp(START)
        or data.get("retrospective_proxy_only") is not True
    ):
        raise ValueError("Truth is not the same training-event reconstructed proxy")
    initial = arrays["initial_perimeter_mask.tif"].astype(bool)
    domain = arrays["study_domain_mask.tif"].astype(bool)
    truth = {}
    previous = initial
    for key, seconds in HORIZONS.items():
        record = data["outputs"][key]
        if common.timestamp(record["valid_time_utc"]) != common.timestamp(START) + timedelta(
            seconds=seconds
        ):
            raise ValueError("Truth horizon does not match the frozen time")
        values, _ = verified_raster(path.parent, record)
        values = values[0]
        if (
            np.any(np.ma.getmaskarray(values) & domain)
            or not np.isin(values.data[domain], [0, 1]).all()
        ):
            raise ValueError("Missing/invalid reference coverage cannot become an unburned label")
        current = values.data.astype(bool)
        if np.any(previous & domain & ~current):
            raise ValueError("Cumulative reconstructed perimeter unexpectedly shrank")
        truth[key] = current
        previous = current
    return data, truth


def evaluate(cases: list[dict], arrivals: dict, truth: dict, arrays: dict) -> dict:
    initial = arrays["initial_perimeter_mask.tif"].astype(bool)
    domain = arrays["study_domain_mask.tif"].astype(bool)
    edge = domain_edge(domain)
    results, baseline = {}, {}
    for key, seconds in HORIZONS.items():
        truth_censored = bool((truth[key] & edge).any())
        baseline[key] = {
            "status": "spatially_censored" if truth_censored else "evaluated",
            "metrics": None
            if truth_censored
            else score_masks(initial, truth[key], initial, domain),
        }
        for case in cases:
            name = case["id"]
            results.setdefault(name, {})
            reason = (
                "simulation_failed"
                if case["status"] not in {"complete", "censored"}
                else "reference_reaches_spatial_boundary"
                if truth_censored
                else "solver_stopped_before_horizon"
                if not case["coverage"]["horizon_completed"][key]
                else "simulation_reaches_spatial_boundary"
                if case["boundary_reached_cells"][key]
                else None
            )
            if reason:
                results[name][key] = {"status": "unavailable", "reason": reason, "metrics": None}
                continue
            raw = arrivals[name]
            predicted = np.isfinite(raw) & (raw >= 0) & (raw <= seconds)
            results[name][key] = {
                "status": "evaluated",
                "metrics": score_masks(predicted, truth[key], initial, domain),
            }
    return FLAGS | {
        "baseline": {"name": "initial_perimeter_persistence", "horizons": baseline},
        "cases": results,
        "primary_metrics": "new growth outside initial perimeter",
        "interpretation": (
            "Development comparison against retrospective GOFER reconstruction; "
            "no forecast skill certification"
        ),
    }


def execute(
    probe_path: Path,
    terrain_path: Path,
    weather_path: Path,
    truth_path: Path,
    output: Path,
    timeout: int = 300,
    prepare_only: bool = False,
) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = FLAGS | {
        "event_id": EVENT,
        "status": "preflight",
        "stage": "preflight",
        "cases": [],
        "future_labels_read": False,
    }
    arrivals = {}
    try:
        source, binary = common.verify_source(probe_path)
        terrain, arrays, profile = verify_terrain(terrain_path)
        domain = arrays["study_domain_mask.tif"].astype(bool)
        weather, wind = verify_weather(weather_path, domain)
        grid_rotation = rotation(profile)
        references = {
            "probe": (probe_path, common.sha256(probe_path)),
            "terrain": (terrain_path, common.sha256(terrain_path)),
            "weather": (weather_path, common.sha256(weather_path)),
            "runner": (Path(__file__).resolve(), common.sha256(Path(__file__))),
            "shared_engine_helpers": (
                Path(common.__file__).resolve(),
                common.sha256(Path(common.__file__)),
            ),
        }
        plan = FLAGS | {
            "study": "walker2019_fixed_moisture_perimeter_hindcast_v1",
            "event_id": EVENT,
            "initial_time_utc": START,
            "forecast_issue_time_utc": ISSUE,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "source_commit": common.SOURCE_SHA,
            "binary_sha256": source["binary_sha256"],
            "license": source["license"],
            "license_scope": source["license_scope"],
            "references": {
                key: {"path": str(path), "sha256": digest}
                for key, (path, digest) in references.items()
            },
            "truth_manifest_path_not_yet_opened": str(truth_path),
            "case_plan": [
                {"id": "moisture_" + "_".join(map(str, m)), "dead_moisture_percent": list(m)}
                for m in MOISTURES
            ],
            "grid": {
                "crs": "EPSG:32610",
                "shape": list(SHAPE),
                "transform": list(TRANSFORM)[:6],
                "pixel_size_m": 100,
            },
            "initialization": (
                "PHI=-1 inside reconstructed initial cumulative perimeter, "
                "+1 elsewhere; no point ignitions"
            ),
            "assumptions": {
                "entire_boundary_active": True,
                "surface_only": True,
                "canopy": [0, 0, 0, 0],
                "live_herb_woody_foliar_moisture_percent": [60, 90, 90],
                "spotting": False,
                "suppression": False,
                "historical_fuel_and_moisture_field_verified": False,
            },
            "numerics": {
                "initial_dt_seconds": 5,
                "maximum_dt_seconds": 30,
                "target_cfl": 0.2,
                "weather_knots": 7,
                "weather_interval_seconds": 3600,
                "stop_seconds": 21600,
                "nodata": -9999,
                "cpu_threads": 1,
                "case_timeout_seconds": timeout,
            },
            "domain_initial_cells": int(arrays["initial_perimeter_mask.tif"].sum()),
            "domain_cells": int(domain.sum()),
            "outside_domain_is_safe": False,
            "wind_rotation_range_deg": [float(grid_rotation.min()), float(grid_rotation.max())],
            "source_terrain_limitations": terrain.get("limitations", []),
            "source_weather_limitations": weather.get("limitations", []),
            "label_boundary": (
                "Freeze three cases and write fit receipt "
                "before opening future reconstructed labels"
            ),
            "limitations": [
                "GOFER source uses retrospective final-perimeter filtering; "
                "not operational as-of input",
                "100m regridding does not create100m observation truth",
                "One train event, no held-out model selection or Korean transfer validation",
                "Fuel model, zero canopy and moisture assumptions "
                "cannot establish actual fire behavior",
                "Negative/zero-union metrics stay undefined; no calibrated probability is computed",
            ],
        }
        common.write_json(output / "plan.json", plan)
        report.update(
            {"plan": plan, "plan_sha256": common.sha256(output / "plan.json"), "status": "running"}
        )
        common.write_json(output / "report.json", report)
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
            raise ValueError("Pinned isolated GDAL missing")
        for scenario, moisture in zip(plan["case_plan"], MOISTURES, strict=True):
            case = output / scenario["id"]
            item = scenario | FLAGS | {"status": "preparing"}
            report["cases"].append(item)
            case_start = time.monotonic()
            try:
                report["stage"] = "prepare_inputs"
                item["input_sha256"] = prepare_case(
                    case, arrays, profile, weather, wind, moisture, grid_rotation
                )
                if prepare_only:
                    item["status"] = "prepared"
                else:
                    report["stage"] = "simulate"
                    common.run_command(
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
                        raise ValueError("Expected one final arrival raster")
                    target = bils[0].with_suffix(".tif")
                    common.run_command(
                        [
                            str(translate),
                            "-a_srs",
                            "EPSG:32610",
                            "-co",
                            "COMPRESS=DEFLATE",
                            str(bils[0]),
                            str(target),
                        ],
                        case,
                        env,
                        60,
                    )
                    item["coverage"] = common.inspect_coverage(case)
                    stats, raw = inspect_arrival(target, arrays, item["coverage"])
                    item.update(stats)
                    arrivals[scenario["id"]] = raw
                    for name, digest in item["input_sha256"].items():
                        if common.sha256(case / "inputs" / name) != digest:
                            raise ValueError(f"Input changed during simulation: {name}")
                    item["status"] = (
                        "complete" if all(item["horizon_available"].values()) else "censored"
                    )
            except Exception as error:
                item.update(
                    {"status": "failed", "error_type": type(error).__name__, "error": str(error)}
                )
            item["elapsed_seconds"] = round(time.monotonic() - case_start, 3)
            common.write_json(output / "report.json", report)
            print(f"{scenario['id']}: {item['status']}", flush=True)
        report["stage"] = "pre_evaluation_integrity"
        if common.sha256(output / "plan.json") != report["plan_sha256"]:
            raise ValueError("Frozen study plan changed during simulation")
        for case in report["cases"]:
            for name, digest in case.get("input_sha256", {}).items():
                if common.sha256(output / case["id"] / "inputs" / name) != digest:
                    raise ValueError("A case input changed before evaluation")
            if case["status"] in {"complete", "censored"}:
                if common.sha256(Path(case["arrival_path"])) != case["arrival_sha256"]:
                    raise ValueError("A case arrival changed before evaluation")
        for path, digest in references.values():
            if common.sha256(path) != digest:
                raise ValueError("Source manifest changed during simulation")
        common.verify_source(probe_path)
        verify_terrain(terrain_path)
        verify_weather(weather_path, domain)
        receipt = FLAGS | {
            "future_labels_read": False,
            "cases_attempted": len(report["cases"]),
            "created_at_utc": datetime.now(UTC).isoformat(),
            "plan_sha256": report["plan_sha256"],
            "input_manifest_sha256": references["terrain"][1],
            "source_archive_sha256": terrain["sources"]["gofer"]["archive_sha256"],
            "cases": report["cases"],
        }
        common.write_json(output / "fit-receipt.json", receipt)
        report["fit_receipt_sha256"] = common.sha256(output / "fit-receipt.json")
        if prepare_only:
            report["status"] = (
                "prepared"
                if all(c["status"] == "prepared" for c in report["cases"])
                else "partial_failure"
            )
        else:
            report["stage"] = "evaluate_retrospective_labels"
            report["future_labels_read"] = True
            truth_manifest_sha256 = common.sha256(truth_path)
            _, truth = load_truth(truth_path, arrays, output / "fit-receipt.json")
            evaluation = evaluate(report["cases"], arrivals, truth, arrays)
            if common.sha256(truth_path) != truth_manifest_sha256:
                raise ValueError("Truth manifest changed during evaluation")
            if common.sha256(output / "fit-receipt.json") != report["fit_receipt_sha256"]:
                raise ValueError("Frozen fit receipt changed during evaluation")
            for case in report["cases"]:
                if case["status"] in {"complete", "censored"}:
                    if common.sha256(Path(case["arrival_path"])) != case["arrival_sha256"]:
                        raise ValueError("Frozen arrival output changed during evaluation")
            evaluation["truth_manifest_sha256"] = truth_manifest_sha256
            evaluation["fit_receipt_sha256"] = report["fit_receipt_sha256"]
            common.write_json(output / "evaluation.json", evaluation)
            report["evaluation_path"] = str(output / "evaluation.json")
            report["status"] = (
                "complete"
                if all(c["status"] == "complete" for c in report["cases"])
                else "censored"
                if all(c["status"] in {"complete", "censored"} for c in report["cases"])
                else "partial_failure"
            )
    except Exception as error:
        report.update({"status": "failed", "error_type": type(error).__name__, "error": str(error)})
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["finished_at_utc"] = datetime.now(UTC).isoformat()
    common.write_json(output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("probe-report", "terrain-manifest", "weather", "truth-manifest", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--case-timeout", type=int, default=300)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.case_timeout <= 300:
        parser.error("case timeout must be1..300 seconds")
    report = execute(
        args.probe_report.resolve(),
        args.terrain_manifest.resolve(),
        args.weather.resolve(),
        args.truth_manifest.resolve(),
        args.output.resolve(),
        args.case_timeout,
        args.prepare_only,
    )
    print(f"Walker development hindcast {report['status']}: {args.output / 'report.json'}")
    return 0 if report["status"] in {"complete", "censored", "prepared"} else 1


if __name__ == "__main__":
    sys.exit(main())
