import json

import numpy as np
import pytest
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin

from bonghwa_training.download import file_sha256
from bonghwa_training.korea_terrain import (
    CENTER,
    CRS,
    DEM_NAMES,
    SHAPE,
    TREE_CLASSES,
    build_terrain,
    project_dem,
    project_landcover,
    scenario_grid,
    terrain_derivatives,
    verified_source,
)


def write_raster(path, array, transform, crs="EPSG:32652", nodata=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=array.shape[0],
        width=array.shape[1],
        count=1,
        dtype=array.dtype,
        transform=transform,
        crs=crs,
        nodata=nodata,
    ) as dst:
        dst.write(array, 1)
    return path


@pytest.mark.parametrize(
    ("east_gradient", "north_gradient", "expected_aspect"),
    [(1, 0, 270), (-1, 0, 90), (0, 1, 180), (0, -1, 0), (1, 1, 225)],
)
def test_downslope_aspect_cardinal_and_diagonal_planes(
    east_gradient, north_gradient, expected_aspect
):
    row, col = np.mgrid[:7, :8]
    z = col * 100 * east_gradient - row * 100 * north_gradient
    slope, aspect, flat = terrain_derivatives(z, 100)
    np.testing.assert_allclose(
        slope, np.degrees(np.arctan(np.hypot(east_gradient, north_gradient)))
    )
    np.testing.assert_allclose(aspect, expected_aspect)
    assert not flat.any()


def test_flat_aspect_is_explicit_numeric_convention():
    slope, aspect, flat = terrain_derivatives(np.zeros((5, 5)), 100)
    assert not slope.any() and not aspect.any()
    assert flat.all()


def test_terrain_rejects_nonfinite():
    values = np.zeros((5, 5))
    values[2, 2] = np.nan
    with pytest.raises(ValueError, match="finite"):
        terrain_derivatives(values, 100)


def test_dem_mosaic_crosses_two_tile_boundary_without_zero_nodata(tmp_path):
    # North/south tiles form the same analytic northing plane, continuous across seam.
    north = np.repeat((1000 - (np.arange(10) + 0.5) * 100)[:, None], 10, axis=1)
    south = np.repeat((0 - (np.arange(10) + 0.5) * 100)[:, None], 10, axis=1)
    a = write_raster(
        tmp_path / "north.tif", north.astype("float32"), from_origin(0, 1000, 100, 100)
    )
    b = write_raster(tmp_path / "south.tif", south.astype("float32"), from_origin(0, 0, 100, 100))
    transform = from_origin(200, 250, 100, 100)
    result, qc = project_dem([a, b], transform, (5, 5))
    np.testing.assert_allclose(result[:, 2], [200, 100, 0, -100, -200])
    assert qc["valid_coverage_fraction"] == 1
    assert result[2, 2] == 0
    with pytest.raises(ValueError, match="footprint"):
        project_dem([a], transform, (5, 5))


def test_dem_nodata_hole_cannot_be_hidden_by_bilinear_interpolation(tmp_path):
    values = np.ones((20, 20), dtype="float32")
    values[9:11, 9:11] = -9999
    path = write_raster(tmp_path / "dem.tif", values, from_origin(0, 2000, 100, 100), nodata=-9999)
    with pytest.raises(ValueError, match="coverage"):
        project_dem([path], from_origin(500, 1500, 100, 100), (10, 10))


def test_geographic_dem_reprojects_zero_elevation_as_valid(tmp_path):
    path = write_raster(
        tmp_path / "dem.tif",
        np.zeros((300, 300), dtype="float32"),
        from_origin(129.15, 37.15, 0.001, 0.001),
        crs="EPSG:4326",
    )
    transform, _ = scenario_grid()
    result, qc = project_dem([path], transform, SHAPE)
    assert result.shape == SHAPE
    assert np.isfinite(result).all() and (result == 0).all()
    assert qc["source_zero_elevation_preserved"]


def test_class_nearest_preserves_unknown_and_mixed_class_not_tree(tmp_path):
    values = np.array([[70, 100, 210], [0, 250, 190], [151, 160, 170]], dtype="uint8")
    path = write_raster(tmp_path / "cci.tif", values, from_origin(0, 900, 300, 300), nodata=0)
    classes, forest, water, unknown = project_landcover(path, from_origin(0, 900, 100, 100), (9, 9))
    assert set(np.unique(classes)) == set(values.ravel())  # No interpolated class IDs.
    assert (forest[:3, :3] == 1).all()
    assert (forest[:3, 3:6] == 0).all()  # 100 tree/shrub mosaic is not explicit tree cover.
    assert (forest[3:6, :6] == 255).all()
    assert (unknown[3:6, :6] == 1).all()
    assert (water[3:6, :6] == 255).all()
    assert (water[:3, 6:] == 1).all()
    assert (forest[6:, :] == 1).all()


