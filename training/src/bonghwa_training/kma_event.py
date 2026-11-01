"""GK2A 재처리 FF의 관측 재현용 입력. 실제 과거 수신 시각을 만들어내지 않는다."""

import json
from datetime import datetime
from pathlib import Path

import netCDF4
import numpy as np
from pyproj import CRS, Transformer

from bonghwa_training.download import file_sha256


def classify(ff, quality):
    # KMA ATBD 표 2.9. FF=0 자체는 fill/background도 포함하므로 음성으로 충분하지 않다.
    state = np.full(ff.shape, -1, dtype=np.int8)
    state[(ff == 0) & (quality == 2)] = 0
    state[(ff == 1) & np.isin(quality, [8, 9])] = 1
    return state


def grid_from_projection(attrs, bbox, ellipsoid="WGS84"):
    if attrs["grid_mapping_name"] != "lambert_conformal_conic":
        raise ValueError("확인되지 않은 GK2A 투영입니다.")
    crs = CRS.from_proj4(
        f"+proj=lcc +lat_1={attrs['standard_parallel1']} +lat_2={attrs['standard_parallel2']} "
        f"+lat_0={attrs['origin_latitude']} +lon_0={attrs['central_meridian']} "
        f"+x_0={attrs['false_easting']} +y_0={attrs['false_northing']} +ellps={ellipsoid} +units=m"
    )
    cols, rows = int(attrs["image_width"]), int(attrs["image_height"])
    spacing = float(attrs["pixel_size"])
    xs = float(attrs["upper_left_easting"]) + np.arange(cols) * spacing
    ys = float(attrs["upper_left_northing"]) - np.arange(rows) * spacing
    if not np.isclose(xs[-1], float(attrs["lower_right_easting"])) or not np.isclose(
        ys[-1], float(attrs["lower_right_northing"])
    ):
        raise ValueError("GK2A 격자 간격과 모서리가 충돌합니다.")
    xx, yy = np.meshgrid(xs, ys)
    lon, lat = Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform(xx, yy)
    inside = (lon >= bbox[0]) & (lon <= bbox[2]) & (lat >= bbox[1]) & (lat <= bbox[3])
    rr, cc = np.where(inside)
    if not len(rr):
        raise ValueError("사건 영역이 FF 원본에 없습니다.")
    rs, cs = slice(rr.min(), rr.max() + 1), slice(cc.min(), cc.max() + 1)
    # 실제 지상 거리의 근사에는 Korea 2000 / Unified CS를 사용한다.
    east, north = Transformer.from_crs("EPSG:4326", "EPSG:5179", always_xy=True).transform(
        lon[rs, cs], lat[rs, cs]
    )
    return (
        rs,
        cs,
        {
            "longitude": lon[rs, cs],
            "latitude": lat[rs, cs],
            "east_m": east,
            "north_m": north,
            "inside_bbox": inside[rs, cs],
        },
        crs.to_wkt(),
    )


def read_event(root: Path, event: dict, cfg: dict, *, maximum_issue_epoch_seconds=None):
    manifest = json.loads((root / event["id"] / "manifest.json").read_text())
    files = sorted(manifest["files"], key=lambda r: r["requested_observation_utc"])
    if maximum_issue_epoch_seconds is not None:
        files = [
            record
            for record in files
            if datetime.fromisoformat(record["requested_observation_utc"]).timestamp()
            + cfg["assumed_input_delay_minutes"] * 60
            <= maximum_issue_epoch_seconds
        ]
    if not files:
        empty = np.empty((0, 0, 0), dtype=np.int8)
        time = np.empty(0, dtype=np.float64)
        grid = {name: np.empty((0, 0)) for name in ("latitude", "longitude", "east_m", "north_m")}
        return (
            empty,
            empty.astype(float),
            empty.astype(float),
            time,
            time,
            time,
            grid,
            "unavailable-no-source",
        )
    with netCDF4.Dataset(files[0]["path"]) as src:
        p = src["gk2a_imager_projection"]
        attrs = {k: p.getncattr(k) for k in p.ncattrs()}
    rs, cs, grid, crs = grid_from_projection(
        attrs, event["bbox"], cfg.get("earth_ellipsoid", "WGS84")
    )
    states, starts = [], []
    for record in files:
        path = Path(record["path"])
        if file_sha256(path) != record["sha256"]:
            raise ValueError("국내 FF 원본 SHA 불일치")
        when = datetime.fromisoformat(record["requested_observation_utc"])
        if when.year >= 2025:
            raise ValueError("국내 최종 연도의 정답은 잠금 상태입니다.")
        with netCDF4.Dataset(path) as src:
            p = src["gk2a_imager_projection"]
            if attrs != {k: p.getncattr(k) for k in p.ncattrs()}:
                raise ValueError("사건 내 FF 투영/격자가 바뀌었습니다.")
            original = str(getattr(src, "origianl_sourece_file", ""))
            if when.strftime("%Y%m%d%H%M") not in original:
                raise ValueError("요청 시각과 FF 내부 원본 파일 시각 불일치")
            state = classify(
                np.ma.filled(src["FF"][rs, cs], 255),
                np.ma.filled(src["DQF_FF"][rs, cs], 255),
            )
            state[~grid["inside_bbox"]] = -1
            states.append(state)
            starts.append(when.timestamp())
    starts = np.array(starts)
    # 이 배열은 가정한 지연이다. 당시 발행/수신 시각이라는 의미가 아니다.
    assumed_available = starts + cfg["assumed_input_delay_minutes"] * 60
    states = np.array(states)
    unknown_power = np.full(states.shape, np.nan, dtype=np.float32)
    return (
        states,
        unknown_power,
        unknown_power.copy(),
        starts,
        starts.copy(),
        assumed_available,
        grid,
        crs,
    )
