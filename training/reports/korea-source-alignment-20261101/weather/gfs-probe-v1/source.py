"""Bounded, credential-private KMA historical weather access research.

No training, labels, validation or holdout reads. Observations downloaded today
do not establish their historical publication time. This never changes services.
"""

import argparse
import hashlib
import json
import re
import shlex
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

from bonghwa_training.download import file_sha256
from bonghwa_training.kma_forecast_probe import NoRedirect, contains_sensitive
from bonghwa_training.kma_metadata_probe import inspect_netcdf

ROOT = "https://apihub.kma.go.kr/api"
MAX_REQUESTS = 20
MAX_BYTES = 100 * 1024 * 1024
TRAIN_IDS = frozenset(
    "andong_2020 andong_2021 hapcheon_2022 uljin_2022 ulju_2020 goseong_2020 "
    "yeongdeok_2022 yeongwol_2022 gangneung_donghae_2022 bonghwa_2022 "
    "yanggu_2022 gunwi_2022 uljin_may_2022 miryang_2022".split()
)
SAMPLES = (
    ("uljin_2022", "202203041000", "2022-03-04T01:00:00Z"),
    ("ulju_2020", "202003191400", "2020-03-19T05:00:00Z"),
)
DOCUMENTATION = {
    "numerical": "https://apihub.kma.go.kr/apiList.do?seqApi=9",
    "asos": "https://apihub.kma.go.kr/apiList.do?seqApi=2",
    "aws": "https://apihub.kma.go.kr/apiList.do?seqApi=2&seqApiSub=239",
    "station": "https://apihub.kma.go.kr/apiList.do?seqApi=2&seqApiSub=317",
}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def build_plan():
    records = [
        {
            "id": "kiml-axis-registration-recheck",
            "kind": "netcdf",
            "endpoint": ROOT + "/typ06/url/nwp_nc_vars_down.php",
            "parameters_without_auth": {
                "group": "KIML",
                "data": "U",
                "vars": "U10",
                "tmfc": "2026103112",
                "hf": "5",
                "lon1": "129.29",
                "lat1": "36.98",
                "lon2": "129.31",
                "lat2": "37.01",
                "dataType": "NC",
            },
            "requested_reference_time_utc": "2026-10-31T12:00:00Z",
            "requested_valid_time_utc": "2026-10-31T17:00:00Z",
            "max_bytes": 4 * 1024 * 1024,
            "note": "One registration recheck only; contemporary metadata, not train input",
        },
        {
            "id": "uljin_2022-umkr-point",
            "kind": "um_point",
            "endpoint": ROOT + "/typ06/cgi-bin/url/nph-um_grib_pt_txt1",
            "parameters_without_auth": {
                "group": "UMKR",
                "nwp": "N512",
                "data": "U",
                "varn": "2002,2003,0,1001",
                "tmfc": "2022030400",
                "hf": "1",
                "lon": "129.3",
                "lat": "37.2",
                "disp": "A",
                "mode": "1",
                "help": "1",
            },
            "max_bytes": 1024 * 1024,
            "note": "Archived forecast reference time is not verified release time",
        },
        {
            "id": "uljin_2022-ldaps-header",
            "kind": "grib_header",
            "endpoint": ROOT + "/typ06/cgi-bin/url/nph-nwp_header",
            "parameters_without_auth": {
                "model": "um",
                "nwp": "l015",
                "sub": "unis",
                "tmfc": "202203040000",
                "ef": "1",
                "help": "1",
            },
            "max_bytes": 1024 * 1024,
            "note": "Header/variable access probe, no full grid or guessed variable download",
        },
    ]
    for event_id, kst, utc in SAMPLES:
        for kind, endpoint, params in (
            ("asos", "/typ01/url/kma_sfctm2.php", {"tm": kst, "stn": "0", "help": "1"}),
            (
                "aws",
                "/typ01/cgi-bin/url/nph-aws2_min",
                {"tm2": kst, "stn": "0", "disp": "0", "help": "1"},
            ),
            (
                "station_sfc",
                "/typ01/url/stn_inf.php",
                {"inf": "SFC", "tm": kst, "stn": "0", "help": "1"},
            ),
            (
                "station_aws",
                "/typ01/url/stn_inf.php",
                {"inf": "AWS", "tm": kst, "stn": "0", "help": "1"},
            ),
        ):
            records.append(
                {
                    "id": f"{event_id}-{kind}",
                    "event_id": event_id,
                    "kind": kind,
                    "endpoint": ROOT + endpoint,
                    "parameters_without_auth": params,
                    "observation_time_utc": utc,
                    "max_bytes": 2 * 1024 * 1024,
                }
            )
    return {
        "schema": "kma_weather_alignment_probe_v1",
        "max_http_requests": MAX_REQUESTS,
        "max_bytes_per_file": MAX_BYTES,
        "max_total_bytes": MAX_BYTES,
        "planned_max_total_bytes": sum(r["max_bytes"] for r in records),
        "planned_request_count": len(records),
        "no_retries": True,
        "stop_same_endpoint_after_403": True,
        "stop_all_after_401_or_429": True,
        "redirects_allowed": False,
        "request_spacing_seconds": 1,
        "timeout_seconds": 30,
        "samples_selected_before_response": (
            "Two fixed train cases spanning 2020/2022, not representative"
        ),
        "documentation": DOCUMENTATION,
        "requests": records,
        "validation_read": False,
        "calibration_read": False,
        "test_read": False,
        "operational_use": False,
        "historical_release_time_verified": False,
        "license": (
            "KMA API service terms and source attribution apply; "
            "no open-source software license inferred"
        ),
    }


