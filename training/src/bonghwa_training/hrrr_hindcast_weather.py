"""Fixed Walker 2019 HRRR wind acquisition and vector-aware raster conversion.

Uses the actual 20 UTC operational forecast cycle, not future observed weather.
Historical publication latency remains unverified. No probability or Korean labels.
"""

import argparse
import hashlib
import json
import math
import os
import shutil
import time
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform, transform_bounds
from rasterio.windows import Window, from_bounds

CYCLE = datetime(2019, 9, 4, 20, tzinfo=UTC)
START = CYCLE + timedelta(hours=2)
HOURS = tuple(range(2, 9))
VARIABLES = {"UGRD": 2, "VGRD": 3}
BASE = "https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.20190904/conus/"
SHAPE = (419, 411)
TRANSFORM = from_origin(677100, 4456400, 100, 100)
CRS = "EPSG:32610"
BOUNDS = (677100, 4414500, 718200, 4456400)
MAX_GRIB = 4 * 1024 * 1024


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def url(hour):
    if hour not in HOURS:
        raise ValueError("Forecast hour outside the fixed plan")
    return BASE + f"hrrr.t20z.wrfsfcf{hour:02d}.grib2"


def index_ranges(payload, hour):
    url(hour)
    if len(payload) > 131072:
        raise ValueError("Index too large")
    rows = [row.split(":") for row in payload.decode("ascii").splitlines() if row.strip()]
    if not rows or any(len(row) < 6 for row in rows):
        raise ValueError("Malformed GRIB index")
    offsets = [int(row[1]) for row in rows]
    if offsets != sorted(set(offsets)) or offsets[0] != 0:
        raise ValueError("Invalid GRIB index offsets")
    result = {}
    for variable in VARIABLES:
        selected = [
            i
            for i, row in enumerate(rows)
            if len(row) >= 6 and row[3:6] == [variable, "10 m above ground", f"{hour} hour fcst"]
        ]
        if len(selected) != 1 or selected[0] >= len(rows) - 1:
            raise ValueError("Exactly one bounded 10m field is required")
        i = selected[0]
        if rows[i][2] != "d=2019090420":
            raise ValueError("Index reference time differs from the fixed cycle")
        start, end = offsets[i], offsets[i + 1] - 1
        if not 0 < end - start + 1 <= MAX_GRIB:
            raise ValueError("GRIB field size is outside the bounded plan")
        result[variable] = (start, end)
    return result


def inspect_grib(raw, variable, hour):
    url(hour)
    if variable not in VARIABLES:
        raise ValueError("Unexpected wind variable")
    if len(raw) < 20:
        raise ValueError("Truncated GRIB message")
    if (
        raw[:4] != b"GRIB"
        or raw[-4:] != b"7777"
        or raw[7] != 2
        or int.from_bytes(raw[8:16], "big") != len(raw)
        or raw[6] != 0
    ):
        raise ValueError("A single meteorological GRIB2 message is required")
    sections, pos = {}, 16
    while pos < len(raw) - 4:
        size = int.from_bytes(raw[pos : pos + 4], "big")
        if size < 5 or pos + size > len(raw) - 4:
            raise ValueError("Invalid section boundary")
        section = raw[pos : pos + size]
        if section[4] in sections:
            raise ValueError("Multiple GRIB fields are not accepted")
        sections[section[4]] = section
        pos += size
    if pos != len(raw) - 4 or not {1, 3, 4, 5, 6, 7}.issubset(sections):
        raise ValueError("Incomplete GRIB message")
    s = sections[1]
    if len(s) != 21:
        raise ValueError("Invalid identification section")
    reference = datetime(int.from_bytes(s[12:14], "big"), *s[14:19], tzinfo=UTC)
    if (
        len(s) != 21
        or reference != CYCLE
        or s[11] != 1
        or s[19:21] != b"\x00\x01"
        or int.from_bytes(s[5:7], "big") != 7
    ):
        raise ValueError("Expected NCEP operational forecast reference")
    grid = sections[3]
    if len(grid) != 81 or int.from_bytes(grid[12:14], "big") != 30:
        raise ValueError("Expected explicit Lambert GRIB grid template3.30")
    product = sections[4]
    if (
        len(product) != 34
        or int.from_bytes(product[7:9], "big") != 0
        or product[9:11] != bytes([2, VARIABLES[variable]])
        or product[17] != 1
        or int.from_bytes(product[18:22], "big") != hour
        or product[22:24] != bytes([103, 0])
        or int.from_bytes(product[24:28], "big") != 10
    ):
        raise ValueError("Expected requested 10m wind component and forecast hour")
    return {
        "forecast_reference_time_utc": reference.isoformat(),
        "valid_time_utc": (reference + timedelta(hours=hour)).isoformat(),
        "height_m": 10,
        "grid_definition_template": 30,
        "resolution_component_flags": grid[46],
        "grid_relative": bool(grid[46] & 8),
        "grid_definition_sha256": hashlib.sha256(grid).hexdigest(),
        "product_template": 0,
        "variable": variable,
    }


