import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="기관 수집기 scaffold. 실제 수집 기능은 미구현입니다."
    )
    parser.add_argument("--check", action="store_true", help="외부 호출 없이 설치 상태만 확인")
    args = parser.parse_args()
    if args.check:
        print(json.dumps({"component": "ingestion", "status": "not_implemented"}))
        return
    parser.exit(2, "수집 어댑터가 없습니다. B2/B3에서 자료 계약과 수집기를 구현해야 합니다.\n")


if __name__ == "__main__":
    main()
