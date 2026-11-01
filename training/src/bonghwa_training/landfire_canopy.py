"""Bounded LF2016 canopy acquisition and fixed Walker research input bundle.

No future perimeter is read; no fuel replacement, moisture fitting or interpolation
of canopy categories occurs. Native 30m values are sampled to the existing 100m grid.
"""

import argparse
import html
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from bonghwa_training.download import file_sha256

BASE = "https://edcintl.cr.usgs.gov/arcgis/rest/services/Landfire_LF2016"
SHAPE = (419, 411)
TRANSFORM = from_origin(677100, 4456400, 100, 100)
CRS = "EPSG:32610"
MAX_BYTES = 10_000_000
MAX_REQUESTS = 12
PRODUCTS = {
    "CC": ("cc_pct.tif", "percent", 1.0, "percent", 100.0),
    "CH": ("ch_m_x10.tif", "meters_times_10", 0.1, "m", 1200.0),
    "CBH": ("cbh_m_x10.tif", "meters_times_10", 0.1, "m", 1200.0),
    "CBD": ("cbd_kg_m3_x100.tif", "kg_per_m3_times_100", 0.01, "kg/m3", 100.0),
}
PARAMETERS = {
    "bbox": "677100,4414500,718200,4456400",
    "bboxSR": "32610",
    "imageSR": "32610",
    "size": "411,419",
    "format": "tiff",
    "pixelType": "S16",
    "interpolation": "RSP_NearestNeighbor",
    "renderingRule": '{"rasterFunction":"None"}',
    "f": "image",
}
FLAGS = {
    "simulation_only": True,
    "operational_use": False,
    "probability": None,
    "source_asof_verified": False,
    "event_id": "walker_2019",
    "split": "train",
}
LICENSE = {
    "name": "Public domain USGS/LANDFIRE data; source attribution retained",
    "scope": "Published LANDFIRE raster products; not a license for ELMFIRE software",
    "provider_evidence_url": "https://landfire.gov/helpdesk",
    "provider_evidence_record": "11081 (2024-02-28): LF data/maps/graphics are public domain",
    "usgs_policy_url": "https://pubs.usgs.gov/documentation/faq",
    "citation": (
        "LANDFIRE 2016 Remap, Forest Canopy Cover/Height/Base Height/Bulk Density, USGS/USFS"
    ),
}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def requests_plan():
    requests = []
    for product in PRODUCTS:
        service = f"{BASE}/LF2016_{product}_CONUS/ImageServer"
        requests.extend(
            [
                {
                    "name": f"{product}-service.json",
                    "role": "service_metadata",
                    "product": product,
                    "url": service + "?f=pjson",
                },
                {
                    "name": f"{product}-100m.tif",
                    "role": "raw_canopy_grid",
                    "product": product,
                    "url": service + "/exportImage?" + urllib.parse.urlencode(PARAMETERS),
                    "request_parameters": PARAMETERS,
                },
                {
                    "name": f"{product}-units.html",
                    "role": "official_product_unit_documentation",
                    "product": product,
                    "url": f"https://www.landfire.gov/fuel/{product.lower()}",
                },
            ]
        )
    return requests


def bounded_fetch(url, target, *, opener=urllib.request.urlopen):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Bonghwajigi-private-research/1.0", "Accept-Encoding": "identity"},
    )
    temporary = target.with_name(target.name + ".part")
    with opener(request, timeout=60) as response:
        if response.status != 200:
            raise ValueError("Expected successful complete HTTP response")
        length = response.headers.get("Content-Length")
        if length is not None and int(length) > MAX_BYTES:
            raise ValueError("Source exceeds fixed 10MB request limit")
        count = 0
        with temporary.open("wb") as stream:
            while block := response.read(64 * 1024):
                count += len(block)
                if count > MAX_BYTES:
                    raise ValueError("Source stream exceeds fixed 10MB request limit")
                stream.write(block)
        if count == 0:
            raise ValueError("Empty source response")
        record = {
            "final_url": response.geturl(),
            "http_status": response.status,
            "content_type": response.headers.get("Content-Type"),
            "bytes": count,
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
        }
    temporary.replace(target)
    return record | {"sha256": file_sha256(target)}


