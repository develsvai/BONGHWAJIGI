"""Local, provenance-checked Korean terrain for an explicitly hypothetical fire scenario.

Only static DEM/2015 land-cover sources are read. No fire observations, labels,
weather, fuel-model lookup or network access is involved.
"""

import argparse
import json
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.merge import merge
from rasterio.transform import array_bounds, from_origin
from rasterio.warp import reproject, transform_bounds
from shapely.geometry import box
from shapely.ops import unary_union

from bonghwa_training.download import file_sha256

CENTER = (129.3, 37.0)
CRS = "EPSG:32652"
PIXEL_SIZE_M = 100
SHAPE = (100, 100)
DEM_NAMES = (
    "Copernicus_DSM_COG_30_N36_00_E129_00_DEM.tif",
    "Copernicus_DSM_COG_30_N37_00_E129_00_DEM.tif",
)
TREE_CLASSES = (50, 60, 61, 62, 70, 71, 72, 80, 81, 82, 90, 151, 160, 170)
KNOWN_CLASSES = (
    10,
    11,
    12,
    20,
    30,
    40,
    50,
    60,
    61,
    62,
    70,
    71,
    72,
    80,
    81,
    82,
    90,
    100,
    110,
    120,
    121,
    122,
    130,
    140,
    150,
    151,
    152,
    153,
    160,
    170,
    180,
    190,
    200,
    201,
    202,
    210,
    220,
)


def verified_source(path: Path, sidecar: Path) -> dict:
    """Verify acquired bytes, retaining the original source URL and nodata semantics."""
    record = json.loads(sidecar.read_text())
    actual_hash = file_sha256(path)
    if record.get("sha256") != actual_hash:
        raise ValueError(f"Source SHA256 mismatch: {path.name}")
    size = path.stat().st_size
    if "bytes" in record and record["bytes"] != size:
        raise ValueError(f"Source byte count mismatch: {path.name}")
    url = record.get("url", "")
    if not url.startswith("https://") or "?" in url:
        raise ValueError("Source URL must be unsigned public HTTPS without query credentials")
    with rasterio.open(path) as src:
        if src.count != 1 or src.crs is None:
            raise ValueError(f"Expected one georeferenced band: {path.name}")
        info = {
            "path": str(path),
            "sha256": actual_hash,
            "bytes": size,
            "source_url": url,
            "source_sidecar": str(sidecar),
            "source_sidecar_sha256": file_sha256(sidecar),
            "crs": src.crs.to_string(),
            "shape": list(src.shape),
            "transform": list(src.transform)[:6],
            "bounds": list(src.bounds),
            "dtype": src.dtypes[0],
            "nodata": src.nodata,
        }
    for key in ("derivation", "bbox", "item_id", "retrieved_at_utc", "headers"):
        if key in record:
            info[key] = record[key]
    return info


def scenario_grid():
    """Exactly center a 10 km square; an even grid has four central cell centers."""
    east, north = Transformer.from_crs(4326, CRS, always_xy=True).transform(*CENTER)
    transform = from_origin(east - 5000, north + 5000, PIXEL_SIZE_M, PIXEL_SIZE_M)
    return transform, (east, north)


def terrain_derivatives(elevation: np.ndarray, pixel_size_m: float):
    """Slope and downslope azimuth clockwise from UTM grid north, not true north."""
    z = np.asarray(elevation, dtype=np.float64)
    if z.ndim != 2 or min(z.shape) < 3 or not np.isfinite(z).all():
        raise ValueError("Slope/aspect require a finite 2D elevation grid with a halo")
    if not np.isfinite(pixel_size_m) or pixel_size_m <= 0:
        raise ValueError("Pixel size must be positive")
    dz_south, dz_east = np.gradient(z, pixel_size_m, pixel_size_m, edge_order=2)
    gradient = np.hypot(dz_east, dz_south)
    slope = np.rad2deg(np.arctan(gradient))
    # Downslope east=-dz_east; downslope north=+dz_south for north-up row order.
    aspect = np.mod(np.rad2deg(np.arctan2(-dz_east, dz_south)), 360.0)
    flat = gradient <= 1e-12
    aspect[flat] = 0.0  # Numeric convention only; flat_mask preserves undefined bearing.
    return slope.astype("float32"), aspect.astype("float32"), flat.astype("uint8")


