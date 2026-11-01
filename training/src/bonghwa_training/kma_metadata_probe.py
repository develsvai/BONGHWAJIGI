"""Three bounded metadata requests: small KIML U/V NetCDF and one 2022 UM point.

Credential injection is the caller's responsibility. No retries, service changes,
wind-direction calculation, 2025 labels, or operational forecast use.
"""

import argparse
import hashlib
import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from bonghwa_training.kiml_point_forecast import VARIABLE_DOCUMENTATION
from bonghwa_training.kma_forecast_probe import (
    DOCUMENTATION,
    NoRedirect,
    contains_sensitive,
    iso,
    retry_after_seconds,
    write_private,
)

NC_ENDPOINT = "https://apihub.kma.go.kr/api/typ06/url/nwp_nc_vars_down.php"
UM_ENDPOINT = "https://apihub.kma.go.kr/api/typ06/cgi-bin/url/nph-um_grib_pt_txt1"
MAX_NC_BYTES = 4 * 1024 * 1024
MAX_TEXT_BYTES = 128 * 1024
MAX_VARIABLE_VALUES = 4096
NC_MAGIC = (b"\x89HDF\r\n\x1a\n", b"CDF\x01", b"CDF\x02", b"CDF\x05")


def build_plan():
    records = []
    for variable in ("U10", "V10"):
        records.append(
            {
                "id": f"kiml-20261031T12Z-{variable.lower()}-h5-nc",
                "branch": "kiml_netcdf",
                "format": "netcdf",
                "endpoint": NC_ENDPOINT,
                "parameters_without_auth": {
                    "group": "KIML",
                    "data": "U",
                    "vars": variable,
                    "tmfc": "2026103112",
                    "hf": "5",
                    "lon1": "129.29",
                    "lat1": "36.98",
                    "lon2": "129.31",
                    "lat2": "37.01",
                    "dataType": "NC",
                },
                "requested_reference_time_utc": "2026-10-31T12:00:00+00:00",
                "requested_valid_time_utc": "2026-10-31T17:00:00+00:00",
                "max_bytes": MAX_NC_BYTES,
            }
        )
    records.append(
        {
            "id": "umkr-20220304T00Z-point-h1",
            "branch": "historical_um",
            "format": "text",
            "endpoint": UM_ENDPOINT,
            "parameters_without_auth": {
                "group": "UMKR",
                "nwp": "N512",
                "data": "U",
                "varn": "2002,2003,0,1001",
                "tmfc": "2022030400",
                "hf": "1",
                "lon": "129.3",
                "lat": "37.0",
                "disp": "A",
                "mode": "1",
                "help": "1",
            },
            "requested_reference_time_utc": "2022-03-04T00:00:00+00:00",
            "requested_valid_time_utc": "2022-03-04T01:00:00+00:00",
            "max_bytes": MAX_TEXT_BYTES,
        }
    )
    return {
        "schema_version": 1,
        "purpose": "kma_small_area_axis_and_historical_access_metadata_research",
        "max_http_attempts": 3,
        "request_spacing_seconds": 1,
        "retry_count": 0,
        "operational_use": False,
        "holdout_2025_accessed": False,
        "fire_labels_requested": False,
        "grib_requested": False,
        "documentation": DOCUMENTATION,
        "unit_documentation": VARIABLE_DOCUMENTATION,
        "requests": records,
    }


def fetch_once(spec, key, *, opener=None, now=None):
    opener = opener or urllib.request.build_opener(NoRedirect()).open
    now = now or (lambda: datetime.now(UTC))
    started = iso(now())
    params = dict(spec["parameters_without_auth"], authKey=key)
    request = urllib.request.Request(
        spec["endpoint"] + "?" + urllib.parse.urlencode(params),
        headers={"Accept": "application/x-netcdf,application/octet-stream,text/plain"},
    )
    try:
        with opener(request, timeout=30) as response:
            if response.status != 200:
                raise urllib.error.HTTPError("", response.status, "", response.headers, None)
            payload = response.read(spec["max_bytes"] + 1)
        if len(payload) > spec["max_bytes"]:
            return {"status": "body_size_limit", "started_at_utc": started}, None
        if contains_sensitive(payload, key):
            return {"status": "sensitive_response_rejected", "started_at_utc": started}, None
        return {
            "status": "response_received",
            "http_status": 200,
            "started_at_utc": started,
            "retrieved_at_utc": iso(now()),
        }, payload
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        delay = (
            retry_after_seconds((exc.headers or {}).get("Retry-After"), now())
            if status == 429
            else None
        )
        exc.close()
        return {
            "status": "rate_limited" if status == 429 else "http_error",
            "http_status": status,
            "started_at_utc": started,
            "retry_after_seconds": delay,
        }, None
    except Exception:
        return {"status": "transport_or_read_error", "started_at_utc": started}, None


