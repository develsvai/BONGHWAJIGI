"""Fixed Walker 2019 retrospective hindcast inputs, with separately stored future truth.

Uses only already acquired, hash-linked static sources. Initial terrain/domain
construction cannot consume future geometries. GOFER/DEM/LANDFIRE availability
at the historical issue time is not established by this research bundle.
"""

import argparse
import io
import json
import math
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import rasterio
import shapefile
import shapely
from pyproj import CRS, Transformer
from rasterio.features import rasterize
from rasterio.transform import from_origin
from shapely.geometry import mapping, shape

from bonghwa_training.download import file_sha256
from bonghwa_training.gofer_approach import utc, verify_archive
from bonghwa_training.korea_terrain import project_dem, terrain_derivatives

EVENT = "walker_2019"
START = datetime(2019, 9, 4, 22, tzinfo=UTC)
TARGET_CRS = "EPSG:32610"
BOUNDS = (677100, 4414500, 718200, 4456400)
SHAPE = (419, 411)
TRANSFORM = from_origin(BOUNDS[0], BOUNDS[3], 100, 100)
DEM_NAMES = (
    "Copernicus_DSM_COG_30_N39_00_W121_00_DEM.tif",
    "Copernicus_DSM_COG_30_N40_00_W121_00_DEM.tif",
)
BURNABLE_CODES = tuple(
    list(range(101, 110))
    + list(range(121, 125))
    + list(range(141, 150))
    + list(range(161, 166))
    + list(range(181, 190))
    + list(range(201, 205))
)
NONBURNABLE_CODES = (91, 92, 93, 98, 99)


def json_write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def source_receipt(path):
    sidecar = path.with_name(path.name + ".source.json")
    data = json.loads(sidecar.read_text())
    if file_sha256(path) != data["sha256"] or path.stat().st_size != data["bytes"]:
        raise ValueError(f"Acquired source checksum/size mismatch: {path.name}")
    if not data["url"].startswith("https://"):
        raise ValueError("Public source URL required")
    return {**data, "path": str(path), "sidecar_sha256": file_sha256(sidecar)}


def perimeter_layer(archive_path, requested_time=None):
    """Read only the chosen Walker geometry; full-event bounds/areas are never read."""
    with zipfile.ZipFile(archive_path) as archive:
        base = "GOFER/GOFER_Combined/GOFERC_fireProg"
        source_crs = CRS.from_wkt(archive.read(base + ".prj").decode())
        reader = shapefile.Reader(
            shp=io.BytesIO(archive.read(base + ".shp")),
            shx=io.BytesIO(archive.read(base + ".shx")),
            dbf=io.BytesIO(archive.read(base + ".dbf")),
        )
        fields = ["fname", "fyear", "tUTC", "timestep"]
        candidates = []
        for index, record in enumerate(reader.iterRecords(fields=fields)):
            values = dict(zip(fields, record, strict=True))
            if values["fname"] == "Walker" and int(values["fyear"]) == 2019:
                time = utc(values["tUTC"])
                if requested_time is None or time == requested_time:
                    candidates.append((time, index, float(values["timestep"])))
        if not candidates:
            raise ValueError("Requested Walker perimeter is missing")
        candidates.sort()
        selected = candidates[0]
        if sum(time == selected[0] for time, _, _ in candidates) != 1:
            raise ValueError("Duplicate Walker perimeter time")
        geometry = shape(reader.shape(selected[1]).__geo_interface__)
        if (
            not geometry.is_valid
            or geometry.is_empty
            or geometry.geom_type not in ("Polygon", "MultiPolygon")
        ):
            raise ValueError("Invalid selected source perimeter")
        if not source_crs.equals(CRS.from_epsg(4326), ignore_axis_order=True):
            raise ValueError("Expected GOFER geographic EPSG4326 source")
        projector = Transformer.from_crs(source_crs, TARGET_CRS, always_xy=True)
        metric = shapely.transform(
            geometry, lambda xy: np.column_stack(projector.transform(xy[:, 0], xy[:, 1]))
        )
        return (
            geometry,
            metric,
            {
                "event_id": EVENT,
                "valid_time_utc": selected[0].isoformat(),
                "timestep": selected[2],
                "shape_index": selected[1],
                "archive_layer": base,
                "source_crs": "EPSG:4326",
            },
        )