def acquire(raw):
    raw.mkdir(parents=True, exist_ok=False)
    plan = FLAGS | {
        "requests": requests_plan(),
        "max_requests": MAX_REQUESTS,
        "max_bytes_per_request": MAX_BYTES,
        "automatic_retries": 0,
        "license": LICENSE,
        "created_at_utc": datetime.now(UTC).isoformat(),
    }
    write_json(raw / "plan.json", plan)
    report = FLAGS | {
        "status": "running",
        "requests_attempted": 0,
        "files": [],
        "plan_sha256": file_sha256(raw / "plan.json"),
    }
    for item in plan["requests"]:
        if report["requests_attempted"] >= MAX_REQUESTS:
            raise ValueError("Fixed request budget exhausted")
        report["requests_attempted"] += 1
        write_json(raw / "report.json", report)
        record = item | {"status": "requesting"}
        try:
            record.update(bounded_fetch(item["url"], raw / item["name"]))
            record["status"] = "complete"
        except Exception as error:
            record.update(status="failed", error_type=type(error).__name__, error=str(error))
        report["files"].append(record)
        write_json(raw / "report.json", report)
        print(f"{item['name']}: {record['status']}", flush=True)
    report["status"] = (
        "complete" if all(r["status"] == "complete" for r in report["files"]) else "partial_failure"
    )
    write_json(raw / "report.json", report)
    return report


def validate_metadata(product, metadata, documentation):
    if (
        metadata.get("name") != f"Landfire_LF2016/LF2016_{product}_CONUS"
        or metadata.get("pixelType") != "S16"
        or metadata.get("bandCount") != 1
        or metadata.get("noDataValue") != -9999
    ):
        raise ValueError("Unexpected product, encoding, band count or missing-data sentinel")
    if metadata.get("pixelSizeX") != 30 or metadata.get("pixelSizeY") != 30:
        raise ValueError("Expected native 30m LF2016 source service")
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", documentation)))
    unit_pattern = {
        "CC": r"percent cover",
        "CH": r"meters\s*\*\s*10",
        "CBH": r"meters\s*\*\s*10",
        "CBD": r"kg\s*m\s*3\s*\*\s*100",
    }[product]
    if not re.search(unit_pattern, text, re.I):
        raise ValueError(f"Official product documentation does not confirm {product} units")
    return {
        "service_name": metadata["name"],
        "source_native_resolution_m": 30,
        "raw_unit": PRODUCTS[product][1],
        "physical_scale": PRODUCTS[product][2],
        "physical_unit": PRODUCTS[product][3],
        "service_copyright_text": metadata.get("copyrightText", ""),
        "documentation_units_verified": True,
    }


def read_grid(path):
    with rasterio.open(path) as source:
        if (
            source.shape != SHAPE
            or source.count != 1
            or source.crs.to_string() != CRS
            or source.transform != TRANSFORM
            or source.dtypes != ("int16",)
            or source.nodata not in (None, -9999)
        ):
            raise ValueError("Canopy raster does not match the fixed raw-code 100m UTM grid")
        values = source.read(1, masked=True)
        # ArcGIS TIFF exports may omit the tag when this tile has no missing cells.
        # The separately verified ImageServer contract defines -9999, never zero.
        return np.ma.array(values.data, mask=np.ma.getmaskarray(values) | (values.data == -9999))


