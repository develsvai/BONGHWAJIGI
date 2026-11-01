import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import xgboost as xgb

from bonghwa_training.download import file_sha256
from bonghwa_training.ranking_audit import (
    audit,
    select_candidates,
    standard_metrics,
    verify_inputs,
    workload_metrics,
)


def test_ties_are_label_independent_and_input_order_independent():
    scores = np.array([0.7, 0.7, 0.7, 0.7])
    rows, cols = np.array([3, 1, 1, 2]), np.array([0, 2, 1, 0])
    selected, _ = select_candidates(scores, rows, cols, 50)
    assert list(zip(rows[selected], cols[selected], strict=True)) == [(1, 1), (1, 2)]
    a = workload_metrics(np.array([1, 0, 1, 0]), scores, np.zeros(4), rows, cols, 50)
    b = workload_metrics(np.array([0, 1, 0, 1]), scores, np.zeros(4), rows, cols, 50)
    assert a["true_positives"] == b["true_positives"] == 1
    assert a["issues_with_boundary_ties"] == 1
    assert a["boundary_tie_candidates"] == 4
    order = np.array([3, 1, 0, 2])
    shuffled = workload_metrics(
        np.array([1, 0, 1, 0])[order], scores[order], np.zeros(4), rows[order], cols[order], 50
    )
    assert shuffled == a


def test_budget_is_applied_per_timestamp_not_globally():
    # A global top 50% would choose both cells at timestamp 20 and miss the positive at 10.
    result = workload_metrics(
        np.array([1, 0, 1, 0]),
        np.array([0.2, 0.1, 0.9, 0.8]),
        np.array([10, 10, 20, 20]),
        np.array([0, 1, 0, 1]),
        np.zeros(4),
        50,
    )
    assert result["issues"] == 2
    assert result["examined_candidates"] == 2
    assert result["true_positives"] == 2
    assert result["recall"] == 1
    assert result["precision"] == 1
    assert result["random_budget_expected_true_positives"] == 1
    assert result["lift_over_random_budget"] == 2


def test_random_budget_uses_each_issue_prevalence_and_ceiling():
    result = workload_metrics(
        np.array([1, 0, 0, 0, 0]),
        np.arange(5),
        np.array([1, 2, 2, 2, 2]),
        np.arange(5),
        np.zeros(5),
        20,
    )
    assert result["examined_candidates"] == 2
    assert result["actual_examined_fraction"] == 0.4
    assert result["random_budget_expected_true_positives"] == 1
    assert result["lift_over_random_budget"] == 1


def test_missing_scores_rank_last_and_undefined_results_are_null():
    chosen, _ = select_candidates([np.nan, 0.2, np.nan], [0, 1, 2], [0, 0, 0], 20)
    assert chosen.tolist() == [1]
    result = workload_metrics(
        np.zeros(3), np.array([np.nan, 0.2, np.nan]), np.zeros(3), np.arange(3), np.zeros(3), 20
    )
    assert result["recall"] is None and result["lift_over_random_budget"] is None
    assert result["missing_score_candidates"] == 2
    assert result["examined_missing_score_candidates"] == 0
    assert result["precision"] == 0
    json.dumps(result, allow_nan=False)
    empty = standard_metrics(np.array([]), np.array([]), probability=True)
    assert empty["average_precision"] is None and empty["brier"] is None
    json.dumps(empty, allow_nan=False)
    with pytest.raises(ValueError, match="중복"):
        select_candidates([1, 2], [0, 0], [0, 0], 20)


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


