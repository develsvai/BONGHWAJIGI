#!/usr/bin/env python3
"""Six predeclared canopy/moisture ablations on the already exposed Walker train event."""

import argparse
import copy
import json
import os
import re
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path

import elmfire_gofer_hindcast as base
import numpy as np
import rasterio
import reconcile_elmfire_endpoint as audit

from bonghwa_training import landfire_canopy as canopy_data

common = base.common
FIXED_CASES = [
    {
        "id": f"canopy_crown{crown}_m{m[0]}_{m[1]}_{m[2]}",
        "crown_fire_model": crown,
        "dead_moisture_percent": list(m),
        "baseline_id": f"moisture_{m[0]}_{m[1]}_{m[2]}",
    }
    for crown in (0, 1)
    for m in base.MOISTURES
]
FLAGS = base.FLAGS | {"future_labels_previously_exposed": True, "held_out_evaluation": False}


def verify_canopy(path: Path, terrain_path: Path, arrays: dict) -> tuple[dict, dict]:
    data = audit.read_json(path)
    if (
        data["status"] != "ready"
        or data["schema_version"] != "lf2016_canopy_walker_v1"
        or data["input_terrain_manifest_sha256"] != common.sha256(terrain_path)
        or data["shape"] != list(base.SHAPE)
        or data["crs"] != "EPSG:32610"
        or data["transform"] != list(base.TRANSFORM)[:6]
    ):
        raise ValueError("Canopy manifest does not match the frozen Walker terrain")
    sources = data["sources"]
    expected = canopy_data.requests_plan()
    if set(sources) != {item["name"] for item in expected}:
        raise ValueError("Canopy source inventory differs from fixed twelve requests")
    for item in expected:
        record = sources[item["name"]]
        if any(record.get(key) != value for key, value in item.items()):
            raise ValueError("Canopy source parameters changed")
        source = audit.checked(path.parent / record["path"], record["sha256"])
        if source.stat().st_size != record["bytes"] or record["status"] != "complete":
            raise ValueError("Canopy source receipt is incomplete")
    raw_root = (path.parent / sources["CC-service.json"]["path"]).resolve().parent
    audit.checked(raw_root / "report.json", data["source_acquisition_report_sha256"])
    raw, encoded = {}, {}
    for product, specification in canopy_data.PRODUCTS.items():
        filename = specification[0]
        units = canopy_data.validate_metadata(
            product,
            audit.read_json(raw_root / f"{product}-service.json"),
            (raw_root / f"{product}-units.html").read_text(),
        )
        raw[product] = canopy_data.read_grid(raw_root / f"{product}-100m.tif")
        record = data["outputs"][filename]
        audit.checked(path.parent / record["path"], record["sha256"])
        values, _ = base.verified_raster(path.parent, record)
        if (
            values.shape[0] != 1
            or record["raw_unit"] != units["raw_unit"]
            or not np.array_equal(values[0].filled(-9999), raw[product].filled(-9999))
        ):
            raise ValueError("Encoded canopy grid differs from the unmodified source values")
        encoded[product] = values[0].filled(-9999).astype("float32")
    domain = arrays["study_domain_mask.tif"].astype(bool)
    quality, _ = canopy_data.canopy_quality(raw, domain)
    if any(data["qc"].get(key) != value for key, value in quality.items()):
        raise ValueError("Canopy QC record differs from actual source values")
    initial = arrays["initial_perimeter_mask.tif"].astype(bool)
    density_only = (
        (raw["CC"].data == 0)
        & (raw["CH"].data == 0)
        & (raw["CBH"].data == 0)
        & (raw["CBD"].data > 0)
    )
    if data["qc"]["initial_density_without_cover_or_height_cells"] != int(
        (density_only & initial).sum()
    ):
        raise ValueError("Initial canopy inconsistency count changed")
    return data, encoded


