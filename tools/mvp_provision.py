"""승인된 일반 서버의 비밀 설정과 제한된 GPU 터널 키를 준비한다. 값은 출력하지 않는다."""

import argparse
import json
import secrets
import shlex
import subprocess
from pathlib import Path

from bonghwajigi.common.config import Settings

REMOTE = r"""
import json, os, pathlib, sys, tempfile
values = json.load(sys.stdin)
root = pathlib.Path('/home1/ncloud/.config/bonghwajigi')
root.mkdir(parents=True, exist_ok=True, mode=0o700)
root.chmod(0o700)
path = root / 'general.env'
old = {}
if path.exists():
    if path.stat().st_mode & 0o077:
        raise RuntimeError('기존 비밀 설정 권한을 확인하세요')
    old = dict(line.split('=', 1) for line in path.read_text().splitlines() if '=' in line)
for name in ('POSTGRES_PASSWORD', 'BONGHWA_SERVICE_TOKEN', 'BONGHWA_JWT_SECRET'):
    if old.get(name):
        values[name] = old[name]
for value in values.values():
    if any(c in value for c in (chr(13), chr(10), chr(0))):
        raise ValueError('설정 줄바꿈 거부')
fd, temp = tempfile.mkstemp(dir=root)
with os.fdopen(fd, 'w') as stream:
    stream.write(chr(10).join(k + '=' + v for k, v in values.items()) + chr(10))
os.chmod(temp, 0o600)
os.replace(temp, path)
(root / 'accounts').mkdir(exist_ok=True, mode=0o700)
print('일반 서버 비밀 설정 준비 완료. 값은 출력하지 않습니다.')
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", type=Path, default=Path("/private/tmp/bonghwa-mvp-server-ssh"))
    args = parser.parse_args()
    settings = Settings()
    token = settings.embedding_service_token
    if not token:
        parser.exit(2, "기존 GPU API 인증 설정이 필요합니다.\n")
    release = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    values = {
        "POSTGRES_PASSWORD": secrets.token_urlsafe(32),
        "BONGHWA_SERVICE_TOKEN": secrets.token_urlsafe(36),
        "BONGHWA_JWT_SECRET": secrets.token_urlsafe(48),
        "BONGHWA_EMBEDDING_SERVICE_TOKEN": token.get_secret_value(),
        "BONGHWA_PRIVATE_DIR": "/home1/ncloud/.config/bonghwajigi",
        "BONGHWA_RELEASE": release,
    }
    prefix = ["ssh", "-S", str(args.control), "inno-server-011"]
    subprocess.run(
        [*prefix, "python3 -c " + shlex.quote(REMOTE)],
        input=json.dumps(values),
        text=True,
        check=True,
    )
    subprocess.run(
        [
            *prefix,
            "umask 077; mkdir -p /home1/ncloud/.ssh; chmod 700 /home1/ncloud/.ssh; "
            "test -f /home1/ncloud/.ssh/bonghwajigi-gpu-api || "
            "ssh-keygen -q -t ed25519 -N '' -C bonghwajigi-general-gpu-api "
            "-f /home1/ncloud/.ssh/bonghwajigi-gpu-api",
        ],
        check=True,
    )
    subprocess.run(
        [
            *prefix,
            "sudo chown 10001:10001 /home1/ncloud/.config/bonghwajigi/accounts && "
            "sudo chmod 700 /home1/ncloud/.config/bonghwajigi/accounts",
        ],
        check=True,
    )
    print("GPU 터널 공개키를 제한된 authorized_keys 항목으로 등록한 뒤 서비스를 시작하세요.")


if __name__ == "__main__":
    main()
