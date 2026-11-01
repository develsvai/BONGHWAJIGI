"""Synthetic contracts only; no held-out wildfire observations or API requests."""

import importlib.util
import json
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pytest
import rasterio

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "elmfire_gofer_hindcast", TOOLS / "elmfire_gofer_hindcast.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
sys.path.pop(0)


@pytest.fixture
def inputs(tmp_path):
    profile = {
        "driver": "GTiff",
        "count": 1,
        "height": 419,
        "width": 411,
        "dtype": "float32",
        "crs": rasterio.crs.CRS.from_epsg(32610),
        "transform": module.TRANSFORM,
    }
    root = tmp_path / "terrain"
    root.mkdir()
    initial = np.zeros(module.SHAPE, dtype="uint8")
    initial[200:202, 200:202] = 1
    domain = np.ones(module.SHAPE, dtype="uint8")
    domain[:3, :] = domain[-3:, :] = 0
    domain[:, :3] = domain[:, -3:] = 0
    arrays = {
        "initial_perimeter_mask.tif": initial,
        "study_domain_mask.tif": domain,
        "unknown_mask.tif": np.zeros(module.SHAPE, dtype="uint8"),
        "elevation_m.tif": np.full(module.SHAPE, 123.4, dtype="float32"),
        "slope_deg.tif": np.full(module.SHAPE, 15, dtype="float32"),
        "aspect_deg.tif": np.full(module.SHAPE, 10, dtype="float32"),
        "fuel_model.tif": np.full(module.SHAPE, 183, dtype="int16"),
    }
    outputs = {}
    for name, values in arrays.items():
        module.common.save_raster(root / name, values, profile)
        outputs[name] = {"path": name, "sha256": module.common.sha256(root / name)}
    initial_geometry = root / "initial_perimeter.geojson"
    initial_geometry.write_text('{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,0]]]}')
    terrain = {
        "status": "ready",
        "event_id": module.EVENT,
        "initial_time_utc": module.START,
        "split": "train",
        "crs": "EPSG:32610",
        "shape": list(module.SHAPE),
        "pixel_size_m": 100,
        "transform": list(module.TRANSFORM)[:6],
        "aspect_reference": "grid_north_clockwise_downslope",
        "outputs": outputs,
        "retrospective_proxy_only": True,
        "source_asof_verified": False,
        "sources": {"gofer": {"archive_sha256": "a" * 64}},
        "initial_geometry": {
            "path": initial_geometry.name,
            "sha256": module.common.sha256(initial_geometry),
            "source_archive_sha256": "a" * 64,
        },
    }
    terrain_path = root / "manifest.json"
    module.common.write_json(terrain_path, terrain)
    evidence = root / "axis.txt"
    evidence.write_text("Synthetic test metadata, not an actual GRIB artifact")
    record = {
        "artifact_path": evidence.name,
        "sha256": module.common.sha256(evidence),
        "role": "original_forecast_metadata",
        "retrieved_at_utc": "2026-11-01T01:00:00Z",
    }
    weather = {
        "schema_version": "elmfire_hrrr_gridded_weather_v1",
        "source": "NOAA_HRRR",
        "historical_forecast_cycle_verified": True,
        "operational_availability_verified": False,
        "wind_axis_basis_verified": True,
        "wind_direction_basis": "true_north_clockwise_from",
        "wind_height_m": 10,
        "wind_speed_unit": "m/s",
        "wind_direction_unit": "degree",
        "forecast_issue_time_utc": module.ISSUE,
        "simulation_start_time_utc": module.START,
        "hours": [
            {
                "valid_time_utc": (
                    module.common.timestamp(module.START) + timedelta(hours=i)
                ).isoformat()
            }
            for i in range(7)
        ],
        "provenance": [record],
        "axis_verification": record | {"method": "synthetic fixture"},
        "outputs": {},
    }
    for name, value in (("wind_speed_m_s.tif", 5), ("wind_direction_true_deg.tif", 270)):
        raster = root / name
        module.common.save_raster(
            raster, np.full((7, *module.SHAPE), value, dtype="float32"), profile, nodata=-9999
        )
        weather["outputs"][name] = {"path": name, "sha256": module.common.sha256(raster)}
    weather_path = root / "weather.json"
    module.common.write_json(weather_path, weather)
    truth_path = root / "truth-manifest.json"
    truth_manifest = {
        "event_id": module.EVENT,
        "split": "train",
        "initial_time_utc": module.START,
        "retrospective_proxy_only": True,
        "outputs": {},
        "input_manifest_sha256": module.common.sha256(terrain_path),
        "source_archive_sha256": "a" * 64,
    }
    for key, seconds in module.HORIZONS.items():
        values = initial.copy()
        values[202, 200:202] = 1
        name = f"truth_{key}.tif"
        module.common.save_raster(root / name, values, profile)
        truth_manifest["outputs"][key] = {
            "path": name,
            "sha256": module.common.sha256(root / name),
            "valid_time_utc": (
                module.common.timestamp(module.START) + timedelta(seconds=seconds)
            ).isoformat(),
        }
    module.common.write_json(truth_path, truth_manifest)
    return terrain_path, weather_path, truth_path, arrays, profile


