import json
import urllib.error
from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest

from bonghwa_training.public_forecast_probe import (
    MAX_BYTES,
    UNITS,
    acquire,
    build_request,
    validate_response,
)

NOW = datetime(2026, 10, 31, 16, 20, tzinfo=UTC)


def response():
    start = NOW.replace(minute=0) + timedelta(hours=1)
    return {
        "latitude": 37.0,
        "longitude": 129.3,
        "utc_offset_seconds": 0,
        "timezone": "GMT",
        "hourly_units": {"time": "iso8601", **UNITS},
        "hourly": {
            "time": [(start + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(6)],
            "temperature_2m": [10.0] * 6,
            "relative_humidity_2m": [40] * 6,
            "wind_speed_10m": [2.0] * 6,
            "wind_direction_10m": [270] * 6,
            "precipitation": [0.0] * 6,
        },
    }


def validate(data):
    return validate_response(json.dumps(data).encode(), build_request(NOW), NOW)


def test_request_is_explicit_global_gfs_future_utc_and_ms():
    params = build_request(NOW)
    assert params["models"] == "gfs_global"
    assert params["wind_speed_unit"] == "ms"
    assert params["timezone"] == "UTC"
    assert params["start_hour"] == "2026-10-31T17:00"
    assert params["end_hour"] == "2026-10-31T22:00"
    assert not ({"apikey", "current", "past_days", "past_hours"} & params.keys())


def test_2025_is_locked_even_if_clock_is_injected():
    with pytest.raises(ValueError, match="2025"):
        build_request(datetime(2025, 3, 22, tzinfo=UTC))


def test_validated_weather_is_not_observed_or_given_an_invented_issue_time():
    result = validate(response())
    assert len(result["records"]) == 6
    for record in result["records"]:
        assert not record["observed"]
        assert record["forecast_reference_time_utc"] is None
        assert record["hours_after_retrieval"] > 0
    assert result["records"][0]["precipitation_interval_start_utc"] == "2026-10-31T16:00:00+00:00"


@pytest.mark.parametrize("unit", ["km/h", "mph", "kn"])
def test_wrong_wind_units_rejected(unit):
    data = response()
    data["hourly_units"]["wind_speed_10m"] = unit
    with pytest.raises(ValueError, match="units"):
        validate(data)


@pytest.mark.parametrize("change", ["duplicate", "past", "missing", "unordered"])
def test_invalid_valid_times_rejected(change):
    data = response()
    if change == "duplicate":
        data["hourly"]["time"][1] = data["hourly"]["time"][0]
    elif change == "past":
        data["hourly"]["time"][0] = "2026-10-31T16:00"
    elif change == "missing":
        data["hourly"]["time"].pop()
    else:
        data["hourly"]["time"].reverse()
    with pytest.raises(ValueError, match="future UTC"):
        validate(data)


def test_null_weather_remains_missing_never_zero():
    data = response()
    data["hourly"]["wind_speed_10m"][2] = None
    result = validate(data)
    assert result["records"][2]["values"]["wind_speed_10m"] is None
    assert not result["records"][2]["usable_for_adapter_check"]
    assert not result["all_values_present"]


@pytest.mark.parametrize(
    "variable,value",
    [
        ("relative_humidity_2m", 101),
        ("wind_speed_10m", -1),
        ("temperature_2m", float("nan")),
        ("precipitation", True),
    ],
)
def test_nonphysical_and_non_numeric_weather_rejected(variable, value):
    data = response()
    data["hourly"][variable][0] = value
    with pytest.raises(ValueError):
        validate(data)


def test_utc_and_location_are_checked():
    data = response()
    data["utc_offset_seconds"] = 32400
    with pytest.raises(ValueError, match="UTC"):
        validate(data)
    data = response()
    data["latitude"] = 52.0
    with pytest.raises(ValueError, match="grid point"):
        validate(data)


def test_success_one_request_provenance_private_raw_and_immutable(tmp_path):
    class HTTPResponse(BytesIO):
        status = 200

    calls = []

    def opener(url, **kwargs):
        calls.append(url)
        return HTTPResponse(json.dumps(response()).encode())

    output = tmp_path / "forecast"
    report = acquire(output, opener=opener, now=lambda: NOW)
    assert len(calls) == 1
    assert report["status"] == "validated_forecast_response"
    assert report["data_licence"] == "CC-BY-4.0"
    assert not report["operational_use"]
    assert not report["historical_input_availability_proven"]
    assert (output / "response.json").stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        acquire(output, opener=opener, now=lambda: NOW)
    assert len(calls) == 1


def test_429_recorded_once_and_never_missing_or_retried(tmp_path):
    calls = []

    def opener(url, **kwargs):
        calls.append(url)
        raise urllib.error.HTTPError(url, 429, "quota", {"Retry-After": "600"}, None)

    report = acquire(tmp_path / "forecast", opener=opener, now=lambda: NOW)
    assert report["status"] == "rate_limited"
    assert len(calls) == 1
    assert not (tmp_path / "forecast/response.json").exists()


def test_huge_payload_rejected():
    with pytest.raises(ValueError, match="size limit"):
        validate_response(b" " * (MAX_BYTES + 1), build_request(NOW), NOW)