def fetch(source, destination, *, byte_range=None):
    headers = {}
    limit = 131072
    if byte_range is not None:
        start, end = byte_range
        limit = end - start + 1
        headers["Range"] = f"bytes={start}-{end}"
    request = urllib.request.Request(source, headers=headers)
    with urllib.request.urlopen(request, timeout=45) as response:
        status = response.status
        content_range = response.headers.get("Content-Range", "")
        raw = response.read(limit + 1)
    if byte_range is None:
        if status != 200 or len(raw) > limit:
            raise ValueError("Invalid index response")
    elif (
        status != 206 or len(raw) != limit or not content_range.startswith(f"bytes {start}-{end}/")
    ):
        raise ValueError("Server did not honor the exact bounded byte range")
    destination.write_bytes(raw)
    return {
        "path": destination.name,
        "url": source,
        "http_status": status,
        "byte_range": list(byte_range) if byte_range else None,
        "content_range": content_range,
        "bytes": len(raw),
        "sha256": sha(destination),
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
    }


def acquire(output, probe):
    output.mkdir(parents=True, exist_ok=False)
    plan = {
        "cycle_utc": CYCLE.isoformat(),
        "simulation_start_time_utc": START.isoformat(),
        "forecast_hours": list(HOURS),
        "variables": list(VARIABLES),
        "max_new_http_requests": 18,
        "request_spacing_seconds": 1,
        "retries": 0,
        "reuse": "Verified h2 index and U/V from the bounded access probe",
        "operational_use": False,
        "historical_release_time_verified": False,
    }
    save(output / "plan.json", plan)
    report = {"plan": plan, "records": [], "http_attempts": 0, "complete": False}
    try:
        first = json.loads((probe / "report.json").read_text())
        if first["sha256"] != sha(probe / "response.idx") or first["url"] != url(2) + ".idx":
            raise ValueError("Initial index provenance mismatch")
        cached = json.loads((probe / "grib-receipts.json").read_text())
        for hour in HOURS:
            index = output / f"h{hour:02d}.idx"
            if hour == 2:
                shutil.copyfile(probe / "response.idx", index)
                index_record = {
                    "path": index.name,
                    "sha256": sha(index),
                    "url": first["url"],
                    "retrieved_at_utc": first["retrieved_at_utc"],
                    "reused": True,
                }
            else:
                time.sleep(1)
                report["http_attempts"] += 1
                index_record = fetch(url(hour) + ".idx", index)
            report["records"].append(index_record | {"role": "index", "hour": hour})
            ranges = index_ranges(index.read_bytes(), hour)
            for variable in VARIABLES:
                destination = output / f"h{hour:02d}-{variable.lower()}.grib2"
                if hour == 2:
                    source = next(row for row in cached if row["variable"] == variable)
                    if (
                        source["sha256"] != sha(probe / source["path"])
                        or tuple(source["range"]) != ranges[variable]
                        or source["url"] != url(hour)
                    ):
                        raise ValueError("Initial field provenance mismatch")
                    shutil.copyfile(probe / source["path"], destination)
                    receipt = source | {"path": destination.name, "reused": True}
                else:
                    time.sleep(1)
                    report["http_attempts"] += 1
                    receipt = fetch(url(hour), destination, byte_range=ranges[variable])
                metadata = inspect_grib(destination.read_bytes(), variable, hour)
                report["records"].append(
                    receipt
                    | {
                        "role": "wind_grib",
                        "hour": hour,
                        "variable": variable,
                        "metadata": metadata,
                    }
                )
            save(output / "report.json", report)
        report["complete"] = True
    except Exception as error:
        report.update(error_type=type(error).__name__, error=str(error))
    save(output / "report.json", report)
    return report


def grid_to_true(u, v, beta_deg):
    """beta: clockwise true-north bearing of the source grid's positive y axis."""
    beta = np.deg2rad(beta_deg)
    return u * np.cos(beta) + v * np.sin(beta), -u * np.sin(beta) + v * np.cos(beta)


