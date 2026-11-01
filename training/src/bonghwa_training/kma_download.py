"""기상청 GK2A 산불탐지 FF NetCDF 확보. 인증키/오류 응답 본문을 기록하지 않는다."""

import argparse
import json
import os
import shlex
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

import netCDF4

from bonghwa_training.download import file_sha256

ENDPOINT = "https://apihub.kma.go.kr/api/typ05/api/GK2A/LE2/FF/KO/data"


class RateLimited(RuntimeError):
    def __init__(self, seconds):
        self.seconds = seconds
        super().__init__("기상청 요청 제한. 자료 누락으로 처리하지 않습니다.")


def load_key(path: Path) -> str:
    value = os.environ.get("KMA_APIHUB_AUTH_KEY", "").strip()
    if not value and path.exists():
        if path.stat().st_mode & 0o077:
            raise ValueError("인증키 파일의 권한을 chmod 600으로 제한하세요.")
        for line in path.read_text().splitlines():
            if line.strip().startswith("KMA_APIHUB_AUTH_KEY="):
                pieces = shlex.split(line.split("=", 1)[1], comments=False)
                value = pieces[0] if len(pieces) == 1 else ""
    if not value or any(c.isspace() for c in value):
        raise ValueError("서버 training.env에 KMA_APIHUB_AUTH_KEY를 설정하세요.")
    return value


def validate_original(path: Path) -> dict:
    with path.open("rb") as src:
        header = src.read(8)
    if not (header.startswith(b"CDF") or header == b"\x89HDF\r\n\x1a\n"):
        raise ValueError("NetCDF 원본이 아닌 응답입니다. 오류 본문은 보관하지 않습니다.")
    with netCDF4.Dataset(path) as src:
        variables = {
            name: {
                "shape": list(var.shape),
                "dtype": str(var.dtype),
                "attributes": {
                    key: str(var.getncattr(key))
                    for key in var.ncattrs()
                    if key in ("long_name", "units", "flag_values", "flag_meanings", "_FillValue")
                },
            }
            for name, var in src.variables.items()
        }
        return {
            "variables": variables,
            "dimensions": {k: len(v) for k, v in src.dimensions.items()},
            "global_attributes": {k: str(src.getncattr(k)) for k in src.ncattrs()},
            "projection_attributes": {
                k: str(src["gk2a_imager_projection"].getncattr(k))
                for k in src["gk2a_imager_projection"].ncattrs()
            }
            if "gk2a_imager_projection" in src.variables
            else {},
        }


