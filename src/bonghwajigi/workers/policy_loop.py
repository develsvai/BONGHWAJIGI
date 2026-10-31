import argparse
import logging
import time

from bonghwajigi.common.config import Settings
from bonghwajigi.db.session import session_factory
from bonghwajigi.policy.integration import ConfiguredGenerator, integrate_once
from bonghwajigi.policy.service import evaluate_once


def main():
    parser = argparse.ArgumentParser(
        description="개인별 정책 갱신 또는 Qwen 통합 DB 대기열을 처리한다."
    )
    parser.add_argument("--mode", choices=["plans", "integrations"], default="plans")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    if not settings.policy_enabled or settings.mode != "simulation":
        parser.exit(2, "simulation 정책 루프 설정이 필요합니다.\n")
    if args.mode == "integrations" and not settings.policy_qwen_enabled:
        parser.exit(2, "Qwen 정책 통합 설정이 비활성화되어 있습니다.\n")
    sessions = session_factory(settings)
    try:
        while True:
            try:
                if args.mode == "plans":
                    result = evaluate_once(sessions, settings.policy_check_seconds)
                else:
                    result = integrate_once(sessions, ConfiguredGenerator(settings))
                if args.once:
                    print({"processed": result})
                    return
            except Exception:
                logging.error("POLICY_LOOP_FAILED")
                if args.once:
                    raise SystemExit(1) from None
            time.sleep(settings.policy_poll_seconds)
    finally:
        sessions.kw["bind"].dispose()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
