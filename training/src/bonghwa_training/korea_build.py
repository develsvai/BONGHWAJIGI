"""국내 과거 재현 데이터 구축. 날짜·좌표를 보존하고 미관측을 음성으로 바꾸지 않는다."""

import argparse
import csv
import gzip
import json
from collections import defaultdict
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import rasterio
from affine import Affine
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.warp import reproject, transform_geom
from scipy.ndimage import convolve, uniform_filter
from scipy.spatial import cKDTree
from shapely.geometry import shape

from bonghwa_training.download import file_sha256

WEATHER = (
    "temperature_mean_c",
    "temperature_max_c",
    "temperature_min_c",
    "humidity_min_pct",
    "wind_speed_mean_ms",
    "wind_speed_max_ms",
    "wind_u_mean_ms",
    "wind_v_mean_ms",
    "observed_precipitation_sum_mm",
    "weather_hours",
    "precipitation_hours",
)
FEATURES = (
    "previous_fire",
    "previous_unknown",
    "fire_neighbors_3",
    "fire_neighbors_11",
    "observed_fraction_11",
    "distance_to_previous_fire_km",
    "nearest_fire_dx_km",
    "nearest_fire_dy_km",
    "previous_frp_mw",
    "nearby_frp_mw",
    "fire_days_last_7",
    "observed_days_last_7",
    "forest_fraction",
    "landcover_class",
    "elevation_m",
    "slope_degrees",
    "day_of_year_sin",
    "day_of_year_cos",
    "station_distance_km",
    *WEATHER,
)


def classify(mask: np.ndarray, qa: np.ndarray) -> np.ndarray:
    """7=불확실, 8/9=양성, 5=관측 음성. QA의 육지/해안만 인정."""
    result = np.zeros_like(mask, dtype=np.uint8)
    land = np.isin(qa & 3, [1, 2])
    result[(mask == 5) & land] = 5
    result[(mask == 7) & land] = 7
    result[np.isin(mask, [8, 9]) & land] = 9
    return result


def band_dates(tags: dict, count: int) -> list[date]:
    dates = [date.fromisoformat(s) for s in tags.get("Dates", "").split()]
    if len(dates) != count or len(set(dates)) != count or dates != sorted(dates):
        raise ValueError("내부 Dates와 실제 밴드의 일대일 순서를 확인해야 합니다.")
    return dates


def allowed_day(day: date, gap: int) -> bool:
    return (day - date(day.year, 1, 1)).days >= gap and (date(day.year + 1, 1, 1) - day).days > gap


