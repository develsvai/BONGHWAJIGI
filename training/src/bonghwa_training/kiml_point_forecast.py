"""Bounded KIML point-weather research acquisition; never an operational risk model.

Exactly six future clock hours and four variables, at most one HTTP attempt each.
CSV does not echo its variable, unit or run time: requested metadata stays distinct
from source-confirmed metadata. Wind-axis rotation is not yet verified.
"""

import argparse
import csv
import hashlib
import io
import json
import math
import os
import struct
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

from bonghwa_training.kma_forecast_probe import (
    DOCUMENTATION,
    KIM_ENDPOINT,
    MAX_BYTES,
    NoRedirect,
    contains_sensitive,
    fetch_probe,
    iso,
    parse_issue,
    retry_after_seconds,
    write_private,
)

CSV_COLUMNS = ("req_lon", "req_lat", "lvl", "ix", "iy", "lon", "lat", "value")
VARIABLES = {
    "U10": {"unit": "m/s", "height_m": 10, "range": (-150, 150)},
    "V10": {"unit": "m/s", "height_m": 10, "range": (-150, 150)},
    "T2": {"unit": "K", "height_m": 2, "range": (180, 340)},
    "RH2": {"unit": "%", "height_m": 2, "range": (0, 100)},
}
EARLIEST_CYCLE = datetime(2026, 2, 9, tzinfo=UTC)
VARIABLE_DOCUMENTATION = "https://apihub.kma.go.kr/getAttachFile.do?fileName=" + urllib.parse.quote(
    "한국형 수치모델(KIM) 변수정보.pdf"
)


