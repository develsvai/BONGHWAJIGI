import json
import shutil
from pathlib import Path

import pytest

from bonghwa_training import kiml_forecast_extend as extend

SOURCE = Path(__file__).parents[1] / "reports/kiml-forecast-access-20261101/current-forecast"
KEY = "test-private-key"


@pytest.fixture
def base(tmp_path):
    destination = tmp_path / "base"
    shutil.copytree(SOURCE, destination)
    return destination / "report.json"


def test_extension_requests_only_new_two_hours_and_rejects_tampering(base):
    plan = extend.extension_plan(base)
    assert len(plan["requests"]) == 8
    assert {s["parameters_without_auth"]["hf"] for s in plan["requests"]} == {"11", "12"}
    assert plan["requests"][-1]["requested_valid_time_utc"] == "2026-11-01T00:00:00+00:00"
    raw = next(base.parent.glob("*.csv"))
    raw.write_bytes(raw.read_bytes() + b"extra")
    with pytest.raises(ValueError, match="hash mismatch"):
        extend.extension_plan(base)


def good_fetch(spec, key):
    values = {"U10": 3, "V10": 4, "T2": 280, "RH2": 20}
    value = values[spec["requested_variable"]]
    payload = (
        "req_lon,req_lat,lvl,ix,iy,lon,lat,value\n"
        f"129.300003,37,-1,873,664,129.293854,36.991207,{value}\n"
    ).encode()
    return {"status": "response_received", "retrieved_at_utc": "2026-10-31T17:00:00Z"}, payload


def test_extension_preserves_plan_before_fetch_and_completes_eight(base, tmp_path):
    output = tmp_path / "output"
    calls = []

    def fetch(spec, key):
        assert (output / "plan.json").exists()
        calls.append(spec["id"])
        return good_fetch(spec, key)

    result = extend.run(base, output, KEY, fetcher=fetch, sleeper=lambda _: None)
    assert result["complete"] and len(set(calls)) == 8
    assert result["wind_axis_basis_verified"] is False
    assert len(list(output.glob("*.csv"))) == 8


@pytest.mark.parametrize("failure", ["forbidden", "rate_limit", "secret", "grid", "late"])
def test_failed_extension_stops_after_one_and_never_fills_missing(base, tmp_path, failure):
    calls = []

    def fetch(spec, key):
        calls.append(spec)
        if failure == "forbidden":
            return {"status": "http_error", "http_status": 403}, None
        if failure == "rate_limit":
            return {"status": "rate_limited", "http_status": 429}, None
        result, payload = good_fetch(spec, key)
        if failure == "secret":
            payload += key.encode()
        if failure == "grid":
            payload = payload.replace(b"873,664", b"872,664")
        if failure == "late":
            result["retrieved_at_utc"] = "2026-11-02T00:00:00Z"
        return result, payload

    output = tmp_path / failure
    result = extend.run(base, output, KEY, fetcher=fetch, sleeper=lambda _: None)
    assert not result["complete"] and len(calls) == 1
    assert KEY not in (output / "report.json").read_text()
    assert not json.loads((output / "report.json").read_text())["wind_axis_basis_verified"]
