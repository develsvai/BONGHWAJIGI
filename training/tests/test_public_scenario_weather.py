import hashlib
import json
import urllib.error
from datetime import UTC, datetime, timedelta
from io import BytesIO
from urllib.parse import parse_qs, urlparse

import pytest

from bonghwa_training.public_scenario_weather import (
    AXIS_FIELDS,
    EXPECTED_TIMES,
    MAX_BYTES,
    SCHEMA,
    SOURCE,
    START,
    UNITS,
    acquire,
    build_request,
    validate_axis_evidence,
    validate_response,
)

NOW = datetime(2026, 10, 31, 17, tzinfo=UTC)


def provider_response():
    return {
        "latitude": 37.0,
        "longitude": 129.25,
        "utc_offset_seconds": 0,
        "timezone": "GMT",
        "hourly_units": {"time": "iso8601", **UNITS},
        "hourly": {
            "time": [x.strftime("%Y-%m-%dT%H:%M") for x in EXPECTED_TIMES],
            "wind_speed_10m": [0, 1, 2, 3, 4, 5, 6],
            "wind_direction_10m": [0, 30, 60, 90, 180, 270, 360],
            "temperature_2m": [10] * 7,
            "relative_humidity_2m": [50] * 7,
            "precipitation": [0] * 7,
        },
    }


def evidence_file(tmp_path, **changes):
    data = {
        "verified": True,
        "method": "pinned official provider source and documented 10m wind",
        "retrieved_at_utc": (NOW - timedelta(minutes=10)).isoformat(),
        "source_url": "https://example.org/provider/source/commit",
        **AXIS_FIELDS,
        "limitations": ["Public source inspection does not prove deployed server version"],
        "sources": [{"url": "https://example.org/docs", "sha256": "a" * 64}],
    }
    data.update(changes)
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(data))
    return path


class HTTPResponse(BytesIO):
    status = 200
    headers = {"Content-Type": "application/json"}


def test_explicit_seven_knots_and_model_are_fixed():
    params = build_request(NOW)
    assert params["models"] == "gfs_global"
    assert params["start_hour"] == "2026-10-31T18:00"
    assert params["end_hour"] == "2026-11-01T00:00"
    assert params["latitude"] == "37.0" and params["longitude"] == "129.3"
    assert params["wind_speed_unit"] == "ms" and params["timezone"] == "UTC"
    assert not {"apikey", "past_days", "past_hours", "current"} & params.keys()


@pytest.mark.parametrize("now", [START, START + timedelta(minutes=1)])
def test_late_request_rejected_before_http(now):
    with pytest.raises(ValueError, match="strictly after"):
        build_request(now)


def test_clock_requires_timezone():
    with pytest.raises(ValueError, match="timezone"):
        build_request(datetime(2026, 10, 31, 17))


def test_correct_response_preserves_exact_values_and_unknown_issue():
    data = provider_response()
    result = validate_response(json.dumps(data).encode(), NOW)
    assert len(result["hours"]) == 7
    assert result["returned_grid_point"]["longitude"] == 129.25
    for index, hour in enumerate(result["hours"]):
        assert hour["wind_speed_m_s"] == data["hourly"]["wind_speed_10m"][index]
        assert hour["wind_direction_deg"] == data["hourly"]["wind_direction_10m"][index]
        assert hour["forecast_issue_time_utc"] is None and hour["observed"] is False
        assert hour["hours_after_retrieval"] > 0
    assert result["hours"][0]["precipitation_interval_start_utc"] == NOW.isoformat()


@pytest.mark.parametrize(
    "change", ["six", "duplicate", "unordered", "wrong_start", "late_retrieval"]
)
def test_no_missing_unordered_wrong_or_already_started_horizon(change):
    data = provider_response()
    retrieved = NOW
    if change == "six":
        data["hourly"]["time"].pop()
    elif change == "duplicate":
        data["hourly"]["time"][1] = data["hourly"]["time"][0]
    elif change == "unordered":
        data["hourly"]["time"].reverse()
    elif change == "wrong_start":
        data["hourly"]["time"][0] = "2026-10-31T17:00"
    else:
        retrieved = START
    with pytest.raises(ValueError, match="seven explicit future"):
        validate_response(json.dumps(data).encode(), retrieved)


@pytest.mark.parametrize(
    "name,value",
    [
        ("wind_speed_10m", None),
        ("wind_speed_10m", -1),
        ("wind_speed_10m", 101),
        ("wind_direction_10m", 361),
        ("relative_humidity_2m", 101),
        ("temperature_2m", float("nan")),
        ("precipitation", True),
    ],
)
def test_missing_or_nonphysical_values_never_become_zero(name, value):
    data = provider_response()
    data["hourly"][name][3] = value
    with pytest.raises(ValueError, match="forecast value"):
        validate_response(json.dumps(data).encode(), NOW)