def as_utc(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("timezone-aware datetime required")
    return value.astimezone(UTC)


def build_plan(issue, asof, *, lon=129.3, lat=37.0):
    """Freeze 24 requests before network access; only KIML point forecasts."""
    issue, asof = as_utc(issue), as_utc(asof)
    parse_issue(iso(issue))
    if not EARLIEST_CYCLE <= issue <= asof:
        raise ValueError("cycle must be available-era KIML and no later than acquisition asof")
    if not (math.isfinite(lon) and math.isfinite(lat) and 124 <= lon <= 132 and 33 <= lat <= 39):
        raise ValueError("one Korean point required")
    # The endpoint echoes request coordinates with six decimals.
    lon, lat = round(lon, 6), round(lat, 6)
    start = asof.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    specs = []
    for offset in range(6):
        valid = start + timedelta(hours=offset)
        hf = int((valid - issue).total_seconds() / 3600)
        if not 1 <= hf <= 48:
            raise ValueError("all six forecast times must be within cycle +1..48 hours")
        for variable, definition in VARIABLES.items():
            specs.append(
                {
                    "id": f"kiml-{issue:%Y%m%dT%HZ}-{variable.lower()}-h{hf}",
                    "endpoint": KIM_ENDPOINT,
                    "parameters_without_auth": {
                        "group": "KIML",
                        "data": "U",
                        "vars": variable,
                        "tmfc": issue.strftime("%Y%m%d%H"),
                        "hf": str(hf),
                        "lon": f"{lon:.6f}",
                        "lat": f"{lat:.6f}",
                        "dataType": "CSV",
                    },
                    # fetch_probe uses these fields only for diagnostic stamp matching.
                    "forecast_reference_time_utc": iso(issue),
                    "reference_time_basis": "requested_parameter_only",
                    "requested_valid_time_utc": iso(valid),
                    "requested_lead_from_cycle_hours": hf,
                    "requested_lead_from_asof_hours": (valid - asof).total_seconds() / 3600,
                    "requested_variable": variable,
                    "documented_unit": definition["unit"],
                    "documented_height_m": definition["height_m"],
                    "unit_and_height_documentation": VARIABLE_DOCUMENTATION,
                    "source_kind": "numerical_weather_forecast",
                    "observed": False,
                }
            )
    return {
        "schema_version": 1,
        "purpose": "kiml_point_forecast_research_adapter_check",
        "asof_utc": iso(asof),
        "requested_reference_time_utc": iso(issue),
        "requested_longitude": lon,
        "requested_latitude": lat,
        "max_http_attempts": 24,
        "request_spacing_seconds": 1,
        "operational_use": False,
        "fire_labels_requested": False,
        "holdout_2025_accessed": False,
        "documentation": DOCUMENTATION,
        "requests": specs,
    }


class _RetryBlocked(Exception):
    """Private flow control: no request URL or response message is retained."""


def fetch_once(spec, key, *, opener=None, now=None):
    """Reuse the safe existing fetcher, stopping before any automatic retry."""
    now = now or (lambda: datetime.now(UTC))
    opener = opener or urllib.request.build_opener(NoRedirect()).open
    started = iso(now())
    failure = {}

    def open_once(request, **kwargs):
        try:
            response = opener(request, **kwargs)
            if response.status >= 400:
                failure["http_status"] = int(response.status)
                if response.status == 429:
                    failure["retry_after_seconds"] = retry_after_seconds(
                        (response.headers or {}).get("Retry-After"), now()
                    )
            return response
        except urllib.error.HTTPError as exc:
            failure["http_status"] = int(exc.code)
            if exc.code == 429:
                failure["retry_after_seconds"] = retry_after_seconds(
                    (exc.headers or {}).get("Retry-After"), now()
                )
            raise

    def stop_retry(_delay):
        raise _RetryBlocked

    try:
        return fetch_probe(spec, key, opener=open_once, sleeper=stop_retry, now=now)
    except _RetryBlocked:
        status = failure.get("http_status")
        result = {
            "status": "rate_limited"
            if status == 429
            else "http_error"
            if status is not None
            else "transport_or_read_error",
            "attempts": [{"attempt": 1, "started_at_utc": started, **failure}],
            **failure,
        }
        return result, None


def parse_point_csv(payload, spec):
    """Validate the observed eight-column schema, without inventing echoed metadata."""
    try:
        rows = list(csv.reader(io.StringIO(payload.decode("utf-8")), strict=True))
    except (UnicodeError, csv.Error):
        raise ValueError("invalid CSV encoding or syntax") from None
    if len(rows) != 2 or tuple(rows[0]) != CSV_COLUMNS or len(rows[1]) != 8:
        raise ValueError("exact eight-column header and one data row required")
    try:
        numbers = [float(value) for value in rows[1]]
    except (ValueError, OverflowError):
        raise ValueError("all eight CSV fields must be finite numeric values") from None
    if not all(math.isfinite(value) for value in numbers):
        raise ValueError("nonfinite or missing CSV field")
    row = dict(zip(CSV_COLUMNS, numbers, strict=True))
    params = spec["parameters_without_auth"]
    echo_precision = {}
    for name in ("req_lon", "req_lat"):
        requested = float(params[name[4:]])
        requested_float32 = struct.unpack("!f", struct.pack("!f", requested))[0]
        # The API can print a float32 request echo to six decimals. Check two
        # precise representations, not an enlarged interval between them.
        if abs(row[name] - requested) <= 0.00000051:
            echo_precision[name] = "requested_float64_six_decimal_echo"
        elif abs(row[name] - requested_float32) <= 0.00000051:
            echo_precision[name] = "requested_float32_six_decimal_echo"
        else:
            raise ValueError("request coordinates do not match echoed coordinates")
    if row["lvl"] != -1:
        raise ValueError("unrecognized level marker")
    if any(not row[name].is_integer() or not 0 <= row[name] <= 100000 for name in ("ix", "iy")):
        raise ValueError("invalid grid indices")
    if not (124 <= row["lon"] <= 132 and 33 <= row["lat"] <= 39):
        raise ValueError("grid coordinates outside the Korean point probe bounds")
    if abs(row["lon"] - row["req_lon"]) > 0.05 or abs(row["lat"] - row["req_lat"]) > 0.05:
        raise ValueError("grid point unexpectedly far from requested coordinates")
    variable = spec["requested_variable"]
    low, high = VARIABLES[variable]["range"]
    if not low <= row["value"] <= high:
        raise ValueError("value outside documented-variable sanity bounds")
    return {
        "value": row["value"],
        "request_coordinate_echo": {name: row[name] for name in ("req_lon", "req_lat")},
        "request_coordinate_echo_precision": echo_precision,
        "grid": {"ix": int(row["ix"]), "iy": int(row["iy"]), "lon": row["lon"], "lat": row["lat"]},
        "level_marker": -1,
        "level_marker_semantics": "response marker, not verified physical height",
        "csv_schema_verified": True,
        "source_reference_time_utc": None,
        "source_valid_time_utc": None,
        "source_reference_confirmed": False,
        "source_valid_time_confirmed": False,
        "source_variable_confirmed": False,
        "source_unit_confirmed": False,
        "source_height_confirmed": False,
        "interpretation_basis": "requested variable and official variable definitions only",
    }


def assemble_hours(plan, records):
    """Keep missing variables null; derive only complete variable pairs."""
    hours = []
    for offset in range(6):
        expected = plan["requests"][offset * 4 : (offset + 1) * 4]
        identifiers = {request["id"] for request in expected}
        found = {
            record["requested_variable"]: record
            for record in records
            if record["id"] in identifiers
        }
        values = {
            name: found[name]["parsed"]["value"]
            if name in found and found[name]["status"] == "validated_point_csv"
            else None
            for name in VARIABLES
        }
        u, v, kelvin = values["U10"], values["V10"], values["T2"]
        missing = [name for name, value in values.items() if value is None]
        hours.append(
            {
                "requested_valid_time_utc": expected[0]["requested_valid_time_utc"],
                "requested_lead_from_cycle_hours": expected[0]["requested_lead_from_cycle_hours"],
                "requested_lead_from_asof_hours": expected[0]["requested_lead_from_asof_hours"],
                "values_by_requested_variable": values,
                "temperature_celsius": kelvin - 273.15 if kelvin is not None else None,
                "wind_vector_magnitude_ms": math.hypot(u, v)
                if u is not None and v is not None
                else None,
                "wind_direction_from_degrees": None,
                "wind_direction_status": "basis_unverified",
                "wind_axis_basis_verified": False,
                "missing_variables": missing,
                "complete": not missing,
                "source_time_variable_unit_confirmed": False,
                "observed": False,
                "operational_use": False,
            }
        )
    return hours


def _write_json(path, value, key):
    payload = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    if contains_sensitive(payload, key):
        raise ValueError("sensitive metadata rejected")
    write_private(path, payload)


def run_probe(plan, output, key, *, fetcher=fetch_once, sleeper=time.sleep, now=None):
    if not key or len(key) < 8 or any(character.isspace() for character in key):
        raise ValueError("valid private environment credential required")
    # Restrict execution to the exact safe builder, including endpoint and count.
    expected = build_plan(
        datetime.fromisoformat(plan["requested_reference_time_utc"]),
        datetime.fromisoformat(plan["asof_utc"]),
        lon=plan["requested_longitude"],
        lat=plan["requested_latitude"],
    )
    if plan != expected:
        raise ValueError("plan differs from bounded KIML point request contract")
    now = now or (lambda: datetime.now(UTC))
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    _write_json(output / "plan.json", plan, key)
    report = {
        "schema_version": 1,
        "purpose": plan["purpose"],
        "source_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "unit_and_height_documentation": VARIABLE_DOCUMENTATION,
        "plan_sha256": hashlib.sha256((output / "plan.json").read_bytes()).hexdigest(),
        "asof_utc": plan["asof_utc"],
        "requested_reference_time_utc": plan["requested_reference_time_utc"],
        "source_reference_time_utc": None,
        "source_reference_confirmed": False,
        "observed": False,
        "operational_use": False,
        "personal_risk_probability": False,
        "historical_input_availability_proven": False,
        "fire_labels_requested": False,
        "holdout_2025_accessed": False,
        "planned_requests": 24,
        "max_http_attempts": 24,
        "records": [],
        "stopped_early": None,
        "limitations": [
            "CSV does not echo run, valid time, variable, unit or physical height",
            "Official variable definitions interpret requested values, not response confirmation",
            "Wind coordinate-axis rotation is unverified; no geographic bearing is derived",
            "Current forecast retrieval does not prove historical issue-time availability",
            "Weather input research only; not a fire forecast or personal response decision",
        ],
    }
    grid = None
    for index, spec in enumerate(plan["requests"]):
        if index:
            sleeper(1)
        try:
            result, payload = fetcher(spec, key)
            encoded_result = json.dumps(result, allow_nan=False).encode()
            if contains_sensitive(encoded_result, key) or (
                payload is not None and contains_sensitive(payload, key)
            ):
                result, payload = {"status": "sensitive_response_rejected"}, None
            elif payload is not None and len(payload) > MAX_BYTES:
                result, payload = {"status": "body_size_limit"}, None
            elif result["status"] != "response_received":
                payload = None
        except Exception:
            result, payload = {"status": "request_failed_without_diagnostics"}, None
        record = {**spec, "transport": result, "status": result["status"]}
        if payload is not None:
            # Persist only bounded, secret-free bodies supplied by the safe fetcher.
            record["source_sha256"] = hashlib.sha256(payload).hexdigest()
            record["raw_file"] = spec["id"] + ".csv"
            write_private(output / record["raw_file"], payload)
            try:
                parsed = parse_point_csv(payload, spec)
                if grid is not None and parsed["grid"] != grid:
                    raise ValueError("inconsistent grid")
                retrieved = datetime.fromisoformat(result["retrieved_at_utc"])
                retrieved = as_utc(retrieved)
                valid = datetime.fromisoformat(spec["requested_valid_time_utc"])
                record["retrieved_at_utc"] = iso(retrieved)
                record["hours_after_retrieval"] = (valid - retrieved).total_seconds() / 3600
                record["future_at_retrieval"] = valid > retrieved
                record["parsed"] = parsed
                record["status"] = "validated_point_csv"
                grid = parsed["grid"]
            except (KeyError, ValueError, TypeError):
                record["status"] = "csv_or_grid_validation_failed"
        report["records"].append(record)
        if record["status"] != "validated_point_csv":
            report["stopped_early"] = record["status"]
            break
    report["hours"] = assemble_hours(plan, report["records"])
    report["retrieved_requests"] = len(report["records"])
    report["validated_requests"] = sum(
        record["status"] == "validated_point_csv" for record in report["records"]
    )
    report["complete"] = report["validated_requests"] == 24
    report["all_future_at_retrieval"] = report["complete"] and all(
        record.get("future_at_retrieval", False) for record in report["records"]
    )
    report["grid"] = grid
    report["finished_at_utc"] = iso(now())
    report["status"] = "complete_research_forecast" if report["complete"] else "partial_forecast"
    _write_json(output / "report.json", report, key)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue", required=True, help="explicit 00/06/12/18 UTC KIML cycle")
    parser.add_argument("--lat", type=float, default=37.0)
    parser.add_argument("--lon", type=float, default=129.3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = build_plan(parse_issue(args.issue), datetime.now(UTC), lon=args.lon, lat=args.lat)
        report = run_probe(plan, args.output, os.environ.get("KMA_APIHUB_AUTH_KEY", ""))
    except Exception:
        print(
            json.dumps({"status": "probe_failed", "details": "no credentials or exceptions logged"})
        )
        return 1
    print(
        json.dumps(
            {
                "status": report["status"],
                "validated_requests": report["validated_requests"],
                "complete": report["complete"],
                "source_reference_confirmed": False,
                "wind_direction_status": "basis_unverified",
                "operational_use": False,
            }
        )
    )
    return 0 if report["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