def canopy_quality(grids, domain):
    unknown = np.zeros(SHAPE, dtype=bool)
    invalid = np.zeros(SHAPE, dtype=bool)
    stats = {}
    for product, values in grids.items():
        mask = np.ma.getmaskarray(values)
        unknown |= mask
        raw = values.data
        invalid |= ~mask & (~np.isfinite(raw) | (raw < 0) | (raw > PRODUCTS[product][4]))
        valid = domain & ~mask
        physical = raw[valid] * PRODUCTS[product][2]
        stats[product] = {
            "active_missing_cells": int((domain & mask).sum()),
            "active_zero_cells": int((valid & (raw == 0)).sum()),
            "active_positive_cells": int((valid & (raw > 0)).sum()),
            "physical_min": float(physical.min()) if physical.size else None,
            "physical_max": float(physical.max()) if physical.size else None,
        }
    cc, ch, cbh, cbd = (grids[p].data for p in ("CC", "CH", "CBH", "CBD"))
    joint_valid = domain & ~unknown
    base_above_top = joint_valid & (cbh > ch)
    contradictory_nonforest = joint_valid & (cc == 0) & ((ch > 0) | (cbh > 0))
    density_only = joint_valid & (cc == 0) & (ch == 0) & (cbh == 0) & (cbd > 0)
    qc = {
        "products": stats,
        "unknown_active_cells": int((unknown & domain).sum()),
        "invalid_active_cells": int((invalid & domain).sum()),
        "canopy_base_above_top_cells": int(base_above_top.sum()),
        "zero_cover_with_other_positive_canopy_cells": int(contradictory_nonforest.sum()),
        "density_without_cover_or_height_cells": int(density_only.sum()),
        "density_only_policy": (
            "Preserve source CBD and flag inconsistency; never invent canopy cover/height. "
            "Pinned ELMFIRE crown ROS requires positive CC as well as CBD."
        ),
        "zero_means_source_no_tree_canopy_not_missing": True,
    }
    if qc["unknown_active_cells"] or qc["invalid_active_cells"]:
        raise ValueError("Missing or invalid canopy inside the active domain; no filling allowed")
    if qc["canopy_base_above_top_cells"] or qc["zero_cover_with_other_positive_canopy_cells"]:
        raise ValueError("Cross-product canopy inconsistency requires explicit review; no clipping")
    return qc, unknown | invalid


