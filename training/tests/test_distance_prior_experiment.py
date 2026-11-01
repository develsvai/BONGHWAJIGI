import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from bonghwa_training import distance_prior_experiment as study
from bonghwa_training.download import file_sha256


def write_json(path, value):
    path.write_text(json.dumps(value) + "\n")


def contracts():
    cfg = json.loads((Path(__file__).parents[1] / "configs/korea-gk2a-context-v3.json").read_text())
    features = [f for f in cfg["feature_names"] if f not in cfg.get("drop_features", [])]
    reference = next(
        c for c in study.expanded.make_candidates(features) if c["name"] == study.REFERENCE
    )
    return cfg, features, reference


@pytest.fixture
def inputs(tmp_path):
    cfg, features, _ = contracts()
    dataset, run = tmp_path / "dataset", tmp_path / "source"
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
    cfg.update(
        profile=study.expanded.CONTEXT_PROFILE,
        events=events
        + [
            {"id": "forbidden_calibration", "split": "calibration"},
            {"id": "forbidden_test_2025", "split": "test", "locked": True},
        ],
    )
    config = tmp_path / "config.json"
    write_json(config, cfg)
    (dataset / "config.json").write_bytes(config.read_bytes())
    for event in events:
        count = 0 if event["id"].startswith("empty") else 96
        indices = np.tile(np.arange(32), 3)[:count]
        start = study.datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00"))
        values = {f: np.zeros(count) for f in features}
        for distance in study.DISTANCES:
            values[distance] = indices.astype(float) + 1
        values.update(
            {
                "horizon_hours": np.repeat([1, 3, 6], 32)[:count],
                "fire_within_horizon": (indices == 0).astype(int),
                "issue_epoch_seconds": np.full(count, start.timestamp() + 900),
                "max_input_available_epoch_seconds": np.full(count, start.timestamp()),
                "row": indices,
                "col": np.zeros(count),
            }
        )
        path = dataset / f"{event['id']}.parquet"
        pq.write_table(pa.table(values), path)
        write_json(
            path.with_name(f"{event['id']}-report.json"),
            {
                "rows": count,
                "sha256": file_sha256(path),
                "event": event,
                "unusable_reason": "no observed rows" if not count else None,
            },
        )
    report = study.expanded.experiment(SimpleNamespace(dataset=dataset, config=config, output=run))
    assert report["selected"] == study.REFERENCE
    return SimpleNamespace(dataset=dataset, config=config, run=run, output=tmp_path / "distance")


def test_fixed_34_19_3_feature_candidates_and_conditional_constraints():
    cfg, features, reference = contracts()
    original = json.dumps(reference, sort_keys=True)
    cases = study.make_candidates(reference, features, cfg["context_features"])
    assert [len(c["features"]) for c in cases] == [34, 34, 19, 3]
    assert json.dumps(reference, sort_keys=True) == original
    assert cases[0] == reference
    assert not (set(cases[2]["features"]) & (set(cfg["context_features"]) | study.CLOCK))
    assert cases[3]["features"] == [
        "distance_fire_km",
        "distance_recent_fire_60m_km",
        "horizon_hours",
    ]
    for case in cases[1:]:
        mapping = dict(zip(case["features"], case["monotone_constraints"], strict=True))
        assert mapping["horizon_hours"] == 1
        assert all(mapping[f] == -1 for f in study.DISTANCES & set(case["features"]))
        assert case["rounds"] == 100 and case["parameters"]["seed"] == 47
        assert case["parameters"]["device"] == "cpu" and case["parameters"]["nthread"] == 2
    assert cases[3]["positive_weight_rule"] == "unit"
    assert cases[3]["parameters"]["max_depth"] == 3
    assert (
        cases[1]["positive_weight_rule"] == cases[2]["positive_weight_rule"] == "training_fold_sqrt"
    )


def test_tie_prefers_existing_reference_and_failure_prevents_selection():
    cfg, features, reference = contracts()
    cases = study.make_candidates(reference, features, cfg["context_features"])
    cv = {c["name"]: {"status": "completed", "mean_event_horizon_ap": 0.5} for c in cases}
    assert study.select_candidate(cases, cv) == reference
    cv[cases[-1]["name"]]["mean_event_horizon_ap"] = 0.6
    assert study.select_candidate(cases, cv) == cases[-1]
    cv[cases[1]["name"]]["status"] = "failed"
    with pytest.raises(ValueError, match="실패한 후보"):
        study.select_candidate(cases, cv)


