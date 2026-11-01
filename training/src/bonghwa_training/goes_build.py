"""사건 분리 1·3·6시간 관측 위험 자료. 미래 구름/누락은 비화재가 아니다."""

import argparse
import json
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import netCDF4
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from pyproj import CRS, Transformer
from scipy.ndimage import convolve
from scipy.spatial import cKDTree

from bonghwa_training.download import file_sha256
from bonghwa_training.goes_release import verify_release

FEATURES = (
    "distance_fire_km",
    "nearest_fire_dx_km",
    "nearest_fire_dy_km",
    "neighbors_3",
    "neighbors_7",
    "nearby_frp_mw",
    "nearby_temperature_k",
    "distance_fire_30m_km",
    "distance_fire_60m_km",
    "closing_speed_30m_kmh",
    "closing_speed_60m_kmh",
    "fire_frames_last_hour",
    "clear_frames_last_hour",
    "utc_hour_sin",
    "utc_hour_cos",
    "horizon_hours",
)

RECENT_FEATURES = (
    "distance_recent_fire_60m_km",
    "nearest_recent_fire_60m_dx_km",
    "nearest_recent_fire_60m_dy_km",
    "nearest_recent_fire_60m_age_minutes",
    "own_last_fire_60m_age_minutes",
    "recent_fire_60m_neighbors_3",
    "recent_fire_60m_neighbors_7",
)


def recent_fire_features(states, starts, issue, grid, indices):
    """미래 프레임을 쓰지 않는 관측 이력. 과거 화재가 현재도 연소 중이라는 뜻은 아니다."""
    if np.any(starts > issue):
        raise ValueError("과거 화재 이력에 미래 관측이 포함됐습니다.")
    seen = np.any(states == 1, axis=0)
    distance, nearest = distances(seen.astype(np.int8), grid)
    if distance is None:
        return {name: np.full(len(indices[0]), np.nan) for name in RECENT_FEATURES}
    last = np.max(np.where(states == 1, starts[:, None, None], -np.inf), axis=0)
    near = (nearest[0][indices], nearest[1][indices])
    age = np.where(np.isfinite(last), (issue - last) / 60, np.nan)
    return dict(
        zip(
            RECENT_FEATURES,
            [
                distance[indices],
                (grid["east_m"][near] - grid["east_m"][indices]) / 1000,
                (grid["north_m"][near] - grid["north_m"][indices]) / 1000,
                age[near],
                age[indices],
                convolve(seen.astype(float), np.ones((3, 3)), mode="constant")[indices],
                convolve(seen.astype(float), np.ones((7, 7)), mode="constant")[indices],
            ],
            strict=True,
        )
    )


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def classify(mask, quality):
    result = np.full(mask.shape, -1, dtype=np.int8)
    result[(quality == 1) & (mask == 100)] = 0
    result[(quality == 0) & np.isin(mask, [10, 11, 30, 31])] = 1
    return result


def future_target(states: np.ndarray, complete: bool) -> np.ndarray:
    """양성 증거가 있으면 1, 전체 관측이 명백한 비화재일 때만 0, 나머지는 검열."""
    if not len(states):
        raise ValueError("미래 관측 구간이 비었습니다.")
    positive = np.any(states == 1, axis=0)
    result = np.full(states.shape[1:], -1, dtype=np.int8)
    if complete:
        result[np.all(states == 0, axis=0)] = 0
    result[positive] = 1
    return result


def chronological_indices(starts, ends, available):
    """스캔 모드가 파일명 정렬을 바꿔도 실제 시각 순서를 유지한다."""
    order = np.lexsort((available, starts))
    kept = []
    for i in order:
        if kept and starts[i] == starts[kept[-1]]:
            if abs(ends[i] - ends[kept[-1]]) > 1:
                raise ValueError("같은 시작 시각의 관측 구간이 충돌합니다.")
            continue  # 재처리 중복은 최초 공개본만 사용한다.
        kept.append(i)
    return np.asarray(kept, dtype=int)


