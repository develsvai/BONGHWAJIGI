"""공개 한국 MODIS·ISD 기상·지형·토지피복 확보. 서명 URL은 기록하지 않는다."""

import argparse
import csv
import io
import json
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import planetary_computer
import rasterio
from rasterio.windows import from_bounds

from bonghwa_training.download import file_sha256

STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
NOAA = "https://noaa-isd-pds.s3.amazonaws.com"
BOUNDARY = (
    "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/"
    "releaseData/gbOpen/KOR/ADM0/geoBoundaries-KOR-ADM0.geojson"
)


def fetch(url: str, path: Path, *, signed: bool = False) -> dict:
    """부분 파일을 완료 원본으로 재사용하지 않고 오류에서도 SAS를 노출하지 않는다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sidecar = path.with_name(path.name + ".source.json")
    if path.exists() and sidecar.exists():
        old = json.loads(sidecar.read_text())
        if old["url"] == url and old["sha256"] == file_sha256(path):
            return old
    part = path.with_name(path.name + ".part")
    for attempt in range(3):
        try:
            target = planetary_computer.sign(url) if signed else url
            with urllib.request.urlopen(target, timeout=90) as src, part.open("wb") as dst:
                if src.status != 200:
                    raise ValueError("전체 원본 응답이 아닙니다.")
                shutil.copyfileobj(src, dst, length=1024 * 1024)
                headers = {k: src.headers.get(k) for k in ("ETag", "Last-Modified")}
            part.replace(path)
            record = {
                "url": url,
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
                "headers": headers,
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
            }
            sidecar.write_text(json.dumps(record, indent=2) + "\n")
            return record
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise FileNotFoundError(f"공개 원본 없음: {path.name}") from None
            error = f"HTTP {exc.code}"
        except Exception as exc:
            error = type(exc).__name__
        if attempt < 2:
            time.sleep(attempt + 1)
    raise RuntimeError(f"공개 원본 다운로드 실패: {path.name} ({error})") from None


def search(collection: str, bbox: list, interval: str | None = None) -> list:
    params = {"collections": collection, "bbox": ",".join(map(str, bbox)), "limit": 1000}
    if interval:
        params["datetime"] = interval
    url = f"{STAC}/search?{urllib.parse.urlencode(params)}"
    result = []
    seen = set()
    while url:
        if url in seen:
            raise ValueError("STAC 페이지가 반복됩니다.")
        seen.add(url)
        with urllib.request.urlopen(url, timeout=90) as src:
            page = json.load(src)
        result.extend(page["features"])
        links = [x for x in page["links"] if x["rel"] == "next"]
        if links and links[0].get("method", "GET") != "GET":
            raise ValueError("지원하지 않는 STAC 페이지 방식입니다.")
        url = links[0]["href"] if links else None
    return result


def inspect_fire(path: Path) -> dict:
    with rasterio.open(path) as src:
        tags = src.tags()
        dates = tags.get("Dates", "").split()
        if len(dates) != src.count or len(set(dates)) != src.count:
            raise ValueError(f"내부 날짜/밴드 수 불일치: {path.name}")
        return {
            "dates": dates,
            "bands": src.count,
            "shape": list(src.shape),
            "transform": list(src.transform)[:6],
            "crs_wkt": src.crs.to_wkt(),
            "production_datetime": tags.get("PRODUCTIONDATETIME"),
            "local_granule_id": tags.get("LOCALGRANULEID"),
        }


def acquire_fire(root: Path, cfg: dict, years: list[int], workers: int):
    for year in years:
        listing = root / "stac" / f"fire-{year}.json"
        listing.parent.mkdir(parents=True, exist_ok=True)
        if listing.exists():
            items = json.loads(listing.read_text())["features"]
        else:
            items = search(
                "modis-14A1-061",
                cfg["bbox"],
                f"{year}-01-01T00:00:00Z/{year}-12-31T23:59:59Z",
            )
            listing.write_text(json.dumps({"features": items}, indent=2) + "\n")
        unique = {}
        for item in items:
            for key in ("FireMask", "QA", "MaxFRP"):
                href = item["assets"][key]["href"]
                unique.setdefault(href, {"asset": key, "item_ids": []})["item_ids"].append(
                    item["id"]
                )

        def one(pair, year=year):
            href, info = pair
            path = root / "fire" / str(year) / Path(urllib.parse.urlparse(href).path).name
            record = fetch(href, path, signed=True)
            return {**record, **info, **inspect_fire(path)}

        records = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for record in pool.map(one, unique.items()):
                records.append(record)
                if len(records) % 50 == 0:
                    print(
                        json.dumps(
                            {"year": year, "downloaded": len(records), "total": len(unique)}
                        ),
                        flush=True,
                    )
        (root / f"fire-manifest-{year}.json").write_text(
            json.dumps({"stac_items": len(items), "files": records}, indent=2) + "\n"
        )
        print(
            json.dumps(
                {"year": year, "files": len(records), "bytes": sum(r["bytes"] for r in records)}
            ),
            flush=True,
        )


def acquire_weather(root: Path, years: list[int], workers: int):
    history = root / "weather" / "isd-history.csv"
    fetch(f"{NOAA}/isd-history.csv", history)
    fetch(f"{NOAA}/isd-lite/isd-lite-format.txt", root / "weather" / "format.txt")
    stations = []
    for row in csv.DictReader(io.StringIO(history.read_text())):
        if row["CTRY"] != "KS" or not row["LAT"] or not row["LON"]:
            continue
        lat, lon = float(row["LAT"]), float(row["LON"])
        if not (33 <= lat <= 38.7 and 124.5 <= lon <= 132):
            continue
        stations.append(row)
    (root / "weather" / "stations.json").write_text(json.dumps(stations, indent=2) + "\n")
    jobs = [
        (year, s)
        for year in years
        for s in stations
        if int(s["BEGIN"][:4]) <= year <= int(s["END"][:4])
    ]

    def one(job):
        year, station = job
        name = f"{station['USAF']}-{station['WBAN']}-{year}.gz"
        try:
            return fetch(f"{NOAA}/isd-lite/data/{year}/{name}", root / "weather" / str(year) / name)
        except FileNotFoundError:
            return {"missing": name}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        records = list(pool.map(one, jobs))
    for year in years:
        year_records = [
            r for r in records if Path(r.get("path", r.get("missing"))).name.endswith(f"-{year}.gz")
        ]
        (root / f"weather-manifest-{year}.json").write_text(
            json.dumps(year_records, indent=2) + "\n"
        )
    if not any("sha256" in record for record in records):
        raise ValueError("실제 기상 원본이 하나도 없습니다. 원본 경로와 목록을 검토하세요.")
    print(
        json.dumps(
            {
                "weather_stations": len(stations),
                "files": len(records),
                "missing_files": sum("missing" in r for r in records),
            }
        ),
        flush=True,
    )


def acquire_firms(root: Path, years: list[int], workers: int):
    base = "https://firms.modaps.eosdis.nasa.gov/data/country"
    index = root / "firms" / "yearly_summary_files.txt"
    fetch(f"{base}/yearly_summary_files.txt", index)
    available = {r["filename"]: r for r in csv.DictReader(io.StringIO(index.read_text()))}
    fetch(f"{base}/AttributesReadme.txt", root / "firms" / "AttributesReadme.txt")
    jobs = []
    for year in years:
        for sensor in ("viirs-snpp", "viirs-jpss1"):
            name = f"{sensor}_{year}_Republic_of_Korea.csv"
            if name not in available:
                raise ValueError(f"공식 연간 공개 목록에 없음: {name}")
            jobs.append((year, sensor, name))

    def one(job):
        year, sensor, name = job
        record = fetch(f"{base}/{sensor}/{year}/{name}", root / "firms" / str(year) / name)
        if record["bytes"] != int(available[name]["size"]):
            raise ValueError(f"NASA 발행 길이 불일치: {name}")
        return {
            **record,
            "year": year,
            "sensor": sensor,
            "published_updated": available[name]["updated"],
        }

    with ThreadPoolExecutor(max_workers=workers) as pool:
        records = list(pool.map(one, jobs))
    # 서로 다른 연도 실행이 원본 provenance를 지우지 않게 연도별 manifest를 쓴다.
    for year in years:
        (root / "firms" / f"manifest-{year}.json").write_text(
            json.dumps([r for r in records if r["year"] == year], indent=2) + "\n"
        )
    print(
        json.dumps({"firms_files": len(records), "firms_bytes": sum(r["bytes"] for r in records)}),
        flush=True,
    )


def acquire_static(root: Path, cfg: dict):
    fetch(BOUNDARY, root / "boundary.geojson")
    boundary = json.loads((root / "boundary.geojson").read_text())
    if boundary.get("type") != "FeatureCollection" or not boundary.get("features"):
        raise ValueError("국가 경계의 실제 GeoJSON이 아닙니다.")
    # CCI 자산의 한국 창만 읽어 별도 저장. 전체 원본과 혼동하지 않도록 출처/창을 보존한다.
    out = root / "static" / "landcover-2015-korea.tif"
    items = search("esa-cci-lc", cfg["bbox"], "2015-01-01T00:00:00Z/2015-12-31T23:59:59Z")
    if len(items) != 1:
        raise ValueError("토지피복 타일 목록을 검토해야 합니다.")
    item = items[0]
    (root / "stac" / "landcover.json").write_text(json.dumps(item, indent=2) + "\n")
    href = item["assets"]["lccs_class"]["href"]
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            with rasterio.open(planetary_computer.sign(href)) as src:
                window = from_bounds(*cfg["bbox"], src.transform).round_offsets().round_lengths()
                data = src.read(1, window=window)
                profile = src.profile.copy()
                profile.update(
                    width=data.shape[1],
                    height=data.shape[0],
                    count=1,
                    transform=src.window_transform(window),
                    compress="deflate",
                )
                with rasterio.open(out, "w", **profile) as dst:
                    dst.write(data, 1)
        except Exception as exc:
            raise RuntimeError(f"토지피복 창 추출 실패: {type(exc).__name__}") from None
    meta = {
        "url": href,
        "derivation": "원본 COG의 bbox 창 추출",
        "bbox": cfg["bbox"],
        "path": str(out),
        "sha256": file_sha256(out),
        "item_id": item["id"],
    }
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    dem = search("cop-dem-glo-90", cfg["bbox"])
    (root / "stac" / "dem.json").write_text(json.dumps({"features": dem}, indent=2) + "\n")
    for item in dem:
        href = item["assets"]["data"]["href"]
        fetch(
            href, root / "static" / "dem" / Path(urllib.parse.urlparse(href).path).name, signed=True
        )
    print(
        json.dumps({"static_dem_tiles": len(dem), "landcover_sha256": meta["sha256"]}), flush=True
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--years", type=int, nargs="+")
    parser.add_argument(
        "--parts",
        nargs="+",
        choices=("fire", "weather", "static", "firms"),
        default=["fire", "weather", "static"],
    )
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    args.root.mkdir(parents=True, exist_ok=True)
    (args.root / "stac").mkdir(exist_ok=True)
    years = args.years or cfg["years"]
    if not set(years) <= set(cfg["years"]) or not 1 <= args.workers <= 8:
        raise ValueError("수집 연도 또는 동시 요청 수를 확인하세요.")
    if "fire" in args.parts:
        acquire_fire(args.root, cfg, years, args.workers)
    if "weather" in args.parts:
        acquire_weather(args.root, years, args.workers)
    if "static" in args.parts:
        acquire_static(args.root, cfg)
    if "firms" in args.parts:
        acquire_firms(args.root, years, args.workers)


if __name__ == "__main__":
    main()
