"""경보 포함 과거 재생을 분석 큐와 Qwen3에 연결하고 수치 추론 직전에서 멈춘다."""

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx

from bonghwajigi.common.config import Settings
from bonghwajigi.integration.service import (
    GenerationClient,
    IntegrationError,
    build_pre_inference,
    make_prompt,
    prepare_evidence,
    validate_model_output,
)
from bonghwajigi.retrieval.web_search import plain_text

QWEN_REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def prepare_scenario(template, scenario_id):
    collected = datetime.now(UTC).isoformat()
    documents = []
    for item in template["source_definitions"]:
        source = {**item["source"], "collected_at": collected}
        documents.append(
            {
                "mode": "simulation",
                "scenario_id": scenario_id,
                "document_id": item["document_id"],
                "revision": 1,
                "origin": item["origin"],
                "source_kind": item["source_kind"],
                "text": item["text"],
                "source": source,
                "valid_from": source["published_at"],
            }
        )
    return {
        **template,
        "scenario_id": scenario_id,
        "documents": documents,
        "official_alerts": [
            {**item, "scenario_id": scenario_id} for item in template["official_alerts"]
        ],
    }


def verify_official_sources(scenario):
    checks = []
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        for item in scenario["source_definitions"]:
            response = client.get(item["source"]["url"])
            response.raise_for_status()
            if item["fetch_must_contain"] not in plain_text(response.text):
                raise IntegrationError("OFFICIAL_SOURCE_CONTENT_CHANGED")
            checks.append(
                {
                    "document_id": item["document_id"],
                    "requested_url": item["source"]["url"],
                    "fetched_url": str(response.url),
                    "http_status": response.status_code,
                    "html_sha256": hashlib.sha256(response.content).hexdigest(),
                    "checked_at": datetime.now(UTC).isoformat(),
                    "check": "known_official_publication_contains_expected_text",
                    "semantic_or_policy_approval": False,
                }
            )
    return checks


def retrieve_via_queue(scenario, settings, base_url):
    with httpx.Client(
        base_url=base_url,
        timeout=15,
        headers={"Authorization": "Bearer " + settings.service_token.get_secret_value()},
    ) as client:

        def submit(path, data):
            response = client.post(path, json=data)
            response.raise_for_status()
            return response.json()

        def wait(job):
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                response = client.get(
                    f"/internal/v1/scenarios/{scenario['scenario_id']}/analysis-jobs/{job['job_id']}"
                )
                response.raise_for_status()
                result = response.json()
                if result["status"] in {"indexed", "ready_for_qwen"}:
                    return result
                if result["status"] == "failed":
                    raise IntegrationError("ANALYSIS_FAILED_" + str(result["error_code"]))
                time.sleep(0.5)
            raise IntegrationError("ANALYSIS_TIMEOUT")

        for document in scenario["documents"]:
            wait(submit("/internal/v1/retrieval-documents", document))
        document = scenario["documents"][0]
        event = {
            "mode": "simulation",
            "scenario_id": scenario["scenario_id"],
            "event_id": "yeongdeok-historical-observation",
            "origin": "historical_replay",
            "queue": "analysis",
            "payload": {
                "disaster_type": "wildfire",
                "text": document["text"],
                "source": document["source"],
                "as_of": scenario["as_of"],
                "search_query": scenario["search_query"],
            },
        }
        return wait(submit("/internal/v1/scenario-events", event))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:18000")
    parser.add_argument(
        "--scenario", type=Path, default=Path("data/scenarios/yeongdeok-integration.json")
    )
    parser.add_argument(
        "--feature-report", type=Path, default=Path("training/reports/dataset-report.json")
    )
    parser.add_argument("--qwen-revision", default=QWEN_REVISION)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    settings = Settings()
    gpu_token = settings.embedding_service_token
    if not settings.service_token or not gpu_token:
        parser.exit(2, "분석 API 토큰과 GPU 서비스 토큰 설정이 필요합니다.\n")
    run_id = "yeongdeok-" + uuid4().hex
    directory = args.output_dir or Path("data/artifacts") / run_id
    directory.mkdir(parents=True, exist_ok=False)
    template = json.loads(args.scenario.read_text())
    scenario = prepare_scenario(template, run_id)
    write_json(directory / "scenario-input.json", scenario)
    checks = verify_official_sources(scenario)
    write_json(directory / "source-checks.json", checks)
    job = retrieve_via_queue(scenario, settings, args.base_url)
    write_json(directory / "retrieval-handoff.json", job)
    sources, alerts = prepare_evidence(job["result"], scenario)
    prompt = make_prompt(sources, alerts, scenario["area_name"])
    write_json(directory / "generation-request.json", {"text": prompt, "max_output_tokens": 512})
    generator = GenerationClient(
        settings.gpu_base_url, gpu_token, settings.qwen_model, args.qwen_revision
    )
    try:
        generation = generator.generate(prompt)
    finally:
        generator.close()
    # 검증 실패 시에도 생성 원문을 남겨 성공으로 포장하지 않는다.
    write_json(directory / "generation-response.json", generation)
    output = validate_model_output(generation["text"], sources)
    report = json.loads(args.feature_report.read_text())
    feature_contract = {
        "source": str(args.feature_report),
        "source_sha256": hashlib.sha256(args.feature_report.read_bytes()).hexdigest(),
        "feature_names": report["feature_names"],
        "target": report["target"],
        "interpretation": "next daily satellite fire observation; not personal impact",
    }
    result = build_pre_inference(
        job["result"], scenario, sources, alerts, generation, output, feature_contract
    )
    write_json(directory / "pre-inference.json", result)
    write_json(
        directory / "run-metadata.json",
        {
            "finished_at": datetime.now(UTC).isoformat(),
            "scenario_id": run_id,
            "analysis_job_id": job["job_id"],
            "status": "integration_completed",
            "web_search": job["result"]["web_search"],
            "model_output_validation": "schema_and_exact_evidence_quotes_passed",
            "xgboost_invoked": False,
            "inference_gate": result["inference_gate"]["status"],
        },
    )
    print(
        json.dumps(
            {
                "output_dir": str(directory),
                "stage": result["stage"],
                "official_alerts": len(alerts),
                "sources": len(sources),
                "facts": len(output["facts"]),
                "generation": {
                    key: generation[key]
                    for key in ("model", "input_tokens", "output_tokens", "elapsed_ms")
                },
                "inference_gate": result["inference_gate"]["status"],
                "xgboost_invoked": False,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