def plain(value):
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        if len(value) > MAX_VARIABLE_VALUES:
            raise ValueError("metadata array exceeds small probe limit")
        return [plain(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, str) and len(value) > 65536:
        raise ValueError("metadata text exceeds small probe limit")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ValueError("unsupported metadata type")


def flattened(value):
    if isinstance(value, list):
        return [item for child in value for item in flattened(child)]
    return [value]


def inspect_netcdf(payload, spec):
    """Read a bounded in-memory dataset; all derived interpretation is provisional."""
    if not payload.startswith(NC_MAGIC):
        raise ValueError("NetCDF/HDF5 magic required")
    import netCDF4

    expected_variable = spec["parameters_without_auth"]["vars"]
    with netCDF4.Dataset("probe.nc", memory=payload) as dataset:
        if len(dataset.variables) > 64 or len(dataset.dimensions) > 32:
            raise ValueError("dataset exceeds bounded metadata scope")
        if len(dataset.ncattrs()) > 128:
            raise ValueError("too many global attributes")
        result = {
            "global_attributes": {
                name: plain(dataset.getncattr(name)) for name in dataset.ncattrs()
            },
            "dimensions": {name: len(value) for name, value in dataset.dimensions.items()},
            "variables": {},
            "coordinate_bounds": {},
            "time_candidates": [],
            "reference_time_candidates": [],
        }
        for name, variable in dataset.variables.items():
            if len(variable.ncattrs()) > 128:
                raise ValueError("too many variable attributes")
            attrs = {attr: plain(variable.getncattr(attr)) for attr in variable.ncattrs()}
            entry = {
                "dimensions": list(variable.dimensions),
                "shape": list(variable.shape),
                "dtype": str(variable.dtype),
                "attributes": attrs,
                "raw_values": None,
            }
            result["variables"][name] = entry
            if variable.size > MAX_VARIABLE_VALUES:
                entry["values_omitted_reason"] = "exceeds_small_area_value_limit"
                continue
            variable.set_auto_maskandscale(False)
            values = variable[...]
            entry["raw_values"] = plain(values)
            flat = flattened(entry["raw_values"])
            standard = attrs.get("standard_name", "")
            coordinate = None
            if standard == "longitude" or name.lower() in ("lon", "longitude", "xlong"):
                coordinate = "longitude"
            elif standard == "latitude" or name.lower() in ("lat", "latitude", "xlat"):
                coordinate = "latitude"
            if (
                coordinate
                and flat
                and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in flat)
            ):
                minimum, maximum = min(flat), max(flat)
                prefix = "lon" if coordinate == "longitude" else "lat"
                params = spec["parameters_without_auth"]
                result["coordinate_bounds"][name] = {
                    "coordinate": coordinate,
                    "minimum": minimum,
                    "maximum": maximum,
                    "within_requested_bbox": float(params[prefix + "1"])
                    <= minimum
                    <= maximum
                    <= float(params[prefix + "2"]),
                }
            time_kind = (
                "reference_time_candidates"
                if standard == "forecast_reference_time"
                else (
                    "time_candidates"
                    if standard == "time" or name.lower() in ("time", "valid_time")
                    else None
                )
            )
            if time_kind and isinstance(attrs.get("units"), str) and " since " in attrs["units"]:
                try:
                    decoded = netCDF4.num2date(
                        values, units=attrs["units"], calendar=attrs.get("calendar", "standard")
                    )
                    for timestamp in flattened(plain_time_array(decoded)):
                        result[time_kind].append({"variable": name, "utc": timestamp})
                except Exception:
                    entry["time_decode_status"] = "unrecognized_or_invalid_time_encoding"
    selected = result["variables"].get(expected_variable)
    attrs = selected["attributes"] if selected else {}
    standard = attrs.get("standard_name")
    geographic = "eastward_wind" if expected_variable == "U10" else "northward_wind"
    grid_names = (
        ("x_wind", "grid_eastward_wind")
        if expected_variable == "U10"
        else ("y_wind", "grid_northward_wind")
    )
    basis = (
        "geographic"
        if standard == geographic
        else "grid"
        if standard in grid_names
        else "unverified"
    )
    result.update(
        requested_variable_present=selected is not None,
        source_declared_axis_basis=basis,
        source_declared_standard_name=standard,
        source_declared_unit=attrs.get("units"),
        source_unit_matches_documentation=attrs.get("units")
        in ("m/s", "m s-1", "m s**-1", "m.s-1", "m s^-1"),
        wind_basis_validated=False,
        csv_values_compared=False,
        source_height_confirmed=False,
        preview_interpretation=(
            "Raw values; no missing-value masking, scale/offset or rotation applied"
        ),
    )
    for kind, requested, output in (
        ("time_candidates", "requested_valid_time_utc", "time_candidates_match_request"),
        (
            "reference_time_candidates",
            "requested_reference_time_utc",
            "reference_candidates_match_request",
        ),
    ):
        candidates = result[kind]
        expected = datetime.fromisoformat(spec[requested])
        result[output] = (
            all(datetime.fromisoformat(row["utc"]) == expected for row in candidates)
            if candidates
            else None
        )
    return result


