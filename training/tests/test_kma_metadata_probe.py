import json
import urllib.error
from datetime import UTC, datetime
from io import BytesIO

import pytest

from bonghwa_training.kma_metadata_probe import (
    MAX_NC_BYTES,
    build_plan,
    fetch_once,
    inspect_netcdf,
    inspect_um_text,
    run_probe,
)

KEY = "fake-metadata-probe-key-not-real"
NOW = datetime(2026, 10, 31, 18, tzinfo=UTC)
UM_BODY = b"# TMFC TMEF VARN LEVEL VALUS\n2022030400 2022030401 2002 10 3.2\n"


class Response(BytesIO):
    status = 200
    headers = {}


def nc_fixture(tmp_path, variable="U10", standard_name="eastward_wind", valid_hour=5):
    netcdf = pytest.importorskip("netCDF4")
    path = tmp_path / f"{variable}-{standard_name}-{valid_hour}.nc"
    with netcdf.Dataset(path, "w") as dataset:
        dataset.Conventions = "CF-1.8"
        for name, size in (("time", 1), ("y", 2), ("x", 2)):
            dataset.createDimension(name, size)
        time = dataset.createVariable("time", "f8", ("time",))
        time.standard_name = "time"
        time.units = "hours since 2026-10-31 12:00:00 +00:00"
        time[:] = [valid_hour]
        reference = dataset.createVariable("reference", "f8", ("time",))
        reference.standard_name = "forecast_reference_time"
        reference.units = time.units
        reference[:] = [0]
        lon = dataset.createVariable("lon", "f8", ("y", "x"))
        lon.standard_name = "longitude"
        lon[:] = [[129.295, 129.305], [129.295, 129.305]]
        lat = dataset.createVariable("lat", "f8", ("y", "x"))
        lat.standard_name = "latitude"
        lat[:] = [[36.985, 36.985], [37.005, 37.005]]
        wind = dataset.createVariable(variable, "f4", ("time", "y", "x"), fill_value=-9999)
        if standard_name:
            wind.standard_name = standard_name
        wind.units = "m s-1"
        wind[:] = [[[3, 4], [-9999, 5]]]
    return path.read_bytes()


def result(payload):
    return {
        "status": "response_received",
        "http_status": 200,
        "retrieved_at_utc": NOW.isoformat(),
    }, payload


def test_fixed_plan_is_small_bounded_and_2025_free():
    plan = build_plan()
    assert plan["max_http_attempts"] == len(plan["requests"]) == 3
    assert plan["retry_count"] == 0 and plan["grib_requested"] is False
    assert [r["parameters_without_auth"].get("vars") for r in plan["requests"][:2]] == [
        "U10",
        "V10",
    ]
    for spec in plan["requests"][:2]:
        assert spec["max_bytes"] == 4 * 1024 * 1024
        params = spec["parameters_without_auth"]
        assert params["hf"] == "5" and params["dataType"] == "NC"
        assert [params[x] for x in ("lon1", "lat1", "lon2", "lat2")] == [
            "129.29",
            "36.98",
            "129.31",
            "37.01",
        ]
    um = plan["requests"][2]["parameters_without_auth"]
    assert um["group"] == "UMKR" and um["nwp"] == "N512"
    assert um["tmfc"] == "2022030400" and um["varn"] == "2002,2003,0,1001"
    assert "level" not in um
    assert all(
        datetime.fromisoformat(r["requested_valid_time_utc"]).year != 2025 for r in plan["requests"]
    )


@pytest.mark.parametrize("status", [403, 429, 500, 302])
def test_http_errors_never_retry_or_retain_body(status):
    calls = []

    def opener(request, **kwargs):
        calls.append(request)
        raise urllib.error.HTTPError(
            request.full_url, status, KEY, {"Retry-After": "15"}, BytesIO(KEY.encode())
        )

    record, raw = fetch_once(build_plan()["requests"][0], KEY, opener=opener, now=lambda: NOW)
    assert len(calls) == 1 and raw is None
    assert record["http_status"] == status
    assert KEY not in json.dumps(record)
    if status == 429:
        assert record["retry_after_seconds"] == 15


def test_response_size_and_credentials_checked_before_return():
    spec = build_plan()["requests"][0]
    for body, status in (
        (b"X" * (MAX_NC_BYTES + 1), "body_size_limit"),
        (b"CDF\x01" + KEY.encode(), "sensitive_response_rejected"),
        (b"CDF\x01https://test.invalid/?authKey=other", "sensitive_response_rejected"),
    ):
        record, raw = fetch_once(
            spec, KEY, opener=lambda *a, payload=body, **k: Response(payload), now=lambda: NOW
        )
        assert record["status"] == status and raw is None


