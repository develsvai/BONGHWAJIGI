import copy
import hashlib
import json
from datetime import datetime, timedelta

import pytest

from bonghwa_training import kma_profile


def event(ident="hongseong_2023", split="validation", **changes):
    return {
        "id": ident,
        "split": split,
        "start_utc": "2023-04-02T02:00:00Z",
        "hours": 1,
        "bbox": [126.2, 36.2, 127.0, 36.9],
        "source": "https://example.org/incident",
        **changes,
    }


def config(tmp_path, events):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"events": events, "input_availability": "research"}))
    return path


def manifest(root, item):
    first = datetime.fromisoformat(item["start_utc"].replace("Z", "+00:00")) - timedelta(hours=1)
    files = [
        {"requested_observation_utc": (first + timedelta(minutes=10 * i)).isoformat()}
        for i in range((item["hours"] + 8) * 6)
    ]
    path = root / item["id"] / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "event": item,
                "config_sha256": "original-acquisition-config",
                "files": files,
                "missing_observations_utc": [],
            }
        )
    )
    return path


@pytest.fixture
def downloads(monkeypatch):
    calls = []

    def download(root, when, key):
        calls.append(when)
        return {"requested_observation_utc": when.isoformat()}

    monkeypatch.setattr(kma_profile, "load_key", lambda _: "unused-fixture")
    monkeypatch.setattr(kma_profile, "acquire_with_backoff", download)
    monkeypatch.setattr(kma_profile.time, "sleep", lambda _: None)
    return calls


def test_split_only_reuse_preserves_originals_and_completes_receipt(tmp_path, downloads):
    root = tmp_path / "raw"
    hongseong = event()
    gangneung = event("gangneung_2023", "calibration")
    original_paths = [
        manifest(root, {**hongseong, "split": "calibration"}),
        manifest(root, {**gangneung, "split": "validation"}),
    ]
    original_bytes = [p.read_bytes() for p in original_paths]
    current = config(tmp_path, [hongseong, gangneung, event("new_2023", "train")])
    receipt = kma_profile.acquire(root, current, tmp_path / "unused.env")
    assert [p.read_bytes() for p in original_paths] == original_bytes
    assert len(downloads) == 54
    assert receipt["non_test_event_ids"] == ["hongseong_2023", "gangneung_2023", "new_2023"]
    assert receipt["events"]["hongseong_2023"] == {
        "requested_split": "validation",
        "manifest_split": "calibration",
        "split_reused": True,
    }
    assert not receipt["events"]["new_2023"]["split_reused"]
    assert receipt["config_sha256"] == hashlib.sha256(current.read_bytes()).hexdigest()
    assert kma_profile.verify_receipt(root, current) == receipt
    receipt_path = root / "acquisition-receipts" / f"{receipt['config_sha256']}.json"
    before = receipt_path.stat().st_mtime_ns
    assert kma_profile.acquire(root, current, tmp_path / "unused.env") == receipt
    assert receipt_path.stat().st_mtime_ns == before
    assert len(downloads) == 54
    assert receipt_path.stat().st_mode & 0o077 == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"bbox": [126.1, 36.2, 127.0, 36.9]},
        {"hours": 2},
        {"start_utc": "2023-04-02T03:00:00Z"},
        {"source": "https://example.org/other"},
        {"id": "other_2023"},
        {"extra": "changed"},
        {"split": "test"},
    ],
)
def test_all_existing_contracts_checked_before_new_downloads(tmp_path, monkeypatch, changes):
    root = tmp_path / "raw"
    old = event()
    path = manifest(root, old)
    payload = json.loads(path.read_text())
    payload["event"].update(changes)
    path.write_text(json.dumps(payload))
    current = config(tmp_path, [event("new_2023", "train"), old])
    monkeypatch.setattr(kma_profile, "load_key", lambda _: pytest.fail("key read before preflight"))
    with pytest.raises(ValueError, match="계약"):
        kma_profile.acquire(root, current, tmp_path / "unused.env")
    assert not (root / "new_2023").exists()
    assert not (root / "acquisition-receipts").exists()


@pytest.mark.parametrize(
    "changes",
    [
        {"id": "../escape"},
        {"id": "a/b"},
        {"id": "."},
        {"split": "unknown"},
        {"locked": True},
        {"locked": "false"},
        {"hours": 0},
        {"hours": 25},
        {"hours": True},
        {"start_utc": "2023-04-02T02:00:00"},
        {"start_utc": "2023-04-02T02:00:00+09:00"},
        {"start_utc": "2023-04-02T02:01:00Z"},
        {"start_utc": "2023-04-02T02:00:01Z"},
        {"start_utc": "2025-01-01T02:00:00Z"},
        {"start_utc": "2024-12-31T20:00:00Z"},
    ],
)
def test_invalid_non_test_contract_fails_before_key_or_download(tmp_path, monkeypatch, changes):
    root = tmp_path / "raw"
    current = config(tmp_path, [event("new_2023", "train"), event(**changes)])
    monkeypatch.setattr(kma_profile, "load_key", lambda _: pytest.fail("key read before preflight"))
    with pytest.raises(ValueError):
        kma_profile.acquire(root, current, tmp_path / "unused.env")
    assert not root.exists()


