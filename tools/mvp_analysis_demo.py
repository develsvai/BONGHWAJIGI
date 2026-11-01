"""기존 GPU를 통해 임베딩·인터넷 검색·Qwen 통합까지 실제 작업 큐를 점검한다."""

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx
from mvp_demo import AREA, private_json, wait

from bonghwajigi.common.config import Settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("/accounts"))
    args = parser.parse_args()
    settings = Settings()
    if settings.mode != "simulation":
        parser.exit(2, "simulation 전용 시연입니다.\n")
    scenario = "mvp-analysis-" + uuid4().hex[:16]
    moment = datetime.now(UTC)
    source = {
        "title": "실제 사건이 아닌 합성 산불 관측",
        "url": "https://example.invalid/synthetic-wildfire",
        "published_at": (moment - timedelta(minutes=1)).isoformat(),
        "collected_at": moment.isoformat(),
        "verified": False,
    }
    observation = (
        "[합성 시연] 산불 관측을 접수하고 관련 자료를 정리한 상황이다. 실제 재난 발령이 아니다."
    )
    with httpx.Client(
        base_url="http://127.0.0.1:8000",
        timeout=20,
        headers={"Authorization": "Bearer " + settings.service_token.get_secret_value()},
    ) as client:

        def submit(path, body):
            response = client.post(path, json=body)
            if response.status_code != 202:
                raise RuntimeError("분석 입력 HTTP " + str(response.status_code))
            return response.json()["job_id"]

        def job(identifier):
            response = client.get(f"/internal/v1/scenarios/{scenario}/analysis-jobs/{identifier}")
            response.raise_for_status()
            value = response.json()
            if value["status"] == "failed":
                raise RuntimeError("분석 작업 실패: " + str(value["error_code"]))
            return value if value["status"] in {"indexed", "ready_for_qwen"} else None

        document = submit(
            "/internal/v1/retrieval-documents",
            {
                "mode": "simulation",
                "scenario_id": scenario,
                "document_id": "synthetic-manual",
                "origin": "synthetic",
                "text": observation,
                "source": source,
                "valid_from": source["published_at"],
            },
        )
        indexed = wait(lambda: job(document), "실제 임베딩 인덱싱", seconds=180)
        event = submit(
            "/internal/v1/scenario-events",
            {
                "mode": "simulation",
                "scenario_id": scenario,
                "event_id": "observation-1",
                "origin": "synthetic",
                "queue": "analysis",
                "payload": {
                    "text": observation,
                    "search_query": "산불",
                    "as_of": moment.isoformat(),
                    "source": source,
                    "policy_context": {
                        "incident_id": "analysis-fire",
                        "incident_revision": 1,
                        "area": AREA,
                        "expires_at": (moment + timedelta(minutes=30)).isoformat(),
                    },
                },
            },
        )
        retrieval = wait(lambda: job(event), "저장 자료와 인터넷 검색", seconds=180)

        def integrated():
            response = client.get(f"/internal/v1/policy/scenarios/{scenario}/integrations/{event}")
            response.raise_for_status()
            value = response.json()
            if value["status"] == "failed":
                raise RuntimeError("통합 실패: " + str(value["error_code"]))
            return value if value["status"] == "complete" else None

        integration = wait(integrated, "실제 Qwen 통합", seconds=360)
        report = {
            "scenario_id": scenario,
            "mode": "simulation",
            "origin": "합성 관측과 실제 검색 결과",
            "verified_at": datetime.now(UTC).isoformat(),
            "document_status": indexed["status"],
            "retrieval": retrieval,
            "integration": integration,
            "actual_prediction_connected": False,
        }
        output = args.output_dir / (scenario + "-report.json")
        private_json(output, report)
        print("실제 임베딩·검색·Qwen 검증 완료:", output)


if __name__ == "__main__":
    main()
