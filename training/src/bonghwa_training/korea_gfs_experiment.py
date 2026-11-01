"""Fixed 2022 train-only comparison of observed weather and archived GFS context.

Identical past-clear cohorts/labels; unavailable future outcomes consume ranking
budget but are excluded from fitting. Scores are not personal-impact probabilities.
The 2020/2021 archive absence fixes the study population before model outcomes.
"""

import argparse
import copy
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pyproj
import xgboost as xgb
from pyproj import Geod, Transformer

from bonghwa_training import censored_ranking as ranking
from bonghwa_training import expanded_generalization_experiment as expanded
from bonghwa_training import generalization_experiment as common
from bonghwa_training import korea_first_observation as cohort_builder
from bonghwa_training import korea_first_observation_train as first
from bonghwa_training import korean_recent_wind_experiment as recent
from bonghwa_training.download import file_sha256

PROFILE = "korea_gfs_2022_primary_nested_v1"
CONTEXT_PROFILE = "korea_gfs_context_2022_primary_v1"
MAX_FITS = 45
EXPECTED_PRIMARY_ROWS = 238836
EXPECTED_PERIOD_GROUPS = 7
ASSUMED_RELEASE_DELAY_HOURS = 6
TRAIN_IDS = frozenset(e for e in recent.TRAIN_IDS if e.endswith("_2022"))
BASE_FEATURES = [
    "distance_fire_km",
    "nearest_fire_dx_km",
    "nearest_fire_dy_km",
    "neighbors_3",
    "neighbors_7",
    "distance_fire_30m_km",
    "distance_fire_60m_km",
    "closing_speed_30m_kmh",
    "closing_speed_60m_kmh",
    "fire_frames_last_hour",
    "clear_frames_last_hour",
    "utc_hour_sin",
    "utc_hour_cos",
    "distance_recent_fire_60m_km",
    "nearest_recent_fire_60m_dx_km",
    "nearest_recent_fire_60m_dy_km",
    "nearest_recent_fire_60m_age_minutes",
    "own_last_fire_60m_age_minutes",
    "recent_fire_60m_neighbors_3",
    "recent_fire_60m_neighbors_7",
    "forest_fraction",
    "elevation_m",
    "slope_degrees",
    "temperature_c",
    "humidity_pct",
    "wind_speed_ms",
    "wind_u_ms",
    "wind_v_ms",
    "observed_hourly_precipitation_mm",
    "weather_station_distance_km",
    "weather_age_hours",
    "wind_toward_target_ms",
    "wind_cross_target_ms",
    "horizon_hours",
]
OLD_WEATHER_FEATURES = [
    "temperature_c",
    "humidity_pct",
    "wind_speed_ms",
    "wind_u_ms",
    "wind_v_ms",
    "observed_hourly_precipitation_mm",
    "weather_station_distance_km",
    "weather_age_hours",
    "wind_toward_target_ms",
    "wind_cross_target_ms",
]
GFS_INPUT_FEATURES = [
    "gfs_temperature_c",
    "gfs_humidity_pct",
    "gfs_wind_u_ms",
    "gfs_wind_v_ms",
    "gfs_grid_distance_km",
    "gfs_reference_age_hours",
    "gfs_valid_age_hours",
]
GFS_DERIVED_FEATURES = [
    "gfs_wind_speed_ms",
    "gfs_wind_toward_target_ms",
    "gfs_wind_cross_target_ms",
]
GFS_FEATURES = GFS_INPUT_FEATURES + GFS_DERIVED_FEATURES
WEATHER_DIAGNOSTICS = [
    "gfs_grid_lon",
    "gfs_grid_lat",
    "gfs_reference_epoch_seconds",
    "gfs_valid_epoch_seconds",
    "gfs_assumed_available_epoch_seconds",
    "gfs_forecast_lead_hours",
    "gfs_source_id",
    "gfs_sample_valid",
]


