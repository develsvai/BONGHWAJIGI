"""국내 과거 재현 자료에 기확보 지형·식생·과거 기상을 결합한다."""

import argparse
import gzip
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from pyproj import Geod, Transformer
from scipy.spatial import cKDTree

from bonghwa_training.download import file_sha256
from bonghwa_training.goes_build import FEATURES

CONTEXT = [
    "forest_fraction",
    "elevation_m",
    "slope_degrees",
    "temperature_c",
    "humidity_pct",
    "wind_speed_ms",
    "wind_u_ms",
    "wind_v_ms",
    "observed_hourly_precipitation_mm",
    "weather_station_distance_km",
    "weather_age_hours",
    "wind_toward_target_ms",
    "wind_cross_target_ms",
]


def weather_values(arr):
    values = arr[:, 4:].astype(np.float32).copy()
    values[values == -9999] = np.nan
    temp, dew, _, direction, speed, _, rain, _ = values.T
    temp, dew, speed = temp / 10, dew / 10, speed / 10
    temp[(temp < -90) | (temp > 65)] = np.nan
    dew[(dew < -100) | (dew > 65) | (dew > temp)] = np.nan
    speed[(speed < 0) | (speed > 100)] = np.nan
    direction[(direction < 0) | (direction > 360)] = np.nan
    u, v = -speed * np.sin(np.deg2rad(direction)), -speed * np.cos(np.deg2rad(direction))
    u[speed == 0], v[speed == 0] = 0, 0
    humidity = 100 * np.exp(17.625 * dew / (243.04 + dew) - 17.625 * temp / (243.04 + temp))
    rain[rain == -1] = 0
    rain[rain < 0] = np.nan
    return np.column_stack((temp, humidity, speed, u, v, rain / 10))


def past_record(times, issue, lag_seconds=3600, maximum_age_seconds=10800):
    i = np.searchsorted(times, issue - lag_seconds, side="right") - 1
    return int(i) if i >= 0 and issue - times[i] <= maximum_age_seconds else None


class Weather:
    def __init__(self, root, year):
        records = json.loads((root / f"weather-manifest-{year}.json").read_text())
        digests = {Path(r["path"]).name: r["sha256"] for r in records if "sha256" in r}
        stations = json.loads((root / "weather/stations.json").read_text())
        project = Transformer.from_crs("EPSG:4326", "EPSG:5179", always_xy=True)
        points, self.records, self.hashes = [], [], {}
        for s in stations:
            p = root / "weather" / str(year) / f"{s['USAF']}-{s['WBAN']}-{year}.gz"
            if p.name not in digests:
                continue
            if file_sha256(p) != digests[p.name]:
                raise ValueError("기상 원본 SHA 불일치")
            with gzip.open(p, "rt") as src:
                arr = np.loadtxt(src, dtype=np.float32, ndmin=2)
            if arr.shape[1] != 12:
                raise ValueError("ISD-Lite 열 수 불일치")
            times = np.array(
                [datetime(*row[:4].astype(int), tzinfo=UTC).timestamp() for row in arr]
            )
            if np.any(np.diff(times) <= 0):
                raise ValueError("기상 시각 중복/역순")
            points.append(project.transform(float(s["LON"]), float(s["LAT"])))
            self.records.append((times, weather_values(arr)))
            self.hashes[str(p)] = digests[p.name]
        if not points:
            raise ValueError("실제 기상 관측소가 없습니다.")
        self.tree = cKDTree(points)

    def at(self, points, issues):
        result = np.full((len(points), 8), np.nan, dtype=np.float32)
        if not len(points):
            return result
        distance, nearest = self.tree.query(points, k=min(8, len(self.records)))
        distance, nearest = distance.reshape(len(points), -1), nearest.reshape(len(points), -1)
        for issue in np.unique(issues):
            rows = np.where(issues == issue)[0]
            snapshots = {}
            for station, (times, values) in enumerate(self.records):
                i = past_record(times, issue)
                while i is not None and not np.isfinite(values[i, 2:5]).all():
                    i = i - 1 if i > 0 and issue - times[i - 1] <= 10800 else None
                if i is not None:
                    snapshots[station] = (values[i], (issue - times[i]) / 3600)
            for rank in range(nearest.shape[1]):
                missing = rows[np.isnan(result[rows, 7])]
                for station in np.unique(nearest[missing, rank]):
                    if station not in snapshots:
                        continue
                    selected = missing[
                        (nearest[missing, rank] == station) & (distance[missing, rank] <= 100000)
                    ]
                    values, age = snapshots[station]
                    result[selected, :6] = values
                    result[selected, 6] = distance[selected, rank] / 1000
                    result[selected, 7] = age
        return result


