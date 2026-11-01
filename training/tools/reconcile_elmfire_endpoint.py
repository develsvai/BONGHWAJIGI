#!/usr/bin/env python3
"""Reconcile one audited endpoint without relaxing the shared coverage guard."""

from __future__ import annotations

import argparse
import copy
import difflib
import json
import re
import sys
import time
from pathlib import Path

import elmfire_gofer_hindcast as hindcast
import numpy as np
import rasterio

common = hindcast.common
COMMIT = "f4927b7ce68cb74eb0eb117085cc920782c8644e"
LEVEL_SHA = "48f444ed3547236ea1ebb37f14d862e94bac98feecfdc38553c4df232f771374"
BINARY_SHA = "f57750977084080f692cc51498f16f21197ee34de767e11d6407749bb52f947b"
CASE_IDS = ["moisture_3_4_5", "moisture_6_7_8", "moisture_9_10_11"]
ANCHOR = "      ENDDO !ISTEP=1,2\n"
ADDED = """
      ! BONGHWA diagnostic only: report the completed RK2 step without mutation.
      IF (T .GE. REAL(TSTOP,8) - 60.0_8) THEN
         WRITE(*,'(A,5(ES24.16,1X))') 'BONGHWA_RK2_ENDPOINT ', T, REAL(DT,8), &
            T + REAL(DT,8), REAL(TSTOP,8), REAL(MAXVAL(ABS(PHIP - phi_previous)),8)
         CALL FLUSH(6)
      ENDIF
"""


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def checked(path: Path, digest: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{64}", digest) or common.sha256(path) != digest:
        raise ValueError(f"SHA256 mismatch: {path}")
    return path


def hashes(folder: Path) -> dict:
    return {
        str(path.relative_to(folder)): common.sha256(path)
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def verify_hashes(folder: Path, expected: dict) -> None:
    if not expected or hashes(folder) != expected:
        raise ValueError(f"Artifact file set or SHA256 changed: {folder}")


def validate_instrumentation(before: str, after: str, patch: str) -> None:
    if before.count(ANCHOR) != 1 or after != before.replace(ANCHOR, ANCHOR + ADDED):
        raise ValueError("Diagnostic source is not the exact output-only instrumentation")
    expected = "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile="original/elmfire_level_set.f90",
            tofile="diagnostic/elmfire_level_set.f90",
        )
    )
    if patch != expected:
        raise ValueError("Diagnostic source patch differs from the audited source difference")


def parse_endpoints(text: str) -> list[dict]:
    rows = []
    for match in re.finditer(r"BONGHWA_RK2_ENDPOINT\s+([^\r\n]+)", text):
        values = [float(value) for value in match.group(1).split()]
        if len(values) != 5 or not np.isfinite(values).all():
            raise ValueError("Invalid endpoint diagnostic record")
        rows.append(
            dict(
                zip(
                    (
                        "start_seconds",
                        "dt_seconds",
                        "integrated_until_seconds",
                        "tstop_seconds",
                        "maximum_phi_change",
                    ),
                    values,
                    strict=True,
                )
            )
        )
    if not rows:
        raise ValueError("Missing post-RK2 endpoint diagnostic records")
    for row in rows:
        if (
            not 0 < row["dt_seconds"] <= 30
            or row["start_seconds"] + row["dt_seconds"] != row["integrated_until_seconds"]
            or row["tstop_seconds"] != 21600
            or not 0 <= row["maximum_phi_change"]
            or row["integrated_until_seconds"] > 21600
        ):
            raise ValueError("Inconsistent RK2 endpoint record")
    if any(
        left["integrated_until_seconds"] != right["start_seconds"]
        for left, right in zip(rows, rows[1:], strict=False)
    ):
        raise ValueError("Diagnostic endpoint records are not contiguous")
    last = rows[-1]
    # This exception concerns the witnessed final clipped step of these three cases only.
    if (
        last["start_seconds"] != 21595
        or last["dt_seconds"] != 5
        or last["integrated_until_seconds"] != 21600
        or last["maximum_phi_change"] >= 0.001
    ):
        raise ValueError("Diagnostic does not prove the audited 21600-second final RK2 step")
    stops = list(re.finditer(r"STOPPING:[^\r\n]*", text))
    if len(stops) != 1 or stops[0].group(0).strip() != "STOPPING: FIRE FRONT PROPAGATION STALLED":
        raise ValueError("Unexpected or multiple engine stop reasons")
    last_record = text.rfind("BONGHWA_RK2_ENDPOINT")
    if stops[0].start() < last_record or "End of simulation reached successfully" not in text:
        raise ValueError("Endpoint record must precede the final stall and successful shutdown")
    return rows