def prepare(raw, terrain_manifest, output):
    if output.exists():
        raise ValueError("Canopy output must be new; existing bundles are immutable")
    report = json.loads((raw / "report.json").read_text())
    plan = json.loads((raw / "plan.json").read_text())
    if (
        report["status"] != "complete"
        or report["requests_attempted"] != MAX_REQUESTS
        or plan["requests"] != requests_plan()
        or file_sha256(raw / "plan.json") != report["plan_sha256"]
    ):
        raise ValueError("Raw acquisition differs from the frozen bounded request plan")
    records = {item["name"]: item for item in report["files"]}
    if set(records) != {item["name"] for item in requests_plan()}:
        raise ValueError("Incomplete or duplicate source inventory")
    for item in requests_plan():
        actual = records[item["name"]]
        path = raw / item["name"]
        if any(actual.get(key) != value for key, value in item.items()) or (
            actual["status"] != "complete"
            or path.stat().st_size != actual["bytes"]
            or file_sha256(path) != actual["sha256"]
            or actual["bytes"] > MAX_BYTES
        ):
            raise ValueError("Acquired source/receipt/parameter mismatch")
    terrain = json.loads(terrain_manifest.read_text())
    if (
        terrain["event_id"] != "walker_2019"
        or terrain["split"] != "train"
        or terrain["shape"] != list(SHAPE)
        or terrain["crs"] != CRS
        or terrain["transform"] != list(TRANSFORM)[:6]
    ):
        raise ValueError("Expected frozen Walker input terrain grid")
    domain_record = terrain["outputs"]["study_domain_mask.tif"]
    domain_path = terrain_manifest.parent / domain_record["path"]
    if file_sha256(domain_path) != domain_record["sha256"]:
        raise ValueError("Frozen study-domain hash mismatch")
    with rasterio.open(domain_path) as source:
        if source.shape != SHAPE or source.transform != TRANSFORM or source.crs.to_string() != CRS:
            raise ValueError("Frozen domain grid mismatch")
        domain = source.read(1) == 1
    grids, units = {}, {}
    for product in PRODUCTS:
        units[product] = validate_metadata(
            product,
            json.loads((raw / f"{product}-service.json").read_text()),
            (raw / f"{product}-units.html").read_text(),
        )
        grids[product] = read_grid(raw / f"{product}-100m.tif")
    qc, unknown = canopy_quality(grids, domain)
    initial_record = terrain["outputs"]["initial_perimeter_mask.tif"]
    initial_path = terrain_manifest.parent / initial_record["path"]
    if file_sha256(initial_path) != initial_record["sha256"]:
        raise ValueError("Frozen initial-perimeter hash mismatch")
    with rasterio.open(initial_path) as source:
        if source.shape != SHAPE or source.transform != TRANSFORM or source.crs.to_string() != CRS:
            raise ValueError("Frozen initial-perimeter grid mismatch")
        initial = source.read(1) == 1
    density_only = (
        (grids["CC"].data == 0)
        & (grids["CH"].data == 0)
        & (grids["CBH"].data == 0)
        & (grids["CBD"].data > 0)
    )
    qc["initial_density_without_cover_or_height_cells"] = int((density_only & initial).sum())
    qc["initial_cells"] = int(initial.sum())
    output.mkdir(parents=True)
    outputs = {}
    profile = {
        "driver": "GTiff",
        "height": SHAPE[0],
        "width": SHAPE[1],
        "count": 1,
        "dtype": "float32",
        "crs": CRS,
        "transform": TRANSFORM,
        "nodata": -9999,
        "compress": "DEFLATE",
    }
    for product, grid in grids.items():
        filename = PRODUCTS[product][0]
        path = output / filename
        with rasterio.open(path, "w", **profile) as target:
            target.write(grid.filled(-9999).astype("float32"), 1)
            target.update_tags(unit=PRODUCTS[product][1], source_product=f"LF2016_{product}_CONUS")
        outputs[filename] = {
            "path": filename,
            "sha256": file_sha256(path),
            "bytes": path.stat().st_size,
            "nodata": -9999,
            "dtype": "float32",
            **units[product],
        }
    unknown_path = output / "unknown_mask.tif"
    with rasterio.open(
        unknown_path, "w", **(profile | {"dtype": "uint8", "nodata": 255})
    ) as target:
        target.write(unknown.astype("uint8"), 1)
    outputs[unknown_path.name] = {
        "path": unknown_path.name,
        "sha256": file_sha256(unknown_path),
        "bytes": unknown_path.stat().st_size,
        "nodata": 255,
    }
    manifest = FLAGS | {
        "schema_version": "lf2016_canopy_walker_v1",
        "status": "ready",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "outputs": outputs,
        "qc": qc,
        "crs": CRS,
        "shape": list(SHAPE),
        "transform": list(TRANSFORM)[:6],
        "pixel_size_m": 100,
        "input_terrain_manifest_sha256": file_sha256(terrain_manifest),
        "source_acquisition_report_sha256": file_sha256(raw / "report.json"),
        "sources": {
            name: item | {"path": os.path.relpath(raw / name, output)}
            for name, item in records.items()
        },
        "license": LICENSE,
        "elmfire_flags_for_encoded_outputs": {
            "CC_IN_PERCENT": True,
            "CH_TIMES_10": True,
            "CBH_TIMES_10": True,
            "CBD_TIMES_100": True,
        },
        "method": (
            "Server-side nearest-neighbor raw-code export; no rendering, imputation or clipping"
        ),
        "source_nodata_rule": (
            "Use ImageServer -9999 sentinel even when exported TIFF omits its NoData tag"
        ),
        "limitations": [
            "LF2016 circa2016 canopy models are not measured September2019 canopy conditions",
            "LF2016 capable fuels can represent expected2019/2020 regrowth in disturbed areas",
            "Historical source availability and fire-day canopy accuracy are unverified",
            "30m source sampled to100m loses subcell canopy structure; no new spatial detail",
            "Canopy wind shielding means adding canopy need not increase surface spread",
            "Crown-fire activation depends on moisture, intensity and model assumptions",
            "No inference about Korean fire behavior or individual risk probability",
        ],
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    acquire_parser = sub.add_parser("acquire")
    acquire_parser.add_argument("--raw", required=True, type=Path)
    prepare_parser = sub.add_parser("prepare")
    for name in ("raw", "terrain-manifest", "output"):
        prepare_parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    if args.command == "acquire":
        report = acquire(args.raw)
        return 0 if report["status"] == "complete" else 1
    report = prepare(args.raw, args.terrain_manifest, args.output)
    print(json.dumps({"status": report["status"], "qc": report["qc"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