def initial_masks(initial_geometry):
    """Fixed grid depends exclusively on t0 geometry; cell-center membership throughout."""
    west, south, east, north = initial_geometry.bounds
    actual_bounds = (
        math.floor((west - 20000) / 100) * 100,
        math.floor((south - 20000) / 100) * 100,
        math.ceil((east + 20000) / 100) * 100,
        math.ceil((north + 20000) / 100) * 100,
    )
    if actual_bounds != BOUNDS:
        raise ValueError("Initial-only 20km rectangle differs from the pre-fixed Walker grid")
    initial = rasterize(
        [(initial_geometry, 1)],
        out_shape=SHAPE,
        transform=TRANSFORM,
        fill=0,
        dtype="uint8",
        all_touched=False,
    )
    if not initial.any():
        raise ValueError(
            "Initial perimeter has no cell centers; do not replace it with one ignition"
        )
    rows, cols = np.indices(SHAPE)
    x = BOUNDS[0] + (cols + 0.5) * 100
    y = BOUNDS[3] - (rows + 0.5) * 100
    distance = shapely.distance(initial_geometry, shapely.points(x.ravel(), y.ravel()))
    domain = (distance.reshape(SHAPE) <= 20000).astype("uint8")
    if np.any((initial == 1) & (domain == 0)):
        raise ValueError("Initial cells must remain inside the study domain")
    return initial, domain


def fuel_grid(path):
    """Keep source FBFM40 codes, distinguishing missing from real non-burnable categories."""
    with rasterio.open(path) as src:
        if (
            src.count != 1
            or src.shape != SHAPE
            or src.crs != CRS.from_user_input(TARGET_CRS)
            or src.transform != TRANSFORM
            or src.dtypes[0] != "int16"
        ):
            raise ValueError("LANDFIRE export differs from fixed raw-code int16 grid")
        values = src.read(1)
        invalid = src.read_masks(1) == 0
        # Source service explicitly declares -9999, although its TIFF may omit nodata metadata.
        unknown = invalid | ~np.isin(values, BURNABLE_CODES + NONBURNABLE_CODES)
        info = {
            "tiff_nodata": src.nodata,
            "service_nodata": -9999,
            "source_dtype": src.dtypes[0],
            "raw_codes_preserved": True,
            "missing_not_replaced": True,
        }
    return values, unknown.astype("uint8"), info


def write_raster(output, name, values, nodata=None):
    path = output / name
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        count=1,
        dtype=values.dtype,
        height=SHAPE[0],
        width=SHAPE[1],
        crs=TARGET_CRS,
        transform=TRANSFORM,
        nodata=nodata,
        compress="deflate",
    ) as dst:
        dst.write(values, 1)
    return {
        "path": name,
        "sha256": file_sha256(path),
        "bytes": path.stat().st_size,
        "dtype": str(values.dtype),
        "nodata": nodata,
    }


def grid_contract():
    return {
        "event_id": EVENT,
        "initial_time_utc": START.isoformat(),
        "split": "train",
        "retrospective_proxy_only": True,
        "source_asof_verified": False,
        "operational_use": False,
        "crs": TARGET_CRS,
        "shape": list(SHAPE),
        "pixel_size_m": 100,
        "transform": list(TRANSFORM)[:6],
        "bounds_m": list(BOUNDS),
    }


