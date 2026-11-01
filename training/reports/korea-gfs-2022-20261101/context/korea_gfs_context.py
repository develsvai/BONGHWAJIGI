"""Input-only, 2022 primary-cohort GFS context; no outcomes are decoded.

Two stages use existing environments: rasterio decodes bounded native windows,
then pyarrow joins primary input positions. Neither stage makes network calls.
WGS84 numeric longitude/latitude are sampled on the native 6371229 m sphere;
this is an explicitly recorded angular-coordinate approximation, not a datum transform.
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from bonghwa_training.download import file_sha256
from bonghwa_training.kma_weather_alignment_probe import GFS_FIELDS, gfs_metadata

PROFILE = "korea_gfs_context_2022_primary_v1"
DECODE_PROFILE = "gfs_2022_native_korea_windows_v1"
COHORT_PROFILE = "kor_gk2a_first_future_observation_train_only_v1"
ACQUISITION_PROFILE = "gfs_2022_train_current_weather_v1"
TRAIN_IDS = frozenset(
    "hapcheon_2022 uljin_2022 yeongdeok_2022 yeongwol_2022 gangneung_donghae_2022 "
    "bonghwa_2022 yanggu_2022 gunwi_2022 uljin_may_2022 miryang_2022".split()
)
INPUT_COLUMNS = [
    "cohort_primary_clear60",
    "issue_epoch_seconds",
    "row",
    "col",
    "latitude",
    "longitude",
]
EXPECTED_UNIQUE_ROWS = 79612
EXPECTED_SOURCE_FILES = 71
SPHERE_RADIUS_M = 6371229.0
ASSUMED_DELAY_HOURS = 6
# Fixed native source centers enclosing Korea plus a margin. No reprojection.
ROW_START, ROW_STOP, COL_START, COL_STOP = 198, 235, 494, 531
DOCUMENTATION = [
    "https://gdal.org/en/stable/drivers/raster/grib.html",
    "https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table3-2.shtml",
    "https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table3-3.shtml",
    "https://registry.opendata.aws/noaa-gfs-bdp-pds/",
]


def save(path, value):
    with Path(path).open("x") as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def utc_seconds(value):
    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.utcoffset() is None or value.utcoffset().total_seconds() != 0 or value.year != 2022:
        raise ValueError("UTC 2022 train timestamps only")
    return int(value.timestamp())


def cycle_for_issue(issue):
    issue = np.asarray(issue)
    if not np.isfinite(issue).all() or np.any(issue != np.floor(issue)):
        raise ValueError("finite integral input issue required")
    issue = issue.astype(np.int64)
    lower, upper = utc_seconds("2022-01-01T00:00:00Z"), utc_seconds("2022-12-31T23:59:59Z")
    if np.any((issue < lower) | (issue > upper)):
        raise ValueError("only 2022 input issues permitted")
    reference = (issue - 6 * 3600) // (6 * 3600) * (6 * 3600)
    valid = issue // 3600 * 3600
    lead = (valid - reference) // 3600
    if np.any((lead < 6) | (lead > 11)) or np.any(reference + 6 * 3600 > issue):
        raise ValueError("forecast as-of contract")
    return reference, valid, lead


def source_id(reference, lead):
    return f"{datetime.fromtimestamp(int(reference), UTC):%Y%m%d%H}-f{int(lead):03d}"


def inside(root, relative):
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError("source path escapes acquisition root")
    return path


def verify_hashes(hashes):
    if any(file_sha256(Path(path)) != digest for path, digest in hashes.items()):
        raise ValueError("frozen source/code/plan changed")


def code_hashes():
    return {
        str(path): file_sha256(path)
        for path in (
            Path(__file__),
            Path(__file__).with_name("kma_weather_alignment_probe.py"),
            Path(__file__).with_name("download.py"),
        )
    }


def acquisition(raw):
    report_path, plan_path = raw / "report.json", raw / "plan.json"
    report, plan = json.loads(report_path.read_text()), json.loads(plan_path.read_text())
    if (
        report.get("schema") != ACQUISITION_PROFILE
        or report.get("status") != "completed"
        or report.get("plan_sha256") != file_sha256(plan_path)
        or plan.get("schema") != ACQUISITION_PROFILE
        or set(plan.get("events", {})) != TRAIN_IDS
        or report.get("historical_publication_time_verified") is not False
        or plan.get("future_outcome_or_audit_columns_read") is not False
    ):
        raise ValueError("completed fixed acquisition required")
    files = report["files"]
    if len(files) != EXPECTED_SOURCE_FILES or len({f["id"] for f in files}) != len(files):
        raise ValueError("fixed unique source file inventory required")
    if {f["id"] for f in plan["files"]} != {f["id"] for f in files}:
        raise ValueError("acquisition inventory changed")
    hashes = {str(p): file_sha256(p) for p in (report_path, plan_path)}
    for spec in files:
        reference, valid = utc_seconds(spec["cycle_utc"]), utc_seconds(spec["valid_time_utc"])
        lead = spec["lead_hours"]
        if (
            reference % 21600
            or lead not in range(6, 12)
            or valid != reference + lead * 3600
            or spec["id"] != source_id(reference, lead)
            or set(spec["fields"]) != set(GFS_FIELDS)
        ):
            raise ValueError("acquisition time/field inventory mismatch")
        for variable, field in spec["fields"].items():
            path = inside(raw, field["path"])
            if path.name != variable + ".grib2" or path.stat().st_size != field["bytes"]:
                raise ValueError("field path/size mismatch")
            if utc_seconds(field["source_last_modified_utc"]) > valid:
                raise ValueError("source object unavailable before input valid hour")
            hashes[str(path)] = field["sha256"]
    verify_hashes(hashes)
    return plan, files, hashes


def grid_section(raw):
    offset = 16
    while offset < len(raw) - 4:
        size = int.from_bytes(raw[offset : offset + 4], "big")
        if size < 5 or offset + size > len(raw) - 4:
            raise ValueError("invalid GRIB grid section")
        if raw[offset + 4] == 3:
            return raw[offset : offset + size]
        offset += size
    raise ValueError("missing native grid section")


def check_decoding(tags, crs, transform, shape, count, variable, reference, lead, raw):
    grid = grid_section(raw)
    if len(grid) != 72 or grid[14] != 6:
        raise ValueError("source must declare the 6371229 m sphere")
    expected = {
        "GRIB_UNIT": {"TMP": "[K]", "RH": "[%]", "UGRD": "[m/s]", "VGRD": "[m/s]"}[variable],
        "GRIB_ELEMENT": variable,
        "GRIB_SHORT_NAME": ("2" if variable in ("TMP", "RH") else "10") + "-HTGL",
        "GRIB_REF_TIME": str(reference),
        "GRIB_VALID_TIME": str(reference + lead * 3600),
        "GRIB_FORECAST_SECONDS": str(lead * 3600),
    }
    if count != 1 or any(tags.get(k) != v for k, v in expected.items()):
        raise ValueError("GDAL variable/unit/height/time disagrees with raw GRIB")
    expected_transform = (0.25, 0.0, -0.125, 0.0, -0.25, 90.125)
    if tuple(shape) != (721, 1440) or not np.allclose(
        tuple(transform)[:6], expected_transform, rtol=0, atol=1e-10
    ):
        raise ValueError("native quarter-degree geometry changed")
    params = crs.to_dict()
    radius = float(params.get("R", params.get("a", np.nan)))
    minor = float(params.get("R", params.get("b", np.nan)))
    if not crs.is_geographic or radius != SPHERE_RADIUS_M or minor != SPHERE_RADIUS_M:
        raise ValueError("decoded sphere cannot be relabelled EPSG4326")


def decode(raw, output):
    import rasterio
    from rasterio.windows import Window

    plan, files, hashes = acquisition(raw)
    hashes.update(code_hashes())
    output.mkdir(parents=True, exist_ok=False)
    decode_plan = {
        "profile": DECODE_PROFILE,
        "source_hashes": hashes,
        "source_acquisition_plan_sha256": file_sha256(raw / "plan.json"),
        "source_acquisition_report_sha256": file_sha256(raw / "report.json"),
        "native_window_row_col": [ROW_START, ROW_STOP, COL_START, COL_STOP],
        "normalization": {"GRIB_NORMALIZE_UNITS": "NO", "GRIB_ADJUST_LONGITUDE_RANGE": "NO"},
        "no_network_calls": True,
        "source_plan_event_ids": sorted(plan["events"]),
    }
    save(output / "plan.json", decode_plan)
    hashes[str(output / "plan.json")] = file_sha256(output / "plan.json")
    records = {}
    window = Window(COL_START, ROW_START, COL_STOP - COL_START, ROW_STOP - ROW_START)
    with rasterio.Env(GRIB_NORMALIZE_UNITS="NO", GRIB_ADJUST_LONGITUDE_RANGE="NO"):
        for spec in files:
            arrays, metadata, tags = {}, {}, {}
            ref, lead = utc_seconds(spec["cycle_utc"]), spec["lead_hours"]
            for variable, field in spec["fields"].items():
                path = inside(raw, field["path"])
                payload = path.read_bytes()
                meta = gfs_metadata(
                    payload, variable, reference=datetime.fromtimestamp(ref, UTC), lead=lead
                )
                if meta != field["metadata"]:
                    raise ValueError("source field metadata changed")
                metadata[variable] = meta
                with rasterio.open(path) as src:
                    check_decoding(
                        src.tags(1),
                        src.crs,
                        src.transform,
                        src.shape,
                        src.count,
                        variable,
                        ref,
                        lead,
                        payload,
                    )
                    values = src.read(1, window=window, masked=True).astype(np.float64)
                    arrays[variable] = values.filled(np.nan)
                    tags[variable] = src.tags(1)
                    native_crs_wkt = src.crs.to_wkt()
            if len({m["grid_sha256"] for m in metadata.values()}) != 1:
                raise ValueError("four fields have inconsistent native grids")
            target = output / (spec["id"] + ".npz")
            with target.open("xb") as stream:
                np.savez_compressed(stream, **arrays)
            records[spec["id"]] = {
                "path": target.name,
                "sha256": file_sha256(target),
                "metadata": metadata,
                "raw_fields": spec["fields"],
                "decoded_tags": tags,
                "native_crs_wkt": native_crs_wkt,
            }
    verify_hashes(hashes)
    report = {
        "profile": DECODE_PROFILE,
        "status": "completed",
        "files": records,
        "plan_sha256": file_sha256(output / "plan.json"),
        "source_acquisition_plan_sha256": file_sha256(raw / "plan.json"),
        "source_acquisition_report_sha256": file_sha256(raw / "report.json"),
        "versions": {
            "numpy": np.__version__,
            "rasterio": rasterio.__version__,
            "gdal": rasterio.__gdal_version__,
        },
        "source_hashes_rechecked": len(hashes),
        "native_sphere_radius_m": SPHERE_RADIUS_M,
        "operational_use": False,
    }
    save(output / "report.json", report)
    return {"status": report["status"], "decoded_files": len(records)}


def primary_inputs(path):
    import pyarrow.parquet as pq

    table = pq.read_table(path, columns=INPUT_COLUMNS)
    columns = {k: table[k].to_numpy() for k in INPUT_COLUMNS}
    primary = columns.pop("cohort_primary_clear60")
    if primary.dtype != bool:
        raise ValueError("primary cohort must be a complete boolean column")
    values = {k: v[primary] for k, v in columns.items()}
    for name in ("issue_epoch_seconds", "row", "col"):
        if not np.isfinite(values[name]).all() or np.any(values[name] != np.floor(values[name])):
            raise ValueError("finite integral row identity required")
    if any(not np.isfinite(values[k]).all() for k in ("latitude", "longitude")):
        raise ValueError("finite source coordinates required")
    if np.any((values["latitude"] < 32) | (values["latitude"] > 40)) or np.any(
        (values["longitude"] < 124) | (values["longitude"] > 132)
    ):
        raise ValueError("fixed Korean spatial scope")
    keys = np.rec.fromarrays(
        [values[k].astype(np.int64) for k in ("issue_epoch_seconds", "row", "col")],
        names="issue,row,col",
    )
    _, indices, inverse, counts = np.unique(
        keys, return_index=True, return_inverse=True, return_counts=True
    )
    if not len(indices) or not np.all(counts == 3):
        raise ValueError("exactly three horizon repeats per primary input required")
    for name in ("latitude", "longitude"):
        if not np.array_equal(values[name], values[name][indices][inverse]):
            raise ValueError("repeated row coordinates disagree")
    values = {k: v[indices] for k, v in values.items()}
    cycle_for_issue(values["issue_epoch_seconds"])
    return values, int(primary.sum())


def nearest_native(longitude, latitude):
    """Spherical great-circle nearest among bracketing native centers; no interpolation."""
    lon, lat = np.asarray(longitude, float), np.asarray(latitude, float)
    if lon.shape != lat.shape or not np.isfinite(lon).all() or not np.isfinite(lat).all():
        raise ValueError("matching finite angular coordinates required")
    if np.any((lon < 124) | (lon > 132) | (lat < 32) | (lat > 40)):
        raise ValueError("fixed Korean spatial scope")
    rr, cc = np.floor((90 - lat) / 0.25).astype(int), np.floor(lon / 0.25).astype(int)
    rows = np.stack((rr, rr, rr + 1, rr + 1), axis=-1)
    cols = np.stack((cc, cc + 1, cc, cc + 1), axis=-1)
    ys, xs = 90 - rows * 0.25, cols * 0.25
    delta_lat = np.deg2rad(ys - lat[..., None])
    delta_lon = np.deg2rad(xs - lon[..., None])
    hav = (
        np.sin(delta_lat / 2) ** 2
        + np.cos(np.deg2rad(lat[..., None])) * np.cos(np.deg2rad(ys)) * np.sin(delta_lon / 2) ** 2
    )
    distance = 2 * SPHERE_RADIUS_M * np.arctan2(np.sqrt(hav), np.sqrt(1 - hav)) / 1000
    choice = np.argmin(distance, axis=-1)[..., None]
    take = lambda value: np.take_along_axis(value, choice, axis=-1)[..., 0]  # noqa: E731
    row, col, gap = take(rows), take(cols), take(distance)
    if np.any((row < ROW_START) | (row >= ROW_STOP) | (col < COL_START) | (col >= COL_STOP)):
        raise ValueError("nearest native point outside frozen decoded window")
    return row, col, 90 - row * 0.25, col * 0.25, gap


def sample_values(arrays, row, col):
    shape = (ROW_STOP - ROW_START, COL_STOP - COL_START)
    if set(arrays) != set(GFS_FIELDS) or any(arrays[k].shape != shape for k in GFS_FIELDS):
        raise ValueError("decoded window schema mismatch")
    values = {k: np.asarray(arrays[k], float)[row - ROW_START, col - COL_START] for k in GFS_FIELDS}
    bounds = {"TMP": (180, 340), "RH": (0, 100), "UGRD": (-150, 150), "VGRD": (-150, 150)}
    valid = np.ones(np.asarray(row).shape, dtype=bool)
    for key, (low, high) in bounds.items():
        good = np.isfinite(values[key]) & (values[key] >= low) & (values[key] <= high)
        values[key] = np.where(good, values[key], np.nan)
        valid &= good
    return {
        "gfs_temperature_c": values["TMP"] - 273.15,
        "gfs_humidity_pct": values["RH"],
        "gfs_wind_u_ms": values["UGRD"],
        "gfs_wind_v_ms": values["VGRD"],
        "gfs_sample_valid": valid,
    }


def make_plan(cohort, raw, decoded):
    cfg_path = cohort / "config.json"
    cfg = json.loads(cfg_path.read_text())
    if cfg.get("profile") != COHORT_PROFILE or len(cfg["events"]) != 14:
        raise ValueError("frozen train-only first-observation cohort required")
    events = [e for e in cfg["events"] if e["id"] in TRAIN_IDS]
    if (
        len(events) != 10
        or {e["id"] for e in events} != TRAIN_IDS
        or any(e.get("split") != "train" or utc_seconds(e["start_utc"]) <= 0 for e in events)
    ):
        raise ValueError("fixed ten 2022 training events required")
    raw_plan, files, hashes = acquisition(raw)
    dreport = json.loads((decoded / "report.json").read_text())
    dplan = json.loads((decoded / "plan.json").read_text())
    if (
        dreport.get("profile") != DECODE_PROFILE
        or dreport.get("status") != "completed"
        or dreport["plan_sha256"] != file_sha256(decoded / "plan.json")
        or dreport["source_acquisition_report_sha256"] != file_sha256(raw / "report.json")
        or dreport["source_acquisition_plan_sha256"] != file_sha256(raw / "plan.json")
        or dplan["native_window_row_col"] != [ROW_START, ROW_STOP, COL_START, COL_STOP]
        or set(dreport["files"]) != {f["id"] for f in files}
    ):
        raise ValueError("complete same-source decoded window receipt required")
    for name in ("plan.json", "report.json"):
        hashes[str(decoded / name)] = file_sha256(decoded / name)
    for spec in files:
        receipt = dreport["files"][spec["id"]]
        if receipt["raw_fields"] != spec["fields"]:
            raise ValueError("decoded raw-source inventory mismatch")
        hashes[str(inside(decoded, receipt["path"]))] = receipt["sha256"]
    hashes[str(cfg_path)] = file_sha256(cfg_path)
    hashes[str(cohort / "plan.json")] = file_sha256(cohort / "plan.json")
    hashes.update(code_hashes())
    inventory, ids, unique_total = {}, set(), 0
    for event in events:
        name = event["id"]
        path = cohort / (name + ".parquet")
        digest = file_sha256(path)
        if digest != raw_plan["events"][name]["source_sha256"]:
            raise ValueError("cohort differs from acquisition input-only plan")
        values, repeats = primary_inputs(path)
        if repeats != raw_plan["events"][name]["primary_rows_with_horizon_repeats"]:
            raise ValueError("primary input row count changed")
        ref, _, lead = cycle_for_issue(values["issue_epoch_seconds"])
        ids.update(source_id(r, h) for r, h in set(zip(ref.tolist(), lead.tolist(), strict=True)))
        rows = len(values["row"])
        unique_total += rows
        inventory[name] = {
            "event": event,
            "rows": rows,
            "source_primary_rows": repeats,
            "source_cohort_parquet_sha256": digest,
        }
        hashes[str(path)] = digest
    if unique_total != EXPECTED_UNIQUE_ROWS or ids != set(dreport["files"]):
        raise ValueError("fixed primary candidate/source inventory changed")
    verify_hashes(hashes)
    return {
        "profile": PROFILE,
        "events": inventory,
        "rows": unique_total,
        "source_hashes": hashes,
        "input_columns_decoded": INPUT_COLUMNS,
        "future_outcome_or_audit_columns_read": False,
        "source_cohort_config_sha256": file_sha256(cfg_path),
        "source_cohort_plan_sha256": file_sha256(cohort / "plan.json"),
        "source_acquisition_report_sha256": file_sha256(raw / "report.json"),
        "source_acquisition_plan_sha256": file_sha256(raw / "plan.json"),
        "source_decoded_report_sha256": file_sha256(decoded / "report.json"),
        "source_decoded_plan_sha256": file_sha256(decoded / "plan.json"),
        "wind_basis": "earth_relative_east_north",
        "assumed_release_delay_hours": 6,
        "historical_publication_time_verified": False,
        "time_contract": "reference=floor((issue-6h)/6h)*6h; valid=floor(issue/1h)*1h",
        "native_sphere_radius_m": SPHERE_RADIUS_M,
        "coordinate_sampling": (
            "Numeric WGS84 lon/lat sampled as native spherical angular coordinates; "
            "four bracketing cell centers, minimum spherical great-circle distance. "
            "No datum transformation, interpolation, resampling or EPSG4326 relabelling. "
            "GFS winds are true east/north. Downstream WGS84 fire bearing "
            "is a separate approximation."
        ),
        "missing_policy": "invalid native values remain NaN with sample_valid=false; no zero fill",
        "not_fine_scale_weather": "0.25 degree forecast; repeated nearby target cells share values",
        "documentation": DOCUMENTATION,
        "documentation_checked_kst": "2026-11-01",
        "validation_read": False,
        "calibration_read": False,
        "test_read": False,
        "operational_use": False,
        "probability": None,
    }


def build(cohort, raw, decoded, output, plan_only=False):
    import pyarrow as pa
    import pyarrow.parquet as pq

    plan = make_plan(cohort, raw, decoded)
    if plan_only:
        output.mkdir(parents=True, exist_ok=False)
        save(output / "plan.json", plan)
        return {"status": "plan_frozen", "rows": plan["rows"]}
    if json.loads((output / "plan.json").read_text()) != plan:
        raise ValueError("frozen converter plan changed")
    plan_sha = file_sha256(output / "plan.json")
    save(
        output / "started.json", {"plan_sha256": plan_sha, "at_utc": datetime.now(UTC).isoformat()}
    )
    decoded_report = json.loads((decoded / "report.json").read_text())
    cache, events = {}, {}
    for name, item in plan["events"].items():
        values, _ = primary_inputs(cohort / (name + ".parquet"))
        issue = values["issue_epoch_seconds"].astype(np.int64)
        reference, valid, lead = cycle_for_issue(issue)
        row, col, lat, lon, distance = nearest_native(values["longitude"], values["latitude"])
        ids = np.asarray([source_id(r, h) for r, h in zip(reference, lead, strict=True)])
        weather = {
            k: np.full(len(issue), np.nan)
            for k in ("gfs_temperature_c", "gfs_humidity_pct", "gfs_wind_u_ms", "gfs_wind_v_ms")
        }
        weather["gfs_sample_valid"] = np.zeros(len(issue), dtype=bool)
        for sid in sorted(set(ids)):
            if sid not in cache:
                path = inside(decoded, decoded_report["files"][sid]["path"])
                with np.load(path, allow_pickle=False) as data:
                    cache[sid] = {k: data[k] for k in data.files}
            selected = ids == sid
            sampled = sample_values(cache[sid], row[selected], col[selected])
            for key, data in sampled.items():
                weather[key][selected] = data
        columns = {
            "event_id": np.full(len(issue), name),
            **values,
            **weather,
            "gfs_grid_lon": lon,
            "gfs_grid_lat": lat,
            "gfs_grid_distance_km": distance,
            "gfs_reference_epoch_seconds": reference,
            "gfs_valid_epoch_seconds": valid,
            "gfs_assumed_available_epoch_seconds": reference + 21600,
            "gfs_forecast_lead_hours": lead,
            "gfs_reference_age_hours": (issue - reference) / 3600,
            "gfs_valid_age_hours": (issue - valid) / 3600,
            "gfs_source_id": ids,
        }
        path = output / (name + ".parquet")
        if path.exists():
            raise FileExistsError(path)
        pq.write_table(pa.table(columns), path, compression="zstd")
        events[name] = {
            **item,
            "sha256": file_sha256(path),
            "invalid_samples": int((~weather["gfs_sample_valid"]).sum()),
            "native_grid_distance_km_min": float(distance.min()),
            "native_grid_distance_km_max": float(distance.max()),
            "unique_native_cells": len(set(zip(row.tolist(), col.tolist(), strict=True))),
        }
    checks = {**plan["source_hashes"], str(output / "plan.json"): plan_sha}
    checks.update({str(output / (name + ".parquet")): r["sha256"] for name, r in events.items()})
    verify_hashes(checks)
    report = {
        **{k: v for k, v in plan.items() if k not in ("source_hashes", "events")},
        "status": "completed",
        "plan_sha256": plan_sha,
        "events": events,
        "source_files_rechecked": len(checks),
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "invalid_samples": sum(r["invalid_samples"] for r in events.values()),
        "versions": {"numpy": np.__version__, "pyarrow": pa.__version__},
    }
    save(output / "report.json", report)
    return {
        "status": report["status"],
        "rows": report["rows"],
        "invalid_samples": report["invalid_samples"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("decode", "plan", "build"))
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--decoded", type=Path, required=True)
    parser.add_argument("--cohort", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "decode":
        result = decode(args.raw, args.decoded)
    else:
        if args.cohort is None or args.output is None:
            parser.error("plan/build require --cohort and --output")
        result = build(args.cohort, args.raw, args.decoded, args.output, args.command == "plan")
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