def compare_arrivals(left: Path, right: Path) -> dict:
    with rasterio.open(left) as a, rasterio.open(right) as b:
        if (
            a.shape != b.shape
            or a.count != b.count
            or a.transform != b.transform
            or a.crs != b.crs
            or a.nodata != b.nodata
            or a.dtypes != b.dtypes
            or not np.array_equal(a.read(), b.read(), equal_nan=True)
            or not np.array_equal(a.read_masks(), b.read_masks())
        ):
            raise ValueError("Original and diagnostic arrival values, masks or grid differ")
    if common.sha256(left) != common.sha256(right):
        raise ValueError("Original and diagnostic raw BIL bytes differ")
    return {"all_cells_identical": True, "raw_bil_sha256": common.sha256(left)}


def preserve_short_metrics(original: dict, revised: dict) -> None:
    if set(original["cases"]) != set(CASE_IDS) or set(revised["cases"]) != set(CASE_IDS):
        raise ValueError("Expected the same three fixed moisture cases")
    for name in CASE_IDS:
        for horizon in ("1h", "3h"):
            if original["cases"][name][horizon] != revised["cases"][name][horizon]:
                raise ValueError(f"Existing short-horizon metric changed: {name}/{horizon}")
    if original["baseline"] != revised["baseline"]:
        raise ValueError("Original persistence baseline changed")


def verify_diagnostic(original: Path, diagnostic: Path, digest: str) -> tuple[dict, dict]:
    checked(diagnostic / "report.json", digest)
    evidence = read_json(diagnostic / "report.json")
    if (
        evidence.get("status") != "complete"
        or evidence.get("source_commit") != COMMIT
        or evidence.get("original_artifact_source_binary_preserved") is not True
        or evidence.get("simulation_only") is not True
        or evidence.get("operational_use") is not False
        or evidence.get("probability") is not None
        or Path(evidence["original"]).resolve() != original
        or [case["id"] for case in evidence["cases"]] != CASE_IDS
    ):
        raise ValueError("Diagnostic is not the complete fixed three-case audit")
    verify_hashes(original, evidence["original_artifact_sha256"])
    study = read_json(original / "report.json")
    if [case["id"] for case in study["cases"]] != CASE_IDS or study["status"] != "censored":
        raise ValueError("Original study does not match the audited censored three cases")
    checked(original / "plan.json", study["plan_sha256"])
    checked(original / "fit-receipt.json", study["fit_receipt_sha256"])
    if read_json(original / "plan.json") != study["plan"]:
        raise ValueError("Original plan/report disagree")
    for reference in study["plan"]["references"].values():
        checked(Path(reference["path"]), reference["sha256"])
    for name, module_path in (
        ("runner", Path(hindcast.__file__)),
        ("shared_engine_helpers", Path(common.__file__)),
    ):
        checked(module_path, study["plan"]["references"][name]["sha256"])
    common.verify_source(Path(study["plan"]["references"]["probe"]["path"]))
    work = Path(evidence["environment_overrides"]["CONDA_PREFIX"]).parent
    source = work / ("source-" + COMMIT)
    copied = diagnostic / "source"
    verify_hashes(source / "build", evidence["original_source_build_sha256"])
    verify_hashes(copied / "build", evidence["diagnostic_source_build_sha256"])
    checked(work / "bin/elmfire_1.1", BINARY_SHA)
    checked(diagnostic / "bin/elmfire_1.1", evidence["diagnostic_binary_sha256"])
    checked(source / "build/source/elmfire_level_set.f90", LEVEL_SHA)
    checked(copied / "build/source/elmfire_level_set.f90", evidence["diagnostic_level_set_sha256"])
    checked(diagnostic / "source.patch", evidence["source_patch_sha256"])
    checked(diagnostic / "diagnostic.py", evidence["script_sha256"])
    for name, digest in evidence["license_sha256"].items():
        checked(source / name, digest)
        checked(copied / name, digest)
    before = (source / "build/source/elmfire_level_set.f90").read_text()
    after = (copied / "build/source/elmfire_level_set.f90").read_text()
    validate_instrumentation(before, after, (diagnostic / "source.patch").read_text())
    original_build, diag_build = (
        evidence["original_source_build_sha256"],
        evidence["diagnostic_source_build_sha256"],
    )
    if set(original_build) != set(diag_build) or any(
        original_build[name] != diag_build[name]
        for name in original_build
        if name != "source/elmfire_level_set.f90"
    ):
        raise ValueError("A source/build file beyond the output-only patch changed")
    commands = evidence["commands"]
    if len(commands) != 4:
        raise ValueError("Expected one build and exactly three diagnostic runs")
    for index, command in enumerate(commands):
        if command["exit_code"] != 0:
            raise ValueError("Diagnostic command did not complete successfully")
        if index == 0:
            expected_argv = ["nice", "-n", "10", "bash", "make_gnu.sh", "fast"]
            expected_cwd, log = copied / "build/linux", diagnostic / "build.log"
        else:
            expected_argv = [
                "nice",
                "-n",
                "10",
                str(diagnostic / "bin/elmfire_1.1"),
                "./inputs/elmfire.data",
            ]
            expected_cwd = diagnostic / CASE_IDS[index - 1]
            log = expected_cwd / "run.log"
        if command["argv"] != expected_argv or Path(command["cwd"]) != expected_cwd:
            raise ValueError("Unexpected diagnostic build/run command")
        checked(log, command["log_sha256"])
    return study, evidence


