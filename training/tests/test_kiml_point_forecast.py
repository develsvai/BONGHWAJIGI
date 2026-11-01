import hashlib
import json
import urllib.error
from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest

from bonghwa_training.kiml_point_forecast import (
    CSV_COLUMNS,
    MAX_BYTES,
    build_plan,
    fetch_once,
    parse_point_csv,
    run_probe,
)

KEY = "fake-test-key-not-a-real-credential"
ISSUE = datetime(2026, 10, 31, 12, tzinfo=UTC)
ASOF = datetime(2026, 10, 31, 16, 38, tzinfo=UTC)


def plan():
    return build_plan(ISSUE, ASOF, lon=127.5, lat=37.5)


def body(spec, *, value=None, **overrides):
    values = {"U10": 3.0, "V10": 4.0, "T2": 293.03, "RH2": 50.0}
    row = {
        "req_lon": 127.5,
        "req_lat": 37.5,
        "lvl": -1.0,
        "ix": 716,
        "iy": 714,
        "lon": 127.493958,
        "lat": 37.495201,
        "value": values[spec["requested_variable"]] if value is None else value,
        **overrides,
    }
    return (
        ",".join(CSV_COLUMNS) + "\n" + ",".join(str(row[k]) for k in CSV_COLUMNS) + "\n"
    ).encode()


def successful_fetch(spec, key):
    payload = body(spec)
    return {
        "status": "response_received",
        "retrieved_at_utc": (ASOF + timedelta(seconds=10)).isoformat(),
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "attempts": [{"attempt": 1, "http_status": 200}],
    }, payload


class Response(BytesIO):
    status = 200
    headers = {}


def test_plan_exact_24_future_requests_and_real_leads():
    result = plan()
    requests = result["requests"]
    assert len(requests) == result["max_http_attempts"] == 24
    assert {r["requested_lead_from_cycle_hours"] for r in requests} == set(range(5, 11))
    assert requests[0]["requested_lead_from_asof_hours"] == pytest.approx(22 / 60)
    assert requests[-1]["requested_valid_time_utc"] == "2026-10-31T22:00:00+00:00"
    assert {r["requested_variable"] for r in requests} == {"U10", "V10", "T2", "RH2"}
    assert all(r["parameters_without_auth"]["group"] == "KIML" for r in requests)
    assert all("help" not in r["parameters_without_auth"] for r in requests)
    assert all("getAttachFile" in r["unit_and_height_documentation"] for r in requests)
    assert result["holdout_2025_accessed"] is False
    on_hour = build_plan(ISSUE, ISSUE)
    assert on_hour["requests"][0]["requested_lead_from_cycle_hours"] == 1


@pytest.mark.parametrize(
    "issue,asof,kwargs",
    [
        (datetime(2025, 12, 31, 12, tzinfo=UTC), ASOF, {}),
        (datetime(2026, 2, 8, 12, tzinfo=UTC), ASOF, {}),
        (ISSUE + timedelta(hours=6), ASOF, {}),
        (ISSUE - timedelta(days=2), ASOF, {}),
        (ISSUE + timedelta(hours=1), ASOF, {}),
        (ISSUE, ASOF.replace(tzinfo=None), {}),
        (ISSUE, ASOF, {"lat": float("nan")}),
        (ISSUE, ASOF, {"lon": 10}),
    ],
)
def test_invalid_cycles_dates_points_rejected(issue, asof, kwargs):
    with pytest.raises(ValueError):
        build_plan(issue, asof, **kwargs)


def test_actual_sample_schema_does_not_invent_echoed_time_unit_or_height():
    spec = plan()["requests"][2]
    actual = (
        b"req_lon,req_lat,lvl,ix,iy,lon,lat,value\n"
        b"127.500000,37.500000,-1.0,716,714,127.493958,37.495201,2.930300e+02\n"
    )
    parsed = parse_point_csv(actual, spec)
    assert parsed["value"] == 293.03
    assert parsed["grid"]["ix"] == 716
    assert parsed["level_marker"] == -1
    assert parsed["source_reference_time_utc"] is None
    for field in ("reference", "valid_time", "variable", "unit", "height"):
        assert parsed[f"source_{field}_confirmed"] is False


