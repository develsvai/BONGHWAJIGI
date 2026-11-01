import json
import warnings
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from sklearn.exceptions import ConvergenceWarning

from bonghwa_training import expanded_oof_calibration as study
from bonghwa_training.download import file_sha256

FEATURES = ["distance_fire_km", "distance_recent_fire_60m_km", "horizon_hours"]


def write_json(path, value):
    path.write_text(json.dumps(value) + "\n")


@pytest.fixture
def inputs(tmp_path):
    dataset, run = tmp_path / "dataset", tmp_path / "groupcv"
    dataset.mkdir()
    events = [
        {"id": name, "split": split, "start_utc": date + "T00:00:00Z", "hours": 12}
        for name, split, date in [
            ("train_a", "train", "2020-04-25"),
            ("train_b", "train", "2021-02-21"),
            ("train_c", "train", "2022-03-04"),
            ("empty_train", "train", "2022-05-01"),
            ("validation", "validation", "2023-04-02"),
            ("empty_validation", "validation", "2023-04-03"),
        ]
    ]
    cfg = {
        "profile": study.expanded.PROFILE,
        "reader": "gk2a",
        "horizons_hours": [1, 3, 6],
        "feature_names": FEATURES,
        "events": events
        + [
            {"id": "forbidden_calibration", "split": "calibration"},
            {"id": "forbidden_test_2025", "split": "test", "locked": True},
        ],
    }
    config = tmp_path / "config.json"
    write_json(config, cfg)
    (dataset / "config.json").write_bytes(config.read_bytes())
    for event in events:
        count = 0 if event["id"].startswith("empty") else 96
        indices = np.tile(np.arange(32), 3)[:count]
        start = study.datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00"))
        table = pa.table(
            {
                "distance_fire_km": indices.astype(float) + 1,
                "distance_recent_fire_60m_km": indices.astype(float) + 0.5,
                "horizon_hours": np.repeat([1, 3, 6], 32)[:count],
                "fire_within_horizon": (indices < 16).astype(int),
                "issue_epoch_seconds": np.full(count, start.timestamp() + 900),
                "max_input_available_epoch_seconds": np.full(count, start.timestamp()),
                "row": indices,
                "col": np.zeros(count),
            }
        )
        path = dataset / f"{event['id']}.parquet"
        pq.write_table(table, path)
        write_json(
            path.with_name(f"{event['id']}-report.json"),
            {
                "rows": count,
                "sha256": file_sha256(path),
                "event": event,
                "unusable_reason": "no observed rows" if not count else None,
            },
        )
    study.expanded.experiment(SimpleNamespace(dataset=dataset, config=config, output=run))
    return SimpleNamespace(dataset=dataset, config=config, run=run, output=tmp_path / "calibration")


def test_full_replay_fits_only_oof_rows_and_receipt_precedes_validation(inputs, monkeypatch):
    load, fit, sigmoid = study.expanded.load_event, study.expanded.fit, study.fit_sigmoid
    loaded, fitted, fitting = [], [], []

    def tracked_load(dataset, event, features, split):
        assert split in ("train", "validation")
        loaded.append(event["id"])
        if split == "validation":
            receipt = json.loads((inputs.output / "calibrator.json").read_text())
            assert receipt["status"] == "fitted_research_only"
            assert receipt["validation_event_data_read_before_receipt"] is False
        return load(dataset, event, features, split)

    def tracked_fit(events, ids, features, candidate):
        assert (inputs.output / "plan.json").exists()
        assert len(ids) == 2
        assert "empty_train" not in ids
        fitted.append(ids)
        return fit(events, ids, features, candidate)

    def tracked_sigmoid(p, y):
        with np.load(inputs.output / "training-oof.npz") as data:
            np.testing.assert_array_equal(p, data["raw_score"])
            np.testing.assert_array_equal(y, data["label"])
        fitting.append(len(y))
        return sigmoid(p, y)

    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        assert "forbidden_" not in path.name
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(study.expanded, "load_event", tracked_load)
    monkeypatch.setattr(study.expanded, "fit", tracked_fit)
    monkeypatch.setattr(study, "fit_sigmoid", tracked_sigmoid)
    result = study.experiment(inputs)
    assert len(fitted) == 3 and fitting == [288]
    assert loaded == [
        "train_a",
        "train_b",
        "train_c",
        "empty_train",
        "validation",
        "empty_validation",
    ]
    assert result["status"] == "evaluated_research_only"
    assert result["calibration_fitted"] is True
    assert result["probability_calibrated"] is result["operational_use"] is False
    assert result["calibration_split_read"] is result["test_evaluated"] is False
    assert result["maximum_absolute_validation_ap_change"] == pytest.approx(0)
    assert result["validation"]["sigmoid"]["empty_validation"]["1"]["brier"] is None
    with np.load(inputs.output / "training-oof.npz") as data:
        identities = np.column_stack((data["event_index"], data["source_row_index"]))
        assert len(np.unique(identities, axis=0)) == 288
    json.dumps(result, allow_nan=False)