def prepare_inputs(archive_root, static_root, output):
    """Write input manifest completely before the future-label stage is invoked."""
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output must be empty; existing bundles are immutable")
    archive, archive_info = verify_archive(archive_root)
    geographic, metric, layer = perimeter_layer(archive)
    if utc(layer["valid_time_utc"]) != START or layer["timestep"] != 15:
        raise ValueError("Fixed Walker initial snapshot no longer matches source")
    initial, domain = initial_masks(metric)
    dem_paths = [static_root / name for name in DEM_NAMES]
    names = [*DEM_NAMES, "dem-stac.json", "landfire-service.json", "landfire-fbfm40-100m.tif"]
    sources = {name: source_receipt(static_root / name) for name in names}
    stac = json.loads((static_root / "dem-stac.json").read_text())
    dem_items = {item["id"]: item for item in stac["features"]}
    for name in DEM_NAMES:
        item = dem_items[Path(name).stem]
        if (
            item["collection"] != "cop-dem-glo-90"
            or item["properties"]["gsd"] != 90
            or item["assets"]["data"]["href"] != sources[name]["url"]
        ):
            raise ValueError("DEM source does not match GLO90 STAC")
    service = json.loads((static_root / "landfire-service.json").read_text())
    if (
        service.get("name") != "Landfire_LF2016/LF2016_FBFM40_CONUS"
        or service.get("pixelType") != "S16"
        or service.get("bandCount") != 1
        or service.get("noDataValue") != -9999
    ):
        raise ValueError("Expected LF2016 FBFM40 categorical source service")
    export_params = sources["landfire-fbfm40-100m.tif"].get("request_parameters", {})
    required_export = {
        "bbox": "677100,4414500,718200,4456400",
        "bboxSR": "32610",
        "imageSR": "32610",
        "size": "411,419",
        "format": "tiff",
        "pixelType": "S16",
        "interpolation": "RSP_NearestNeighbor",
    }
    if (
        any(export_params.get(k) != v for k, v in required_export.items())
        or json.loads(export_params.get("renderingRule", "{}")) != {"rasterFunction": "None"}
        or "/Landfire_LF2016/LF2016_FBFM40_CONUS/ImageServer/exportImage?"
        not in sources["landfire-fbfm40-100m.tif"]["url"]
    ):
        raise ValueError("Fuel acquisition must retain fixed LF2016 raw-code nearest export")
    fuel, unknown, fuel_info = fuel_grid(static_root / "landfire-fbfm40-100m.tif")
    if np.any((unknown == 1) & (domain == 1)):
        raise ValueError("Unknown source fuel inside the fixed study domain; no fallback permitted")
    halo_transform = TRANSFORM * rasterio.Affine.translation(-1, -1)
    elevation_halo, dem_qc = project_dem(
        dem_paths, halo_transform, (SHAPE[0] + 2, SHAPE[1] + 2), dst_crs=TARGET_CRS
    )
    slope, aspect, flat = terrain_derivatives(elevation_halo, 100)
    elevation, slope, aspect, flat = [a[1:-1, 1:-1] for a in (elevation_halo, slope, aspect, flat)]
    output.mkdir(parents=True, exist_ok=True)
    initial_geojson = {"type": "Feature", "geometry": mapping(geographic), "properties": layer}
    json_write(output / "initial_perimeter.geojson", initial_geojson)
    arrays = {
        "elevation_m.tif": (elevation, None),
        "slope_deg.tif": (slope, None),
        "aspect_deg.tif": (aspect, None),
        "flat_mask.tif": (flat, None),
        "fuel_model.tif": (fuel, -9999),
        "unknown_mask.tif": (unknown, None),
        "initial_perimeter_mask.tif": (initial, None),
        "study_domain_mask.tif": (domain, None),
        "water_mask.tif": ((fuel == 98).astype("uint8"), None),
        "nonburnable_mask.tif": (np.isin(fuel, NONBURNABLE_CODES).astype("uint8"), None),
    }
    outputs = {name: write_raster(output, name, a, no) for name, (a, no) in arrays.items()}
    values, counts = np.unique(fuel, return_counts=True)
    report = {
        **grid_contract(),
        "status": "ready",
        "schema_version": "gofer_hindcast_inputs_v1",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "event_selection": "Earliest GOESIg_UTC among preassigned 2019/2020 train events; "
        "no score selection",
        "initial_layer": layer,
        "initial_geometry": {
            "path": "initial_perimeter.geojson",
            "sha256": file_sha256(output / "initial_perimeter.geojson"),
            "source_archive_sha256": archive_info["archive_sha256"],
            "area_m2_projected": metric.area,
        },
        "aspect_reference": "grid_north_clockwise_downslope",
        "flat_aspect_convention": "0 numeric convention; direction undefined where flat_mask=1",
        "rasterization": {
            "all_touched": False,
            "membership": "cell_center",
            "initial_cells_are_all_preserved": True,
        },
        "domain_definition": {
            "rectangle": "t0 perimeter bounding box expanded by 20km and snapped outward to 100m",
            "rectangle_corners": "Outside strict 20km distance: excluded by study_domain_mask",
            "active_mask": "Cell center Euclidean distance from t0 polygon <= 20000m",
            "future_geometry_used": False,
        },
        "sources": {"gofer": archive_info, "static": sources},
        "outputs": outputs,
        "qc": {
            "dem": dem_qc,
            "fuel": fuel_info,
            "fuel_code_counts": {str(int(v)): int(c) for v, c in zip(values, counts, strict=True)},
            "initial_cells": int(initial.sum()),
            "study_domain_cells": int(domain.sum()),
            "unknown_cells": int(unknown.sum()),
            "initial_nonburnable_cells": int(
                ((initial == 1) & np.isin(fuel, NONBURNABLE_CODES)).sum()
            ),
        },
        "fuel": {
            "source_product": "LANDFIRE LF2016 Remap FBFM40 CONUS",
            "nominal_source_resolution_m": 30,
            "export_resolution_m": 100,
            "interpolation": "nearest",
            "raster_function": "None",
            "fuel_codes_are_actual_source": True,
            "canopy_parameters": "not acquired",
            "burnable_codes": list(BURNABLE_CODES),
            "nonburnable_codes": list(NONBURNABLE_CODES),
            "official_information_url": "https://www.landfire.gov/data/lf2016",
        },
        "limitations": [
            "GOFER is hourly retrospective cumulative satellite reconstruction, not ground arrival",
            "GOES native resolution is about 2km at equator; "
            "100m rasterization adds no observed detail",
            "GOFER final FRAP references and other hindsight preprocessing "
            "prevent as-of validation",
            "Initial cumulative perimeter is not an observed active fire front everywhere",
            "Copernicus GLO90 is surface DSM, not bare-earth DTM; "
            "later release does not prove 2019 availability",
            "LF2016 depicts 2016 ground conditions but capable fuels may refer to 2019/2020; "
            "2019 as-of unverified",
            "Nearest 30m-to-100m fuel resampling loses subcell fuel mixtures "
            "and does not estimate moisture",
            "Canopy structure is absent; canopy zeros in a surface-fire scenario "
            "are explicit assumptions",
            "Nonburnable model categories or outside-domain cells do not imply personal safety",
            "Future geometries are stored separately and excluded from input-domain construction",
        ],
    }
    json_write(output / "manifest.json", report)
    return report


