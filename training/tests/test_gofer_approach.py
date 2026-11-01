import hashlib
import io
import json
import math
import zipfile
from datetime import UTC, datetime, timedelta

import numpy as np
import pyarrow.parquet as pq
import pytest
import shapefile
import shapely
from pyproj import CRS
from shapely.geometry import box

from bonghwa_training.gofer_approach import (
    FEATURES,
    Snapshot,
    approach_intervals,
    build_dataset,
    candidate_points,
    event_rows,
    input_features,
    read_archive,
    verify_archive,
)

START = datetime(2020, 1, 1, tzinfo=UTC)


def snapshots(hours=(0, 1, 3, 6), distances=(1, 2, 4, 7)):
    return [
        Snapshot(START + timedelta(hours=h), box(0, 0, d * 1000, 1000), h)
        for h, d in zip(hours, distances, strict=True)
    ]


def test_interval_censoring_uses_actual_observation_bounds():
    lower, upper, current = approach_intervals(
        snapshots(), START + timedelta(hours=1), shapely.points([[4500, 500]]), 500, 6
    )
    assert lower.tolist() == [0]
    assert upper.tolist() == [2]
    assert current.tolist() == [False]


def test_right_censoring_stops_at_last_observation_not_requested_horizon():
    lower, upper, _ = approach_intervals(
        snapshots(), START + timedelta(hours=1), shapely.points([[50000, 500]]), 500, 12
    )
    assert lower.tolist() == [5]
    assert np.isinf(upper).all()


def test_gap_before_positive_retains_last_known_negative():
    lower, upper, _ = approach_intervals(snapshots(), START, shapely.points([[6500, 500]]), 500, 6)
    assert lower.tolist() == [3]
    assert upper.tolist() == [6]


def test_current_approach_is_separate_and_includes_boundary():
    lower, upper, current = approach_intervals(
        snapshots(), START, shapely.points([[1500, 500]]), 500, 6
    )
    assert current.tolist() == [True]
    assert lower.tolist() == upper.tolist() == [0]


def test_future_outside_horizon_cannot_make_positive():
    lower, upper, _ = approach_intervals(snapshots(), START, shapely.points([[6500, 500]]), 500, 3)
    assert lower.tolist() == [3]
    assert np.isinf(upper).all()


def test_future_snapshots_rejected_for_features():
    with pytest.raises(ValueError, match="Future perimeter"):
        input_features(
            snapshots(), START + timedelta(hours=1), shapely.points([[9000, 500]]), START
        )


def test_closing_speed_uses_actual_history_delta():
    history = snapshots((0, 2), (1, 5))
    f = input_features(history, START + timedelta(hours=2), shapely.points([[9000, 500]]), START)
    assert f["closing_speed_kmh"].tolist() == [2]
    assert f["history_elapsed_hours"].tolist() == [2]
    assert set(f) == set(FEATURES)
    assert not any("longitude" in k or "fareaPer" in k for k in f)


def test_grid_is_current_perimeter_annulus():
    geometry = box(0, 0, 1000, 1000)
    points, east, north = candidate_points(geometry, 1000, 3000, 1000)
    d = shapely.distance(geometry, points)
    assert len(points) == len(east) == len(north) > 0
    assert np.all((d > 1000) & (d <= 3000))
    assert np.all(east % 1000 == 0)


def test_features_unchanged_when_future_perimeter_changes():
    first = snapshots((0, 3, 6, 9, 12), (1, 2, 3, 4, 5))
    second = snapshots((0, 3, 6, 9, 12), (1, 2, 3, 20, 30))
    event = {"id": "x", "split": "train", "start_utc": START.isoformat()}
    a, _ = event_rows({**event, "snapshots": first}, max_issue_hours=6)
    b, _ = event_rows({**event, "snapshots": second}, max_issue_hours=6)
    assert len(a) == len(b) > 0
    for ra, rb in zip(a, b, strict=True):
        assert ra["target_id"] == rb["target_id"]
        assert all(ra[k] == rb[k] for k in FEATURES)
    assert any(
        ra["label_upper_hours"] != rb["label_upper_hours"] for ra, rb in zip(a, b, strict=True)
    )