def test_phi_preserves_all_initial_cells_without_negative_nodata():
    initial = np.array([[False, False], [True, False]])
    phi = module.phi_mask(initial)
    assert phi.dtype == "float32"
    np.testing.assert_equal(phi, [[1, 1], [-1, 1]])
    with pytest.raises(ValueError):
        module.phi_mask(np.zeros((3, 3), dtype=bool))


def test_perimeter_namelist_disables_extra_point_ignition_and_fixes_numerics():
    text = module.namelist((3, 4, 5))
    assert "NUM_IGNITIONS = 0" in text
    assert "X_IGN(" not in text and "T_IGN(" not in text and "Y_IGN(" not in text
    assert "RANDOM_IGNITIONS = .FALSE." in text
    assert "SIMULATION_DTMAX = 30.0" in text
    assert "TARGET_CFL = 0.2" in text
    with pytest.raises(ValueError):
        module.namelist((5, 5, 5))


def test_actual_contract_accepts_past_forecast_download_without_asof_claim(inputs):
    terrain_path, weather_path, _, arrays, _ = inputs
    module.verify_terrain(terrain_path)
    data, wind = module.verify_weather(weather_path, arrays["study_domain_mask.tif"].astype(bool))
    assert data["operational_availability_verified"] is False
    assert wind["wind_speed_m_s.tif"].shape == (7, 419, 411)
    data["forecast_issue_time_utc"] = "2019-09-04T23:00:00Z"
    module.common.write_json(weather_path, data)
    with pytest.raises(ValueError, match="cycle"):
        module.verify_weather(weather_path, arrays["study_domain_mask.tif"].astype(bool))


def test_unknown_active_domain_or_unverified_axis_block_run(inputs):
    terrain_path, weather_path, _, arrays, profile = inputs
    data = json.loads(weather_path.read_text())
    data["wind_axis_basis_verified"] = False
    module.common.write_json(weather_path, data)
    with pytest.raises(ValueError, match="Unverified"):
        module.verify_weather(weather_path, arrays["study_domain_mask.tif"].astype(bool))
    unknown = arrays["unknown_mask.tif"].copy()
    unknown[50, 50] = 1
    target = terrain_path.parent / "unknown_mask.tif"
    module.common.save_raster(target, unknown, profile)
    manifest = json.loads(terrain_path.read_text())
    manifest["outputs"][target.name]["sha256"] = module.common.sha256(target)
    module.common.write_json(terrain_path, manifest)
    with pytest.raises(ValueError, match="Unknown terrain"):
        module.verify_terrain(terrain_path)


def test_score_increment_does_not_reward_large_initial_overlap():
    initial = np.ones((10, 10), dtype=bool)
    initial[8:] = False
    observed = initial.copy()
    observed[8, :2] = True
    metrics = module.score_masks(initial, observed, initial, np.ones_like(initial))
    assert metrics["new_growth_iou"] == 0
    assert metrics["new_growth_recall"] == 0
    assert metrics["new_growth_precision"] is None
    assert metrics["total_iou_secondary"] == pytest.approx(80 / 82)
    assert metrics["signed_new_area_error_ha"] == -2


def test_zero_union_and_zero_denominators_remain_null():
    initial = np.zeros((3, 3), dtype=bool)
    initial[1, 1] = True
    result = module.score_masks(initial, initial, initial, np.ones_like(initial))
    assert result["new_growth_iou"] is None
    assert result["new_growth_precision"] is None
    assert result["new_growth_recall"] is None
    assert result["total_iou_secondary"] == 1