def project_dem(paths: list[Path], transform, shape, dst_crs=CRS):
    """Mosaic before interpolation; reject incomplete footprint or valid-data support.

    NaN is destination bookkeeping only. Source nodata is never rewritten and
    valid zero elevations are retained. A one-cell target halo is supplied by
    the caller so central gradients do not depend on one-sided domain edges.
    """
    with ExitStack() as stack:
        sources = [stack.enter_context(rasterio.open(p)) for p in paths]
        if not sources:
            raise ValueError("No DEM sources")
        reference = sources[0]
        for src in sources:
            if src.count != 1 or src.crs != reference.crs or src.res != reference.res:
                raise ValueError("DEM tiles must have the same CRS, resolution and one band")
            if src.transform.b != 0 or src.transform.d != 0:
                raise ValueError("Rotated source DEM is unsupported")
        bounds = transform_bounds(
            dst_crs, reference.crs, *array_bounds(*shape, transform), densify_pts=41
        )
        # Conservative source-footprint guard includes one native pixel for bilinear support.
        padded = box(
            bounds[0] - reference.res[0],
            bounds[1] - reference.res[1],
            bounds[2] + reference.res[0],
            bounds[3] + reference.res[1],
        )
        footprint = unary_union([box(*src.bounds) for src in sources])
        if not footprint.covers(padded):
            raise ValueError("DEM footprint does not fully cover target and interpolation support")
        mosaic, mosaic_transform = merge(sources, dtype="float32", nodata=np.nan)
        elevation = mosaic[0]
        valid = np.isfinite(elevation).astype("float32")
        projected = np.full(shape, np.nan, dtype="float32")
        support = np.full(shape, np.nan, dtype="float32")
        common = {
            "src_transform": mosaic_transform,
            "src_crs": reference.crs,
            "dst_transform": transform,
            "dst_crs": dst_crs,
            "resampling": Resampling.bilinear,
        }
        reproject(elevation, projected, src_nodata=np.nan, dst_nodata=np.nan, **common)
        # Here zero means missing support and is intentionally a valid value to interpolate.
        reproject(valid, support, src_nodata=None, dst_nodata=np.nan, **common)
    supported = np.isfinite(projected) & np.isfinite(support) & (support >= 1 - 1e-7)
    if not supported.all():
        raise ValueError(f"DEM valid coverage is not 100%: {int(supported.sum())}/{supported.size}")
    return projected, {
        "mosaic_shape": list(elevation.shape),
        "resampling": "bilinear",
        "valid_target_pixels_including_halo": int(supported.sum()),
        "target_pixels_including_halo": int(supported.size),
        "valid_coverage_fraction": 1.0,
        "source_zero_elevation_preserved": True,
        "source_nodata_reassigned": False,
        "footprint_and_interpolation_support_complete": True,
    }


def project_landcover(path: Path, transform, shape, dst_crs=CRS):
    """Nearest CCI class only. Missing/unknown remain unknown, never non-burnable."""
    result = np.zeros(shape, dtype="uint8")
    with rasterio.open(path) as src:
        if src.count != 1 or src.dtypes[0] != "uint8":
            raise ValueError("CCI source must be a single uint8 class band")
        reproject(
            rasterio.band(src, 1),
            result,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=transform,
            dst_crs=dst_crs,
            dst_nodata=0,
            resampling=Resampling.nearest,
        )
    unknown = ~np.isin(result, KNOWN_CLASSES)
    forest = np.isin(result, TREE_CLASSES).astype("uint8")
    water = (result == 210).astype("uint8")
    forest[unknown] = 255
    water[unknown] = 255
    return result, forest, water, unknown.astype("uint8")


