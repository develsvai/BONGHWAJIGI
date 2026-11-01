import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from pyproj import Geod, Transformer

from bonghwa_training import korea_gfs_experiment as study
from bonghwa_training.download import file_sha256


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    cfg = json.loads((Path(__file__).parents[1] / "configs/korea-gk2a-context-v4.json").read_text())
    base = [f for f in cfg["feature_names"] if f not in cfg["drop_features"]]
    assert base == study.BASE_FEATURES
    cfg.update(
        profile=study.cohort_builder.PROFILE,
        events=[e for e in cfg["events"] if e["split"] == "train"],
        feature_names=base + study.cohort_builder.ADDITIONAL_FEATURES,
        input_feature_allowlist=base + study.cohort_builder.ADDITIONAL_FEATURES,
        target_column="observed_fire_within_horizon",
        unknown_target_value=-1,
    )
    dataset, weather = tmp_path / "cohort", tmp_path / "weather"
    dataset.mkdir()
    weather.mkdir()
    (dataset / "config.json").write_text(json.dumps(cfg))
    (dataset / "plan.json").write_text(json.dumps({"base_features": base}))
    (dataset / "report.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "config_sha256": file_sha256(dataset / "config.json"),
                "plan_sha256": file_sha256(dataset / "plan.json"),
            }
        )
    )
    (weather / "plan.json").write_text(json.dumps({"synthetic": True}))
    context = {
        "profile": study.CONTEXT_PROFILE,
        "status": "completed",
        "plan_sha256": file_sha256(weather / "plan.json"),
        "source_cohort_config_sha256": file_sha256(dataset / "config.json"),
        "source_cohort_plan_sha256": file_sha256(dataset / "plan.json"),
        "wind_basis": "earth_relative_east_north",
        "assumed_release_delay_hours": 6,
        "historical_publication_time_verified": False,
        "events": {},
    }
    for event in cfg["events"]:
        if event["id"] not in study.TRAIN_IDS:
            # Deliberately no 2020/2021 Parquet or event report exists.
            continue
        name = event["id"]
        row = np.tile(np.arange(10), 3)
        n = len(row)
        values = {f: np.ones(n, np.float32) for f in cfg["feature_names"]}
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
            audit_future_fire_count=np.full(n, 99999),
        )
        path = dataset / f"{name}.parquet"
        pq.write_table(pa.table(values), path)
        digest = file_sha256(path)
        (dataset / f"{name}-report.json").write_text(
            json.dumps({"event": event, "rows": n, "sha256": digest})
        )
        reference = np.floor((issue - 6 * 3600) / (6 * 3600)) * (6 * 3600)
        valid = np.floor(issue / 3600) * 3600
        wr = np.arange(9)
        weather_values = {
            "event_id": [name] * 9,
            "issue_epoch_seconds": np.full(9, issue),
            "row": wr,
            "col": np.zeros(9, int),
            "longitude": np.full(9, 129.1),
            "latitude": np.full(9, 37.1),
            "gfs_temperature_c": 20.0 + wr,
            "gfs_humidity_pct": np.full(9, 50.0),
            "gfs_wind_u_ms": np.full(9, 3.0),
            "gfs_wind_v_ms": np.full(9, 4.0),
            "gfs_grid_distance_km": np.full(9, 5.0),
            "gfs_reference_age_hours": np.full(9, (issue - reference) / 3600),
            "gfs_valid_age_hours": np.full(9, (issue - valid) / 3600),
            "gfs_grid_lon": np.full(9, 129.0),
            "gfs_grid_lat": np.full(9, 37.0),
            "gfs_reference_epoch_seconds": np.full(9, reference),
            "gfs_valid_epoch_seconds": np.full(9, valid),
            "gfs_assumed_available_epoch_seconds": np.full(9, reference + 6 * 3600),
            "gfs_forecast_lead_hours": np.full(9, (valid - reference) / 3600),
            "gfs_source_id": ["synthetic_GFS"] * 9,
            "gfs_sample_valid": np.ones(9, bool),
        }
        weather_path = weather / f"{name}.parquet"
        pq.write_table(pa.table(weather_values), weather_path)
        context["events"][name] = {
            "event": event,
            "rows": 9,
            "sha256": file_sha256(weather_path),
            "source_cohort_parquet_sha256": digest,
        }
    (weather / "report.json").write_text(json.dumps(context))
    monkeypatch.setattr(study, "EXPECTED_PRIMARY_ROWS", 270)
    return SimpleNamespace(
        dataset=dataset, weather=weather, output=tmp_path / "model", plan_only=True
    )


