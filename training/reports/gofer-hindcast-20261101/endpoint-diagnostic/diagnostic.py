#!/usr/bin/env python3
"""Output-only endpoint audit; never changes original source, cases or evaluation."""

import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time
from datetime import datetime, timezone

import numpy as np
import rasterio

COMMIT = "f4927b7ce68cb74eb0eb117085cc920782c8644e"
LEVEL_SHA = "48f444ed3547236ea1ebb37f14d862e94bac98feecfdc38553c4df232f771374"
BINARY_SHA = "f57750977084080f692cc51498f16f21197ee34de767e11d6407749bb52f947b"
ANCHOR = "      ENDDO !ISTEP=1,2\n"
ADDED = """
      ! BONGHWA diagnostic only: report the completed RK2 step without mutation.
      IF (T .GE. REAL(TSTOP,8) - 60.0_8) THEN
         WRITE(*,'(A,5(ES24.16,1X))') 'BONGHWA_RK2_ENDPOINT ', T, REAL(DT,8), &
            T + REAL(DT,8), REAL(TSTOP,8), REAL(MAXVAL(ABS(PHIP - phi_previous)),8)
         CALL FLUSH(6)
      ENDIF
"""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hashes(folder):
    return {
        str(p.relative_to(folder)): sha(p)
        for p in sorted(Path(folder).rglob("*"))
        if p.is_file()
    }


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def patch(text):
    if text.count(ANCHOR) != 1:
        raise ValueError("Expected exactly one RK2 completion anchor")
    return text.replace(ANCHOR, ANCHOR + ADDED)


