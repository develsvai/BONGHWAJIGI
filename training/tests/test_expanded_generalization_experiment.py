import ast
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from bonghwa_training import expanded_generalization_experiment as study
from bonghwa_training.download import file_sha256

FEATURES = ["distance_fire_km", "distance_recent_fire_60m_km", "horizon_hours"]


def _json(path, value):
    path.write_text(json.dumps(value) + "\n")


@pytest.fixture
def tiny_dataset(tmp_path):
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    events = [
        {"id": name, "split": split, "start_utc": date + "T00:00:00Z", "hours": 12}
        for name, split, date in [
            ("march4", "train", "2022-03-04"),
            ("march5", "train", "2022-03-05"),
            ("april_a", "train", "2022-04-10"),
            ("april_b", "train", "2022-04-10"),
            ("other", "train", "2020-04-25"),
            ("empty_train", "train", "2022-05-01"),
            ("validation", "validation", "2023-04-02"),
            ("empty_validation", "validation", "2023-04-03"),
        ]
    ]
    # Forbidden files deliberately do not exist; their event metadata is never loaded.
    events += [
        {"id": "forbidden_cal", "split": "calibration"},
        {"id": "forbidden_test_2025", "split": "test", "locked": True},
    ]
    config = tmp_path / "config.json"
    _json(
        config,
        {
            "profile": study.PROFILE,
            "reader": "gk2a",
            "horizons_hours": [1, 3, 6],
            "feature_names": FEATURES,
            "events": events,
        },
    )
    (dataset / "config.json").write_bytes(config.read_bytes())
    for event in events[:8]:
        size = 0 if event["id"].startswith("empty") else 12
        start = study.datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00"))
        values = {
            "distance_fire_km": np.tile([3.0, 1.0, 4.0, 2.0], 3)[:size],
            "distance_recent_fire_60m_km": np.tile([4.0, 2.0, 3.0, 1.0], 3)[:size],
            "horizon_hours": np.repeat([1, 3, 6], 4)[:size],
            "fire_within_horizon": np.tile([0, 1, 0, 1], 3)[:size],
            "issue_epoch_seconds": np.full(size, start.timestamp() + 900),
            "max_input_available_epoch_seconds": np.full(size, start.timestamp()),
            "row": np.tile([1, 2, 3, 4], 3)[:size],
            "col": np.zeros(size),
        }
        path = dataset / f"{event['id']}.parquet"
        pq.write_table(pa.table(values), path)
        _json(
            dataset / f"{event['id']}-report.json",
            {
                "sha256": file_sha256(path),
                "event": event,
                "rows": size,
                "unusable_reason": "no observed candidates" if not size else None,
            },
        )
    return SimpleNamespace(dataset=dataset, config=config, output=tmp_path / "output")


def test_fixed_candidates_separate_weighting_event_mass_and_regularization():
    cases = study.make_candidates(FEATURES)
    assert len(cases) == 5
    assert [c["positive_weight_rule"] for c in cases] == [
        "unit",
        "fixed3",
        "training_fold_sqrt",
        "unit",
        "unit",
    ]
    assert [c["equal_event_mass"] for c in cases] == [False, False, False, True, True]
    assert [c["parameters"]["max_depth"] for c in cases] == [4, 4, 4, 4, 2]
    for case in cases:
        assert case["features"] == FEATURES
        assert case["rounds"] == 100
        assert case["parameters"]["device"] == "cpu"
        assert case["parameters"]["nthread"] == 2
        assert case["parameters"]["seed"] == 47
        assert case["monotone_constraints"] == [0, 0, 1]


def test_sqrt_weight_ignores_heldout_labels_and_caps_from_training_rows_only():
    candidate = study.make_candidates(FEATURES)[2]
    events = {"train": {"y": np.array([1, 0, 0, 0, 0])}, "held": {"y": np.ones(300)}}
    first = study.resolve_candidate(candidate, events, ["train"])
    events["held"]["y"] = np.zeros(300)
    second = study.resolve_candidate(candidate, events, ["train"])
    assert first["parameters"]["scale_pos_weight"] == 2.0
    assert first == second
    assert candidate["parameters"]["scale_pos_weight"] == 1.0
    events["train"]["y"] = np.r_[1, np.zeros(20000)]
    assert (
        study.resolve_candidate(candidate, events, ["train"])["parameters"]["scale_pos_weight"]
        == 100
    )


def test_single_class_and_empty_cells_have_null_ap_and_no_fake_perfect_scores():
    data = {
        "y": np.array([1, 1]),
        "h": np.array([1, 1]),
        "issues": np.array([0, 0]),
        "rows": np.array([1, 2]),
        "cols": np.array([0, 0]),
    }
    result = study.evaluate(data, np.array([0.3, 0.7]), probability=True)
    assert result["1"]["rows"] == 2
    assert result["1"]["average_precision"] is None
    assert result["3"]["rows"] == 0
    assert result["3"]["average_precision"] is None
    assert result["3"]["top_10_percent_per_issue"]["recall"] is None
    json.dumps(result, allow_nan=False)


