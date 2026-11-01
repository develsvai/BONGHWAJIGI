"""시나리오 수신→실제 분석 큐→임베딩·인터넷 검색→Qwen 직전 결과를 확인한다."""

import argparse
import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx

from bonghwajigi.common.config import Settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:18000")
    parser.add_argument("--search-query", default="현황")
    parser.add_argument("--report", type=Path, default=Path("data/artifacts/analysis-demo.json"))
    args = parser.parse_args()
    settings = Settings()
    if not settings.service_token:
        parser.exit(2, "내부 API 서비스 토큰 설정이 필요합니다.\n")
    scenario = "demo-" + uuid4().hex
    moment = datetime.now(UTC)
    source = {
        "title": "합성 시연 자료",
        "url": "https://example.invalid/scenario",
        "published_at": (moment - timedelta(minutes=1)).isoformat(),
        "collected_at": moment.isoformat(),
        "verified": False,
    }
    document = {
        "mode": "simulation",
        "scenario_id": scenario,
        "document_id": "stored-demo",
        "origin": "synthetic",
        "text": "[합성 시연 자료] 산불 관측 문서의 출처와 발표 시각을 정리하는 예제입니다.",
        "source": source,
        "valid_from": source["published_at"],
    }
    event = {
        "mode": "simulation",
        "scenario_id": scenario,
        "event_id": "demo-observation",
        "origin": "synthetic",
        "queue": "analysis",
        "payload": {
            "text": "[합성 시연] 산불 관측 입력입니다. 저장한 자료와 관련 인터넷 뉴스를 찾습니다.",
            "search_query": args.search_query,
            "as_of": moment.isoformat(),
            "source": source,
        },
    }
    with httpx.Client(
        base_url=args.base_url,
        timeout=15,
        headers={"Authorization": "Bearer " + settings.service_token.get_secret_value()},
    ) as client:

        def submit(path, body):
            response = client.post(path, json=body)
            if response.status_code != 202:
                raise RuntimeError(f"수신 실패: HTTP {response.status_code}")
            return response.json()

        def wait(job):
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                response = client.get(
                    f"/internal/v1/scenarios/{scenario}/analysis-jobs/{job['job_id']}"
                )
                response.raise_for_status()
                data = response.json()
                if data["status"] in {"indexed", "ready_for_qwen"}:
                    return data
                if data["status"] == "failed":
                    raise RuntimeError("분석 실패: " + str(data["error_code"]))
                time.sleep(0.5)
            raise RuntimeError("분석 결과 대기 시간 초과")

        indexed = wait(submit("/internal/v1/retrieval-documents", document))
        accepted = submit("/internal/v1/scenario-events", event)
        duplicate = submit("/internal/v1/scenario-events", event)
        assert accepted["job_id"] == duplicate["job_id"] and duplicate["duplicate"]
        result = wait(accepted)
        assert result["result"]["qwen_invoked"] is False
        assert result["result"]["embedding"]["dimensions"] == 1024
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "mode": "simulation",
                    "scenario_id": scenario,
                    "document_status": indexed["status"],
                    "job_id": accepted["job_id"],
                    "status": result["status"],
                    "duplicate_idempotent": True,
                    "web_search": result["result"]["web_search"],
                    "evidence_count": len(result["result"]["retrieved_evidence"]),
                    "qwen_invoked": False,
                    "report": str(args.report),
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