def plain_time_array(value):
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, (list, tuple)):
        return [plain_time_array(item) for item in value]
    # CF reference-time units define the offset; num2date returns this UTC clock.
    converted = datetime(
        value.year,
        value.month,
        value.day,
        value.hour,
        value.minute,
        value.second,
        value.microsecond,
        tzinfo=UTC,
    )
    return iso(converted)


def inspect_um_text(payload, spec):
    text = payload.decode("utf-8", errors="strict")
    if re.search(
        r"<html|<!doctype|<error|error|unauthori[sz]ed|access denied|인증|권한", text, re.I
    ):
        raise ValueError("error/markup response is not meteorological data")
    tokens = ("TMFC", "TMEF", "VARN", "LEVEL")
    if not all(token in text.upper() for token in tokens):
        raise ValueError("unrecognized UM header")
    rows = [
        line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")
    ]
    numeric = [
        line
        for line in rows
        if re.search(r"\d", line) and not any(token in line.upper() for token in tokens)
    ]
    if not numeric:
        raise ValueError("no numeric UM data candidates")
    return {
        "recognized_header_tokens": list(tokens),
        "numeric_candidate_rows": len(numeric),
        "requested_reference_stamp_seen": spec["parameters_without_auth"]["tmfc"] in text,
        "requested_valid_stamp_seen": datetime.fromisoformat(
            spec["requested_valid_time_utc"]
        ).strftime("%Y%m%d%H")
        in text,
        "schema_verified": False,
        "height_confirmed": False,
        "wind_basis_validated": False,
        "interpretation": "Header/data candidates only; UM layers and schema need separate review",
    }


def write_json(path, value, key):
    payload = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    if contains_sensitive(payload, key):
        raise ValueError("sensitive metadata blocked")
    write_private(path, payload)


def run_probe(output, key, *, fetcher=fetch_once, sleeper=time.sleep, now=None):
    if not key or len(key) < 8 or any(char.isspace() for char in key):
        raise ValueError("credential must be injected privately")
    now = now or (lambda: datetime.now(UTC))
    plan = build_plan()
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    write_json(output / "plan.json", plan, key)
    report = {
        "schema_version": 1,
        "purpose": plan["purpose"],
        "started_at_utc": iso(now()),
        "source_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "plan_sha256": hashlib.sha256((output / "plan.json").read_bytes()).hexdigest(),
        "operational_use": False,
        "holdout_2025_accessed": False,
        "wind_basis_validated": False,
        "max_http_attempts": 3,
        "actual_http_requests": 0,
        "records": [],
    }
    stopped = set()
    for spec in plan["requests"]:
        if spec["branch"] in stopped:
            report["records"].append({**spec, "status": "skipped_after_branch_access_failure"})
            continue
        if report["actual_http_requests"]:
            sleeper(1)
        report["actual_http_requests"] += 1
        try:
            result, payload = fetcher(spec, key)
            if contains_sensitive(json.dumps(result).encode(), key) or (
                payload is not None and contains_sensitive(payload, key)
            ):
                result, payload = {"status": "sensitive_response_rejected"}, None
        except Exception:
            result, payload = {"status": "request_failed_without_diagnostics"}, None
        record = {**spec, "transport": result, "status": result["status"]}
        if result.get("http_status") in (401, 403, 429):
            stopped.add(spec["branch"])
        if payload is not None and result["status"] == "response_received":
            try:
                if len(payload) > spec["max_bytes"]:
                    raise ValueError("body exceeds limit")
                metadata = (
                    inspect_netcdf(payload, spec)
                    if spec["format"] == "netcdf"
                    else inspect_um_text(payload, spec)
                )
                encoded = json.dumps(metadata, ensure_ascii=False, allow_nan=False).encode()
                if len(encoded) > 1024 * 1024 or contains_sensitive(encoded, key):
                    raise ValueError("unsafe or excessive decoded metadata")
                filename = spec["id"] + (".nc" if spec["format"] == "netcdf" else ".txt")
                write_private(output / filename, payload)
                record.update(
                    status="metadata_recorded",
                    raw_file=filename,
                    bytes=len(payload),
                    source_sha256=hashlib.sha256(payload).hexdigest(),
                    metadata=metadata,
                )
            except Exception:
                record["status"] = "unrecognized_or_unsafe_metadata"
        report["records"].append(record)
    report["finished_at_utc"] = iso(now())
    report["metadata_records"] = sum(
        record["status"] == "metadata_recorded" for record in report["records"]
    )
    report["complete"] = report["metadata_records"] == 3
    write_json(output / "report.json", report, key)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run_probe(args.output, os.environ.get("KMA_APIHUB_AUTH_KEY", ""))
    except Exception:
        print(
            json.dumps(
                {"status": "probe_failed", "detail": "no credentials or exception bodies logged"}
            )
        )
        return 1
    print(
        json.dumps(
            {
                "status": "metadata_probe_recorded",
                "actual_http_requests": report["actual_http_requests"],
                "metadata_records": report["metadata_records"],
                "complete": report["complete"],
                "wind_basis_validated": False,
                "operational_use": False,
            }
        )
    )
    return 0 if report["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