def make_candidates(base):
    if base != BASE_FEATURES:
        raise ValueError("exact original34 input contract required")
    control = recent.make_candidates(base)[0]
    replacement = [f for f in base if f not in OLD_WEATHER_FEATURES] + GFS_FEATURES
    if len(replacement) != 34 or set(replacement) & set(OLD_WEATHER_FEATURES):
        raise ValueError("all ten original weather features must be replaced")
    candidates = []
    for name, features in (("A_original34", base), ("D_gfs_weather34", replacement)):
        candidate = copy.deepcopy(control)
        candidate.update(name=name, features=features)
        candidate["monotone_constraints"] = [int(f == "horizon_hours") for f in features]
        candidates.append(candidate)
    return candidates


def derive_wind(base, features, longitude, latitude, gfs):
    """Earth-relative wind projected along current fire-anchor to target geodesic.

    The existing offsets are target->fire in EPSG:5179. No future fire location,
    labels, raw absolute coordinates, or identifiers become model features.
    """
    base, gfs = np.asarray(base), np.asarray(gfs)
    lon, lat = np.asarray(longitude, float), np.asarray(latitude, float)
    if base.ndim != 2 or gfs.shape != (len(base), 7) or lon.shape != (len(base),):
        raise ValueError("wind input shape mismatch")
    if lat.shape != lon.shape or not np.isfinite(lon).all() or not np.isfinite(lat).all():
        raise ValueError("invalid target coordinates")
    if np.any((lon < 124) | (lon > 132) | (lat < 32) | (lat > 40)):
        raise ValueError("target outside Korean study region")
    dx = base[:, features.index("nearest_fire_dx_km")]
    dy = base[:, features.index("nearest_fire_dy_km")]
    distance = base[:, features.index("distance_fire_km")]
    target_x, target_y = Transformer.from_crs(4326, 5179, always_xy=True).transform(lon, lat)
    anchor_lon, anchor_lat = Transformer.from_crs(5179, 4326, always_xy=True).transform(
        target_x + dx * 1000, target_y + dy * 1000
    )
    azimuth, _, separation = Geod(ellps="WGS84").inv(anchor_lon, anchor_lat, lon, lat)
    valid = (
        np.isfinite(dx)
        & np.isfinite(dy)
        & np.isfinite(distance)
        & (distance > 0)
        & np.isfinite(separation)
        & (separation > 1e-6)
    )
    east, north = np.sin(np.deg2rad(azimuth)), np.cos(np.deg2rad(azimuth))
    u, v = gfs[:, 2], gfs[:, 3]
    values = np.column_stack(
        (
            np.hypot(u, v),
            np.where(valid, u * east + v * north, np.nan),
            np.where(valid, u * north - v * east, np.nan),
        )
    )
    if np.isinf(values).any():
        raise ValueError("infinite derived wind feature")
    return values


def keys(issues, rows, cols):
    return list(zip(issues.tolist(), rows.tolist(), cols.tolist(), strict=True))