def _write_raster(path: Path, array: np.ndarray, transform, *, nodata=None, tags=None):
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=array.shape[0],
        width=array.shape[1],
        count=1,
        dtype=array.dtype,
        crs=CRS,
        transform=transform,
        nodata=nodata,
        compress="deflate",
    ) as dst:
        dst.write(array, 1)
        dst.update_tags(**(tags or {}))
    return {
        "path": path.name,
        "sha256": file_sha256(path),
        "bytes": path.stat().st_size,
        "dtype": str(array.dtype),
        "nodata": nodata,
        "minimum": float(array.min()),
        "maximum": float(array.max()),
    }


def build_terrain(raw_root: Path, output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError(
            "Output directory must be empty; do not overwrite an existing terrain build"
        )
    dem_paths = [raw_root / "static" / "dem" / name for name in DEM_NAMES]
    landcover_path = raw_root / "static" / "landcover-2015-korea.tif"
    dem_sources = [verified_source(p, p.with_name(p.name + ".source.json")) for p in dem_paths]
    landcover_source = verified_source(
        landcover_path, raw_root / "static" / "landcover-2015-korea.json"
    )
    dem_stac_path = raw_root / "stac" / "dem.json"
    landcover_stac_path = raw_root / "stac" / "landcover.json"
    dem_items = {i["id"]: i for i in json.loads(dem_stac_path.read_text())["features"]}
    for path, record in zip(dem_paths, dem_sources, strict=True):
        item = dem_items[path.stem]
        if (
            item["collection"] != "cop-dem-glo-90"
            or item["properties"]["gsd"] != 90
            or item["assets"]["data"]["href"] != record["source_url"]
        ):
            raise ValueError("DEM STAC collection/resolution/URL does not match acquired source")
        if record["crs"] != "EPSG:4326" or not np.isclose(record["transform"][0], 1 / 1200):
            raise ValueError("Expected native Copernicus GLO-90 geographic grid")
        record.update(
            {
                "collection": item["collection"],
                "nominal_resolution_m": 90,
                "stac_datetime": item["properties"].get("datetime"),
            }
        )
    lc_item = json.loads(landcover_stac_path.read_text())
    if (
        lc_item["collection"] != "esa-cci-lc"
        or lc_item["assets"]["lccs_class"]["href"] != landcover_source["source_url"]
        or not lc_item["properties"]["start_datetime"].startswith("2015-")
    ):
        raise ValueError("Expected ESA CCI 2015 source and matching URL")
    landcover_source.update(
        {
            "collection": "esa-cci-lc",
            "year": 2015,
            "nominal_resolution_m": 300,
            "quality_assets_acquired": False,
        }
    )
    transform, center = scenario_grid()
    halo_transform = transform * rasterio.Affine.translation(-1, -1)
    elevation_halo, dem_qc = project_dem(dem_paths, halo_transform, (102, 102))
    slope_halo, aspect_halo, flat_halo = terrain_derivatives(elevation_halo, PIXEL_SIZE_M)
    elevation, slope, aspect, flat = [
        a[1:-1, 1:-1] for a in (elevation_halo, slope_halo, aspect_halo, flat_halo)
    ]
    classes, forest, water, unknown = project_landcover(landcover_path, transform, SHAPE)
    output.mkdir(parents=True, exist_ok=True)
    arrays = {
        "elevation_m.tif": (elevation, None, {"units": "metres", "source": "surface_DSM"}),
        "slope_deg.tif": (slope, None, {"units": "degrees"}),
        "aspect_deg.tif": (
            aspect,
            None,
            {
                "units": "degrees",
                "direction": "downslope_clockwise_from_UTM_grid_north",
                "flat_convention": "0_numeric_only_undefined_direction_see_flat_mask",
            },
        ),
        "flat_mask.tif": (flat, None, {"values": "1=flat;0=nonflat"}),
        "landcover_class.tif": (classes, 0, {"source_year": "2015", "resampling": "nearest"}),
        "forest_mask.tif": (
            forest,
            255,
            {
                "values": "1=explicit_tree_class;0=other_known_class;255=unknown",
                "not_a_fuel_model_or_nonburnable_mask": "true",
            },
        ),
        "water_mask.tif": (water, 255, {"values": "1=CCI210;0=other_known_class;255=unknown"}),
        "unknown_mask.tif": (unknown, None, {"values": "1=unknown_or_missing;0=known_class"}),
    }
    outputs = {
        name: _write_raster(output / name, a, transform, nodata=no, tags=tags)
        for name, (a, no, tags) in arrays.items()
    }
    to_lonlat = Transformer.from_crs(CRS, 4326, always_xy=True)
    centers = []
    for row, col in ((49, 49), (49, 50), (50, 49), (50, 50)):
        x, y = transform * (col + 0.5, row + 0.5)
        centers.append(
            {
                "row": row,
                "column": col,
                "easting_m": x,
                "northing_m": y,
                "longitude_latitude": list(to_lonlat.transform(x, y)),
            }
        )
    values, counts = np.unique(classes, return_counts=True)
    report = {
        "profile": "korea_static_terrain_100m_research_v1",
        "status": "ready",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "operational_use": False,
        "fire_labels_accessed": False,
        "fuel_model_mapping_performed": False,
        "crs": CRS,
        "shape": list(SHAPE),
        "pixel_size_m": PIXEL_SIZE_M,
        "transform": list(transform)[:6],
        "bounds_m": list(array_bounds(*SHAPE, transform)),
        "requested_center_longitude_latitude": list(CENTER),
        "actual_domain_center_easting_northing_m": list(center),
        "actual_domain_center_longitude_latitude": list(to_lonlat.transform(*center)),
        "central_cell_centers": centers,
        "center_note": "Even-sized grid: requested point is the intersection of four cells",
        "aspect_reference": "grid_north_clockwise_downslope",
        "aspect_reference_note": "EPSG:32652 grid north; not true north",
        "flat_aspect_convention": "0 is numeric only; direction undefined where flat_mask=1",
        "forest_mask_definition": {
            "tree_classes": list(TREE_CLASSES),
            "one": "explicit CCI tree-cover or sparse-tree class",
            "zero": "other known class; does not mean nonburnable or safe",
            "unknown": 255,
            "mixed_tree_shrub_class_100_excluded": True,
        },
        "sources": {
            "dem": dem_sources,
            "landcover": landcover_source,
            "stac": [
                {"path": str(p), "sha256": file_sha256(p)}
                for p in (dem_stac_path, landcover_stac_path)
            ],
        },
        "qc": {
            "dem": dem_qc,
            "halo_pixels_each_side": 1,
            "terrain_finite_fraction": 1.0,
            "landcover_class_counts": {
                str(int(v)): int(c) for v, c in zip(values, counts, strict=True)
            },
            "landcover_unknown_pixels": int(unknown.sum()),
            "landcover_known_fraction": float((unknown == 0).mean()),
            "flat_pixels": int(flat.sum()),
        },
        "outputs": outputs,
        "limitations": [
            "Copernicus GLO-90 is a surface DSM, not a bare-earth DTM; "
            "filename COG_30 is not 30m resolution",
            "100m metric regridding does not increase source detail; "
            "DEM bilinear and CCI nearest only",
            "2015 land-cover classes may differ from present conditions "
            "and do not provide current fuel",
            "CCI quality, observation-count and current-pixel-state assets were not acquired",
            "CCI 0 or unsupported class is unknown, never nonburnable; "
            "urban and non-tree are not safe",
            "Tree classes do not determine species, Scott-Burgan fuel, "
            "canopy, fuel load or moisture",
            "DEM source nodata metadata alone does not establish "
            "terrain accuracy or bare-earth height",
            "Scenario extent is a fixed requested square, "
            "not a fire observation or validated hazard extent",
        ],
    }
    text = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    (output / "report.json").write_text(text)
    (output / "manifest.json").write_text(text)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw/korea-wildfire"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/korea-terrain-100m-v1"))
    args = parser.parse_args()
    report = build_terrain(args.raw_root, args.output)
    print(json.dumps({"status": report["status"], "output": str(args.output), "qc": report["qc"]}))


if __name__ == "__main__":
    main()