def test_horizon_priors_ignore_predictions_and_nontraining_labels():
    events = {
        "train": {
            "event": {"split": "train"},
            "h": np.array([1, 1, 1, 1, 3, 3, 6, 6]),
            "y": np.array([0, 0, 0, 1, 0, 1, 1, 1]),
            "prediction": np.ones(8),
        },
        "validation": {
            "event": {"split": "validation"},
            "h": np.array([1, 3, 6]),
            "y": np.ones(3),
        },
    }
    priors = study.training_horizon_priors(events, ["train"])
    assert [priors[str(h)]["score"] for h in (1, 3, 6)] == [0.25, 0.5, 1.0]
    events["validation"]["y"][:] = 0
    events["train"]["prediction"][:] = 0
    assert study.training_horizon_priors(events, ["train"]) == priors
    assert study.prior_scores(np.array([6, 1, 3, 1]), priors).tolist() == [1, 0.25, 0.5, 0.25]
    with pytest.raises(ValueError, match="학습 사건"):
        study.training_horizon_priors(events, ["train", "validation"])


def test_event_equal_mass_and_positive_class_mass_are_reported_separately():
    def event(y):
        return {
            "y": np.asarray(y),
            "x": np.column_stack((np.arange(len(y)), np.arange(len(y)), np.ones(len(y)))),
        }

    events = {"small": event([0, 1]), "large": event([0, 0, 0, 0, 1, 1])}
    cases = study.make_candidates(FEATURES)
    _, equal, _ = study.fit(events, ["small", "large"], FEATURES, cases[3])
    assert equal["small"]["weight_share"] == pytest.approx(0.5)
    assert equal["large"]["weight_share"] == pytest.approx(0.5)
    assert equal["small"]["class_adjusted_weight_share"] == pytest.approx(0.5)
    _, weighted, _ = study.fit(events, ["small", "large"], FEATURES, cases[1])
    assert weighted["small"]["weight_sum"] == 2
    assert weighted["small"]["class_adjusted_weight_sum"] == 4
    assert weighted["large"]["class_adjusted_weight_sum"] == 10


def test_full_run_excludes_entire_period_groups_and_reads_validation_after_receipt(
    tiny_dataset, monkeypatch
):
    original_load, original_fit = study.load_event, study.fit
    loaded, fitted = [], []

    def tracked_load(dataset, event, features, split):
        loaded.append(event["id"])
        assert split in ("train", "validation")
        if split == "validation":
            assert (tiny_dataset.output / "selection.json").is_file()
            assert (tiny_dataset.output / "depth4_unit.ubj").is_file()
        return original_load(dataset, event, features, split)

    def tracked_fit(events, ids, features, candidate):
        assert (tiny_dataset.output / "plan.json").is_file()
        fitted.append(tuple(ids))
        assert ("march4" in ids) == ("march5" in ids)
        assert ("april_a" in ids) == ("april_b" in ids)
        assert "empty_train" not in ids
        return original_fit(events, ids, features, candidate)

    original_read = Path.read_text

    def guarded_read(path, *args, **kwargs):
        assert "forbidden_" not in path.name
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read)
    monkeypatch.setattr(study, "load_event", tracked_load)
    monkeypatch.setattr(study, "fit", tracked_fit)
    report = study.experiment(tiny_dataset)
    assert loaded[-2:] == ["validation", "empty_validation"]
    assert len(loaded) == 8
    assert report["training_event_count_requested"] == 6
    assert report["training_event_count_nonempty"] == 5
    assert report["training_period_group_count"] == 3
    assert report["eligible_cv_cell_count"] == 15
    assert len(fitted) in (16, 17)
    assert all(
        not report[name]
        for name in (
            "operational_use",
            "probability_calibrated",
            "calibration_read",
            "test_evaluated",
        )
    )
    assert report["validation_inventory"]["empty_validation"]["rows"] == 0
    prior = report["validation"]["constant_training_prior"]["validation"]["1"]
    assert prior["average_precision"] == pytest.approx(0.5)
    assert prior["brier"] == pytest.approx(0.25)
    assert prior["logloss"] == pytest.approx(np.log(2))
    plan = json.loads((tiny_dataset.output / "plan.json").read_text())
    assert plan["training_horizon_priors"] == report["training_horizon_priors"]
    assert report["input_variant"] == plan["input_variant"] == "observations"
    for result in report["cv_distance_baselines"].values():
        assert result["empty_train"]["1"]["average_precision"] is None
    assert report["validation"]["negative_recent_fire_distance"]["validation"]["1"]["brier"] is None
    json.dumps(report, allow_nan=False)


