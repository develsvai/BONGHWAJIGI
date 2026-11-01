import hashlib
import json
import urllib.error
import urllib.parse
from datetime import UTC, datetime
from io import BytesIO

import pytest

from bonghwa_training.kma_forecast_probe import (
    MAX_BYTES,
    NoRedirect,
    build_plan,
    contains_sensitive,
    fetch_probe,
    inspect_payload,
    parse_issue,
    retry_after_seconds,
    run_probe,
)

KEY = "test-secret-not-a-real-key"


def plan():
    return build_plan(parse_issue("2026-10-31T06:00:00Z"), parse_issue("2022-03-04T00:00:00Z"))


class Response(BytesIO):
    status = 200
    headers = {}


def test_plan_limits_models_years_horizon_and_point():
    requests = plan()
    assert len(requests) == 12
    assert {x["model"] for x in requests} == {"KIML", "KIMR", "UMKR"}
    assert all(x["lead_hours"] == 1 and not x["observed"] for x in requests)
    assert requests[0]["parameters_without_auth"]["vars"] == "U10"
    assert requests[-1]["parameters_without_auth"]["varn"] == "1001"
    assert requests[-1]["documented_height_m"] is None
    assert requests[0]["requested_valid_time_utc"] == "2026-10-31T07:00:00+00:00"
    assert "2025" not in json.dumps(requests)
    with pytest.raises(ValueError, match="2025"):
        build_plan(parse_issue("2026-10-31T06:00:00Z"), parse_issue("2025-03-04T00:00:00Z"))
    with pytest.raises(ValueError, match="1, 3 or 6"):
        build_plan(parse_issue("2026-10-31T06:00:00Z"), parse_issue("2022-03-04T00:00:00Z"), lead=0)
    with pytest.raises(ValueError, match="Korean point"):
        build_plan(
            parse_issue("2026-10-31T06:00:00Z"),
            parse_issue("2022-03-04T00:00:00Z"),
            lat=float("nan"),
        )


@pytest.mark.parametrize(
    "value", ["2026-10-31T06:00:00", "2026-10-31T07:00:00Z", "2026-10-31T06:01:00Z"]
)
def test_issue_rejects_ambiguous_or_wrong_cycle(value):
    with pytest.raises(ValueError):
        parse_issue(value)


@pytest.mark.parametrize(
    "payload",
    [
        KEY.encode(),
        urllib.parse.quote(urllib.parse.quote(KEY, safe=""), safe="").encode(),
        ("".join(f"\\u{ord(c):04x}" for c in KEY)).encode(),
        b"https://example.test/?authKey=other-unknown-secret",
        b"https://example.test/?auth%254Bey=other-unknown-secret",
        b'{"serviceKey":"other-unknown-secret"}',
    ],
)
def test_echoed_credentials_and_auth_urls_are_never_safe(payload):
    assert contains_sensitive(payload, KEY)


def test_numeric_http_200_is_preserved_but_not_claimed_validated():
    body = b"# TMFC TMEF U10\n2026103106,2026103107,2.3\n"
    result, raw = fetch_probe(plan()[0], KEY, opener=lambda *a, **k: Response(body))
    assert result["status"] == "response_received"
    assert result["source_sha256"] == hashlib.sha256(body).hexdigest()
    assert result["reference_stamp_seen"] and result["valid_stamp_seen"]
    assert result["schema_verified"] is False
    assert raw == body
    assert KEY not in json.dumps(result)


@pytest.mark.parametrize(
    "body", [b"<html>403 denied</html>", b"ERROR 404 missing data", b"", b"# no data\n"]
)
def test_error_and_empty_bodies_never_saved_as_data(body):
    result, raw = fetch_probe(plan()[0], KEY, opener=lambda *a, **k: Response(body))
    assert result["schema_verified"] is False
    assert raw is None


def test_secret_response_rejected_without_hash_or_raw():
    result, raw = fetch_probe(plan()[0], KEY, opener=lambda *a, **k: Response(KEY.encode()))
    assert result["status"] == "sensitive_response_rejected"
    assert "source_sha256" not in result
    assert raw is None