def crop_grid(sample: Path, bbox: list):
    with netCDF4.Dataset(sample) as source:
        attrs = {
            k: source["goes_imager_projection"].getncattr(k)
            for k in source["goes_imager_projection"].ncattrs()
        }
        geos = CRS.from_cf(attrs)
        height = attrs["perspective_point_height"]
        xs = np.array(source["x"][:], dtype=np.float64) * height
        ys = np.array(source["y"][:], dtype=np.float64) * height
    project = Transformer.from_crs("EPSG:4326", geos, always_xy=True)
    # 경계 네 변을 촘촘히 변환해 비선형 투영의 모서리 누락을 방지한다.
    west, south, east, north = bbox
    longitude = np.concatenate(
        [np.linspace(west, east, 50)] * 2 + [np.full(50, west), np.full(50, east)]
    )
    latitude = np.concatenate(
        [np.full(50, south), np.full(50, north)] + [np.linspace(south, north, 50)] * 2
    )
    px, py = project.transform(longitude, latitude)
    cols = np.where((xs >= min(px)) & (xs <= max(px)))[0]
    rows = np.where((ys >= min(py)) & (ys <= max(py)))[0]
    if not len(rows) or not len(cols):
        raise ValueError("사건 영역이 GOES 원본에 포함되지 않습니다.")
    rs, cs = slice(rows.min(), rows.max() + 1), slice(cols.min(), cols.max() + 1)
    x, y = np.meshgrid(xs[cs], ys[rs])
    lon, lat = Transformer.from_crs(geos, "EPSG:4326", always_xy=True).transform(x, y)
    local = CRS.from_proj4(
        f"+proj=aeqd +lat_0={(south + north) / 2} +lon_0={(west + east) / 2} +datum=WGS84 +units=m"
    )
    ex, ny = Transformer.from_crs(geos, local, always_xy=True).transform(x, y)
    return (
        rs,
        cs,
        {"longitude": lon, "latitude": lat, "east_m": ex, "north_m": ny, "x": xs[cs], "y": ys[rs]},
        geos.to_wkt(),
    )


def read_event(root: Path, event: dict):
    manifest = json.loads((root / event["id"] / "manifest.json").read_text())
    files = sorted(manifest["files"], key=lambda r: r["path"])
    rs, cs, grid, crs = crop_grid(Path(files[0]["path"]), event["bbox"])
    states, powers, temperatures, starts, ends, available = [], [], [], [], [], []
    projection_attrs = None
    for record in files:
        path = Path(record["path"])
        if file_sha256(path) != record["sha256"]:
            raise ValueError(f"GOES SHA 불일치: {path.name}")
        with netCDF4.Dataset(path) as source:
            projection = source["goes_imager_projection"]
            current_attrs = {k: projection.getncattr(k) for k in projection.ncattrs()}
            if projection_attrs is None:
                if not CRS.from_cf(current_attrs).equals(CRS.from_wkt(crs)):
                    raise ValueError("첫 관측과 기준 위성 투영이 다릅니다.")
                projection_attrs = current_attrs
            elif current_attrs != projection_attrs:
                raise ValueError("사건 내 위성 투영 속성이 바뀌었습니다.")
            for axis, selection in (("x", cs), ("y", rs)):
                current = np.array(source[axis][selection], dtype=np.float64) * (
                    projection.perspective_point_height
                )
                if current.shape != grid[axis].shape or not np.allclose(
                    current, grid[axis], atol=0.01, rtol=0
                ):
                    raise ValueError("사건 내 위성 격자가 바뀌었습니다.")
            state = classify(
                np.ma.filled(source["Mask"][rs, cs], -99), np.ma.filled(source["DQF"][rs, cs], 255)
            )
            power = np.ma.filled(source["Power"][rs, cs], np.nan).astype(np.float32)
            temp = np.ma.filled(source["Temp"][rs, cs], np.nan).astype(np.float32)
            states.append(state)
            powers.append(np.where((state == 1) & (power >= 0), power, np.nan))
            temperatures.append(np.where((state == 1) & (temp > 0), temp, np.nan))
            start, end = utc(source.time_coverage_start), utc(source.time_coverage_end)
            created = utc(source.date_created)
            modified = parsedate_to_datetime(record["headers"]["Last-Modified"])
            if end < start or created < end:
                raise ValueError("관측/제작 시각 순서가 유효하지 않습니다.")
            starts.append(start.timestamp())
            ends.append(end.timestamp())
            available.append(max(created, modified).timestamp())
    order = chronological_indices(np.array(starts), np.array(ends), np.array(available))
    return (
        np.array(states)[order],
        np.array(powers)[order],
        np.array(temperatures)[order],
        np.array(starts)[order],
        np.array(ends)[order],
        np.array(available)[order],
        grid,
        crs,
    )


def distances(state: np.ndarray, grid: dict):
    fire = state == 1
    if not fire.any():
        return None, None
    rows, cols = np.where(fire)
    points = np.column_stack((grid["east_m"][fire], grid["north_m"][fire]))
    query = np.column_stack((grid["east_m"].ravel(), grid["north_m"].ravel()))
    dist, index = cKDTree(points).query(query)
    dims = state.shape
    nearest = (rows[index].reshape(dims), cols[index].reshape(dims))
    return dist.reshape(dims) / 1000, nearest


