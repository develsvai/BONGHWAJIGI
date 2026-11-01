import json
from datetime import UTC, datetime
from types import SimpleNamespace

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from pyproj import Geod

from bonghwa_training import korea_gfs_context as context


def test_current_hour_time_uses_six_hour_cycle_release_lag():
    times = ["2022-03-04T00:05:00Z", "2022-03-04T05:59:00Z", "2022-03-04T06:00:00Z"]
    issue = np.array([context.utc_seconds(t) for t in times])
    reference, valid, lead = context.cycle_for_issue(issue)
    assert [datetime.fromtimestamp(int(t), UTC).isoformat() for t in reference] == [
        "2022-03-03T18:00:00+00:00",
        "2022-03-03T18:00:00+00:00",
        "2022-03-04T00:00:00+00:00",
    ]
    assert lead.tolist() == [6, 11, 6]
    assert np.all(valid <= issue) and np.all(reference + 21600 <= issue)
    assert context.source_id(reference[0], lead[0]) == "2022030318-f006"
    with pytest.raises(ValueError, match="2022"):
        context.cycle_for_issue([datetime(2025, 3, 1, tzinfo=UTC).timestamp()])
    with pytest.raises(ValueError, match="integral"):
        context.cycle_for_issue([issue[0] + 0.1])


def test_nearest_native_matches_independent_full_grid_spherical_geodesic():
    lon = np.array([129.25, 129.3749, 129.3751, 128.125, 126.987])
    lat = np.array([37.0, 37.1249, 37.1251, 38.125, 33.337])
    row, col, y, x, distance = context.nearest_native(lon, lat)
    ys, xs = np.meshgrid(np.arange(32, 40.25, 0.25), np.arange(124, 132.25, 0.25), indexing="ij")
    geod = Geod(a=context.SPHERE_RADIUS_M, b=context.SPHERE_RADIUS_M)
    for i in range(len(lon)):
        _, _, metres = geod.inv(
            np.full(xs.size, lon[i]), np.full(ys.size, lat[i]), xs.ravel(), ys.ravel()
        )
        assert distance[i] == pytest.approx(np.min(metres) / 1000, abs=1e-9)
        assert x[i] == col[i] * 0.25 and y[i] == 90 - row[i] * 0.25
    assert distance[0] == 0
    with pytest.raises(ValueError, match="Korean"):
        context.nearest_native([0], [37])


def test_sample_unit_conversion_is_once_and_qc_does_not_zero_fill():
    shape = (context.ROW_STOP - context.ROW_START, context.COL_STOP - context.COL_START)
    values = {"TMP": 293.15, "RH": 67.0, "UGRD": -3.0, "VGRD": 4.0}
    arrays = {key: np.full(shape, v) for key, v in values.items()}
    row = np.array([context.ROW_START, context.ROW_START + 1, context.ROW_START + 2])
    col = np.full(3, context.COL_START)
    arrays["RH"][1, 0] = 9999
    arrays["UGRD"][2, 0] = np.nan
    result = context.sample_values(arrays, row, col)
    assert result["gfs_temperature_c"].tolist() == pytest.approx([20, 20, 20])
    assert result["gfs_sample_valid"].tolist() == [True, False, False]
    assert np.isnan(result["gfs_humidity_pct"][1])
    assert np.isnan(result["gfs_wind_u_ms"][2])
    assert result["gfs_wind_u_ms"][0] == -3


def inputs_file(path, *, conflict=False):
    issue = context.utc_seconds("2022-03-04T00:15:00Z")
    values = {
        "cohort_primary_clear60": [True] * 3 + [False] * 3,
        "issue_epoch_seconds": [issue] * 6,
        "row": [1] * 3 + [2] * 3,
        "col": [3] * 6,
        "latitude": [37.0] * 6,
        "longitude": [129.3, 129.3 if not conflict else 129.4, 129.3] + [130.0] * 3,
        "forbidden_future_label": [1, 1, 1, -1, -1, -1],
    }
    pq.write_table(pa.table(values), path)
    return values


def test_input_only_projection_primary_selection_and_horizon_repeat_identity(tmp_path, monkeypatch):
    path = tmp_path / "input.parquet"
    inputs_file(path)
    original = pq.read_table
    calls = []

    def read(path, *, columns):
        calls.append(columns)
        assert columns == context.INPUT_COLUMNS
        return original(path, columns=columns)

    monkeypatch.setattr(pq, "read_table", read)
    data, count = context.primary_inputs(path)
    assert len(calls) == 1 and count == 3 and len(data["row"]) == 1
    assert data["longitude"][0] == 129.3
    inputs_file(path, conflict=True)
    with pytest.raises(ValueError, match="coordinates disagree"):
        context.primary_inputs(path)


