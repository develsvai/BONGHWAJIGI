"""Input and interpretation guards; these do not measure wildfire forecast skill."""

import copy
import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

PATH = Path(__file__).resolve().parents[1] / "tools/elmfire_korea_scenario.py"
SPEC = importlib.util.spec_from_file_location("elmfire_korea_scenario", PATH)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


@pytest.fixture
def weather(tmp_path):
    evidence = tmp_path / "axis.txt"
    evidence.write_text("synthetic test evidence: eastward_wind/northward_wind")
    start = datetime(2026, 10, 31, 18, tzinfo=UTC)
    record = {
        "artifact_path": evidence.name,
        "sha256": module.sha256(evidence),
        "role": "point_wind_and_axis",
        "retrieved_at_utc": "2026-10-31T16:00:00Z",
    }
    data = {
        "schema_version": "elmfire_kma_point_weather_v1",
        "source": "KMA_APIHub_KIML",
        "point": {"longitude": 129.3, "latitude": 37.0},
        "forecast_issue_time_utc": "2026-10-31T12:00:00Z",
        "simulation_start_time_utc": start.isoformat(),
        "wind_axis_basis_verified": True,
        "wind_direction_basis": "true_north_clockwise_from",
        "wind_height_m": 10,
        "wind_speed_unit": "m/s",
        "wind_direction_unit": "degree",
        "axis_verification": record | {"method": "synthetic test fixture"},
        "provenance": [record],
        "hours": [
            {
                "valid_time_utc": (start + timedelta(hours=i)).isoformat(),
                "wind_speed_m_s": 5 + i,
                "wind_direction_deg": 350 + i,
            }
            for i in range(7)
        ],
    }
    path = tmp_path / "weather.json"
    module.write_json(path, data)
    return path, data


@pytest.fixture
def terrain(tmp_path):
    root = tmp_path / "terrain"
    root.mkdir()
    profile = {
        "driver": "GTiff",
        "height": 100,
        "width": 100,
        "count": 1,
        "dtype": "float32",
        "crs": rasterio.crs.CRS.from_epsg(32652),
        "transform": from_origin(521692.8540702973, 4099914.4265484256, 100, 100),
    }
    zeros = np.zeros((100, 100), dtype="uint8")
    arrays = {
        "elevation_m.tif": np.full((100, 100), 123.4, dtype="float32"),
        "slope_deg.tif": np.full((100, 100), 14.6, dtype="float32"),
        "aspect_deg.tif": np.full((100, 100), 359.8, dtype="float32"),
        "landcover_class.tif": np.full((100, 100), 70, dtype="uint8"),
        "forest_mask.tif": np.ones((100, 100), dtype="uint8"),
        "water_mask.tif": zeros.copy(),
        "unknown_mask.tif": zeros.copy(),
        "flat_mask.tif": zeros.copy(),
    }
    # A genuine water exclusion and a known nonforest exclusion remain distinct.
    arrays["landcover_class.tif"][0, 0] = 210
    arrays["landcover_class.tif"][0, 1] = 100
    arrays["forest_mask.tif"][0, :2] = 0
    arrays["water_mask.tif"][0, 0] = 1
    outputs = {}
    for name, data in arrays.items():
        path = root / name
        module.save_raster(path, data, profile)
        outputs[name] = {"path": name, "sha256": module.sha256(path)}
    manifest = {
        "status": "ready",
        "crs": "EPSG:32652",
        "shape": [100, 100],
        "pixel_size_m": 100,
        "transform": list(profile["transform"])[:6],
        "aspect_reference": "grid_north_clockwise_downslope",
        "requested_center_longitude_latitude": [129.3, 37.0],
        "outputs": outputs,
        "created_at_utc": "2026-10-31T16:52:00Z",
        "sources": {"dem": [{"retrieved_at_utc": "2026-10-31T11:00:00Z"}]},
    }
    path = root / "manifest.json"
    module.write_json(path, manifest)
    return path, arrays, profile


def test_weather_accepts_only_seven_time_aligned_verified_knots(weather):
    path, data = weather
    assert module.verify_weather(path)["hours"] == data["hours"]
    data["hours"].pop()
    module.write_json(path, data)
    with pytest.raises(ValueError, match="Seven hourly"):
        module.verify_weather(path)