def prepare_case(original_case: Path, case: Path, canopy: dict, crown: int) -> dict:
    if crown not in (0, 1):
        raise ValueError("Only the predeclared crown switch is supported")
    case.mkdir()
    shutil.copytree(original_case / "inputs", case / "inputs")
    (case / "outputs").mkdir()
    (case / "scratch").mkdir()
    landscape = case / "inputs/landscape.tif"
    with rasterio.open(landscape) as source:
        values, profile = source.read(), source.profile
    if values.shape != (8, *base.SHAPE) or profile["nodata"] != -9999:
        raise ValueError("Expected original eight-band landscape")
    unchanged = values[:4].copy()
    for band, product in enumerate(("CC", "CH", "CBH", "CBD"), 4):
        values[band] = canopy[product]
    with rasterio.open(landscape, "w", **profile) as target:
        target.write(values)
    with rasterio.open(landscape) as source:
        if not np.array_equal(source.read()[:4], unchanged):
            raise ValueError("Terrain or surface fuel changed while inserting canopy")
    namelist = case / "inputs/elmfire.data"
    text = namelist.read_text()
    if text.count("CROWN_FIRE_MODEL = 0") != 1:
        raise ValueError("Unexpected original crown model setting")
    namelist.write_text(text.replace("CROWN_FIRE_MODEL = 0", f"CROWN_FIRE_MODEL = {crown}"))
    old_hashes, new_hashes = audit.hashes(original_case / "inputs"), audit.hashes(case / "inputs")
    if set(old_hashes) != set(new_hashes) or any(
        old_hashes[key] != new_hashes[key]
        for key in old_hashes
        if key not in ("landscape.tif", "elmfire.data")
    ):
        raise ValueError("An input beyond the canopy bands/crown switch changed")
    return new_hashes


def trace_coverage(case: Path) -> dict:
    conservative = common.inspect_coverage(case)
    text = (case / "run.log").read_text()
    records = []
    for match in re.finditer(r"BONGHWA_RK2_ENDPOINT\s+([^\r\n]+)", text):
        values = [float(value) for value in match.group(1).split()]
        if len(values) != 5 or not np.isfinite(values).all():
            raise ValueError("Malformed post-RK2 trace")
        start, dt, end, stop, phi_change = values
        if (
            not 0 < dt <= 30.000001
            or abs(start + dt - end) > 1e-6
            or stop != 21600
            or end > stop + 1e-4
            or phi_change < 0
        ):
            raise ValueError("Inconsistent integration endpoint trace")
        records.append(
            {
                "start_seconds": start,
                "dt_seconds": dt,
                "integrated_until_seconds": end,
                "tstop_seconds": stop,
                "maximum_phi_change": phi_change,
                "log_offset": match.start(),
            }
        )
    if any(
        abs(a["integrated_until_seconds"] - b["start_seconds"]) > 1e-6
        for a, b in zip(records, records[1:], strict=False)
    ):
        raise ValueError("Non-contiguous integration endpoint trace")
    result = conservative | {
        "conservative_original_inspection": copy.deepcopy(conservative),
        "post_rk2_endpoint_records": records,
        "trace_completion_tolerance_seconds": 1e-4,
    }
    if not records:
        if conservative["full_horizon_completed"]:
            raise ValueError("Diagnostic binary must trace a claimed full final horizon")
        return result
    final = records[-1]
    stops = list(re.finditer(r"STOPPING:[^\r\n]*", text))
    if any(stop.start() < final["log_offset"] for stop in stops):
        raise ValueError("A stop was logged before the final integration endpoint")
    if abs(final["integrated_until_seconds"] - 21600) <= 1e-4:
        if len(stops) > 1 or any(
            stop.group().strip() != "STOPPING: FIRE FRONT PROPAGATION STALLED" for stop in stops
        ):
            raise ValueError("Unexpected stop reason at the final integration endpoint")
        result.update(
            {
                "full_horizon_completed": True,
                "early_stop_detected": False,
                "early_stop_reason": None,
                "engine_stall_warning_present": bool(stops),
                "covered_until_seconds_lower_bound": 21600.0,
                "horizon_completed": {key: True for key in base.HORIZONS},
                "coverage_time_method": "Verified post-RK2 T+DT reaches fixed TSTOP",
                "note": "Actual RK2 endpoint; filename and rounded stats alone are insufficient",
            }
        )
    return result


def compare_baseline(evaluation: dict, baseline: dict) -> dict:
    if baseline["baseline"] != evaluation["baseline"]:
        raise ValueError("Original and canopy studies do not share the same reference baseline")
    comparison = {}
    for scenario in FIXED_CASES:
        name = scenario["id"]
        comparison[name] = {}
        for horizon in base.HORIZONS:
            current = evaluation["cases"][name][horizon]
            prior = baseline["cases"][scenario["baseline_id"]][horizon]
            a, b = current.get("metrics"), prior.get("metrics")
            comparison[name][horizon] = {
                "canopy": current,
                "original_no_canopy": prior,
                "new_growth_iou_delta": a["new_growth_iou"] - b["new_growth_iou"]
                if a and b and a["new_growth_iou"] is not None and b["new_growth_iou"] is not None
                else None,
                "new_growth_recall_delta": a["new_growth_recall"] - b["new_growth_recall"]
                if a
                and b
                and a["new_growth_recall"] is not None
                and b["new_growth_recall"] is not None
                else None,
            }
    return comparison