def update_weather(inputs, transform):
    name = sorted(study.TRAIN_IDS)[0]
    path = inputs.weather / f"{name}.parquet"
    table = transform(pq.read_table(path))
    pq.write_table(table, path)
    report_path = inputs.weather / "report.json"
    report = json.loads(report_path.read_text())
    report["events"][name].update(rows=len(table), sha256=file_sha256(path))
    report_path.write_text(json.dumps(report))


def change_column(table, name, values):
    return table.set_column(table.schema.get_field_index(name), name, pa.array(values))


def test_exact_weather_substitution_and_equal_recipe():
    a, d = study.make_candidates(study.BASE_FEATURES)
    assert len(a["features"]) == len(d["features"]) == 34
    assert len(set(a["features"]) & set(d["features"])) == 24
    assert set(a["features"]) - set(d["features"]) == set(study.OLD_WEATHER_FEATURES)
    assert set(d["features"]) - set(a["features"]) == set(study.GFS_FEATURES)
    assert a["parameters"] == d["parameters"]
    assert a["rounds"] == d["rounds"] == 100
    assert not any(f.startswith("audit_") for f in d["features"])
    with pytest.raises(ValueError, match="exact original34"):
        study.make_candidates(study.BASE_FEATURES[:-1] + ["audit_future_fire_count"])


def test_true_east_north_current_anchor_wind_and_zero_anchor():
    anchor_lon, anchor_lat = np.full(2, 129.0), np.full(2, 37.0)
    lon, lat, _ = Geod(ellps="WGS84").fwd(anchor_lon, anchor_lat, [90, 0], [1000, 1000])
    projected = Transformer.from_crs(4326, 5179, always_xy=True)
    ax, ay = projected.transform(anchor_lon, anchor_lat)
    tx, ty = projected.transform(lon, lat)
    base = np.ones((2, 34))
    base[:, study.BASE_FEATURES.index("nearest_fire_dx_km")] = (ax - tx) / 1000
    base[:, study.BASE_FEATURES.index("nearest_fire_dy_km")] = (ay - ty) / 1000
    gfs = np.zeros((2, 7))
    gfs[:, 2:4] = [[5, 0], [0, 7]]
    result = study.derive_wind(base, study.BASE_FEATURES, lon, lat, gfs)
    np.testing.assert_allclose(result[:, 0], [5, 7])
    np.testing.assert_allclose(result[:, 1], [5, 7], atol=1e-8)
    np.testing.assert_allclose(result[:, 2], 0, atol=1e-8)
    base[:, study.BASE_FEATURES.index("distance_fire_km")] = 0
    result = study.derive_wind(base, study.BASE_FEATURES, lon, lat, gfs)
    assert np.isnan(result[:, 1:]).all()
    np.testing.assert_allclose(result[:, 0], [5, 7])


