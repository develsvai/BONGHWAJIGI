"""공개 GOES 5분 화재/비화재 원본. 최종 사건은 기본 수집하지 않는다."""

import argparse
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

from bonghwa_training.download import file_sha256
from bonghwa_training.goes_release import verify_release
from bonghwa_training.korea_download import fetch

NS = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}


def list_hour(bucket: str, hour: datetime):
    prefix = f"ABI-L2-FDCC/{hour.year}/{hour.timetuple().tm_yday:03d}/{hour.hour:02d}/"
    query = urllib.parse.urlencode({"list-type": 2, "prefix": prefix, "max-keys": 1000})
    with urllib.request.urlopen(f"https://{bucket}.s3.amazonaws.com/?{query}", timeout=60) as src:
        root = ET.fromstring(src.read())
    if root.findtext("s:IsTruncated", namespaces=NS) != "false":
        raise ValueError("GOES 원본 목록 페이지를 모두 확보하지 못했습니다.")
    return [
        {
            "key": c.findtext("s:Key", namespaces=NS),
            "last_modified": c.findtext("s:LastModified", namespaces=NS),
            "etag": c.findtext("s:ETag", namespaces=NS),
            "bytes": int(c.findtext("s:Size", namespaces=NS)),
        }
        for c in root.findall("s:Contents", NS)
    ]


def acquire(
    root: Path,
    config: Path,
    *,
    only_event: str | None = None,
    release: Path | None = None,
    workers: int = 8,
):
    cfg = json.loads(config.read_text())
    if only_event and not any(e["id"] == only_event for e in cfg["events"]):
        raise ValueError("계약에 없는 사건입니다.")
    if not 1 <= workers <= 8:
        raise ValueError("동시 요청 수는 1~8이어야 합니다.")
    for event in cfg["events"]:
        if only_event and event["id"] != only_event:
            continue
        if event["split"] == "test":
            if not only_event:
                continue
            if release is None:
                raise ValueError("미사용 사건은 먼저 모델을 고정해야 합니다.")
            verify_release(release, config)
        folder = root / event["id"]
        folder.mkdir(parents=True, exist_ok=True)
        start = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00"))
        first = start - timedelta(hours=1)
        hours = [first + timedelta(hours=i) for i in range(event["hours"] + 8)]
        listing_path = folder / "listing.json"
        if listing_path.exists():
            listing = json.loads(listing_path.read_text())
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                groups = list(
                    pool.map(lambda h, bucket=event["bucket"]: list_hour(bucket, h), hours)
                )
            listing = [r for group in groups for r in group]
            listing_path.write_text(json.dumps(listing, indent=2) + "\n")
        # 같은 관측 시점은 최초 공개본을 선택해 재처리본을 과거 입력에 섞지 않는다.
        unique = {}
        for item in listing:
            slot = item["key"].split("_s")[1].split("_")[0]
            if slot not in unique or item["last_modified"] < unique[slot]["last_modified"]:
                unique[slot] = item
        selected = sorted(unique.values(), key=lambda r: r["key"])

        def one(item, event=event, folder=folder):
            url = f"https://{event['bucket']}.s3.amazonaws.com/{item['key']}"
            record = fetch(url, folder / Path(item["key"]).name)
            if record["bytes"] != item["bytes"]:
                raise ValueError("공개 원본 목록과 실제 다운로드 길이가 다릅니다.")
            return {
                **record,
                "listed_last_modified": item["last_modified"],
                "listed_etag": item["etag"],
            }

        records = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for record in pool.map(one, selected):
                records.append(record)
                if len(records) % 100 == 0:
                    print(
                        json.dumps(
                            {
                                "event": event["id"],
                                "downloaded": len(records),
                                "total": len(selected),
                            }
                        ),
                        flush=True,
                    )
        manifest = {
            "event": event,
            "config_sha256": file_sha256(config),
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
            "files": records,
        }
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "event": event["id"],
                    "files": len(records),
                    "bytes": sum(r["bytes"] for r in records),
                }
            ),
            flush=True,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--event", help="이 사건만 수집해 다른 원본 manifest를 유지")
    parser.add_argument("--release", type=Path)
    args = parser.parse_args()
    acquire(args.root, args.config, only_event=args.event, release=args.release)


if __name__ == "__main__":
    main()
