import copy
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from pyproj import Transformer
from scipy.spatial import cKDTree

from bonghwa_training import korea_first_observation as study


def observations():
    starts = np.arange(0, 9 * 3600, 600, dtype=float)
    states = np.zeros((len(starts), 1, 3), dtype=np.int8)
    unknown = np.full(states.shape, np.nan)
    return states, unknown, unknown, starts, starts.copy(), starts + 900, {}, "test"


def base():
    return {
        "distance_fire_km": np.full(3, 10.0),
        "distance_fire_30m_km": np.full(3, 15.0),
        "distance_fire_60m_km": np.full(3, 20.0),
    }


def test_history_counts_complete_60_120_and_actual_elapsed_speed():
    obs = observations()
    extra, flags = study.input_history(obs, {}, 12, np.zeros(3, int), np.arange(3), base())
    np.testing.assert_array_equal(extra["history_60m_clear_count"], [7, 7, 7])
    np.testing.assert_array_equal(extra["history_120m_clear_count"], [13, 13, 13])
    assert flags["cohort_primary_clear60"].all() and flags["cohort_sensitivity_clear120"].all()
    np.testing.assert_array_equal(extra["actual_history_30m_minutes"], [20, 20, 20])
    np.testing.assert_array_equal(extra["actual_history_60m_minutes"], [50, 50, 50])
    np.testing.assert_allclose(extra["actual_closing_speed_30m_kmh"], [15, 15, 15])
    np.testing.assert_allclose(extra["actual_closing_speed_60m_kmh"], [12, 12, 12])


def test_past_fire_cloud_and_missing_frames_cannot_enter_primary_cohort():
    obs = observations()
    obs[0][3, 0, 0] = 1  # Clear60 but a fire observation 90min before current scan.
    obs[0][8, 0, 1] = -1
    extra, flags = study.input_history(obs, {}, 12, np.zeros(3, int), np.arange(3), base())
    np.testing.assert_array_equal(flags["cohort_primary_clear60"], [False, False, True])
    assert flags["history_clear60"][0]
    assert flags["history_fire_observed_120m"][0]
    assert extra["history_60m_unknown_count"][1] == 1
    # A missing source file must be counted as an unknown scheduled observation.
    missing = tuple(np.delete(a, 8, axis=0) if isinstance(a, np.ndarray) else a for a in obs)
    extra, flags = study.input_history(missing, {}, 11, np.zeros(3, int), np.arange(3), base())
    assert not flags["cohort_primary_clear60"].any()
    np.testing.assert_allclose(extra["history_60m_source_coverage_fraction"], 6 / 7)


def test_120_history_not_fabricated_when_only_60_minutes_are_available():
    obs = observations()
    extra, flags = study.input_history(obs, {}, 6, np.zeros(3, int), np.arange(3), base())
    assert flags["cohort_primary_clear60"].all()
    assert not flags["cohort_sensitivity_clear120"].any()
    assert not flags["history_120m_source_complete"].any()
    np.testing.assert_array_equal(extra["history_120m_unknown_count"], [6, 6, 6])


def test_future_and_blind_gap_cannot_change_input_features_or_cohorts():
    obs = observations()
    original = study.input_history(obs, {}, 12, np.zeros(3, int), np.arange(3), base())
    obs[0][13:] = 1
    changed = study.input_history(obs, {}, 12, np.zeros(3, int), np.arange(3), base())
    for before, after in zip(original, changed, strict=True):
        for key in before:
            np.testing.assert_array_equal(before[key], after[key])
    assert not any(name.startswith("audit_") for name in study.ADDITIONAL_FEATURES)


def test_outcome_positive_unknown_negative_and_negative_lower_lead():
    obs = observations()
    obs[0][13, 0, 0] = 1  # Not yet available at issue=scan120+15min.
    obs[0][14, 0, 0] = 1
    obs[0][14, 0, 1] = -1
    result = study.observation_outcome(obs, 12, np.zeros(3, int), np.arange(3), 1)
    np.testing.assert_array_equal(result["observed_fire_within_horizon"], [1, -1, 0])
    np.testing.assert_array_equal(result["target_known"], [True, False, True])
    np.testing.assert_array_equal(result["audit_blind_gap_fire_observed"], [True, False, False])
    assert result["audit_observation_transition_lower_lead_hours"][0] == -0.25
    assert result["audit_first_future_fire_observed_lead_hours"][0] == pytest.approx(5 / 60)
    assert result["audit_contiguous_clear_followup_lead_hours"][1] == -0.25
    assert result["audit_contiguous_clear_followup_lead_hours"][2] == pytest.approx(55 / 60)
    assert not result["survival_training_eligible"].any()


def test_missing_future_file_censors_even_if_every_existing_pixel_is_clear():
    obs = observations()
    missing = tuple(np.delete(a, 16, axis=0) if isinstance(a, np.ndarray) else a for a in obs)
    result = study.observation_outcome(missing, 12, np.zeros(3, int), np.arange(3), 1)
    np.testing.assert_array_equal(result["observed_fire_within_horizon"], [-1, -1, -1])
    np.testing.assert_array_equal(result["audit_future_unknown_count"], [1, 1, 1])
    np.testing.assert_allclose(result["audit_contiguous_clear_followup_lead_hours"], 15 / 60)
    assert not result["audit_future_source_complete"].any()


