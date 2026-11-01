import json
from datetime import UTC, datetime, timedelta

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from bonghwa_training import gofer_history_train as study


def event(n=48):
    distance = np.resize([2.5, 3, 4, 6, 10, 15], n)
    return {
        "x": np.column_stack([distance] * 8).astype("float32"),
        "lower": np.resize([0, 1, 2, 4, 6, 2], n).astype(float),
        "upper": np.resize([1, 2, 3, 5, np.inf, np.inf], n),
    }


def test_transitive_periods_never_cross_folds():
    metadata = [
        {"id": name, "start_utc": f"2019-08-{day:02}T00:00:00Z"}
        for name, day in zip("abcdef", [1, 4, 7, 15, 20, 25], strict=True)
    ]
    groups = study.temporal_clusters(metadata)
    assert groups["a"] == groups["b"] == groups["c"]
    split = study.folds(list(groups), groups, 4)
    assert sorted(n for _, held in split for n in held) == sorted(groups)
    for train, held in split:
        assert not {groups[n] for n in train} & {groups[n] for n in held}
    with pytest.raises(ValueError, match="독립 시간"):
        study.folds(list(groups), groups, 5)


def test_unknown_future_labels_excluded_and_event_horizons_balanced():
    events = {"small": event(6), "large": event(60)}
    features = [*study.LEGACY, "new_history"]
    matrix = study.expand(events, features, ["distance_km"], True)
    sizes = []
    positive = 0
    for e in events.values():
        for h in study.HORIZONS:
            known, y = study.known_labels(e["lower"], e["upper"], h)
            sizes.append(int(known.sum()))
            positive += int(y[known].sum())
    assert matrix.num_row() == sum(sizes) < 3 * 66
    assert matrix.get_label().sum() == positive
    sections = np.split(matrix.get_weight(), np.cumsum(sizes)[:-1])
    np.testing.assert_allclose([w.sum() for w in sections], matrix.num_row() / 6, rtol=1e-6)
    prediction = study.expand(events, features, ["distance_km"], False)
    assert prediction.num_row() == 3 * 66


def test_real_shared_classifier_and_positive_calibrator_preserve_horizon_order():
    events = {"a": event(240), "b": event(120)}
    features = [*study.LEGACY, "new_history"]
    candidate = {"features": ["distance_km"], "depth": 2, "rounds": 12}
    fitted = study.fit(events, features, candidate)
    raw = study.predict(fitted, events, features, candidate)
    mapping = study.fit_calibration(events, raw)
    calibrated = study.calibrate(raw, mapping)
    for values in calibrated.values():
        assert np.isfinite(values).all()
        assert np.all(np.diff(values, axis=1) >= 0)
        assert np.all((values > 0) & (values < 1))
    with pytest.raises(ValueError, match="양의"):
        study.calibrate(raw, {"slope": -1, "intercept": 0})


def test_recall_operating_point_includes_ties_and_does_not_force_new_event_recall():
    events = {"a": event(60)}
    predictions = {"a": np.repeat(np.linspace(0.1, 0.9, 60)[:, None], 3, axis=1)}
    threshold = study.threshold80(events, predictions)
    y, p, w = study.flatten_known(events, predictions)
    assert w[(y == 1) & (p >= threshold)].sum() / w[y == 1].sum() >= 0.8 - 1e-12
    ties = {"a": np.full((60, 3), 0.25)}
    assert study.threshold80(events, ties) == 0.25
    low = {"a": np.zeros((60, 3))}
    metrics = study.alert_metrics(events, low, {"a": threshold})
    assert metrics["a"]["6"]["recall"] == 0


