import json
from datetime import UTC, datetime, timedelta

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import shapely
from shapely.geometry import box

import bonghwa_training.gofer_history as history_module
from bonghwa_training.gofer_approach import FEATURES as BASE_FEATURES
from bonghwa_training.gofer_approach import TARGET, Snapshot, event_rows, sha256
from bonghwa_training.gofer_history import (
    FEATURES,
    GEOMETRY_FEATURES,
    NEW_FEATURES,
    augment_table,
    build_history,
    checked_event_table,
    feature_metadata,
    history_features,
    rear_growth_fraction,
)

START = datetime(2020, 1, 1, tzinfo=UTC)


def snapshots(hours=(0, 1, 3, 6, 12), widths=(1, 2, 3, 5, 6), start=START):
    return [
        Snapshot(start + timedelta(hours=h), box(0, 0, w * 1000, 1000), h)
        for h, w in zip(hours, widths, strict=True)
    ]


def test_exact_35_feature_contract_has_no_identifiers_and_all_metadata():
    assert len(FEATURES) == 35 and len(set(FEATURES)) == 35
    assert FEATURES[:7] == BASE_FEATURES
    assert set(feature_metadata()) == set(FEATURES)
    assert not set(FEATURES) & {
        "event_id",
        "target_id",
        "target_longitude",
        "target_latitude",
        "year",
        "issue_time_utc",
        "label_lower_hours",
        "label_upper_hours",
    }
    for item in feature_metadata().values():
        assert item["unit"] and item["description"] and item["nan_meaning"]


def test_signed_closing_speed_and_growth_use_actual_lag():
    features = history_features(
        snapshots()[:4], START + timedelta(hours=6), shapely.points([[10000, 500]])
    )
    assert features["actual_history_hours_1h"].tolist() == [3]
    assert features["past_distance_km_1h"].tolist() == [7]
    assert features["closing_speed_kmh_1h"].tolist() == pytest.approx([2 / 3])
    assert features["area_growth_km2_per_h_1h"].tolist() == pytest.approx([2 / 3])
    assert features["history_known_1h"].tolist() == [1]
    assert features["actual_history_hours_6h"].tolist() == [6]
    assert features["closing_speed_kmh_6h"].tolist() == pytest.approx([4 / 6])


def test_gap_and_missing_history_remain_explicit_without_shorter_fallback():
    data = snapshots((2, 4, 6), (1, 2, 4))
    features = history_features(data, START + timedelta(hours=6), shapely.points([[10000, 500]]))
    assert features["actual_history_hours_3h"].tolist() == [4]
    assert features["closing_speed_kmh_3h"].tolist() == [0.75]
    for lag in (6, 12):
        assert features[f"history_known_{lag}h"].tolist() == [0]
        for prefix in (
            "past_distance_km",
            "closing_speed_kmh",
            "area_growth_km2_per_h",
            "actual_history_hours",
        ):
            assert np.isnan(features[f"{prefix}_{lag}h"]).all()


def test_future_snapshot_rejected_by_pure_feature_function():
    with pytest.raises(ValueError, match="Future perimeter"):
        history_features(snapshots(), START + timedelta(hours=6), shapely.points([[10000, 500]]))


def test_missing_3h_history_does_not_create_growth_direction():
    features = history_features(
        snapshots((5, 6), (1, 2)), START + timedelta(hours=6), shapely.points([[10000, 500]])
    )
    assert features["growth_direction_known_3h"].tolist() == [0]
    for name in GEOMETRY_FEATURES[2:-1]:
        assert np.isnan(features[name]).all()


def test_zero_growth_has_zero_fraction_but_undefined_direction():
    features = history_features(
        snapshots((0, 3), (2, 2)), START + timedelta(hours=3), shapely.points([[10000, 500]])
    )
    assert features["new_growth_area_fraction_3h"].tolist() == [0]
    assert features["growth_direction_known_3h"].tolist() == [0]
    assert np.isnan(features["growth_direction_3h_east_unit"]).all()
    assert np.isnan(features["rear_growth_area_fraction_3h"]).all()


def test_growth_alignment_and_exact_rear_fraction_reverse_with_target_direction():
    points = shapely.points([[10000, 500], [-10000, 500]])
    features = history_features(snapshots((0, 3), (1, 3)), START + timedelta(hours=3), points)
    np.testing.assert_allclose(features["growth_direction_3h_east_unit"], [1, 1])
    np.testing.assert_allclose(features["growth_direction_3h_north_unit"], [0, 0])
    np.testing.assert_allclose(features["target_growth_alignment_3h"], [1, -1])
    np.testing.assert_allclose(features["rear_growth_area_fraction_3h"], [0, 1])
    np.testing.assert_allclose(features["nearest_boundary_to_target_east_unit"], [1, -1])
    assert rear_growth_fraction(box(-1, -1, 1, 1), np.array([0, 0]), shapely.points([[10, 0]]))[
        0
    ] == pytest.approx(0.5)