@pytest.fixture
def frozen_run(tmp_path):
    run, dataset = tmp_path / "run", tmp_path / "dataset"
    run.mkdir()
    dataset.mkdir()
    features = ["distance_fire_km", "horizon_hours"]
    event = {"id": "validation_2023", "split": "validation", "start_utc": "2023-04-02T00:00:00Z"}
    cfg = {
        "profile": "test_research",
        "feature_names": features,
        "events": [
            {"id": "absent_train", "split": "train"},
            event,
            {"id": "absent_cal", "split": "calibration"},
            {
                "id": "absent_test",
                "split": "test",
                "start_utc": "2025-03-22T00:00:00Z",
                "locked": True,
            },
        ],
    }
    config = tmp_path / "config.json"
    _write_json(config, cfg)
    (dataset / "config.json").write_bytes(config.read_bytes())
    _write_json(
        dataset / "report.json", {"config_sha256": file_sha256(config), "features": features}
    )
    values = {
        "distance_fire_km": np.tile([1.0, 2.0], 3),
        "distance_recent_fire_60m_km": np.tile([np.nan, 1.0], 3),
        "horizon_hours": np.repeat([1.0, 3.0, 6.0], 2),
        "fire_within_horizon": np.tile([1, 0], 3),
        "issue_epoch_seconds": np.full(6, 1680393600.0),
        "max_input_available_epoch_seconds": np.full(6, 1680393500.0),
        "row": np.tile([0, 1], 3),
        "col": np.zeros(6),
    }
    parquet = dataset / "validation_2023.parquet"
    pq.write_table(pa.table(values), parquet)
    _write_json(
        dataset / "validation_2023-report.json",
        {"event": event, "rows": 6, "sha256": file_sha256(parquet)},
    )
    model = xgb.train(
        {"objective": "binary:logistic", "device": "cpu", "nthread": 1},
        xgb.DMatrix(
            np.column_stack([values[f] for f in features]),
            label=values["fire_within_horizon"],
            feature_names=features,
        ),
        num_boost_round=1,
    )
    model.save_model(run / "selected.ubj")
    plan = {
        "features": features,
        "config_sha256": file_sha256(config),
        "cases": [{"name": "selected", "features": features}],
        "source_hashes": {event["id"]: file_sha256(parquet)},
    }
    _write_json(run / "plan.json", plan)
    report = {
        "profile": cfg["profile"],
        "plan_sha256": file_sha256(run / "plan.json"),
        "selected": "selected",
        "experiments": {
            "selected": {"features": features, "model_sha256": file_sha256(run / "selected.ubj")}
        },
    }
    _write_json(run / "report.json", report)
    return run, dataset, config, tmp_path / "output.json"


def test_audit_reads_only_validation_and_emits_finite_json(frozen_run, monkeypatch):
    read = pq.read_table
    opened = []

    def tracked(path, **kwargs):
        opened.append(Path(path).name)
        return read(path, **kwargs)

    monkeypatch.setattr(pq, "read_table", tracked)
    result = audit(*frozen_run)
    assert opened == ["validation_2023.parquet"]
    assert result["test_evaluated"] is False
    assert result["operational_use"] is False
    assert list(result["events"]) == ["validation_2023"]
    assert "negative_recent_fire_distance" in result["events"]["validation_2023"]["1"]
    assert result == json.loads(frozen_run[-1].read_text())
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("tamper", ["plan", "model", "config", "parquet", "feature_order"])
def test_audit_rejects_artifact_drift(frozen_run, tamper):
    run, dataset, config, output = frozen_run
    if tamper in ("plan", "model", "config", "parquet"):
        path = {
            "plan": run / "plan.json",
            "model": run / "selected.ubj",
            "config": config,
            "parquet": dataset / "validation_2023.parquet",
        }[tamper]
        path.write_bytes(path.read_bytes() + b" ")
    else:
        report = json.loads((run / "report.json").read_text())
        report["experiments"]["selected"]["features"].reverse()
        _write_json(run / "report.json", report)
    with pytest.raises(ValueError):
        audit(run, dataset, config, output)
    assert not output.exists()


def test_rejects_2025_validation_before_reading_any_parquet(frozen_run, monkeypatch):
    run, dataset, config, _ = frozen_run
    cfg = json.loads(config.read_text())
    cfg["events"][1]["start_utc"] = "2025-01-01T00:00:00Z"
    _write_json(config, cfg)
    (dataset / "config.json").write_bytes(config.read_bytes())
    drep = json.loads((dataset / "report.json").read_text())
    drep["config_sha256"] = file_sha256(config)
    _write_json(dataset / "report.json", drep)
    plan = json.loads((run / "plan.json").read_text())
    plan["config_sha256"] = file_sha256(config)
    _write_json(run / "plan.json", plan)
    report = json.loads((run / "report.json").read_text())
    report["plan_sha256"] = file_sha256(run / "plan.json")
    _write_json(run / "report.json", report)

    def forbidden(*args, **kwargs):
        raise AssertionError("holdout Parquet must never be opened")

    monkeypatch.setattr(pq, "read_table", forbidden)
    with pytest.raises(ValueError, match="2025"):
        verify_inputs(run, dataset, config)