def make_grid(root: Path, output: Path, cfg: dict):
    sample = sorted((root / "fire").glob("*/*_FireMask.tif"))[0]
    with rasterio.open(sample) as src:
        crs, reference = src.crs, src.transform
    geo = json.loads((root / "boundary.geojson").read_text())
    geometries = [transform_geom("EPSG:4326", crs, f["geometry"]) for f in geo["features"]]
    bounds = np.array([shape(g).bounds for g in geometries])
    left, bottom = bounds[:, :2].min(axis=0)
    right, top = bounds[:, 2:].max(axis=0)
    c0 = int(np.floor((left - reference.c) / reference.a))
    c1 = int(np.ceil((right - reference.c) / reference.a))
    r0 = int(np.floor((top - reference.f) / reference.e))
    r1 = int(np.ceil((bottom - reference.f) / reference.e))
    transform = reference * Affine.translation(c0, r0)
    dims = (r1 - r0, c1 - c0)
    country = geometry_mask(geometries, out_shape=dims, transform=transform, invert=True)
    lc = np.zeros(dims, dtype=np.uint8)
    fraction = np.full(dims, np.nan, dtype=np.float32)
    with rasterio.open(root / "static" / "landcover-2015-korea.tif") as src:
        raw = src.read(1)
        forest = np.isin(raw, cfg["forest_classes"]).astype(np.float32)
        forest[raw == 0] = np.nan
        for data, dest, method in [
            (raw, lc, Resampling.mode),
            (forest, fraction, Resampling.average),
        ]:
            reproject(
                data,
                dest,
                src_transform=src.transform,
                src_crs=src.crs,
                src_nodata=0 if data is raw else np.nan,
                dst_transform=transform,
                dst_crs=crs,
                resampling=method,
                dst_nodata=0 if data is raw else np.nan,
            )
    dem = np.full(dims, np.nan, dtype=np.float32)
    for path in sorted((root / "static" / "dem").glob("*.tif")):
        with rasterio.open(path) as src:
            reproject(
                rasterio.band(src, 1),
                dem,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=crs,
                dst_nodata=np.nan,
                init_dest_nodata=False,
                resampling=Resampling.average,
            )
    rows, cols = np.indices(dims)
    xs, ys = transform.c + (cols + 0.5) * transform.a, transform.f + (rows + 0.5) * transform.e
    lon, lat = Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform(xs, ys)
    east, north = Transformer.from_crs(crs, "EPSG:5179", always_xy=True).transform(xs, ys)
    slope = ground_slope(dem, east, north)
    forest = country & (fraction >= 0.5)
    np.savez_compressed(
        output / "grid.npz",
        country=country,
        forest=forest,
        forest_fraction=fraction,
        landcover_class=lc,
        elevation_m=dem,
        slope_degrees=slope,
        longitude=lon,
        latitude=lat,
        easting_m=east,
        northing_m=north,
    )
    metadata = {
        "shape": list(dims),
        "transform": list(transform)[:6],
        "crs_wkt": crs.to_wkt(),
        "nominal_resolution_m": 1000,
        "sinusoidal_grid_spacing_m": transform.a,
        "country_cells": int(country.sum()),
        "forest_cells": int(forest.sum()),
        "forest_fraction_threshold": 0.5,
        "distance_crs": "EPSG:5179",
        "boundary_sha256": file_sha256(root / "boundary.geojson"),
    }
    (output / "grid.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


def ground_slope(elevation, east, north):
    """정현 투영 격자의 전단을 반영해 지상 좌표상의 경사를 계산한다."""
    zr, zc = np.gradient(elevation)
    er, ec = np.gradient(east)
    nr, nc = np.gradient(north)
    determinant = er * nc - ec * nr
    ge = (zr * nc - zc * nr) / determinant
    gn = (er * zc - ec * zr) / determinant
    return np.rad2deg(np.arctan(np.hypot(ge, gn))).astype(np.float32)


def nearest_fire(fire, forest, grid):
    """위도에 따라 전단되는 위성 격자 간격을 실제 지상 거리로 오인하지 않는다."""
    fr, fc = np.where(fire)
    rr, cc = np.where(forest)
    points = np.column_stack((grid["easting_m"][fire], grid["northing_m"][fire]))
    query = np.column_stack((grid["easting_m"][forest], grid["northing_m"][forest]))
    distances, indices = cKDTree(points).query(query)
    distance = np.full(fire.shape, np.inf)
    distance[forest] = distances / 1000
    nearest = np.zeros((2, *fire.shape), dtype=np.int32)
    nearest[:, rr, cc] = np.array([fr[indices], fc[indices]])
    return distance, nearest


def daily_weather(path: Path) -> dict:
    with gzip.open(path, "rt") as src:
        arr = np.loadtxt(src, dtype=np.float32, ndmin=2)
    if arr.shape[1] != 12:
        raise ValueError(f"ISD-Lite 열 수 불일치: {path.name}")
    # 시간 반올림 자료이므로 경계 이후의 관측이 섞이지 않도록 23시 관측을 제외한다.
    arr = arr[(arr[:, 3] >= 0) & (arr[:, 3] <= 22)]
    grouped = defaultdict(list)
    for row in arr:
        grouped[date(*row[:3].astype(int))].append(row)
    result = {}
    for day, rows in grouped.items():
        data = np.array(rows)
        if len(set(data[:, 3])) != len(data):
            raise ValueError(f"ISD-Lite 중복 시간: {path.name} {day}")
        vals = data[:, 4:].copy()
        vals[vals == -9999] = np.nan
        temp, dew, _, direction, speed, _, rain, _ = vals.T
        temp, dew, speed = temp / 10, dew / 10, speed / 10
        temp[(temp < -90) | (temp > 65)] = np.nan
        dew[(dew < -100) | (dew > 65) | (dew > temp)] = np.nan
        speed[(speed < 0) | (speed > 100)] = np.nan
        direction[(direction < 0) | (direction > 360)] = np.nan
        radians = np.deg2rad(direction)
        u, v = -speed * np.sin(radians), -speed * np.cos(radians)
        humidity = 100 * np.exp(17.625 * dew / (243.04 + dew) - 17.625 * temp / (243.04 + temp))
        rain[rain == -1] = 0  # trace
        rain[rain < 0] = np.nan

        def stat(values, method):
            return float(method(values)) if np.isfinite(values).any() else float("nan")

        count = int(np.isfinite(temp).sum())
        rain_count = int(np.isfinite(rain).sum())
        result[day] = np.array(
            [
                stat(temp, np.nanmean),
                stat(temp, np.nanmax),
                stat(temp, np.nanmin),
                stat(humidity, np.nanmin),
                stat(speed, np.nanmean),
                stat(speed, np.nanmax),
                stat(u, np.nanmean),
                stat(v, np.nanmean),
                float(np.nansum(rain) / 10) if rain_count > 0 else np.nan,
                count,
                rain_count,
            ],
            dtype=np.float32,
        )
    return result


def weather_grid(root: Path, year: int, grid: dict, crs: str):
    stations = json.loads((root / "weather" / "stations.json").read_text())
    points, records = [], []
    project = Transformer.from_crs("EPSG:4326", "EPSG:5179", always_xy=True)
    for station in stations:
        path = root / "weather" / str(year) / (f"{station['USAF']}-{station['WBAN']}-{year}.gz")
        if path.exists():
            points.append(project.transform(float(station["LON"]), float(station["LAT"])))
            records.append(daily_weather(path))
    if not points:
        raise ValueError(f"{year}년 기상 관측이 없습니다.")
    xs, ys = project.transform(grid["longitude"], grid["latitude"])
    distance, index = cKDTree(points).query(np.column_stack((xs.ravel(), ys.ravel())))
    return records, distance.reshape(xs.shape) / 1000, index.reshape(xs.shape)


class FireReader:
    def __init__(self, root: Path, year: int, meta: dict, use_firms: bool = False):
        self.root, self.meta = root, meta
        self.read_file = lru_cache(maxsize=12)(self._read_file)
        manifest = json.loads((root / f"fire-manifest-{year}.json").read_text())
        self.entries = defaultdict(dict)
        self.replaced = 0
        self.source_delays = []
        for record in manifest["files"]:
            path = Path(record["path"])
            if not path.exists() or file_sha256(path) != record["sha256"]:
                raise ValueError(f"원본 무결성 오류: {path.name}")
            if record["asset"] != "FireMask":
                continue
            # 위성·타일·실제 내부 날짜마다 최신 실제 원본 제작본을 사용한다.
            tile = ".".join(path.name.split(".")[:3:2])
            with rasterio.open(path) as src:
                dates = band_dates(src.tags(), src.count)
            for band, day in enumerate(dates, 1):
                old = self.entries[day].get(tile)
                if old is not None:
                    self.replaced += 1
                    if old[2] >= record["production_datetime"]:
                        continue
                self.entries[day][tile] = (str(path), band, record["production_datetime"])
                produced = date.fromisoformat(record["production_datetime"][:10])
                self.source_delays.append((produced - day).days)
        self.firms_points = defaultdict(list)
        self.firms_counts = {"raw_rows": 0, "accepted_rows": 0, "duplicate_rows": 0}
        if use_firms:
            manifest = json.loads((root / "firms" / f"manifest-{year}.json").read_text())
            project = Transformer.from_crs("EPSG:4326", meta["crs_wkt"], always_xy=True)
            inverse = ~Affine(*meta["transform"])
            seen = set()
            for record in manifest:
                path = Path(record["path"])
                if file_sha256(path) != record["sha256"]:
                    raise ValueError("FIRMS 원본 SHA 불일치")
                with path.open() as source:
                    for point in csv.DictReader(source):
                        self.firms_counts["raw_rows"] += 1
                        if point["version"] != "2":
                            raise ValueError("VIIRS 표준 과학제품 Collection 2 버전이 아닙니다.")
                        if point["type"] != "0" or point["confidence"] not in ("n", "h"):
                            continue
                        day = date.fromisoformat(point["acq_date"])
                        time = point["acq_time"].zfill(4)
                        if day.year != year or not (
                            0 <= int(time[:2]) < 24 and 0 <= int(time[2:]) < 60
                        ):
                            raise ValueError("VIIRS 관측 시각 오류")
                        lat, lon, frp = (float(point[k]) for k in ("latitude", "longitude", "frp"))
                        if not np.isfinite([lat, lon, frp]).all() or frp < 0:
                            raise ValueError("VIIRS 좌표/FRP가 유효하지 않습니다.")
                        key = (point["satellite"], day, time, lat, lon)
                        if key in seen:
                            self.firms_counts["duplicate_rows"] += 1
                            continue
                        seen.add(key)
                        x, y = project.transform(lon, lat)
                        col, row = inverse * (x, y)
                        row, col = int(np.floor(row)), int(np.floor(col))
                        h, w = meta["shape"]
                        if 0 <= row < h and 0 <= col < w:
                            self.firms_points[day].append((row, col, frp))
                            self.firms_counts["accepted_rows"] += 1

    def _read_file(self, name: str):
        path = Path(name)
        arrays = []
        for suffix in ("FireMask", "QA", "MaxFRP"):
            p = path.with_name(path.name.replace("_FireMask.tif", f"_{suffix}.tif"))
            with rasterio.open(p) as src:
                dates = band_dates(src.tags(), src.count)
                if suffix == "FireMask":
                    expected = dates
                if dates != expected:
                    raise ValueError("FireMask/QA/FRP의 실제 날짜가 다릅니다.")
                # 동일 격자를 정수 창으로 자른다. 보간으로 화재 정답을 퍼뜨리지 않는다.
                target = Affine(*self.meta["transform"])
                col, row = ~src.transform * (target.c, target.f)
                if not np.allclose([row, col], np.round([row, col]), atol=1e-5):
                    raise ValueError("화재 원본 격자가 정렬되지 않습니다.")
                h, w = self.meta["shape"]
                window = rasterio.windows.Window(round(col), round(row), w, h)
                arrays.append(src.read(window=window, boundless=True, fill_value=0))
        return arrays

    def daily(self, day: date):
        mask = np.zeros(self.meta["shape"], dtype=np.uint8)
        frp = np.zeros(self.meta["shape"], dtype=np.float32)
        for path, band, _ in self.entries.get(day, {}).values():
            raw, qa, radiative = self.read_file(path)
            classified = classify(raw[band - 1], qa[band - 1])
            mask = np.maximum(mask, classified)
            frp = np.maximum(frp, np.where(classified == 9, radiative[band - 1] * 0.1, 0))
        for row, col, radiative in self.firms_points.get(day, []):
            mask[row, col] = 9
            frp[row, col] = max(frp[row, col], radiative)
        return mask, frp


def build(root: Path, output: Path, config: Path, years: list[int]):
    cfg = json.loads(config.read_text())
    output.mkdir(parents=True, exist_ok=True)
    if any(year in cfg["locked_test_years"] for year in years):
        raise ValueError("최종 평가 연도는 별도 고정·해제 절차가 필요합니다.")
    if not set(years) <= set(cfg["years"]):
        raise ValueError("계약에 없는 연도입니다.")
    (output / "config.json").write_text(config.read_text())
    meta = make_grid(root, output, cfg)
    grid = dict(np.load(output / "grid.npz"))
    forest = grid["forest"]
    reports = {}
    for year in years:
        path = output / f"{year}.parquet"
        if path.exists():
            raise FileExistsError(f"기존 데이터는 덮어쓰지 않습니다: {path}")
        reader = FireReader(root, year, meta, use_firms=cfg.get("include_viirs", False))
        weather, station_distance, station_index = weather_grid(root, year, grid, meta["crs_wkt"])
        history, writer, stats = (
            [],
            None,
            {"rows": 0, "positives": 0, "days": 0, "new_observation_positives": 0, "daily": []},
        )
        day = date(year, 1, 1)
        missing_counts = dict.fromkeys(FEATURES, 0)
        current, frp = reader.daily(day)
        while day.year == year:
            following, next_frp = reader.daily(day + timedelta(days=1))
            fire = (current == 9) & forest
            observed = np.isin(current, [5, 9])
            history.append((fire.astype(np.uint8), (observed & forest).astype(np.uint8)))
            history = history[-7:]
            if allowed_day(day, cfg["year_boundary_exclusion_days"]) and fire.any():
                distance, nearest = nearest_fire(fire, forest, grid)
                candidate = forest & (distance <= cfg["candidate_distance_km"])
                eligible = candidate & np.isin(following, [5, 9])
                rows, cols = np.where(eligible)
                if len(rows):
                    idx = (rows, cols)
                    previous = np.where(observed, (current == 9).astype(float), np.nan)
                    neighbors = (
                        convolve(fire.astype(np.float32), np.ones((3, 3)), mode="constant") - fire
                    )
                    angle = 2 * np.pi * (day.timetuple().tm_yday - 1) / 365.25
                    nearest_idx = (nearest[0][idx], nearest[1][idx])
                    columns = {
                        "previous_fire": previous[idx],
                        "previous_unknown": ~observed[idx],
                        "fire_neighbors_3": neighbors[idx],
                        "fire_neighbors_11": uniform_filter(
                            fire.astype(float), 11, mode="constant"
                        )[idx]
                        * 121,
                        "observed_fraction_11": uniform_filter(
                            observed.astype(float), 11, mode="constant"
                        )[idx],
                        "distance_to_previous_fire_km": distance[idx],
                        "nearest_fire_dx_km": (
                            grid["easting_m"][nearest_idx] - grid["easting_m"][idx]
                        )
                        / 1000,
                        "nearest_fire_dy_km": (
                            grid["northing_m"][nearest_idx] - grid["northing_m"][idx]
                        )
                        / 1000,
                        "previous_frp_mw": np.where(observed[idx], frp[idx], np.nan),
                        "nearby_frp_mw": frp[nearest_idx],
                        "fire_days_last_7": sum(h[0][idx] for h in history),
                        "observed_days_last_7": sum(h[1][idx] for h in history),
                        "forest_fraction": grid["forest_fraction"][idx],
                        "landcover_class": grid["landcover_class"][idx],
                        "elevation_m": grid["elevation_m"][idx],
                        "slope_degrees": grid["slope_degrees"][idx],
                        "day_of_year_sin": np.full(len(rows), np.sin(angle)),
                        "day_of_year_cos": np.full(len(rows), np.cos(angle)),
                        "station_distance_km": station_distance[idx],
                    }
                    values = np.array([w.get(day, np.full(len(WEATHER), np.nan)) for w in weather])
                    selected = values[station_index[idx]]
                    selected[station_distance[idx] > 50] = np.nan
                    for i, name in enumerate(WEATHER):
                        columns[name] = selected[:, i]
                    y = (following[idx] == 9).astype(np.int8)
                    columns = {k: np.array(columns[k], dtype=np.float32) for k in FEATURES}
                    for name, values in columns.items():
                        missing_counts[name] += int(np.isnan(values).sum())
                    table = pa.table(
                        {
                            **columns,
                            "fire_next_day": y,
                            "feature_date": [day] * len(rows),
                            "target_date": [day + timedelta(days=1)] * len(rows),
                            "row": rows.astype(np.int32),
                            "col": cols.astype(np.int32),
                            "latitude": grid["latitude"][idx],
                            "longitude": grid["longitude"][idx],
                        }
                    )
                    if writer is None:
                        writer = pq.ParquetWriter(path, table.schema, compression="zstd")
                    writer.write_table(table)
                    stats["rows"] += len(y)
                    stats["positives"] += int(y.sum())
                    stats["new_observation_positives"] += int(
                        ((y == 1) & (previous[idx] == 0)).sum()
                    )
                    stats["days"] += 1
                    stats["daily"].append(
                        {
                            "date": str(day),
                            "rows": len(y),
                            "positives": int(y.sum()),
                            "candidate_cells": int(candidate.sum()),
                        }
                    )
            day += timedelta(days=1)
            current, frp = following, next_frp
        if writer:
            writer.close()
        else:
            raise ValueError(f"{year}년에 학습 가능한 행이 없습니다.")
        stats.update(
            sha256=file_sha256(path),
            config_sha256=file_sha256(config),
            build_source_sha256=file_sha256(Path(__file__)),
            source_duplicate_days_replaced=reader.replaced,
            archive_production_delay_days_min=min(reader.source_delays),
            archive_production_delay_days_max=max(reader.source_delays),
            firms_counts=reader.firms_counts,
            positive_dates=sum(d["positives"] > 0 for d in stats["daily"]),
            missing_fraction={k: n / stats["rows"] for k, n in missing_counts.items()},
        )
        reports[str(year)] = stats
        (output / f"report-{year}.json").write_text(json.dumps(stats, indent=2) + "\n")
        reader.read_file.cache_clear()
        print(
            json.dumps({"year": year, **{k: v for k, v in stats.items() if k != "daily"}}),
            flush=True,
        )
    report = {
        "profile": cfg["profile"],
        "config_sha256": file_sha256(config),
        "features": list(FEATURES),
        "target": cfg["target"],
        "years": reports,
        "operational_use": False,
        "probability_calibrated": False,
        "limitations": [
            cfg["availability"],
            "열 이상 관측은 지상 산불의 완전한 정답이 아님",
            "관측불가 정답 제외로 구름 조건의 평가가 빠짐",
            "2015년 토지피복의 변화와 위성 1km 혼합 픽셀 오차",
            "거리·변위·경사는 국내 미터 좌표계 EPSG:5179로 계산한 근사",
            "강수 합은 실제 관측된 시간만의 합이며 하루 총량이나 무강수의 증거가 아님",
            "사건 ID·현장 피해·도달 시간·위치별 개인 영향 정답 없음",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--years", type=int, nargs="+", required=True)
    args = parser.parse_args()
    build(args.root, args.output, args.config, args.years)


if __name__ == "__main__":
    main()
