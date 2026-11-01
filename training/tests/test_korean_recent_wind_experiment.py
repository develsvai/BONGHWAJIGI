import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from pyproj import Geod, Transformer

from bonghwa_training import korean_recent_wind_experiment as study
from bonghwa_training.download import file_sha256


def contracts():
    config = Path(__file__).parents[1] / "configs/korea-gk2a-context-v4.json"
    cfg = json.loads(config.read_text())
    features = [f for f in cfg["feature_names"] if f not in cfg["drop_features"]]
    return cfg, features


def geometry(bearings, wind_u, wind_v):
    _, features = contracts()
    n = len(bearings)
    x = np.zeros((n, len(features)))
    lon, lat = np.full(n, 129.1), np.full(n, 37.1)
    anchor_lon, anchor_lat, _ = Geod(ellps="WGS84").fwd(lon, lat, bearings, np.full(n, 5000.0))
    transform = Transformer.from_crs(4326, 5179, always_xy=True)
    tx, ty = transform.transform(lon, lat)
    ax, ay = transform.transform(anchor_lon, anchor_lat)
    for name, values in {
        "nearest_recent_fire_60m_dx_km": (ax - tx) / 1000,
        "nearest_recent_fire_60m_dy_km": (ay - ty) / 1000,
        "nearest_fire_dx_km": np.full(n, 10),
        "nearest_fire_dy_km": np.full(n, 10),
        "distance_recent_fire_60m_km": np.full(n, 5),
        "wind_u_ms": wind_u,
        "wind_v_ms": wind_v,
        "temperature_c": np.full(n, 24.5),
        "humidity_pct": np.full(n, 50),
    }.items():
        x[:, features.index(name)] = values
    return x, features, lon, lat


def test_recent_geodesic_bearing_wind_signs_and_no_mutation():
    x, features, lon, lat = geometry([270, 90, 180, 0], [3, 3, 0, 0], [0, 0, 3, 3])
    original = x.copy()
    out = study.derive_features(x, features, lon, lat)
    np.testing.assert_allclose(out[:, 0], [3, -3, 3, -3], atol=2e-6)
    np.testing.assert_allclose(out[:, 2], [1, -1, 1, -1], atol=1e-6)
    assert np.all(out[:, 3] > 0)
    np.testing.assert_array_equal(x, original)
    # Current-fire geometry cannot change recent-fire wind projections.
    x[:, features.index("nearest_fire_dx_km")] = -20
    changed = study.derive_features(x, features, lon, lat)
    np.testing.assert_array_equal(changed[:, :3], out[:, :3])
    assert np.all(changed[:, 3] != out[:, 3])


def test_calm_coincident_and_missing_stay_distinct():
    x, features, lon, lat = geometry([180] * 4, [0, 3, np.nan, 3], [0, 0, 0, 0])
    for name in (
        "nearest_recent_fire_60m_dx_km",
        "nearest_recent_fire_60m_dy_km",
        "distance_recent_fire_60m_km",
    ):
        x[1, features.index(name)] = 0
    x[3, features.index("nearest_recent_fire_60m_dx_km")] = np.nan
    out = study.derive_features(x, features, lon, lat)
    np.testing.assert_array_equal(out[0, :2], [0, 0])
    assert np.isnan(out[0, 2])
    assert np.isnan(out[1:, :3]).all()
    assert np.isnan(out[1:, 5]).all()


def test_vpd_fao_example_units_rh_and_explicit_guard():
    # FAO56 Example3 e_s(24.5C)=3.075 kPa, e_s(15C)=1.705 kPa.
    result = study.vapour_pressure_deficit([24.5, 15, 24.5, 24.5], [0, 0, 50, 100])
    np.testing.assert_allclose(result, [3.075, 1.705, 1.5375, 0], atol=0.0005)
    bad = study.vapour_pressure_deficit([-41, 51, 20, 20, np.nan], [50, 50, -1, 101, 50])
    assert np.isnan(bad).all()
    assert np.isfinite(study.vapour_pressure_deficit([-40, -7.2, 50], [50, 50, 50])).all()


def test_candidate_recipe_and_fold_no_leakage():
    cfg, base = contracts()
    candidates = study.make_candidates(base)
    assert [len(c["features"]) for c in candidates] == [34, 38, 40]
    for candidate in candidates:
        assert candidate["rounds"] == 100 and candidate["parameters"]["nthread"] == 2
        assert candidate["parameters"]["seed"] == 47
        assert candidate["positive_weight_rule"] == "training_fold_sqrt"
        assert (
            dict(zip(candidate["features"], candidate["monotone_constraints"], strict=True))[
                "horizon_hours"
            ]
            == 1
        )
        assert sum(candidate["monotone_constraints"]) == 1
    events = {e["id"]: {"event": e} for e in cfg["events"] if e["split"] == "train"}
    all_held = []
    for outer in study.grouped_folds(events, sorted(events), 4):
        all_held += outer["held_ids"]
        assert set(outer["training_ids"]).isdisjoint(outer["held_ids"])
        inner_held = []
        for inner in study.grouped_folds(events, outer["training_ids"], 3):
            inner_held += inner["held_ids"]
            assert set(inner["training_ids"]).isdisjoint(inner["held_ids"])
            assert set(inner["held_ids"]).isdisjoint(outer["held_ids"])
        assert sorted(inner_held) == outer["training_ids"]
    assert sorted(all_held) == sorted(events)
    tied = {c["name"]: {"mean_event_horizon_ap": 0.2} for c in candidates}
    assert study.select_candidate(candidates, tied)["name"] == "A_baseline34"