def test_join_is_by_identity_not_order_or_future_labels(inputs):
    original = study.load_train(inputs.dataset, inputs.weather)
    update_weather(inputs, lambda table: table.take(pa.array(list(reversed(range(len(table)))))))
    reordered = study.load_train(inputs.dataset, inputs.weather)
    assert set(original[0]) == study.TRAIN_IDS
    assert len(original[4]) == 35
    for event in original[0]:
        a, b = original[0][event], reordered[0][event]
        np.testing.assert_array_equal(a["x"], b["x"])
        np.testing.assert_array_equal(a["y"], b["y"])
        np.testing.assert_allclose(a["x"][:, 34], 20 + a["rows"])
        assert len(a["y"]) == 27 and int((a["y"] == -1).sum()) == 3
    # Future outcome perturbation changes only labels, never join/membership/features.
    name = sorted(study.TRAIN_IDS)[0]
    path = inputs.dataset / f"{name}.parquet"
    table = pq.read_table(path)
    new_y = np.full(len(table), -1, np.int8)
    table = change_column(table, "observed_fire_within_horizon", new_y)
    table = change_column(table, "target_known", np.zeros(len(table), bool))
    pq.write_table(table, path)
    digest = file_sha256(path)
    er = inputs.dataset / f"{name}-report.json"
    er_values = json.loads(er.read_text())
    er_values["sha256"] = digest
    er.write_text(json.dumps(er_values))
    wr = inputs.weather / "report.json"
    wr_values = json.loads(wr.read_text())
    wr_values["events"][name]["source_cohort_parquet_sha256"] = digest
    wr.write_text(json.dumps(wr_values))
    changed = study.load_train(inputs.dataset, inputs.weather)[0][name]
    np.testing.assert_array_equal(changed["x"], original[0][name]["x"])
    np.testing.assert_array_equal(changed["rows"], original[0][name]["rows"])
    assert np.all(changed["y"] == -1)


@pytest.mark.parametrize(
    "bad",
    [
        "missing_row",
        "duplicate_row",
        "future_valid",
        "late_release",
        "nan",
        "invalid_sample",
        "coordinates",
    ],
)
def test_join_refuses_missing_or_future_weather_without_candidate_deletion(inputs, bad):
    def mutate(table):
        if bad == "missing_row":
            return table.slice(1)
        if bad == "duplicate_row":
            return pa.concat_tables([table, table.slice(0, 1)])
        if bad == "future_valid":
            return change_column(
                table, "gfs_valid_epoch_seconds", table["issue_epoch_seconds"].to_numpy() + 3600
            )
        if bad == "late_release":
            return change_column(
                table,
                "gfs_assumed_available_epoch_seconds",
                table["issue_epoch_seconds"].to_numpy() + 1,
            )
        if bad == "nan":
            return change_column(table, "gfs_wind_u_ms", np.full(len(table), np.nan))
        if bad == "invalid_sample":
            return change_column(table, "gfs_sample_valid", np.zeros(len(table), bool))
        return change_column(table, "latitude", np.full(len(table), 37.5))

    update_weather(inputs, mutate)
    with pytest.raises(ValueError):
        study.load_train(inputs.dataset, inputs.weather)


def test_weather_hash_and_source_cohort_sha_are_required(inputs):
    path = inputs.weather / f"{sorted(study.TRAIN_IDS)[0]}.parquet"
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="SHA"):
        study.load_train(inputs.dataset, inputs.weather)


def test_2025_metadata_rejected_before_any_event_file_read(inputs, monkeypatch):
    path = inputs.dataset / "config.json"
    cfg = json.loads(path.read_text())
    target = next(e for e in cfg["events"] if e["id"] in study.TRAIN_IDS)
    target["start_utc"] = "2025-03-01T00:00:00Z"
    path.write_text(json.dumps(cfg))
    report_path = inputs.dataset / "report.json"
    report = json.loads(report_path.read_text())
    report["config_sha256"] = file_sha256(path)
    report_path.write_text(json.dumps(report))
    monkeypatch.setattr(study.pq, "read_table", lambda *a, **k: pytest.fail("event read"))
    with pytest.raises(ValueError):
        study.load_train(inputs.dataset, inputs.weather)