def test_full_study_uses_only_new_candidate_fits_and_reads_validation_after_selection(
    inputs, monkeypatch
):
    fit, load, predict = study.expanded.fit, study.expanded.load_event, study.predict
    fitted, loaded = [], []

    def tracked_fit(events, ids, features, candidate):
        assert (inputs.output / "plan.json").is_file()
        assert candidate["name"] != study.REFERENCE
        assert "empty_train" not in ids
        fitted.append((candidate["name"], tuple(ids)))
        return fit(events, ids, features, candidate)

    def tracked_load(dataset, event, features, split):
        assert split in ("train", "validation")
        loaded.append(event["id"])
        if split == "validation":
            assert (inputs.output / "selection.json").is_file()
        return load(dataset, event, features, split)

    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        assert "forbidden_" not in path.name
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(study.expanded, "fit", tracked_fit)
    monkeypatch.setattr(study.expanded, "load_event", tracked_load)

    def new_only_prediction(model, data, features, candidate):
        assert candidate["name"] != study.REFERENCE
        return predict(model, data, features, candidate)

    monkeypatch.setattr(study, "predict", new_only_prediction)
    result = study.experiment(inputs)
    assert len(fitted) == (9 if result["selected"] == study.REFERENCE else 10)
    assert loaded[-2:] == ["validation", "empty_validation"]
    assert len(result["cv"]) == 4
    assert result["cv"][study.REFERENCE]["reused_frozen_cv"] is True
    assert result["selected_model"]["model_path"]
    assert result["calibration_split_read"] is result["test_evaluated"] is False
    assert result["probability_calibrated"] is result["operational_use"] is False
    assert all(c["status"] == "completed" for c in result["cv"].values())
    source_report = json.loads((inputs.run / "report.json").read_text())
    assert result["validation"][study.REFERENCE] == source_report["validation"][study.REFERENCE]
    for metrics in result["validation"].values():
        assert metrics["empty_validation"]["1"]["average_precision"] is None
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("index", [2, 3])
def test_subset_model_fit_reload_and_period_distance_probes_use_declared_columns(inputs, index):
    cfg = json.loads(inputs.config.read_text())
    _, features, reference = contracts()
    candidate = study.make_candidates(reference, features, cfg["context_features"])[index]
    events = {
        e["id"]: study.expanded.load_event(inputs.dataset, e, features, "train")
        for e in cfg["events"]
        if e["split"] == "train"
    }
    ids = [e for e, d in events.items() if len(d["y"])]
    model, _, resolved = study.expanded.fit(events, ids, features, candidate)
    loaded, report = study.save_selected(
        model, inputs.output.with_suffix(".ubj"), events, features, resolved
    )
    assert loaded.feature_names == candidate["features"]
    assert len(loaded.feature_names) == (19 if index == 2 else 3)
    assert report["saved_trees"] == 100
    assert report["horizon_monotonicity_verified"] is True
    assert report["prescribed_distance_monotonicity_verified"] is True
    assert set(report["distance_monotonicity_probes"]) == study.DISTANCES & set(
        candidate["features"]
    )
    assert all(
        p["finite_probe_rows"] > 0 and p["maximum_score_increase"] <= 1e-6
        for p in report["distance_monotonicity_probes"].values()
    )
    assert len(study.predict(loaded, events[ids[0]], features, candidate)) == 96


def test_one_new_candidate_failure_preserves_all_results_and_never_reads_validation(
    inputs, monkeypatch
):
    fit, load = study.expanded.fit, study.expanded.load_event

    def fail_one(events, ids, features, candidate):
        if candidate["name"] == "distance_monotone_observations":
            raise ValueError("deliberate failure")
        return fit(events, ids, features, candidate)

    def train_only(dataset, event, features, split):
        assert split == "train"
        return load(dataset, event, features, split)

    monkeypatch.setattr(study.expanded, "fit", fail_one)
    monkeypatch.setattr(study.expanded, "load_event", train_only)
    with pytest.raises(RuntimeError, match="실패한 후보"):
        study.experiment(inputs)
    failure = json.loads((inputs.output / "failure.json").read_text())
    assert len(failure["cv"]) == 4 and failure["validation_read"] is False
    assert not (inputs.output / "selection.json").exists()
    assert len(list(inputs.output.glob("*-cv.json"))) == 4


def test_pooled_workload_sums_counts_before_ratios_and_keeps_rounding():
    def cell(tp, positives, examined, candidates):
        return {
            "top_10_percent_per_issue": {
                "eligible_candidates": candidates,
                "examined_candidates": examined,
                "true_positives": tp,
                "total_positives": positives,
                "random_budget_expected_true_positives": examined * positives / candidates,
                "issues_with_boundary_ties": 0,
            }
        }

    result = study.pooled_workload(
        {
            "small": {str(h): cell(1, 1, 1, 2) for h in (1, 3, 6)},
            "large": {str(h): cell(1, 9, 10, 100) for h in (1, 3, 6)},
        }
    )
    combined = result["all_horizons_repeated_decisions"]
    assert combined["recall"] == pytest.approx(0.2)
    assert combined["precision"] == pytest.approx(2 / 11)
    assert combined["actual_examined_fraction"] == pytest.approx(11 / 102)
    assert combined["true_positives"] == 6


def test_changed_reference_eligibility_cells_rejected_before_new_fit(inputs, monkeypatch):
    plan_path = inputs.run / "plan.json"
    plan = json.loads(plan_path.read_text())
    plan["eligible_cv_cells"] = plan["eligible_cv_cells"][:-1]
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
        raise AssertionError("different CV populations cannot be compared")

    monkeypatch.setattr(study.expanded, "fit", no_fit)
    with pytest.raises(ValueError, match="평가 셀"):
        study.experiment(inputs)
    assert not inputs.output.exists()
