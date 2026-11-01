"""Append past-perimeter features without changing the frozen GOFER approach rows.

Hourly histories are retrospective satellite reconstructions, not active flame
front observations. No labels, future geometries, absolute location, event ID or
calendar year enter the feature calculation. Previously viewed 2021 validation
is an additional development report, not a fresh independent final evaluation.
"""

import argparse
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import shapely
from pyproj import Transformer

from bonghwa_training.gofer_approach import (
    FEATURES as BASE_FEATURES,
)
from bonghwa_training.gofer_approach import (
    LIMITATIONS,
    TARGET,
    read_archive,
    sha256,
    utc,
    validate_snapshots,
    verify_archive,
)

LAGS = (1, 3, 6, 12)
LAG_FEATURES = tuple(
    f"{name}_{lag}h"
    for lag in LAGS
    for name in (
        "past_distance_km",
        "closing_speed_kmh",
        "area_growth_km2_per_h",
        "actual_history_hours",
        "history_known",
    )
)
GEOMETRY_FEATURES = (
    "nearest_boundary_to_target_east_unit",
    "nearest_boundary_to_target_north_unit",
    "growth_direction_3h_east_unit",
    "growth_direction_3h_north_unit",
    "target_growth_alignment_3h",
    "rear_growth_area_fraction_3h",
    "new_growth_area_fraction_3h",
    "growth_direction_known_3h",
)
NEW_FEATURES = LAG_FEATURES + GEOMETRY_FEATURES
FEATURES = BASE_FEATURES + NEW_FEATURES
PROFILE = "gofer_past_perimeter_history_35features_v1"
REFERENCES = [
    {
        "url": "https://scikit-learn.org/stable/auto_examples/applications/plot_time_series_lagged_features.html",
        "role": (
            "Lag features must use earlier inputs; random row splits can exaggerate forecast skill"
        ),
    },
    {
        "url": "https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html",
        "role": (
            "Non-overlapping event groups for development CV; related events still need grouping"
        ),
    },
]


def feature_metadata():
    base = {
        "distance_km": ("km", "Current reconstructed perimeter distance"),
        "prior_distance_km": (
            "km",
            "Frozen baseline prior distance; original short-history fallback retained",
        ),
        "closing_speed_kmh": (
            "km/h",
            "Frozen baseline signed decrease of distance per actual hour",
        ),
        "history_elapsed_hours": ("h", "Actual time separation of the baseline prior perimeter"),
        "elapsed_event_hours": ("h", "Relative time since GOFER metadata start; not calendar time"),
        "perimeter_area_km2": ("km^2", "Current cumulative reconstructed perimeter area"),
        "perimeter_growth_km2_per_h": ("km^2/h", "Baseline signed area change per actual hour"),
    }
    metadata = {
        name: {
            "unit": unit,
            "description": text,
            "nan_meaning": "No new missing values introduced; original base column retained",
        }
        for name, (unit, text) in base.items()
    }
    definitions = {
        "past_distance_km": ("km", "Distance from target to selected prior perimeter"),
        "closing_speed_kmh": ("km/h", "(prior distance - current distance) / actual elapsed hours"),
        "area_growth_km2_per_h": ("km^2/h", "(current area - prior area) / actual elapsed hours"),
        "actual_history_hours": (
            "h",
            "Actual interval, at least requested lag; may be longer across gaps",
        ),
        "history_known": (
            "0_or_1",
            "1 if a snapshot exists at/before the requested historical cutoff",
        ),
    }
    for lag in LAGS:
        for prefix, (unit, text) in definitions.items():
            metadata[f"{prefix}_{lag}h"] = {
                "unit": unit,
                "description": f"Requested lag {lag}h: {text}",
                "nan_meaning": "Never NaN; 0 denotes absent history"
                if prefix == "history_known"
                else "No snapshot at/before issue minus requested lag",
            }
    for name in GEOMETRY_FEATURES:
        metadata[name] = {
            "unit": "dimensionless",
            "description": {
                "nearest_boundary_to_target_east_unit": (
                    "East component of nearest boundary to target unit vector in EPSG5070"
                ),
                "nearest_boundary_to_target_north_unit": (
                    "North component of nearest boundary to target unit vector in EPSG5070"
                ),
                "growth_direction_3h_east_unit": (
                    "East unit component from prior centroid to added-area centroid"
                ),
                "growth_direction_3h_north_unit": (
                    "North unit component from prior centroid to added-area centroid"
                ),
                "target_growth_alignment_3h": (
                    "Cosine between growth direction and prior-centroid-to-target vector"
                ),
                "rear_growth_area_fraction_3h": (
                    "Fraction of added area in the half-plane away from target "
                    "through prior centroid"
                ),
                "new_growth_area_fraction_3h": "Area(current minus prior) divided by current area",
                "growth_direction_known_3h": (
                    "1 if prior3h exists and nonzero added-area centroid direction exists"
                ),
            }[name],
            "nan_meaning": "Missing3h history or undefined geometry/direction; no interpolation",
        }
    metadata["growth_direction_known_3h"].update(unit="0_or_1", nan_meaning="Never NaN")
    metadata["new_growth_area_fraction_3h"]["nan_meaning"] = (
        "Missing3h history; zero growth remains0"
    )
    for name in GEOMETRY_FEATURES[:2]:
        metadata[name]["nan_meaning"] = "Target and nearest boundary point coincide"
    return metadata


