"""서버에 보관된 토큰을 출력하지 않고 localhost 모델 API를 호출한다."""

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import dotenv_values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["generate", "embed", "ready"])
    parser.add_argument("--text", default="한국어로 '모델 준비 완료' 한 문장만 쓰세요.")
    parser.add_argument("--input-type", choices=["document", "query"], default="document")
    parser.add_argument(
        "--env-file", type=Path, default=Path.home() / ".config/bonghwajigi/gpu.env"
    )
    args = parser.parse_args()
    token = dotenv_values(args.env_file).get("BONGHWA_SERVICE_TOKEN")
    if not token:
        parser.exit(2, "서비스 토큰 설정을 확인하세요.\n")
    path = {
        "generate": "/internal/v1/generate",
        "embed": "/internal/v1/embeddings",
        "ready": "/health/ready",
    }[args.operation]
    body = None
    if args.operation == "generate":
        body = {"text": args.text, "max_output_tokens": 128}
    elif args.operation == "embed":
        body = {"texts": [args.text], "input_type": args.input_type}
    request = urllib.request.Request(
        "http://127.0.0.1:8001" + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            print(response.read().decode())
    except urllib.error.HTTPError as exc:
        print(exc.read().decode())
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