def test_response_size_is_bounded():
    result, raw = fetch_probe(plan()[0], KEY, opener=lambda *a, **k: Response(b"1," * MAX_BYTES))
    assert result["status"] == "body_size_limit"
    assert raw is None


def test_429_retry_after_is_honored_not_missing():
    calls, delays = [], []

    def opener(request, **kwargs):
        calls.append(request)
        if len(calls) == 1:
            raise urllib.error.HTTPError(
                request.full_url, 429, KEY, {"Retry-After": "45"}, BytesIO(KEY.encode())
            )
        return Response(b"# U10\n1,2.3\n")

    result, _ = fetch_probe(plan()[0], KEY, opener=opener, sleeper=delays.append)
    assert delays == [45]
    assert result["status"] == "response_received"
    assert result["attempts"][0]["http_status"] == 429
    assert KEY not in json.dumps(result)


def test_long_429_stops_without_sleeping_or_treating_as_absence():
    def opener(request, **kwargs):
        raise urllib.error.HTTPError(request.full_url, 429, KEY, {"Retry-After": "600"}, None)

    delays = []
    result, _ = fetch_probe(plan()[0], KEY, opener=opener, sleeper=delays.append)
    assert result["status"] == "rate_limited"
    assert result["retry_after_seconds"] == 600
    assert not delays
    assert len(result["attempts"]) == 1


def test_retry_after_http_date_and_transport_sanitization():
    now = datetime(2026, 10, 31, 6, tzinfo=UTC)
    assert retry_after_seconds("Sat, 31 Oct 2026 06:00:50 GMT", now) == 50

    def opener(request, **kwargs):
        raise urllib.error.URLError(request.full_url + KEY)

    delays = []
    result, _ = fetch_probe(plan()[0], KEY, opener=opener, sleeper=delays.append)
    assert result["status"] == "transport_or_read_error"
    assert delays == [1, 2]
    assert KEY not in json.dumps(result)


def test_redirect_never_forwards_credentials():
    import urllib.request

    request = urllib.request.Request("https://apihub.kma.go.kr/api?authKey=" + KEY)
    with pytest.raises(urllib.error.HTTPError):
        NoRedirect().redirect_request(request, None, 302, "", {}, "https://other.test")


def test_output_private_immutable_and_rate_limited_stops_plan(tmp_path):
    calls = []

    def fake(spec, key):
        calls.append(spec)
        return {"status": "rate_limited", "http_status": 429}, None

    output = tmp_path / "probe"
    report = run_probe(plan(), output, KEY, fetcher=fake, sleeper=lambda _: None)
    assert len(calls) == 1
    assert report["holdout_2025_accessed"] is False
    assert report["stopped_early"] == "rate_limited"
    assert output.stat().st_mode & 0o077 == 0
    assert (output / "report.json").stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        run_probe(plan(), output, KEY, fetcher=fake)


def test_numeric_raw_persistence_has_provenance_and_no_auth(tmp_path):
    body = b"# TMFC TMEF U10\n2026103106,2026103107,2.3\n"

    def fake(spec, key):
        return {
            "status": "response_received",
            "source_sha256": hashlib.sha256(body).hexdigest(),
            **inspect_payload(body, spec),
        }, body

    output = tmp_path / "probe"
    report = run_probe(plan(), output, KEY, fetcher=fake, sleeper=lambda _: None)
    assert len(report["records"]) == 12
    assert len(list(output.glob("*.txt"))) == 12
    assert KEY not in (output / "report.json").read_text()
    assert "authKey" not in (output / "report.json").read_text()


def test_persistence_boundary_rejects_secret_even_from_injected_fetcher(tmp_path):
    def fake(spec, key):
        return {"status": "response_received"}, KEY.encode()

    output = tmp_path / "probe"
    with pytest.raises(ValueError, match="sensitive"):
        run_probe(plan(), output, KEY, fetcher=fake)
    assert not list(output.iterdir())
