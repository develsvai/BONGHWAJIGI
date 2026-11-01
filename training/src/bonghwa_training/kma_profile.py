"""사전에 정한 국내 사건의 FF 원본과 누락 목록. 최종 사건은 수집하지 않는다."""

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from bonghwa_training.kma_download import acquire_with_backoff, load_key

NON_TEST_SPLITS = {"train", "validation", "calibration"}


def _utc(value: str) -> datetime:
    when = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if when.tzinfo is None or when.utcoffset() != timedelta(0):
        raise ValueError("국내 수집 시각은 UTC 시간대를 명시해야 합니다.")
    return when.astimezone(UTC)


def _window(event: dict) -> list[datetime]:
    start = _utc(event["start_utc"])
    hours = event["hours"]
    if start.minute % 10 or start.second or start.microsecond:
        raise ValueError("국내 수집 시각은 10분 경계여야 합니다.")
    if type(hours) is not int or not 1 <= hours <= 24:
        raise ValueError("국내 사건의 hours는 1~24 정수여야 합니다.")
    first = start - timedelta(hours=1)
    times = [first + timedelta(minutes=10 * i) for i in range((hours + 8) * 6)]
    if times[-1].year >= 2025:
        raise ValueError("국내 2025년 이후 원본은 잠금 상태입니다.")
    return times


def _manifest_state(root: Path, event: dict, times: list[datetime]) -> dict | None:
    folder = root / event["id"]
    path = folder / "manifest.json"
    if folder.is_symlink() or path.is_symlink():
        raise ValueError("사건 manifest 경로에 심볼릭 링크를 사용하지 않습니다.")
    if not path.exists():
        return None
    payload = path.read_bytes()
    manifest = json.loads(payload)
    old = manifest["event"]
    if old["split"] not in NON_TEST_SPLITS or {k: v for k, v in old.items() if k != "split"} != {
        k: v for k, v in event.items() if k != "split"
    }:
        raise ValueError(
            f"기존 국내 사건 계약이 바뀌었습니다: {event['id']}. 새 경로를 사용하세요."
        )
    # split은 학습 계약에 속한다. 원본 수집 계약·바이트·과거 provenance는 보존한다.
    observed = [_utc(record["requested_observation_utc"]) for record in manifest["files"]]
    missing = [_utc(value) for value in manifest["missing_observations_utc"]]
    covered = observed + missing
    if len(covered) != len(times) or set(covered) != set(times):
        raise ValueError(f"기존 국내 사건 수집 구간이 불완전하거나 중복됩니다: {event['id']}")
    return {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "requested_split": event["split"],
        "manifest_split": old["split"],
        "split_reused": old["split"] != event["split"],
    }


def _preflight(root: Path, config: Path):
    payload = config.read_bytes()
    cfg = json.loads(payload)
    events = cfg["events"]
    if not isinstance(events, list) or not events or not isinstance(cfg["input_availability"], str):
        raise ValueError("국내 수집 config의 events/input_availability를 확인하세요.")
    ids, windows = set(), {}
    # 모든 config 검증을 먼저 수행한다. 잠금 시험 사건의 원본 경로는 읽지 않는다.
    for event in events:
        ident = event["id"]
        if not isinstance(ident, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", ident
        ):
            raise ValueError("국내 사건 ID는 안전한 단일 경로 이름이어야 합니다.")
        if ident in ids:
            raise ValueError(f"국내 사건 ID가 중복됩니다: {ident}")
        ids.add(ident)
        if event["split"] == "test":
            continue
        if event["split"] not in NON_TEST_SPLITS or event.get("locked", False) is not False:
            raise ValueError(f"잠금 또는 잘못된 분할의 사건은 수집하지 않습니다: {ident}")
        windows[ident] = _window(event)
    if not windows:
        raise ValueError("수집할 비시험 사건이 없습니다.")
    states = {
        event["id"]: _manifest_state(root, event, windows[event["id"]])
        for event in events
        if event["split"] != "test"
    }
    return cfg, hashlib.sha256(payload).hexdigest(), windows, states


def _receipt_contract(config_sha: str, states: dict) -> dict:
    if any(state is None for state in states.values()):
        raise ValueError("모든 비시험 사건의 수집 manifest가 있어야 완료할 수 있습니다.")
    return {
        "schema_version": 1,
        "config_sha256": config_sha,
        "non_test_event_ids": list(states),
        "manifest_sha256": {ident: state["sha256"] for ident, state in states.items()},
        "events": {
            ident: {k: v for k, v in state.items() if k != "sha256"}
            for ident, state in states.items()
        },
    }


def _receipt_path(root: Path, config_sha: str) -> Path:
    return root / "acquisition-receipts" / f"{config_sha}.json"


def verify_receipt(root: Path, config: Path) -> dict:
    """현재 config와 모든 비시험 manifest의 완료 영수증을 검증한다. 원본 픽셀은 읽지 않는다."""
    _, config_sha, _, states = _preflight(root, config)
    receipt = json.loads(_receipt_path(root, config_sha).read_bytes())
    expected = _receipt_contract(config_sha, states)
    if any(receipt.get(k) != value for k, value in expected.items()):
        raise ValueError("국내 수집 완료 영수증의 config/manifest SHA 또는 분할 계약이 다릅니다.")
    _utc(receipt["completed_at_utc"])
    return receipt


def _write_new_json_atomic(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=".acquisition-", delete=False
        ) as dst:
            temporary = Path(dst.name)
            json.dump(value, dst, indent=2, ensure_ascii=False)
            dst.write("\n")
            dst.flush()
            os.fsync(dst.fileno())
        # 완성된 파일만 게시하며, 다른 실행이 만든 기존 manifest/영수증을 덮어쓰지 않는다.
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def acquire(root: Path, config: Path, key_file: Path):
    cfg, config_sha, windows, states = _preflight(root, config)
    receipt_path = _receipt_path(root, config_sha)
    if receipt_path.exists():
        return verify_receipt(root, config)
    key = load_key(key_file) if any(state is None for state in states.values()) else None
    for event in cfg["events"]:
        if event["split"] == "test":
            continue
        if states[event["id"]] is not None:
            continue
        folder = root / event["id"]
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        manifest_path = folder / "manifest.json"
        if manifest_path.exists():
            raise ValueError("사전 검사 후 다른 실행이 사건 manifest를 만들었습니다.")
        times = windows[event["id"]]
        count = len(times)
        records, missing = [], []
        for i, when in enumerate(times):
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
                next_when = times[i + 1]
                cached = root / f"gk2a-ff-ko-{next_when:%Y%m%d%H%M}Z.nc"
                if not cached.exists():
                    time.sleep(3)
        manifest = {
            "event": event,
            "config_sha256": config_sha,
            "files": records,
            "missing_observations_utc": missing,
            "availability": cfg["input_availability"],
        }
        _write_new_json_atomic(manifest_path, manifest)
        states[event["id"]] = _manifest_state(root, event, times)
        print(
            json.dumps({"event": event["id"], "files": len(records), "missing": len(missing)}),
            flush=True,
        )
    _, final_sha, _, final_states = _preflight(root, config)
    if final_sha != config_sha or final_states != states:
        raise ValueError(
            "수집 중 config 또는 기존 manifest가 바뀌어 완료 영수증을 만들지 않습니다."
        )
    receipt = {
        **_receipt_contract(config_sha, states),
        "completed_at_utc": datetime.now(UTC).isoformat(),
    }
    _write_new_json_atomic(receipt_path, receipt)
    return receipt


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
