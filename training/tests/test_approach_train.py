import json

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from bonghwa_training import approach_train as study
from bonghwa_training.download import file_sha256


def test_interval_straddles_are_unknown_and_censored_rows_are_not_future_negatives():
    lower = np.array([0, 1, 2, 3, 6], dtype=float)
    upper = np.array([1, 2, np.inf, 4, np.inf])
    known, y = study.known_labels(lower, upper, 3)
    assert known.tolist() == [True, True, False, True, True]
    assert y.tolist() == [1, 1, 0, 0, 0]
    known, y = study.known_labels(lower, upper, 1.5)
    assert known.tolist() == [True, False, True, True, True]


@pytest.mark.parametrize(
    "lower,upper", [([0], [np.inf]), ([-1], [2]), ([1], [1]), ([np.nan], [2]), ([1], [np.nan])]
)
def test_invalid_arrival_intervals_rejected(lower, upper):
    with pytest.raises(ValueError):
        study.validate_intervals(lower, upper)


def test_cdf_uses_log_time_margin_and_increases_with_horizon():
    result = study.cdf(np.log([1.0, 3.0, 6.0]))
    np.testing.assert_allclose(np.diag(result), 0.5)
    assert np.all(np.diff(result, axis=1) >= 0)
    assert result[0, 2] > result[2, 2]
    assert np.all(np.isfinite(study.cdf([-1e6, 1e6])))


def test_constant_speed_baseline_uses_approach_radius_and_unknown_speed():
    actual = study.constant_speed_arrival([5, 5, 5, 5], [1, 0, -1, np.nan], 2)
    np.testing.assert_array_equal(actual, [3, np.inf, np.inf, np.inf])


@pytest.fixture
def pilot(tmp_path):
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    events = [
        {
            "id": "train_a",
            "split": "train",
            "period_group": "2019-a",
            "start_utc": "2019-08-01T00:00:00Z",
        },
        {
            "id": "train_b",
            "split": "train",
            "period_group": "2020-b",
            "start_utc": "2020-08-01T00:00:00Z",
        },
        {
            "id": "validation",
            "split": "validation",
            "period_group": "2021-c",
            "start_utc": "2021-08-01T00:00:00Z",
        },
        {"id": "forbidden_2025", "split": "test", "locked": True},
    ]
    config = {
        "profile": "gofer_reconstructed_approach_pilot",
        "feature_names": list(study.FEATURES),
        "events": events,
        "settings": {"radius_km": 2},
    }
    study.write_json(dataset / "config.json", config)
    for event in events[:3]:
        n = 24
        data = {f: np.tile([0.5, 1.0, 2.0, 4.0, 8.0, 12.0], 4) for f in study.FEATURES}
        data.update(
            {
                "event_id": [event["id"]] * n,
                "split": [event["split"]] * n,
                "issue_time_utc": [event["start_utc"]] * n,
                "target_id": [str(i) for i in range(n)],
                "current_approach": [False] * n,
                "label_lower_hours": np.tile([0, 1, 2, 4, 6, 2], 4),
                "label_upper_hours": np.tile([1, 2, 3, 5, np.inf, np.inf], 4),
            }
        )
        path = dataset / f"{event['id']}.parquet"
        pq.write_table(pa.table(data), path)
        study.write_json(
            dataset / f"{event['id']}-report.json", {"sha256": file_sha256(path), "rows": n}
        )
    return dataset, config


def test_real_aft_fit_receipt_precedes_validation_and_models_reload(pilot, tmp_path, monkeypatch):
    dataset, config = pilot
    output = tmp_path / "output"
    real_loader = study.load_events
    reads = []

    def loader(dataset, config, split):
        reads.append(split)
        if split == "validation":
            assert (output / "fit-receipt.json").exists()
            assert (output / "aft_history.ubj").exists()
        return real_loader(dataset, config, split)

    monkeypatch.setattr(study, "load_events", loader)
    result = study.run(dataset, output)
    assert reads == ["train", "validation"]
    assert result["training_rows"] == 48
    assert result["validation_rows"] == 24
    assert result["test_evaluated"] is False
    assert result["probability_calibrated"] is False
    assert result["operational_use"] is False
    assert result["models"]["aft_history"]["reload_margin_max_abs_difference"] == 0
    assert result["validation"]["aft_history"]["events"]["validation"]["3"]["unknown_rows"] == 4
    predictions = pq.read_table(output / "validation-predictions.parquet")
    assert np.all(predictions["model_cdf_1h"].to_numpy() <= predictions["model_cdf_3h"].to_numpy())
    json.loads((output / "report.json").read_text())
    with pytest.raises(FileExistsError):
        study.run(dataset, output)


def test_group_overlap_rejected_before_data_loading(pilot, tmp_path, monkeypatch):
    dataset, config = pilot
    config["events"][2]["period_group"] = config["events"][0]["period_group"]
    study.write_json(dataset / "config.json", config)
    monkeypatch.setattr(study, "load_events", lambda *a: pytest.fail("data must not be read"))
    with pytest.raises(ValueError, match="기간그룹"):
        study.run(dataset, tmp_path / "out")


def test_changed_dataset_hash_rejected(pilot):
    dataset, config = pilot
    with (dataset / "train_a.parquet").open("ab") as stream:
        stream.write(b"modified")
    with pytest.raises(ValueError, match="SHA"):
        study.load_events(dataset, config, "train")


def test_frozen_year_split_rejected(pilot):
    dataset, config = pilot
    config["events"][0]["start_utc"] = "2021-08-01T00:00:00Z"
    with pytest.raises(ValueError, match="고정 연도"):
        study.load_events(dataset, config, "train")


def test_prediction_matrix_does_not_include_labels(pilot):
    dataset, config = pilot
    events = study.load_events(dataset, config, "train")
    dm = study.matrix(events, list(study.FEATURES), with_labels=False)
    assert len(dm.get_float_info("label_lower_bound")) == 0
    assert len(dm.get_float_info("label_upper_bound")) == 0