def prepare_truth(archive_root, output):
    """Separate future-data stage: evaluates only predeclared +1/+3/+6h layers."""
    manifest = json.loads((output / "manifest.json").read_text())
    if manifest.get("event_id") != EVENT or manifest.get("initial_time_utc") != START.isoformat():
        raise ValueError("Input bundle must be fixed before future labels are read")
    if (output / "truth-manifest.json").exists():
        raise ValueError("Future truth already exists")
    archive, info = verify_archive(archive_root)
    if info["archive_sha256"] != manifest["sources"]["gofer"]["archive_sha256"]:
        raise ValueError("GOFER archive changed between input and truth stages")
    records = {}
    for hour in (1, 3, 6):
        _, geometry, layer = perimeter_layer(archive, START + timedelta(hours=hour))
        values = rasterize(
            [(geometry, 1)],
            out_shape=SHAPE,
            transform=TRANSFORM,
            fill=0,
            dtype="uint8",
            all_touched=False,
        )
        record = write_raster(output, f"truth_{hour}h.tif", values)
        records[f"{hour}h"] = {**record, **layer}
    truth = {
        **grid_contract(),
        "schema_version": "gofer_hindcast_truth_v1",
        "input_manifest_sha256": file_sha256(output / "manifest.json"),
        "source_archive_sha256": info["archive_sha256"],
        "outputs": records,
        "target": "GOFER cumulative reconstructed perimeter at selected future timestamp",
        "rasterization": {"all_touched": False, "membership": "cell_center"},
        "evaluation_domain": "study_domain_mask; initial cells assessed separately",
        "outside_domain": "excluded, not a negative fire observation",
    }
    json_write(output / "truth-manifest.json", truth)
    return truth


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-root", type=Path, default=Path("data/raw/gofer/zenodo-14642378"))
    parser.add_argument(
        "--static-root", type=Path, default=Path("data/raw/gofer-hindcast/walker-2019/static")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("data/processed/gofer-hindcast-walker-v1")
    )
    parser.add_argument("--inputs-only", action="store_true")
    args = parser.parse_args()
    report = prepare_inputs(args.archive_root, args.static_root, args.output)
    if not args.inputs_only:
        prepare_truth(args.archive_root, args.output)
    print(
        json.dumps(
            {
                "status": report["status"],
                "event_id": EVENT,
                "output": str(args.output),
                "qc": report["qc"],
            }
        )
    )


if __name__ == "__main__":
    main()
