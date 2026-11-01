import urllib.error

import numpy as np
import pytest

from bonghwa_training.kma_download import acquire_one, load_key, validate_original


def test_private_key_file_is_data_not_shell(tmp_path, monkeypatch):
    monkeypatch.delenv("KMA_APIHUB_AUTH_KEY", raising=False)
    p = tmp_path / "training.env"
    p.write_text('KMA_APIHUB_AUTH_KEY="literal$(not-executed)"\n')
    p.chmod(0o600)
    assert load_key(p) == "literal$(not-executed)"
    p.chmod(0o644)
    with pytest.raises(ValueError, match="600"):
        load_key(p)


def test_html_auth_error_is_not_valid_netcdf(tmp_path):
    p = tmp_path / "bad.part"
    p.write_bytes(b"<html>permission denied</html>")
    with pytest.raises(ValueError, match="NetCDF"):
        validate_original(p)


def test_http_error_does_not_expose_auth_url_or_body(tmp_path, monkeypatch):
    from datetime import UTC, datetime

    def fail(url, **kwargs):
        raise urllib.error.HTTPError(url, 403, "secret-token", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", fail)
    with pytest.raises(RuntimeError) as caught:
        acquire_one(tmp_path, datetime(2022, 3, 4, tzinfo=UTC), "secret-token")
    assert "403" in str(caught.value)
    assert "secret-token" not in str(caught.value)
    assert not list(tmp_path.glob("*.nc"))


def test_ff_zero_cloud_and_industrial_heat_are_not_negative_labels():
    from bonghwa_training.kma_event import classify

    ff = np.array([0, 0, 1, 1, 0, 1, 1, 0, 255])
    dqf = np.array([2, 4, 8, 9, 7, 10, 2, 1, 255])
    np.testing.assert_array_equal(classify(ff, dqf), [0, -1, 1, 1, -1, -1, -1, -1, -1])


def test_lambert_grid_matches_official_corner_control_points():
    from bonghwa_training.kma_event import grid_from_projection

    attrs = {
        "grid_mapping_name": "lambert_conformal_conic",
        "standard_parallel1": 30,
        "standard_parallel2": 60,
        "origin_latitude": 38,
        "central_meridian": 126,
        "false_easting": 0,
        "false_northing": 0,
        "image_width": 900,
        "image_height": 900,
        "pixel_size": 2000,
        "upper_left_easting": -899000,
        "upper_left_northing": 899000,
        "lower_right_easting": 899000,
        "lower_right_northing": -899000,
    }
    _, _, grid, _ = grid_from_projection(attrs, [100, 20, 145, 50])
    np.testing.assert_allclose(
        [
            [grid["longitude"][0, 0], grid["latitude"][0, 0]],
            [grid["longitude"][0, -1], grid["latitude"][0, -1]],
            [grid["longitude"][-1, 0], grid["latitude"][-1, 0]],
            [grid["longitude"][-1, -1], grid["latitude"][-1, -1]],
        ],
        [
            [113.996418, 45.728965],
            [138.003582, 45.728965],
            [116.753260, 29.312252],
            [135.246740, 29.312252],
        ],
        atol=1e-6,
        rtol=0,
    )


def test_rate_limit_is_retried_with_delay_and_is_not_missing_data(tmp_path, monkeypatch):
    from datetime import UTC, datetime

    from bonghwa_training.kma_download import RateLimited, acquire_with_backoff

    calls, delays = [], []

    def download(*args):
        calls.append(1)
        if len(calls) == 1:
            raise RateLimited(45)
        return {"sha256": "fixture"}

    monkeypatch.setattr("bonghwa_training.kma_download.acquire_one", download)
    monkeypatch.setattr("bonghwa_training.kma_download.time.sleep", delays.append)
    assert acquire_with_backoff(tmp_path, datetime(2022, 3, 4, tzinfo=UTC), "unused") == {
        "sha256": "fixture"
    }
    assert delays == [45]
