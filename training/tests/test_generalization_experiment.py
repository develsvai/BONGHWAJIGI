import json
from types import SimpleNamespace

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from bonghwa_training import generalization_experiment as study
from bonghwa_training.download import file_sha256

FEATURES = [
    "distance_fire_km",
    "utc_hour_sin",
    "utc_hour_cos",
    "weather_station_distance_km",
    "weather_age_hours",
    "horizon_hours",
]


def test_equal_event_weights_use_only_training_events_and_preserve_mean_one():
    def event(size, value):
        return {"x": np.full((size, len(FEATURES)), value), "y": np.arange(size) % 2}

    events = {"small": event(2, 1), "large": event(6, 2), "held_out": event(200, 999)}
    candidate = study.make_candidates(FEATURES)[2]
    x, y, groups, weights = study.stack_training(events, ["small", "large"], FEATURES, candidate)
    assert len(x) == len(y) == 8
    assert not np.any(x == 999)
    assert set(groups) == {"small", "large"}
    assert weights.mean() == pytest.approx(1)
    assert weights[groups == "small"].sum() == pytest.approx(4)
    assert weights[groups == "large"].sum() == pytest.approx(4)
    assert study.sample_weights(groups, False).tolist() == [1] * 8


def test_prespecified_candidates_ablate_only_clock_station_features():
    cases = study.make_candidates(FEATURES)
    assert [c["name"] for c in cases] == [
        "reference_depth4",
        "shallow_depth2",
        "shallow_equal_events",
        "shallow_no_clock_station",
    ]
    assert cases[0]["parameters"]["max_depth"] == 4
    assert cases[0]["parameters"]["min_child_weight"] == 5
    assert cases[1]["parameters"] == cases[2]["parameters"] == cases[3]["parameters"]
    assert cases[1]["equal_event_mass"] is False
    assert cases[2]["equal_event_mass"] is True
    assert cases[3]["equal_event_mass"] is True
    assert cases[0]["features"] == cases[1]["features"] == cases[2]["features"] == FEATURES
    assert cases[3]["features"] == ["distance_fire_km", "horizon_hours"]
    for case in cases:
        assert case["rounds"] == 100
        assert case["parameters"]["device"] == "cpu"
        assert case["parameters"]["nthread"] == 2
        assert case["parameters"]["scale_pos_weight"] == 1
        assert case["parameters"]["seed"] == 47
        assert case["monotone_constraints"] == [0] * (len(case["features"]) - 1) + [1]


@pytest.mark.parametrize(
    "changes,allowed",
    [
        ({"split": "test"}, "test"),
        ({"split": "calibration"}, "calibration"),
        ({"split": "validation"}, "train"),
        ({"locked": True}, "train"),
        ({"start_utc": "2025-01-01T00:00:00Z"}, "train"),
    ],
)
def test_forbidden_splits_and_dates_rejected_before_file_access(tmp_path, changes, allowed):
    event = {"id": "example", "split": "train", "start_utc": "2023-01-01T00:00:00Z", **changes}
    with pytest.raises(ValueError):
        study.load_event(tmp_path, event, FEATURES, allowed)


def test_single_class_fold_is_not_fake_perfect_ap():
    result = study.summarize(np.ones(3), np.array([0.8, 0.7, 0.6]), np.array([1, 3, 6]))
    for cell in result.values():
        assert cell["average_precision"] is None
        assert cell["eligible_for_cv_selection"] is False
        assert cell["exclusion_reason"]
    json.dumps(result, allow_nan=False)


def _json(path, value):
    path.write_text(json.dumps(value) + "\n")


@pytest.fixture
def tiny_dataset(tmp_path):
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    events = [
        {"id": f"training_{i}", "split": "train", "start_utc": "2022-01-01T00:00:00Z"}
        for i in range(4)
    ]
    events += [
        {"id": "validation_2023", "split": "validation", "start_utc": "2023-01-01T00:00:00Z"},
        {"id": "missing_cal", "split": "calibration"},
        {"id": "missing_test_2025", "split": "test", "locked": True},
    ]
    config = tmp_path / "config.json"
    _json(config, {"profile": study.PROFILE, "feature_names": FEATURES, "events": events})
    (dataset / "config.json").write_bytes(config.read_bytes())
    for event in events[:5]:
        y = np.tile([0, 1, 0, 1], 3)
        values = {f: np.arange(12, dtype=float) for f in FEATURES}
        values.update(
            {
                "fire_within_horizon": y,
                "horizon_hours": np.repeat([1, 3, 6], 4),
                "issue_epoch_seconds": np.full(12, 1640995200.0),
                "max_input_available_epoch_seconds": np.full(12, 1640995100.0),
            }
        )
        path = dataset / f"{event['id']}.parquet"
        pq.write_table(pa.table(values), path)
        _json(
            dataset / f"{event['id']}-report.json",
            {"sha256": file_sha256(path), "event": event, "rows": 12},
        )
    return SimpleNamespace(
        dataset=dataset, config=config, output=tmp_path / "output", reference_run=None
    )


def test_full_bounded_run_opens_validation_only_after_selection(tiny_dataset, monkeypatch):
    original_load = study.load_event
    order = []

    def tracked(dataset, event, features, allowed_split):
        order.append(event["split"])
        if event["split"] == "validation":
            assert (tiny_dataset.output / "selection.json").is_file()
            assert (tiny_dataset.output / "selected.ubj").is_file()
        return original_load(dataset, event, features, allowed_split)

    monkeypatch.setattr(study, "load_event", tracked)
    result = study.experiment(tiny_dataset)
    assert order == ["train"] * 4 + ["validation"]
    assert result["saved_trees"] == 100
    assert result["eligible_cv_cell_count"] == 12
    assert len(result["cv"]) == 4
    assert result["monotonicity_verified"] is True
    assert result["operational_use"] is False and result["test_evaluated"] is False
    assert result["probability_calibrated"] is False
    json.dumps(result, allow_nan=False)


def test_failed_folds_are_persisted_and_validation_stays_unread(tiny_dataset, monkeypatch):
    def failing_fit(*args):
        raise ValueError("deliberate fit failure")

    monkeypatch.setattr(study, "fit", failing_fit)
    with pytest.raises(RuntimeError, match="실패한 CV fold"):
        study.experiment(tiny_dataset)
    failure = json.loads((tiny_dataset.output / "failure.json").read_text())
    assert failure["validation_read"] is False
    assert len(failure["cv"]) == 4
    assert not (tiny_dataset.output / "selection.json").exists()
    for candidate in failure["cv"].values():
        assert candidate["status"] == "failed"
        assert candidate["mean_event_horizon_ap"] is None
        assert len(candidate["folds"]) == 4


def test_tampered_event_hash_rejected(tiny_dataset):
    cfg = json.loads(tiny_dataset.config.read_text())
    path = tiny_dataset.dataset / "training_0.parquet"
    path.write_bytes(path.read_bytes() + b"bad")
    with pytest.raises(ValueError, match="SHA"):
        study.load_event(tiny_dataset.dataset, cfg["events"][0], FEATURES, "train")
