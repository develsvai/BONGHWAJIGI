import hashlib
import json
import shutil
import time
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

DATASET = "fantineh/next-day-wildfire-spread"
VERSION = 2
API = "https://www.kaggle.com/api/v1/datasets"
SOURCE_SPLITS = ("train", "eval", "test")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def download_dataset(destination: Path, shards_per_split: int | None = 1) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    metadata = get_json(f"{API}/view/{DATASET}")
    if metadata["currentVersionNumber"] != VERSION:
        raise ValueError("발행 버전이 바뀌었습니다. 원본 목록과 버전을 재검토해야 합니다.")
    listing = get_json(f"{API}/list/{DATASET}")
    if listing.get("hasNextPageToken"):
        raise ValueError("원본 목록이 페이지로 나뉩니다. 전체 목록 확보 후 진행해야 합니다.")
    files = listing["datasetFiles"]
    selected = []
    for split in SOURCE_SPLITS:
        candidates = sorted(
            [f for f in files if f"_{split}_" in f["name"]], key=lambda f: f["name"]
        )
        if shards_per_split is not None and (
            shards_per_split < 1 or len(candidates) < shards_per_split
        ):
            raise ValueError(f"{split} 분할의 요청 파일 수를 확인하세요.")
        selected.extend((split, f) for f in candidates[:shards_per_split])
    previous = {}
    if (destination / "manifest.json").exists():
        previous = {
            item["filename"]: item
            for item in json.loads((destination / "manifest.json").read_text())["files"]
        }
    manifest = {
        "dataset": DATASET,
        "version": VERSION,
        "license": metadata["licenseName"],
        "publisher_url": f"https://www.kaggle.com/datasets/{DATASET}",
        "downloaded_at_utc": datetime.now(UTC).isoformat(),
        "available_files": len(files),
        "full_dataset_bytes": metadata["totalBytes"],
        "selection": (
            "all_official_shards"
            if shards_per_split is None
            else f"first_{shards_per_split}_shards_per_official_split"
        ),
        "complete_dataset": len(selected) == len(files),
        "files": [],
    }
    for split, item in selected:
        name = item["name"]
        target = destination / name
        url = f"{API}/download/{DATASET}/{name}?datasetVersionNumber={VERSION}"
        old = previous.get(name)
        verified = (
            target.exists()
            and target.stat().st_size == item["totalBytes"]
            and old is not None
            and file_sha256(target) == old["sha256"]
        )
        if not verified:
            archive_path = destination / (name + ".zip.part")
            for attempt in range(3):
                try:
                    request = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
                    with urllib.request.urlopen(request, timeout=90) as response:
                        if response.status != 200:
                            raise ValueError("원본의 전체 다운로드 응답이 아닙니다.")
                        with archive_path.open("wb") as output:
                            shutil.copyfileobj(response, output, length=1024 * 1024)
                    with zipfile.ZipFile(archive_path) as archive:
                        if archive.namelist() != [name]:
                            raise ValueError("압축 파일의 내용이 예상 원본과 다릅니다.")
                        if archive.getinfo(name).file_size != item["totalBytes"]:
                            raise ValueError("원본 길이가 발행 메타데이터와 다릅니다.")
                        part = target.with_suffix(target.suffix + ".part")
                        with archive.open(name) as source, part.open("wb") as output:
                            shutil.copyfileobj(source, output, length=1024 * 1024)
                        part.replace(target)
                    archive_path.unlink()
                    break
                except (OSError, ValueError, zipfile.BadZipFile):
                    if attempt == 2:
                        raise
                    time.sleep(attempt + 1)
        record = {
            "filename": name,
            "official_split": split,
            "source_url": url,
            "bytes": target.stat().st_size,
            "sha256": file_sha256(target),
        }
        manifest["files"].append(record)
        (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(
            json.dumps({"downloaded": name, "bytes": record["bytes"], "sha256": record["sha256"]}),
            flush=True,
        )
    return manifest