def read_server_key():
    # Deliberately no command-line, environment dump, shell sourcing or exception values.
    path = Path.home() / ".config/bonghwajigi/training.env"
    found = []
    for line in path.read_text().splitlines():
        match = re.fullmatch(r"\s*(?:export\s+)?KMA_APIHUB_AUTH_KEY\s*=\s*(.*?)\s*", line)
        if match:
            value = shlex.split(match.group(1), comments=True)
            if len(value) != 1 or len(value[0]) < 8:
                raise ValueError("invalid private credential setting")
            found.extend(value)
    if len(found) != 1:
        raise ValueError("one private credential setting required")
    return found[0]


def fetch(spec, key, opener=None):
    opener = opener or urllib.request.build_opener(NoRedirect()).open
    limit = spec["max_bytes"]
    if not 0 < limit <= MAX_BYTES:
        raise ValueError("request size exceeds fixed ceiling")
    params = dict(spec["parameters_without_auth"], authKey=key)
    request = urllib.request.Request(spec["endpoint"] + "?" + urllib.parse.urlencode(params))
    start = datetime.now(UTC).isoformat()
    try:
        response = opener(request, timeout=30)
    except urllib.error.HTTPError as exc:
        response = exc
    except Exception:
        return {"status": "transport_error", "started_at_utc": start}, None
    try:
        with response:
            status = int(response.code)
            payload = response.read(limit + 1)
            content_type = response.headers.get("Content-Type", "")
    except Exception:
        return {"status": "read_error", "started_at_utc": start}, None
    result = {
        "started_at_utc": start,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "http_status": status,
        "bytes_read": len(payload),
        "content_type": content_type,
    }
    if len(payload) > limit:
        return {**result, "status": "size_limit_exceeded"}, None
    if contains_sensitive(payload, key) or contains_sensitive(content_type.encode(), key):
        return {**result, "content_type": None, "status": "sensitive_response_discarded"}, None
    result["source_sha256"] = hashlib.sha256(payload).hexdigest()
    try:
        parsed = json.loads(payload)
        nested = parsed.get("result", {}) if isinstance(parsed, dict) else {}
        provider_status = nested.get("status")
        if isinstance(provider_status, int) and provider_status >= 400:
            result["provider_status"] = provider_status
    except (ValueError, UnicodeDecodeError):
        pass
    if status != 200 or result.get("provider_status", 200) >= 400:
        result["status"] = (
            "access_error"
            if status in (401, 403) or result.get("provider_status") in (401, 403)
            else "http_or_provider_error"
        )
        # No raw error body retained. Only a bounded, key-checked provider message.
        result["safe_body_excerpt"] = payload.decode("utf-8", errors="replace")[:600]
        return result, None
    return {**result, "status": "received"}, payload