def table_fixture(year=2020, name="test_2020"):
    start = START.replace(year=year)
    event = {
        "id": name,
        "name": name,
        "year": year,
        "start_utc": start.isoformat(),
        "period_group": str(year),
        "split": "validation" if year == 2021 else "train",
        "snapshots": snapshots((0, 3, 6, 9, 12), (1, 2, 3, 4, 5), start),
    }
    rows, _ = event_rows(event, max_issue_hours=6)
    return pa.Table.from_pylist(rows), event


def test_future_geometry_and_labels_cannot_change_enriched_input_columns():
    table, event = table_fixture()
    first = augment_table(table, event)
    alternate = {
        **event,
        "snapshots": [
            *event["snapshots"][:3],
            Snapshot(START + timedelta(hours=9), box(-500000, -500000, 500000, 500000), 9),
        ],
    }
    second = augment_table(table, alternate)
    assert first.select(table.column_names).equals(second.select(table.column_names))
    for name in NEW_FEATURES:
        np.testing.assert_allclose(
            first[name].to_numpy(), second[name].to_numpy(), rtol=0, atol=0, equal_nan=True
        )
    labels_changed = table.set_column(
        table.schema.get_field_index("label_upper_hours"),
        "label_upper_hours",
        pa.array([123.0] * table.num_rows),
    )
    third = augment_table(labels_changed, event)
    for name in NEW_FEATURES:
        np.testing.assert_allclose(first[name].to_numpy(), third[name].to_numpy(), equal_nan=True)
    assert first.select(table.column_names).equals(table)


def base_fixture(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    tables, events, reports = {}, {}, []
    for year in (2020, 2021):
        name = f"test_{year}"
        table, event = table_fixture(year, name)
        path = base / f"{name}.parquet"
        pq.write_table(table, path)
        record = {
            "event_id": name,
            "split": event["split"],
            "rows": table.num_rows,
            "sha256": sha256(path),
        }
        (base / f"{name}-report.json").write_text(json.dumps(record))
        reports.append(record)
        tables[name], events[name] = table, event
    config = {
        "feature_names": list(BASE_FEATURES),
        "target": TARGET,
        "events": [{k: v for k, v in e.items() if k != "snapshots"} for e in events.values()],
        "source": {"archive_sha256": "fixture"},
        "settings": {"max_issue_hours": 72, "radius_km": 2},
    }
    (base / "config.json").write_text(json.dumps(config))
    report = {
        "config_sha256": sha256(base / "config.json"),
        "events": reports,
        "rows": sum(t.num_rows for t in tables.values()),
    }
    (base / "report.json").write_text(json.dumps(report))
    return base, config, report, tables, events


def test_fixed_split_and_hash_guards(tmp_path):
    base, config, report, _, _ = base_fixture(tmp_path)
    event = config["events"][0]
    checked_event_table(base, event, report)
    with pytest.raises(ValueError, match="split"):
        checked_event_table(base, {**event, "split": "validation"}, report)
    path = base / f"{event['id']}.parquet"
    with path.open("ab") as output:
        output.write(b"changed")
    with pytest.raises(ValueError, match="SHA256"):
        checked_event_table(base, event, report)


def test_build_preserves_every_row_original_feature_label_and_split(tmp_path, monkeypatch):
    base, config, _, tables, events = base_fixture(tmp_path)
    monkeypatch.setattr(
        history_module,
        "verify_archive",
        lambda _: (tmp_path / "archive", {"archive_sha256": "fixture"}),
    )
    monkeypatch.setattr(history_module, "read_archive", lambda *a: (events, {}))
    output = tmp_path / "enriched"
    report = build_history(tmp_path / "raw", base, output)
    result_config = json.loads((output / "config.json").read_text())
    assert report["rows"] == sum(table.num_rows for table in tables.values())
    assert report["feature_count"] == 35
    assert result_config["events"] == config["events"]
    assert result_config["research_radius_km_unchanged"] == 2
    assert "previously exposed" in result_config["validation_role"]
    for name, original in tables.items():
        actual = pq.read_table(output / f"{name}.parquet")
        assert actual.select(original.column_names).equals(original)
        receipt = json.loads((output / f"{name}-report.json").read_text())
        assert receipt["sha256"] == sha256(output / f"{name}.parquet")
        assert receipt["base_parquet_sha256"] == sha256(base / f"{name}.parquet")
    with pytest.raises(ValueError, match="immutable"):
        build_history(tmp_path / "raw", base, output)


def test_base_config_tampering_is_rejected_before_archive_access(tmp_path):
    base, config, _, _, _ = base_fixture(tmp_path)
    config["events"][0]["split"] = "validation"
    (base / "config.json").write_text(json.dumps(config))
    with pytest.raises(ValueError, match="config hash"):
        build_history(tmp_path / "unused", base, tmp_path / "out")