def test_all_initial_cells_zero_and_initial_only_fire_valid(inputs, tmp_path):
    _, _, _, arrays, profile = inputs
    initial = arrays["initial_perimeter_mask.tif"].astype(bool)
    values = np.full(module.SHAPE, -9999, dtype="float32")
    values[initial] = 0
    target = tmp_path / "arrival.tif"
    module.common.save_raster(target, values, profile, nodata=-9999)
    coverage = {"horizon_completed": dict.fromkeys(module.HORIZONS, True)}
    result, _ = module.inspect_arrival(target, arrays, coverage)
    assert result["initial_cells"] == result["reached_cells"] == 4
    values[200, 200] = 5
    module.common.save_raster(target, values, profile, nodata=-9999)
    with pytest.raises(ValueError, match="Every initial"):
        module.inspect_arrival(target, arrays, coverage)


def test_edge_censor_and_time_censor_remove_metrics(inputs):
    _, _, _, arrays, _ = inputs
    initial = arrays["initial_perimeter_mask.tif"].astype(bool)
    truth = dict.fromkeys(module.HORIZONS, initial)
    raw = np.where(initial, 0, np.nan)
    cases = [
        {
            "id": "case",
            "status": "censored",
            "coverage": {"horizon_completed": {"1h": True, "3h": False, "6h": False}},
            "boundary_reached_cells": {"1h": 1, "3h": 1, "6h": 1},
        }
    ]
    result = module.evaluate(cases, {"case": raw}, truth, arrays)["cases"]["case"]
    assert result["1h"]["reason"] == "simulation_reaches_spatial_boundary"
    assert result["3h"]["reason"] == "solver_stopped_before_horizon"
    assert all(item["metrics"] is None for item in result.values())


def test_unmasked_negative_arrival_is_not_silently_unreached(inputs, tmp_path):
    _, _, _, arrays, profile = inputs
    values = np.full(module.SHAPE, -9999, dtype="float32")
    values[arrays["initial_perimeter_mask.tif"].astype(bool)] = 0
    values[203, 203] = -1
    target = tmp_path / "invalid-arrival.tif"
    module.common.save_raster(target, values, profile, nodata=-9999)
    with pytest.raises(ValueError, match="Unmasked negative"):
        module.inspect_arrival(
            target, arrays, {"horizon_completed": dict.fromkeys(module.HORIZONS, True)}
        )


@pytest.mark.parametrize("field", ["input_manifest_sha256", "source_archive_sha256"])
def test_truth_must_match_frozen_input_and_archive_hashes(inputs, tmp_path, field):
    terrain_path, _, truth_path, arrays, _ = inputs
    receipt = tmp_path / "receipt.json"
    module.common.write_json(
        receipt,
        {
            "future_labels_read": False,
            "cases_attempted": 3,
            "input_manifest_sha256": module.common.sha256(terrain_path),
            "source_archive_sha256": "a" * 64,
        },
    )
    data = json.loads(truth_path.read_text())
    data[field] = "b" * 64
    module.common.write_json(truth_path, data)
    with pytest.raises(ValueError, match=field):
        module.load_truth(truth_path, arrays, receipt)


def test_initial_geometry_hash_is_part_of_preflight(inputs):
    terrain_path, _, _, _, _ = inputs
    (terrain_path.parent / "initial_perimeter.geojson").write_text("changed")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        module.verify_terrain(terrain_path)


def test_labels_require_receipt_and_cannot_shrink(inputs, tmp_path):
    terrain_path, _, truth_path, arrays, profile = inputs
    with pytest.raises(ValueError, match="receipt"):
        module.load_truth(truth_path, arrays, tmp_path / "missing.json")
    receipt = tmp_path / "receipt.json"
    module.common.write_json(
        receipt,
        {
            "future_labels_read": False,
            "cases_attempted": 3,
            "input_manifest_sha256": module.common.sha256(terrain_path),
            "source_archive_sha256": "a" * 64,
        },
    )
    _, truth = module.load_truth(truth_path, arrays, receipt)
    assert truth["1h"].sum() == 6
    truth["1h"][200, 200] = False
    manifest = json.loads(truth_path.read_text())
    raster = truth_path.parent / manifest["outputs"]["1h"]["path"]
    module.common.save_raster(raster, truth["1h"].astype("uint8"), profile)
    manifest["outputs"]["1h"]["sha256"] = module.common.sha256(raster)
    module.common.write_json(truth_path, manifest)
    with pytest.raises(ValueError, match="shrank"):
        module.load_truth(truth_path, arrays, receipt)


