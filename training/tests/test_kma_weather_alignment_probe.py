import io
import json
import urllib.error
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from bonghwa_training import kma_weather_alignment_probe as probe


class Response(io.BytesIO):
    code = 200
    headers = {"Content-Type": "text/plain"}


def test_fixed_budget_dates_and_one_nc_registration_recheck():
    plan = probe.build_plan()
    assert len(plan["requests"]) == 11 <= 20
    assert sum(s["max_bytes"] + 1 for s in plan["requests"]) <= 100 * 1024 * 1024
    nc = [s for s in plan["requests"] if s["kind"] == "netcdf"]
    assert len(nc) == 1
    for spec in plan["requests"]:
        assert "authKey" not in spec["parameters_without_auth"]
        if spec["kind"] != "netcdf":
            params = spec["parameters_without_auth"]
            dates = [v for k, v in params.items() if k in ("tm", "tm2", "tmfc")]
            assert all(v.startswith(("2020", "2021", "2022")) for v in dates)


def test_secret_echo_never_persisted(tmp_path):
    key = "fake-private-test-key"
    spec = probe.build_plan()["requests"][1]
    response = Response(key.encode())
    result, body = probe.fetch(spec, key, opener=lambda *a, **k: response)
    assert body is None
    assert result["status"] == "sensitive_response_discarded"
    assert key not in json.dumps(result)


def test_403_body_safe_and_no_request_url_in_exception():
    spec = probe.build_plan()["requests"][0]

    def failed(*args, **kwargs):
        raise urllib.error.HTTPError(
            "SECRET-URL",
            403,
            "SECRET-REASON",
            {},
            io.BytesIO(b'{"result":{"status":403,"message":"apply first"}}'),
        )

    result, body = probe.fetch(spec, "private-key", opener=failed)
    assert body is None and result["http_status"] == 403
    assert "SECRET" not in json.dumps(result)


def test_provider_403_inside_http200_stops_endpoint(tmp_path):
    calls = []

    def fetcher(spec, key):
        calls.append(spec["endpoint"])
        return {"status": "access_error", "http_status": 200, "provider_status": 403}, None

    report = probe.run(tmp_path / "raw", "private-key", fetcher=fetcher, sleeper=lambda _: None)
    assert len(calls) == len(set(calls)) == 6
    assert report["actual_http_requests"] == 6
    assert len(report["records"]) == 11
    assert sum(r["status"].startswith("skipped") for r in report["records"]) == 5


@pytest.mark.parametrize("status", [401, 429])
def test_auth_or_rate_error_stops_all(tmp_path, status):
    report = probe.run(
        tmp_path / "raw",
        "private-key",
        fetcher=lambda *_: ({"status": "http_or_provider_error", "http_status": status}, None),
        sleeper=lambda _: None,
    )
    assert report["actual_http_requests"] == 1


def test_response_size_guard():
    spec = {**probe.build_plan()["requests"][0], "max_bytes": 4}
    result, body = probe.fetch(spec, "private-key", opener=lambda *a, **k: Response(b"12345"))
    assert result["status"] == "size_limit_exceeded" and body is None


def test_private_key_only_fixed_file_without_shell(tmp_path, monkeypatch):
    monkeypatch.setattr(probe.Path, "home", lambda: tmp_path)
    path = tmp_path / ".config/bonghwajigi/training.env"
    path.parent.mkdir(parents=True)
    path.write_text("# comment\nOTHER=ignored\nexport KMA_APIHUB_AUTH_KEY='fake-test-key'\n")
    assert probe.read_server_key() == "fake-test-key"
    path.write_text("KMA_APIHUB_AUTH_KEY=one-key-valid\nKMA_APIHUB_AUTH_KEY=two-key-valid\n")
    with pytest.raises(ValueError, match="one private"):
        probe.read_server_key()


def test_output_is_immutable(tmp_path):
    output = tmp_path / "already"
    output.mkdir()
    with pytest.raises(FileExistsError):
        probe.run(output, "private-key", fetcher=lambda *_: pytest.fail("no call"))


