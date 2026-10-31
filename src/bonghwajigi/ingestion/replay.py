import argparse
import json
from pathlib import Path

from pydantic import ValidationError

from bonghwajigi.contracts.scenarios import ScenarioEvent


def main() -> None:
    parser = argparse.ArgumentParser(description="MVP 시나리오 JSONL의 입력 계약을 검사합니다.")
    parser.add_argument("file", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.exit(2, "실제 전송은 미구현입니다. --check로 입력 검사만 수행하세요.\n")
    count = 0
    try:
        with args.file.open(encoding="utf-8") as source:
            for line in source:
                if line.strip():
                    ScenarioEvent.model_validate_json(line)
                    count += 1
    except (OSError, ValidationError):
        parser.exit(
            2, "시나리오 파일 또는 입력 계약 오류입니다. 원문은 로그에 출력하지 않습니다.\n"
        )
    print(json.dumps({"mode": "simulation", "validated_events": count, "submitted": False}))


if __name__ == "__main__":
    main()