def joined_weather(path, event, data, longitude, latitude, expected_rows):
    columns = [
        "event_id",
        "issue_epoch_seconds",
        "row",
        "col",
        "longitude",
        "latitude",
        *GFS_INPUT_FEATURES,
        *WEATHER_DIAGNOSTICS,
    ]
    table = pq.read_table(path, columns=columns)
    if len(table) != expected_rows or set(table["event_id"].to_pylist()) != {event["id"]}:
        raise ValueError("GFS event or row count mismatch")
    arrays = {f: table[f].to_numpy() for f in columns if f != "event_id"}
    issues, rows, cols = [arrays[f] for f in ("issue_epoch_seconds", "row", "col")]
    if not all(np.isfinite(x).all() for x in (issues, rows, cols)):
        raise ValueError("invalid GFS candidate identity")
    identity = keys(issues, rows, cols)
    if len(set(identity)) != len(identity):
        raise ValueError("duplicate GFS candidate identity")
    wanted = keys(data["issues"], data["rows"], data["cols"])
    if set(identity) != set(wanted):
        raise ValueError("GFS must cover exactly all primary candidates including unknowns")
    lookup = {key: i for i, key in enumerate(identity)}
    join = np.array([lookup[key] for key in wanted], dtype=int)
    for field, coordinate in (("longitude", longitude), ("latitude", latitude)):
        if not np.allclose(arrays[field][join], coordinate, rtol=0, atol=1e-7):
            raise ValueError("GFS join target coordinates changed")
    inputs = np.column_stack([arrays[f] for f in GFS_INPUT_FEATURES])
    if (
        not np.isfinite(inputs).all()
        or arrays["gfs_sample_valid"].dtype != np.dtype(bool)
        or not arrays["gfs_sample_valid"].all()
    ):
        raise ValueError("missing GFS input; do not drop candidates or zero-fill")
    if np.any((inputs[:, 1] < 0) | (inputs[:, 1] > 100)) or np.any(inputs[:, 4:] < 0):
        raise ValueError("invalid GFS humidity/distance/ages")
    reference, valid, available, lead = [
        arrays[f]
        for f in (
            "gfs_reference_epoch_seconds",
            "gfs_valid_epoch_seconds",
            "gfs_assumed_available_epoch_seconds",
            "gfs_forecast_lead_hours",
        )
    ]
    if not all(np.isfinite(a).all() for a in (reference, valid, available, lead)):
        raise ValueError("missing GFS source times")
    expected_reference = np.floor((issues - 6 * 3600) / (6 * 3600)) * (6 * 3600)
    expected_valid = np.floor(issues / 3600) * 3600
    if (
        not np.array_equal(reference, expected_reference)
        or not np.array_equal(valid, expected_valid)
        or not np.array_equal(available, reference + 6 * 3600)
        or np.any(available > issues)
        or np.any(valid > issues)
        or np.any(valid < reference)
        or not np.allclose(inputs[:, 5], (issues - reference) / 3600, rtol=0, atol=1e-6)
        or not np.allclose(inputs[:, 6], (issues - valid) / 3600, rtol=0, atol=1e-6)
        or not np.allclose(lead, (valid - reference) / 3600, rtol=0, atol=1e-6)
    ):
        raise ValueError("future or mismatched GFS forecast/availability times")
    if any(not isinstance(v, str) or not v for v in arrays["gfs_source_id"]):
        raise ValueError("GFS source identifier missing")
    for f in ("gfs_grid_lon", "gfs_grid_lat"):
        if not np.isfinite(arrays[f]).all():
            raise ValueError("GFS sampling grid coordinate missing")
    return inputs[join]


def read_metadata(dataset, weather):
    cfg = json.loads((dataset / "config.json").read_text())
    dataset_plan = json.loads((dataset / "plan.json").read_text())
    dataset_report = json.loads((dataset / "report.json").read_text())
    if (
        cfg.get("profile") != cohort_builder.PROFILE
        or cfg.get("target_column") != "observed_fire_within_horizon"
        or cfg.get("unknown_target_value") != -1
        or dataset_report.get("status") != "completed"
        or dataset_report["config_sha256"] != file_sha256(dataset / "config.json")
        or dataset_report["plan_sha256"] != file_sha256(dataset / "plan.json")
    ):
        raise ValueError("completed frozen source cohort required")
    if len(cfg["events"]) != 14 or {e["id"] for e in cfg["events"]} != recent.TRAIN_IDS:
        raise ValueError("fixed source14 train metadata required")
    base = dataset_plan["base_features"]
    make_candidates(base)
    expected = base + cohort_builder.ADDITIONAL_FEATURES
    if cfg["feature_names"] != expected or cfg["input_feature_allowlist"] != expected:
        raise ValueError("source feature allowlist changed")
    # Shared metadata is read; no 2020/2021 event file is opened or hashed.
    events = [e for e in cfg["events"] if e["id"] in TRAIN_IDS]
    if (
        len(events) != 10
        or len({expanded.period_group(e) for e in events}) != EXPECTED_PERIOD_GROUPS
    ):
        raise ValueError("fixed2022 ten windows/seven period groups required")
    for event in events:
        common.guard_event(event, "train")
        start = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00"))
        if start.year != 2022:
            raise ValueError("only2022 training event files permitted")
    context = json.loads((weather / "report.json").read_text())
    if (
        context.get("profile") != CONTEXT_PROFILE
        or context.get("status") != "completed"
        or context["plan_sha256"] != file_sha256(weather / "plan.json")
        or context["source_cohort_config_sha256"] != file_sha256(dataset / "config.json")
        or context["source_cohort_plan_sha256"] != file_sha256(dataset / "plan.json")
        or set(context["events"]) != TRAIN_IDS
        or context.get("wind_basis") != "earth_relative_east_north"
        or context.get("assumed_release_delay_hours") != ASSUMED_RELEASE_DELAY_HOURS
        or context.get("historical_publication_time_verified") is not False
    ):
        raise ValueError("completed same-cohort GFS contract required")
    return events, base, context