def test_exact_context_profile_trains_all_34_features(tiny_dataset):
    builder = Path(study.__file__).with_name("hourly_context.py")
    context = next(
        ast.literal_eval(node.value)
        for node in ast.parse(builder.read_text()).body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "CONTEXT" for t in node.targets)
    )
    v4 = json.loads((Path(__file__).parents[1] / "configs/korea-gk2a-hourly-v4.json").read_text())
    cfg = json.loads(tiny_dataset.config.read_text())
    cfg.update(
        {
            "profile": v4["profile"] + "_context_v1",
            "feature_names": [f for f in v4["feature_names"] if f != "horizon_hours"]
            + context
            + ["horizon_hours"],
            "context_features": context,
            "drop_features": v4["drop_features"],
        }
    )
    _json(tiny_dataset.config, cfg)
    (tiny_dataset.dataset / "config.json").write_bytes(tiny_dataset.config.read_bytes())
    for event in cfg["events"]:
        if event["split"] not in ("train", "validation"):
            continue
        path = tiny_dataset.dataset / f"{event['id']}.parquet"
        table = pq.read_table(path)
        for column in cfg["feature_names"]:
            if column not in table.column_names:
                table = table.append_column(column, pa.array(np.zeros(len(table))))
        pq.write_table(table, path)
        report_path = path.with_name(f"{event['id']}-report.json")
        report = json.loads(report_path.read_text())
        report["sha256"] = file_sha256(path)
        _json(report_path, report)
    report = study.experiment(tiny_dataset)
    plan = json.loads((tiny_dataset.output / "plan.json").read_text())
    assert report["profile"] == plan["profile"] == study.CONTEXT_PROFILE
    assert report["input_variant"] == plan["input_variant"] == "context"
    assert report["feature_count"] == plan["feature_count"] == 34
    assert all(len(c["features"]) == 34 for c in plan["candidates"])
    assert set(context).issubset(plan["features"])


def test_unknown_profile_rejected_even_with_matching_dataset_config(tiny_dataset):
    cfg = json.loads(tiny_dataset.config.read_text())
    cfg["profile"] = study.CONTEXT_PROFILE + "_unreviewed"
    _json(tiny_dataset.config, cfg)
    (tiny_dataset.dataset / "config.json").write_bytes(tiny_dataset.config.read_bytes())
    with pytest.raises(ValueError, match="자료 계약"):
        study.experiment(tiny_dataset)
    assert not tiny_dataset.output.exists()


def test_one_candidate_failure_aborts_selection_and_keeps_validation_unread(
    tiny_dataset, monkeypatch
):
    original_fit = study.fit

    def fail_one(events, ids, features, candidate):
        if candidate["name"] == "depth4_positive3":
            raise ValueError("one prespecified candidate failed")
        return original_fit(events, ids, features, candidate)

    monkeypatch.setattr(study, "fit", fail_one)
    with pytest.raises(RuntimeError, match="실패한 CV fold"):
        study.experiment(tiny_dataset)
    failure = json.loads((tiny_dataset.output / "failure.json").read_text())
    assert failure["validation_read"] is False
    assert len(failure["cv"]) == 5
    assert failure["cv"]["depth4_positive3"]["mean_event_horizon_ap"] is None
    assert not (tiny_dataset.output / "selection.json").exists()


@pytest.mark.parametrize(
    "changes,split",
    [
        ({"split": "calibration"}, "calibration"),
        ({"split": "test"}, "test"),
        ({"locked": True}, "train"),
        ({"start_utc": "2025-01-01T00:00:00Z"}, "train"),
        ({"start_utc": "2024-12-31T20:00:00Z"}, "train"),
        ({"start_utc": "2023-01-01T00:00:00Z"}, "train"),
        ({"split": "validation", "start_utc": "2022-01-01T00:00:00Z"}, "validation"),
    ],
)
def test_forbidden_splits_and_2025_crossing_fail_before_file_access(tmp_path, changes, split):
    event = {
        "id": "absent",
        "split": "train",
        "start_utc": "2022-01-01T00:00:00Z",
        "hours": 12,
        **changes,
    }
    with pytest.raises(ValueError):
        study.load_event(tmp_path, event, FEATURES, split)


def test_tampered_hash_and_future_input_rejected(tiny_dataset):
    event = json.loads(tiny_dataset.config.read_text())["events"][0]
    path = tiny_dataset.dataset / "march4.parquet"
    table = pq.read_table(path)
    column = table.schema.get_field_index("max_input_available_epoch_seconds")
    table = table.set_column(
        column,
        "max_input_available_epoch_seconds",
        pa.array(table["issue_epoch_seconds"].to_numpy() + 1),
    )
    pq.write_table(table, path)
    with pytest.raises(ValueError, match="SHA"):
        study.load_event(tiny_dataset.dataset, event, FEATURES, "train")
    report_path = tiny_dataset.dataset / "march4-report.json"
    report = json.loads(report_path.read_text())
    report["sha256"] = file_sha256(path)
    _json(report_path, report)
    with pytest.raises(ValueError, match="입력 누출"):
        study.load_event(tiny_dataset.dataset, event, FEATURES, "train")
