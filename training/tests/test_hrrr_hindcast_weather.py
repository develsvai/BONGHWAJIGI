"""Reject ambiguous forecast inputs and verify geographic vector conventions."""

from io import BytesIO

import numpy as np
import pytest

from bonghwa_training import hrrr_hindcast_weather as weather


def grib_message(variable="UGRD", hour=2, flags=8):
    def section(number, size):
        data = bytearray(size)
        data[:4] = size.to_bytes(4, "big")
        data[4] = number
        return data

    identity = section(1, 21)
    identity[5:7] = (7).to_bytes(2, "big")
    identity[11] = 1
    identity[12:14] = (2019).to_bytes(2, "big")
    identity[14:19] = bytes([9, 4, 20, 0, 0])
    identity[20] = 1
    grid = section(3, 81)
    grid[12:14] = (30).to_bytes(2, "big")
    grid[46] = flags
    product = section(4, 34)
    product[9:11] = bytes([2, weather.VARIABLES[variable]])
    product[17] = 1
    product[18:22] = hour.to_bytes(4, "big")
    product[22:24] = bytes([103, 0])
    product[24:28] = (10).to_bytes(4, "big")
    header = bytearray(b"GRIB\0\0\0\2" + b"\0" * 8)
    result = header + identity + grid + product
    result += section(5, 5) + section(6, 5) + section(7, 5) + b"7777"
    result[8:16] = len(result).to_bytes(8, "big")
    return bytes(result)


def test_grib_time_height_component_and_frame():
    result = weather.inspect_grib(grib_message(), "UGRD", 2)
    assert result["grid_relative"] is True
    assert result["valid_time_utc"] == "2019-09-04T22:00:00+00:00"
    assert result["height_m"] == 10
    assert weather.inspect_grib(grib_message(flags=0), "UGRD", 2)["grid_relative"] is False


@pytest.mark.parametrize("change", ["truncated", "joined", "cycle", "height", "component", "hour"])
def test_grib_rejects_wrong_forecast_or_field(change):
    raw = bytearray(grib_message())
    if change == "truncated":
        raw = raw[:7]
    elif change == "joined":
        raw += grib_message()
    elif change == "cycle":
        raw[16 + 16] = 21
    elif change == "height":
        raw[16 + 21 + 81 + 27] = 80
    elif change == "component":
        raw = bytearray(grib_message("VGRD"))
    else:
        raw = bytearray(grib_message(hour=3))
    with pytest.raises(ValueError):
        weather.inspect_grib(bytes(raw), "UGRD", 2)


def test_index_requires_exact_cycle_hour_and_unique_ten_metre_wind():
    idx = (
        b"1:0:d=2019090420:UGRD:10 m above ground:2 hour fcst:\n"
        b"2:120:d=2019090420:VGRD:10 m above ground:2 hour fcst:\n"
        b"3:230:d=2019090420:TMP:2 m above ground:2 hour fcst:\n"
    )
    assert weather.index_ranges(idx, 2) == {"UGRD": (0, 119), "VGRD": (120, 229)}
    for bad in (
        b"",
        b"malformed",
        idx.replace(b"d=2019090420", b"d=2019090421"),
        idx.replace(b"10 m above ground", b"80 m above ground"),
        idx.replace(b"2:120", b"2:0"),
        idx + idx,
    ):
        with pytest.raises(ValueError):
            weather.index_ranges(bad, 2)
    with pytest.raises(ValueError):
        weather.index_ranges(idx, 3)


def test_vector_rotation_preserves_speed_and_cardinal_direction():
    east, north = weather.grid_to_true(np.array([0.0, 1.0]), np.array([1.0, 0.0]), 90.0)
    np.testing.assert_allclose(east, [1, 0], atol=1e-14)
    np.testing.assert_allclose(north, [0, -1], atol=1e-14)
    u, v, angle = np.array([2.0, -5.0, 0.0]), np.array([4.0, 2.0, -7.0]), [-15.0, 10.0, 0.0]
    e, n = weather.grid_to_true(u, v, angle)
    np.testing.assert_allclose(np.hypot(e, n), np.hypot(u, v))
    back_u, back_v = weather.grid_to_true(e, n, -np.array(angle))
    np.testing.assert_allclose(back_u, u)
    np.testing.assert_allclose(back_v, v)


@pytest.mark.parametrize(
    "status,header,body",
    [
        (200, "bytes 100-103/200", b"abcd"),
        (206, "bytes 0-3/200", b"abcd"),
        (206, "bytes 100-103/200", b"abcde"),
    ],
)
def test_range_request_cannot_silently_download_full_archive(
    tmp_path, monkeypatch, status, header, body
):
    class Response(BytesIO):
        pass

    response = Response(body)
    response.status = status
    response.headers = {"Content-Range": header}
    monkeypatch.setattr(weather.urllib.request, "urlopen", lambda *a, **k: response)
    target = tmp_path / "field.grib2"
    with pytest.raises(ValueError, match="exact bounded"):
        weather.fetch("https://example.test/data", target, byte_range=(100, 103))
    assert not target.exists()