@pytest.mark.parametrize(
    "field,value",
    [
        ("wind_axis_basis_verified", False),
        ("wind_axis_basis_verified", 1),
        ("wind_direction_basis", "grid_north_clockwise_from"),
        ("wind_speed_unit", "knots"),
        ("wind_height_m", 20),
    ],
)
def test_unverified_or_incompatible_wind_is_blocked(weather, field, value):
    path, data = weather
    data[field] = value
    module.write_json(path, data)
    with pytest.raises(ValueError):
        module.verify_weather(path)


def test_post_ignition_lookup_and_modified_evidence_are_blocked(weather):
    path, data = weather
    original = copy.deepcopy(data)
    data["provenance"][0]["retrieved_at_utc"] = data["simulation_start_time_utc"]
    module.write_json(path, data)
    with pytest.raises(ValueError, match="precede simulation start"):
        module.verify_weather(path)
    module.write_json(path, original)
    (path.parent / "axis.txt").write_text("changed")
    with pytest.raises(ValueError, match="SHA256"):
        module.verify_weather(path)


def test_open_meteo_unknown_issue_and_original_units_values_checked(weather):
    path, data = weather
    data.update(
        {
            "schema_version": "elmfire_open_meteo_point_weather_v1",
            "source": "OpenMeteo_GFS",
            "forecast_issue_time_utc": None,
            "forecast_issue_time_known": False,
            "issue_time_note": "Provider response does not expose forecast cycle; do not infer it",
        }
    )
    raw = {
        "utc_offset_seconds": 0,
        "hourly_units": {"time": "iso8601", "wind_speed_10m": "m/s", "wind_direction_10m": "°"},
        "hourly": {
            "time": [hour["valid_time_utc"].replace("+00:00", "") for hour in data["hours"]],
            "wind_speed_10m": [hour["wind_speed_m_s"] for hour in data["hours"]],
            "wind_direction_10m": [hour["wind_direction_deg"] for hour in data["hours"]],
        },
    }
    raw_path = path.parent / "open-meteo.json"
    module.write_json(raw_path, raw)
    data["provenance"].append(
        {
            "artifact_path": raw_path.name,
            "sha256": module.sha256(raw_path),
            "retrieved_at_utc": "2026-10-31T17:00:00Z",
            "role": "open_meteo_response",
        }
    )
    module.write_json(path, data)
    assert module.verify_weather(path)["forecast_issue_time_utc"] is None
    data["hours"][0]["wind_speed_m_s"] += 1
    module.write_json(path, data)
    with pytest.raises(ValueError, match="differ from original"):
        module.verify_weather(path)
    data["hours"][0]["wind_speed_m_s"] -= 1
    raw["hourly_units"]["wind_speed_10m"] = "km/h"
    module.write_json(raw_path, raw)
    data["provenance"][-1]["sha256"] = module.sha256(raw_path)
    module.write_json(path, data)
    with pytest.raises(ValueError, match="units or timezone"):
        module.verify_weather(path)


def test_source_receipt_binary_and_both_licenses_are_reverified(tmp_path):
    binary = tmp_path / "binary"
    binary.write_bytes(b"test binary")
    inputs = tmp_path / "tutorials/01-constant-wind/inputs"
    inputs.mkdir(parents=True)
    (inputs / "input").write_bytes(b"test input")
    licenses = {}
    for name in ("LICENSE.md", "COMMERCIAL_LICENSE.md"):
        (tmp_path / name).write_text("test license")
        licenses[name] = module.sha256(tmp_path / name)
    receipt = {
        "status": "synthetic_probe_passed",
        "source_commit": module.SOURCE_SHA,
        "simulation_only": True,
        "operational_use": False,
        "binary_path": str(binary),
        "binary_sha256": module.sha256(binary),
        "license_sha256": licenses,
        "input_sha256": {"input": module.sha256(inputs / "input")},
    }
    path = tmp_path / "report.json"
    module.write_json(path, receipt)
    module.verify_source(path)
    (tmp_path / "COMMERCIAL_LICENSE.md").write_text("changed")
    with pytest.raises(ValueError, match="License receipt changed"):
        module.verify_source(path)