def context_for_table(table, grid, tree, weather):
    """Same past-only environmental lookup for training and research replay."""
    project = Transformer.from_crs("EPSG:4326", "EPSG:5179", always_xy=True)
    mask = grid["country"]
    points = np.column_stack(
        project.transform(table["longitude"].to_numpy(), table["latitude"].to_numpy())
    )
    distance, index = tree.query(points)
    extra = {}
    for name in CONTEXT[:3]:
        extra[name] = grid[name][mask][index].copy()
        extra[name][distance > 2000] = np.nan
    values = weather.at(points, table["issue_epoch_seconds"].to_numpy())
    for j, name in enumerate(CONTEXT[3:11]):
        extra[name] = values[:, j]
    fire_lon, fire_lat = Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=True).transform(
        points[:, 0] + table["nearest_fire_dx_km"].to_numpy() * 1000,
        points[:, 1] + table["nearest_fire_dy_km"].to_numpy() * 1000,
    )
    azimuth, _, _ = Geod(ellps="WGS84").inv(
        fire_lon, fire_lat, table["longitude"].to_numpy(), table["latitude"].to_numpy()
    )
    east, north = np.sin(np.deg2rad(azimuth)), np.cos(np.deg2rad(azimuth))
    extra["wind_toward_target_ms"] = values[:, 3] * east + values[:, 4] * north
    extra["wind_cross_target_ms"] = values[:, 3] * north - values[:, 4] * east
    return extra


def augment(dataset, raw, static, output, config_output):
    cfg = json.loads((dataset / "config.json").read_text())
    if cfg.get("reader") != "gk2a":
        raise ValueError("국내 재처리 연구 자료에만 결합합니다.")
    output.mkdir(parents=True, exist_ok=False)
    cfg["profile"] += "_context_v1"
    base_features = json.loads((dataset / "report.json").read_text()).get(
        "features", list(FEATURES)
    )
    cfg["feature_names"] = (
        [f for f in base_features if f != "horizon_hours"] + CONTEXT + ["horizon_hours"]
    )
    cfg["context_features"] = CONTEXT
    cfg["weather_time_basis"] = (
        "ISD 사후 QC 반올림 시각. 1시간 이상 과거만 사용. 당시 실시간 가용성 미검증"
    )
    cfg["limitations"] = [s for s in cfg["limitations"] if "기상·연료·지형" not in s] + [
        "기상은 최대100km 내 과거 관측소 실황. 국지풍·돌풍·향후 예보를 대신하지 않음",
        "DSM90/CCI2015를 약1km 감사 격자에서 최근접 표본. 정확한 2km 연료/지형 평균이 아님",
        "진화 활동·연료 수분·사용자 취약성·현장 피해 정답 없음",
    ]
    encoded = json.dumps(cfg, indent=2, ensure_ascii=False) + "\n"
    config_output.write_text(encoded)
    (output / "config.json").write_text(encoded)
    grid = np.load(static / "grid.npz")
    mask = grid["country"]
    tree = cKDTree(np.column_stack((grid["easting_m"][mask], grid["northing_m"][mask])))
    reports, weather = {}, {}
    for event in cfg["events"]:
        if event["split"] == "test":
            continue
        p = dataset / f"{event['id']}.parquet"
        original = json.loads((dataset / f"{event['id']}-report.json").read_text())
        if file_sha256(p) != original["sha256"]:
            raise ValueError("기본 관측 자료 SHA 불일치")
        table = pq.read_table(p)
        year = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00")).year
        if year not in weather:
            weather[year] = Weather(raw, year)
        extra = context_for_table(table, grid, tree, weather[year])
        for name, vals in extra.items():
            table = table.append_column(name, pa.array(vals.astype(np.float32)))
        out = output / p.name
        pq.write_table(table, out, compression="zstd")
        reports[event["id"]] = {
            **original,
            "sha256": file_sha256(out),
            "base_parquet_sha256": file_sha256(p),
            "context_missing_fraction": {
                k: float(np.isnan(v).mean()) if len(v) else None for k, v in extra.items()
            },
        }
        (output / f"{event['id']}-report.json").write_text(
            json.dumps(reports[event["id"]], indent=2, ensure_ascii=False) + "\n"
        )
        print(
            json.dumps(
                {
                    "event": event["id"],
                    "rows": len(table),
                    "missing": reports[event["id"]]["context_missing_fraction"],
                }
            ),
            flush=True,
        )
    report = {
        "profile": cfg["profile"],
        "config_sha256": file_sha256(config_output),
        "features": cfg["feature_names"],
        "events": reports,
        "static_grid_sha256": file_sha256(static / "grid.npz"),
        "weather_station_registry_sha256": file_sha256(raw / "weather/stations.json"),
        "weather_files_sha256": {str(y): w.hashes for y, w in weather.items()},
        "source_sha256": file_sha256(Path(__file__)),
        "operational_use": False,
        "limitations": cfg["limitations"],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("dataset", "raw", "static", "output", "config-output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    augment(a.dataset, a.raw, a.static, a.output, a.config_output)


if __name__ == "__main__":
    main()
