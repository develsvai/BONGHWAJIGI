"""One keyless Open-Meteo GFS request for non-commercial research adapter checks.

This collects future weather, never observed weather or wildfire truth. API service
terms and data licence are distinct. No operational/personal-risk interpretation.
"""

import argparse
import hashlib
import json
import math
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

ENDPOINT = "https://api.open-meteo.com/v1/gfs"
MODEL = "gfs_global"
MAX_BYTES = 128 * 1024
UNITS = {
    "temperature_2m": "°C",
    "relative_humidity_2m": "%",
    "wind_speed_10m": "m/s",
    "wind_direction_10m": "°",
    "precipitation": "mm",
}


def build_request(now, *, latitude=37.0, longitude=129.3):
    if now.tzinfo is None:
        raise ValueError("timezone is required")
    if not (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and 33 <= latitude <= 39
        and 124 <= longitude <= 132
    ):
        raise ValueError("one Korean sample location is required")
    start = now.astimezone(UTC).replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    end = start + timedelta(hours=5)
    if start.year == 2025 or end.year == 2025:
        raise ValueError("2025 holdout period remains locked")
    return {
        "latitude": str(latitude),
        "longitude": str(longitude),
        "models": MODEL,
        "hourly": ",".join(UNITS),
        "temperature_unit": "celsius",
        "wind_speed_unit": "ms",
        "precipitation_unit": "mm",
        "timezone": "UTC",
        "timeformat": "iso8601",
        "start_hour": start.strftime("%Y-%m-%dT%H:%M"),
        "end_hour": end.strftime("%Y-%m-%dT%H:%M"),
        "cell_selection": "nearest",
    }


def parse_hour(value):
    parsed = datetime.fromisoformat(value)
    # Provider documents timezone=UTC timestamps without suffix; never assume local time.
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def validate_response(payload, params, retrieved_at):
    if len(payload) > MAX_BYTES:
        raise ValueError("response exceeds single-point size limit")
    data = json.loads(payload)
    if not isinstance(data, dict) or data.get("error"):
        raise ValueError("provider returned error or unexpected response")
    if data.get("utc_offset_seconds") != 0 or data.get("timezone") not in ("GMT", "UTC", "Etc/GMT"):
        raise ValueError("response must explicitly identify UTC")
    units = data.get("hourly_units", {})
    if units.get("time") != "iso8601" or any(units.get(k) != v for k, v in UNITS.items()):
        raise ValueError("weather units do not match the request")
    hourly = data.get("hourly", {})
    start = parse_hour(params["start_hour"])
    expected = [start + timedelta(hours=i) for i in range(6)]
    times = [parse_hour(t) for t in hourly.get("time", [])]
    if times != expected or any(t <= retrieved_at for t in times):
        raise ValueError("exactly six ordered future UTC hours are required")
    if any(not isinstance(hourly.get(k), list) or len(hourly[k]) != 6 for k in UNITS):
        raise ValueError("all five hourly variables need six values")
    for coordinate, limit in (("latitude", 1.0), ("longitude", 1.0)):
        value = data.get(coordinate)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError("response grid coordinates must be finite")
        if abs(value - float(params[coordinate])) > limit:
            raise ValueError("response grid point differs unexpectedly from requested location")
    records = []
    bounds = {
        "relative_humidity_2m": (0, 100),
        "wind_direction_10m": (0, 360),
        "wind_speed_10m": (0, 150),
        "precipitation": (0, 1000),
        "temperature_2m": (-100, 70),
    }
    for i, valid in enumerate(times):
        values = {name: hourly[name][i] for name in UNITS}
        missing = []
        for name, value in values.items():
            if value is None:
                missing.append(name)
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("weather fields must be numbers or explicit null")
            low, high = bounds[name]
            if not math.isfinite(value) or not low <= value <= high:
                raise ValueError("weather field failed physical sanity check")
        records.append(
            {
                "valid_time_utc": valid.isoformat(),
                "hours_after_retrieval": (valid - retrieved_at).total_seconds() / 3600,
                "forecast_reference_time_utc": None,
                "observed": False,
                "values": values,
                "missing_variables": missing,
                "usable_for_adapter_check": not missing,
                "precipitation_interval_start_utc": (valid - timedelta(hours=1)).isoformat(),
            }
        )
    return {
        "returned_grid_latitude": data["latitude"],
        "returned_grid_longitude": data["longitude"],
        "units": UNITS,
        "records": records,
        "all_values_present": all(not record["missing_variables"] for record in records),
    }