def _json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def lag_snapshot(history, issue_time, lag_hours):
    eligible = [s for s in history if s.time <= issue_time - timedelta(hours=lag_hours)]
    return eligible[-1] if eligible else None


def rear_growth_fraction(growth, origin, points):
    """Exact area behind the prior centroid relative to each target direction.

    The dividing line passes through the prior centroid, perpendicular to the
    vector towards the target. A finite enclosing half-plane polygon is made
    using the *past/current growth geometry only*. No future/domain bounds enter.
    """
    coordinates = shapely.get_coordinates(points)
    vectors = coordinates - origin
    norms = np.linalg.norm(vectors, axis=1)
    valid = norms > 1e-9
    result = np.full(len(points), np.nan)
    if growth.is_empty or growth.area <= 1e-6 or not valid.any():
        return result
    west, south, east, north = growth.bounds
    corners = np.array([[west, south], [west, north], [east, south], [east, north]])
    extent = np.max(np.linalg.norm(corners - origin, axis=1)) + 1.0
    unit = vectors[valid] / norms[valid, None]
    perpendicular = np.column_stack([-unit[:, 1], unit[:, 0]])
    left, right = origin - perpendicular * extent, origin + perpendicular * extent
    polygon_coords = np.stack(
        [left, right, right - unit * 2 * extent, left - unit * 2 * extent], axis=1
    )
    areas = shapely.area(shapely.intersection(growth, shapely.polygons(polygon_coords)))
    result[valid] = np.clip(areas / growth.area, 0, 1)
    return result


def history_features(history, issue_time, points):
    """Only already available snapshots; missing history stays NaN with known=0."""
    validate_snapshots(history)
    if any(s.time > issue_time for s in history):
        raise ValueError("Future perimeter supplied to history feature calculation")
    if history[-1].time != issue_time:
        raise ValueError("Current perimeter must exactly match the issue timestamp")
    n = len(points)
    output = {name: np.full(n, np.nan, dtype="float64") for name in NEW_FEATURES}
    current = history[-1].geometry
    current_distance = shapely.distance(current, points) / 1000
    for lag in LAGS:
        output[f"history_known_{lag}h"].fill(0)
        prior = lag_snapshot(history, issue_time, lag)
        if prior is None:
            continue
        elapsed = (issue_time - prior.time).total_seconds() / 3600
        if elapsed < lag or elapsed <= 0:
            raise ValueError("History interval must respect the requested cutoff")
        distance = shapely.distance(prior.geometry, points) / 1000
        output[f"past_distance_km_{lag}h"] = distance
        output[f"closing_speed_kmh_{lag}h"] = (distance - current_distance) / elapsed
        output[f"area_growth_km2_per_h_{lag}h"].fill(
            (current.area - prior.geometry.area) / 1e6 / elapsed
        )
        output[f"actual_history_hours_{lag}h"].fill(elapsed)
        output[f"history_known_{lag}h"].fill(1)
    nearest = shapely.get_point(shapely.shortest_line(current, points), 0)
    vector = shapely.get_coordinates(points) - shapely.get_coordinates(nearest)
    norm = np.linalg.norm(vector, axis=1)
    valid = norm > 1e-9
    output["nearest_boundary_to_target_east_unit"][valid] = vector[valid, 0] / norm[valid]
    output["nearest_boundary_to_target_north_unit"][valid] = vector[valid, 1] / norm[valid]
    output["growth_direction_known_3h"].fill(0)
    prior = lag_snapshot(history, issue_time, 3)
    if prior is None:
        return output
    growth = shapely.difference(current, prior.geometry)
    output["new_growth_area_fraction_3h"].fill(growth.area / current.area)
    if growth.area <= 1e-6:
        return output  # Zero new growth has no direction, not a fabricated northward bearing.
    origin = np.array([prior.geometry.centroid.x, prior.geometry.centroid.y])
    displacement = np.array([growth.centroid.x, growth.centroid.y]) - origin
    length = np.linalg.norm(displacement)
    # Rear area remains meaningful even when symmetric growth has undefined mean direction.
    output["rear_growth_area_fraction_3h"] = rear_growth_fraction(growth, origin, points)
    if length <= 1e-9:
        return output
    direction = displacement / length
    output["growth_direction_3h_east_unit"].fill(direction[0])
    output["growth_direction_3h_north_unit"].fill(direction[1])
    output["growth_direction_known_3h"].fill(1)
    to_target = shapely.get_coordinates(points) - origin
    target_length = np.linalg.norm(to_target, axis=1)
    valid_target = target_length > 1e-9
    output["target_growth_alignment_3h"][valid_target] = (
        to_target[valid_target] @ direction / target_length[valid_target]
    )
    return output