def parse_endpoints(text):
    rows = []
    for match in re.finditer(r"BONGHWA_RK2_ENDPOINT\s+([^\r\n]+)", text):
        values = [float(s) for s in match.group(1).split()]
        if len(values) != 5 or not all(np.isfinite(values)):
            raise ValueError("Invalid endpoint diagnostic row")
        rows.append(dict(zip(
            ("start_seconds", "dt_seconds", "integrated_until_seconds", "tstop_seconds",
             "maximum_phi_change"), values, strict=True
        )))
    if not rows:
        raise ValueError("No endpoint diagnostic records")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    original, work, output = (p.resolve() for p in (args.original, args.work, args.output))
    output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, output / "diagnostic.py")
    source = work / ("source-" + COMMIT)
    copied_source = output / "source"
    prefix = work / "env"
    install = output / "bin"
    report = {
        "status": "running", "stage": "verify_original", "simulation_only": True,
        "operational_use": False, "probability": None, "evaluation_changed": False,
        "source_commit": COMMIT, "original": str(original), "cases": [], "commands": [],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "license": "AGPL-3.0 with Commons Clause; private research evaluation only",
        "license_urls": [f"https://github.com/lautenberger/elmfire/blob/{COMMIT}/{s}"
                         for s in ("LICENSE.md", "COMMERCIAL_LICENSE.md")],
    }
    started = time.monotonic()
    try:
        if sha(source / "build/source/elmfire_level_set.f90") != LEVEL_SHA:
            raise ValueError("Original level-set source SHA mismatch")
        if sha(work / "bin/elmfire_1.1") != BINARY_SHA:
            raise ValueError("Original binary SHA mismatch")
        original_report = json.loads((original / "report.json").read_text())
        if original_report["plan"]["source_commit"] != COMMIT:
            raise ValueError("Original study source mismatch")
        frozen_original = hashes(original)
        report["original_artifact_sha256"] = frozen_original
        report["original_source_build_sha256"] = hashes(source / "build")
        report["original_binary_sha256"] = BINARY_SHA
        report["script_sha256"] = sha(output / "diagnostic.py")
        report["license_sha256"] = {s: sha(source / s) for s in ("LICENSE.md", "COMMERCIAL_LICENSE.md")}
        write(output / "plan.json", report | {
            "fixed_case_ids": [c["id"] for c in original_report["cases"]],
            "patch_purpose": "Print completed last60s RK2 endpoints and max PHI change only",
            "cpu_threads": 1, "case_timeout_seconds": 300, "build_timeout_seconds": 900,
            "comparison": "All TOA values, masks, metadata and raw BIL bytes against original",
        })
        shutil.copytree(source / "build", copied_source / "build")
        for name in ("VERSION", "LICENSE.md", "COMMERCIAL_LICENSE.md"):
            shutil.copy2(source / name, copied_source / name)
        level = copied_source / "build/source/elmfire_level_set.f90"
        before = level.read_text()
        after = patch(before)
        level.write_text(after)
        delta = "".join(difflib.unified_diff(before.splitlines(keepends=True),
                      after.splitlines(keepends=True), fromfile="original/elmfire_level_set.f90",
                      tofile="diagnostic/elmfire_level_set.f90"))
        (output / "source.patch").write_text(delta)
        report["source_patch_sha256"] = sha(output / "source.patch")
        report["diagnostic_level_set_sha256"] = sha(level)
        install.mkdir()
        env = os.environ.copy() | {
            "PATH": str(prefix / "bin") + os.pathsep + os.environ.get("PATH", ""),
            "CONDA_PREFIX": str(prefix), "GDAL_DATA": str(prefix / "share/gdal"),
            "PROJ_DATA": str(prefix / "share/proj"), "CUDA_VISIBLE_DEVICES": "",
            "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
            "MAKEFLAGS": "-j1", "ELMFIRE_BASE_DIR": str(copied_source),
            "ELMFIRE_INSTALL_DIR": str(install), "ELMFIRE_VER": "1.1",
            "ELMFIRE_SCRATCH_BASE": str(output / "scratch"),
            "ELMFIRE_FCOMPL_MPI_GNU": str(prefix / "bin/mpifort"),
        }
        report["environment_overrides"] = {k: env[k] for k in (
            "CONDA_PREFIX", "GDAL_DATA", "PROJ_DATA", "CUDA_VISIBLE_DEVICES", "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "MAKEFLAGS", "ELMFIRE_BASE_DIR",
            "ELMFIRE_INSTALL_DIR", "ELMFIRE_VER", "ELMFIRE_FCOMPL_MPI_GNU"
        )}
        def run(argv, cwd, log, timeout):
            command = {"argv": argv, "cwd": str(cwd), "timeout_seconds": timeout}
            report["commands"].append(command)
            write(output / "report.json", report)
            with log.open("w") as stream:
                process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stream,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    result = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    raise
            command["exit_code"] = result
            command["log_sha256"] = sha(log)
            if result:
                raise ValueError(f"Command failed; read {log}")

        report["stage"] = "build"
        run(["nice", "-n", "10", "bash", "make_gnu.sh", "fast"],
            copied_source / "build/linux", output / "build.log", 900)
        binary = install / "elmfire_1.1"
        report["diagnostic_binary_sha256"] = sha(binary)
        report["diagnostic_source_build_sha256"] = hashes(copied_source / "build")
        print("Diagnostic build complete", flush=True)
        report["stage"] = "run_identical_cases"
        for original_case in original_report["cases"]:
            case_id = original_case["id"]
            case = output / case_id
            case.mkdir()
            shutil.copytree(original / case_id / "inputs", case / "inputs")
            (case / "outputs").mkdir()
            (case / "scratch").mkdir()
            inputs_before = hashes(case / "inputs")
            if inputs_before != hashes(original / case_id / "inputs"):
                raise ValueError("Copied inputs are not identical")
            run(["nice", "-n", "10", str(binary), "./inputs/elmfire.data"],
                case, case / "run.log", 300)
            text = (case / "run.log").read_text()
            if "End of simulation reached successfully" not in text:
                raise ValueError("Missing engine completion marker")
            endpoints = parse_endpoints(text)
            bils = list((case / "outputs").glob("time_of_arrival*.bil"))
            originals = list((original / case_id / "outputs").glob("time_of_arrival*.bil"))
            if len(bils) != 1 or len(originals) != 1:
                raise ValueError("Expected exactly one arrival raster in each run")
            with rasterio.open(bils[0]) as left, rasterio.open(originals[0]) as right:
                a, b = left.read(1), right.read(1)
                identical = np.array_equal(a, b, equal_nan=True)
                metadata_identical = (left.shape == right.shape and left.transform == right.transform
                                      and left.nodata == right.nodata and left.dtypes == right.dtypes)
                masks_identical = np.array_equal(left.read_masks(1), right.read_masks(1))
                differences = int(np.count_nonzero(a != b))
            unchanged = hashes(case / "inputs") == inputs_before
            item = {"id": case_id, "input_sha256": inputs_before,
                    "inputs_unchanged": unchanged, "endpoint_records": endpoints,
                    "completed_21600_second_rk2": endpoints[-1]["integrated_until_seconds"] == 21600.0,
                    "toa_all_values_identical": bool(identical), "toa_metadata_identical": metadata_identical,
                    "toa_masks_identical": bool(masks_identical), "toa_different_cells": differences,
                    "original_bil_sha256": sha(originals[0]), "diagnostic_bil_sha256": sha(bils[0]),
                    "bil_bytes_identical": sha(originals[0]) == sha(bils[0]),
                    "run_log_sha256": sha(case / "run.log")}
            report["cases"].append(item)
            write(output / "report.json", report)
            if not (identical and metadata_identical and masks_identical and unchanged):
                raise ValueError("Diagnostic changed original numeric result or input")
            print(case_id + ": " + json.dumps(item), flush=True)
        report["stage"] = "verify_original_preserved"
        if frozen_original != hashes(original):
            raise ValueError("Original artifact changed during audit")
        if sha(work / "bin/elmfire_1.1") != BINARY_SHA or hashes(source / "build") != report["original_source_build_sha256"]:
            raise ValueError("Original source or binary changed during audit")
        report["original_artifact_source_binary_preserved"] = True
        report["status"] = "complete"
    except Exception as error:
        report.update(status="failed", error_type=type(error).__name__, error=str(error))
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    write(output / "report.json", report)
    print(json.dumps({k: report[k] for k in ("status", "stage", "elapsed_seconds")}), flush=True)
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
