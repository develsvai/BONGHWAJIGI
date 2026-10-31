"""로컬 API·분석 워커·outbox를 함께 시작하고 종료 시 자식 프로세스를 정리한다."""

import argparse
import signal
import subprocess
import sys
import time
from pathlib import Path

from bonghwajigi.common.config import Settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=18000)
    args = parser.parse_args()
    if not Settings().analysis_enabled:
        parser.exit(2, "분석 환경 설정에서 BONGHWA_ANALYSIS_ENABLED=true가 필요합니다.\n")
    root = Path(__file__).resolve().parents[1]
    commands = [
        [
            sys.executable,
            "-m",
            "uvicorn",
            "bonghwajigi.api.app:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(args.port),
            "--no-access-log",
        ],
        [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "bonghwajigi.workers.analysis:app",
            "worker",
            "-Q",
            "analysis",
            "--concurrency=1",
            "--pool=solo",
            "--loglevel=INFO",
        ],
        [sys.executable, "-m", "bonghwajigi.workers.outbox"],
    ]
    children = []

    def stop(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    try:
        for command in commands:
            children.append(subprocess.Popen(command, cwd=root))
        while all(child.poll() is None for child in children):
            time.sleep(0.5)
        raise SystemExit("분석 프로세스가 종료됐습니다. 위 오류를 확인하세요.")
    except KeyboardInterrupt:
        pass
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    main()
