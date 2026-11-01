"""Research-only approach intervals from retrospective GOFER reconstructed perimeters.

This is not a ground-observed fire arrival dataset. GOFER's source pipeline uses
final FRAP references to remove stray polygons and truncates after last growth.
Timestamp filtering below prevents additional feature leakage, but cannot undo
that source-level hindsight. Neither Korean transfer nor personal harm is tested.
"""

import argparse
import csv
import hashlib
import io
import json
import math
import re
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import shapefile
import shapely
from pyproj import CRS, Transformer
from shapely.geometry import shape

FEATURES = (
    "distance_km",
    "prior_distance_km",
    "closing_speed_kmh",
    "history_elapsed_hours",
    "elapsed_event_hours",
    "perimeter_area_km2",
    "perimeter_growth_km2_per_h",
)
PROFILE = "gofer_reconstructed_perimeter_approach_1_3_6h_v1"
TARGET = "gofer_reconstructed_perimeter_first_approach"
LIMITATIONS = [
    "Retrospective California large-fire satellite reconstruction, not ground arrival or harm.",
    "GOFER source QA uses final FRAP references to remove stray polygons.",
    "GOFER threshold/parallax parameters were tuned using 2020 final MTBS perimeters.",
    "Source removes trailing no-growth hours; end-of-series censoring may be informative.",
    "Source has coarse GOES resolution and smoothing; grid spacing adds no observation detail.",
    "A research radius is not a safety distance or a response-level threshold.",
    "Past-timestamp features do not establish historical operational availability.",
    "Targets are a synthetic spatial grid, not users, buildings, or representative population.",
    "Nearby simultaneous fires are not unified; only the named event perimeter is considered.",
    "Censoring here concerns reconstruction follow-up, not absence of real-world fire.",
    "No South Korea transfer, smoke exposure, individual injury, or evacuation validation.",
]