def test_unknown_terrain_never_becomes_nonburnable(terrain):
    path, arrays, profile = terrain
    module.verify_terrain(path)
    arrays["unknown_mask.tif"][5, 5] = 1
    output = path.parent / "unknown_mask.tif"
    module.save_raster(output, arrays["unknown_mask.tif"], profile)
    manifest = json.loads(path.read_text())
    manifest["outputs"]["unknown_mask.tif"]["sha256"] = module.sha256(output)
    module.write_json(path, manifest)
    with pytest.raises(ValueError, match="Unknown landcover"):
        module.verify_terrain(path)


def test_landscape_band_order_rounding_and_separate_exclusions(terrain):
    _, arrays, _ = terrain
    values = module.landscape(arrays, 183)
    assert values.shape == (8, 100, 100)
    assert values.dtype == "int16"
    assert values[:, 10, 10].tolist() == [123, 15, 0, 183, 0, 0, 0, 0]
    assert values[3, 0, :2].tolist() == [98, 99]
    with pytest.raises(ValueError, match="predeclared"):
        module.landscape(arrays, 184)


def test_projection_rotation_sign_and_central_meridian(terrain):
    _, _, profile = terrain
    angles = module.grid_rotation(profile)
    # East of UTM52 central meridian129E, true north lies west of grid north.
    assert np.all((angles > -0.3) & (angles < -0.1))
    profile = profile | {
        "height": 1,
        "width": 1,
        "transform": from_origin(499950, 4095050, 100, 100),
    }
    assert abs(module.grid_rotation(profile)[0, 0]) < 1e-5


def test_ignition_is_nearest_forest_cell_center_and_guarded(terrain):
    _, arrays, profile = terrain
    points = module.select_probes(arrays, profile)
    assert (points[0]["row"], points[0]["column"]) == (49, 49)
    assert points[0]["xy_m"] == list(profile["transform"] * (49.5, 49.5))
    arrays["forest_mask.tif"][:] = 0
    with pytest.raises(ValueError, match="500m"):
        module.select_probes(arrays, profile)


def test_prepared_weather_rasters_have_seven_bands_units_and_rotation(terrain, weather, tmp_path):
    _, arrays, profile = terrain
    _, data = weather
    rotation = module.grid_rotation(profile)
    case = tmp_path / "case"
    module.prepare_case(
        case, arrays, profile, data, 181, rotation, module.select_probes(arrays, profile)
    )
    with rasterio.open(case / "inputs/ws.tif") as ws, rasterio.open(case / "inputs/wd.tif") as wd:
        assert ws.nodata == wd.nodata == -9999
        assert ws.count == wd.count == 7
        assert ws.descriptions[-1] == data["hours"][-1]["valid_time_utc"]
        assert ws.read(7)[50, 50] == pytest.approx(11 * 3.6)
        assert wd.read(1)[50, 50] == pytest.approx((350 + rotation[50, 50]) % 360)
    with rasterio.open(case / "inputs/m100.tif") as moisture:
        assert moisture.count == 7
        assert moisture.nodata == -9999
        assert np.all(moisture.read() == 8)
    with rasterio.open(case / "inputs/landscape.tif") as land:
        assert land.nodata == -9999
        assert not np.ma.getmaskarray(land.read(5, masked=True)).any()
    text = (case / "inputs/elmfire.data").read_text()
    assert "CROWN_FIRE_MODEL = 0" in text
    assert "SIMULATION_TSTOP = 21600.0" in text
    assert "WS_AT_10M = .TRUE." in text
    assert "GRID_DECLINATION = 0.0" in text


