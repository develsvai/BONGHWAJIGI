import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="XGBoost 실행 기반. 학습·추론은 미구현입니다.")
    parser.add_argument("--check", action="store_true", help="모델 없이 설치 상태만 확인")
    args = parser.parse_args()
    if args.check:
        print(json.dumps({"component": "ml", "status": "not_implemented"}))
        return
    parser.exit(2, "예측 목표·학습 자료·검증된 모델을 C1~C5에서 준비해야 합니다.\n")


if __name__ == "__main__":
    main()
