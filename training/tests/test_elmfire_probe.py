"""Checks on the research probe's output acceptance and failure boundaries."""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

TOOL = Path(__file__).resolve().parents[1] / "tools/elmfire_probe.py"
SPEC = importlib.util.spec_from_file_location("elmfire_probe", TOOL)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def write_arrival(path, values, *, crs="EPSG:32610", resolution=30):
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=values.shape[0],
        width=values.shape[1],
        count=1,
        dtype="float32",
        crs=crs,
        nodata=-9999,
        transform=from_origin(-6000, 6000, resolution, resolution),
    ) as output:
        output.write(values.astype("float32"), 1)


def test_inspection_accepts_nontrivial_synthetic_arrival(tmp_path):
    values = np.full((400, 400), -9999.0)
    values[190:210, 190:210] = np.arange(400).reshape(20, 20) * 30
    path = tmp_path / "toa.tif"
    write_arrival(path, values)
    report = probe.inspect_arrival(path)
    assert report["reached_cells"] == 400
    assert report["max_arrival_seconds"] == 11970
    assert "not real-world risk probability" in report["meaning"]


@pytest.mark.parametrize("kind", ["all_unburned", "all_burned", "nan", "over_horizon"])
def test_inspection_rejects_invalid_arrivals(tmp_path, kind):
    values = np.full((400, 400), -9999.0)
    if kind == "all_burned":
        values[:] = 30
    elif kind == "nan":
        values[20:30, 20:30] = np.nan
    elif kind == "over_horizon":
        values[20:30, 20:30] = 25000
    path = tmp_path / "bad.tif"
    write_arrival(path, values)
    with pytest.raises(ValueError):
        probe.inspect_arrival(path)


@pytest.mark.parametrize("setting", [{"crs": "EPSG:4326"}, {"resolution": 100}])
def test_inspection_rejects_wrong_georeferencing(tmp_path, setting):
    values = np.full((400, 400), -9999.0)
    values[20:30, 20:30] = 60
    path = tmp_path / "bad-grid.tif"
    write_arrival(path, values, **setting)
    with pytest.raises(ValueError):
        probe.inspect_arrival(path)


def test_failed_stage_persists_and_does_not_claim_validation(tmp_path, monkeypatch):
    monkeypatch.setattr(probe.platform, "system", lambda: "unsupported")
    output = tmp_path / "report"
    assert probe.main(["--work-root", str(tmp_path / "work"), "--output", str(output)]) == 1
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "failed"
    assert report["failed_stage"] == "platform"
    assert report["stages"][0]["status"] == "failed"
    assert report["simulation_only"] is True
    assert report["operational_use"] is False
    assert report["personal_risk_validated"] is False


def test_external_failure_cannot_be_reported_as_success(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    run = probe.Probe(work, tmp_path / "report")
    with pytest.raises(RuntimeError, match="exited 7"), run.phase("fixture"):
        run.command([sys.executable, "-c", "raise SystemExit(7)"])
    report = json.loads((run.output / "report.json").read_text())
    assert report["stages"][0]["status"] == "failed"
    assert (run.output / "fixture.log").exists()