def input_snapshot(observations, cfg, index):
    """Construct all eligible input-time candidates without consulting any future labels."""
    state, power, temp, starts, ends, available, grid, _ = observations
    i = index
    issue = available[i]
    valid_inputs = np.where((available <= issue) & (ends <= issue))[0]
    if not len(valid_inputs) or valid_inputs[-1] != i:
        raise ValueError("현재 입력과 발행 시각이 일치하지 않습니다.")
    distance, nearest = distances(state[i], grid)
    if distance is None:
        return None
    candidate = (state[i] == 0) & (distance <= cfg["candidate_distance_km"])
    rr, cc = np.where(candidate)
    if not len(rr):
        return None
    idx = (rr, cc)
    fire = (state[i] == 1).astype(float)
    n3 = convolve(fire, np.ones((3, 3)), mode="constant")[idx]
    n7 = convolve(fire, np.ones((7, 7)), mode="constant")[idx]
    recent = valid_inputs[ends[valid_inputs] >= issue - 3600]
    past_distance = []
    for minutes in (30, 60):
        prior = valid_inputs[ends[valid_inputs] <= issue - minutes * 60]
        if not len(prior) or ends[prior[-1]] < issue - (minutes + 10) * 60:
            past_distance.append(np.full(len(rr), np.nan))
            continue
        d, _ = distances(state[prior[-1]], grid)
        past_distance.append(d[idx] if d is not None else np.full(len(rr), np.nan))
    near_idx = (nearest[0][idx], nearest[1][idx])
    hour = (issue % 86400) / 86400 * 2 * np.pi
    base = {
        "distance_fire_km": distance[idx],
        "nearest_fire_dx_km": (grid["east_m"][near_idx] - grid["east_m"][idx]) / 1000,
        "nearest_fire_dy_km": (grid["north_m"][near_idx] - grid["north_m"][idx]) / 1000,
        "neighbors_3": n3,
        "neighbors_7": n7,
        "nearby_frp_mw": power[i][near_idx],
        "nearby_temperature_k": temp[i][near_idx],
        "distance_fire_30m_km": past_distance[0],
        "distance_fire_60m_km": past_distance[1],
        "closing_speed_30m_kmh": (past_distance[0] - distance[idx]) * 2,
        "closing_speed_60m_kmh": past_distance[1] - distance[idx],
        "fire_frames_last_hour": (state[recent][:, rr, cc] == 1).sum(axis=0),
        "clear_frames_last_hour": (state[recent][:, rr, cc] == 0).sum(axis=0),
        "utc_hour_sin": np.full(len(rr), np.sin(hour)),
        "utc_hour_cos": np.full(len(rr), np.cos(hour)),
    }
    if cfg.get("recent_fire_features"):
        base.update(recent_fire_features(state[recent], starts[recent], issue, grid, idx))
    return rr, cc, base


