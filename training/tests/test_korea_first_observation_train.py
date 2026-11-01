import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from bonghwa_training import korea_first_observation_train as study
from bonghwa_training.download import file_sha256


@pytest.fixture
def inputs(tmp_path):
    cfg = json.loads((Path(__file__).parents[1] / "configs/korea-gk2a-context-v4.json").read_text())
    base = [f for f in cfg["feature_names"] if f not in cfg["drop_features"]]
    features = base + study.dataset_builder.ADDITIONAL_FEATURES
    cfg.update(
        profile=study.dataset_builder.PROFILE,
        events=[e for e in cfg["events"] if e["split"] == "train"],
        feature_names=features,
        input_feature_allowlist=features,
        target_column="observed_fire_within_horizon",
        unknown_target_value=-1,
    )
    directory = tmp_path / "dataset"
    directory.mkdir()
    (directory / "config.json").write_text(json.dumps(cfg))
    (directory / "plan.json").write_text(json.dumps({"base_features": base}))
    (directory / "report.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "config_sha256": file_sha256(directory / "config.json"),
                "plan_sha256": file_sha256(directory / "plan.json"),
            }
        )
    )
    for event in cfg["events"]:
        row = np.tile(np.arange(10), 3)
        n = len(row)
        values = {f: np.ones(n, np.float32) for f in features}
        issue = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00")).timestamp() + 900
        y = np.where(row == 0, -1, np.where(row == 1, 1, 0)).astype(np.int8)
        values.update(
            horizon_hours=np.repeat([1, 3, 6], 10),
            observed_fire_within_horizon=y,
            target_known=y >= 0,
            cohort_primary_clear60=row < 9,
            cohort_sensitivity_clear120=row < 8,
            latitude=np.full(n, 37.1),
            longitude=np.full(n, 129.1),
            row=row,
            col=np.zeros(n),
            issue_epoch_seconds=np.full(n, issue),
            max_input_available_epoch_seconds=np.full(n, issue),
            audit_first_future_fire_observed_epoch_seconds=np.full(n, 999999999999),
        )
        path = directory / f"{event['id']}.parquet"
        pq.write_table(pa.table(values), path)
        (directory / f"{event['id']}-report.json").write_text(
            json.dumps(
                {
                    "event": event,
                    "rows": n,
                    "sha256": file_sha256(path),
                }
            )
        )
    return SimpleNamespace(dataset=directory, output=tmp_path / "model", plan_only=True)


def test_candidate_correction_removes_only_wrong_interval_speeds(inputs):
    events, base, features, inventory, hashes = study.load_train(inputs.dataset)
    candidates = study.make_candidates(base)
    assert [len(c["features"]) for c in candidates] == [34, 44, 50]
    assert study.OLD_SPEED.issubset(candidates[0]["features"])
    assert not study.OLD_SPEED.intersection(candidates[1]["features"])
    assert not any(f.startswith("audit_") for f in features)
    assert all(d["primary_unknown"] == 3 for d in inventory.values())
    assert all(len(d["y"]) == 27 for d in events.values())
    assert len(hashes) == 31


def test_known_training_excludes_unknown_without_changing_candidate_universe(inputs):
    events, *_ = study.load_train(inputs.dataset)
    training = study.known_training(events)
    for name, data in events.items():
        assert len(data["y"]) == 27 and len(training[name]["y"]) == 24
        assert np.isin(training[name]["y"], [0, 1]).all()
        scores = np.where(data["y"] == -1, 1.0, 0.0)
        metrics = study.evaluate(data, scores)["1"]["budget"]
        assert metrics["selected_unknown"] == 1
        assert metrics["observed_positive_recall"] == 0


def test_full_frozen_nested_fit_does_not_train_on_unknowns_or_read_audits(inputs, monkeypatch):
    original_read, original_fit = study.pq.read_table, study.expanded.fit
    calls = []

    def guarded_read(path, **kwargs):
        assert Path(path).stem in study.recent.TRAIN_IDS
        assert kwargs["columns"]
        assert not any(f.startswith("audit_") for f in kwargs["columns"])
        return original_read(path, **kwargs)

    def guarded_fit(events, ids, features, candidate):
        assert all(np.isin(events[e]["y"], [0, 1]).all() for e in ids)
        calls.append(ids)
        return original_fit(events, ids, features, candidate)

    monkeypatch.setattr(study.pq, "read_table", guarded_read)
    monkeypatch.setattr(study.expanded, "fit", guarded_fit)
    assert study.run(inputs)["status"] == "plan_frozen"
    plan = json.loads((inputs.output / "plan.json").read_text())
    held = []
    for outer in plan["outer_folds"]:
        held += outer["held_ids"]
        assert set(outer["held_ids"]).isdisjoint(outer["training_ids"])
        for inner in outer["inner_folds"]:
            assert set(inner["held_ids"]).isdisjoint(outer["held_ids"])
            assert set(inner["held_ids"]).isdisjoint(inner["training_ids"])
    assert set(held) == study.recent.TRAIN_IDS and len(held) == 14
    inputs.plan_only = False
    result = study.run(inputs)
    assert result["fits_executed"] == len(calls) == 57
    report = json.loads((inputs.output / "report.json").read_text())
    assert report["final_source_audit"]["all_hashes_match"]
    for method in report["summaries"]["primary"].values():
        assert method["budget"]["unknown_rows"] == 42
        assert method["budget"]["candidate_rows"] == 378
    assert report["selected_model"]["cpu_reload_max_abs_difference"] == 0
    assert not report["operational_use"] and not report["test_evaluated"]


@pytest.mark.parametrize("bad", ["future_column", "event_2025", "source_changed"])
def test_loader_rejects_tampered_contracts(inputs, bad):
    config = inputs.dataset / "config.json"
    cfg = json.loads(config.read_text())
    if bad == "future_column":
        cfg["input_feature_allowlist"].append("audit_future_fire_count")
    elif bad == "event_2025":
        cfg["events"][0]["start_utc"] = "2025-03-01T00:00:00Z"
    else:
        path = inputs.dataset / f"{cfg['events'][0]['id']}.parquet"
        path.write_bytes(b"changed")
    config.write_text(json.dumps(cfg))
    report_path = inputs.dataset / "report.json"
    report = json.loads(report_path.read_text())
    report["config_sha256"] = file_sha256(config)
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError):
        study.load_train(inputs.dataset)
