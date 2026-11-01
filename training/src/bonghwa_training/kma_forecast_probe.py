"""Bounded KMA forecast access probe; never a fire label or operational predictor.

Run with KMA_APIHUB_AUTH_KEY injected by the caller. Keys are never read from files.
Default: twelve single-point, one-hour forecast requests (KIML/KIMR and 2022 UMKR).
"""

import argparse
import hashlib
import html
import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

DOCUMENTATION = "https://apihub.kma.go.kr/apiList.do?seqApi=9"
KIM_ENDPOINT = "https://apihub.kma.go.kr/api/typ06/url/nwp_nc_pnt_down.php"
UM_ENDPOINT = "https://apihub.kma.go.kr/api/typ06/cgi-bin/url/nph-um_grib_pt_txt1"
VARIABLES = (
    ("U10", "2002", "eastward_wind", "m/s", 10),
    ("V10", "2003", "northward_wind", "m/s", 10),
    ("T2", "0", "temperature", "K", 2),
    ("RH2", "1001", "relative_humidity", "%", 2),
)
MAX_BYTES = 512 * 1024
MAX_ATTEMPTS = 3
MAX_RETRY_DELAY = 60


def iso(value):
    return value.astimezone(UTC).isoformat()


def parse_issue(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise ValueError("issue time must be ISO-8601 with timezone") from None
    if result.tzinfo is None:
        raise ValueError("issue time requires timezone")
    result = result.astimezone(UTC)
    if result.minute or result.second or result.microsecond or result.hour % 6:
        raise ValueError("issue time must be a 00/06/12/18 UTC cycle")
    return result


def build_plan(current_issue, historical_issue, *, lon=129.3, lat=37.0, lead=1):
    """One Korean location only; lock out 2025 and any observation endpoints."""
    if current_issue.year != 2026 or current_issue < datetime(2026, 2, 9, tzinfo=UTC):
        raise ValueError("current probe is restricted to KIM 2026 cycles")
    if historical_issue.year not in (2020, 2021, 2022, 2023):
        raise ValueError("historical probe is restricted to 2020-2023; 2025 stays locked")
    for when in (current_issue, historical_issue):
        if parse_issue(iso(when)) != when:
            raise ValueError("invalid issue cycle")
    if not (math.isfinite(lon) and math.isfinite(lat) and 124 <= lon <= 132 and 33 <= lat <= 39):
        raise ValueError("a single Korean point is required")
    if lead not in (1, 3, 6):
        raise ValueError("lead must be 1, 3 or 6 hours")
    plan = []
    for model, issue in (
        ("KIML", current_issue),
        ("KIMR", current_issue),
        ("UMKR", historical_issue),
    ):
        for name, code, meaning, unit, height in VARIABLES:
            params = {
                "group": model,
                "data": "U",
                "tmfc": issue.strftime("%Y%m%d%H"),
                "hf": str(lead),
                "lon": str(lon),
                "lat": str(lat),
                "help": "1",
            }
            if model == "UMKR":
                params.update(nwp="N512", varn=code, disp="A")
            else:
                params.update(vars=name, dataType="CSV")
            endpoint = UM_ENDPOINT if model == "UMKR" else KIM_ENDPOINT
            plan.append(
                {
                    "id": f"{model.lower()}-{issue:%Y%m%dT%HZ}-{name.lower()}-h{lead}",
                    "model": model,
                    "endpoint": endpoint,
                    "parameters_without_auth": params,
                    "source_kind": "numerical_weather_forecast",
                    "observed": False,
                    "forecast_reference_time_utc": iso(issue),
                    "issue_time_semantics": "model cycle, not proof of publication/availability",
                    "requested_valid_time_utc": iso(issue + timedelta(hours=lead)),
                    "lead_hours": lead,
                    "variable": name,
                    "meaning": meaning,
                    "documented_unit": unit,
                    "documented_height_m": height if model != "UMKR" else None,
                    "height_note": "UM returned levels must be inspected; no 2m assumption"
                    if model == "UMKR"
                    else "KIM standard variable definition",
                    "documentation": DOCUMENTATION,
                }
            )
    return plan


def contains_sensitive(payload, key):
    """Fail closed on key echoes/auth URLs, including percent/HTML/JSON escapes."""
    text = payload.decode("utf-8", errors="replace")
    for _ in range(3):
        text = html.unescape(urllib.parse.unquote_plus(text))
        text = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m[1], 16)), text)
    if re.search(r"auth.?key|service.?key|authorization|api.?key", text, re.I):
        return True
    forms = {
        key,
        urllib.parse.quote(key, safe=""),
        urllib.parse.quote_plus(key),
        json.dumps(key, ensure_ascii=True)[1:-1],
    }
    return any(form and form in text for form in forms) or key.encode() in payload