def augment_table(table, event):
    """Append columns without reconstructing or filtering any source row or label."""
    if any(name in table.column_names for name in NEW_FEATURES):
        raise ValueError("History features already exist")
    if not table.num_rows:
        raise ValueError("Empty event table")
    if set(table["event_id"].to_pylist()) != {event["id"]}:
        raise ValueError("Event identity differs between fixed rows and geometry")
    if set(table["split"].to_pylist()) != {event["split"]}:
        raise ValueError("Source row split differs from fixed event split")
    coordinates = []
    for value in table["target_id"].to_pylist():
        match = re.fullmatch(r"e(-?\d+)_n(-?\d+)", value)
        if match is None:
            raise ValueError("Target ID is not a frozen EPSG5070 grid point")
        coordinates.append((int(match[1]), int(match[2])))
    points = shapely.points(coordinates)
    projection = Transformer.from_crs(5070, 4326, always_xy=True)
    longitude, latitude = projection.transform(*np.asarray(coordinates).T)
    if not np.allclose(
        longitude, table["target_longitude"].to_numpy(), rtol=0, atol=1e-9
    ) or not np.allclose(latitude, table["target_latitude"].to_numpy(), rtol=0, atol=1e-9):
        raise ValueError("Target ID and recorded coordinates disagree")
    issues = np.array(table["issue_time_utc"].to_pylist())
    columns = {name: np.full(table.num_rows, np.nan) for name in NEW_FEATURES}
    for issue in sorted(set(issues)):
        time = utc(issue)
        index = np.flatnonzero(issues == issue)
        history = [s for s in event["snapshots"] if s.time <= time]
        features = history_features(history, time, points[index])
        actual_distance = shapely.distance(history[-1].geometry, points[index]) / 1000
        if not np.allclose(
            actual_distance, table["distance_km"].to_numpy()[index], rtol=0, atol=1e-8
        ):
            raise ValueError("Frozen current distance disagrees with the source perimeter")
        for name in NEW_FEATURES:
            columns[name][index] = features[name]
    extended = table
    for name in NEW_FEATURES:
        if np.isinf(columns[name]).any():
            raise ValueError("History features may be missing NaN, never infinite")
        extended = extended.append_column(name, pa.array(columns[name], type=pa.float64()))
    if not extended.select(table.column_names).equals(table):
        raise ValueError("Frozen source rows or labels changed")
    return extended


def checked_event_table(base, event, outer_report):
    name = event["id"]
    if Path(name).name != name:
        raise ValueError("Invalid event path")
    expected_split = "train" if event["year"] in (2019, 2020) else "validation"
    if (
        event["year"] not in (2019, 2020, 2021)
        or event["split"] != expected_split
        or utc(event["start_utc"]).year != event["year"]
    ):
        raise ValueError("Fixed historical event-year split violated")
    record_path = base / f"{name}-report.json"
    record = json.loads(record_path.read_text())
    top = next((x for x in outer_report["events"] if x["event_id"] == name), None)
    if top is None or top["sha256"] != record["sha256"] or record["split"] != expected_split:
        raise ValueError("Per-event and dataset receipts disagree")
    path = base / f"{name}.parquet"
    if sha256(path) != record["sha256"]:
        raise ValueError("Base parquet SHA256 mismatch")
    table = pq.read_table(path)
    if table.num_rows != record["rows"] or top["rows"] != table.num_rows:
        raise ValueError("Base event row count mismatch")
    return table, record