def test_gfs_exact_old_cycle_heights_and_range():
    index = (
        b"1:0:d=2022030318:TMP:2 m above ground:7 hour fcst:\n"
        b"2:100:d=2022030318:RH:2 m above ground:7 hour fcst:\n"
        b"3:200:d=2022030318:UGRD:10 m above ground:7 hour fcst:\n"
        b"4:300:d=2022030318:VGRD:10 m above ground:7 hour fcst:\n"
        b"5:400:d=2022030318:LAND:surface:7 hour fcst:\n"
    )
    ranges, combined = probe.gfs_ranges(index)
    assert combined == (0, 399) and ranges["UGRD"] == (200, 299)
    with pytest.raises(ValueError, match="reference time"):
        probe.gfs_ranges(index.replace(b"2022030318", b"2025030318"))
    with pytest.raises(ValueError, match="exactly one"):
        probe.gfs_ranges(index.replace(b"10 m above ground", b"100 m above ground"))


def test_gfs_404_stops_after_one_request(tmp_path):
    calls = []

    def absent(url, **kwargs):
        calls.append(url)
        return {"http_status": 404, "bytes_read": 0}, None

    report = probe.gfs_probe(tmp_path / "gfs", fetcher=absent)
    assert report["actual_requests"] == len(calls) == 1
    assert report["status"] == "historical_index_unavailable"
    assert report["historical_publication_time_verified"] is False


def test_gfs_rejects_nonexact_range_and_oversize():
    response = Response(b"12345")
    # Header/body checks precede any parsing or file save.
    with pytest.raises(ValueError, match="complete meteorological"):
        probe.gfs_metadata(response.read(), "UGRD")


def test_gfs_grid_axis_and_time_metadata():
    ident, grid, product = bytearray(21), bytearray(72), bytearray(34)
    ident[5:7], ident[11] = (7).to_bytes(2), 1
    ident[12:14], ident[14:19], ident[19:21] = (
        (2022).to_bytes(2),
        bytes([3, 3, 18, 0, 0]),
        b"\x00\x01",
    )
    grid[30:34], grid[34:38] = (1440).to_bytes(4), (721).to_bytes(4)
    grid[54] = 48
    grid[63:67] = grid[67:71] = (250000).to_bytes(4)
    product[9:11], product[17] = bytes([2, 2]), 1
    product[18:22], product[22:24], product[24:28] = (
        (7).to_bytes(4),
        bytes([103, 0]),
        (10).to_bytes(4),
    )

    def message():
        parts = []
        for number, part in (
            (1, ident),
            (3, grid),
            (4, product),
            (5, bytearray(5)),
            (6, bytearray(5)),
            (7, bytearray(5)),
        ):
            part[:4], part[4] = len(part).to_bytes(4), number
            parts.append(part)
        raw = (
            b"GRIB\x00\x00\x00\x02"
            + (20 + sum(map(len, parts))).to_bytes(8)
            + b"".join(parts)
            + b"7777"
        )
        return raw

    result = probe.gfs_metadata(message(), "UGRD")
    assert result["wind_axis_verified"] is True
    assert result["valid_time_utc"] == "2022-03-04T01:00:00+00:00"
    grid[54] |= 8
    with pytest.raises(ValueError, match="grid-relative"):
        probe.gfs_metadata(message(), "UGRD")


