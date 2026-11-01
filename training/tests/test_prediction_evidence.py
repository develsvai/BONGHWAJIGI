import json

import numpy as np
import pytest

from bonghwa_training.goes_build import input_snapshot
from bonghwa_training.kma_event import read_event
from bonghwa_training.prediction_evidence import score_horizons


def observations(future):
    # At issue=900 only the first scan is available. Future pixels must have no effect.
    state = np.array([[[1, 0, -1, 0]], [future]], dtype=np.int8)
    grid = {"east_m": np.array([[0, 2000, 4000, 40000]]), "north_m": np.zeros((1, 4))}
    times = np.array([0, 1200])
    return (
        state,
        np.full(state.shape, np.nan),
        np.full(state.shape, np.nan),
        times,
        times,
        times + 900,
        grid,
        "fixture",
    )


def test_snapshot_never_filters_candidates_by_future_outcomes():
    cfg = {"candidate_distance_km": 30, "recent_fire_features": True}
    a = input_snapshot(observations([0, -1, 1, 1]), cfg, 0)
    b = input_snapshot(observations([1, 1, 0, -1]), cfg, 0)
    assert a[0].tolist() == [0] and a[1].tolist() == [1]
    for name in a[2]:
        np.testing.assert_equal(a[2][name], b[2][name])
    assert a[2]["distance_fire_km"].tolist() == [2]


def test_asof_reader_does_not_open_future_files(tmp_path, monkeypatch):
    event = {"id": "case"}
    (tmp_path / "case").mkdir()
    (tmp_path / "case/manifest.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "requested_observation_utc": "2023-04-02T03:00:00+00:00",
                        "path": "/must-not-open.nc",
                    }
                ]
            }
        )
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Future file opened")

    monkeypatch.setattr("bonghwa_training.kma_event.netCDF4.Dataset", forbidden)
    result = read_event(
        tmp_path, event, {"assumed_input_delay_minutes": 15}, maximum_issue_epoch_seconds=0
    )
    assert result[0].shape == (0, 0, 0)


class FakeModel:
    feature_names = ["distance_fire_km", "horizon_hours"]

    def __init__(self, reverse=False):
        self.reverse = reverse
        self.seen = []

    def inplace_predict(self, matrix):
        self.seen.append(matrix.copy())
        return (7 - matrix[:, 1] if self.reverse else matrix[:, 1]) / 10


def test_all_horizons_reuse_identical_past_features_and_preserve_missing():
    model = FakeModel()
    p = score_horizons(model, model.feature_names, {"distance_fire_km": np.array([2, np.nan])})
    np.testing.assert_allclose(p, [[0.1, 0.3, 0.6], [0.1, 0.3, 0.6]])
    for matrix in model.seen:
        np.testing.assert_equal(matrix[:, 0], [2, np.nan])
    with pytest.raises(ValueError, match="단조성"):
        score_horizons(
            FakeModel(reverse=True), model.feature_names, {"distance_fire_km": np.array([2])}
        )
    with pytest.raises(ValueError, match="순서"):
        score_horizons(
            model, list(reversed(model.feature_names)), {"distance_fire_km": np.array([2])}
        )