def test_units_utc_and_grid_location_are_required():
    data = provider_response()
    data["hourly_units"]["wind_speed_10m"] = "km/h"
    with pytest.raises(ValueError, match="units"):
        validate_response(json.dumps(data).encode(), NOW)
    data = provider_response()
    data["utc_offset_seconds"] = 32400
    with pytest.raises(ValueError, match="UTC"):
        validate_response(json.dumps(data).encode(), NOW)
    data = provider_response()
    data["latitude"] = 40
    with pytest.raises(ValueError, match="grid point"):
        validate_response(json.dumps(data).encode(), NOW)


@pytest.mark.parametrize(
    "change",
    [
        {"verified": False},
        {"wind_direction_basis": "grid_north_clockwise_from"},
        {"method": ""},
        {"wind_height_m": 20},
        {"limitations": []},
        {"retrieved_at_utc": START.isoformat()},
    ],
)
def test_unverified_or_incompatible_axis_evidence_blocks_request(tmp_path, change):
    path = evidence_file(tmp_path, **change)
    calls = []
    with pytest.raises(ValueError):
        acquire(tmp_path / "out", path, opener=lambda *a, **k: calls.append(a), now=lambda: NOW)
    assert not calls and not (tmp_path / "out").exists()


def test_axis_evidence_hash_links_exact_bytes(tmp_path):
    path = evidence_file(tmp_path)
    _, payload, digest = validate_axis_evidence(path, NOW)
    assert payload == path.read_bytes() and digest == hashlib.sha256(payload).hexdigest()


def test_success_persists_immutable_raw_receipt_evidence_and_normalized_contract(tmp_path):
    path = evidence_file(tmp_path)
    payload = json.dumps(provider_response()).encode()
    calls = []

    def opener(url, **kwargs):
        calls.append(url)
        return HTTPResponse(payload)

    output = tmp_path / "out"
    report = acquire(output, path, opener=opener, now=lambda: NOW)
    assert len(calls) == 1
    assert urlparse(calls[0]).path == "/v1/gfs"
    assert parse_qs(urlparse(calls[0]).query)["models"] == ["gfs_global"]
    assert report["schema_version"] == SCHEMA and report["source"] == SOURCE
    assert report["status"] == "ready" and report["wind_axis_basis_verified"] is True
    assert report["forecast_issue_time_utc"] is None
    assert report["forecast_issue_time_known"] is False
    assert report["issue_time_note"]
    assert report["personal_risk_probability"] is None
    assert not report["kma_data_combined"] and not report["operational_use"]
    assert (output / "response.json").read_bytes() == payload
    assert (output / "axis-evidence.json").read_bytes() == path.read_bytes()
    assert json.loads((output / "weather.json").read_text()) == report
    assert {r["role"] for r in report["provenance"]} == {
        "open_meteo_response",
        "open_meteo_request_receipt",
        "axis_verification_evidence",
    }
    for record in report["provenance"]:
        artifact = output / record["artifact_path"]
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == record["sha256"]
        assert artifact.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        acquire(output, path, opener=opener, now=lambda: NOW)
    assert len(calls) == 1


def test_request_crossing_start_preserves_rejected_raw_but_no_weather(tmp_path):
    moments = iter([NOW, START, START])
    output = tmp_path / "out"
    report = acquire(
        output,
        evidence_file(tmp_path),
        opener=lambda *a, **k: HTTPResponse(json.dumps(provider_response()).encode()),
        now=lambda: next(moments),
    )
    assert report["status"] == "request_or_validation_failed"
    assert (output / "response.json").exists() and (output / "receipt.json").exists()
    assert not (output / "weather.json").exists()


def test_429_is_not_retried_or_normalized(tmp_path):
    calls = []

    def opener(url, **kwargs):
        calls.append(url)
        raise urllib.error.HTTPError(url, 429, "quota", {}, None)

    output = tmp_path / "out"
    report = acquire(output, evidence_file(tmp_path), opener=opener, now=lambda: NOW)
    assert len(calls) == 1 and report["status"] == "rate_limited"
    assert (output / "receipt.json").exists() and not (output / "weather.json").exists()


def test_oversized_response_is_rejected():
    with pytest.raises(ValueError, match="size limit"):
        validate_response(b" " * (MAX_BYTES + 1), NOW)