def load_train(dataset, weather):
    contracts, base, context = read_metadata(dataset, weather)
    source_hashes = {
        f"cohort/{name}": file_sha256(dataset / name)
        for name in ("config.json", "plan.json", "report.json")
    }
    source_hashes.update(
        {f"weather/{name}": file_sha256(weather / name) for name in ("plan.json", "report.json")}
    )
    events, inventory = {}, {}
    for event in contracts:
        name = event["id"]
        path, event_report_path = dataset / f"{name}.parquet", dataset / f"{name}-report.json"
        digest = file_sha256(path)
        event_report = json.loads(event_report_path.read_text())
        descriptor = context["events"][name]
        weather_path = weather / f"{name}.parquet"
        if (
            event_report["event"] != event
            or event_report["sha256"] != digest
            or descriptor["event"] != event
            or descriptor["source_cohort_parquet_sha256"] != digest
            or descriptor["sha256"] != file_sha256(weather_path)
        ):
            raise ValueError("same-event cohort/GFS SHA contract mismatch")
        for role, p in (("cohort", path), ("cohort", event_report_path), ("weather", weather_path)):
            source_hashes[f"{role}/{p.name}"] = file_sha256(p)
        columns = [
            *base,
            "observed_fire_within_horizon",
            "target_known",
            first.PRIMARY,
            first.SENSITIVITY,
            "latitude",
            "longitude",
            "row",
            "col",
            "issue_epoch_seconds",
            "max_input_available_epoch_seconds",
        ]
        table = pq.read_table(path, columns=columns)
        values = {f: table[f].to_numpy() for f in columns}
        x = np.column_stack([values[f] for f in base])
        y, known = values["observed_fire_within_horizon"], values["target_known"]
        primary, sensitivity = values[first.PRIMARY], values[first.SENSITIVITY]
        issue, available, rows, cols, horizon = [
            values[f]
            for f in (
                "issue_epoch_seconds",
                "max_input_available_epoch_seconds",
                "row",
                "col",
                "horizon_hours",
            )
        ]
        start = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00")).timestamp()
        if len(y) != event_report["rows"] or not np.isin(y, [-1, 0, 1]).all():
            raise ValueError("invalid source cohort labels/count")
        if not np.array_equal(known, y >= 0) or np.any(sensitivity & ~primary):
            raise ValueError("source cohort mask contract changed")
        if np.isinf(x).any() or not np.isin(horizon, expanded.HORIZONS).all():
            raise ValueError("invalid input features/horizons")
        if (
            not all(np.isfinite(v).all() for v in (issue, available, rows, cols))
            or np.any(available > issue)
            or np.any(issue < start)
            or np.any(issue >= start + (event["hours"] + 1) * 3600)
            or np.any(issue + horizon * 3600 >= common.HOLDOUT_START)
        ):
            raise ValueError("source future input or invalid event time")
        identity = np.column_stack((issue, horizon, rows, cols))
        if len(np.unique(identity, axis=0)) != len(y):
            raise ValueError("duplicate cohort candidate")
        data = first.subset(
            dict(
                x=x,
                y=y,
                h=horizon,
                issues=issue,
                rows=rows,
                cols=cols,
                sensitivity=sensitivity,
                event=event,
            ),
            primary,
        )
        lon, lat = values["longitude"][primary], values["latitude"][primary]
        gfs = joined_weather(weather_path, event, data, lon, lat, descriptor["rows"])
        derived = derive_wind(data["x"], base, lon, lat, gfs)
        data["x"] = np.column_stack((data["x"], gfs, derived))
        events[name] = data
        inventory[name] = {
            "all_source_candidates": len(y),
            "primary_candidates": len(data["y"]),
            "primary_known": int((data["y"] >= 0).sum()),
            "primary_unknown": int((data["y"] < 0).sum()),
            "primary_positive": int((data["y"] == 1).sum()),
            "sensitivity_candidates": int(data["sensitivity"].sum()),
            "unique_weather_candidates": descriptor["rows"],
            "period_group": expanded.period_group(event),
        }
    if sum(d["primary_candidates"] for d in inventory.values()) != EXPECTED_PRIMARY_ROWS:
        raise ValueError("fixed2022 primary candidate count changed")
    verify_sources(dataset, weather, source_hashes)
    return events, base, base + GFS_FEATURES, inventory, source_hashes