def test_duplicate_timestamps_rejected():
    data = snapshots((0, 0), (1, 2))
    with pytest.raises(ValueError, match="strictly increasing"):
        approach_intervals(data, START, shapely.points([[9000, 500]]), 500, 6)


def archive_fixture(tmp_path, license_id="cc-by-4.0"):
    raw = tmp_path / "raw"
    raw.mkdir()
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    writer = shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYGON)
    for name, kind, size, decimal in [
        ("fname", "C", 30, 0),
        ("fyear", "N", 4, 0),
        ("tUTC", "C", 30, 0),
        ("timestep", "N", 5, 0),
        ("fareaPer", "N", 10, 3),
    ]:
        writer.field(name, kind, size=size, decimal=decimal)
    metadata = "fname,fyear,GOESIg_UTC\n"
    for name, year in [("Old Fire", 2020), ("New Fire", 2021)]:
        start = START.replace(year=year)
        metadata += f"{name},{year},{start.isoformat()}\n"
        for hour in range(1, 79):
            west, south, east, north = -121, 39, -121 + hour * 0.002, 39.05
            writer.poly(
                [[(west, south), (west, north), (east, north), (east, south), (west, south)]]
            )
            writer.record(name, year, (start + timedelta(hours=hour)).isoformat(), hour, 999)
    writer.close()
    path = raw / "GOFER.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("GOFER/fireData.csv", metadata)
        base = "GOFER/GOFER_Combined/GOFERC_fireProg"
        for ext, value in [
            ("shp", shp.getvalue()),
            ("shx", shx.getvalue()),
            ("dbf", dbf.getvalue()),
            ("prj", CRS.from_epsg(4326).to_wkt()),
        ]:
            z.writestr(base + "." + ext, value)
    data = path.read_bytes()
    (raw / "record.json").write_text(
        json.dumps(
            {
                "id": 14642378,
                "metadata": {"license": {"id": license_id}, "version": "0.2"},
                "files": [
                    {
                        "key": "GOFER.zip",
                        "size": len(data),
                        "checksum": "md5:" + hashlib.md5(data).hexdigest(),
                    }
                ],
            }
        )
    )
    return raw


def test_archive_rights_and_checksum_gate(tmp_path):
    raw = archive_fixture(tmp_path, "unknown")
    with pytest.raises(ValueError, match="CC BY"):
        verify_archive(raw)
    record = json.loads((raw / "record.json").read_text())
    record["metadata"]["license"]["id"] = "cc-by-4.0"
    record["files"][0]["checksum"] = "md5:wrong"
    (raw / "record.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match="checksum"):
        verify_archive(raw)


def test_source_reader_fixed_year_split_and_ignores_final_area(tmp_path):
    raw = archive_fixture(tmp_path)
    events, _ = read_archive(raw / "GOFER.zip")
    assert events["old_fire_2020"]["split"] == "train"
    assert events["new_fire_2021"]["split"] == "validation"
    assert events["new_fire_2021"]["period_group"] == "2021"
    assert "fareaPer" not in events["new_fire_2021"]


def test_dataset_contract_and_no_overwrite(tmp_path):
    raw = archive_fixture(tmp_path)
    output = tmp_path / "processed"
    report = build_dataset(raw, output)
    config = json.loads((output / "config.json").read_text())
    assert report["retrospective_proxy_only"]
    assert not report["source_asof_verified"]
    assert not report["operational_use"]
    assert config["feature_names"] == list(FEATURES)
    assert len(report["events"]) == 2
    for event in report["events"]:
        data = pq.read_table(output / f"{event['event_id']}.parquet").to_pylist()
        assert len(data) == event["rows"]
        assert all(not row["current_approach"] for row in data)
        assert all(row["label_upper_hours"] > row["label_lower_hours"] for row in data)
        assert all(
            row["label_lower_hours"] > 0 or math.isfinite(row["label_upper_hours"]) for row in data
        )
    with pytest.raises(ValueError, match="overwrite"):
        build_dataset(raw, output)