def test_positive_after_unknown_is_observation_audit_not_survival_interval():
    obs = observations()
    obs[0][14, 0, 0] = -1
    obs[0][17, 0, 0] = 1
    result = study.observation_outcome(obs, 12, np.zeros(3, int), np.arange(3), 1)
    assert result["observed_fire_within_horizon"][0] == 1
    assert result["audit_observation_transition_lower_lead_hours"][0] == pytest.approx(25 / 60)
    assert result["audit_contiguous_clear_followup_lead_hours"][0] == -0.25
    assert not result["survival_training_eligible"][0]


def test_invalid_train_allowlist_rejected_before_any_raw_read(tmp_path, monkeypatch):
    config = Path(__file__).parents[1] / "configs/korea-gk2a-context-v4.json"
    cfg = copy.deepcopy(json.loads(config.read_text()))
    cfg["events"][0]["id"] = "forbidden_2025"
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg))
    original = Path.read_text

    def guarded(path, *args, **kwargs):
        assert path.name == "config.json"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    with pytest.raises(ValueError, match="allowlist"):
        study.preflight(SimpleNamespace(config=path))


def test_full_event_preserves_old_rows_and_adds_unknown_candidates(tmp_path, monkeypatch):
    cfg = json.loads((Path(__file__).parents[1] / "configs/korea-gk2a-context-v4.json").read_text())
    event = {**cfg["events"][0], "hours": 1}
    initial = study.datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00")).timestamp()
    starts = initial - 120 * 60 + np.arange(0, 10 * 3600, 600, dtype=float)
    states = np.zeros((len(starts), 1, 4), dtype=np.int8)
    states[:, 0, 0] = 1
    states[15, 0, 1] = 1
    states[16, 0, 2] = -1
    lon = np.array([[129.0, 129.01, 129.02, 129.03]])
    lat = np.full(lon.shape, 37.0)
    east, north = Transformer.from_crs(4326, 5179, always_xy=True).transform(lon, lat)
    source_grid = {"longitude": lon, "latitude": lat, "east_m": east, "north_m": north}
    unknown = np.full(states.shape, np.nan)
    obs = states, unknown, unknown, starts, starts, starts + 900, source_grid, "test"
    static = {
        "country": np.ones(lon.shape, bool),
        "forest_fraction": np.full(lon.shape, 0.8),
        "elevation_m": np.full(lon.shape, 100.0),
        "slope_degrees": np.full(lon.shape, 10.0),
    }
    tree = cKDTree(np.column_stack((east.ravel(), north.ravel())))

    class Weather:
        def at(self, points, issues):
            return np.tile([20, 50, 3, 3, 0, np.nan, 1, 1], (len(points), 1))

    weather = Weather()
    features = [f for f in cfg["feature_names"] if f not in cfg["drop_features"]]
    # Independently construct the old known-only recipe using its original target helper.
    old = []
    for i, scan in enumerate(starts):
        if not initial <= scan < initial + 3600 or scan % 1200:
            continue
        rr, cc, base_values = study.goes_build.input_snapshot(obs, cfg, i)
        coords = {
            "row": rr.astype(np.int32),
            "col": cc.astype(np.int32),
            "longitude": lon[rr, cc],
            "latitude": lat[rr, cc],
            "issue_epoch_seconds": np.full(len(rr), starts[i] + 900),
        }
        inputs = {name: np.asarray(value, np.float32) for name, value in base_values.items()}
        context = study.hourly_context.context_for_table(
            pa.table({**inputs, **coords}), static, tree, weather
        )
        inputs.update({name: np.asarray(value, np.float32) for name, value in context.items()})
        for h in (1, 3, 6):
            future = np.flatnonzero(
                (starts > starts[i] + 900) & (starts <= starts[i] + 900 + h * 3600)
            )
            target = study.goes_build.future_target(states[future][:, rr, cc], len(future) == h * 6)
            known = target >= 0
            old.append(
                pa.table(
                    {
                        **{k: v[known] for k, v in inputs.items()},
                        **{k: v[known] for k, v in coords.items()},
                        "horizon_hours": np.full(known.sum(), h, np.float32),
                        "fire_within_horizon": target[known],
                    }
                )
            )
    reference = tmp_path / "reference"
    output = tmp_path / "new"
    reference.mkdir()
    output.mkdir()
    old_table = pa.concat_tables(old)
    pq.write_table(old_table, reference / f"{event['id']}.parquet")
    monkeypatch.setattr(study.kma_event, "read_event", lambda *args: obs)
    args = SimpleNamespace(reference=reference, output=output, raw=tmp_path / "unused")
    report = study.build_event(args, cfg, {"base_features": features}, event, static, tree, weather)
    result = pq.read_table(output / f"{event['id']}.parquet")
    assert report["matched_v4_rows"] == len(old_table)
    assert len(result) > len(old_table)
    assert report["base_feature_max_abs_difference"] == 0
    assert (result["observed_fire_within_horizon"].to_numpy() == -1).any()
    assert result["cohort_primary_clear60"].to_numpy().any()
    assert not result["survival_training_eligible"].to_numpy().any()