@dataclass(frozen=True)
class Snapshot:
    time: datetime
    geometry: object
    timestep: float


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def utc(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def event_id(name, year):
    return f"{re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')}_{int(year)}"


def validate_snapshots(snapshots):
    if not snapshots:
        raise ValueError("No perimeter observations")
    for i, item in enumerate(snapshots):
        if item.time.tzinfo is None:
            raise ValueError("Snapshot times must have timezone")
        if item.geometry.is_empty or not item.geometry.is_valid:
            raise ValueError("Empty or invalid perimeter")
        if item.geometry.geom_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError("Expected polygon perimeter")
        if i and item.time <= snapshots[i - 1].time:
            raise ValueError("Snapshot times must be strictly increasing")


def approach_intervals(snapshots, issue_time, points, radius_m, horizon_hours):
    """Return (lower, upper], current flag using supplied cumulative perimeters.

    Outside at issue then inside at the first available future snapshot yields an
    interval. Outside through last available follow-up is right censored there.
    No follow-up is represented by (0, inf), and is excluded by the builder.
    """
    validate_snapshots(snapshots)
    if radius_m <= 0 or horizon_hours <= 0:
        raise ValueError("Radius and horizon must be positive")
    history = [s for s in snapshots if s.time <= issue_time]
    if not history or history[-1].time != issue_time:
        raise ValueError("Issue time must match an observed perimeter")
    past_union = shapely.union_all([s.geometry for s in history])
    current = shapely.distance(past_union, points) <= radius_m
    lower = np.zeros(len(points), dtype=np.float64)
    upper = np.full(len(points), np.inf)
    lower[current] = 0
    upper[current] = 0
    for snapshot in snapshots:
        elapsed = (snapshot.time - issue_time).total_seconds() / 3600
        if elapsed <= 0 or elapsed > horizon_hours:
            continue
        pending = ~current & np.isinf(upper)
        hit = shapely.distance(snapshot.geometry, points) <= radius_m
        upper[pending & hit] = elapsed
        lower[pending & ~hit] = elapsed
    return lower, upper, current


def input_features(history, issue_time, points, event_start, history_hours=3):
    """Use only supplied snapshots at/before issue; denominator is actual dt."""
    validate_snapshots(history)
    if any(s.time > issue_time for s in history):
        raise ValueError("Future perimeter supplied to features")
    if history[-1].time != issue_time:
        raise ValueError("Current observation must match issue time")
    prior_limit = issue_time - timedelta(hours=history_hours)
    eligible = [s for s in history if s.time <= prior_limit]
    prior = eligible[-1] if eligible else history[0]
    current = history[-1]
    elapsed = (current.time - prior.time).total_seconds() / 3600
    if elapsed <= 0:
        raise ValueError("Positive history interval is required")
    distance = shapely.distance(current.geometry, points) / 1000
    prior_distance = shapely.distance(prior.geometry, points) / 1000
    return {
        "distance_km": distance,
        "prior_distance_km": prior_distance,
        "closing_speed_kmh": (prior_distance - distance) / elapsed,
        "history_elapsed_hours": np.full(len(points), elapsed),
        "elapsed_event_hours": np.full(
            len(points), (issue_time - event_start).total_seconds() / 3600
        ),
        "perimeter_area_km2": np.full(len(points), current.geometry.area / 1e6),
        "perimeter_growth_km2_per_h": np.full(
            len(points), (current.geometry.area - prior.geometry.area) / 1e6 / elapsed
        ),
    }


def candidate_points(current_geometry, radius_m, max_distance_m, spacing_m):
    """Grid fixed in EPSG:5070, bounded using current geometry only."""
    if not 0 < radius_m < max_distance_m or spacing_m <= 0:
        raise ValueError("Invalid candidate grid settings")
    west, south, east, north = current_geometry.bounds
    xs = (
        np.arange(
            math.floor((west - max_distance_m) / spacing_m),
            math.ceil((east + max_distance_m) / spacing_m) + 1,
        )
        * spacing_m
    )
    ys = (
        np.arange(
            math.floor((south - max_distance_m) / spacing_m),
            math.ceil((north + max_distance_m) / spacing_m) + 1,
        )
        * spacing_m
    )
    x, y = np.meshgrid(xs, ys)
    points = shapely.points(x.ravel(), y.ravel())
    distances = shapely.distance(current_geometry, points)
    keep = (distances > radius_m) & (distances <= max_distance_m)
    return points[keep], x.ravel()[keep], y.ravel()[keep]


def verify_archive(raw_root):
    raw_root = Path(raw_root)
    record = json.loads((raw_root / "record.json").read_text())
    if record["metadata"]["license"]["id"] != "cc-by-4.0":
        raise ValueError("Expected verified CC BY 4.0 GOFER release")
    if record["id"] != 14642378 or record["metadata"]["version"] != "0.2":
        raise ValueError("Unexpected GOFER release")
    entries = [f for f in record["files"] if f["key"] == "GOFER.zip"]
    if len(entries) != 1:
        raise ValueError("Expected one GOFER.zip")
    entry = entries[0]
    path = raw_root / entry["key"]
    contents = path.read_bytes()
    if len(contents) != entry["size"]:
        raise ValueError("Archive size mismatch")
    if "md5:" + hashlib.md5(contents).hexdigest() != entry["checksum"]:
        raise ValueError("Archive checksum mismatch")
    return path, {
        "record_url": "https://zenodo.org/records/14642378",
        "license": "CC-BY-4.0",
        "version": "0.2",
        "archive_bytes": len(contents),
        "archive_sha256": hashlib.sha256(contents).hexdigest(),
        "record_sha256": sha256(raw_root / "record.json"),
        "attribution": "Liu et al. (2025), GOFER v0.2, doi:10.5281/zenodo.14642378",
    }


def _member(archive, suffix):
    names = [n for n in archive.namelist() if n.endswith(suffix) and not n.startswith("__MACOSX")]
    if len(names) != 1:
        raise ValueError(f"Expected unique archive member {suffix}")
    return names[0]


def read_archive(archive_path, maximum_hours=78):
    """Read only Combined fireProg; never use fireSummary/fareaPer/rfireLine."""
    with zipfile.ZipFile(archive_path) as archive:
        metadata_name = _member(archive, "/fireData.csv")
        metadata = list(
            csv.DictReader(io.StringIO(archive.read(metadata_name).decode("utf-8-sig")))
        )
        base = _member(archive, "/GOFERC_fireProg.shp")[:-4]
        source_crs = CRS.from_wkt(archive.read(base + ".prj").decode())
        project = Transformer.from_crs(source_crs, "EPSG:5070", always_xy=True).transform
        reader = shapefile.Reader(
            shp=io.BytesIO(archive.read(base + ".shp")),
            shx=io.BytesIO(archive.read(base + ".shx")),
            dbf=io.BytesIO(archive.read(base + ".dbf")),
        )
        fields = [f[0] for f in reader.fields[1:]]
        required = {"fname", "fyear", "tUTC", "timestep"}
        if not required.issubset(fields):
            raise ValueError(f"Unexpected source fields: {fields}")
        events = {}
        for item in metadata:
            key = event_id(item["fname"], item["fyear"])
            year = int(item["fyear"])
            if year not in {2019, 2020, 2021}:
                raise ValueError("Unexpected event year")
            events[key] = {
                "id": key,
                "name": item["fname"],
                "year": year,
                "start_utc": utc(item["GOESIg_UTC"]).isoformat(),
                "split": "train" if year <= 2020 else "validation",
                "period_group": str(year),
                "snapshots": [],
            }
        repaired = 0
        for i, record in enumerate(reader.iterRecords()):
            attributes = dict(zip(fields, record, strict=True))
            if float(attributes["timestep"]) > maximum_hours:
                continue
            key = event_id(attributes["fname"], attributes["fyear"])
            geometry = shapely.transform(
                shape(reader.shape(i).__geo_interface__),
                lambda xy: np.column_stack(project(xy[:, 0], xy[:, 1])),
            )
            if not geometry.is_valid:
                geometry = shapely.make_valid(geometry)
                repaired += 1
            if geometry.is_empty or geometry.geom_type not in {"Polygon", "MultiPolygon"}:
                raise ValueError(f"Non-polygon source geometry: {key}")
            events[key]["snapshots"].append(
                Snapshot(utc(attributes["tUTC"]), geometry, float(attributes["timestep"]))
            )
        for event in events.values():
            event["snapshots"].sort(key=lambda x: x.time)
            if event["snapshots"]:
                validate_snapshots(event["snapshots"])
        return events, {
            "source_fields": fields,
            "source_crs": source_crs.to_string(),
            "projection": "EPSG:5070",
            "geometry_repairs": repaired,
            "archive_members": len(archive.namelist()),
        }


def event_rows(
    event,
    radius_km=2,
    max_distance_km=20,
    spacing_km=2,
    issue_interval_hours=6,
    max_issue_hours=72,
    horizon_hours=6,
):
    snapshots = event["snapshots"]
    event_start = utc(event["start_utc"])
    rows, excluded_current, missing_followup = [], 0, 0
    to_lonlat = Transformer.from_crs("EPSG:5070", "EPSG:4326", always_xy=True)
    for i, current in enumerate(snapshots):
        elapsed = (current.time - event_start).total_seconds() / 3600
        if (
            i == 0
            or elapsed < issue_interval_hours
            or elapsed > max_issue_hours
            or not np.isclose(elapsed % issue_interval_hours, 0)
        ):
            continue
        history = snapshots[: i + 1]
        points, east, north = candidate_points(
            current.geometry, radius_km * 1000, max_distance_km * 1000, spacing_km * 1000
        )
        if not len(points):
            continue
        features = input_features(history, current.time, points, event_start)
        lower, upper, already = approach_intervals(
            snapshots, current.time, points, radius_km * 1000, horizon_hours
        )
        excluded_current += int(already.sum())
        eligible = ~already & ((lower > 0) | np.isfinite(upper))
        missing_followup += int((~already & ~eligible).sum())
        longitude, latitude = to_lonlat.transform(east, north)
        for j in np.flatnonzero(eligible):
            rows.append(
                {
                    "event_id": event["id"],
                    "issue_time_utc": current.time.isoformat(),
                    "target_id": f"e{int(east[j])}_n{int(north[j])}",
                    "split": event["split"],
                    "label_lower_hours": float(lower[j]),
                    "label_upper_hours": float(upper[j]),
                    "current_approach": False,
                    "target_longitude": float(longitude[j]),
                    "target_latitude": float(latitude[j]),
                    "research_radius_km": radius_km,
                    **{name: float(features[name][j]) for name in FEATURES},
                }
            )
    return rows, {
        "excluded_already_approached": excluded_current,
        "excluded_no_followup": missing_followup,
    }


def _write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def build_dataset(raw_root, output, **settings):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Refusing to overwrite an existing dataset")
    output.mkdir(parents=True, exist_ok=True)
    archive, source = verify_archive(raw_root)
    max_issue_hours = settings.get("max_issue_hours", 72)
    horizon_hours = settings.get("horizon_hours", 6)
    events, source_audit = read_archive(archive, max_issue_hours + horizon_hours)
    config = {
        "profile": PROFILE,
        "target": TARGET,
        "feature_names": list(FEATURES),
        "events": [
            {k: v for k, v in event.items() if k != "snapshots"}
            for event in sorted(events.values(), key=lambda e: e["id"])
        ],
        "split_rule": "2019 and 2020 train; 2021 validation; no label-based selection",
        "retrospective_proxy_only": True,
        "operational_use": False,
        "source_asof_verified": False,
        "personal_harm_probability": False,
        "source": source,
        "source_audit": source_audit,
        "settings": {
            "radius_km": 2,
            "max_distance_km": 20,
            "spacing_km": 2,
            "issue_interval_hours": 6,
            "max_issue_hours": 72,
            "horizon_hours": 6,
            **settings,
        },
        "limitations": LIMITATIONS,
    }
    # Freeze the event split and candidate settings before constructing any labels.
    _write_json(output / "config.json", config)
    reports = []
    for event in sorted(events.values(), key=lambda e: e["id"]):
        rows, exclusions = event_rows(event, **settings)
        if not rows:
            raise ValueError(f"No usable observations in fixed event: {event['id']}")
        path = output / f"{event['id']}.parquet"
        pq.write_table(pa.Table.from_pylist(rows), path, compression="zstd")
        report = {
            "event_id": event["id"],
            "split": event["split"],
            "rows": len(rows),
            "sha256": sha256(path),
            "positive_intervals": sum(np.isfinite(r["label_upper_hours"]) for r in rows),
            "issues": len({r["issue_time_utc"] for r in rows}),
            "source_snapshots_used": len(event["snapshots"]),
            **exclusions,
        }
        report["positive_intervals"] = int(report["positive_intervals"])
        _write_json(output / f"{event['id']}-report.json", report)
        reports.append(report)
        print(json.dumps(report), flush=True)
    report = {
        "profile": PROFILE,
        "target": TARGET,
        "source": source,
        "config_sha256": sha256(output / "config.json"),
        "events": reports,
        "rows": sum(r["rows"] for r in reports),
        "operational_use": False,
        "retrospective_proxy_only": True,
        "source_asof_verified": False,
        "limitations": LIMITATIONS,
    }
    _write_json(output / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_dataset(args.raw_root, args.output)


if __name__ == "__main__":
    main()