def verify_sources(dataset, weather, hashes):
    for key, digest in hashes.items():
        role, name = key.split("/")
        directory = {"cohort": dataset, "weather": weather}[role]
        if file_sha256(directory / name) != digest:
            raise ValueError("frozen source changed during read/fit")


def training_label_audit(events, ids):
    """Describe fixed training folds; never select cases/folds from these counts."""
    per_event = {
        e: {
            "positive_rows": int((events[e]["y"] == 1).sum()),
            "negative_rows": int((events[e]["y"] == 0).sum()),
            "excluded_unknown_rows": int((events[e]["y"] < 0).sum()),
        }
        for e in ids
    }
    return {
        "positive_rows": sum(v["positive_rows"] for v in per_event.values()),
        "negative_rows": sum(v["negative_rows"] for v in per_event.values()),
        "excluded_unknown_rows": sum(v["excluded_unknown_rows"] for v in per_event.values()),
        "positive_event_count": sum(v["positive_rows"] > 0 for v in per_event.values()),
        "per_event": per_event,
    }


def audited_folds(events, ids, count):
    return [
        {**fold, "training_label_audit": training_label_audit(events, fold["training_ids"])}
        for fold in recent.grouped_folds(events, ids, count)
    ]


def make_plan(events, base, features, inventory, hashes):
    ids = sorted(events)
    outer = [
        {**fold, "inner_folds": audited_folds(events, fold["training_ids"], 3)}
        for fold in audited_folds(events, ids, 4)
    ]
    modules = [
        Path(__file__),
        *[Path(m.__file__) for m in (ranking, expanded, common, recent, first, cohort_builder)],
        *[
            Path(__file__).with_name(n)
            for n in ("ranking_audit.py", "download.py", "risk_metrics.py")
        ],
    ]
    return {
        "experiment": PROFILE,
        "source_hashes": hashes,
        "code_sha256": {p.name: file_sha256(p) for p in modules},
        "versions": {
            "xgboost": xgb.__version__,
            "numpy": np.__version__,
            "pyproj": pyproj.__version__,
            "proj": pyproj.proj_version_str,
        },
        "features": features,
        "candidates": make_candidates(base),
        "inventory": inventory,
        "outer_folds": outer,
        "final_folds": audited_folds(events, ids, 4),
        "minimum_inner_training_positive_rows": min(
            inner["training_label_audit"]["positive_rows"]
            for fold in outer
            for inner in fold["inner_folds"]
        ),
        "maximum_fit_count": MAX_FITS,
        "cpu_threads": 2,
        "rounds_per_fit": 100,
        "population_selection": (
            "fixed2022 ten training windows/seven metadata period groups because public "
            "GFS2020/2021 objects unavailable; no outcome-based case/row filtering"
        ),
        "fit_rule": "same primary clear60 candidates; fit known labels only; fold-only sqrt weight",
        "selection": "inner macro known-only AP; both-class event/horizon cells; A wins ties",
        "weather_substitution": (
            "replace all10 observed-weather inputs with GFS7+derived3; both candidates34; "
            "no GFS precipitation, no observed weather fallback, no candidate deletion"
        ),
        "gfs_time_rule": (
            "latest6h cycle no later than issue-6h; forecast valid=floor(issue to hour); "
            "reference+6h is assumed availability, not proven historical release time"
        ),
        "historical_publication_time_verified": False,
        "gfs_sampling_limit": (
            "converter samples native GFS6371229m sphere by WGS84 numeric lon/lat; "
            "nearest-grid distance is approximate; coarse grid is not local terrain wind"
        ),
        "budget_rule": "rank all primary unknown+known candidates before per-issue ceil10%",
        "sensitivity": (
            "same outer models;120m subset reranked with its own10% budget; no refitting/selection"
        ),
        "control": (
            "fixed A34 and fixed D_gfs34 each refit in every outer training fold; "
            "preserve both held predictions independently of nested selection"
        ),
        "small_positive_fold_limit": (
            "training label counts are audited after metadata folds fixed; few positive rows "
            "or one positive event can dominate a fold; no fold is changed to improve scores"
        ),
        "count_semantics": "event x horizon x issue/location rows, not unique users or alerts",
        "prior_exposure": "previously explored training events; no new independent holdout",
        "comparison_limit": (
            "2022-only population differs from earlier57fit study; do not compare scores directly"
        ),
        "target": "sampled future satellite fire observation, not physical arrival/personal impact",
        "score_semantics": "uncalibrated class-weighted logistic ranking scores",
        "validation_read": False,
        "calibration_read": False,
        "test_evaluated": False,
        "non2022_event_files_read": False,
        "probability_calibrated": False,
        "operational_use": False,
    }


