"""검증된 6시각 KIML 연구 자료에 끝의 2시각만 추가한다. 위험 추론이 아니다."""

import argparse
import json
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from bonghwa_training.download import file_sha256
from bonghwa_training.kiml_point_forecast import (
    VARIABLES,
    _write_json,
    build_plan,
    contains_sensitive,
    fetch_once,
    iso,
    parse_point_csv,
    write_private,
)


def extension_plan(base_path):
    base_path = Path(base_path)
    base = json.loads(base_path.read_text())
    plan_path = base_path.parent / "plan.json"
    if file_sha256(plan_path) != base["plan_sha256"]:
        raise ValueError("base plan hash mismatch")
    old_plan = json.loads(plan_path.read_text())
    expected = build_plan(
        datetime.fromisoformat(old_plan["requested_reference_time_utc"]),
        datetime.fromisoformat(old_plan["asof_utc"]),
        lon=old_plan["requested_longitude"],
        lat=old_plan["requested_latitude"],
    )
    if old_plan != expected or not base["complete"] or len(base["records"]) != 24:
        raise ValueError("complete canonical 24-request base required")
    for record, spec in zip(base["records"], old_plan["requests"], strict=True):
        if record["id"] != spec["id"] or record["status"] != "validated_point_csv":
            raise ValueError("base request identity or status mismatch")
        name = record["raw_file"]
        if Path(name).name != name:
            raise ValueError("invalid raw filename")
        raw = base_path.parent / name
        if file_sha256(raw) != record["source_sha256"]:
            raise ValueError("base raw hash mismatch")
        if parse_point_csv(raw.read_bytes(), spec)["grid"] != base["grid"]:
            raise ValueError("base grid mismatch")
    final = datetime.fromisoformat(old_plan["requests"][-1]["requested_valid_time_utc"])
    issue = datetime.fromisoformat(old_plan["requested_reference_time_utc"])
    original_asof = datetime.fromisoformat(old_plan["asof_utc"])
    requests = []
    for delta in (1, 2):
        valid = final + timedelta(hours=delta)
        hf = int((valid - issue).total_seconds() / 3600)
        if not 1 <= hf <= 48:
            raise ValueError("extension exceeds 48-hour forecast range")
        for variable in VARIABLES:
            spec = dict(
                next(s for s in old_plan["requests"] if s["requested_variable"] == variable)
            )
            spec["parameters_without_auth"] = dict(spec["parameters_without_auth"], hf=str(hf))
            spec.update(
                id=f"kiml-{issue:%Y%m%dT%HZ}-{variable.lower()}-h{hf}",
                requested_valid_time_utc=iso(valid),
                requested_lead_from_cycle_hours=hf,
                requested_lead_from_asof_hours=(valid - original_asof).total_seconds() / 3600,
            )
            requests.append(spec)
    return {
        "purpose": "two_additional_hours_for_seven_endpoint_scenario",
        "base_report_path": str(base_path.resolve()),
        "base_report_sha256": file_sha256(base_path),
        "base_plan_sha256": file_sha256(plan_path),
        "source_code_sha256": file_sha256(Path(__file__)),
        "grid": base["grid"],
        "max_http_attempts": 8,
        "operational_use": False,
        "holdout_2025_accessed": False,
        "requests": requests,
    }


def run(base_path, output, key, *, fetcher=fetch_once, sleeper=time.sleep):
    if not key or len(key) < 8 or any(c.isspace() for c in key):
        raise ValueError("private environment credential required")
    plan = extension_plan(base_path)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    _write_json(output / "plan.json", plan, key)
    report = {
        "purpose": plan["purpose"],
        "plan_sha256": file_sha256(output / "plan.json"),
        "base_report_sha256": plan["base_report_sha256"],
        "operational_use": False,
        "source_reference_confirmed": False,
        "wind_axis_basis_verified": False,
        "records": [],
    }
    for i, spec in enumerate(plan["requests"]):
        if i:
            sleeper(1)
        try:
            result, payload = fetcher(spec, key)
            if contains_sensitive(json.dumps(result).encode(), key) or (
                payload is not None and contains_sensitive(payload, key)
            ):
                result, payload = {"status": "sensitive_response_rejected"}, None
        except Exception:
            result, payload = {"status": "request_failed_without_diagnostics"}, None
        record = {**spec, "transport": result, "status": result["status"]}
        if payload is not None:
            name = spec["id"] + ".csv"
            write_private(output / name, payload)
            record.update(raw_file=name, source_sha256=file_sha256(output / name))
            try:
                parsed = parse_point_csv(payload, spec)
                if parsed["grid"] != plan["grid"]:
                    raise ValueError("extension grid differs from base")
                fetched = datetime.fromisoformat(result["retrieved_at_utc"])
                valid = datetime.fromisoformat(spec["requested_valid_time_utc"])
                if fetched.tzinfo is None or valid <= fetched:
                    raise ValueError("extension must be future at retrieval")
                record.update(
                    parsed=parsed, retrieved_at_utc=iso(fetched), status="validated_point_csv"
                )
            except (ValueError, KeyError, TypeError):
                record["status"] = "csv_grid_or_time_validation_failed"
        report["records"].append(record)
        if record["status"] != "validated_point_csv":
            break
    report["complete"] = len(report["records"]) == 8 and all(
        r["status"] == "validated_point_csv" for r in report["records"]
    )
    report["finished_at_utc"] = datetime.now(UTC).isoformat()
    _write_json(output / "report.json", report, key)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.base_report, args.output, os.environ.get("KMA_APIHUB_AUTH_KEY", ""))
    except Exception:
        print(json.dumps({"status": "extension_failed", "detail": "unsafe diagnostics suppressed"}))
        return 1
    print(json.dumps({"complete": report["complete"], "records": len(report["records"])}))
    return 0 if report["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
