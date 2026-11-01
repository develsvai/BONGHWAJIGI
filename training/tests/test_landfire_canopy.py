"""Synthetic metadata/encoding/budget guards; no network or wildfire labels."""

import io
import json

import numpy as np
import pytest
import rasterio

from bonghwa_training import landfire_canopy as module


def metadata(product):
    return {
        "name": f"Landfire_LF2016/LF2016_{product}_CONUS",
        "pixelType": "S16",
        "bandCount": 1,
        "noDataValue": -9999,
        "pixelSizeX": 30,
        "pixelSizeY": 30,
    }


@pytest.mark.parametrize(
    "product,documentation,scale",
    [
        ("CC", "percent cover", 1.0),
        ("CH", "meters * 10", 0.1),
        ("CBH", "meters * 10", 0.1),
        ("CBD", "kg m<sup>3</sup> * 100", 0.01),
    ],
)
def test_official_units_are_explicit(product, documentation, scale):
    actual = module.validate_metadata(product, metadata(product), documentation)
    assert actual["physical_scale"] == scale
    with pytest.raises(ValueError, match="units"):
        module.validate_metadata(product, metadata(product), "unverified")


def test_wrong_product_or_nodata_rejected():
    wrong = metadata("CH") | {"name": "Landfire_LF2025/LF2025_CH_CONUS"}
    with pytest.raises(ValueError, match="Unexpected"):
        module.validate_metadata("CH", wrong, "meters * 10")
    with pytest.raises(ValueError, match="sentinel"):
        module.validate_metadata("CH", metadata("CH") | {"noDataValue": 0}, "meters * 10")


def grids():
    values = {
        p: np.ma.array(np.full(module.SHAPE, v, dtype="int16"), mask=False)
        for p, v in (("CC", 50), ("CH", 100), ("CBH", 20), ("CBD", 15))
    }
    return values, np.ones(module.SHAPE, dtype=bool)


def test_physical_scaling_preserves_raw_values():
    values, domain = grids()
    quality, unknown = module.canopy_quality(values, domain)
    assert quality["products"]["CH"]["physical_max"] == 10
    assert quality["products"]["CBD"]["physical_max"] == 0.15
    assert not unknown.any()
    assert values["CH"][0, 0] == 100


def test_missing_is_not_zero_canopy():
    values, domain = grids()
    for p in values:
        values[p][0, 0] = 0
    quality, _ = module.canopy_quality(values, domain)
    assert quality["products"]["CC"]["active_zero_cells"] == 1
    values["CC"].mask[0, 0] = True
    with pytest.raises(ValueError, match="Missing"):
        module.canopy_quality(values, domain)
    domain[0, 0] = False
    _, unknown = module.canopy_quality(values, domain)
    assert unknown[0, 0]


@pytest.mark.parametrize("product,value", [("CC", 101), ("CBD", -1), ("CH", 9999)])
def test_physical_range_invalid_not_clipped(product, value):
    values, domain = grids()
    values[product][0, 0] = value
    with pytest.raises(ValueError, match="invalid canopy"):
        module.canopy_quality(values, domain)


def test_base_cannot_exceed_top_and_nonforest_must_be_consistent():
    values, domain = grids()
    values["CBH"][0, 0] = 200
    with pytest.raises(ValueError, match="inconsistency"):
        module.canopy_quality(values, domain)
    values["CBH"][0, 0] = 20
    values["CC"][0, 0] = 0
    with pytest.raises(ValueError, match="inconsistency"):
        module.canopy_quality(values, domain)


def test_density_only_source_inconsistency_is_retained_and_reported():
    values, domain = grids()
    for product in ("CC", "CH", "CBH"):
        values[product][0, 0] = 0
    quality, unknown = module.canopy_quality(values, domain)
    assert quality["density_without_cover_or_height_cells"] == 1
    assert values["CBD"][0, 0] == 15
    assert not unknown[0, 0]


def test_missing_tag_does_not_hide_service_nodata_sentinel(tmp_path):
    path = tmp_path / "no-tag.tif"
    values = np.zeros(module.SHAPE, dtype="int16")
    values[1, 1] = -9999
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=module.SHAPE[0],
        width=module.SHAPE[1],
        count=1,
        dtype="int16",
        crs=module.CRS,
        transform=module.TRANSFORM,
    ) as target:
        target.write(values, 1)
    result = module.read_grid(path)
    assert result.mask[1, 1] and not result.mask[0, 0]


def test_twelve_fixed_requests_preserve_raw_nearest_values():
    plan = module.requests_plan()
    assert len(plan) == 12
    raw = [r for r in plan if r["role"] == "raw_canopy_grid"]
    assert len(raw) == 4
    assert all(r["request_parameters"]["interpolation"] == "RSP_NearestNeighbor" for r in raw)
    assert all(
        json.loads(r["request_parameters"]["renderingRule"]) == {"rasterFunction": "None"}
        for r in raw
    )
    assert all("LF2025" not in r["url"] for r in plan)


class Response(io.BytesIO):
    status = 200
    headers = {}

    def geturl(self):
        return "https://example.test"


def test_download_limit_applies_without_content_length(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "MAX_BYTES", 3)
    with pytest.raises(ValueError, match="exceeds"):
        module.bounded_fetch(
            "https://example.test", tmp_path / "file", opener=lambda *_a, **_k: Response(b"1234")
        )
    assert not (tmp_path / "file").exists()


def test_grid_mismatch_is_rejected(tmp_path):
    path = tmp_path / "bad.tif"
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=2,
        width=2,
        count=1,
        dtype="int16",
        crs=module.CRS,
        transform=module.TRANSFORM,
        nodata=-9999,
    ) as target:
        target.write(np.zeros((2, 2), dtype="int16"), 1)
    with pytest.raises(ValueError, match="grid"):
        module.read_grid(path)
