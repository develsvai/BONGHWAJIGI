"""Fixed-case and output-trace guards for canopy ablations; no real future labels."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "elmfire_canopy_hindcast", TOOLS / "elmfire_canopy_hindcast.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
sys.path.pop(0)


def conservative(complete=False):
    return {
        "full_horizon_completed": complete,
        "early_stop_detected": not complete,
        "horizon_completed": {"1h": True, "3h": True, "6h": complete},
    }


def test_all_six_crown_moisture_conditions_fixed_without_new_moistures():
    cases = module.FIXED_CASES
    assert len(cases) == 6 and len({c["id"] for c in cases}) == 6
    assert {(c["crown_fire_model"], tuple(c["dead_moisture_percent"])) for c in cases} == {
        (crown, moisture) for crown in (0, 1) for moisture in ((3, 4, 5), (6, 7, 8), (9, 10, 11))
    }


@pytest.mark.parametrize("start,dt", [(21595, 5), (21580, 20), (21587.5, 12.5)])
def test_trace_does_not_assume_last_step_starts_at21595(tmp_path, monkeypatch, start, dt):
    monkeypatch.setattr(module.common, "inspect_coverage", lambda _p: conservative())
    (tmp_path / "run.log").write_text(
        f"BONGHWA_RK2_ENDPOINT {start} {dt} 21600 21600 0.0005\n"
        "STOPPING: FIRE FRONT PROPAGATION STALLED\n"
    )
    result = module.trace_coverage(tmp_path)
    assert result["horizon_completed"]["6h"]
    assert not result["conservative_original_inspection"]["horizon_completed"]["6h"]


def test_early_actual_stop_keeps6h_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(module.common, "inspect_coverage", lambda _p: conservative())
    (tmp_path / "run.log").write_text(
        "BONGHWA_RK2_ENDPOINT 21550 10 21560 21600 0.0001\n"
        "STOPPING: FIRE FRONT PROPAGATION STALLED\n"
    )
    assert not module.trace_coverage(tmp_path)["horizon_completed"]["6h"]


def test_missing_trace_cannot_confirm_full_horizon(tmp_path, monkeypatch):
    monkeypatch.setattr(module.common, "inspect_coverage", lambda _p: conservative(True))
    (tmp_path / "run.log").write_text("End of simulation reached successfully")
    with pytest.raises(ValueError, match="must trace"):
        module.trace_coverage(tmp_path)


@pytest.mark.parametrize(
    "trace", ["21595 nan 21600 21600 0", "21595 5 21599 21600 0", "21595 30 21625 21600 0"]
)
def test_nonfinite_inconsistent_or_overshot_endpoint_rejected(tmp_path, monkeypatch, trace):
    monkeypatch.setattr(module.common, "inspect_coverage", lambda _p: conservative())
    (tmp_path / "run.log").write_text("BONGHWA_RK2_ENDPOINT " + trace + "\n")
    with pytest.raises(ValueError):
        module.trace_coverage(tmp_path)


def test_unrelated_stop_cannot_be_reclassified(tmp_path, monkeypatch):
    monkeypatch.setattr(module.common, "inspect_coverage", lambda _p: conservative())
    (tmp_path / "run.log").write_text(
        "BONGHWA_RK2_ENDPOINT 21595 5 21600 21600 0.0005\n"
        "STOPPING: ELAPSED TIME GREATER THAN MAX_RUNTIME\n"
    )
    with pytest.raises(ValueError, match="Unexpected stop"):
        module.trace_coverage(tmp_path)


def test_canopy_insertion_preserves_first4bands_and_other_inputs(tmp_path):
    original, case = tmp_path / "original", tmp_path / "case"
    (original / "inputs").mkdir(parents=True)
    source = original / "inputs/landscape.tif"
    values = np.zeros((8, *module.base.SHAPE), dtype="float32")
    for i in range(4):
        values[i] = i + 1
    with rasterio.open(
        source,
        "w",
        driver="GTiff",
        count=8,
        dtype="float32",
        width=module.base.SHAPE[1],
        height=module.base.SHAPE[0],
        crs="EPSG:32610",
        transform=module.base.TRANSFORM,
        nodata=-9999,
    ) as target:
        target.write(values)
    (original / "inputs/elmfire.data").write_text("CROWN_FIRE_MODEL = 0\nOTHER_FIXED = 1\n")
    (original / "inputs/weather.marker").write_text("original identical weather")
    canopy = {
        p: np.full(module.base.SHAPE, v, dtype="float32")
        for p, v in (("CC", 50), ("CH", 100), ("CBH", 20), ("CBD", 15))
    }
    module.prepare_case(original, case, canopy, 1)
    with rasterio.open(case / "inputs/landscape.tif") as target:
        output = target.read()
    np.testing.assert_equal(output[:4], values[:4])
    assert output[4, 0, 0] == 50 and output[5, 0, 0] == 100
    assert (case / "inputs/weather.marker").read_bytes() == (
        original / "inputs/weather.marker"
    ).read_bytes()
    assert (case / "inputs/elmfire.data").read_text() == "CROWN_FIRE_MODEL = 1\nOTHER_FIXED = 1\n"
    assert (original / "inputs/elmfire.data").read_text().startswith("CROWN_FIRE_MODEL = 0")


def test_comparison_keeps_unavailable_cases_undefined():
    evaluation = {"baseline": {"name": "unchanged"}, "cases": {}}
    baseline = {"baseline": evaluation["baseline"], "cases": {}}
    for c in module.FIXED_CASES:
        evaluation["cases"][c["id"]] = {
            h: {"status": "unavailable", "metrics": None} for h in module.base.HORIZONS
        }
        baseline["cases"][c["baseline_id"]] = {
            h: {"metrics": {"new_growth_iou": 0.1, "new_growth_recall": 0.1}}
            for h in module.base.HORIZONS
        }
    result = module.compare_baseline(evaluation, baseline)
    assert all(x["6h"]["new_growth_iou_delta"] is None for x in result.values())