def test_source_hash_and_byte_size_are_verified(tmp_path):
    path = write_raster(
        tmp_path / "a.tif", np.ones((3, 3), dtype="float32"), from_origin(0, 300, 100, 100)
    )
    sidecar = tmp_path / "source.json"
    record = {
        "sha256": file_sha256(path),
        "bytes": path.stat().st_size,
        "url": "https://example.org/a.tif",
    }
    sidecar.write_text(json.dumps(record))
    assert verified_source(path, sidecar)["nodata"] is None
    sidecar.write_text(json.dumps({**record, "sha256": "0" * 64}))
    with pytest.raises(ValueError, match="SHA256"):
        verified_source(path, sidecar)
    sidecar.write_text(json.dumps({**record, "bytes": 1}))
    with pytest.raises(ValueError, match="byte count"):
        verified_source(path, sidecar)


def test_requested_center_is_domain_center_and_not_a_cell_center():
    transform, center = scenario_grid()
    np.testing.assert_allclose(transform * (50, 50), center)
    np.testing.assert_allclose(
        Transformer.from_crs(CRS, 4326, always_xy=True).transform(*center), CENTER, atol=1e-10
    )
    assert transform.a == 100 and transform.e == -100
    assert transform * (49.5, 49.5) != center


def raw_fixture(tmp_path):
    raw = tmp_path / "raw"
    (raw / "stac").mkdir(parents=True)
    items = []
    for name, north in zip(DEM_NAMES, (37 + 1 / 2400, 38 + 1 / 2400), strict=True):
        path = write_raster(
            raw / "static" / "dem" / name,
            np.full((1200, 1200), 500, dtype="float32"),
            from_origin(129 - 1 / 2400, north, 1 / 1200, 1 / 1200),
            crs="EPSG:4326",
        )
        url = f"https://example.org/{name}"
        path.with_name(path.name + ".source.json").write_text(
            json.dumps(
                {
                    "sha256": file_sha256(path),
                    "url": url,
                    "bytes": path.stat().st_size,
                }
            )
        )
        items.append(
            {
                "id": path.stem,
                "collection": "cop-dem-glo-90",
                "properties": {"gsd": 90},
                "assets": {"data": {"href": url}},
            }
        )
    (raw / "stac" / "dem.json").write_text(json.dumps({"features": items}))
    path = write_raster(
        raw / "static" / "landcover-2015-korea.tif",
        np.full((120, 120), 70, dtype="uint8"),
        from_origin(129.1, 37.2, 1 / 360, 1 / 360),
        crs="EPSG:4326",
        nodata=0,
    )
    url = "https://example.org/cci2015.tif"
    (raw / "static" / "landcover-2015-korea.json").write_text(
        json.dumps(
            {
                "sha256": file_sha256(path),
                "url": url,
            }
        )
    )
    (raw / "stac" / "landcover.json").write_text(
        json.dumps(
            {
                "collection": "esa-cci-lc",
                "assets": {"lccs_class": {"href": url}},
                "properties": {"start_datetime": "2015-01-01T00:00:00Z"},
            }
        )
    )
    return raw


def test_complete_build_has_consistent_rasters_manifest_and_provenance(tmp_path):
    raw = raw_fixture(tmp_path)
    output = tmp_path / "terrain"
    report = build_terrain(raw, output)
    assert report["status"] == "ready"
    assert report["aspect_reference"] == "grid_north_clockwise_downslope"
    assert not report["operational_use"] and not report["fuel_model_mapping_performed"]
    assert report["forest_mask_definition"]["tree_classes"] == list(TREE_CLASSES)
    assert report["qc"]["dem"]["valid_target_pixels_including_halo"] == 102 * 102
    assert report["qc"]["landcover_unknown_pixels"] == 0
    assert (output / "manifest.json").read_bytes() == (output / "report.json").read_bytes()
    for name, metadata in report["outputs"].items():
        assert metadata["path"] == name
        assert file_sha256(output / name) == metadata["sha256"]
        with rasterio.open(output / name) as src:
            assert src.shape == SHAPE and src.crs.to_string() == CRS
            assert list(src.transform)[:6] == report["transform"]
    with pytest.raises(ValueError, match="empty"):
        build_terrain(raw, output)


def test_build_checks_hash_before_writing_any_output(tmp_path):
    raw = raw_fixture(tmp_path)
    source = raw / "static" / "dem" / DEM_NAMES[0]
    with source.open("ab") as target:
        target.write(b"changed")
    output = tmp_path / "terrain"
    with pytest.raises(ValueError, match="SHA256"):
        build_terrain(raw, output)
    assert not output.exists()
