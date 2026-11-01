#!/usr/bin/env python3
"""Build a pinned ELMFIRE in user space and run its unmodified synthetic tutorial.

This is an installation/output smoke test, not Korean fire validation or a
personal risk probability model. It neither publishes an API nor touches Qwen.
The external source remains under its AGPL-3.0 + Commons Clause conditions.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

SOURCE_URL = "https://github.com/lautenberger/elmfire.git"
SOURCE_SHA = "f4927b7ce68cb74eb0eb117085cc920782c8644e"
MAMBA_URL = (
    "https://github.com/mamba-org/micromamba-releases/releases/download/"
    "2.10.0-0/micromamba-linux-64"
)
MAMBA_SHA = "701f39c06f8e6a670a0e186c8479b9e5c0502a2f0cda6cef65d83bdd2875e8bd"
TUTORIAL = "tutorials/01-constant-wind"
DEPENDENCIES = [
    "python=3.12",
    "gdal>=3.8,<3.11",
    "rasterio",
    "numpy>=2,<3",
    "gfortran_linux-64=14",
    "mpich>=4,<5",
    "make",
    "bc",
]


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def plan() -> dict:
    return {
        "purpose": "synthetic_installation_research_probe",
        "simulation_only": True,
        "operational_use": False,
        "personal_risk_validated": False,
        "source_url": SOURCE_URL,
        "source_commit": SOURCE_SHA,
        "tutorial": TUTORIAL,
        "license": "AGPL-3.0 with Commons Clause; commercial use requires separate terms",
        "license_scope": "Private research evaluation only; no hosted/API/product integration",
        "license_urls": [
            f"https://github.com/lautenberger/elmfire/blob/{SOURCE_SHA}/LICENSE.md",
            f"https://github.com/lautenberger/elmfire/blob/{SOURCE_SHA}/COMMERCIAL_LICENSE.md",
        ],
        "bootstrap_url": MAMBA_URL,
        "bootstrap_sha256": MAMBA_SHA,
        "environment_specs": DEPENDENCIES,
        "dependency_reproducibility": (
            "Initial solve is recorded as an explicit package lock; later rebuilds reuse it. "
            "Version ranges alone are not a byte-identical dependency lock."
        ),
        "cpu_threads": 1,
        "gpu_used": False,
        "services_changed": False,
        "case": {"domain_m": 12000, "cellsize_m": 30, "stop_seconds": 19800},
    }


def inspect_arrival(path: Path) -> dict:
    """Reject malformed/no-spread outputs; this does not assess physical accuracy."""
    import numpy as np
    import rasterio

    with rasterio.open(path) as raster:
        values = raster.read(1, masked=True)
        valid = ~np.ma.getmaskarray(values)
        raw = values.filled(np.nan)
        if raster.count != 1 or raster.shape != (400, 400):
            raise ValueError("Official tutorial must produce a one-band 400x400 arrival raster")
        if raster.crs is None or raster.crs.to_epsg() != 32610:
            raise ValueError("Official tutorial CRS must be EPSG:32610")
        if not np.allclose(raster.res, (30, 30)):
            raise ValueError("Official tutorial cell size must be 30m")
        if np.any(valid & ~np.isfinite(raw)):
            raise ValueError("Non-finite unmasked arrival values")
        # ELMFIRE uses negative/no-data values for unburned cells.
        reached = valid & np.isfinite(raw) & (raw >= 0)
        count = int(reached.sum())
        if count <= 1 or count == raw.size:
            raise ValueError("Expected a nontrivial, partially burned synthetic domain")
        maximum = float(raw[reached].max())
        if maximum > 19800 + 30:
            raise ValueError("Arrival exceeds the fixed tutorial simulation horizon")
        return {
            "file": path.name,
            "sha256": digest(path),
            "shape": list(raster.shape),
            "crs": raster.crs.to_string(),
            "cellsize_m": list(raster.res),
            "reached_cells": count,
            "total_cells": int(raw.size),
            "min_arrival_seconds": float(raw[reached].min()),
            "max_arrival_seconds": maximum,
            "meaning": "Synthetic fire arrival time, not real-world risk probability",
        }


class Probe:
    def __init__(self, work_root: Path, output: Path):
        self.work = work_root.resolve()
        self.output = output.resolve()
        self.output.mkdir(parents=True, exist_ok=False)
        self.report = plan() | {"status": "running", "stages": [], "started_at": utc_now()}
        self.stage = "initializing"
        self.started = time.monotonic()
        self.env = os.environ.copy()
        self.env.update(
            {
                "CUDA_VISIBLE_DEVICES": "",
                "OMP_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
                "MAKEFLAGS": "-j1",
                "MAMBA_ROOT_PREFIX": str(self.work / "mamba-root"),
                "MAMBA_NO_BANNER": "1",
                "PYTHONNOUSERSITE": "1",
            }
        )

    def save(self) -> None:
        self.report["elapsed_seconds"] = round(time.monotonic() - self.started, 3)
        self.report["current_stage"] = self.stage
        atomic_json(self.output / "report.json", self.report)

    @contextlib.contextmanager
    def phase(self, name: str):
        self.stage = name
        item = {"name": name, "started_at": utc_now(), "status": "running"}
        self.report["stages"].append(item)
        self.save()
        start = time.monotonic()
        print(f"[{utc_now()}] {name}", flush=True)
        try:
            yield
        except BaseException:
            item["status"] = "failed"
            raise
        else:
            item["status"] = "complete"
        finally:
            item["elapsed_seconds"] = round(time.monotonic() - start, 3)
            self.save()

    def command(self, argv: list[str], *, cwd: Path | None = None, timeout: int = 900) -> str:
        logfile = self.output / f"{self.stage}.log"
        with logfile.open("a") as stream:
            stream.write(json.dumps({"argv": argv, "cwd": str(cwd or self.work)}) + "\n")
            stream.flush()
            process = subprocess.Popen(
                argv,
                cwd=cwd or self.work,
                env=self.env,
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
            raise RuntimeError(f"Command exited {returncode}; see {logfile.name}")
        return logfile.read_text(errors="replace")

    def execute(self) -> None:
        with self.phase("platform"):
            if platform.system() != "Linux" or platform.machine() not in {"x86_64", "amd64"}:
                raise RuntimeError(
                    "This pinned compiler/bootstrap probe supports Linux x86_64 only"
                )
            for name in ["git", "bash", "nice"]:
                if not shutil.which(name):
                    raise RuntimeError(f"Required host utility is missing: {name}")
            self.report["platform"] = platform.platform()
            self.work.mkdir(parents=True, exist_ok=True)

        source = self.work / f"source-{SOURCE_SHA}"
        with self.phase("source_and_license"):
            if not source.exists():
                source.mkdir()
                self.command(["git", "init", "--quiet"], cwd=source)
                self.command(["git", "remote", "add", "origin", SOURCE_URL], cwd=source)
            # Fetch precisely the fixed object, never a moving branch.
            self.command(["git", "fetch", "--depth", "1", "origin", SOURCE_SHA], cwd=source)
            self.command(["git", "checkout", "--detach", SOURCE_SHA], cwd=source)
            actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True)
            if actual.strip() != SOURCE_SHA:
                raise RuntimeError("Source commit verification failed")
            self.command(["git", "diff", "--exit-code"], cwd=source)
            licenses = {}
            for name in ["LICENSE.md", "COMMERCIAL_LICENSE.md"]:
                shutil.copy2(source / name, self.output / name)
                licenses[name] = digest(source / name)
            self.report["license_sha256"] = licenses
            self.report["source_version"] = (source / "VERSION").read_text().strip()

        mamba = self.work / "micromamba-2.10.0"
        with self.phase("bootstrap"):
            if not mamba.exists():
                temporary = mamba.with_suffix(".download")
                with urllib.request.urlopen(MAMBA_URL, timeout=120) as response:
                    with temporary.open("wb") as stream:
                        shutil.copyfileobj(response, stream)
                if digest(temporary) != MAMBA_SHA:
                    raise RuntimeError("Micromamba download SHA256 mismatch")
                temporary.replace(mamba)
                mamba.chmod(0o700)
            if digest(mamba) != MAMBA_SHA:
                raise RuntimeError("Existing micromamba SHA256 mismatch")

        prefix = self.work / "env"
        package_lock = self.work / "environment.explicit.txt"
        with self.phase("environment"):
            if not (prefix / "conda-meta/history").exists():
                args = [str(mamba), "--no-rc", "create", "-y", "-p", str(prefix)]
                if package_lock.exists():
                    args += ["-f", str(package_lock)]
                else:
                    args += ["--override-channels", "-c", "conda-forge", *DEPENDENCIES]
                self.command(args, timeout=1800)
            explicit = subprocess.check_output(
                [str(mamba), "--no-rc", "list", "-p", str(prefix), "--explicit"],
                env=self.env,
                text=True,
            )
            if package_lock.exists():
                old_urls = [
                    s for s in package_lock.read_text().splitlines() if s.startswith("http")
                ]
                new_urls = [s for s in explicit.splitlines() if s.startswith("http")]
                if sorted(old_urls) != sorted(new_urls):
                    raise RuntimeError("Existing environment differs from its package lock")
            else:
                package_lock.write_text(explicit)
            shutil.copy2(package_lock, self.output / package_lock.name)
            self.report["environment_lock_sha256"] = digest(package_lock)
            self.env["PATH"] = str(prefix / "bin") + os.pathsep + self.env.get("PATH", "")
            self.env["CONDA_PREFIX"] = str(prefix)
            self.env["GDAL_DATA"] = str(prefix / "share/gdal")
            self.env["PROJ_DATA"] = str(prefix / "share/proj")
            for name in [
                "mpifort",
                "make",
                "bc",
                "gdal_translate",
                "gdalwarp",
                "gdal_calc.py",
                "gdal_merge.py",
                "gdal_contour",
            ]:
                if not shutil.which(name, path=self.env["PATH"]):
                    raise RuntimeError(f"Environment missing {name}")
            self.command(
                [
                    str(prefix / "bin/python"),
                    "-c",
                    "import rasterio, numpy; print(rasterio.__version__, numpy.__version__)",
                ]
            )
            self.command([str(prefix / "bin/mpifort"), "--version"])
            self.command([str(prefix / "bin/gdalinfo"), "--version"])

        install = self.work / "bin"
        install.mkdir(exist_ok=True)
        self.env.update(
            {
                "ELMFIRE_BASE_DIR": str(source),
                "ELMFIRE_INSTALL_DIR": str(install),
                "ELMFIRE_VER": self.report["source_version"],
                "ELMFIRE_SCRATCH_BASE": str(self.output / "scratch"),
                "ELMFIRE_FCOMPL_MPI_GNU": str(prefix / "bin/mpifort"),
                "PATH": str(install) + os.pathsep + self.env["PATH"],
            }
        )
        with self.phase("build"):
            self.command(
                ["nice", "-n", "10", "bash", "make_gnu.sh", "fast"], cwd=source / "build/linux"
            )
            executable = install / f"elmfire_{self.report['source_version']}"
            if not executable.is_file() or not os.access(executable, os.X_OK):
                raise RuntimeError("Build did not produce the main executable")
            self.report["binary_sha256"] = digest(executable)
            self.report["binary_path"] = str(executable)
            self.command(["git", "diff", "--exit-code"], cwd=source)

        case = self.output / "tutorials/01-constant-wind"
        with self.phase("synthetic_tutorial"):
            shutil.copytree(source / TUTORIAL, case)
            shutil.copytree(source / "tutorials/functions", case.parent / "functions")
            log = self.command(
                ["nice", "-n", "10", "bash", "-e", "01-run.sh"], cwd=case, timeout=900
            )
            if "End of simulation reached successfully" not in log:
                raise RuntimeError("ELMFIRE did not report a completed simulation")
            self.report["tutorial_script_sha256"] = digest(case / "01-run.sh")
            self.report["input_sha256"] = {
                item.name: digest(item)
                for item in sorted((case / "inputs").iterdir())
                if item.is_file()
            }

        with self.phase("output_validation"):
            arrivals = list((case / "outputs").glob("time_of_arrival*.tif"))
            if len(arrivals) != 1:
                raise RuntimeError("Expected exactly one synthetic arrival-time output")
            summary = self.output / "arrival-summary.json"
            self.command(
                [
                    str(prefix / "bin/python"),
                    str(Path(__file__).resolve()),
                    "--inspect-arrival",
                    str(arrivals[0]),
                    "--inspection-output",
                    str(summary),
                ]
            )
            self.report["arrival_summary"] = json.loads(summary.read_text())
            self.report["status"] = "synthetic_probe_passed"
            self.report["finished_at"] = utc_now()
            self.save()


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan", action="store_true", help="Print immutable plan without writing/network"
    )
    parser.add_argument(
        "--work-root", type=Path, default=root / "data/artifacts/research-tools/elmfire"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--inspect-arrival", type=Path)
    parser.add_argument("--inspection-output", type=Path)
    args = parser.parse_args(argv)
    if args.plan:
        print(json.dumps(plan(), ensure_ascii=False, indent=2))
        return 0
    if args.inspect_arrival:
        value = inspect_arrival(args.inspect_arrival)
        if args.inspection_output:
            atomic_json(args.inspection_output, value)
        else:
            print(json.dumps(value, indent=2))
        return 0
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or root / "data/artifacts/elmfire" / f"synthetic-{stamp}-{os.getpid()}"
    probe = Probe(args.work_root, output)
    try:
        probe.execute()
    except Exception as error:
        probe.report.update(
            {
                "status": "failed",
                "failed_stage": probe.stage,
                "error_type": type(error).__name__,
                "error": str(error),
                "finished_at": utc_now(),
            }
        )
        probe.save()
        print(f"Probe failed at {probe.stage}: {error}", file=sys.stderr)
        print(f"Report: {probe.output / 'report.json'}", file=sys.stderr)
        return 1
    print(f"Synthetic probe complete: {probe.output / 'report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
