"""Acquire seven explicit future Open-Meteo GFS knots for a research scenario.

This adapter does not invent a forecast issue time, combine KMA data, or infer
wind-axis semantics from numeric degrees. Verified external axis evidence is
required before one public API attempt. The CLI never retries or overwrites.
"""

import argparse
import hashlib
import json
import math
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

from bonghwa_training.public_forecast_probe import ENDPOINT, MAX_BYTES, MODEL, UNITS, write_new

SCHEMA = "elmfire_open_meteo_point_weather_v1"
SOURCE = "OpenMeteo_GFS"
START = datetime(2026, 10, 31, 18, tzinfo=UTC)
EXPECTED_TIMES = tuple(START + timedelta(hours=i) for i in range(7))
POINT = {"longitude": 129.3, "latitude": 37.0}
AXIS_FIELDS = {
    "wind_direction_basis": "true_north_clockwise_from",
    "wind_height_m": 10,
    "wind_speed_unit": "m/s",
    "wind_direction_unit": "degree",
}
BOUNDS = {
    "temperature_2m": (-100, 70),
    "relative_humidity_2m": (0, 100),
    "wind_speed_10m": (0, 100),
    "wind_direction_10m": (0, 360),
    "precipitation": (0, 1000),
}


def utc_time(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Evidence and receipt timestamps require an explicit timezone")
    return parsed.astimezone(UTC)


def checked_now(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("Clock must return a timezone-aware datetime")
    return value.astimezone(UTC)


def build_request(now):
    if checked_now(now) >= START:
        raise ValueError("The fixed first forecast knot must still be strictly after retrieval")
    return {
        "latitude": "37.0",
        "longitude": "129.3",
        "models": MODEL,
        "hourly": ",".join(UNITS),
        "temperature_unit": "celsius",
        "wind_speed_unit": "ms",
        "precipitation_unit": "mm",
        "timezone": "UTC",
        "timeformat": "iso8601",
        "start_hour": "2026-10-31T18:00",
        "end_hour": "2026-11-01T00:00",
        "cell_selection": "nearest",
    }


def validate_axis_evidence(path: Path, before: datetime):
    payload = path.read_bytes()
    if len(payload) > 2 * 1024 * 1024:
        raise ValueError("Axis evidence must be a small explicit JSON receipt")
    data = json.loads(payload)
    if not isinstance(data, dict) or data.get("verified") is not True:
        raise ValueError("Axis evidence must explicitly be verified")
    if any(data.get(key) != value for key, value in AXIS_FIELDS.items()):
        raise ValueError("Axis evidence does not establish the required wind semantics")
    if not isinstance(data.get("method"), str) or not data["method"].strip():
        raise ValueError("Axis evidence requires a verification method")
    if not isinstance(data.get("source_url"), str) or not data["source_url"].startswith("https://"):
        raise ValueError("Axis evidence requires its public HTTPS source URL")
    if not isinstance(data.get("limitations"), list) or not data["limitations"]:
        raise ValueError("Axis evidence must retain its limitations")
    retrieved = utc_time(data["retrieved_at_utc"])
    if retrieved > checked_now(before) or retrieved >= START:
        raise ValueError("Axis evidence must exist before retrieval and simulation start")
    return data, payload, hashlib.sha256(payload).hexdigest()


def validate_response(payload: bytes, retrieved_at: datetime):
    retrieved_at = checked_now(retrieved_at)
    if len(payload) > MAX_BYTES:
        raise ValueError("Response exceeds single-point size limit")
    data = json.loads(payload)
    if not isinstance(data, dict) or data.get("error"):
        raise ValueError("Provider returned an error or unexpected JSON")
    if data.get("utc_offset_seconds") != 0 or data.get("timezone") not in ("GMT", "UTC", "Etc/GMT"):
        raise ValueError("Provider response must explicitly identify UTC")
    units = data.get("hourly_units", {})
    if units.get("time") != "iso8601" or any(units.get(k) != v for k, v in UNITS.items()):
        raise ValueError("Provider units differ from requested m/s, degrees and auxiliary units")
    hourly = data.get("hourly", {})
    times = []
    for item in hourly.get("time", []):
        parsed = datetime.fromisoformat(item.replace("Z", "+00:00"))
        # This is allowed only after the response's explicit UTC metadata has been checked.
        times.append(
            parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
        )
    if tuple(times) != EXPECTED_TIMES or times[0] <= retrieved_at:
        raise ValueError("Exactly seven explicit future UTC knots t0 through t6 are required")
    if any(not isinstance(hourly.get(name), list) or len(hourly[name]) != 7 for name in UNITS):
        raise ValueError("Every requested variable requires exactly seven values")
    returned_point = {}
    for name, requested in POINT.items():
        value = data.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or abs(value - requested) > 0.5
        ):
            raise ValueError(
                "Returned GFS grid point is invalid or too far from the requested point"
            )
        returned_point[name] = value
    hours = []
    for i, valid in enumerate(times):
        values = {name: hourly[name][i] for name in UNITS}
        for name, value in values.items():
            low, high = BOUNDS[name]
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not low <= value <= high
            ):
                raise ValueError("Missing, nonnumeric or physically invalid forecast value")
        hours.append(
            {
                "valid_time_utc": valid.isoformat(),
                "wind_speed_m_s": values["wind_speed_10m"],
                "wind_direction_deg": values["wind_direction_10m"],
                "temperature_2m_c": values["temperature_2m"],
                "relative_humidity_2m_percent": values["relative_humidity_2m"],
                "precipitation_mm": values["precipitation"],
                "precipitation_interval_start_utc": (valid - timedelta(hours=1)).isoformat(),
                "forecast_issue_time_utc": None,
                "hours_after_retrieval": (valid - retrieved_at).total_seconds() / 3600,
                "observed": False,
            }
        )
    return {"hours": hours, "returned_grid_point": returned_point}