def run(args):
    started = perf_counter()
    events, base, features, inventory, hashes = load_train(args.dataset, args.weather)
    plan = make_plan(events, base, features, inventory, hashes)
    if args.plan_only:
        args.output.mkdir(parents=True, exist_ok=False)
        common.write_json(
            args.output / "plan.json", {"created_at_utc": datetime.now(UTC).isoformat(), **plan}
        )
        return {"status": "plan_frozen", "maximum_fit_count": MAX_FITS}
    saved = json.loads((args.output / "plan.json").read_text())
    saved.pop("created_at_utc")
    if saved != plan:
        raise ValueError("frozen plan/source mismatch")
    plan_hash = file_sha256(args.output / "plan.json")
    common.write_json(
        args.output / "started.json",
        {"at_utc": datetime.now(UTC).isoformat(), "plan_sha256": plan_hash},
    )
    training, fits = first.known_training(events), 0
    fit_audit = []

    def fit_once(ids, candidate):
        nonlocal fits
        if fits >= MAX_FITS:
            raise ValueError("fit budget exceeded")
        fits += 1
        usable = [e for e in ids if len(training[e]["y"])]
        result = expanded.fit(training, usable, features, candidate)
        fit_audit.append(
            {
                "fit_index": fits,
                "candidate": candidate["name"],
                "training_ids": usable,
                "empty_training_events_excluded": sorted(set(ids) - set(usable)),
                "positive_rows": result[2]["training_positive_rows"],
                "negative_rows": result[2]["training_negative_rows"],
                "positive_weight": result[2]["parameters"]["scale_pos_weight"],
            }
        )
        return result

    methods = (
        "nested_selected",
        "fixed_original34",
        "fixed_gfs34",
        "recent_distance",
        "current_distance",
    )
    diagnostics = {co: {m: {} for m in methods} for co in ("primary", "sensitivity")}
    outer, predictions = [], []
    try:
        for i, fold in enumerate(plan["outer_folds"]):
            directory = args.output / f"outer-{i}"
            directory.mkdir()
            chosen, cv = first.select_cv(
                events,
                fold["training_ids"],
                features,
                plan["candidates"],
                fold["inner_folds"],
                directory,
                fit_once,
            )
            model, shares, resolved = fit_once(fold["training_ids"], chosen)
            control, _, _ = fit_once(fold["training_ids"], plan["candidates"][0])
            gfs_control, _, _ = fit_once(fold["training_ids"], plan["candidates"][1])
            for e in fold["held_ids"]:
                data = events[e]
                scores = {
                    "nested_selected": recent.predict(model, data, features, chosen),
                    "fixed_original34": recent.predict(
                        control, data, features, plan["candidates"][0]
                    ),
                    "fixed_gfs34": recent.predict(
                        gfs_control, data, features, plan["candidates"][1]
                    ),
                    "recent_distance": -data["x"][:, features.index("distance_recent_fire_60m_km")],
                    "current_distance": -data["x"][:, features.index("distance_fire_km")],
                }
                for cohort in diagnostics:
                    for method in methods:
                        diagnostics[cohort][method][e] = first.evaluate(
                            data, scores[method], cohort == "sensitivity"
                        )
                predictions.append(
                    pa.table(
                        {
                            "event_id": pa.array([e] * len(data["y"]), type=pa.string()),
                            "issue_epoch_seconds": data["issues"],
                            "horizon_hours": data["h"],
                            "row": data["rows"],
                            "col": data["cols"],
                            "target": data["y"],
                            first.SENSITIVITY: data["sensitivity"],
                            **scores,
                        }
                    )
                )
            outer.append(
                {
                    "index": i,
                    "held_ids": fold["held_ids"],
                    "training_ids": fold["training_ids"],
                    "selected": chosen["name"],
                    "inner_macro_ap": cv,
                    "positive_weight": resolved["parameters"]["scale_pos_weight"],
                    "training_event_shares": shares,
                    "training_label_audit": fold["training_label_audit"],
                }
            )
            common.write_json(directory / "selected-result.json", outer[-1])
            print(json.dumps({"outer_completed": i + 1, "fits": fits}), flush=True)
        if any(set(d) != set(events) for c in diagnostics.values() for d in c.values()):
            raise ValueError("outer coverage mismatch")
        directory = args.output / "final-cv"
        directory.mkdir()
        chosen, cv = first.select_cv(
            events,
            sorted(events),
            features,
            plan["candidates"],
            plan["final_folds"],
            directory,
            fit_once,
        )
        model, shares, resolved = fit_once(sorted(events), chosen)
        model_audit = recent.save_selected(
            model, args.output / "model.ubj", events, features, chosen
        )
        if fits != MAX_FITS:
            raise ValueError("unexpected fit count")
        prediction_path = args.output / "outer-predictions.parquet"
        pq.write_table(pa.concat_tables(predictions), prediction_path, compression="zstd")
        verify_sources(args.dataset, args.weather, hashes)
        if file_sha256(args.output / "plan.json") != plan_hash or any(
            file_sha256(Path(__file__).with_name(n)) != sha
            for n, sha in plan["code_sha256"].items()
        ):
            raise ValueError("source code or plan changed during fitting")
        result = {
            "status": "completed",
            "elapsed_seconds": perf_counter() - started,
            "plan_sha256": plan_hash,
            "fits_executed": fits,
            "selected": chosen["name"],
            "summaries": {
                co: {m: ranking.aggregate(d) for m, d in value.items()}
                for co, value in diagnostics.items()
            },
            "per_event_horizon": diagnostics,
            "outer": outer,
            "final_cv_macro_ap": cv,
            "final_positive_weight": resolved["parameters"]["scale_pos_weight"],
            "final_training_event_shares": shares,
            "fit_label_audit": fit_audit,
            "minimum_inner_training_positive_rows": plan["minimum_inner_training_positive_rows"],
            "small_positive_fold_limit": plan["small_positive_fold_limit"],
            "selected_model": model_audit,
            "outer_predictions_sha256": file_sha256(prediction_path),
            "final_source_audit": {
                "all_hashes_match": True,
                "source_files_checked": len(hashes),
                "code_files_checked": len(plan["code_sha256"]),
                "plan_files_checked": 1,
                "files_checked": len(hashes) + len(plan["code_sha256"]) + 1,
            },
            **{
                key: plan[key]
                for key in (
                    "comparison_limit",
                    "prior_exposure",
                    "score_semantics",
                    "target",
                    "historical_publication_time_verified",
                    "validation_read",
                    "calibration_read",
                    "test_evaluated",
                    "non2022_event_files_read",
                    "probability_calibrated",
                    "operational_use",
                )
            },
        }
        common.write_json(args.output / "report.json", result)
        return {k: result[k] for k in ("status", "fits_executed", "selected", "summaries")}
    except Exception as exc:
        common.write_json(
            args.output / "failure.json",
            {"exception_type": type(exc).__name__, "fits_attempted": fits, "non2022_read": False},
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--weather", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--plan-only", action="store_true")
    modes.add_argument("--run-frozen", action="store_true")
    print(json.dumps(run(parser.parse_args())))


if __name__ == "__main__":
    main()