def build_event(root: Path, output: Path, event: dict, cfg: dict):
    if cfg.get("reader") == "gk2a":
        from bonghwa_training.kma_event import read_event as read_kma_event

        observations = read_kma_event(root, event, cfg)
    else:
        observations = read_event(root, event)
    state, power, temp, starts, ends, available, grid, crs = observations
    if np.any(np.diff(starts) <= 0):
        raise ValueError("관측 시점 중복/역순")
    initial = utc(event["start_utc"]).timestamp()
    stop = initial + event["hours"] * 3600
    writer = None
    path = output / f"{event['id']}.parquet"
    if path.exists():
        raise FileExistsError(path)
    stats = {
        "rows": 0,
        "positives": 0,
        "anchors": 0,
        "censored_rows": 0,
        "horizons": {str(h): {"rows": 0, "positives": 0} for h in cfg["horizons_hours"]},
    }
    # 사건의 전체 미래 영상을 읽었어도 아래 입력 조회에는 available <= issue를 강제한다.
    for i in range(len(starts)):
        if not (initial <= starts[i] < stop):
            continue
        if int(starts[i] // 300) % (cfg["input_interval_minutes"] // 5) != 0:
            continue
        issue = available[i]
        if issue > starts[i] + 1800:
            continue  # 뒤늦게 공개/재업로드된 자료를 그때 이용 가능했던 입력으로 보지 않는다.
        valid_inputs = np.where((available <= issue) & (ends <= issue))[0]
        if not len(valid_inputs) or valid_inputs[-1] != i:
            continue
        snapshot = input_snapshot(observations, cfg, i)
        if snapshot is None:
            continue
        rr, cc, base = snapshot
        idx = (rr, cc)
        for horizon in cfg["horizons_hours"]:
            future = np.where((starts > issue) & (ends <= issue + horizon * 3600))[0]
            if not len(future):
                continue
            cadence = cfg["source_cadence_minutes"] * 60
            complete = (
                len(future) == horizon * 3600 // cadence
                and np.max(np.diff(starts[future]), initial=0) <= cadence * 1.1
                and starts[future[0]] - issue <= cadence * 1.1
                and issue + horizon * 3600 - ends[future[-1]] <= cadence * 1.1
            )
            target = future_target(state[future][:, rr, cc], complete)
            known = target >= 0
            stats["censored_rows"] += int((~known).sum())
            if not known.any():
                continue
            columns = {k: np.asarray(v[known], dtype=np.float32) for k, v in base.items()}
            columns["horizon_hours"] = np.full(known.sum(), horizon, dtype=np.float32)
            table = pa.table(
                {
                    **columns,
                    "fire_within_horizon": target[known],
                    "issue_epoch_seconds": np.full(known.sum(), issue),
                    "max_input_available_epoch_seconds": np.full(
                        known.sum(), available[valid_inputs].max()
                    ),
                    "row": rr[known].astype(np.int32),
                    "col": cc[known].astype(np.int32),
                    "latitude": grid["latitude"][idx][known],
                    "longitude": grid["longitude"][idx][known],
                    "input_time_basis": [
                        "assumed_delay_not_actual_release"
                        if cfg.get("reader") == "gk2a"
                        else "public_release_proxy"
                    ]
                    * int(known.sum()),
                }
            )
            if writer is None:
                writer = pq.ParquetWriter(path, table.schema, compression="zstd")
            writer.write_table(table)
            stats["rows"] += int(known.sum())
            stats["positives"] += int((target == 1).sum())
            stats["horizons"][str(horizon)]["rows"] += int(known.sum())
            stats["horizons"][str(horizon)]["positives"] += int((target == 1).sum())
        stats["anchors"] += 1
    if writer is None:
        names = list(FEATURES) + (list(RECENT_FEATURES) if cfg.get("recent_fire_features") else [])
        empty = {k: pa.array([], type=pa.float32()) for k in names}
        empty.update(
            {
                "fire_within_horizon": pa.array([], type=pa.int8()),
                "issue_epoch_seconds": pa.array([], type=pa.float64()),
                "max_input_available_epoch_seconds": pa.array([], type=pa.float64()),
                "row": pa.array([], type=pa.int32()),
                "col": pa.array([], type=pa.int32()),
                "latitude": pa.array([], type=pa.float64()),
                "longitude": pa.array([], type=pa.float64()),
                "input_time_basis": pa.array([], type=pa.string()),
            }
        )
        pq.write_table(pa.table(empty), path, compression="zstd")
        stats["unusable_reason"] = (
            "관측 가능한 현재 화재/후보/정답이 없어 0행. 비화재 음성으로 간주하지 않음"
        )
    else:
        writer.close()
    stats.update(
        sha256=file_sha256(path),
        event=event,
        native_grid_crs=crs,
        native_grid_shape=list(grid["latitude"].shape),
        source_frames=len(starts),
        source_manifest_sha256=file_sha256(root / event["id"] / "manifest.json"),
        input_availability_note=cfg.get("input_availability"),
    )
    (output / f"{event['id']}-report.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps({k: v for k, v in stats.items() if k not in ("native_grid_crs",)}), flush=True)
    return stats


def build(root: Path, output: Path, config: Path, *, release: Path | None = None):
    cfg = json.loads(config.read_text())
    output.mkdir(parents=True, exist_ok=True)
    if release:
        verify_release(release, config)
    (output / "config.json").write_text(config.read_text())
    reports = {}
    for event in cfg["events"]:
        if (event["split"] == "test") == bool(release):
            reports[event["id"]] = build_event(root, output, event, cfg)
    report = {
        "profile": cfg["profile"],
        "features": list(FEATURES)
        + (list(RECENT_FEATURES) if cfg.get("recent_fire_features") else []),
        "events": reports,
        "config_sha256": file_sha256(config),
        "builder_sha256": file_sha256(Path(__file__)),
        "frozen_release_sha256": file_sha256(release) if release else None,
        "operational_use": False,
        "target": cfg["target"],
        "target_country": cfg.get("domain", "국외 연구용, 국내 외부 검증 전"),
        "limitations": cfg.get(
            "limitations",
            [
                "6개 사건 중 학습3/튜닝1/보정1/잠금1로 사건 수가 매우 적음",
                "환경 기상/연료/지형 및 진화 조치 입력을 아직 결합하지 않음",
                "위성 격자 열 이상은 실제 화선·개인 피해·도달 시각과 다름",
                "미래 구름/누락 구간의 음성 정답 제외로 관측 선택 편향이 있음",
                "국내 위성/실황/예보 입력과 동등성·지연·보정을 별도 검증해야 함",
            ],
        ),
    }
    (output / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--release", type=Path, help="고정된 모델로 최종 사건만 구축")
    args = parser.parse_args()
    build(args.root, args.output, args.config, release=args.release)


if __name__ == "__main__":
    main()
