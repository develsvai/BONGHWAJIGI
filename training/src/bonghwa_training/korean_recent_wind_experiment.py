"""Train-only nested comparison of recent-fire wind geometry and air dryness.

The fixed v4 satellite observation target is unchanged. Outputs are research ranking
scores, not calibrated personal-impact probabilities. No non-train file is opened.
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

from bonghwa_training import expanded_generalization_experiment as expanded
from bonghwa_training import generalization_experiment as common
from bonghwa_training import ranking_audit
from bonghwa_training.download import file_sha256

TRAIN_IDS = frozenset(
    "andong_2020 andong_2021 hapcheon_2022 uljin_2022 ulju_2020 goseong_2020 "
    "yeongdeok_2022 yeongwol_2022 gangneung_donghae_2022 bonghwa_2022 "
    "yanggu_2022 gunwi_2022 uljin_may_2022 miryang_2022".split()
)
WIND_FEATURES = [
    "recent_wind_toward_target_ms",
    "recent_wind_cross_target_ms",
    "recent_wind_alignment_cos",
    "current_recent_fire_anchor_separation_km",
]
DRY_FEATURES = ["vpd_kpa", "positive_recent_wind_toward_times_vpd"]
FAO_SOURCE = "https://www.fao.org/4/x0490e/x0490e07.htm"
MAX_FITS = 53


def vapour_pressure_deficit(temperature_c, humidity_pct):
    """FAO56 Eq10/11 water-relative VPD in kPa; invalid inputs remain missing.

    [-40, 50] Celsius is this experiment's conservative input guard, not a
    published accuracy guarantee for Eq11. Below-zero water/ice differences
    are not corrected. This is air dryness, not fuel moisture.
    """
    t, rh = np.broadcast_arrays(np.asarray(temperature_c, float), np.asarray(humidity_pct, float))
    out = np.full(t.shape, np.nan)
    valid = np.isfinite(t) & np.isfinite(rh) & (t >= -40) & (t <= 50) & (rh >= 0) & (rh <= 100)
    out[valid] = 0.6108 * np.exp(17.27 * t[valid] / (t[valid] + 237.3)) * (1 - rh[valid] / 100)
    return out


def derive_features(x, features, longitude, latitude):
    """No target, time-future lookup, learned imputation or current-fire substitution."""
    x = np.asarray(x)
    lon, lat = np.asarray(longitude, float), np.asarray(latitude, float)
    if x.ndim != 2 or lon.shape != (len(x),) or lat.shape != lon.shape:
        raise ValueError("feature/coordinate shape mismatch")
    if not np.isfinite(lon).all() or not np.isfinite(lat).all():
        raise ValueError("missing target coordinates")
    if np.any((lon < 124) | (lon > 132) | (lat < 32) | (lat > 40)):
        raise ValueError("coordinates outside fixed Korean research region")
    column = lambda name: x[:, features.index(name)]  # noqa: E731
    dx, dy = column("nearest_recent_fire_60m_dx_km"), column("nearest_recent_fire_60m_dy_km")
    distance = column("distance_recent_fire_60m_km")
    u, v = column("wind_u_ms"), column("wind_v_ms")
    projected = Transformer.from_crs(4326, 5179, always_xy=True).transform(lon, lat)
    anchor_lon, anchor_lat = Transformer.from_crs(5179, 4326, always_xy=True).transform(
        projected[0] + dx * 1000, projected[1] + dy * 1000
    )
    azimuth, _, separation_m = Geod(ellps="WGS84").inv(anchor_lon, anchor_lat, lon, lat)
    valid_anchor = (
        np.isfinite(dx)
        & np.isfinite(dy)
        & np.isfinite(distance)
        & (distance > 0)
        & np.isfinite(separation_m)
        & (separation_m > 1e-6)
    )
    east, north = np.sin(np.deg2rad(azimuth)), np.cos(np.deg2rad(azimuth))
    toward = np.where(valid_anchor, u * east + v * north, np.nan)
    cross = np.where(valid_anchor, u * north - v * east, np.nan)
    speed = np.hypot(u, v)
    alignment = np.divide(toward, speed, out=np.full(len(x), np.nan), where=speed > 0)
    separation = np.hypot(column("nearest_fire_dx_km") - dx, column("nearest_fire_dy_km") - dy)
    vpd = vapour_pressure_deficit(column("temperature_c"), column("humidity_pct"))
    out = np.column_stack((toward, cross, alignment, separation, vpd, np.maximum(0, toward) * vpd))
    if np.isinf(out).any():
        raise ValueError("nonfinite derived feature")
    return out


def make_candidates(base_features):
    if len(base_features) != 34 or len(set(base_features)) != 34:
        raise ValueError("fixed 34-feature control required")
    reference = next(
        c for c in expanded.make_candidates(base_features) if c["name"] == "depth4_positive_sqrt"
    )
    result = []
    for name, extra in (
        ("A_baseline34", []),
        ("B_recent_wind38", WIND_FEATURES),
        ("C_recent_wind_vpd40", WIND_FEATURES + DRY_FEATURES),
    ):
        candidate = copy.deepcopy(reference)
        candidate.update(name=name, features=base_features + extra)
        candidate["monotone_constraints"] = [
            int(f == "horizon_hours") for f in candidate["features"]
        ]
        result.append(candidate)
    return result


def grouped_folds(events, ids, count):
    """Sorted metadata period groups round-robin; labels/row counts do not select folds."""
    groups = sorted({expanded.period_group(events[e]["event"]) for e in ids})
    if len(groups) < count:
        raise ValueError("insufficient period groups")
    return [
        {
            "held_groups": groups[i::count],
            "held_ids": sorted(
                e for e in ids if expanded.period_group(events[e]["event"]) in groups[i::count]
            ),
            "training_ids": sorted(
                e for e in ids if expanded.period_group(events[e]["event"]) not in groups[i::count]
            ),
        }
        for i in range(count)
    ]


def load_train(dataset, config):
    cfg = json.loads(config.read_text())
    if (
        file_sha256(config) != file_sha256(dataset / "config.json")
        or cfg.get("profile") != expanded.CONTEXT_PROFILE
        or cfg.get("reader") != "gk2a"
        or cfg.get("horizons_hours") != [1, 3, 6]
    ):
        raise ValueError("fixed v4 context config mismatch")
    training = [e for e in cfg["events"] if e.get("split") == "train"]
    if len(training) != 14 or {e["id"] for e in training} != TRAIN_IDS:
        raise ValueError("exact train-only 14-window allowlist required")
    if len({e["id"] for e in cfg["events"]}) != len(cfg["events"]):
        raise ValueError("duplicate event ID")
    features = [f for f in cfg["feature_names"] if f not in cfg.get("drop_features", [])]
    make_candidates(features)
    events = {}
    for event in training:
        common.guard_event(event, "train")
        data = expanded.load_event(dataset, event, features, "train")
        path = dataset / f"{event['id']}.parquet"
        table = pq.read_table(
            path,
            columns=["longitude", "latitude", "row", "col", "issue_epoch_seconds", "horizon_hours"],
        )
        for name, value in (
            ("row", data["rows"]),
            ("col", data["cols"]),
            ("issue_epoch_seconds", data["issues"]),
            ("horizon_hours", data["h"]),
        ):
            if not np.array_equal(table[name].to_numpy(), value):
                raise ValueError("coordinate read row identity changed")
        extra = derive_features(
            data["x"], features, table["longitude"].to_numpy(), table["latitude"].to_numpy()
        )
        if file_sha256(path) != data["sha256"]:
            raise ValueError("parquet changed while deriving features")
        data["x"] = np.column_stack((data["x"], extra))
        events[event["id"]] = data
    if len({expanded.period_group(d["event"]) for d in events.values()}) != 11:
        raise ValueError("fixed 11 period-group contract mismatch")
    return events, features, features + WIND_FEATURES + DRY_FEATURES


def build_plan(events, base, features, config):
    ids = sorted(events)
    outer = grouped_folds(events, ids, 4)
    sources = [
        Path(__file__),
        Path(expanded.__file__),
        Path(common.__file__),
        Path(ranking_audit.__file__),
        Path(__file__).with_name("download.py"),
        Path(__file__).with_name("risk_metrics.py"),
    ]
    return {
        "experiment": "korea_v4_recent_anchor_wind_train_only_nested_v1",
        "config_sha256": file_sha256(config),
        "code_sha256": {p.name: file_sha256(p) for p in sources},
        "versions": {
            "xgboost": xgb.__version__,
            "numpy": np.__version__,
            "pyproj": pyproj.__version__,
        },
        "source_hashes": {e: d["sha256"] for e, d in events.items()},
        "event_report_hashes": {e: d["report_sha256"] for e, d in events.items()},
        "train_inventory": expanded.inventory(events),
        "features": features,
        "base_features": base,
        "candidates": make_candidates(base),
        "outer_folds": [
            {**fold, "inner_folds": grouped_folds(events, fold["training_ids"], 3)}
            for fold in outer
        ],
        "final_folds": grouped_folds(events, ids, 4),
        "maximum_fit_count": MAX_FITS,
        "rounds_per_fit": 100,
        "cpu_threads": 2,
        "selection": (
            "unweighted mean AP of identical both-class event/horizon cells; "
            "first candidate wins exact ties"
        ),
        "group_rule": (
            "UTC start date; 2022-03-04/05 combined; sorted round-robin; independence is not proven"
        ),
        "feature_definition": {
            "recent_anchor": (
                "EPSG5179 target plus stored target-to-recent-fire offsets; "
                "WGS84 geodesic fire-to-target bearing"
            ),
            "toward": "u*sin(azimuth)+v*cos(azimuth), m/s; unknown/coincident anchor remains NaN",
            "cross": "u*cos(azimuth)-v*sin(azimuth), m/s",
            "alignment": "toward/hypot(u,v); calm remains NaN",
            "anchor_separation": "Current/recent anchor Euclidean separation in EPSG5179, km",
            "vpd": "0.6108*exp(17.27*T/(T+237.3))*(1-RH/100), kPa; T Celsius, RH percent",
            "vpd_input_guard": (
                "finite T in [-40,50] C and RH in [0,100]; experiment QC guard, "
                "not cited accuracy guarantee; invalid -> NaN"
            ),
            "vpd_source": FAO_SOURCE,
            "vpd_equations": [10, 11],
            "vpd_source_reviewed_date_kst": "2026-11-01",
            "vpd_limit": (
                "water-relative empirical approximation; subzero ice correction absent; "
                "air dryness, not fuel moisture or fire spread rate"
            ),
            "interaction": "max(0,recent_wind_toward_target_ms)*vpd_kpa, m/s*kPa",
            "weather_time_basis": (
                "existing past-only ISD reprocessed observations; "
                "contemporaneous operational availability unverified"
            ),
        },
        "target": (
            "Unchanged future GK2A fire observation within 1/3/6h; not arrival or personal harm"
        ),
        "prior_exposure": (
            "exploratory domestic v4 train/validation already studied; "
            "this nested run is not a new independent holdout"
        ),
        "score_semantics": (
            "class-weighted raw logistic model scores; "
            "no probability calibration or response thresholds"
        ),
        "validation_read": False,
        "calibration_read": False,
        "test_evaluated": False,
        "probability_calibrated": False,
        "operational_use": False,
    }


def predict(model, data, features, candidate):
    if not len(data["y"]):
        return np.empty(0)
    scores = common.prediction(model, data, features, candidate["features"])
    if not np.isfinite(scores).all() or np.any((scores < 0) | (scores > 1)):
        raise ValueError("invalid raw logistic scores")
    return scores


def verify_frozen_sources(args, plan, plan_sha256):
    """Detect concurrent changes without opening any non-train source."""
    if set(plan["source_hashes"]) != TRAIN_IDS:
        raise ValueError("source audit requires the fixed train allowlist")
    checks = {
        args.config: plan["config_sha256"],
        args.dataset / "config.json": plan["config_sha256"],
        args.output / "plan.json": plan_sha256,
    }
    for event_id in sorted(TRAIN_IDS):
        checks[args.dataset / f"{event_id}.parquet"] = plan["source_hashes"][event_id]
        checks[args.dataset / f"{event_id}-report.json"] = plan["event_report_hashes"][event_id]
    checks.update(
        {Path(__file__).with_name(name): sha for name, sha in plan["code_sha256"].items()}
    )
    if any(file_sha256(path) != expected for path, expected in checks.items()):
        raise ValueError("frozen source changed during experiment")
    return {"all_hashes_match": True, "files_checked": len(checks), "nontrain_source_read": False}


def select_candidate(candidates, cv):
    if any(cv[c["name"]]["mean_event_horizon_ap"] is None for c in candidates):
        raise ValueError("candidate has no eligible comparison cells")
    return max(candidates, key=lambda c: cv[c["name"]]["mean_event_horizon_ap"])


def cv_select(events, ids, features, candidates, folds, output, fit_once):
    cv = {}
    cells = expanded.eligible_cells({e: events[e] for e in ids})
    for candidate in candidates:
        diagnostics, audit = {}, []
        for fold in folds:
            model, shares, resolved = fit_once(fold["training_ids"], candidate)
            for e in fold["held_ids"]:
                if e in diagnostics:
                    raise ValueError("duplicate held-out prediction")
                diagnostics[e] = expanded.evaluate(
                    events[e], predict(model, events[e], features, candidate), probability=False
                )
            audit.append(
                {
                    **fold,
                    "positive_weight": resolved["parameters"]["scale_pos_weight"],
                    "training_event_shares": shares,
                }
            )
        if set(diagnostics) != set(ids):
            raise ValueError("incomplete held-out coverage")
        cv[candidate["name"]] = {
            "mean_event_horizon_ap": expanded.mean_ap(diagnostics, cells),
            "folds": audit,
            "held_out": diagnostics,
        }
        common.write_json(output / f"{candidate['name']}.json", cv[candidate["name"]])
    return select_candidate(candidates, cv), cv


def score_summary(diagnostics, events):
    cells = expanded.eligible_cells(events)
    count_keys = (
        "eligible_candidates",
        "examined_candidates",
        "true_positives",
        "total_positives",
        "missing_score_candidates",
    )
    counts = {
        key: sum(
            cell["top_10_percent_per_issue"][key]
            for d in diagnostics.values()
            for cell in d.values()
        )
        for key in count_keys
    }
    counts["recall"] = (
        counts["true_positives"] / counts["total_positives"] if counts["total_positives"] else None
    )
    counts["precision"] = (
        counts["true_positives"] / counts["examined_candidates"]
        if counts["examined_candidates"]
        else None
    )
    return {
        "mean_event_horizon_ap": expanded.mean_ap(diagnostics, cells),
        "eligible_ap_cells": len(cells),
        "top_10_percent_counts": counts,
    }


def save_selected(model, path, events, features, candidate):
    model.save_model(path)
    restored = xgb.Booster()
    restored.load_model(path)
    restored.set_param({"device": "cpu", "nthread": 2})
    if restored.feature_names != candidate["features"] or restored.num_boosted_rounds() != 100:
        raise ValueError("saved model contract mismatch")
    maximum, rows, violations = 0.0, 0, 0
    max_drop = 0.0
    for data in events.values():
        if not len(data["y"]):
            continue
        before, after = (
            predict(model, data, features, candidate),
            predict(restored, data, features, candidate),
        )
        delta = float(np.max(np.abs(before - after)))
        maximum = max(maximum, delta)
        if delta > 1e-6:
            raise ValueError("CPU reload predictions changed")
        probe = data["x"][:, [features.index(f) for f in candidate["features"]]].copy()
        scores = []
        for h in expanded.HORIZONS:
            probe[:, candidate["features"].index("horizon_hours")] = h
            scores.append(restored.inplace_predict(np.ascontiguousarray(probe)))
        difference = np.diff(np.asarray(scores), axis=0)
        violations += int((difference < -1e-6).sum())
        max_drop = max(max_drop, max(0.0, float(-difference.min())))
        rows += len(probe)
    return {
        "model_sha256": file_sha256(path),
        "saved_trees": 100,
        "cpu_reload_max_abs_difference": maximum,
        "horizon_monotonicity_probe_rows": rows,
        "horizon_monotonicity_violation_pairs": violations,
        "horizon_maximum_score_drop": max_drop,
        "horizon_monotonicity_verified": violations == 0,
    }


def experiment(args):
    started = perf_counter()
    events, base, features = load_train(args.dataset, args.config)
    plan = build_plan(events, base, features, args.config)
    if args.plan_only:
        args.output.mkdir(parents=True, exist_ok=False)
        common.write_json(
            args.output / "plan.json", {"created_at_utc": datetime.now(UTC).isoformat(), **plan}
        )
        return {"status": "plan_frozen", "maximum_fit_count": MAX_FITS, "training_started": False}
    saved = json.loads((args.output / "plan.json").read_text())
    saved.pop("created_at_utc")
    if saved != plan:
        raise ValueError("frozen plan/source/data mismatch; do not overwrite")
    plan_sha256 = file_sha256(args.output / "plan.json")
    common.write_json(
        args.output / "started.json",
        {
            "at_utc": datetime.now(UTC).isoformat(),
            "plan_sha256": plan_sha256,
        },
    )
    fits = 0

    def fit_once(ids, candidate):
        nonlocal fits
        if fits >= MAX_FITS:
            raise ValueError("fit budget exceeded")
        fits += 1
        nonempty = [e for e in ids if len(events[e]["y"])]
        return expanded.fit(events, nonempty, features, candidate)

    candidates, ids = plan["candidates"], sorted(events)
    outer, predictions, diagnostics = [], [], {}
    try:
        for index, fold in enumerate(plan["outer_folds"]):
            directory = args.output / f"outer-{index}"
            directory.mkdir()
            chosen, cv = cv_select(
                events,
                fold["training_ids"],
                features,
                candidates,
                fold["inner_folds"],
                directory,
                fit_once,
            )
            model, shares, resolved = fit_once(fold["training_ids"], chosen)
            held = {}
            for event_id in fold["held_ids"]:
                data = events[event_id]
                scores = predict(model, data, features, chosen)
                held[event_id] = expanded.evaluate(data, scores, probability=False)
                predictions.append(
                    pa.table(
                        {
                            "event_id": pa.array([event_id] * len(scores), type=pa.string()),
                            "issue_epoch_seconds": data["issues"],
                            "horizon_hours": data["h"],
                            "row": data["rows"],
                            "col": data["cols"],
                            "target": data["y"],
                            "raw_model_score": np.asarray(scores, dtype=np.float64),
                            "negative_recent_distance_score": -data["x"][
                                :, features.index("distance_recent_fire_60m_km")
                            ],
                        }
                    )
                )
            diagnostics.update(held)
            result = {
                "outer_index": index,
                "held_groups": fold["held_groups"],
                "training_ids": fold["training_ids"],
                "held_ids": fold["held_ids"],
                "selected": chosen["name"],
                "inner_candidate_macro_ap": {
                    name: value["mean_event_horizon_ap"] for name, value in cv.items()
                },
                "positive_weight": resolved["parameters"]["scale_pos_weight"],
                "training_event_shares": shares,
                "held_out": held,
            }
            outer.append(result)
            common.write_json(directory / "selected-result.json", result)
        if set(diagnostics) != set(ids):
            raise ValueError("outer coverage incomplete")
        recent = {
            e: expanded.evaluate(
                d, -d["x"][:, features.index("distance_recent_fire_60m_km")], probability=False
            )
            for e, d in events.items()
        }
        directory = args.output / "final-cv"
        directory.mkdir()
        chosen, cv = cv_select(
            events, ids, features, candidates, plan["final_folds"], directory, fit_once
        )
        common.write_json(
            args.output / "selection.json",
            {"selected": chosen, "training_only_cv": cv, "nontrain_read": False},
        )
        model, shares, resolved = fit_once(ids, chosen)
        model_audit = save_selected(model, args.output / "model.ubj", events, features, chosen)
        if fits != MAX_FITS:
            raise ValueError("unexpected total fit count")
        prediction_path = args.output / "outer-predictions.parquet"
        pq.write_table(pa.concat_tables(predictions), prediction_path)
        final_source_audit = verify_frozen_sources(args, plan, plan_sha256)
        report = {
            "status": "completed",
            "plan_sha256": file_sha256(args.output / "plan.json"),
            "fits_executed": fits,
            "elapsed_seconds": perf_counter() - started,
            "selected": chosen["name"],
            "outer": outer,
            "nested_oof": score_summary(diagnostics, events),
            "recent_distance_baseline": score_summary(recent, events),
            "recent_distance_per_event_horizon": recent,
            "final_cv_macro_ap": {
                name: value["mean_event_horizon_ap"] for name, value in cv.items()
            },
            "selected_model": model_audit,
            "final_training_event_shares": shares,
            "final_positive_weight": resolved["parameters"]["scale_pos_weight"],
            "outer_predictions_sha256": file_sha256(prediction_path),
            "final_source_audit": final_source_audit,
            "train_inventory": plan["train_inventory"],
            "score_semantics": plan["score_semantics"],
            "prior_exposure": plan["prior_exposure"],
            "validation_read": False,
            "calibration_read": False,
            "test_evaluated": False,
            "probability_calibrated": False,
            "operational_use": False,
        }
        common.write_json(args.output / "report.json", report)
        return report
    except Exception as exc:
        common.write_json(
            args.output / "failure.json",
            {
                "exception_type": type(exc).__name__,
                "fits_attempted": fits,
                "completed_outer_folds": len(outer),
                "validation_read": False,
                "calibration_read": False,
                "test_evaluated": False,
            },
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan-only", action="store_true")
    mode.add_argument("--run-frozen", action="store_true")
    args = parser.parse_args()
    result = experiment(args)
    print(
        json.dumps(
            {
                key: result[key]
                for key in ("status", "maximum_fit_count", "fits_executed", "selected")
                if key in result
            }
        )
    )


if __name__ == "__main__":
    main()