@pytest.fixture
def inputs(tmp_path):
    cfg, features = contracts()
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    config = tmp_path / "config.json"
    config.write_text(json.dumps(cfg))
    (dataset / "config.json").write_bytes(config.read_bytes())
    for event in cfg["events"]:
        if event["split"] != "train":
            continue
        n = 96
        indices = np.tile(np.arange(32), 3)
        x, _, lon, lat = geometry([180] * n, np.ones(n), np.ones(n))
        values = {name: x[:, i] for i, name in enumerate(features)}
        start = study.datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00")).timestamp()
        values.update(
            {
                "horizon_hours": np.repeat([1, 3, 6], 32),
                "distance_fire_km": indices + 2.0,
                "distance_recent_fire_60m_km": indices + 1.0,
                "observed_hourly_precipitation_mm": np.full(n, np.nan),
                "longitude": lon,
                "latitude": lat,
                "row": indices,
                "col": np.zeros(n),
                "issue_epoch_seconds": np.full(n, start + 900),
                "max_input_available_epoch_seconds": np.full(n, start),
                "fire_within_horizon": (indices < 3).astype(int),
            }
        )
        path = dataset / f"{event['id']}.parquet"
        pq.write_table(pa.table(values), path)
        (dataset / f"{event['id']}-report.json").write_text(
            json.dumps({"event": event, "rows": n, "sha256": file_sha256(path)})
        )
    return SimpleNamespace(
        dataset=dataset, config=config, output=tmp_path / "study", plan_only=True
    )


def test_frozen_plan_train_only_full_53_fit_experiment(inputs, monkeypatch):
    original_read = study.pq.read_table
    original_fit = study.expanded.fit
    fit_calls = []

    def guarded_read(path, *args, **kwargs):
        assert Path(path).stem in study.TRAIN_IDS
        return original_read(path, *args, **kwargs)

    def tracked_fit(events, ids, features, candidate):
        assert (inputs.output / "plan.json").is_file()
        assert set(ids) <= study.TRAIN_IDS
        fit_calls.append(tuple(ids))
        return original_fit(events, ids, features, candidate)

    monkeypatch.setattr(study.pq, "read_table", guarded_read)
    monkeypatch.setattr(study.expanded, "fit", tracked_fit)
    frozen = study.experiment(inputs)
    assert frozen["training_started"] is False and not fit_calls
    plan_bytes = (inputs.output / "plan.json").read_bytes()
    inputs.plan_only = False
    report = study.experiment(inputs)
    assert len(fit_calls) == report["fits_executed"] == 53
    assert len(report["outer"]) == 4
    assert report["selected_model"]["horizon_monotonicity_verified"] is True
    assert report["selected_model"]["cpu_reload_max_abs_difference"] <= 1e-6
    assert (inputs.output / "plan.json").read_bytes() == plan_bytes
    assert (
        report["validation_read"] is report["calibration_read"] is report["test_evaluated"] is False
    )
    assert report["operational_use"] is report["probability_calibrated"] is False
    assert report["nested_oof"]["eligible_ap_cells"] == 42
    assert report["final_source_audit"]["all_hashes_match"] is True
    json.dumps(report, allow_nan=False)
    with pytest.raises(FileExistsError):
        study.experiment(inputs)


def test_frozen_data_tamper_rejected_before_fit(inputs, monkeypatch):
    study.experiment(inputs)
    path = inputs.output / "plan.json"
    plan = json.loads(path.read_text())
    plan["source_hashes"]["andong_2020"] = "0" * 64
    path.write_text(json.dumps(plan))
    inputs.plan_only = False

    def no_fit(*args, **kwargs):
        pytest.fail("tampered plan must not train")

    monkeypatch.setattr(study.expanded, "fit", no_fit)
    with pytest.raises(ValueError, match="frozen plan"):
        study.experiment(inputs)
    assert not (inputs.output / "started.json").exists()


def test_train_id_substitution_rejected_before_parquet_read(inputs, monkeypatch):
    cfg = json.loads(inputs.config.read_text())
    cfg["events"][0]["id"] = "forbidden_2025"
    inputs.config.write_text(json.dumps(cfg))
    (inputs.dataset / "config.json").write_bytes(inputs.config.read_bytes())

    def no_read(*args, **kwargs):
        pytest.fail("invalid allowlist must not read parquet")

    monkeypatch.setattr(study.pq, "read_table", no_read)
    with pytest.raises(ValueError, match="allowlist"):
        study.experiment(inputs)


def test_final_source_audit_detects_concurrent_report_change(inputs):
    study.experiment(inputs)
    plan_path = inputs.output / "plan.json"
    plan = json.loads(plan_path.read_text())
    path = inputs.dataset / "andong_2020-report.json"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="changed during"):
        study.verify_frozen_sources(inputs, plan, file_sha256(plan_path))


def test_failure_is_preserved_without_nontrain_read(inputs, monkeypatch):
    study.experiment(inputs)
    inputs.plan_only = False

    def fail(*args, **kwargs):
        raise RuntimeError("deliberate test failure")

    monkeypatch.setattr(study.expanded, "fit", fail)
    with pytest.raises(RuntimeError, match="deliberate"):
        study.experiment(inputs)
    failure = json.loads((inputs.output / "failure.json").read_text())
    assert failure["fits_attempted"] == 1 and failure["validation_read"] is False
    assert not (inputs.output / "selection.json").exists()