def run(output, key, fetcher=fetch, sleeper=time.sleep):
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    plan = build_plan()
    if sum(r["max_bytes"] + 1 for r in plan["requests"]) > MAX_BYTES:
        raise ValueError("plan exceeds aggregate download ceiling")
    write_json(output / "plan.json", plan)
    report = {
        "plan_sha256": file_sha256(output / "plan.json"),
        "source_code_sha256": file_sha256(Path(__file__)),
        "actual_http_requests": 0,
        "total_response_bytes_read": 0,
        "operational_use": False,
        "validation_read": False,
        "calibration_read": False,
        "test_read": False,
        "historical_release_time_verified": False,
        "records": [],
    }
    blocked, all_blocked = set(), False
    for spec in plan["requests"]:
        record = dict(spec)
        if all_blocked or spec["endpoint"] in blocked:
            record["status"] = "skipped_after_access_or_rate_failure"
        else:
            if report["actual_http_requests"] >= MAX_REQUESTS:
                raise ValueError("request budget exhausted")
            report["actual_http_requests"] += 1
            result, payload = fetcher(spec, key)
            record.update(result)
            report["total_response_bytes_read"] += result.get("bytes_read", 0)
            codes = {result.get("http_status"), result.get("provider_status")}
            if 403 in codes:
                blocked.add(spec["endpoint"])
            if codes & {401, 429}:
                all_blocked = True
            if payload is not None:
                suffix = ".nc" if spec["kind"] == "netcdf" else ".txt"
                path = output / (spec["id"] + suffix)
                path.write_bytes(payload)
                path.chmod(0o600)
                record["path"] = path.name
                record["sha256"] = file_sha256(path)
                if spec["kind"] == "netcdf":
                    try:
                        record["metadata"] = inspect_netcdf(payload, spec)
                    except Exception:
                        record["metadata_status"] = "not_validated_netcdf"
                else:
                    lines = payload.decode("utf-8", errors="replace").splitlines()
                    record["noncomment_lines"] = sum(
                        bool(s.strip()) and not s.lstrip().startswith("#") for s in lines
                    )
                    record["data_schema_verified"] = False
            sleeper(1)
        report["records"].append(record)
        encoded = json.dumps(report, ensure_ascii=False).encode()
        if contains_sensitive(encoded, key):
            raise ValueError("sensitive report blocked")
        write_json(output / "report.json", report)
    return report