def test_duplicate_id_even_across_test_split_is_rejected(tmp_path, monkeypatch):
    item = event()
    current = config(tmp_path, [item, {**item, "split": "test", "locked": True}])
    monkeypatch.setattr(kma_profile, "load_key", lambda _: pytest.fail("key read"))
    with pytest.raises(ValueError, match="중복"):
        kma_profile.acquire(tmp_path / "raw", current, tmp_path / "unused.env")


def test_locked_2025_test_manifest_is_not_read(tmp_path, downloads, monkeypatch):
    root = tmp_path / "raw"
    test_dir = root / "sancheong_2025"
    test_dir.mkdir(parents=True)
    (test_dir / "manifest.json").write_text("not-json-do-not-read")
    current = config(
        tmp_path,
        [
            event(),
            event(
                "sancheong_2025",
                "test",
                start_utc="2025-03-22T00:00:00Z",
                locked=True,
            ),
        ],
    )
    read_bytes = type(current).read_bytes

    def guarded_read(path):
        if test_dir in path.parents:
            pytest.fail("test source was read")
        return read_bytes(path)

    monkeypatch.setattr(type(current), "read_bytes", guarded_read)
    receipt = kma_profile.acquire(root, current, tmp_path / "unused.env")
    assert receipt["non_test_event_ids"] == ["hongseong_2023"]
    assert kma_profile.verify_receipt(root, current) == receipt


def test_manifest_sha_change_invalidates_existing_receipt_and_restart(tmp_path, downloads):
    root = tmp_path / "raw"
    current = config(tmp_path, [event()])
    receipt = kma_profile.acquire(root, current, tmp_path / "unused.env")
    path = root / "hongseong_2023" / "manifest.json"
    path.write_text(path.read_text() + "\n")
    for call in (
        lambda: kma_profile.verify_receipt(root, current),
        lambda: kma_profile.acquire(root, current, tmp_path / "unused.env"),
    ):
        with pytest.raises(ValueError, match="영수증"):
            call()
    assert len(downloads) == 54
    stored = root / "acquisition-receipts" / f"{receipt['config_sha256']}.json"
    assert json.loads(stored.read_text()) == receipt


def test_failed_second_event_has_no_completion_receipt(tmp_path, downloads, monkeypatch):
    root = tmp_path / "raw"
    current = config(tmp_path, [event(), event("other_2023", start_utc="2023-04-03T02:00:00Z")])
    original = kma_profile.acquire_with_backoff

    def fail(root, when, key):
        if when.day == 3:
            raise RuntimeError("simulated network failure")
        return original(root, when, key)

    monkeypatch.setattr(kma_profile, "acquire_with_backoff", fail)
    with pytest.raises(RuntimeError, match="simulated"):
        kma_profile.acquire(root, current, tmp_path / "unused.env")
    assert (root / "hongseong_2023" / "manifest.json").exists()
    assert not (root / "acquisition-receipts").exists()


@pytest.mark.parametrize("kind", ["missing", "duplicate"])
def test_incomplete_or_duplicate_manifest_coverage_rejected(tmp_path, kind):
    root = tmp_path / "raw"
    path = manifest(root, event())
    payload = json.loads(path.read_text())
    if kind == "missing":
        payload["files"].pop()
    else:
        payload["files"][-1] = copy.deepcopy(payload["files"][0])
    path.write_text(json.dumps(payload))
    current = config(tmp_path, [event()])
    with pytest.raises(ValueError, match="불완전|중복"):
        kma_profile.acquire(root, current, tmp_path / "unused.env")


def test_all_404_observations_are_explicit_missing_and_complete(tmp_path, downloads, monkeypatch):
    def missing(*args):
        raise FileNotFoundError("fixture 404")

    monkeypatch.setattr(kma_profile, "acquire_with_backoff", missing)
    root = tmp_path / "raw"
    current = config(tmp_path, [event()])
    kma_profile.acquire(root, current, tmp_path / "unused.env")
    payload = json.loads((root / "hongseong_2023" / "manifest.json").read_text())
    assert payload["files"] == []
    assert len(payload["missing_observations_utc"]) == 54
    assert kma_profile.verify_receipt(root, current)["non_test_event_ids"] == ["hongseong_2023"]


def test_atomic_write_never_replaces_existing_file(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        kma_profile._write_new_json_atomic(path, {"replacement": True})
    assert path.read_bytes() == b"original"
    assert not list(tmp_path.glob(".acquisition-*"))


def test_config_or_old_manifest_change_during_acquisition_prevents_receipt(
    tmp_path,
    downloads,
    monkeypatch,
):
    root = tmp_path / "raw"
    old = manifest(root, event())
    current = config(tmp_path, [event(), event("new_2023", "train")])
    original = kma_profile.acquire_with_backoff

    def mutate(root, when, key):
        old.write_text(old.read_text() + "\n")
        return original(root, when, key)

    monkeypatch.setattr(kma_profile, "acquire_with_backoff", mutate)
    with pytest.raises(ValueError, match="수집 중"):
        kma_profile.acquire(root, current, tmp_path / "unused.env")
    assert not (root / "acquisition-receipts").exists()
