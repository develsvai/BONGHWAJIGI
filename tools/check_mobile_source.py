"""커밋된 앱 gitlink와 실제 checkout·API 명세를 확인하고 빌드 출처를 출력한다."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOBILE = ROOT / "apps/mobile"


def git(*args, cwd=ROOT):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    entry = git("ls-tree", "HEAD", "--", "apps/mobile").split()
    if len(entry) != 4 or entry[:2] != ["160000", "commit"]:
        raise SystemExit("메인 HEAD에 apps/mobile 서브모듈이 고정되어 있지 않습니다.")
    metadata_changes = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            "HEAD",
            "--",
            ".gitmodules",
            "apps/mobile",
            "docs/V2/delivery/api/mvp-openapi.json",
        ],
        cwd=ROOT,
    )
    if metadata_changes.returncode:
        raise SystemExit("앱 gitlink·원격 설정·서버 API 명세에 미커밋 변경이 있습니다.")
    expected = entry[2]
    if not (MOBILE / ".git").exists():
        raise SystemExit("git submodule update --init --recursive를 먼저 실행하세요.")
    actual = git("rev-parse", "HEAD", cwd=MOBILE)
    if actual != expected:
        raise SystemExit("앱 checkout이 메인 gitlink와 다릅니다. 고정 커밋을 초기화하세요.")
    if git("status", "--porcelain", "--untracked-files=normal", cwd=MOBILE):
        raise SystemExit("앱 소스에 미커밋 변경이 있습니다. 검증된 커밋을 사용하세요.")
    server_schema = ROOT / "docs/V2/delivery/api/mvp-openapi.json"
    app_schema = MOBILE / "docs/api/mvp-openapi.json"
    if json.loads(server_schema.read_text()) != json.loads(app_schema.read_text()):
        raise SystemExit("앱 생성 타입 원본과 서버 OpenAPI가 다릅니다.")
    package = json.loads((MOBILE / "package.json").read_text())
    result = {
        "main_commit": git("rev-parse", "HEAD"),
        "app_path": "apps/mobile",
        "app_remote": git(
            "config", "--blob", "HEAD:.gitmodules", "--get", "submodule.apps/mobile.url"
        ),
        "app_commit": actual,
        "api_schema_version": json.loads(app_schema.read_text())["info"]["version"],
        "api_contract_sha256": sha256(app_schema),
        "package_lock_sha256": sha256(MOBILE / "package-lock.json"),
        "node_engine": package["engines"]["node"],
        "expo_version": package["dependencies"]["expo"],
        "react_native_version": package["dependencies"]["react-native"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
