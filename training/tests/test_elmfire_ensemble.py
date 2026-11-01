"""No real wildfire observations or personal locations are used in these tests."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

PATH = Path(__file__).resolve().parents[1] / "tools/elmfire_ensemble.py"
SPEC = importlib.util.spec_from_file_location("elmfire_ensemble", PATH)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def case(value, *, initial=False):
    return {
        "status": "complete",
        "probes": [
            {
                "id": name,
                "arrival_seconds": value,
                "state": "initially_reached"
                if initial
                else ("unreached_within_horizon" if value is None else "future_arrival"),
            }
            for name, _, _ in module.PROBES
        ],
    }


def test_fractions_use_frozen_denominator_and_monotone_horizons():
    cases = [
        case(1800),
        case(3600),
        case(7200),
        case(10800),
        case(15000),
        case(21600),
        case(None),
        case(None),
        case(None),
    ]
    for result in module.aggregate(cases):
        assert result["scenario_fraction"] == {"1h": 2 / 9, "3h": 4 / 9, "6h": 6 / 9}
        assert result["probability"] is None
        assert result["operational_use"] is False


def test_partial_failure_is_never_an_unburned_negative():
    cases = [case(1000)] * 8 + [{"status": "failed"}]
    result = module.aggregate(cases)[0]
    assert result["scenario_fraction"] == dict.fromkeys(module.HORIZONS)
    assert result["completed_scenarios"] == 8
    assert result["future_arrival_counts"]["1h"] == 8
    assert result["unavailable_reason"] == "partial_or_failed_ensemble"


def test_initial_exposure_is_not_a_future_first_arrival():
    result = module.aggregate([case(0, initial=True)] + [case(1000)] * 8)[0]
    assert result["initially_reached_scenarios"] == 1
    assert result["scenario_fraction"] == dict.fromkeys(module.HORIZONS)
    assert result["future_arrival_counts"]["1h"] == 8


def test_all_successful_unreached_is_a_scenario_zero_not_verified_safety():
    result = module.aggregate([case(None)] * 9)[0]
    assert result["scenario_fraction"] == {"1h": 0, "3h": 0, "6h": 0}
    assert result["probability"] is None
    assert result["simulation_only"] is True


def test_stop_time_update_does_not_change_other_inputs():
    text = "&TIME_CONTROL\nSIMULATION_DT = 30\nSIMULATION_TSTOP = 19800.0\n/\n"
    result = module.set_stop_time(text)
    assert "SIMULATION_DT = 30" in result
    assert "SIMULATION_TSTOP = 21600.0" in result
    with pytest.raises(ValueError):
        module.set_stop_time("&TIME_CONTROL\n/\n")


def test_wind_rewrite_preserves_mask_georeferencing_and_source_copy(tmp_path):
    path = tmp_path / "ws.tif"
    values = np.array([[15, -9999], [15, 15]], dtype="float32")
    transform = from_origin(-6000, 6000, 30, 30)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=2,
        width=2,
        count=1,
        dtype="float32",
        crs="EPSG:32610",
        transform=transform,
        nodata=-9999,
    ) as output:
        output.write(values, 1)
    module.replace_constant_raster(path, 20)
    with rasterio.open(path) as result:
        np.testing.assert_equal(result.read(1), [[20, -9999], [20, 20]])
        assert result.transform == transform
        assert result.crs.to_epsg() == 32610


def test_unapproved_source_receipt_stops_before_plan_or_cases(tmp_path):
    receipt = tmp_path / "source.json"
    receipt.write_text('{"status":"failed"}')
    output = tmp_path / "output"
    result = module.execute(receipt, output, 1)
    assert result["status"] == "failed"
    assert result["cases"] == []
    assert not (output / "plan.json").exists()
    assert all(item["scenario_fraction"]["1h"] is None for item in result["probes"])