def normalize_pair(upath, vpath, hour):
    metadata = [
        inspect_grib(p.read_bytes(), v, hour) for p, v in ((upath, "UGRD"), (vpath, "VGRD"))
    ]
    if metadata[0]["grid_definition_sha256"] != metadata[1]["grid_definition_sha256"]:
        raise ValueError("U/V source grids disagree")
    values, profile, tags, first = [], None, [], None
    for path, variable in ((upath, "UGRD"), (vpath, "VGRD")):
        with rasterio.open(path) as source:
            expected = {
                "GRIB_UNIT": "[m/s]",
                "GRIB_ELEMENT": variable,
                "GRIB_SHORT_NAME": "10-HTGL",
                "GRIB_REF_TIME": str(int(CYCLE.timestamp())),
                "GRIB_VALID_TIME": str(int((CYCLE + timedelta(hours=hour)).timestamp())),
                "GRIB_FORECAST_SECONDS": str(hour * 3600),
            }
            source_tags = source.tags(1)
            if source.count != 1 or any(source_tags.get(k) != v for k, v in expected.items()):
                raise ValueError("GDAL decoding disagrees with raw GRIB metadata")
            geometry = (source.crs, source.transform, source.shape)
            if first is not None and geometry != first:
                raise ValueError("Decoded component geometry differs")
            first = geometry
            if source.transform.a <= 0 or source.transform.e >= 0:
                raise ValueError("Expected east-right, north-up source raster")
            extent = transform_bounds(CRS, source.crs, *BOUNDS, densify_pts=41)
            window = from_bounds(*extent, source.transform)
            col, row = math.floor(window.col_off) - 2, math.floor(window.row_off) - 2
            right = math.ceil(window.col_off + window.width) + 2
            bottom = math.ceil(window.row_off + window.height) + 2
            window = Window(col, row, right - col, bottom - row)
            if col < 0 or row < 0 or right > source.width or bottom > source.height:
                raise ValueError("Target is outside the forecast domain")
            value = source.read(1, window=window, masked=True)
            if np.ma.getmaskarray(value).any() or not np.isfinite(value.data).all():
                raise ValueError("Unknown source winds are not filled")
            if np.max(np.abs(value.data)) > 100:
                raise ValueError("Source component outside physical sanity range")
            values.append(value.data)
            profile = {"crs": source.crs, "transform": source.window_transform(window)}
            tags.append(source_tags)
    rows, cols = np.indices(values[0].shape)
    xs, ys = profile["transform"] * (cols + 0.5, rows + 0.5)
    lon, lat = transform(profile["crs"], "EPSG:4326", xs.ravel(), ys.ravel())
    lon_n, lat_n = transform(profile["crs"], "EPSG:4326", xs.ravel(), (ys + 1).ravel())
    dlon = (np.asarray(lon_n) - lon + 180) % 360 - 180
    beta = np.rad2deg(np.arctan2(dlon * np.cos(np.deg2rad(lat)), np.asarray(lat_n) - lat))
    beta = beta.reshape(xs.shape)
    if not np.isfinite(beta).all() or np.max(np.abs(beta)) > 45:
        raise ValueError("Unexpected source meridian convergence")
    east, north = grid_to_true(*values, beta) if metadata[0]["grid_relative"] else values
    projected = []
    for component in (east, north):
        dest = np.full(SHAPE, np.nan, dtype="float32")
        reproject(
            component,
            dest,
            src_transform=profile["transform"],
            src_crs=profile["crs"],
            dst_transform=TRANSFORM,
            dst_crs=CRS,
            src_nodata=None,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )
        if not np.isfinite(dest).all():
            raise ValueError("Forecast does not fully cover the target grid")
        projected.append(dest)
    east, north = projected
    speed = np.hypot(east, north)
    direction = np.mod(np.rad2deg(np.arctan2(-east, -north)), 360)
    direction[speed == 0] = 0  # Numeric convention at calm cells, no physical direction.
    return (
        speed,
        direction,
        {
            "raw_metadata": metadata,
            "decoded_metadata": tags,
            "grid_north_true_bearing_range_deg": [float(beta.min()), float(beta.max())],
            "speed_range_m_s": [float(speed.min()), float(speed.max())],
            "calm_cells": int((speed == 0).sum()),
        },
    )


