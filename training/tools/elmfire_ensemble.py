#!/usr/bin/env python3
"""Nine fixed synthetic ELMFIRE scenarios; fractions are NOT calibrated probabilities.

Run with the probe's isolated Python environment. All source inputs are verified
against the completed probe and copied. This never evaluates a real user location.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rasterio

HORIZONS = {"1h": 3600, "3h": 10800, "6h": 21600}
SPEEDS_MPH = (10, 15, 20)
DIRECTIONS_DEG = (340, 0, 20)
PROBES = (
    ("ignition_neighborhood", 0.0, 3000.0),
    ("south_1500m", 0.0, 1500.0),
    ("southwest", -1500.0, 1500.0),
    ("southeast", 1500.0, 1500.0),
    ("north_1500m", 0.0, 4500.0),
)


def sha256(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def frozen_plan(probe_report: Path, receipt: dict) -> dict:
    return {
        "study": "synthetic_3x3_wind_sensitivity_v1",
        "simulation_only": True,
        "operational_use": False,
        "probability": None,
        "personal_risk_validated": False,
        "source_probe_report": str(probe_report.resolve()),
        "source_probe_report_sha256": sha256(probe_report),
        "source_commit": receipt["source_commit"],
        "source_binary_sha256": receipt["binary_sha256"],
        "source_inputs_sha256": receipt["input_sha256"],
        "license": receipt["license"],
        "license_scope": receipt["license_scope"],
        "created_at": datetime.now(UTC).isoformat(),
        "stop_seconds": 21600,
        "horizon_seconds": HORIZONS,
        "cpu_threads_per_case": 1,
        "sequential_cases": True,
        "scenario_interpretation": (
            "Equal counts over nine predetermined synthetic wind combinations. "
            "Not samples from a real uncertainty distribution, not calibrated probability."
        ),
        "grid": {
            "crs": "EPSG:32610",
            "units": "metres",
            "cellsize_m": 30,
            "coordinates": "Artificial tutorial coordinates, NOT actual geographic user locations",
        },
        "scenario_plan": [
            {
                "id": f"ws{speed:02d}_wd{direction:03d}",
                "wind_speed_mph": speed,
                "wind_direction_deg": direction,
            }
            for speed, direction in itertools.product(SPEEDS_MPH, DIRECTIONS_DEG)
        ],
        "probe_locations": [{"id": name, "x_m": x, "y_m": y} for name, x, y in PROBES],
        "fraction_rule": (
            "Only if all nine scenarios succeed and none has arrival <=0 at the probe: "
            "count(0 < arrival_seconds <= horizon) / 9. Otherwise null. "
            "Unburned within the complete simulation is distinct from a failed scenario."
        ),
        "validation_scope": "Synthetic sensitivity only; no Korean/physical validation",
    }


def verify_probe(path: Path) -> tuple[dict, Path, Path]:
    receipt = json.loads(path.read_text())
    if receipt.get("status") != "synthetic_probe_passed":
        raise ValueError("Requires a successfully completed synthetic probe")
    if receipt.get("simulation_only") is not True or receipt.get("operational_use") is not False:
        raise ValueError("Source receipt must be explicitly non-operational simulation")
    binary = Path(receipt["binary_path"]).resolve()
    if sha256(binary) != receipt["binary_sha256"]:
        raise ValueError("ELMFIRE binary has changed since its successful probe")
    inputs = path.parent / "tutorials/01-constant-wind/inputs"
    actual_names = {item.name for item in inputs.iterdir() if item.is_file()}
    if actual_names != set(receipt["input_sha256"]):
        raise ValueError("Probe input file set has changed")
    for name, expected in receipt["input_sha256"].items():
        if sha256(inputs / name) != expected:
            raise ValueError(f"Probe input changed: {name}")
    return receipt, binary, inputs


def set_stop_time(text: str) -> str:
    text, count = re.subn(r"(?m)^\s*SIMULATION_TSTOP\s*=.*$", "SIMULATION_TSTOP = 21600.0", text)
    if count != 1:
        raise ValueError("Expected exactly one stop time in the verified tutorial namelist")
    return text


def replace_constant_raster(path: Path, value: float) -> None:
    with rasterio.open(path) as original:
        profile = original.profile
        values = original.read(masked=True)
    if values.dtype.kind != "f":
        raise ValueError("Expected floating-point tutorial wind rasters")
    replacement = np.where(np.ma.getmaskarray(values), values.data, value).astype(values.dtype)
    temporary = path.with_name(path.stem + ".rewrite.tif")
    with rasterio.open(temporary, "w", **profile) as output:
        output.write(replacement)
    temporary.replace(path)


def run_command(command: list[str], cwd: Path, env: dict, log: Path, timeout: int) -> None:
    with log.open("a") as stream:
        stream.write(json.dumps({"argv": command}) + "\n")
        stream.flush()
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise
    if returncode:
        raise RuntimeError(f"Command exit {returncode}; inspect {log.name}")


def arrival_probes(path: Path, reference: Path) -> list[dict]:
    with rasterio.open(reference) as base, rasterio.open(path) as result:
        if (
            result.shape != base.shape
            or result.crs != base.crs
            or result.transform != base.transform
            or result.count != 1
        ):
            raise ValueError("Arrival grid differs from the synthetic input grid")
        data = result.read(1, masked=True)
        raw = data.filled(np.nan)
        valid = ~np.ma.getmaskarray(data)
        if np.any(valid & ~np.isfinite(raw)):
            raise ValueError("Non-finite unmasked arrival values")
        arrived = valid & (raw >= 0)
        if arrived.sum() <= 1 or np.any(raw[arrived] > 21600 + 30):
            raise ValueError("Invalid synthetic arrival range or no spread")
        points = []
        for name, x, y in PROBES:
            row, column = result.index(x, y)
            if not (0 <= row < result.height and 0 <= column < result.width):
                raise ValueError(f"Probe outside synthetic domain: {name}")
            center_x, center_y = result.xy(row, column)
            value = float(raw[row, column]) if arrived[row, column] else None
            state = (
                "unreached_within_horizon"
                if value is None
                else ("initially_reached" if value <= 0 else "future_arrival")
            )
            points.append(
                {
                    "id": name,
                    "requested_xy_m": [x, y],
                    "sampled_cell_center_xy_m": [float(center_x), float(center_y)],
                    "row": row,
                    "column": column,
                    "arrival_seconds": value,
                    "state": state,
                }
            )
        return points


def aggregate(cases: list[dict], expected_count: int = 9) -> list[dict]:
    successful = [case for case in cases if case["status"] == "complete"]
    complete = len(cases) == expected_count and len(successful) == expected_count
    result = []
    for name, x, y in PROBES:
        observations = [
            next(point for point in case["probes"] if point["id"] == name) for case in successful
        ]
        initial = sum(point["state"] == "initially_reached" for point in observations)
        reason = (
            "partial_or_failed_ensemble"
            if not complete
            else ("initially_reached_requires_current_state_handling" if initial else None)
        )
        counts = {
            key: sum(
                point["arrival_seconds"] is not None and 0 < point["arrival_seconds"] <= seconds
                for point in observations
            )
            for key, seconds in HORIZONS.items()
        }
        result.append(
            {
                "id": name,
                "synthetic_xy_m": [x, y],
                "simulation_only": True,
                "probability": None,
                "operational_use": False,
                "completed_scenarios": len(successful),
                "planned_scenarios": expected_count,
                "initially_reached_scenarios": initial,
                "future_arrival_counts": counts,
                "scenario_fraction": {
                    key: count / expected_count if reason is None else None
                    for key, count in counts.items()
                },
                "unavailable_reason": reason,
            }
        )
    return result


def execute(probe_path: Path, output: Path, case_timeout: int) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "preflight",
        "simulation_only": True,
        "probability": None,
        "operational_use": False,
        "cases": [],
    }
    started = time.monotonic()
    try:
        receipt, binary, original_inputs = verify_probe(probe_path)
        plan = frozen_plan(probe_path, receipt)
        write_json(output / "plan.json", plan)  # Must exist before generating/running any scenario.
        report.update({"plan_sha256": sha256(output / "plan.json"), "status": "running"})
        write_json(output / "report.json", report)
        prefix = binary.parent.parent / "env"
        env = os.environ.copy()
        env.update(
            {
                "PATH": str(prefix / "bin") + os.pathsep + env.get("PATH", ""),
                "CONDA_PREFIX": str(prefix),
                "GDAL_DATA": str(prefix / "share/gdal"),
                "PROJ_DATA": str(prefix / "share/proj"),
                "CUDA_VISIBLE_DEVICES": "",
                "OMP_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
            }
        )
        translate = prefix / "bin/gdal_translate"
        if not translate.is_file():
            raise ValueError("Verified probe's isolated GDAL executable is missing")
        for scenario in plan["scenario_plan"]:
            item = scenario | {"status": "running"}
            report["cases"].append(item)
            case_start = time.monotonic()
            case = output / scenario["id"]
            try:
                case.mkdir()
                shutil.copytree(original_inputs, case / "inputs")
                (case / "scratch").mkdir()
                (case / "outputs").mkdir()
                replace_constant_raster(case / "inputs/ws.tif", scenario["wind_speed_mph"])
                replace_constant_raster(case / "inputs/wd.tif", scenario["wind_direction_deg"])
                config = case / "inputs/elmfire.data"
                config.write_text(set_stop_time(config.read_text()))
                item["input_sha256"] = {
                    p.name: sha256(p) for p in sorted((case / "inputs").iterdir()) if p.is_file()
                }
                log = case / "run.log"
                run_command(
                    ["nice", "-n", "10", str(binary), "./inputs/elmfire.data"],
                    case,
                    env,
                    log,
                    case_timeout,
                )
                if "End of simulation reached successfully" not in log.read_text(errors="replace"):
                    raise ValueError("Simulation did not report successful completion")
                bils = list((case / "outputs").glob("time_of_arrival*.bil"))
                if len(bils) != 1:
                    raise ValueError("Expected exactly one final arrival output")
                target = bils[0].with_suffix(".tif")
                run_command(
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
                    log,
                    60,
                )
                item["probes"] = arrival_probes(target, original_inputs / "ws.tif")
                item["arrival_sha256"] = sha256(target)
                item["status"] = "complete"
            except Exception as error:
                item.update(
                    {"status": "failed", "error_type": type(error).__name__, "error": str(error)}
                )
            item["elapsed_seconds"] = round(time.monotonic() - case_start, 3)
            report["probes"] = aggregate(report["cases"])
            write_json(output / "report.json", report)
            print(f"{scenario['id']}: {item['status']}", flush=True)
        # Recheck the source receipt's input and binary integrity after all runs.
        verify_probe(probe_path)
        report["status"] = (
            "complete"
            if all(item["status"] == "complete" for item in report["cases"])
            else "partial_failure"
        )
    except Exception as error:
        report.update({"status": "failed", "error_type": type(error).__name__, "error": str(error)})
        report["probes"] = aggregate(report["cases"])
        # A failed final integrity check invalidates even completed case fractions.
        for point in report["probes"]:
            point["scenario_fraction"] = dict.fromkeys(HORIZONS)
            point["unavailable_reason"] = "study_preflight_or_integrity_failure"
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["finished_at"] = datetime.now(UTC).isoformat()
    write_json(output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case-timeout", type=int, default=300)
    args = parser.parse_args()
    if not 1 <= args.case_timeout <= 900:
        parser.error("--case-timeout must be between 1 and 900 seconds")
    report = execute(args.probe_report.resolve(), args.output.resolve(), args.case_timeout)
    print(f"Synthetic study {report['status']}: {args.output / 'report.json'}")
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())