def diagnose_existing(dataset, output):
    """Only input columns of fixed train files; never read target or nontrain parquet."""
    import numpy as np
    import pyarrow.parquet as pq

    config = json.loads((dataset / "config.json").read_text())
    if config.get("profile") != "kor_gk2a_10min_approach_hindcast_1_3_6h_v4_expanded_context_v1":
        raise ValueError("fixed v4 context profile required")
    events = [e for e in config["events"] if e["split"] == "train"]
    if {e["id"] for e in events} != TRAIN_IDS or len(events) != 14:
        raise ValueError("fixed train allowlist required")
    results = {}
    for event in events:
        if event.get("locked") or datetime.fromisoformat(
            event["start_utc"].replace("Z", "+00:00")
        ).year not in (2020, 2021, 2022):
            raise ValueError("train year guard")
        path = dataset / f"{event['id']}.parquet"
        expected = json.loads((dataset / f"{event['id']}-report.json").read_text())["sha256"]
        if file_sha256(path) != expected:
            raise ValueError("source digest mismatch")
        table = pq.read_table(
            path,
            columns=[
                "longitude",
                "latitude",
                "issue_epoch_seconds",
                "weather_station_distance_km",
                "weather_age_hours",
            ],
        )
        row = {"rows_with_horizon_repeats": len(table), "source_sha256": expected}
        for column in ("weather_station_distance_km", "weather_age_hours"):
            values = table[column].to_numpy()
            valid = values[np.isfinite(values)]
            row[column] = {
                "finite_rows": len(valid),
                "missing_rows": len(values) - len(valid),
                "p05_p50_p95": np.quantile(valid, [0.05, 0.5, 0.95]).tolist()
                if len(valid)
                else None,
                "maximum": float(valid.max()) if len(valid) else None,
            }
        if len(table):
            row["issue_time_min_max_utc"] = [
                datetime.fromtimestamp(float(value), UTC).isoformat()
                for value in (
                    min(table["issue_epoch_seconds"].to_numpy()),
                    max(table["issue_epoch_seconds"].to_numpy()),
                )
            ]
        results[event["id"]] = row
    report = {
        "input_only": True,
        "target_read": False,
        "validation_read": False,
        "calibration_read": False,
        "test_read": False,
        "events": results,
        "note": (
            "Row-weighted descriptive input audit, repeated 1/3/6h rows retained; "
            "no performance metrics"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    write_json(output, report)
    return report


GFS_URL = "https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20220303/18/atmos/gfs.t18z.pgrb2.0p25.f007"
GFS_FIELDS = {
    "UGRD": ("10 m above ground", 2, 2, 10, "m/s"),
    "VGRD": ("10 m above ground", 2, 3, 10, "m/s"),
    "TMP": ("2 m above ground", 0, 0, 2, "K"),
    "RH": ("2 m above ground", 1, 1, 2, "%"),
}
GFS_MAX_BYTES = 16 * 1024 * 1024


def gfs_ranges(payload):
    rows = [line.split(":") for line in payload.decode("ascii").splitlines() if line]
    if not rows or any(len(r) < 6 for r in rows):
        raise ValueError("invalid GFS index")
    offsets = [int(r[1]) for r in rows]
    if offsets != sorted(set(offsets)) or offsets[0] != 0:
        raise ValueError("invalid GFS index offsets")
    result = {}
    for variable, (level, *_rest) in GFS_FIELDS.items():
        selected = [i for i, r in enumerate(rows) if r[3:6] == [variable, level, "7 hour fcst"]]
        if len(selected) != 1 or selected[0] >= len(rows) - 1:
            raise ValueError("exactly one bounded forecast field required")
        i = selected[0]
        if rows[i][2] != "d=2022030318":
            raise ValueError("unexpected GFS reference time")
        result[variable] = (offsets[i], offsets[i + 1] - 1)
    start, end = min(r[0] for r in result.values()), max(r[1] for r in result.values())
    if end - start + 1 + len(payload) > GFS_MAX_BYTES:
        raise ValueError("combined GFS range exceeds 16 MiB ceiling")
    return result, (start, end)


def gfs_metadata(raw, variable):
    if (
        len(raw) < 20
        or raw[:4] != b"GRIB"
        or raw[-4:] != b"7777"
        or raw[7] != 2
        or raw[6] != 0
        or int.from_bytes(raw[8:16], "big") != len(raw)
    ):
        raise ValueError("one complete meteorological GRIB2 field required")
    sections, position = {}, 16
    while position < len(raw) - 4:
        size = int.from_bytes(raw[position : position + 4], "big")
        if size < 5 or position + size > len(raw) - 4:
            raise ValueError("GRIB section boundary")
        section = raw[position : position + size]
        if section[4] in sections:
            raise ValueError("duplicate GRIB section")
        sections[section[4]] = section
        position += size
    if position != len(raw) - 4 or not {1, 3, 4, 5, 6, 7}.issubset(sections):
        raise ValueError("incomplete GRIB2 sections")
    ident, grid, product = (sections[i] for i in (1, 3, 4))
    ref = datetime(int.from_bytes(ident[12:14], "big"), *ident[14:19], tzinfo=UTC)
    if (
        len(ident) != 21
        or int.from_bytes(ident[5:7], "big") != 7
        or ident[11] != 1
        or ref != datetime(2022, 3, 3, 18, tzinfo=UTC)
        or ident[19:21] != b"\x00\x01"
    ):
        raise ValueError("not the fixed NCEP operational forecast reference")
    if len(grid) != 72 or int.from_bytes(grid[12:14], "big") != 0:
        raise ValueError("regular lat/lon grid template 3.0 required")
    _level, category, number, height, unit = GFS_FIELDS[variable]
    if (
        len(product) != 34
        or int.from_bytes(product[7:9], "big") != 0
        or product[9:11] != bytes([category, number])
        or product[17] != 1
        or int.from_bytes(product[18:22], "big") != 7
        or product[22:24] != bytes([103, 0])
        or int.from_bytes(product[24:28], "big") != height
    ):
        raise ValueError("GFS variable/height/lead metadata mismatch")
    if bool(grid[54] & 8):
        raise ValueError("grid-relative GFS wind requires separate rotation")
    return {
        "forecast_reference_time_utc": ref.isoformat(),
        "valid_time_utc": (ref + timedelta(hours=7)).isoformat(),
        "forecast_lead_hours": 7,
        "height_m": height,
        "variable": variable,
        "canonical_unit_from_grib_parameter_table": unit,
        "grid_template": 0,
        "resolution_component_flags": grid[54],
        "wind_axis_basis": "true_east_north",
        "wind_axis_verified": True,
        "ni": int.from_bytes(grid[30:34], "big"),
        "nj": int.from_bytes(grid[34:38], "big"),
        "di_microdegrees": int.from_bytes(grid[63:67], "big"),
        "dj_microdegrees": int.from_bytes(grid[67:71], "big"),
        "grid_sha256": hashlib.sha256(grid).hexdigest(),
        "historical_publication_time_verified": False,
    }


def public_get(url, *, method="GET", byte_range=None):
    headers = {"Range": f"bytes={byte_range[0]}-{byte_range[1]}"} if byte_range else {}
    request = urllib.request.Request(url, headers=headers, method=method)
    limit = byte_range[1] - byte_range[0] + 1 if byte_range else 131072
    try:
        response = urllib.request.build_opener(NoRedirect()).open(request, timeout=30)
    except urllib.error.HTTPError as exc:
        result = {"url": url, "method": method, "http_status": exc.code, "bytes_read": 0}
        exc.close()
        return result, None
    with response:
        payload = b"" if method == "HEAD" else response.read(limit + 1)
        result = {
            "url": url,
            "method": method,
            "http_status": response.status,
            "bytes_read": len(payload),
            "content_length": response.headers.get("Content-Length"),
            "content_range": response.headers.get("Content-Range"),
            "last_modified": response.headers.get("Last-Modified"),
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
        }
    if byte_range:
        start, end = byte_range
        if (
            result["http_status"] != 206
            or len(payload) != limit
            or not (result["content_range"] or "").startswith(f"bytes {start}-{end}/")
        ):
            raise ValueError("exact public byte range was not honored")
    elif result["http_status"] != 200 or len(payload) > limit:
        raise ValueError("invalid public response")
    return result, payload


def gfs_probe(output, fetcher=public_get):
    output.mkdir(parents=True, exist_ok=False)
    plan = {
        "experiment": "uljin_train_gfs_access_probe_v1",
        "url": GFS_URL,
        "max_requests": 3,
        "max_total_response_bytes": GFS_MAX_BYTES,
        "event": "uljin_2022",
        "cycle_utc": "2022-03-03T18:00:00Z",
        "valid_time_utc": "2022-03-04T01:00:00Z",
        "lead_hours": 7,
        "fields": GFS_FIELDS,
        "bbox": [128.8, 36.7, 129.8, 37.7],
        "sequence": ["GET index", "HEAD global file", "GET combined exact field range"],
        "spatial_subsetting": "local only; HTTP Range selects fields, not geographic pixels",
        "stop_if_404": True,
        "no_retries": True,
        "operational_use": False,
        "historical_publication_time_verified": False,
        "documentation": [
            "https://registry.opendata.aws/noaa-gfs-bdp-pds/",
            "https://www.ncei.noaa.gov/products/weather-climate-models/global-forecast",
            "https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table3-3.shtml",
        ],
        "license": (
            "NOAA NODD open use; attribution requested; no implied NOAA endorsement; "
            "label derived products"
        ),
    }
    write_json(output / "plan.json", plan)
    report = {
        "plan_sha256": file_sha256(output / "plan.json"),
        "requests": [],
        "source_code_sha256": file_sha256(Path(__file__)),
        "operational_use": False,
        "historical_publication_time_verified": False,
    }
    try:
        index_result, index = fetcher(GFS_URL + ".idx")
        report["requests"].append(index_result)
        if index is None:
            report["status"] = "historical_index_unavailable"
            return report
        (output / "response.idx").write_bytes(index)
        report["index_sha256"] = file_sha256(output / "response.idx")
        ranges, combined = gfs_ranges(index)
        report["ranges"], report["combined_range"] = ranges, combined
        head, _ = fetcher(GFS_URL, method="HEAD")
        report["requests"].append(head)
        if head["http_status"] != 200:
            report["status"] = "historical_global_file_unavailable"
            return report
        report["full_global_file_bytes"] = int(head["content_length"])
        transfer, raw = fetcher(GFS_URL, byte_range=combined)
        report["requests"].append(transfer)
        if raw is None:
            report["status"] = "field_range_unavailable"
            return report
        report["fields"] = {}
        for variable, (start, end) in ranges.items():
            field = raw[start - combined[0] : end - combined[0] + 1]
            metadata = gfs_metadata(field, variable)
            path = output / f"{variable}.grib2"
            path.write_bytes(field)
            metadata.update(path=path.name, bytes=len(field), sha256=file_sha256(path))
            report["fields"][variable] = metadata
        if len({m["grid_sha256"] for m in report["fields"].values()}) != 1:
            raise ValueError("GFS field grids differ")
        report["status"] = "four_field_metadata_verified"
        return report
    except Exception as exc:
        report["status"] = "failed"
        report["exception_type"] = type(exc).__name__
        return report
    finally:
        report["actual_requests"] = len(report["requests"])
        report["response_bytes_read"] = sum(r["bytes_read"] for r in report["requests"])
        write_json(output / "report.json", report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    acquire = sub.add_parser("acquire")
    acquire.add_argument("--output", type=Path, required=True)
    audit = sub.add_parser("audit-existing")
    audit.add_argument("--dataset", type=Path, required=True)
    audit.add_argument("--output", type=Path, required=True)
    public = sub.add_parser("gfs-probe")
    public.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "acquire":
            result = run(args.output, read_server_key())
            print(
                json.dumps(
                    {
                        "requests": result["actual_http_requests"],
                        "records": [
                            {
                                "id": r["id"],
                                "status": r["status"],
                                "http_status": r.get("http_status"),
                            }
                            for r in result["records"]
                        ],
                    }
                )
            )
        elif args.command == "audit-existing":
            result = diagnose_existing(args.dataset, args.output)
            print(json.dumps({"events_audited": len(result["events"]), "target_read": False}))
        else:
            result = gfs_probe(args.output)
            print(json.dumps({"status": result["status"], "requests": result["actual_requests"]}))
    except Exception as exc:
        # Never print exception text, request URLs, environment, or credentials.
        print(json.dumps({"status": "failed", "exception_type": type(exc).__name__}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