def test_primary_repeat_count_not_silently_deduplicated(tmp_path):
    path = tmp_path / "input.parquet"
    values = inputs_file(path)
    values = {k: v[:-1] for k, v in values.items()}
    values["cohort_primary_clear60"] = [True] * 5
    pq.write_table(pa.table(values), path)
    with pytest.raises(ValueError, match="three horizon"):
        context.primary_inputs(path)


def fake_grid_raw():
    grid = bytearray(72)
    grid[:4], grid[4], grid[14] = (72).to_bytes(4, "big"), 3, 6
    return b"GRIB" + bytes(12) + bytes(grid) + b"7777"


def test_decode_guard_rejects_wrong_units_height_time_and_wgs84_relabel():
    reference = context.utc_seconds("2022-03-03T18:00:00Z")
    tags = {
        "GRIB_UNIT": "[K]",
        "GRIB_ELEMENT": "TMP",
        "GRIB_SHORT_NAME": "2-HTGL",
        "GRIB_REF_TIME": str(reference),
        "GRIB_VALID_TIME": str(reference + 7 * 3600),
        "GRIB_FORECAST_SECONDS": str(7 * 3600),
    }
    sphere = SimpleNamespace(is_geographic=True, to_dict=lambda: {"R": 6371229})
    transform = (0.25, 0, -0.125, 0, -0.25, 90.125)
    args = (sphere, transform, (721, 1440), 1, "TMP", reference, 7, fake_grid_raw())
    context.check_decoding(tags, *args)
    for name, wrong in (
        ("GRIB_UNIT", "[C]"),
        ("GRIB_SHORT_NAME", "10-HTGL"),
        ("GRIB_VALID_TIME", str(reference + 8 * 3600)),
    ):
        with pytest.raises(ValueError, match="disagrees"):
            context.check_decoding({**tags, name: wrong}, *args)
    wgs84 = SimpleNamespace(is_geographic=True, to_dict=lambda: {"a": 6378137, "b": 6356752})
    with pytest.raises(ValueError, match="EPSG4326"):
        context.check_decoding(tags, wgs84, *args[1:])


def test_paths_and_tamper_audit_fail_closed(tmp_path):
    path = tmp_path / "source"
    path.write_text("one")
    checks = {str(path): context.file_sha256(path)}
    context.verify_hashes(checks)
    path.write_text("two")
    with pytest.raises(ValueError, match="changed"):
        context.verify_hashes(checks)
    with pytest.raises(ValueError, match="escapes"):
        context.inside(tmp_path, "../outside")
    with pytest.raises(ValueError, match="escapes"):
        context.inside(tmp_path, str(path))


def test_plan_frozen_then_build_with_same_input_only_receipt(tmp_path, monkeypatch):
    cohort, raw, decoded, output = [tmp_path / n for n in ("cohort", "raw", "decoded", "output")]
    for folder in (cohort, raw, decoded):
        folder.mkdir()
    path = cohort / "uljin_2022.parquet"
    inputs_file(path)
    ref = context.utc_seconds("2022-03-03T18:00:00Z")
    sid = context.source_id(ref, 6)
    shape = (context.ROW_STOP - context.ROW_START, context.COL_STOP - context.COL_START)
    np.savez(
        decoded / (sid + ".npz"),
        TMP=np.full(shape, 293.15),
        RH=np.full(shape, 70.0),
        UGRD=np.full(shape, -3.0),
        VGRD=np.full(shape, 4.0),
    )
    context.save(decoded / "report.json", {"files": {sid: {"path": sid + ".npz"}}})
    plan = {
        "profile": context.PROFILE,
        "rows": 1,
        "source_hashes": {str(path): context.file_sha256(path)},
        "events": {
            "uljin_2022": {
                "rows": 1,
                "event": {"id": "uljin_2022"},
                "source_cohort_parquet_sha256": context.file_sha256(path),
            }
        },
    }
    monkeypatch.setattr(context, "make_plan", lambda *args: plan)
    assert context.build(cohort, raw, decoded, output, True)["status"] == "plan_frozen"
    result = context.build(cohort, raw, decoded, output)
    assert result == {"status": "completed", "rows": 1, "invalid_samples": 0}
    table = pq.read_table(output / "uljin_2022.parquet")
    assert table["gfs_reference_age_hours"][0].as_py() == 6.25
    assert table["gfs_valid_age_hours"][0].as_py() == 0.25
    assert table["gfs_assumed_available_epoch_seconds"][0].as_py() == ref + 21600
    assert "forbidden_future_label" not in table.column_names
    assert json.loads((output / "report.json").read_text())["events"]["uljin_2022"]["rows"] == 1
    with pytest.raises(FileExistsError):
        context.build(cohort, raw, decoded, output)