def execute(original: Path, diagnostic: Path, digest: str, output: Path) -> dict:
    if (
        output == original
        or output == diagnostic
        or original in output.parents
        or diagnostic in output.parents
    ):
        raise ValueError("Reconciliation output must be separate from the immutable artifacts")
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = hindcast.FLAGS | {
        "status": "running",
        "stage": "verify_diagnostic",
        "cases": [],
        "original_artifact": str(original),
        "diagnostic_artifact": str(diagnostic),
        "diagnostic_report_sha256": digest,
        "parameters_changed": False,
        "simulated_values_changed": False,
        "shared_coverage_guard_changed": False,
        "reconciliation_runner_sha256": common.sha256(Path(__file__)),
    }
    try:
        study, evidence = verify_diagnostic(original, diagnostic, digest)
        original_evaluation = read_json(original / "evaluation.json")
        terrain_path = Path(study["plan"]["references"]["terrain"]["path"])
        terrain, arrays, _ = hindcast.verify_terrain(terrain_path)
        receipt = read_json(original / "fit-receipt.json")
        if (
            receipt["input_manifest_sha256"] != common.sha256(terrain_path)
            or receipt["source_archive_sha256"] != terrain["sources"]["gofer"]["archive_sha256"]
            or receipt["plan_sha256"] != study["plan_sha256"]
        ):
            raise ValueError("Original fit receipt is not linked to the current frozen inputs")
        cases, arrivals = [], {}
        for old, audit in zip(study["cases"], evidence["cases"], strict=True):
            name = old["id"]
            current = diagnostic / name
            prior = original / name
            verify_hashes(prior / "inputs", audit["input_sha256"])
            verify_hashes(current / "inputs", audit["input_sha256"])
            for filename, sha in old["input_sha256"].items():
                checked(prior / "inputs" / filename, sha)
            checked(prior / "run.log", old["coverage"]["run_log_sha256"])
            checked(current / "run.log", audit["run_log_sha256"])
            endpoints = parse_endpoints((current / "run.log").read_text())
            if endpoints != audit["endpoint_records"]:
                raise ValueError("Diagnostic endpoint report disagrees with actual log")
            if (
                any(
                    audit.get(key) is not True
                    for key in (
                        "inputs_unchanged",
                        "completed_21600_second_rk2",
                        "toa_all_values_identical",
                        "toa_metadata_identical",
                        "toa_masks_identical",
                        "bil_bytes_identical",
                    )
                )
                or audit["toa_different_cells"] != 0
            ):
                raise ValueError("Diagnostic does not establish unchanged completed arrivals")
            old_bils, new_bils = (
                list((prior / "outputs").glob("time_of_arrival*.bil")),
                list((current / "outputs").glob("time_of_arrival*.bil")),
            )
            if len(old_bils) != 1 or len(new_bils) != 1:
                raise ValueError("Expected one final raw arrival raster per case")
            checked(old_bils[0], audit["original_bil_sha256"])
            checked(new_bils[0], audit["diagnostic_bil_sha256"])
            identity = compare_arrivals(old_bils[0], new_bils[0])
            arrival = checked(Path(old["arrival_path"]), old["arrival_sha256"])
            conservative = common.inspect_coverage(prior)
            if conservative != old["coverage"] or conservative["horizon_completed"] != {
                "1h": True,
                "3h": True,
                "6h": False,
            }:
                raise ValueError("Original conservative coverage differs from the audited case")
            reconciled = copy.deepcopy(conservative) | {
                "full_horizon_completed": True,
                "covered_until_seconds_lower_bound": 21600.0,
                "horizon_completed": {key: True for key in hindcast.HORIZONS},
                "coverage_time_method": (
                    "Post-RK2 endpoint trace plus byte-identical original arrival"
                ),
                "early_stop_detected": False,
                "early_stop_reason": None,
                "engine_stall_warning_present": True,
                "diagnostic_report_sha256": digest,
                "note": (
                    "This case reached TSTOP before the stall check; no generic guard exception"
                ),
            }
            stats, raw = hindcast.inspect_arrival(arrival, arrays, reconciled)
            item = copy.deepcopy(old) | stats | {"coverage": reconciled}
            item["status"] = "complete" if all(stats["horizon_available"].values()) else "censored"
            cases.append(item)
            arrivals[name] = raw
            report["cases"].append(
                {
                    "id": name,
                    "original_coverage": conservative,
                    "reconciled_coverage": reconciled,
                    "endpoint_records": endpoints,
                    "arrival_identity": identity,
                }
            )
        report["stage"] = "recompute_same_metrics"
        truth_path = Path(study["plan"]["truth_manifest_path_not_yet_opened"])
        truth_sha = original_evaluation["truth_manifest_sha256"]
        checked(truth_path, truth_sha)
        _, truth = hindcast.load_truth(truth_path, arrays, original / "fit-receipt.json")
        revised = hindcast.evaluate(cases, arrivals, truth, arrays)
        preserve_short_metrics(original_evaluation, revised)
        checked(truth_path, truth_sha)
        # Re-open through the same manifest verifier to catch changed truth raster bytes as well.
        hindcast.load_truth(truth_path, arrays, original / "fit-receipt.json")
        verify_diagnostic(original, diagnostic, digest)
        revised.update(
            {
                "truth_manifest_sha256": truth_sha,
                "fit_receipt_sha256": study["fit_receipt_sha256"],
                "original_evaluation_sha256": common.sha256(original / "evaluation.json"),
                "diagnostic_report_sha256": digest,
                "reconciliation": "Only endpoint coverage for the three audited fixed-input cases",
                "parameters_changed": False,
                "simulated_values_changed": False,
                "short_horizon_metrics_exactly_preserved": True,
            }
        )
        common.write_json(output / "evaluation.json", revised)
        report.update(
            {
                "status": "complete",
                "stage": "complete",
                "evaluation_sha256": common.sha256(output / "evaluation.json"),
                "short_horizon_metrics_exactly_preserved": True,
                "original_artifacts_preserved": True,
                "interpretation": (
                    "One retrospective training event; "
                    "no calibrated probability or Korean validation"
                ),
            }
        )
    except Exception as error:
        report.update(status="failed", error_type=type(error).__name__, error=str(error))
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    common.write_json(output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("original", "diagnostic", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--diagnostic-report-sha256", required=True)
    args = parser.parse_args()
    report = execute(
        args.original.resolve(),
        args.diagnostic.resolve(),
        args.diagnostic_report_sha256,
        args.output.resolve(),
    )
    print(json.dumps({key: report[key] for key in ("status", "stage", "elapsed_seconds")}))
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())