def test_actual_float32_coordinate_echo_is_accepted_without_widening_tolerance():
    spec = build_plan(ISSUE, ASOF, lon=129.3, lat=37.0)["requests"][0]
    actual = (
        b"req_lon,req_lat,lvl,ix,iy,lon,lat,value\n"
        b"129.300003,37.000000,-1.0,873,664,129.293854,36.991207,-5.000000e-02\n"
    )
    parsed = parse_point_csv(actual, spec)
    assert parsed["value"] == -0.05
    assert parsed["request_coordinate_echo"]["req_lon"] == 129.300003
    assert parsed["request_coordinate_echo_precision"]["req_lon"] == (
        "requested_float32_six_decimal_echo"
    )
    # The original float64 request echo remains supported too.
    exact = parse_point_csv(actual.replace(b"129.300003", b"129.300000"), spec)
    assert exact["request_coordinate_echo_precision"]["req_lon"] == (
        "requested_float64_six_decimal_echo"
    )
    # Reject values between the two allowed precision representations, as well
    # as values outside them. A loose coordinate tolerance would accept these.
    for rejected in (b"129.300001", b"129.300002", b"129.300004", b"129.300010"):
        with pytest.raises(ValueError, match="coordinates"):
            parse_point_csv(actual.replace(b"129.300003", rejected), spec)
    with pytest.raises(ValueError, match="coordinates"):
        parse_point_csv(actual.replace(b"37.000000", b"37.000001"), spec)


@pytest.mark.parametrize(
    "variable,value",
    [
        ("T2", -999),
        ("T2", -9999),
        ("T2", 20),
        ("T2", 341),
        ("RH2", -1),
        ("RH2", 101),
        ("U10", -9999),
        ("V10", 151),
        ("U10", "NaN"),
        ("T2", "inf"),
        ("RH2", ""),
        ("V10", "1e1000"),
    ],
)
def test_missing_sentinels_nonfinite_and_bad_units_never_become_weather(variable, value):
    spec = next(r for r in plan()["requests"] if r["requested_variable"] == variable)
    with pytest.raises(ValueError):
        parse_point_csv(body(spec, value=value), spec)


@pytest.mark.parametrize(
    "overrides",
    [{"req_lon": 127.6}, {"lvl": 2}, {"ix": 1.5}, {"iy": -1}, {"lon": 128.5}, {"lat": "NaN"}],
)
def test_request_coordinates_grid_and_response_marker_are_checked(overrides):
    spec = plan()["requests"][0]
    with pytest.raises(ValueError):
        parse_point_csv(body(spec, **overrides), spec)


def test_exact_header_and_one_row_required():
    spec = plan()["requests"][0]
    good = body(spec)
    for bad in (
        good.replace(b"req_lon,req_lat", b"req_lat,req_lon"),
        good + good.splitlines()[1] + b"\n",
        good.replace(b",value", b",value,extra"),
        b"<html>200 3.0</html>",
    ):
        with pytest.raises(ValueError):
            parse_point_csv(bad, spec)


@pytest.mark.parametrize("status", [403, 429, 500])
def test_fetcher_makes_one_attempt_even_when_old_fetcher_would_retry(status):
    calls = []

    def opener(request, **kwargs):
        calls.append(request)
        raise urllib.error.HTTPError(request.full_url, status, KEY, {"Retry-After": "5"}, None)

    result, payload = fetch_once(plan()["requests"][0], KEY, opener=opener, now=lambda: ASOF)
    assert len(calls) == 1
    assert payload is None
    assert result["http_status"] == status
    if status == 429:
        assert result["status"] == "rate_limited"
        assert result["retry_after_seconds"] == 5
    assert KEY not in json.dumps(result)