def test_transport_error_is_sanitized():
    def opener(request, **kwargs):
        raise urllib.error.URLError(request.full_url)

    record, raw = fetch_once(build_plan()["requests"][0], KEY, opener=opener)
    assert record["status"] == "transport_or_read_error" and raw is None
    assert KEY not in json.dumps(record)


@pytest.mark.parametrize(
    "standard,basis",
    [
        ("eastward_wind", "geographic"),
        ("x_wind", "grid"),
        ("grid_eastward_wind", "grid"),
        ("", "unverified"),
    ],
)
def test_nc_attributes_dimensions_coordinates_and_times_are_provisional(tmp_path, standard, basis):
    meta = inspect_netcdf(nc_fixture(tmp_path, standard_name=standard), build_plan()["requests"][0])
    assert meta["source_declared_axis_basis"] == basis
    assert meta["wind_basis_validated"] is False and meta["csv_values_compared"] is False
    assert meta["source_unit_matches_documentation"] is True
    assert meta["dimensions"] == {"time": 1, "y": 2, "x": 2}
    assert meta["time_candidates_match_request"] is True
    assert meta["reference_candidates_match_request"] is True
    assert all(item["within_requested_bbox"] for item in meta["coordinate_bounds"].values())
    assert meta["variables"]["U10"]["raw_values"][0][1][0] == -9999
    assert meta["source_height_confirmed"] is False


def test_wrong_time_or_axis_name_not_silently_confirmed(tmp_path):
    meta = inspect_netcdf(
        nc_fixture(tmp_path, standard_name="northward_wind", valid_hour=6),
        build_plan()["requests"][0],
    )
    assert meta["source_declared_axis_basis"] == "unverified"
    assert meta["time_candidates_match_request"] is False
    with pytest.raises(ValueError, match="magic"):
        inspect_netcdf(b"<html>200 success</html>", build_plan()["requests"][0])


def test_um_header_is_not_accepted_as_height_or_schema_verification():
    spec = build_plan()["requests"][2]
    meta = inspect_um_text(UM_BODY, spec)
    assert meta["numeric_candidate_rows"] == 1
    assert meta["requested_reference_stamp_seen"] and meta["requested_valid_stamp_seen"]
    assert meta["schema_verified"] is False and meta["height_confirmed"] is False
    for bad in (
        b"<html>TMFC TMEF VARN LEVEL 2022030400</html>",
        b"# TMFC TMEF VARN LEVEL\n",
        b"ERROR 403",
        b"1,2,3",
    ):
        with pytest.raises(ValueError):
            inspect_um_text(bad, spec)


def test_plan_saved_before_any_request_and_all_raw_files_are_private(tmp_path):
    output = tmp_path / "output"
    u = nc_fixture(tmp_path)
    v = nc_fixture(tmp_path, variable="V10", standard_name="northward_wind")
    calls, sleeps = [], []

    def fetch(spec, key):
        assert (output / "plan.json").exists()
        calls.append(spec)
        return result(
            UM_BODY
            if spec["format"] == "text"
            else u
            if spec["parameters_without_auth"]["vars"] == "U10"
            else v
        )

    report = run_probe(output, KEY, fetcher=fetch, sleeper=sleeps.append, now=lambda: NOW)
    assert len(calls) == report["actual_http_requests"] == 3
    assert sleeps == [1, 1]
    assert report["metadata_records"] == 3 and report["complete"]
    assert report["wind_basis_validated"] is False
    for path in output.iterdir():
        assert path.stat().st_mode & 0o077 == 0
        assert KEY.encode() not in path.read_bytes()
    for record in report["records"]:
        assert len(record["source_sha256"]) == 64
    with pytest.raises(FileExistsError):
        run_probe(output, KEY)


@pytest.mark.parametrize("status", [403, 429])
def test_access_failure_stops_branch_but_allows_independent_historical_probe(tmp_path, status):
    calls = []

    def fetch(spec, key):
        calls.append(spec)
        if spec["branch"] == "kiml_netcdf":
            return {
                "status": "rate_limited" if status == 429 else "http_error",
                "http_status": status,
            }, None
        return result(UM_BODY)

    report = run_probe(tmp_path / "output", KEY, fetcher=fetch, sleeper=lambda _: None)
    assert len(calls) == 2
    assert report["records"][1]["status"] == "skipped_after_branch_access_failure"
    assert report["records"][2]["status"] == "metadata_recorded"
    assert report["complete"] is False


def test_unknown_and_sensitive_body_is_never_persisted(tmp_path):
    def fetch(spec, key):
        return result(b"<html>123 error</html>" if spec["format"] == "netcdf" else KEY.encode())

    output = tmp_path / "output"
    report = run_probe(output, KEY, fetcher=fetch, sleeper=lambda _: None)
    assert report["metadata_records"] == 0
    assert sorted(p.name for p in output.iterdir()) == ["plan.json", "report.json"]
    assert KEY not in (output / "report.json").read_text()