def test_oof_duplicate_assignment_and_missing_rows_are_rejected():
    predictions = {"event": np.full(3, np.nan)}
    coverage = {"event": np.zeros(3, dtype=np.uint8)}
    study.assign_oof(predictions, coverage, "event", np.array([0, 2]), np.array([0.2, 0.7]))
    with pytest.raises(ValueError, match="OOF 행"):
        study.assign_oof(predictions, coverage, "event", np.array([0]), np.array([0.1]))
    with pytest.raises(ValueError, match="누락"):
        study.check_coverage(predictions, coverage)
    study.assign_oof(predictions, coverage, "event", np.array([1]), np.array([0.4]))
    study.check_coverage(predictions, coverage)


@pytest.mark.parametrize("p", [np.array([0.9, 0.8, 0.2, 0.1]), np.full(4, 0.5)])
def test_negative_or_zero_slope_is_withheld(p):
    result = study.fit_sigmoid(p, np.array([0, 0, 1, 1]))
    assert result["status"] == "withheld"
    assert result["calibration_fitted"] is True
    assert result["reason"] == "nonpositive_slope"
    with pytest.raises(ValueError, match="보류"):
        study.transform(p, result)


def test_nonconvergence_is_withheld_with_fixed_unweighted_parameters(monkeypatch):
    class Unconverged:
        def __init__(self, **kwargs):
            assert kwargs == {
                "C": 1.0,
                "class_weight": None,
                "solver": "lbfgs",
                "max_iter": 1000,
                "random_state": 47,
            }

        def fit(self, x, y):
            assert x.shape == (4, 1)
            warnings.warn("not converged", ConvergenceWarning, stacklevel=2)
            self.coef_, self.intercept_, self.n_iter_ = np.array([[1.0]]), np.array([0.0]), [1000]
            return self

    monkeypatch.setattr(study, "LogisticRegression", Unconverged)
    result = study.fit_sigmoid(np.array([0.1, 0.2, 0.8, 0.9]), np.array([0, 0, 1, 1]))
    assert result["status"] == "withheld" and result["reason"] == "nonconvergence"


def test_withheld_receipt_prevents_any_validation_event_read(inputs, monkeypatch):
    load = study.expanded.load_event

    def train_only(dataset, event, features, split):
        assert split == "train"
        return load(dataset, event, features, split)

    monkeypatch.setattr(study.expanded, "load_event", train_only)
    monkeypatch.setattr(
        study,
        "fit_sigmoid",
        lambda p, y: {
            "status": "withheld",
            "calibration_fitted": True,
            "slope": -0.5,
            "intercept": 0.0,
            "reason": "nonpositive_slope",
        },
    )
    result = study.experiment(inputs)
    assert result["status"] == "withheld" and result["validation_read"] is False
    assert result["calibration_fitted"] is True
    assert (inputs.output / "calibrator.json").exists()


@pytest.mark.parametrize("tamper", ["model", "cv_result"])
def test_tampered_frozen_artifacts_rejected_before_replay(inputs, monkeypatch, tamper):
    report = json.loads((inputs.run / "report.json").read_text())
    selected = report["selected"]
    path = inputs.run / (f"{selected}.ubj" if tamper == "model" else f"{selected}-cv.json")
    path.write_bytes(path.read_bytes() + b" ")

    def no_fit(*args, **kwargs):
        raise AssertionError("a changed frozen run must be rejected before replay")

    monkeypatch.setattr(study.expanded, "fit", no_fit)
    with pytest.raises(ValueError, match="SHA"):
        study.experiment(inputs)
    assert not inputs.output.exists()


def test_positive_sigmoid_preserves_order_including_clipped_boundaries():
    p = np.array([0, 1e-9, 0.1, 0.5, 0.8, 1 - 1e-9, 1])
    calibration = {"status": "fitted_research_only", "slope": 0.8, "intercept": -0.2}
    transformed = study.transform(p, calibration)
    assert np.all(np.diff(transformed) >= 0)
    assert np.isfinite(transformed).all()
    assert transformed[0] == transformed[1]
    assert transformed[-1] == transformed[-2]


def test_changed_period_group_rejected_even_with_rebound_outer_hashes(inputs, monkeypatch):
    plan_path = inputs.run / "plan.json"
    plan = json.loads(plan_path.read_text())
    group = next(iter(plan["period_groups"]))
    plan["period_groups"][group] = []
    write_json(plan_path, plan)
    selection_path = inputs.run / "selection.json"
    selection = json.loads(selection_path.read_text())
    selection["plan_sha256"] = file_sha256(plan_path)
    write_json(selection_path, selection)
    report_path = inputs.run / "report.json"
    report = json.loads(report_path.read_text())
    report.update(plan_sha256=file_sha256(plan_path), selection_sha256=file_sha256(selection_path))
    write_json(report_path, report)

    def no_fit(*args, **kwargs):
        raise AssertionError("changed period groups must fail before replay")

    monkeypatch.setattr(study.expanded, "fit", no_fit)
    with pytest.raises(ValueError, match="기간그룹"):
        study.experiment(inputs)
    assert not inputs.output.exists()