def test_arrival_interpretation_initial_exclusion_and_origin_roundoff(terrain, tmp_path):
    _, arrays, profile = terrain
    probes = module.select_probes(arrays, profile)
    values = np.full((100, 100), -9999, dtype="float32")
    values[49, 49] = 0
    values[39, 49] = 3600
    target = tmp_path / "arrival.tif"
    rounded = profile | {"transform": from_origin(521692.84, 4099914.5, 100, 100)}
    module.save_raster(target, values, rounded, nodata=-9999)
    result = module.inspect_arrival(target, arrays, profile, probes)
    assert result["probes"][0]["state"] == "initially_reached"
    assert result["probes"][1]["arrival_seconds"] == 3600
    assert result["future_reached_area_ha"] == {"1h": 1, "3h": 1, "6h": 1}
    values[0, 0] = 1000
    module.save_raster(target, values, profile, nodata=-9999)
    with pytest.raises(ValueError, match="excluded input cell"):
        module.inspect_arrival(target, arrays, profile, probes)


def test_initial_only_fire_is_valid_but_zero_nodata_is_ambiguous(terrain, tmp_path):
    _, arrays, profile = terrain
    probes = module.select_probes(arrays, profile)
    values = np.full((100, 100), -9999, dtype="float32")
    values[49, 49] = 0
    target = tmp_path / "initial-only.tif"
    module.save_raster(target, values, profile, nodata=-9999)
    result = module.inspect_arrival(target, arrays, profile, probes)
    assert result["reached_cells"] == result["initial_cells"] == 1
    assert result["future_reached_area_ha"] == {"1h": 0, "3h": 0, "6h": 0}
    assert result["probes"][0]["state"] == "initially_reached"
    # Engine defaults to zero when no input nodata was supplied, making the
    # exported raster unable to distinguish initial ignition from unreached.
    module.save_raster(target, np.zeros((100, 100), dtype="float32"), profile, nodata=0)
    with pytest.raises(ValueError, match="distinct from valid initial zero"):
        module.inspect_arrival(target, arrays, profile, probes)


def test_fraction_null_for_partial_initial_excluded_and_integrity_failure(terrain):
    _, arrays, profile = terrain
    probes = module.select_probes(arrays, profile)
    cases = []
    for fuel, seconds in zip(module.FUEL_SCENARIOS, (3600, 10800, 21600), strict=True):
        cases.append(
            {
                "status": "complete",
                "fuel_model": fuel,
                "coverage": {"horizon_completed": dict.fromkeys(module.HORIZONS, True)},
                "probes": [
                    point | {"state": "future_arrival", "arrival_seconds": seconds}
                    for point in probes
                ],
            }
        )
    result = module.aggregate(cases, probes)
    assert result[1]["scenario_fraction"] == {"1h": 1 / 3, "3h": 2 / 3, "6h": 1}
    assert result[1]["probability"] is None
    for case in cases:
        case["probes"][0].update({"state": "initially_reached", "arrival_seconds": 0})
    assert module.aggregate(cases, probes)[0]["scenario_fraction"] == dict.fromkeys(module.HORIZONS)
    probes[1]["eligibility"] = "excluded_nonforest"
    assert module.aggregate(cases, probes)[1]["unavailable_reason"] == "excluded_nonforest"
    assert module.aggregate(cases, probes, integrity_ok=False)[2][
        "scenario_fraction"
    ] == dict.fromkeys(module.HORIZONS)
    cases[2] = {"status": "failed", "fuel_model": 185}
    assert module.aggregate(cases, probes)[2]["unavailable_reason"] == "partial_or_failed_ensemble"


def coverage_fixture(tmp_path, tstop, log):
    case = tmp_path / "coverage"
    (case / "outputs").mkdir(parents=True)
    (case / "outputs/fire_size_stats.csv").write_text(
        f"icase,Meteorology band,tstop (h)\n1,1,{tstop}\n"
    )
    (case / "run.log").write_text(log)
    return module.inspect_coverage(case)


def test_early_stall_is_not_final_raster_horizon(tmp_path):
    result = coverage_fixture(
        tmp_path,
        "1.00",
        (
            "[1] Current Timestep: 3605.0 of 21600.0\r"
            "[1] STOPPING: FIRE FRONT PROPAGATION STALLED\n"
            "time_of_arrival_0000001_0021605.bil\nEnd of simulation reached successfully\n"
        ),
    )
    assert result["early_stop_detected"] is True
    assert result["full_horizon_completed"] is False
    assert result["covered_until_seconds_lower_bound"] == pytest.approx(3604.95)
    assert result["horizon_completed"] == {"1h": True, "3h": False, "6h": False}


