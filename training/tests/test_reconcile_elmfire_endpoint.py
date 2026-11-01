"""Synthetic failure checks for evidence-bound endpoint reconciliation."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "reconcile_elmfire_endpoint", TOOLS / "reconcile_elmfire_endpoint.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
sys.path.pop(0)


def log(endpoint="21595 5 21600 21600 0.00065", stop="STOPPING: FIRE FRONT PROPAGATION STALLED"):
    return (
        "BONGHWA_RK2_ENDPOINT "
        + endpoint
        + "\n"
        + stop
        + "\nEnd of simulation reached successfully\n"
    )


def test_accepts_completed_final_step_only():
    assert module.parse_endpoints(log())[-1]["integrated_until_seconds"] == 21600


@pytest.mark.parametrize(
    "endpoint",
    [
        "21595 4 21599 21600 0.00065",
        "21595 5 21600 21600 nan",
        "21595 5 21599 21600 0.00065",
        "21595 5 21600 21600 0.001",
        "21594 6 21600 21600 0.00065",
    ],
)
def test_rejects_incomplete_or_inconsistent_endpoint(endpoint):
    with pytest.raises(ValueError):
        module.parse_endpoints(log(endpoint))


def test_rejects_missing_trace_or_unrelated_stop():
    with pytest.raises(ValueError, match="Missing"):
        module.parse_endpoints("Current Timestep:21595 of21600\n" + log().split("\n", 1)[1])
    with pytest.raises(ValueError, match="stop reasons"):
        module.parse_endpoints(log(stop="STOPPING: ELAPSED TIME GREATER THAN MAX_RUNTIME"))


def test_requires_post_integration_trace_before_stop():
    with pytest.raises(ValueError, match="precede"):
        module.parse_endpoints(
            "STOPPING: FIRE FRONT PROPAGATION STALLED\n"
            "BONGHWA_RK2_ENDPOINT 21595 5 21600 21600 0.00065\n"
            "End of simulation reached successfully"
        )


def test_rejects_any_source_edit_beyond_output_patch():
    before = "before\n" + module.ANCHOR + "after\n"
    after = before.replace(module.ANCHOR, module.ANCHOR + module.ADDED)
    patch = "".join(
        module.difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile="original/elmfire_level_set.f90",
            tofile="diagnostic/elmfire_level_set.f90",
        )
    )
    module.validate_instrumentation(before, after, patch)
    with pytest.raises(ValueError, match="output-only"):
        module.validate_instrumentation(before, after.replace("after", "DT=10"), patch)
    with pytest.raises(ValueError, match="patch differs"):
        module.validate_instrumentation(before, after, patch + "extra")


def test_rejects_tampered_or_extra_artifact_file(tmp_path):
    path = tmp_path / "test"
    path.write_text("fixed")
    frozen = module.hashes(tmp_path)
    module.verify_hashes(tmp_path, frozen)
    path.write_text("changed")
    with pytest.raises(ValueError, match="changed"):
        module.verify_hashes(tmp_path, frozen)
    path.write_text("fixed")
    (tmp_path / "extra").write_text("extra")
    with pytest.raises(ValueError, match="changed"):
        module.verify_hashes(tmp_path, frozen)


def test_requires_identical_arrival_cells(tmp_path):
    paths = [tmp_path / name for name in ("a.tif", "b.tif")]
    values = np.array([[0, 30], [-9999, 120]], dtype="float32")
    profile = dict(
        driver="GTiff",
        height=2,
        width=2,
        count=1,
        dtype="float32",
        nodata=-9999,
        crs="EPSG:32610",
        transform=from_origin(100, 200, 100, 100),
    )
    for path in paths:
        with rasterio.open(path, "w", **profile) as target:
            target.write(values, 1)
    assert module.compare_arrivals(*paths)["all_cells_identical"]
    values[1, 1] = 121
    with rasterio.open(paths[1], "w", **profile) as target:
        target.write(values, 1)
    with pytest.raises(ValueError, match="arrival values"):
        module.compare_arrivals(*paths)


def evaluation():
    return {
        "baseline": {"horizons": "fixed"},
        "cases": {
            name: {h: {"metrics": {"recall": 0.1}} for h in ("1h", "3h", "6h")}
            for name in module.CASE_IDS
        },
    }


def test_short_horizon_metrics_and_fixed_cases_must_be_preserved():
    original, revised = evaluation(), evaluation()
    revised["cases"][module.CASE_IDS[0]]["6h"] = {"new": "evaluation"}
    module.preserve_short_metrics(original, revised)
    revised["cases"][module.CASE_IDS[1]]["1h"]["metrics"]["recall"] = 0.2
    with pytest.raises(ValueError, match="short-horizon metric changed"):
        module.preserve_short_metrics(original, revised)
    del revised["cases"][module.CASE_IDS[1]]
    with pytest.raises(ValueError, match="three fixed"):
        module.preserve_short_metrics(original, revised)


def test_mismatching_report_sha_blocks_before_reading_json(tmp_path):
    (tmp_path / "report.json").write_text("not json")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        module.verify_diagnostic(tmp_path, tmp_path, "a" * 64)