def execute(
    original: Path,
    diagnostic: Path,
    diagnostic_sha: str,
    canopy_path: Path,
    baseline_path: Path,
    output: Path,
    timeout: int = 300,
) -> dict:
    if not 1 <= timeout <= 300:
        raise ValueError("Timeout must be bounded at300s per case")
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = FLAGS | {
        "status": "running",
        "stage": "verify_inputs",
        "cases": [],
        "future_labels_read_in_this_run": False,
    }
    try:
        study, engine = audit.verify_diagnostic(original, diagnostic, diagnostic_sha)
        terrain_path = Path(study["plan"]["references"]["terrain"]["path"])
        weather_path = Path(study["plan"]["references"]["weather"]["path"])
        terrain, arrays, _ = base.verify_terrain(terrain_path)
        base.verify_weather(weather_path, arrays["study_domain_mask.tif"].astype(bool))
        canopy_manifest, canopy = verify_canopy(canopy_path, terrain_path, arrays)
        binary = diagnostic / "bin/elmfire_1.1"
        references = {
            "original_report": {
                "path": str(original / "report.json"),
                "sha256": common.sha256(original / "report.json"),
            },
            "canopy_manifest": {"path": str(canopy_path), "sha256": common.sha256(canopy_path)},
            "diagnostic_report": {
                "path": str(diagnostic / "report.json"),
                "sha256": diagnostic_sha,
            },
            "runner": {
                "path": str(Path(__file__).resolve()),
                "sha256": common.sha256(Path(__file__)),
            },
            "canopy_code": {
                "path": str(Path(canopy_data.__file__).resolve()),
                "sha256": common.sha256(Path(canopy_data.__file__)),
            },
            "baseline_evaluation_hash_only_before_runs": {
                "path": str(baseline_path),
                "sha256": common.sha256(baseline_path),
            },
        }
        plan = FLAGS | {
            "study": "walker2019_actual_canopy_crown_moisture_ablation_v1",
            "created_at_utc": datetime.now(UTC).isoformat(),
            "fixed_cases": FIXED_CASES,
            "references": references,
            "source_commit": audit.COMMIT,
            "binary_version": "ELMFIRE1.1 + output-only final-RK2 trace",
            "binary_sha256": engine["diagnostic_binary_sha256"],
            "diagnostic_source_patch_sha256": engine["source_patch_sha256"],
            "engine_license": engine["license"],
            "engine_license_urls": engine["license_urls"],
            "engine_license_sha256": engine["license_sha256"],
            "canopy_license": canopy_manifest["license"],
            "canopy_qc": canopy_manifest["qc"],
            "canopy_sources": canopy_manifest["sources"],
            "original_physical_plan": study["plan"],
            "changes_from_original": [
                "Actual LF2016 CC/CH/CBH/CBD in landscape bands5..8",
                "Predeclared crown switch0or1",
                "Output-only engine diagnostic trace",
            ],
            "unchanged": [
                "Initial140cell mask",
                "Surface fuel/elevation/slope/aspect",
                "Seven HRRR wind fields and true-to-grid rotation",
                "Dead/live/foliar moisture",
                "dt5/dtmax30/CFL0.2",
                "Spottingoff/suppressionoff",
                "All spread adjustment multipliers remain1",
            ],
            "numerics": {"cpu_threads": 1, "case_timeout_seconds": timeout},
            "assumptions": {
                "live_herb_percent": 60,
                "live_woody_percent": 90,
                "foliar_percent": 90,
                "crown_ratio": 1.0,
                "critical_canopy_cover": 0.39,
                "crown_spread_limit_ft_min": 250,
                "moisture_observed": False,
            },
            "limitations": canopy_manifest["limitations"]
            + [
                "Walker labels were exposed during development; this is not held-out evaluation",
                "Density-only source cells retained including1initialcell; no invented canopy",
                "Crown model cannot create validated personal or Korean risk probabilities",
                "All six cases are reported; improved train-event score is not transfer evidence",
            ],
        }
        common.write_json(output / "plan.json", plan)
        report.update(plan=plan, plan_sha256=common.sha256(output / "plan.json"), stage="simulate")
        common.write_json(output / "report.json", report)
        prefix = Path(engine["environment_overrides"]["CONDA_PREFIX"])
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
        arrivals = {}
        for scenario in FIXED_CASES:
            case = output / scenario["id"]
            item = copy.deepcopy(scenario) | FLAGS | {"status": "running"}
            report["cases"].append(item)
            case_start = time.monotonic()
            try:
                item["input_sha256"] = prepare_case(
                    original / scenario["baseline_id"], case, canopy, scenario["crown_fire_model"]
                )
                common.run_command(
                    ["nice", "-n", "10", str(binary), "./inputs/elmfire.data"], case, env, timeout
                )
                if "End of simulation reached successfully" not in (case / "run.log").read_text():
                    raise ValueError("Engine did not complete successfully")
                bils = list((case / "outputs").glob("time_of_arrival*.bil"))
                if len(bils) != 1:
                    raise ValueError("Expected one final arrival raster")
                target = bils[0].with_suffix(".tif")
                common.run_command(
                    [
                        str(prefix / "bin/gdal_translate"),
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
                item["coverage"] = trace_coverage(case)
                stats, raw = base.inspect_arrival(target, arrays, item["coverage"])
                item.update(stats)
                arrivals[scenario["id"]] = raw
                audit.verify_hashes(case / "inputs", item["input_sha256"])
                item["status"] = (
                    "complete" if all(stats["horizon_available"].values()) else "censored"
                )
            except Exception as error:
                item.update(status="failed", error_type=type(error).__name__, error=str(error))
            item["elapsed_seconds"] = round(time.monotonic() - case_start, 3)
            common.write_json(output / "report.json", report)
            print(scenario["id"] + ": " + item["status"], flush=True)
        report["stage"] = "freeze_inputs_before_label_evaluation"
        audit.checked(output / "plan.json", report["plan_sha256"])
        for record in references.values():
            audit.checked(Path(record["path"]), record["sha256"])
        for case in report["cases"]:
            audit.verify_hashes(output / case["id"] / "inputs", case["input_sha256"])
            if case["status"] in ("complete", "censored"):
                audit.checked(Path(case["arrival_path"]), case["arrival_sha256"])
        audit.verify_diagnostic(original, diagnostic, diagnostic_sha)
        verify_canopy(canopy_path, terrain_path, arrays)
        receipt = FLAGS | {
            "cases_attempted": len(report["cases"]),
            "cases": report["cases"],
            "future_labels_read_in_this_run": False,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "plan_sha256": report["plan_sha256"],
            "input_manifest_sha256": common.sha256(terrain_path),
            "source_archive_sha256": terrain["sources"]["gofer"]["archive_sha256"],
        }
        common.write_json(output / "fit-receipt.json", receipt)
        report["fit_receipt_sha256"] = common.sha256(output / "fit-receipt.json")
        report["stage"] = "evaluate_training_event"
        report["future_labels_read_in_this_run"] = True
        # Reuse the original initial-input-linked receipt for the unchanged truth contract.
        truth_path = Path(study["plan"]["truth_manifest_path_not_yet_opened"])
        truth_sha = common.sha256(truth_path)
        baseline = audit.read_json(baseline_path)
        if baseline["truth_manifest_sha256"] != truth_sha:
            raise ValueError("Baseline uses different reconstructed reference labels")
        _, truth = base.load_truth(truth_path, arrays, original / "fit-receipt.json")
        evaluation = base.evaluate(report["cases"], arrivals, truth, arrays) | FLAGS
        evaluation.update(
            {
                "comparison_to_original": compare_baseline(evaluation, baseline),
                "truth_manifest_sha256": truth_sha,
                "fit_receipt_sha256": report["fit_receipt_sha256"],
                "baseline_evaluation_sha256": common.sha256(baseline_path),
                "all_six_predeclared_cases_reported": True,
            }
        )
        audit.checked(truth_path, truth_sha)
        base.load_truth(truth_path, arrays, original / "fit-receipt.json")
        audit.checked(output / "fit-receipt.json", report["fit_receipt_sha256"])
        for case in report["cases"]:
            if case["status"] in ("complete", "censored"):
                audit.checked(Path(case["arrival_path"]), case["arrival_sha256"])
        common.write_json(output / "evaluation.json", evaluation)
        report.update(
            status="complete"
            if all(c["status"] == "complete" for c in report["cases"])
            else "censored"
            if all(c["status"] in ("complete", "censored") for c in report["cases"])
            else "partial_failure",
            evaluation_sha256=common.sha256(output / "evaluation.json"),
        )
    except Exception as error:
        report.update(status="failed", error_type=type(error).__name__, error=str(error))
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    common.write_json(output / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("original", "diagnostic", "canopy", "baseline-evaluation", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--diagnostic-report-sha256", required=True)
    parser.add_argument("--case-timeout", type=int, default=300)
    args = parser.parse_args()
    report = execute(
        args.original.resolve(),
        args.diagnostic.resolve(),
        args.diagnostic_report_sha256,
        args.canopy.resolve(),
        args.baseline_evaluation.resolve(),
        args.output.resolve(),
        args.case_timeout,
    )
    print(json.dumps({key: report[key] for key in ("status", "stage", "elapsed_seconds")}))
    return 0 if report["status"] in ("complete", "censored") else 1


if __name__ == "__main__":
    raise SystemExit(main())