def json_bytes(data):
    return (json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def acquire(output: Path, axis_evidence: Path, *, opener=None, now=None):
    """One request; immutable raw response/receipt and a separate normalized contract."""
    now = now or (lambda: datetime.now(UTC))
    opener = opener or urllib.request.urlopen
    started = checked_now(now())
    params = build_request(started)
    evidence, evidence_payload, evidence_sha = validate_axis_evidence(axis_evidence, started)
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    write_new(output / "axis-evidence.json", evidence_payload)
    receipt = {
        "schema_version": "open_meteo_seven_hour_request_receipt_v1",
        "source": SOURCE,
        "source_url": url,
        "request_parameters": params,
        "request_started_at_utc": started.isoformat(),
        "max_http_attempts": 1,
        "forecast_issue_time_utc": None,
        "forecast_issue_time_known": False,
        "model_identity_basis": "explicit gfs_global request parameter, not a returned cycle ID",
        "operational_use": False,
        "fire_labels_requested": False,
        "kma_data_combined": False,
    }
    payload = None
    status = None
    headers = {}
    try:
        with opener(url, timeout=30) as response:
            status = int(response.status)
            response_headers = getattr(response, "headers", {})
            headers = {name: response_headers.get(name) for name in ("Date", "Content-Type")}
            payload = response.read(MAX_BYTES + 1)
        retrieved = checked_now(now())
        if retrieved < started:
            raise ValueError("Retrieval clock moved backwards")
        if status != 200:
            raise ValueError("Provider did not return HTTP 200")
        checked = validate_response(payload, retrieved)
        receipt["status"] = "validated_forecast_response"
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        retrieved = checked_now(now())
        receipt.update(status="rate_limited" if status == 429 else "http_error")
        exc.close()
    except Exception as exc:
        retrieved = checked_now(now())
        receipt.update(status="request_or_validation_failed", failure_type=type(exc).__name__)
    receipt.update(
        retrieved_at_utc=retrieved.isoformat(), http_status=status, response_headers=headers
    )
    if payload is not None:
        write_new(output / "response.json", payload)
        receipt.update(
            response_path="response.json",
            response_bytes=len(payload),
            response_sha256=hashlib.sha256(payload).hexdigest(),
        )
    receipt_payload = json_bytes(receipt)
    write_new(output / "receipt.json", receipt_payload)
    if receipt["status"] != "validated_forecast_response":
        return receipt
    provenance = [
        {
            "role": "open_meteo_response",
            "artifact_path": "response.json",
            "sha256": receipt["response_sha256"],
            "retrieved_at_utc": retrieved.isoformat(),
            "source_url": url,
        },
        {
            "role": "open_meteo_request_receipt",
            "artifact_path": "receipt.json",
            "sha256": hashlib.sha256(receipt_payload).hexdigest(),
            "retrieved_at_utc": retrieved.isoformat(),
            "source_url": url,
        },
        {
            "role": "axis_verification_evidence",
            "artifact_path": "axis-evidence.json",
            "sha256": evidence_sha,
            "retrieved_at_utc": evidence["retrieved_at_utc"],
            "source_url": evidence["source_url"],
        },
    ]
    normalized = {
        "schema_version": SCHEMA,
        "source": SOURCE,
        "status": "ready",
        "point": POINT,
        "simulation_start_time_utc": START.isoformat(),
        "retrieved_at_utc": retrieved.isoformat(),
        "forecast_issue_time_utc": None,
        "forecast_issue_time_known": False,
        "issue_time_note": "Open-Meteo response does not identify the underlying GFS issue cycle; "
        "retrieval time is not a forecast issue time",
        "wind_axis_basis_verified": True,
        **AXIS_FIELDS,
        "axis_verification": {
            "artifact_path": "axis-evidence.json",
            "sha256": evidence_sha,
            "method": evidence["method"],
        },
        "axis_verification_limitations": evidence["limitations"],
        "provenance": provenance,
        "requested_model": MODEL,
        "endpoint": ENDPOINT,
        **checked,
        "observed": False,
        "operational_use": False,
        "historical_issue_time_availability_proven": False,
        "fire_labels_requested": False,
        "holdout_2025_accessed": False,
        "kma_data_combined": False,
        "personal_risk_probability": None,
        "data_licence": "CC-BY-4.0",
        "licence_url": "https://open-meteo.com/en/licence",
        "attribution": "Weather data by Open-Meteo.com; underlying model NOAA GFS",
        "service_terms_url": "https://open-meteo.com/en/terms",
        "service_terms_note": "Free API is non-commercial; a paid plan is required commercially",
        "documentation_url": "https://open-meteo.com/en/docs/gfs-api",
        "limitations": [
            "Single GFS grid-point forecast is applied uniformly to the scenario domain",
            "Global forecast cannot resolve local terrain, mountain gusts or fire-induced winds",
            "2015 land cover or assumed fuels do not acquire current moisture from this API",
            "Seven t0..t6 hourly knots define a six-hour scenario, not seven hours of duration",
            "Provider wind-axis evidence does not prove the deployed server software revision",
            "Future retrieval checks do not establish a known underlying forecast issue cycle",
            "Weather input alone does not establish fire approach or personal harm probability",
        ],
    }
    write_new(output / "weather.json", json_bytes(normalized))
    return normalized


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--axis-evidence", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = acquire(args.output, args.axis_evidence)
    except Exception as exc:
        print(json.dumps({"status": "preflight_failed", "failure_type": type(exc).__name__}))
        return 1
    print(
        json.dumps(
            {
                "status": result["status"],
                "records": len(result.get("hours", [])),
                "forecast_issue_time_utc": None,
                "operational_use": False,
            }
        )
    )
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