def test_transport_exceptions_with_credentials_never_escape_or_retry():
    calls = []

    def opener(request, **kwargs):
        calls.append(request)
        raise urllib.error.URLError(request.full_url + KEY)

    result, payload = fetch_once(plan()["requests"][0], KEY, opener=opener, now=lambda: ASOF)
    assert len(calls) == 1 and payload is None
    assert result["status"] == "transport_or_read_error"
    assert KEY not in json.dumps(result)


def test_full_run_saves_plan_first_derives_celsius_and_magnitude_but_no_bearing(tmp_path):
    output = tmp_path / "forecast"
    calls, delays = [], []

    def fetch(spec, key):
        assert (output / "plan.json").exists()
        calls.append(spec)
        return successful_fetch(spec, key)

    report = run_probe(plan(), output, KEY, fetcher=fetch, sleeper=delays.append, now=lambda: ASOF)
    assert len(calls) == 24 and delays == [1] * 23
    assert report["complete"] and report["all_future_at_retrieval"]
    assert len(report["hours"]) == 6
    hour = report["hours"][0]
    assert hour["temperature_celsius"] == pytest.approx(19.88)
    assert hour["wind_vector_magnitude_ms"] == 5
    assert hour["wind_direction_from_degrees"] is None
    assert hour["wind_direction_status"] == "basis_unverified"
    assert report["records"][0]["hours_after_retrieval"] == pytest.approx(1310 / 3600)
    assert report["source_reference_confirmed"] is False
    assert report["operational_use"] is False
    assert len(list(output.glob("*.csv"))) == 24
    assert output.stat().st_mode & 0o077 == 0
    for path in output.iterdir():
        assert path.stat().st_mode & 0o077 == 0
        assert KEY.encode() not in path.read_bytes()
    with pytest.raises(FileExistsError):
        run_probe(plan(), output, KEY)


@pytest.mark.parametrize("failure", ["403", "429", "grid", "missing", "secret", "oversized"])
def test_partial_failure_stops_and_missing_values_stay_null(tmp_path, failure):
    count = 0

    def fetch(spec, key):
        nonlocal count
        count += 1
        if count == 2:
            if failure in ("403", "429"):
                return {
                    "status": "rate_limited" if failure == "429" else "http_error",
                    "http_status": int(failure),
                }, None
            result, _ = successful_fetch(spec, key)
            payload = {
                "grid": body(spec, ix=717),
                "missing": body(spec, value=-9999),
                "secret": KEY.encode(),
                "oversized": b"1" * (MAX_BYTES + 1),
            }[failure]
            return result, payload
        return successful_fetch(spec, key)

    output = tmp_path / failure
    report = run_probe(plan(), output, KEY, fetcher=fetch, sleeper=lambda _: None, now=lambda: ASOF)
    assert count == 2
    assert report["complete"] is False and report["validated_requests"] == 1
    assert report["hours"][0]["values_by_requested_variable"]["U10"] == 3
    assert report["hours"][0]["values_by_requested_variable"]["V10"] is None
    assert report["hours"][0]["wind_vector_magnitude_ms"] is None
    assert report["hours"][0]["temperature_celsius"] is None
    assert all(not hour["complete"] for hour in report["hours"])
    assert KEY not in (output / "report.json").read_text()
    if failure in ("secret", "oversized"):
        assert len(list(output.glob("*.csv"))) == 1


def test_injected_plan_cannot_change_count_endpoint_or_horizon(tmp_path):
    changed = plan()
    changed["requests"][0]["endpoint"] = "https://example.invalid/"
    with pytest.raises(ValueError, match="bounded"):
        run_probe(changed, tmp_path / "bad", KEY)
    assert not (tmp_path / "bad").exists()
