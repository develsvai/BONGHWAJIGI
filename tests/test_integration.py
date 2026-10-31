import copy
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from bonghwajigi.integration.service import (
    GenerationClient,
    IntegrationError,
    build_pre_inference,
    prepare_evidence,
    validate_model_output,
)


@pytest.fixture
def inputs():
    template = json.loads(Path("data/scenarios/yeongdeok-integration.json").read_text())
    scenario_id = "integration-test"
    documents = [
        {
            **{key: item[key] for key in ("document_id", "text", "source_kind", "origin")},
            "scenario_id": scenario_id,
            "source": {**item["source"], "collected_at": datetime.now(UTC).isoformat()},
        }
        for item in template["source_definitions"]
    ]
    scenario = {
        "scenario_id": scenario_id,
        "area_name": template["area_name"],
        "documents": documents,
        "official_alerts": [
            {**item, "scenario_id": scenario_id} for item in template["official_alerts"]
        ],
    }
    handoff = {
        "mode": "simulation",
        "stage": "ready_for_qwen",
        "qwen_invoked": False,
        "scenario_id": scenario_id,
        "event": {"as_of": template["as_of"]},
        "retrieved_evidence": [],
    }
    return handoff, scenario


def test_alert_survives_empty_semantic_retrieval_and_model_cannot_modify_it(inputs):
    handoff, scenario = inputs
    sources, alerts = prepare_evidence(handoff, scenario)
    assert len(sources) == 2 and alerts[0]["severity"] == "심각"
    assert alerts[0]["original_sms_available"] is False
    good = {
        "summary": "당시 경북 지역에 산불 확산과 주민 대피가 보고됐다.",
        "facts": [
            {
                "evidence_id": sources[0]["evidence_id"],
                "quote": "주민 대피와 전기·통신·도로 장애가 보고됐다.",
            }
        ],
    }
    result = validate_model_output(json.dumps(good), sources)
    assert result == good
    good["official_alerts"] = [{"severity": "안전"}]
    with pytest.raises(IntegrationError, match="INVALID_MODEL_JSON"):
        validate_model_output(json.dumps(good), sources)


@pytest.mark.parametrize("mutation", ["cross_scenario", "future", "future_alert", "fake_excerpt"])
def test_reject_wrong_scenario_future_or_unsupported_alert(inputs, mutation):
    handoff, scenario = copy.deepcopy(inputs)
    if mutation == "cross_scenario":
        scenario["documents"][0]["scenario_id"] = "other"
    elif mutation == "future":
        scenario["documents"][0]["source"]["published_at"] = "2025-03-28T00:00:00Z"
    elif mutation == "future_alert":
        scenario["official_alerts"][0]["issued_at"] = "2025-03-28T00:00:00Z"
    else:
        scenario["official_alerts"][0]["original_excerpt"] = "원문에 없는 경보"
    with pytest.raises(IntegrationError):
        prepare_evidence(handoff, scenario)


@pytest.mark.parametrize(
    "failure", ["unknown_source", "invented_quote", "numeric_feature", "truncated"]
)
def test_reject_unsupported_facts_numeric_generation_and_incomplete_json(inputs, failure):
    sources, _ = prepare_evidence(*inputs)
    body = {
        "summary": "당시 산불 기록이다.",
        "facts": [
            {
                "evidence_id": sources[0]["evidence_id"],
                "quote": "주민 대피와 전기·통신·도로 장애가 보고됐다.",
            }
        ],
    }
    if failure == "unknown_source":
        body["facts"][0]["evidence_id"] = "unknown"
    if failure == "invented_quote":
        body["facts"][0]["quote"] = "현재 화재 도달 확률은 99퍼센트다."
    if failure == "numeric_feature":
        body["numeric_features"] = {"vs": 25}
    raw = json.dumps(body)
    if failure == "truncated":
        raw = raw[:-5]
    with pytest.raises(IntegrationError):
        validate_model_output(raw, sources)


def test_news_only_integration_never_becomes_xgboost_input(inputs):
    handoff, scenario = inputs
    sources, alerts = prepare_evidence(handoff, scenario)
    generation = {
        "model": "qwen-test",
        "revision": "fixed",
        "input_tokens": 100,
        "output_tokens": 80,
        "elapsed_ms": 123.0,
    }
    result = build_pre_inference(
        handoff,
        scenario,
        sources,
        alerts,
        generation,
        {"summary": "당시 산불 상황 기록이다.", "facts": []},
        {"feature_names": ["vs", "th", "PrevFireMask"], "target": "fire_next_day"},
    )
    gate = result["inference_gate"]
    assert gate["status"] == "blocked" and gate["xgboost_invoked"] is False
    assert gate["numeric_features"] == {"vs": None, "th": None, "PrevFireMask": None}
    assert gate["probability"] is None and gate["personal_response_level"] is None
    assert result["official_alerts"] == alerts
    assert result["integration"]["summary_review_status"] == "not_reviewed"


@pytest.mark.parametrize("failure", [None, "revision", "truncated", "budget", "http", "type"])
def test_generation_response_requires_fixed_model_and_complete_token_budget(failure):
    body = {
        "model": "qwen-test",
        "revision": "fixed",
        "text": "{}",
        "input_tokens": 100,
        "output_tokens": 10,
        "elapsed_ms": 100.0,
    }
    if failure == "revision":
        body["revision"] = "changed"
    if failure == "truncated":
        body["output_tokens"] = 512
    if failure == "budget":
        body["input_tokens"] = 4000
    if failure == "type":
        body = []
    paths = []

    def respond(request):
        paths.append(request.url.path)
        return httpx.Response(503 if failure == "http" else 200, json=body)

    client = GenerationClient(
        "http://test", SecretStr("test-only"), "qwen-test", "fixed", httpx.MockTransport(respond)
    )
    try:
        if failure is None:
            assert client.generate("과거 산불 자료") == body
        else:
            code = "GENERATION_OUTPUT_LIMIT_REACHED" if failure == "truncated" else None
            with pytest.raises(IntegrationError, match=code):
                client.generate("과거 산불 자료")
    finally:
        client.close()
    assert paths == ["/internal/v1/generate"]