def test_existing_audit_reads_only_train_input_columns(tmp_path, monkeypatch):
    dataset = tmp_path / "data"
    dataset.mkdir()
    events = [
        {"id": name, "split": "train", "start_utc": "2022-01-01T00:00:00Z"}
        for name in probe.TRAIN_IDS
    ]
    events.append(
        {
            "id": "locked_holdout",
            "split": "test",
            "start_utc": "2025-01-01T00:00:00Z",
            "locked": True,
        }
    )
    (dataset / "config.json").write_text(
        json.dumps(
            {
                "profile": "kor_gk2a_10min_approach_hindcast_1_3_6h_v4_expanded_context_v1",
                "events": events,
            }
        )
    )
    for name in probe.TRAIN_IDS:
        p = dataset / f"{name}.parquet"
        pq.write_table(
            pa.table(
                {
                    "longitude": [129.0],
                    "latitude": [37.0],
                    "issue_epoch_seconds": [1640995200.0],
                    "weather_station_distance_km": [23.0],
                    "weather_age_hours": [1.5],
                }
            ),
            p,
        )
        (dataset / f"{name}-report.json").write_text(json.dumps({"sha256": probe.file_sha256(p)}))
    original = pq.read_table
    reads = []

    def guarded(path, *, columns):
        assert Path(path).stem in probe.TRAIN_IDS
        assert "fire_within_horizon" not in columns
        reads.append(Path(path).stem)
        return original(path, columns=columns)

    monkeypatch.setattr(pq, "read_table", guarded)
    result = probe.diagnose_existing(dataset, tmp_path / "audit.json")
    assert set(reads) == probe.TRAIN_IDS and len(reads) == 14
    assert result["target_read"] is result["test_read"] is False


def test_gfs_field_tamper_rejected_before_decoding(tmp_path):
    (tmp_path / "UGRD.grib2").write_bytes(b"tampered")
    (tmp_path / "report.json").write_text(
        json.dumps(
            {
                "status": "four_field_metadata_verified",
                "fields": {"UGRD": {"path": "UGRD.grib2", "sha256": "0" * 64}},
            }
        )
    )
    with pytest.raises(ValueError, match="source hash"):
        probe.inspect_gfs_values(tmp_path)


def primary_dataset(tmp_path):
    dataset, raw = tmp_path / "cohort", tmp_path / "gfs"
    dataset.mkdir()
    raw.mkdir()
    events = []
    for event_id in sorted(probe.TRAIN_IDS):
        year = int(event_id.rsplit("_", 1)[1])
        start = probe.datetime(year, 2, 21, 8, tzinfo=probe.UTC)
        events.append({"id": event_id, "split": "train", "start_utc": start.isoformat()})
        pq.write_table(
            pa.table(
                {
                    "cohort_primary_clear60": [True, True, False],
                    "issue_epoch_seconds": [start.timestamp()] * 3,
                    "row": [0, 1, 2],
                    "col": [0, 1, 2],
                    # One future-unknown row must remain. No outcome decoding.
                    "target_known": [True, False, True],
                    "observed_fire_within_horizon": [1, -1, 0],
                }
            ),
            dataset / (event_id + ".parquet"),
        )
    (dataset / "config.json").write_text(
        json.dumps({"profile": "kor_gk2a_first_future_observation_train_only_v1", "events": events})
    )
    (raw / "report.json").write_text(
        json.dumps(
            {
                "status": "four_field_metadata_verified",
                "response_bytes_read": 2000,
                "requests": [{"url": "https://example.invalid/f.idx", "bytes_read": 20}],
                "fields": {name: {"bytes": 100} for name in probe.GFS_FIELDS},
            }
        )
    )
    return dataset, raw


def test_primary_plan_preserves_unknown_without_decoding_outcome(tmp_path, monkeypatch):
    dataset, raw = primary_dataset(tmp_path)
    original = pq.read_table
    reads = []

    def guarded(path, *, columns):
        assert columns == ["cohort_primary_clear60", "issue_epoch_seconds", "row", "col"]
        reads.append(Path(path).stem)
        return original(path, columns=columns)

    monkeypatch.setattr(pq, "read_table", guarded)
    result = probe.plan_primary_cohort(dataset, raw, tmp_path / "plan")
    assert set(reads) == probe.TRAIN_IDS and len(reads) == 14
    assert result["total_primary_rows_with_horizon_repeats"] == 28
    assert result["total_unique_point_issue_rows"] == 28
    assert result["future_unknown_rows_preserved"] is True
    assert result["future_outcome_or_audit_columns_read"] is False
    assert result["current_only"]["unique_cycle_lead_files"] == 3
    assert result["current_only"]["estimated_requests_index_head_one_range"] == 9
    assert result["current_only"]["requests_four_separate_fields_plus_index"] == 15
    assert result["current_only"]["estimated_bytes_four_exact_fields_plus_index"] == 1260