@pytest.fixture
def dataset(tmp_path):
    root = tmp_path / "dataset"
    root.mkdir()
    events = [
        {
            "id": f"event_{i}",
            "split": "train" if i < 7 else "validation",
            "start_utc": (
                datetime(2019, 7, 1, tzinfo=UTC) + timedelta(days=i * 7)
                if i < 7
                else datetime(2021, 7, 1, tzinfo=UTC)
            ).isoformat(),
        }
        for i in range(8)
    ]
    config = {
        "target": "gofer_reconstructed_perimeter_first_approach",
        "feature_names": [*study.LEGACY, "new_history"],
        "events": [*events, {"id": "never_open_2025", "split": "test", "locked": True}],
        "settings": {"radius_km": 2, "max_issue_hours": 72, "horizon_hours": 6},
        "retrospective_proxy_only": True,
        "operational_use": False,
        "source_asof_verified": False,
    }
    study.write_json(root / "config.json", config)
    for meta in events:
        e = event()
        n = len(e["lower"])
        data = {f: e["x"][:, i] for i, f in enumerate(config["feature_names"])}
        data.update(
            {
                "event_id": [meta["id"]] * n,
                "split": [meta["split"]] * n,
                "issue_time_utc": [meta["start_utc"]] * n,
                "target_id": [str(i) for i in range(n)],
                "current_approach": [False] * n,
                "label_lower_hours": e["lower"],
                "label_upper_hours": e["upper"],
            }
        )
        path = root / f"{meta['id']}.parquet"
        pq.write_table(pa.table(data), path)
        study.write_json(root / f"{meta['id']}-report.json", {"sha256": study.sha(path), "rows": n})
    return root, config


def test_nested_real_fit_excludes_outer_labels_and_validation_follows_freeze(
    dataset, tmp_path, monkeypatch
):
    root, config = dataset
    output = tmp_path / "output"
    real_load, real_select, real_cal = study.load_events, study.select, study.fit_calibration
    all_train = {e["id"] for e in config["events"] if e["split"] == "train"}
    excluded, reads = set(), []

    def select(events, *args, **kwargs):
        excluded.clear()
        excluded.update(all_train - set(events))
        return real_select(events, *args, **kwargs)

    def calibration(events, predictions):
        assert not excluded & set(events)
        assert set(events) == set(predictions)
        return real_cal(events, predictions)

    def load(root, config, split):
        reads.append(split)
        if split == "validation":
            assert (output / "fit-receipt.json").exists()
            assert (output / "nested-evaluation.json").exists()
            assert (output / "selected.ubj").exists()
        return real_load(root, config, split)

    monkeypatch.setattr(study, "load_events", load)
    monkeypatch.setattr(study, "select", select)
    monkeypatch.setattr(study, "fit_calibration", calibration)
    monkeypatch.setattr(
        study,
        "candidates",
        lambda _: [{"name": "tiny", "features": ["distance_km"], "depth": 2, "rounds": 3}],
    )
    result = study.run(root, output)
    assert reads == ["train", "validation"]
    assert result["training_rows"] == 7 * 48
    assert result["validation_rows"] == 48
    assert result["reload_max_difference"] == 0
    assert result["operational_use"] is False
    assert result["test_evaluated"] is False
    held_once = []
    for outer in result["outer_fits"]:
        held_once.extend(outer["held"])
        for inner in outer["selection"]["folds"]:
            assert not set(outer["held"]) & (set(inner["held"]) | set(inner["train"]))
    assert sorted(held_once) == sorted(all_train)
    predictions = pq.read_table(output / "validation-predictions.parquet")
    assert len(predictions) == 48
    assert np.all(
        predictions["calibrated_1h"].to_numpy() <= predictions["calibrated_6h"].to_numpy()
    )


def test_tampered_parquet_and_operational_config_rejected(dataset, tmp_path):
    root, config = dataset
    path = root / "event_0.parquet"
    path.write_bytes(path.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="해시"):
        study.load_events(root, config, "train")
    config["operational_use"] = True
    study.write_json(root / "config.json", config)
    with pytest.raises(ValueError, match="계약"):
        study.run(root, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_locked_test_never_read(dataset):
    root, config = dataset
    assert len(study.load_events(root, config, "train")) == 7
    with pytest.raises(ValueError, match="구획"):
        study.load_events(root, config, "test")
    assert not (root / "never_open_2025.parquet").exists()
    assert json.loads((root / "config.json").read_text())["events"][-1]["locked"]
