import numpy as np

from bonghwa_training.hourly_context import Weather, past_record, weather_values


def test_rounded_weather_is_past_and_stale_weather_is_missing():
    times = np.array([0, 3600, 7200, 10800])
    assert past_record(times, issue=8100) == 1
    assert past_record(times, issue=1800) is None
    assert past_record(times, issue=30000) is None


def test_weather_qc_distinguishes_calm_trace_and_missing():
    rows = np.array(
        [
            [2022, 3, 4, 0, 200, 100, 10000, 90, 30, 0, -1, 0],
            [2022, 3, 4, 1, 200, 250, 10000, -9999, 0, 0, -9999, 0],
        ]
    )
    values = weather_values(rows)
    assert values[0, 0] == 20
    np.testing.assert_allclose(values[0, 3:5], [-3, 0], atol=1e-6)
    assert values[0, 5] == 0
    assert np.isnan(values[1, 1]) and np.isnan(values[1, 5])
    np.testing.assert_array_equal(values[1, 2:5], [0, 0, 0])


def test_station_without_wind_does_not_hide_nearby_past_wind():
    from scipy.spatial import cKDTree

    w = Weather.__new__(Weather)
    w.tree = cKDTree([[0, 0], [1000, 0]])
    times = np.array([0, 3600, 7200])
    missing_wind = np.tile([20, 50, np.nan, np.nan, np.nan, np.nan], (3, 1))
    observed = np.tile([21, 60, 3, -3, 0, np.nan], (3, 1))
    observed[-1, 2:5] = [99, 99, 99]  # 미래 관측은 사용하면 안 된다.
    w.records = [(times, missing_wind), (times, observed)]
    result = w.at(np.array([[0, 0]]), np.array([8100]))
    np.testing.assert_allclose(result[0, 2:5], [3, -3, 0])
    np.testing.assert_allclose(result[0, 6:], [1, 1.25])