def test_primary_plan_rejects_nontrain_before_parquet_read(tmp_path, monkeypatch):
    dataset, raw = primary_dataset(tmp_path)
    path = dataset / "config.json"
    cfg = json.loads(path.read_text())
    cfg["events"][0]["split"] = "validation"
    path.write_text(json.dumps(cfg))
    monkeypatch.setattr(pq, "read_table", lambda *_a, **_k: pytest.fail("no nontrain reads"))
    with pytest.raises(ValueError, match="14 unlocked"):
        probe.plan_primary_cohort(dataset, raw, tmp_path / "plan")


def test_old_indexes_four_distinct_fixed_paths_no_retry(tmp_path):
    dataset, raw = primary_dataset(tmp_path)
    probe.plan_primary_cohort(dataset, raw, tmp_path / "plan")
    path = tmp_path / "plan/acquisition-plan.json"
    calls = []

    def unavailable(url):
        assert "/atmos/" not in url
        calls.append(url)
        assert (tmp_path / "indexes/plan.json").exists()
        return {"http_status": 404, "bytes_read": 0}, None

    result = probe.probe_earlier_indexes(path, tmp_path / "indexes", fetcher=unavailable)
    assert len(calls) == result["actual_requests"] == 4
    # Some synthetic cases share a timestamp, but actual fixed cases have distinct dates.
    assert result["weather_grib_downloaded"] is False
    assert all(r["http_status"] == 404 for r in result["records"])


def test_old_indexes_dynamic_cycle_lead_field_metadata(tmp_path):
    dataset, raw = primary_dataset(tmp_path)
    probe.plan_primary_cohort(dataset, raw, tmp_path / "plan")

    def index(url):
        date = url.split("/gfs.")[1].split("/")[0]
        hour = url.split("/gfs.")[1].split("/")[1]
        lead = int(url.rsplit(".f", 1)[1].split(".")[0])
        body = "".join(
            f"{i + 1}:{i * 100}:d={date}{hour}:{var}:{level}:{lead} hour fcst:\n"
            for i, (var, level) in enumerate(
                [(v, data[0]) for v, data in probe.GFS_FIELDS.items()] + [("LAND", "surface")]
            )
        ).encode()
        return {"http_status": 200, "bytes_read": len(body)}, body

    result = probe.probe_earlier_indexes(
        tmp_path / "plan/acquisition-plan.json", tmp_path / "indexes", fetcher=index
    )
    assert all(r["status"] == "four_fields_present_in_index_only" for r in result["records"])
    assert result["total_response_bytes"] <= 512 * 1024
    assert result["wind_axis_verified"] is False


def test_old_index_reader_counts_oversize_sentinel_within_budget(monkeypatch):
    response = Response(b"x" * (128 * 1024))
    response.status = 200

    class Opener:
        def open(self, *args, **kwargs):
            return response

    monkeypatch.setattr(probe.urllib.request, "build_opener", lambda *_: Opener())
    result, payload = probe.public_index_get("https://example.invalid/old.idx")
    assert payload is None and result["bytes_read"] == 128 * 1024
    assert result["status"] == "invalid_or_oversized_response"


def current_plan(tmp_path):
    dataset, raw = primary_dataset(tmp_path)
    probe.plan_primary_cohort(dataset, raw, tmp_path / "plan")
    path = tmp_path / "plan/acquisition-plan.json"
    plan = json.loads(path.read_text())
    # Two synthetic current-hour files; all ten fixed event IDs remain in scope.
    plan["current_only"]["cycle_lead_inventory"] = [
        {
            "cycle_utc": "2022-02-21T00:00:00+00:00",
            "lead_hours": lead,
            "valid_time_utc": f"2022-02-21T{lead:02d}:00:00+00:00",
        }
        for lead in (8, 9)
    ]
    path.write_text(json.dumps(plan))
    return path