def test_early_stop_without_progress_has_conservative_csv_bound(tmp_path):
    result = coverage_fixture(tmp_path, "1.00", "STOPPING: FIRE FRONT PROPAGATION STALLED\n")
    assert result["covered_until_seconds_lower_bound"] == 3582
    assert result["horizon_completed"] == dict.fromkeys(module.HORIZONS, False)


def test_full_solver_coverage_requires_consistent_stats_and_no_early_exit(tmp_path):
    result = coverage_fixture(tmp_path, "6.00", "End of simulation reached successfully\n")
    assert result["full_horizon_completed"] is True
    assert result["horizon_completed"] == dict.fromkeys(module.HORIZONS, True)


def test_mismatched_stop_log_and_stats_cannot_make_scenario_negative(tmp_path):
    with pytest.raises(ValueError, match="disagrees"):
        coverage_fixture(
            tmp_path,
            "3.00",
            ("Current Timestep: 3605.0 of 21600.0\rSTOPPING: FIRE FRONT PROPAGATION STALLED\n"),
        )


def test_censored_case_preserves_short_horizon_but_not_late_fractions(terrain):
    _, arrays, profile = terrain
    probes = module.select_probes(arrays, profile)
    cases = [
        {
            "fuel_model": fuel,
            "status": "censored" if fuel == 181 else "complete",
            "coverage": {"horizon_completed": {"1h": True, "3h": fuel != 181, "6h": fuel != 181}},
            "probes": [
                p | {"state": "unreached_within_simulated_coverage", "arrival_seconds": None}
                for p in probes
            ],
        }
        for fuel in module.FUEL_SCENARIOS
    ]
    result = module.aggregate(cases, probes)[1]
    assert result["scenario_fraction"] == {"1h": 0, "3h": None, "6h": None}
    assert result["horizon_unavailable_reason"]["6h"] == "solver_stopped_before_horizon"
    assert result["probability"] is None


def test_prepare_only_freezes_plan_before_inputs_and_preserves_source(
    terrain, weather, tmp_path, monkeypatch
):
    terrain_path, _, _ = terrain
    weather_path, _ = weather
    receipt = {
        "binary_sha256": "test",
        "license": "research test fixture",
        "license_scope": "no operational use",
        "license_sha256": {},
    }
    probe_path = tmp_path / "probe.json"
    module.write_json(probe_path, receipt)
    monkeypatch.setattr(module, "verify_source", lambda _: (receipt, tmp_path / "bin/elmfire_1.1"))
    original_prepare = module.prepare_case
    output = tmp_path / "run"

    def prepare(*args):
        assert (output / "plan.json").is_file()
        return original_prepare(*args)

    monkeypatch.setattr(module, "prepare_case", prepare)
    digest = module.sha256(terrain_path)
    report = module.execute(probe_path, terrain_path, weather_path, output, 1, prepare_only=True)
    assert report["status"] == "prepared"
    assert [case["fuel_model"] for case in report["cases"]] == [181, 183, 185]
    assert module.sha256(terrain_path) == digest
    assert all(point["probability"] is None for point in report["probes"])
    assert all(
        point["scenario_fraction"] == dict.fromkeys(module.HORIZONS) for point in report["probes"]
    )
    collection = json.loads((output / "probes.geojson").read_text())
    assert len(collection["features"]) == 5
    assert collection["operational_use"] is False


def test_failed_preflight_runs_no_cases(terrain, weather, tmp_path, monkeypatch):
    terrain_path, _, _ = terrain
    weather_path, data = weather
    data["wind_axis_basis_verified"] = False
    module.write_json(weather_path, data)
    monkeypatch.setattr(module, "verify_source", lambda _: ({}, tmp_path / "missing"))
    report = module.execute(tmp_path / "probe", terrain_path, weather_path, tmp_path / "fail", 1)
    assert report["status"] == "failed"
    assert not report["cases"]
    assert not (tmp_path / "fail/plan.json").exists()
