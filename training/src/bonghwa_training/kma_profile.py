"""사전에 정한 국내 사건의 FF 원본과 누락 목록. 최종 사건은 수집하지 않는다."""

import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

from bonghwa_training.download import file_sha256
from bonghwa_training.kma_download import acquire_with_backoff, load_key


def acquire(root: Path, config: Path, key_file: Path):
    cfg = json.loads(config.read_text())
    key = load_key(key_file)
    for event in cfg["events"]:
        if event["split"] == "test":
            continue
        folder = root / event["id"]
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        manifest_path = folder / "manifest.json"
        if manifest_path.exists():
            old = json.loads(manifest_path.read_text())
            if old["event"] == event:
                continue
            raise ValueError("기존 국내 사건 계약이 바뀌었습니다. 새 경로를 사용하세요.")
        start = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00"))
        first = start - timedelta(hours=1)
        count = (event["hours"] + 8) * 6
        records, missing = [], []
        for i in range(count):
            when = first + timedelta(minutes=10 * i)
            try:
                records.append(acquire_with_backoff(root, when, key))
            except FileNotFoundError:
                missing.append(when.isoformat())
            if i % 25 == 0:
                print(
                    json.dumps(
                        {
                            "event": event["id"],
                            "requested": i + 1,
                            "total": count,
                            "missing": len(missing),
                        }
                    ),
                    flush=True,
                )
            # SHA로 확인된 캐시는 네트워크 요청 없이 즉시 재개한다.
            if i + 1 < count:
                next_when = first + timedelta(minutes=10 * (i + 1))
                cached = root / f"gk2a-ff-ko-{next_when:%Y%m%d%H%M}Z.nc"
                if not cached.exists():
                    time.sleep(3)
        manifest = {
            "event": event,
            "config_sha256": file_sha256(config),
            "files": records,
            "missing_observations_utc": missing,
            "availability": cfg["input_availability"],
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        manifest_path.chmod(0o600)
        print(
            json.dumps({"event": event["id"], "files": len(records), "missing": len(missing)}),
            flush=True,
        )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("data/raw/korea-wildfire/gk2a-ff"))
    p.add_argument("--config", type=Path, required=True)
    p.add_argument(
        "--key-file", type=Path, default=Path.home() / ".config/bonghwajigi/training.env"
    )
    a = p.parse_args()
    acquire(a.root, a.config, a.key_file)


if __name__ == "__main__":
    main()