def inspect_payload(payload, spec):
    """Conservative diagnostics; unrecognized schemas never become verified inputs."""
    text = payload.decode("utf-8", errors="replace")
    lower = text.lower()
    if any(
        word in lower
        for word in (
            "<!doctype",
            "<html",
            "<response",
            "<error",
            "resultcode",
            "service_error",
            "access denied",
        )
    ):
        return {"content_status": "error_or_markup_payload", "schema_verified": False}
    if any(word in lower for word in ("error", "invalid", "unauthorized", "인증", "권한")):
        return {"content_status": "error_payload", "schema_verified": False}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    rows = []
    for line in lines:
        if line.startswith("#"):
            continue
        fields = re.split(r"[\s,;]+", line)
        if len(fields) >= 2:
            numbers = []
            for value in fields:
                try:
                    number = float(value)
                except ValueError:
                    continue
                if math.isfinite(number):
                    numbers.append(number)
            if len(numbers) >= 2:
                rows.append(numbers)
    expected = datetime.fromisoformat(spec["forecast_reference_time_utc"])
    valid = datetime.fromisoformat(spec["requested_valid_time_utc"])
    return {
        "content_status": "numeric_candidate_requires_schema_review"
        if rows
        else "unrecognized_or_empty_payload",
        "schema_verified": False,
        "numeric_row_count": len(rows),
        "reference_stamp_seen": expected.strftime("%Y%m%d%H") in text,
        "valid_stamp_seen": valid.strftime("%Y%m%d%H") in text,
        "interpretation": "HTTP success/numeric text alone does not prove meteorological values",
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Do not forward credentials through redirects, even to a same-host URL.
        raise urllib.error.HTTPError(req.full_url, code, "redirect blocked", {}, None)


def retry_after_seconds(value, now):
    try:
        if str(value).strip().isdigit():
            return max(0, int(value))
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return max(0, math.ceil((parsed - now).total_seconds()))
    except (ValueError, TypeError, OverflowError):
        return 30


def fetch_probe(spec, key, *, opener=None, sleeper=time.sleep, now=None):
    """Return safe metadata + safe body. Never return exception strings or headers."""
    if opener is None:
        opener = urllib.request.build_opener(NoRedirect()).open
    now = now or (lambda: datetime.now(UTC))
    params = dict(spec["parameters_without_auth"], authKey=key)
    request = urllib.request.Request(
        spec["endpoint"] + "?" + urllib.parse.urlencode(params),
        headers={"Accept": "text/plain,text/csv"},
    )
    attempts = []
    for attempt in range(MAX_ATTEMPTS):
        started = iso(now())
        try:
            with opener(request, timeout=30) as response:
                status = response.status
                if status != 200:
                    raise urllib.error.HTTPError("", status, "", response.headers, None)
                payload = response.read(MAX_BYTES + 1)
            record = {"attempt": attempt + 1, "started_at_utc": started, "http_status": 200}
            attempts.append(record)
            if len(payload) > MAX_BYTES:
                return {"status": "body_size_limit", "attempts": attempts}, None
            if contains_sensitive(payload, key):
                return {"status": "sensitive_response_rejected", "attempts": attempts}, None
            details = inspect_payload(payload, spec)
            result = {
                "status": "response_received",
                "attempts": attempts,
                "retrieved_at_utc": iso(now()),
                "bytes": len(payload),
                "source_sha256": hashlib.sha256(payload).hexdigest(),
                **details,
            }
            # Retain bounded, secret-free numeric candidates only, never error bodies.
            return result, payload if details.get("numeric_row_count", 0) > 0 else None
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            attempts.append(
                {"attempt": attempt + 1, "started_at_utc": started, "http_status": status}
            )
            retry = status == 429 or status >= 500
            delay = max(
                2**attempt,
                retry_after_seconds((exc.headers or {}).get("Retry-After"), now())
                if status == 429
                else 0,
            )
            exc.close()
            if retry and attempt + 1 < MAX_ATTEMPTS and delay <= MAX_RETRY_DELAY:
                attempts[-1]["retry_after_seconds"] = delay
                sleeper(delay)
                continue
            return {
                "status": "rate_limited" if status == 429 else "http_error",
                "http_status": status,
                "attempts": attempts,
                "retry_after_seconds": delay if retry else None,
            }, None
        except Exception:
            # URLError/repr can contain complete credentialed URLs; never interpolate it.
            attempts.append(
                {
                    "attempt": attempt + 1,
                    "started_at_utc": started,
                    "status": "transport_or_read_error",
                }
            )
            if attempt + 1 < MAX_ATTEMPTS:
                sleeper(2**attempt)
                continue
            return {"status": "transport_or_read_error", "attempts": attempts}, None
    raise AssertionError("unreachable")


def write_private(path, payload):
    # New files only: immutable probe evidence and no accidental overwrites.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as dst:
        dst.write(payload)


def run_probe(plan, output, key, *, fetcher=fetch_probe, sleeper=time.sleep):
    if not key or len(key) < 8 or any(c.isspace() for c in key):
        raise ValueError("KMA_APIHUB_AUTH_KEY must be injected as an environment variable")
    if len(plan) != 12:
        raise ValueError("probe plan must contain exactly twelve bounded requests")
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    report = {
        "schema_version": 1,
        "purpose": "forecast_access_and_schema_probe",
        "operational_use": False,
        "fire_labels_requested": False,
        "holdout_2025_accessed": False,
        "records": [],
        "availability_note": "current retrieval does not prove historical issue-time availability",
        "compatibility_note": "UM and KIM grids/heights/bias require separate reconciliation",
        "max_requests_including_retries": 12 * MAX_ATTEMPTS,
    }
    for spec in plan:
        result, payload = fetcher(spec, key)
        record = {**spec, **result}
        if payload is not None:
            # Guard again at the persistence boundary, including custom fetcher tests.
            if contains_sensitive(payload, key):
                raise ValueError("sensitive response blocked before persistence")
            name = spec["id"] + ".txt"
            write_private(output / name, payload)
            record["raw_file"] = name
        report["records"].append(record)
        if result["status"] == "rate_limited" or result.get("http_status") in (401, 403):
            report["stopped_early"] = result["status"]
            break
        sleeper(1)
    encoded = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode()
    if contains_sensitive(encoded, key):
        # Metadata contains no auth parameter names or uncontrolled response strings.
        raise ValueError("sensitive metadata blocked before persistence")
    write_private(output / "report.json", encoded)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-issue", required=True, help="UTC ISO KIM cycle in 2026")
    parser.add_argument("--historical-issue", default="2022-03-04T00:00:00Z")
    parser.add_argument("--lon", type=float, default=129.3)
    parser.add_argument("--lat", type=float, default=37.0)
    parser.add_argument("--lead", type=int, choices=(1, 3, 6), default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = build_plan(
            parse_issue(args.current_issue),
            parse_issue(args.historical_issue),
            lon=args.lon,
            lat=args.lat,
            lead=args.lead,
        )
        report = run_probe(plan, args.output, os.environ.get("KMA_APIHUB_AUTH_KEY", ""))
    except Exception:
        print(json.dumps({"status": "probe_failed", "detail": "no secrets or error bodies logged"}))
        return 1
    counts = {}
    for record in report["records"]:
        status = record["status"]
        counts[status] = counts.get(status, 0) + 1
    print(
        json.dumps(
            {
                "status": "probe_recorded",
                "request_results": counts,
                "schema_verified": False,
                "operational_use": False,
            }
        )
    )
    return 2 if report.get("stopped_early") else 0


if __name__ == "__main__":
    raise SystemExit(main())
