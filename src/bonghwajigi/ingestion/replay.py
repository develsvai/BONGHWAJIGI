import argparse
import json
from pathlib import Path

from pydantic import ValidationError

from bonghwajigi.contracts.analysis import AnalysisInput
from bonghwajigi.contracts.scenarios import ScenarioEvent


def main() -> None:
    parser = argparse.ArgumentParser(description="MVP 시나리오 JSONL의 입력 계약을 검사합니다.")
    parser.add_argument("file", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--submit", action="store_true", help="내부 이벤트 API에 실제 전송")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    if args.check == args.submit:
        parser.exit(2, "--check 또는 --submit 중 하나를 선택하세요.\n")
    count = 0
    try:
        with args.file.open(encoding="utf-8") as source:
            for line in source:
                if line.strip():
                    event = ScenarioEvent.model_validate_json(line)
                    if event.queue == "analysis":
                        AnalysisInput.model_validate(event.payload)
                    if args.submit:
                        import httpx

                        from bonghwajigi.common.config import Settings

                        settings = Settings()
                        if not settings.service_token:
                            parser.exit(2, "내부 서비스 토큰이 필요합니다.\n")
                        response = httpx.post(
                            args.base_url.rstrip("/") + "/internal/v1/scenario-events",
                            json=event.model_dump(mode="json"),
                            timeout=15,
                            headers={
                                "Authorization": "Bearer "
                                + settings.service_token.get_secret_value()
                            },
                        )
                        if response.status_code != 202:
                            parser.exit(2, f"전송 실패 HTTP {response.status_code}.\n")
                        print(json.dumps(response.json(), ensure_ascii=False))
                    count += 1
    except (OSError, ValidationError):
        parser.exit(
            2, "시나리오 파일 또는 입력 계약 오류입니다. 원문은 로그에 출력하지 않습니다.\n"
        )
    print(json.dumps({"mode": "simulation", "validated_events": count, "submitted": args.submit}))


if __name__ == "__main__":
    main()