def normalize(raw_root, output):
    receipt = json.loads((raw_root / "report.json").read_text())
    if not receipt["complete"] or receipt["http_attempts"] > 18:
        raise ValueError("Incomplete or unexpected acquisition plan")
    for row in receipt["records"]:
        if sha(raw_root / row["path"]) != row["sha256"]:
            raise ValueError("Acquired source changed")
    output.mkdir(parents=True, exist_ok=False)
    speeds, directions, checks = [], [], []
    for hour in HOURS:
        speed, direction, check = normalize_pair(
            raw_root / f"h{hour:02d}-ugrd.grib2", raw_root / f"h{hour:02d}-vgrd.grib2", hour
        )
        speeds.append(speed)
        directions.append(direction)
        checks.append(check | {"hour": hour})
    times = [(CYCLE + timedelta(hours=h)).isoformat() for h in HOURS]
    files = {}
    for name, arrays in (
        ("wind_speed_m_s.tif", speeds),
        ("wind_direction_true_deg.tif", directions),
    ):
        path = output / name
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=SHAPE[0],
            width=SHAPE[1],
            count=7,
            dtype="float32",
            crs=CRS,
            transform=TRANSFORM,
            nodata=-9999,
            compress="deflate",
        ) as target:
            target.write(np.asarray(arrays, dtype="float32"))
            for band, valid in enumerate(times, 1):
                target.set_band_description(band, valid)
        files[name] = {"path": name, "sha256": sha(path)}
    evidence = {
        "method": "Raw GRIB2 templates3.30/4.0 and GDAL cross-check; source-grid U/V rotated "
        "to true east/north before bilinear reprojection; direction derived afterwards",
        "checks": checks,
        "source_grid_angle_method": "Projected +1m north vector transformed to geographic; "
        "atan2(dlon*cos(latitude),dlat)",
        "calm_direction_convention": "0 degrees where both vector components are zero",
        "raw_report_sha256": sha(raw_root / "report.json"),
        "historical_release_time_verified": False,
        "operational_use": False,
    }
    save(output / "axis-verification.json", evidence)
    provenance = [
        {
            "artifact_path": os.path.relpath(raw_root / r["path"], output),
            "sha256": r["sha256"],
            "role": r["role"],
            "retrieved_at_utc": r["retrieved_at_utc"],
        }
        for r in receipt["records"]
    ]
    now = datetime.now(UTC).isoformat()
    provenance.append(
        {
            "artifact_path": "axis-verification.json",
            "sha256": sha(output / "axis-verification.json"),
            "role": "axis_verification",
            "retrieved_at_utc": now,
        }
    )
    weather = {
        "schema_version": "elmfire_hrrr_gridded_weather_v1",
        "source": "NOAA_HRRR",
        "forecast_issue_time_utc": CYCLE.isoformat(),
        "simulation_start_time_utc": START.isoformat(),
        "historical_forecast_cycle_verified": True,
        "operational_availability_verified": False,
        "wind_axis_basis_verified": True,
        "wind_direction_basis": "true_north_clockwise_from",
        "wind_height_m": 10,
        "wind_speed_unit": "m/s",
        "wind_direction_unit": "degree",
        "hours": [{"valid_time_utc": t} for t in times],
        "outputs": files,
        "axis_verification": {
            "artifact_path": "axis-verification.json",
            "sha256": sha(output / "axis-verification.json"),
            "method": evidence["method"],
        },
        "provenance": provenance,
        "source_code_sha256": sha(Path(__file__)),
        "grid": {"crs": CRS, "shape": list(SHAPE), "transform": list(TRANSFORM)[:6]},
        "operational_use": False,
        "probability": None,
        "limitations": [
            "Two-hour model-cycle lag is a fixed assumption, not historical release proof",
            "3km wind resampled to100m does not resolve100m atmospheric processes",
            "Archived operational forecast, not observed future weather",
            "This US development case does not validate Korean personal risk",
        ],
        "attribution": "NOAA HRRR via NOAA Open Data Dissemination on AWS; modified/reprojected",
        "license_url": "https://registry.opendata.aws/noaa-hrrr-pds/",
    }
    save(output / "weather.json", weather)
    return weather


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    acquire_args = sub.add_parser("acquire")
    acquire_args.add_argument("--probe", type=Path, required=True)
    acquire_args.add_argument("--output", type=Path, required=True)
    convert = sub.add_parser("normalize")
    convert.add_argument("--raw", type=Path, required=True)
    convert.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "acquire":
        report = acquire(args.output, args.probe)
        print(
            json.dumps({"complete": report["complete"], "http_attempts": report["http_attempts"]})
        )
        return 0 if report["complete"] else 1
    normalize(args.raw, args.output)
    print(json.dumps({"status": "normalized", "hours": 7, "operational_use": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