def synthetic_current_fetch(url, *, byte_range=None):
    result = {
        "url": url,
        "status": "received",
        "http_status": 200 if byte_range is None else 206,
        "last_modified": "Mon, 21 Feb 2022 03:00:00 GMT",
        "global_file_bytes": 1000,
    }
    if byte_range is None:
        lead = int(url.rsplit(".f", 1)[1].split(".")[0])
        body = "".join(
            f"{i + 1}:{i * 100}:d=2022022100:{var}:{level}:{lead} hour fcst:\n"
            for i, (var, level) in enumerate(
                [(v, data[0]) for v, data in probe.GFS_FIELDS.items()] + [("LAND", "surface")]
            )
        ).encode()
    else:
        body = b"x" * (byte_range[1] - byte_range[0] + 1)
    return {**result, "bytes_read": len(body)}, body


def test_current_all_indexes_precede_fields_complete_sha_receipt(tmp_path, monkeypatch):
    plan = current_plan(tmp_path)
    calls = []

    def fetcher(url, *, byte_range=None):
        calls.append(byte_range)
        return synthetic_current_fetch(url, byte_range=byte_range)

    def metadata(payload, variable, reference, lead):
        assert reference.year == 2022 and lead in (8, 9)
        assert variable in probe.GFS_FIELDS
        return {"grid_sha256": "test-only-grid"}

    monkeypatch.setattr(probe, "gfs_metadata", metadata)
    report = probe.acquire_gfs_2022_current(
        plan, tmp_path / "current", fetcher=fetcher, progress=lambda *_a, **_k: None
    )
    assert report["status"] == "completed"
    assert calls[:2] == [None, None] and all(c is not None for c in calls[2:])
    assert len(calls) == report["actual_requests"] == 10
    assert report["historical_publication_time_verified"] is False
    for item in report["files"]:
        for field in item["fields"].values():
            assert probe.file_sha256(tmp_path / "current" / field["path"]) == field["sha256"]


@pytest.mark.parametrize("status", [403, 404, 429])
def test_current_failed_index_stops_without_fields_or_retry(tmp_path, status):
    plan = current_plan(tmp_path)
    calls = []

    def fetcher(url, *, byte_range=None):
        calls.append((url, byte_range))
        if len(calls) == 2:
            return {"status": "http_error", "http_status": status, "bytes_read": 0}, None
        return synthetic_current_fetch(url, byte_range=byte_range)

    report = probe.acquire_gfs_2022_current(
        plan, tmp_path / "current", fetcher=fetcher, progress=lambda *_a, **_k: None
    )
    assert report["status"] == "failed" and len(calls) == 2
    assert all(byte_range is None for _, byte_range in calls)
    assert not list((tmp_path / "current").rglob("*.grib2"))


def test_current_late_object_time_blocks_before_field_download(tmp_path):
    plan = current_plan(tmp_path)

    def fetcher(url, *, byte_range=None):
        result, body = synthetic_current_fetch(url, byte_range=byte_range)
        return {**result, "last_modified": "Mon, 21 Feb 2022 09:00:00 GMT"}, body

    report = probe.acquire_gfs_2022_current(
        plan, tmp_path / "current", fetcher=fetcher, progress=lambda *_a, **_k: None
    )
    assert report["status"] == "failed" and report["actual_requests"] == 1
    assert report["stage"] == "indexes"


def test_current_grib_metadata_failure_stops_after_first_field(tmp_path, monkeypatch):
    plan = current_plan(tmp_path)

    def wrong(*_a, **_k):
        raise ValueError("wrong time or axis")

    monkeypatch.setattr(probe, "gfs_metadata", wrong)
    report = probe.acquire_gfs_2022_current(
        plan, tmp_path / "current", fetcher=synthetic_current_fetch, progress=lambda *_a, **_k: None
    )
    assert report["status"] == "failed" and report["actual_requests"] == 3
    assert report["stage"] == "fields"
    assert not list((tmp_path / "current").rglob("*.grib2"))