def acquire_one(root: Path, when: datetime, key: str) -> dict:
    when = when.astimezone(UTC)
    if when.year >= 2025:
        raise ValueError("국내 2025년 이후 최종 관측 정답은 아직 잠금 상태입니다.")
    stamp = when.astimezone(UTC).strftime("%Y%m%d%H%M")
    root.mkdir(parents=True, exist_ok=True)
    root.chmod(0o700)
    path = root / f"gk2a-ff-ko-{stamp}Z.nc"
    sidecar = path.with_suffix(".json")
    params = {"date": stamp}
    canonical = ENDPOINT + "?" + urllib.parse.urlencode(params)
    if path.exists() and sidecar.exists():
        record = json.loads(sidecar.read_text())
        if record["sha256"] != file_sha256(path) or record["url_without_auth"] != canonical:
            raise ValueError("기존 기상청 원본의 SHA/요청 계약이 다릅니다.")
        return record
    part = path.with_suffix(".part")
    request = canonical + "&" + urllib.parse.urlencode({"authKey": key})
    try:
        with urllib.request.urlopen(request, timeout=90) as src:
            if src.status != 200:
                raise ValueError("전체 원본 응답이 아닙니다.")
            with part.open("wb") as dst:
                part.chmod(0o600)
                while block := src.read(1024 * 1024):
                    dst.write(block)
                    if dst.tell() > 64 * 1024 * 1024:
                        raise ValueError("예상한 단일 FF 파일 크기를 초과했습니다.")
            headers = {k: src.headers.get(k) for k in ("Content-Type", "Last-Modified", "ETag")}
        schema = validate_original(part)
    except urllib.error.HTTPError as exc:
        part.unlink(missing_ok=True)
        if exc.code == 404:
            raise FileNotFoundError(f"기상청 원본 없음: {stamp}Z") from None
        if exc.code == 429:
            raw = exc.headers.get("Retry-After", "30")
            if not raw.isdigit():
                from email.utils import parsedate_to_datetime

                raw = str(
                    max(30, int((parsedate_to_datetime(raw) - datetime.now(UTC)).total_seconds()))
                )
            raise RateLimited(max(30, int(raw))) from None
        raise RuntimeError(
            f"기상청 응답 HTTP {exc.code}. 키/활용승인/자료 시각을 확인하세요."
        ) from None
    except Exception as exc:
        part.unlink(missing_ok=True)
        raise RuntimeError(f"기상청 원본 검증 실패 ({type(exc).__name__})") from None
    part.replace(path)
    record = {
        "url_without_auth": canonical,
        "requested_observation_utc": when.astimezone(UTC).isoformat(),
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "path": str(path),
        "sha256": file_sha256(path),
        "bytes": path.stat().st_size,
        "headers": headers,
        "schema": schema,
        "availability_note": "과거 자료의 현재 수신 시각. 당시 입력 가용 시각의 증거가 아님",
        "label_note": "FF/DQF의 실제 범례를 공식 문서와 확인한 후 정답으로 변환할 것",
    }
    sidecar.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    sidecar.chmod(0o600)
    return record


def acquire_with_backoff(root, when, key):
    for attempt in range(4):
        try:
            return acquire_one(root, when, key)
        except RateLimited as exc:
            delay = max(exc.seconds, 30 * 2**attempt)
            if attempt == 3 or delay > 300:
                raise RuntimeError(
                    "기상청 요청 제한이 반복되거나 긴 중지를 요구해 자동 수집을 중지합니다."
                ) from None
            print(json.dumps({"status": "rate_limited", "retry_in_seconds": delay}), flush=True)
            time.sleep(delay)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("data/raw/korea-wildfire/gk2a-ff"))
    p.add_argument(
        "--key-file", type=Path, default=Path.home() / ".config/bonghwajigi/training.env"
    )
    p.add_argument("--start", required=True, help="UTC ISO 시각. 예: 2022-03-04T00:00:00Z")
    p.add_argument("--hours", type=int, default=1)
    p.add_argument("--allow-missing", action="store_true", help="404는 관측 누락으로 기록하고 계속")
    a = p.parse_args()
    start = datetime.fromisoformat(a.start.replace("Z", "+00:00"))
    if start.tzinfo is None or start.minute % 10 or start.second or start.microsecond:
        raise ValueError("시간대가 명시된 10분 경계 시각을 입력하세요.")
    if not 1 <= a.hours <= 24:
        raise ValueError("한 번에 1~24시간의 작은 구간만 확보합니다.")
    key = load_key(a.key_file)
    records = []
    for i in range(a.hours * 6):
        when = start + timedelta(minutes=10 * i)
        try:
            record = acquire_with_backoff(a.root, when, key)
        except FileNotFoundError:
            if not a.allow_missing:
                raise
            record = {"missing_observation_utc": when.astimezone(UTC).isoformat()}
        records.append(record)
        print(
            json.dumps(
                record
                if "missing_observation_utc" in record
                else {k: record[k] for k in ("path", "bytes", "sha256")}
            ),
            flush=True,
        )
        time.sleep(3)
    manifest = a.root / f"manifest-{start.astimezone(UTC):%Y%m%dT%H%MZ}-{a.hours}h.json"
    manifest.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    manifest.chmod(0o600)


if __name__ == "__main__":
    main()