def test_prepare_only_never_opens_future_manifest(inputs, tmp_path, monkeypatch):
    terrain_path, weather_path, _, _, _ = inputs
    receipt = {"binary_sha256": "test", "license": "test", "license_scope": "test"}
    probe = tmp_path / "probe.json"
    module.common.write_json(probe, receipt)
    monkeypatch.setattr(
        module.common, "verify_source", lambda _: (receipt, tmp_path / "bin/elmfire_1.1")
    )
    report = module.execute(
        probe,
        terrain_path,
        weather_path,
        tmp_path / "future-does-not-exist.json",
        tmp_path / "prepared",
        prepare_only=True,
    )
    assert report["status"] == "prepared"
    assert report["future_labels_read"] is False
    assert len(report["cases"]) == 3
    for case in report["cases"]:
        with rasterio.open(tmp_path / "prepared" / case["id"] / "inputs/phi.tif") as phi:
            assert phi.nodata == -9999
            assert set(np.unique(phi.read(1))) == {-1, 1}


@pytest.mark.parametrize("mutate_truth", [False, True])
def test_three_simulations_freeze_receipt_before_future_labels(
    inputs, tmp_path, monkeypatch, mutate_truth
):
    terrain_path, weather_path, truth_path, arrays, profile = inputs
    receipt = {"binary_sha256": "test", "license": "test", "license_scope": "test"}
    probe = tmp_path / "probe.json"
    module.common.write_json(probe, receipt)
    binary = tmp_path / "prefix/bin/elmfire_1.1"
    gdal = tmp_path / "prefix/env/bin/gdal_translate"
    gdal.parent.mkdir(parents=True)
    gdal.touch()
    monkeypatch.setattr(module.common, "verify_source", lambda _: (receipt, binary))
    ran = []

    def fake_command(command, case, env, timeout):
        if command[0] == "nice":
            ran.append(case.name)
            (case / "run.log").write_text("End of simulation reached successfully\n")
            (case / "outputs/time_of_arrival_0000001_0021600.bil").write_bytes(b"test")
            (case / "outputs/fire_size_stats.csv").write_text(
                "icase,Meteorology band,tstop (h)\n1,1,6.00\n"
            )
        else:
            values = np.full(module.SHAPE, -9999, dtype="float32")
            values[arrays["initial_perimeter_mask.tif"].astype(bool)] = 0
            values[202, 200:202] = 3600
            module.common.save_raster(Path(command[-1]), values, profile, nodata=-9999)

    original_load = module.load_truth

    def audited_load(path, inputs, fit_receipt):
        assert len(ran) == 3
        assert json.loads(fit_receipt.read_text())["future_labels_read"] is False
        return original_load(path, inputs, fit_receipt)

    monkeypatch.setattr(module.common, "run_command", fake_command)
    monkeypatch.setattr(module, "load_truth", audited_load)
    original_evaluate = module.evaluate

    def audited_evaluate(*args):
        result = original_evaluate(*args)
        if mutate_truth:
            data = json.loads(truth_path.read_text())
            data["changed_after_loading"] = True
            module.common.write_json(truth_path, data)
        return result

    monkeypatch.setattr(module, "evaluate", audited_evaluate)
    output = tmp_path / "executed"
    report = module.execute(probe, terrain_path, weather_path, truth_path, output)
    if mutate_truth:
        assert report["status"] == "failed"
        assert "Truth manifest changed" in report["error"]
        assert not (output / "evaluation.json").exists()
        return
    assert report["status"] == "complete"
    evaluation = json.loads((output / "evaluation.json").read_text())
    assert evaluation["probability"] is None
    assert evaluation["cases"][ran[0]]["1h"]["metrics"]["new_growth_iou"] == 1
    assert evaluation["baseline"]["horizons"]["1h"]["metrics"]["new_growth_iou"] == 0