def test_full45fits_unknown_budget_period_split_and_non2022_file_guard(inputs, monkeypatch):
    original_read, original_fit, original_sha = (
        study.pq.read_table,
        study.expanded.fit,
        study.file_sha256,
    )
    calls = []

    def guarded_read(path, **kwargs):
        assert Path(path).stem in study.TRAIN_IDS
        assert kwargs["columns"] and not any(f.startswith("audit_") for f in kwargs["columns"])
        return original_read(path, **kwargs)

    def guarded_sha(path):
        stem = Path(path).stem.removesuffix("-report")
        assert stem not in study.recent.TRAIN_IDS - study.TRAIN_IDS
        return original_sha(path)

    def guarded_fit(events, ids, features, candidate):
        assert set(ids).issubset(study.TRAIN_IDS)
        assert all(np.isin(events[e]["y"], [0, 1]).all() for e in ids)
        calls.append(ids)
        return original_fit(events, ids, features, candidate)

    monkeypatch.setattr(study.pq, "read_table", guarded_read)
    monkeypatch.setattr(study, "file_sha256", guarded_sha)
    monkeypatch.setattr(study.expanded, "fit", guarded_fit)
    assert study.run(inputs)["status"] == "plan_frozen"
    plan = json.loads((inputs.output / "plan.json").read_text())
    assert len(plan["inventory"]) == 10
    assert len({d["period_group"] for d in plan["inventory"].values()}) == 7
    for outer in plan["outer_folds"]:
        assert set(outer["held_ids"]).isdisjoint(outer["training_ids"])
        for inner in outer["inner_folds"]:
            assert set(inner["held_ids"]).isdisjoint(inner["training_ids"])
            assert set(inner["held_ids"] + inner["training_ids"]) == set(outer["training_ids"])
    inputs.plan_only = False
    result = study.run(inputs)
    assert result["fits_executed"] == len(calls) == 45
    report = json.loads((inputs.output / "report.json").read_text())
    assert "fixed_gfs34" in report["summaries"]["primary"]
    for diagnostic in report["summaries"]["primary"].values():
        assert diagnostic["budget"]["candidate_rows"] == 270
        assert diagnostic["budget"]["unknown_rows"] == 30
        assert diagnostic["budget"]["selected_rows"] == 30
    assert report["final_source_audit"]["all_hashes_match"]
    audit = report["final_source_audit"]
    assert audit["files_checked"] == (
        audit["source_files_checked"] + audit["code_files_checked"] + audit["plan_files_checked"]
    )
    assert len(report["fit_label_audit"]) == 45
    assert all(fit["positive_rows"] > 0 for fit in report["fit_label_audit"])
    assert report["minimum_inner_training_positive_rows"] > 0
    predictions = original_read(inputs.output / "outer-predictions.parquet")
    assert "fixed_gfs34" in predictions.column_names
    for fold in report["outer"]:
        mask = np.isin(predictions["event_id"].to_numpy(), fold["held_ids"])
        fixed = "fixed_gfs34" if fold["selected"] == "D_gfs_weather34" else "fixed_original34"
        np.testing.assert_array_equal(
            predictions["nested_selected"].to_numpy()[mask], predictions[fixed].to_numpy()[mask]
        )
    assert report["selected_model"]["cpu_reload_max_abs_difference"] == 0
    assert not report["non2022_event_files_read"] and not report["operational_use"]
    assert not report["historical_publication_time_verified"]


def test_training_positive_audit_does_not_reassign_folds(inputs):
    events, base, features, inventory, hashes = study.load_train(inputs.dataset, inputs.weather)
    before = study.make_plan(events, base, features, inventory, hashes)
    for data in events.values():
        data["y"] = np.where(data["y"] < 0, -1, 0)
    events[sorted(events)[0]]["y"][0] = 1
    after = study.make_plan(events, base, features, inventory, hashes)
    assert after["minimum_inner_training_positive_rows"] == 0
    for a, b in zip(before["outer_folds"], after["outer_folds"], strict=True):
        assert a["held_ids"] == b["held_ids"] and a["training_ids"] == b["training_ids"]
        for i, j in zip(a["inner_folds"], b["inner_folds"], strict=True):
            assert i["held_ids"] == j["held_ids"] and i["training_ids"] == j["training_ids"]


def test_frozen_plan_blocks_changed_weather_before_fit(inputs, monkeypatch):
    study.run(inputs)
    update_weather(inputs, lambda t: change_column(t, "gfs_temperature_c", np.full(len(t), 30.0)))
    inputs.plan_only = False
    monkeypatch.setattr(
        study.expanded, "fit", lambda *a, **k: pytest.fail("fit after plan mutation")
    )
    with pytest.raises(ValueError, match="frozen plan/source mismatch"):
        study.run(inputs)
