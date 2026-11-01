import hashlib
import io
import json
import zipfile
from datetime import timedelta

import numpy as np
import pytest
import rasterio
import shapefile
import shapely
from pyproj import CRS, Transformer
from shapely.geometry import box

from bonghwa_training.gofer_hindcast_data import (
    BOUNDS,
    NONBURNABLE_CODES,
    SHAPE,
    START,
    TARGET_CRS,
    TRANSFORM,
    fuel_grid,
    initial_masks,
    perimeter_layer,
    prepare_truth,
    source_receipt,
)


def archive_fixture(tmp_path, future_size=1500):
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    writer = shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYGON)
    for key, kind in [("fname", "C"), ("fyear", "N"), ("tUTC", "C"), ("timestep", "N")]:
        writer.field(key, kind, size=40)
    to_geo = Transformer.from_crs(TARGET_CRS, 4326, always_xy=True)
    # Initial bounds snap to the exact pre-fixed Walker rectangle.
    initial = box(697165, 4434531, 698136, 4436384)
    for hour in (0, 1, 3, 6):
        geom = initial if hour == 0 else box(697165, 4434531, 698136 + future_size, 4436384)
        projected = shapely.transform(
            geom, lambda xy: np.column_stack(to_geo.transform(xy[:, 0], xy[:, 1]))
        )
        writer.poly([list(projected.exterior.coords)[::-1]])
        writer.record("Walker", 2019, (START + timedelta(hours=hour)).isoformat(), 15 + hour)
    writer.close()
    path = tmp_path / "GOFER.zip"
    with zipfile.ZipFile(path, "w") as archive:
        base = "GOFER/GOFER_Combined/GOFERC_fireProg"
        for ext, payload in [
            ("shp", shp.getvalue()),
            ("shx", shx.getvalue()),
            ("dbf", dbf.getvalue()),
            ("prj", CRS.from_epsg(4326).to_wkt("WKT1_ESRI")),
        ]:
            archive.writestr(base + "." + ext, payload)
    return path


def test_selected_initial_and_future_times_are_distinct(tmp_path):
    path = archive_fixture(tmp_path)
    _, initial, meta = perimeter_layer(path)
    assert meta["valid_time_utc"] == START.isoformat() and meta["timestep"] == 15
    _, future, future_meta = perimeter_layer(path, START + timedelta(hours=3))
    assert future_meta["timestep"] == 18 and future.area > initial.area
    with pytest.raises(ValueError, match="missing"):
        perimeter_layer(path, START - timedelta(hours=15))


def test_changing_future_geometry_cannot_change_initial_grid_or_masks(tmp_path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    first.mkdir()
    second.mkdir()
    _, a, _ = perimeter_layer(archive_fixture(first, 1500))
    _, b, _ = perimeter_layer(archive_fixture(second, 150000))
    initial_a, domain_a = initial_masks(a)
    initial_b, domain_b = initial_masks(b)
    np.testing.assert_array_equal(initial_a, initial_b)
    np.testing.assert_array_equal(domain_a, domain_b)
    assert int(initial_a.sum()) > 1  # Initial burned polygon is not reduced to one ignition.


def test_domain_excludes_rectangle_corners_and_preserves_initial_cells():
    geometry = box(697165, 4434531, 698136, 4436384)
    initial, domain = initial_masks(geometry)
    assert not domain[0, 0] and not domain[-1, -1]
    assert np.all(domain[initial == 1] == 1)
    rows, cols = np.indices(SHAPE)
    distances = shapely.distance(
        geometry,
        shapely.points(
            (BOUNDS[0] + (cols + 0.5) * 100).ravel(), (BOUNDS[3] - (rows + 0.5) * 100).ravel()
        ),
    ).reshape(SHAPE)
    assert np.all(distances[domain == 1] <= 20000)
    assert np.all(distances[domain == 0] > 20000)


def test_wrong_initial_domain_is_rejected_instead_of_resizing_to_future():
    with pytest.raises(ValueError, match="pre-fixed"):
        initial_masks(box(0, 0, 1000, 1000))


def write_fuel(path, values, crs=TARGET_CRS, nodata=None):
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        count=1,
        dtype="int16",
        crs=crs,
        transform=TRANSFORM,
        height=SHAPE[0],
        width=SHAPE[1],
        nodata=nodata,
    ) as dst:
        dst.write(values.astype("int16"), 1)


def test_real_nonburnable_codes_are_not_unknown_and_codes_are_preserved(tmp_path):
    values = np.full(SHAPE, 186, dtype="int16")
    values[0, :5] = NONBURNABLE_CODES
    path = tmp_path / "fuel.tif"
    write_fuel(path, values)
    actual, unknown, info = fuel_grid(path)
    np.testing.assert_array_equal(actual, values)
    assert not unknown.any()
    assert info["tiff_nodata"] is None and info["service_nodata"] == -9999


@pytest.mark.parametrize("code", [-9999, 0, 255, 999])
def test_missing_or_unsupported_fuel_never_becomes_nonburnable(tmp_path, code):
    values = np.full(SHAPE, 186, dtype="int16")
    values[200, 200] = code
    path = tmp_path / "fuel.tif"
    write_fuel(path, values)
    actual, unknown, _ = fuel_grid(path)
    assert actual[200, 200] == code and unknown[200, 200] == 1
    assert unknown.sum() == 1


def test_wrong_crs_fuel_rejected(tmp_path):
    path = tmp_path / "fuel.tif"
    write_fuel(path, np.full(SHAPE, 186), crs="EPSG:32652")
    with pytest.raises(ValueError, match="fixed"):
        fuel_grid(path)


def test_acquired_source_hash_is_checked(tmp_path):
    path = tmp_path / "source.dat"
    path.write_bytes(b"original")
    sidecar = path.with_name(path.name + ".source.json")
    sidecar.write_text(
        json.dumps(
            {
                "url": "https://example.org/source",
                "bytes": 8,
                "sha256": hashlib.sha256(b"original").hexdigest(),
            }
        )
    )
    assert source_receipt(path)["bytes"] == 8
    path.write_bytes(b"modified")
    with pytest.raises(ValueError, match="checksum"):
        source_receipt(path)


def test_truth_stage_requires_committed_initial_manifest(tmp_path):
    with pytest.raises(FileNotFoundError):
        prepare_truth(tmp_path / "raw", tmp_path)