def write_new(path, payload):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as target:
        target.write(payload)


def acquire(output, *, latitude=37.0, longitude=129.3, opener=None, now=None):
    """Exactly one HTTP attempt, no automatic retries or historical API requests."""
    now = now or (lambda: datetime.now(UTC))
    opener = opener or urllib.request.urlopen
    started = now()
    params = build_request(started, latitude=latitude, longitude=longitude)
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    report = {
        "schema_version": 1,
        "purpose": "non_commercial_research_adapter_smoke_test",
        "source_kind": "numerical_weather_forecast",
        "provider": "Open-Meteo / NOAA GFS",
        "requested_model": MODEL,
        "model_identity_basis": "explicit request parameter",
        "forecast_reference_time_utc": None,
        "issue_time_note": "provider response does not identify the underlying forecast cycle",
        "request_started_at_utc": started.isoformat(),
        "request_parameters": params,
        "source_url": url,
        "max_http_attempts": 1,
        "observed": False,
        "fire_labels_requested": False,
        "holdout_2025_accessed": False,
        "historical_input_availability_proven": False,
        "operational_use": False,
        "personal_risk_probability": False,
        "data_licence": "CC-BY-4.0",
        "licence_url": "https://open-meteo.com/en/licence",
        "attribution": "Weather data by Open-Meteo.com; underlying model NOAA GFS",
        "service_terms_url": "https://open-meteo.com/en/terms",
        "service_terms_note": "Free API is non-commercial; commercial service needs a paid plan",
        "documentation_url": "https://open-meteo.com/en/docs/gfs-api",
        "limits": [
            "Current retrieval is not evidence of historical issue-time availability",
            "GFS global grid cannot resolve local mountain/fire winds",
            "Nearest returned grid point is retained; requested point is not a local sensor",
            "Precipitation is forecast accumulation for the preceding hour, not an observation",
            "This is weather input connectivity, not verified fire approach or smoke risk",
        ],
    }
    payload = None
    try:
        with opener(url, timeout=30) as response:
            if response.status != 200:
                raise urllib.error.HTTPError(url, response.status, "", {}, None)
            payload = response.read(MAX_BYTES + 1)
        retrieved = now()
        report["retrieved_at_utc"] = retrieved.isoformat()
        checked = validate_response(payload, params, retrieved)
        report.update(checked)
        report.update(
            status="validated_forecast_response",
            bytes=len(payload),
            source_sha256=hashlib.sha256(payload).hexdigest(),
        )
        write_new(output / "response.json", payload)
    except urllib.error.HTTPError as exc:
        report.update(
            status="rate_limited" if exc.code == 429 else "http_error",
            http_status=int(exc.code),
            retrieved_at_utc=now().isoformat(),
        )
        exc.close()
    except Exception:
        report.update(status="request_or_validation_failed", retrieved_at_utc=now().isoformat())
        if payload is not None:
            report["rejected_response_bytes"] = len(payload)
    write_new(
        output / "report.json", (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode()
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--latitude", type=float, default=37.0)
    parser.add_argument("--longitude", type=float, default=129.3)
    args = parser.parse_args()
    try:
        report = acquire(args.output, latitude=args.latitude, longitude=args.longitude)
    except Exception:
        print(json.dumps({"status": "probe_failed"}))
        return 1
    print(
        json.dumps(
            {
                "status": report["status"],
                "records": len(report.get("records", [])),
                "forecast_reference_time_utc": None,
                "operational_use": False,
            }
        )
    )
    return 0 if report["status"] == "validated_forecast_response" else 1


if __name__ == "__main__":
    raise SystemExit(main())