def build_history(raw_root, base_dataset, output):
    raw_root, base, output = Path(raw_root), Path(base_dataset), Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output must be empty; existing feature datasets are immutable")
    base_config_path = base / "config.json"
    base_config = json.loads(base_config_path.read_text())
    base_report = json.loads((base / "report.json").read_text())
    config_hash, report_hash = sha256(base_config_path), sha256(base / "report.json")
    if base_report["config_sha256"] != config_hash:
        raise ValueError("Base config hash differs from its dataset report")
    if tuple(base_config["feature_names"]) != BASE_FEATURES or base_config["target"] != TARGET:
        raise ValueError("Expected the frozen seven-feature approach dataset")
    archive, source = verify_archive(raw_root)
    if source["archive_sha256"] != base_config["source"]["archive_sha256"]:
        raise ValueError("GOFER archive differs from the base dataset")
    events, _ = read_archive(archive, base_config["settings"]["max_issue_hours"])
    names = [e["id"] for e in base_config["events"]]
    if len(set(names)) != len(names) or set(names) != set(events):
        raise ValueError("Frozen event coverage differs from source archive")
    for event in base_config["events"]:
        if any(event[k] != events[event["id"]][k] for k in ("year", "split", "start_utc")):
            raise ValueError("Source event metadata or split differs from the base dataset")
    config = {
        **base_config,
        "profile": PROFILE,
        "feature_names": list(FEATURES),
        "base_feature_names": list(BASE_FEATURES),
        "additional_feature_names": list(NEW_FEATURES),
        "feature_metadata": feature_metadata(),
        "source": source,
        "base_dataset": {
            "path": str(base),
            "config_sha256": config_hash,
            "report_sha256": report_hash,
        },
        "feature_definition": {
            "lags_hours": list(LAGS),
            "prior_selection": "latest snapshot <= issue minus requested lag; no shorter fallback",
            "missing": (
                "NaN plus lag known=0; actual elapsed hours retained when older snapshot used"
            ),
            "direction_axes": "EPSG5070 projected east/north, not true north or wind direction",
            "growth_direction": "prior3h centroid towards current-minus-prior growth centroid",
            "rear_growth": "fraction of new3h area behind prior centroid away from target",
            "growth_fraction": "area(current minus prior3h) / current area",
            "zero_growth": "fraction0 but undefined directions NaN and direction_known0",
        },
        "row_selection_unchanged": True,
        "interval_labels_unchanged": True,
        "research_radius_km_unchanged": base_config["settings"]["radius_km"],
        "history_source_max_timestep_hours": base_config["settings"]["max_issue_hours"],
        "source_asof_verified": False,
        "retrospective_proxy_only": True,
        "operational_use": False,
        "personal_harm_probability": False,
        "tuning_scope": "2019/2020 event-group CV only; related incidents must share a group",
        "validation_role": "2021 previously exposed; additional development reporting only",
        "method_references": REFERENCES,
        "limitations": LIMITATIONS
        + [
            "Past reconstructed perimeter history does not remove upstream hindsight",
            "Directions and area changes describe cumulative reconstruction, "
            "not observed active flames",
            "No event ID, absolute target coordinates, calendar year or labels are model features",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    _json(output / "config.json", config)
    reports = []
    for event in base_config["events"]:
        table, receipt = checked_event_table(base, event, base_report)
        extended = augment_table(table, events[event["id"]])
        path = output / f"{event['id']}.parquet"
        pq.write_table(extended, path, compression="zstd")
        if not pq.read_table(path, columns=table.column_names).equals(table):
            raise ValueError("Saved source columns differ after enrichment")
        report = {
            **receipt,
            "sha256": sha256(path),
            "base_parquet_sha256": receipt["sha256"],
            "source_rows_preserved": True,
            "missing_feature_counts": {
                name: int(np.isnan(extended[name].to_numpy()).sum()) for name in NEW_FEATURES
            },
        }
        _json(output / f"{event['id']}-report.json", report)
        reports.append(report)
        print(json.dumps({"event_id": event["id"], "rows": extended.num_rows}), flush=True)
    if sum(r["rows"] for r in reports) != base_report["rows"]:
        raise ValueError("Enriched total rows differ from the frozen base dataset")
    if sha256(base_config_path) != config_hash or sha256(base / "report.json") != report_hash:
        raise ValueError("Base dataset receipts changed during enrichment")
    for event in base_config["events"]:
        checked_event_table(base, event, base_report)
    report = {
        "profile": PROFILE,
        "target": TARGET,
        "source": source,
        "config_sha256": sha256(output / "config.json"),
        "events": reports,
        "rows": sum(r["rows"] for r in reports),
        "feature_count": len(FEATURES),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "base_dataset_report_sha256": report_hash,
        "source_rows_preserved": True,
        "operational_use": False,
        "retrospective_proxy_only": True,
        "source_asof_verified": False,
        "personal_harm_probability": False,
        "validation_role": config["validation_role"],
        "limitations": config["limitations"],
    }
    _json(output / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw/gofer/zenodo-14642378"))
    parser.add_argument(
        "--base-dataset", type=Path, default=Path("data/processed/gofer-approach-v1")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_history(args.raw_root, args.base_dataset, args.output)
    print(json.dumps({"rows": report["rows"], "feature_count": report["feature_count"]}))


if __name__ == "__main__":
    main()
