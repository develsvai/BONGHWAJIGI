import gzip
import json
from datetime import date

import numpy as np
import pytest

from bonghwa_training.korea_build import (
    WEATHER,
    allowed_day,
    band_dates,
    build,
    classify,
    daily_weather,
    ground_slope,
    nearest_fire,
)


def test_cloud_low_confidence_and_water_never_become_observed_negatives():
    raw = np.arange(10, dtype=np.uint8)
    qa = np.full(10, 6, dtype=np.uint8)  # land, day
    np.testing.assert_array_equal(classify(raw, qa), [0, 0, 0, 0, 0, 5, 0, 7, 9, 9])
    np.testing.assert_array_equal(classify(raw, np.zeros_like(qa)), np.zeros(10))
    np.testing.assert_array_equal(classify(raw, np.full_like(qa, 3)), np.zeros(10))


def test_internal_dates_override_catalog_eight_day_extent():
    assert band_dates({"Dates": "2022-03-30 2022-03-31"}, 2) == [
        date(2022, 3, 30),
        date(2022, 3, 31),
    ]
    for tags in (
        {"Dates": "2022-03-30"},
        {"Dates": "2022-03-30 2022-03-30"},
        {"Dates": "2022-03-31 2022-03-30"},
    ):
        with pytest.raises(ValueError):
            band_dates(tags, 2)


def test_temporal_gap_and_locked_final_year(tmp_path):
    assert not allowed_day(date(2022, 1, 30), 30)
    assert allowed_day(date(2022, 1, 31), 30)
    assert not allowed_day(date(2022, 12, 2), 30)
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"locked_test_years": [2025]}))
    with pytest.raises(ValueError, match="최종 평가"):
        build(tmp_path / "no_sources", tmp_path / "out", cfg, [2025])


def test_weather_rounded_boundary_and_trace_precipitation(tmp_path):
    path = tmp_path / "station.gz"
    rows = [[2022, 3, 5, hour, 200, 100, 10130, 90, 40, 0, -1, -9999] for hour in range(23)]
    rows.append([2022, 3, 5, 23, 600, 500, 10130, 270, 990, 0, 9990, -9999])
    with gzip.open(path, "wt") as out:
        out.write("\n".join(" ".join(map(str, row)) for row in rows))
    values = dict(zip(WEATHER, daily_weather(path)[date(2022, 3, 5)], strict=True))
    assert values["temperature_mean_c"] == 20
    assert values["wind_speed_max_ms"] == 4
    assert values["wind_u_mean_ms"] == pytest.approx(-4)
    assert values["observed_precipitation_sum_mm"] == 0
    assert values["weather_hours"] == 23
    assert values["humidity_min_pct"] == pytest.approx(52.54, abs=0.1)


def test_missing_rain_is_not_zero_and_duplicate_hours_rejected(tmp_path):
    path = tmp_path / "station.gz"
    row = "2022 3 5 12 -9999 -9999 -9999 -9999 -9999 -9999 -9999 -9999"
    with gzip.open(path, "wt") as out:
        out.write(row)
    values = daily_weather(path)[date(2022, 3, 5)]
    assert np.isnan(values[WEATHER.index("observed_precipitation_sum_mm")])
    assert values[WEATHER.index("weather_hours")] == 0
    with gzip.open(path, "wt") as out:
        out.write(row + "\n" + row)
    with pytest.raises(ValueError, match="중복 시간"):
        daily_weather(path)


def test_distance_and_slope_respect_sheared_satellite_grid():
    rows, cols = np.indices((3, 3))
    # 위성 격자에서 수직 한 칸은 이 예에서 동쪽 1km+북쪽 1km다.
    east = cols * 1000.0 + rows * 1000.0
    north = rows * 1000.0
    elevation = east * 0.1
    np.testing.assert_allclose(
        ground_slope(elevation, east, north), np.rad2deg(np.arctan(0.1)), atol=1e-5
    )
    fire = np.zeros((3, 3), dtype=bool)
    fire[0, 0] = True
    distance, nearest = nearest_fire(
        fire, np.ones_like(fire), {"easting_m": east, "northing_m": north}
    )
    assert distance[1, 0] == pytest.approx(np.sqrt(2))
    assert distance[1, 1] == pytest.approx(np.sqrt(5))
    assert tuple(nearest[:, 2, 2]) == (0, 0)
