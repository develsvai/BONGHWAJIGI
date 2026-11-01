"""Train-only nested ranking on past-clear cohorts with unknown outcome coverage.

No future audit columns enter features or candidate selection. Fixed research
scores concern future satellite observations, not physical arrival/personal harm.
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
import xgboost as xgb

from bonghwa_training import censored_ranking as ranking
from bonghwa_training import expanded_generalization_experiment as expanded
from bonghwa_training import generalization_experiment as common
from bonghwa_training import korea_first_observation as dataset_builder
from bonghwa_training import korean_recent_wind_experiment as recent
from bonghwa_training.download import file_sha256

MAX_FITS = 57
PRIMARY = "cohort_primary_clear60"
SENSITIVITY = "cohort_sensitivity_clear120"
OLD_SPEED = {"closing_speed_30m_kmh", "closing_speed_60m_kmh"}


def make_candidates(base):
    control = recent.make_candidates(base)[0]
    if not OLD_SPEED.issubset(base):
        raise ValueError("original fixed-interval speed features missing")
    corrected = [f for f in base if f not in OLD_SPEED] + dataset_builder.ADDITIONAL_FEATURES
    result = []
    for name, features in (
        ("A_original34", base),
        ("B_corrected_history44", corrected),
        ("C_corrected_history_wind50", corrected + recent.WIND_FEATURES + recent.DRY_FEATURES),
    ):
        candidate = copy.deepcopy(control)
        candidate.update(name=name, features=features)
        candidate["monotone_constraints"] = [int(f == "horizon_hours") for f in features]
        result.append(candidate)
    return result


def subset(data, mask):
    """One mask across all row arrays; metadata is never sliced or learned."""
    return {
        key: value[mask] if isinstance(value, np.ndarray) else value for key, value in data.items()
    }


def known_training(events):
    return {e: subset(d, d["y"] >= 0) for e, d in events.items()}


def evaluate(data, scores, sensitivity=False):
    result = {}
    for h in expanded.HORIZONS:
        mask = data["h"] == h
        if sensitivity:
            mask &= data["sensitivity"]
        result[str(h)] = ranking.summarize(
            data["y"][mask],
            scores[mask],
            data["issues"][mask],
            data["rows"][mask],
            data["cols"][mask],
        )
    return result


def load_train(directory):
    cfg = json.loads((directory / "config.json").read_text())
    report = json.loads((directory / "report.json").read_text())
    plan = json.loads((directory / "plan.json").read_text())
    if (
        cfg.get("profile") != dataset_builder.PROFILE
        or cfg.get("target_column") != "observed_fire_within_horizon"
        or cfg.get("unknown_target_value") != -1
        or report.get("status") != "completed"
        or file_sha256(directory / "config.json") != report["config_sha256"]
        or file_sha256(directory / "plan.json") != report["plan_sha256"]
    ):
        raise ValueError("completed frozen cohort dataset required")
    contracts = cfg["events"]
    if len(contracts) != 14 or {e["id"] for e in contracts} != recent.TRAIN_IDS:
        raise ValueError("exact domestic train-only allowlist required")
    base = plan["base_features"]
    make_candidates(base)
    inputs = base + dataset_builder.ADDITIONAL_FEATURES
    if cfg["feature_names"] != inputs or cfg["input_feature_allowlist"] != inputs:
        raise ValueError("input feature allowlist changed")
    all_features = inputs + recent.WIND_FEATURES + recent.DRY_FEATURES
    events, inventory, source_hashes = {}, {}, {}
    for name in ("config.json", "plan.json", "report.json"):
        source_hashes[name] = file_sha256(directory / name)
    for event in contracts:
        common.guard_event(event, "train")
        start = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00"))
        if start.year not in (2020, 2021, 2022):
            raise ValueError("non-train year")
        name = event["id"]
        path, report_path = directory / f"{name}.parquet", directory / f"{name}-report.json"
        event_report = json.loads(report_path.read_text())
        if event_report["event"] != event or file_sha256(path) != event_report["sha256"]:
            raise ValueError("event source contract mismatch")
        source_hashes[path.name] = file_sha256(path)
        source_hashes[report_path.name] = file_sha256(report_path)
        # Deliberately no audit_* / transition / first-future-time column is opened.
        table = pq.read_table(
            path,
            columns=[
                *inputs,
                "observed_fire_within_horizon",
                "target_known",
                PRIMARY,
                SENSITIVITY,
                "latitude",
                "longitude",
                "row",
                "col",
                "issue_epoch_seconds",
                "max_input_available_epoch_seconds",
            ],
        )
        x = np.column_stack([table[f].to_numpy() for f in inputs])
        y = table["observed_fire_within_horizon"].to_numpy()
        h = table["horizon_hours"].to_numpy()
        issues, rows, cols, available = [
            table[f].to_numpy()
            for f in (
                "issue_epoch_seconds",
                "row",
                "col",
                "max_input_available_epoch_seconds",
            )
        ]
        primary, sensitivity, known = [
            table[f].to_numpy() for f in (PRIMARY, SENSITIVITY, "target_known")
        ]
        if len(y) != event_report["rows"] or not np.isin(y, [-1, 0, 1]).all():
            raise ValueError("invalid labels/row count")
        if not np.array_equal(known, y >= 0) or np.any(sensitivity & ~primary):
            raise ValueError("cohort/known-label contract mismatch")
        if np.isinf(x).any() or not np.isin(h, expanded.HORIZONS).all():
            raise ValueError("feature/horizon mismatch")
        if (
            not all(np.isfinite(v).all() for v in (issues, rows, cols, available))
            or np.any(available > issues)
            or np.any(issues < start.timestamp())
            or np.any(issues >= start.timestamp() + (event["hours"] + 1) * 3600)
            or np.any(issues + h * 3600 >= common.HOLDOUT_START)
        ):
            raise ValueError("invalid time/coordinate or future input")
        identity = np.column_stack((issues, h, rows, cols))
        if len(np.unique(identity, axis=0)) != len(y):
            raise ValueError("duplicate candidate identity")
        extra = recent.derive_features(
            x, inputs, table["longitude"].to_numpy(), table["latitude"].to_numpy()
        )
        data = dict(
            x=np.column_stack((x, extra)),
            y=y,
            h=h,
            issues=issues,
            rows=rows,
            cols=cols,
            sensitivity=sensitivity,
            event=event,
        )
        events[name] = subset(data, primary)
        inventory[name] = {
            "all_candidates": len(y),
            "primary_candidates": int(primary.sum()),
            "primary_known": int((primary & known).sum()),
            "primary_positive": int((primary & (y == 1)).sum()),
            "primary_unknown": int((primary & ~known).sum()),
            "sensitivity_candidates": int(sensitivity.sum()),
            "period_group": expanded.period_group(event),
        }
        if file_sha256(path) != source_hashes[path.name]:
            raise ValueError("source changed during read")
    if len({expanded.period_group(d["event"]) for d in events.values()}) != 11:
        raise ValueError("fixed 11 period groups changed")
    return events, base, all_features, inventory, source_hashes


def make_plan(events, base, features, inventory, source_hashes):
    ids = sorted(events)
    outer = recent.grouped_folds(events, ids, 4)
    modules = [
        Path(__file__),
        *[Path(m.__file__) for m in (ranking, expanded, common, recent, dataset_builder)],
    ]
    modules += [
        Path(__file__).with_name(n) for n in ("ranking_audit.py", "download.py", "risk_metrics.py")
    ]
    return {
        "experiment": "korea_first_observation_train_nested_v1",
        "source_hashes": source_hashes,
        "code_sha256": {p.name: file_sha256(p) for p in modules},
        "versions": {"xgboost": xgb.__version__, "numpy": np.__version__},
        "features": features,
        "candidates": make_candidates(base),
        "inventory": inventory,
        "outer_folds": [
            {**f, "inner_folds": recent.grouped_folds(events, f["training_ids"], 3)} for f in outer
        ],
        "final_folds": recent.grouped_folds(events, ids, 4),
        "maximum_fit_count": MAX_FITS,
        "cpu_threads": 2,
        "rounds_per_fit": 100,
        "fit_rule": (
            "primary past-clear60 cohort, known outcomes only; "
            "positive weight from each training fold"
        ),
        "selection": (
            "macro known-only AP on identical both-class event/horizon cells; "
            "first candidate wins ties"
        ),
        "budget_rule": (
            "rank ALL primary candidates including unknowns before top10% per issue selection"
        ),
        "sensitivity": (
            "same held-out models, past-clear120 subset; no refitting/selection; "
            "top10% budget reranked inside that subset, not primary selected intersection"
        ),
        "count_semantics": (
            "rows/budgets/issues sum event x horizon x issue candidates; "
            "not unique people, fires, spatial cells or notifications"
        ),
        "control": (
            "fixed A original34 refit within every outer training fold; "
            "no all-train model used as held-out"
        ),
        "target": "future sampled GK2A fire observation, not physical first arrival/personal harm",
        "prior_exposure": (
            "train events explored previously; nested study is not a new independent holdout"
        ),
        "comparison_limit": (
            "cohort and full candidate budget differ from old known-only v4; "
            "cross-study AP/recall not direct improvement"
        ),
        "score_semantics": "uncalibrated class-weighted logistic ranking scores",
        "validation_read": False,
        "calibration_read": False,
        "test_evaluated": False,
        "probability_calibrated": False,
        "operational_use": False,
    }


def select_cv(events, ids, features, candidates, folds, directory, fit_once):
    records = {}
    for candidate in candidates:
        diagnostics, audit = {}, []
        for fold in folds:
            model, _, resolved = fit_once(fold["training_ids"], candidate)
            for e in fold["held_ids"]:
                if e in diagnostics:
                    raise ValueError("duplicate held prediction")
                diagnostics[e] = evaluate(
                    events[e], recent.predict(model, events[e], features, candidate)
                )
            audit.append({**fold, "positive_weight": resolved["parameters"]["scale_pos_weight"]})
        if set(diagnostics) != set(ids):
            raise ValueError("incomplete held prediction")
        records[candidate["name"]] = {
            "summary": ranking.aggregate(diagnostics),
            "folds": audit,
            "held_out": diagnostics,
        }
        common.write_json(directory / f"{candidate['name']}.json", records[candidate["name"]])
    values = {
        c["name"]: records[c["name"]]["summary"]["macro_known_event_horizon_ap"] for c in candidates
    }
    if any(v is None for v in values.values()):
        raise ValueError("no eligible positive comparison cells")
    return max(candidates, key=lambda c: values[c["name"]]), values


def run(args):
    started = perf_counter()
    events, base, features, inventory, hashes = load_train(args.dataset)
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
    training = known_training(events)
    fits = 0

    def fit_once(ids, candidate):
        nonlocal fits
        if fits >= MAX_FITS:
            raise ValueError("fit budget exceeded")
        fits += 1
        usable = [e for e in ids if len(training[e]["y"])]
        return expanded.fit(training, usable, features, candidate)

    methods = ("nested_selected", "fixed_original34", "recent_distance", "current_distance")
    diagnostics = {cohort: {m: {} for m in methods} for cohort in ("primary", "sensitivity")}
    outer, predictions = [], []
    try:
        for i, fold in enumerate(plan["outer_folds"]):
            directory = args.output / f"outer-{i}"
            directory.mkdir()
            chosen, cv = select_cv(
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
            for e in fold["held_ids"]:
                d = events[e]
                scores = {
                    "nested_selected": recent.predict(model, d, features, chosen),
                    "fixed_original34": recent.predict(control, d, features, plan["candidates"][0]),
                    "recent_distance": -d["x"][:, features.index("distance_recent_fire_60m_km")],
                    "current_distance": -d["x"][:, features.index("distance_fire_km")],
                }
                for cohort in diagnostics:
                    for method in methods:
                        diagnostics[cohort][method][e] = evaluate(
                            d, scores[method], cohort == "sensitivity"
                        )
                predictions.append(
                    pa.table(
                        {
                            "event_id": pa.array([e] * len(d["y"]), type=pa.string()),
                            "issue_epoch_seconds": d["issues"],
                            "horizon_hours": d["h"],
                            "row": d["rows"],
                            "col": d["cols"],
                            "target": d["y"],
                            SENSITIVITY: d["sensitivity"],
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
                }
            )
            common.write_json(directory / "selected-result.json", outer[-1])
            print(
                json.dumps({"outer_completed": i + 1, "fits": fits, "selected": chosen["name"]}),
                flush=True,
            )
        if any(set(d) != set(events) for c in diagnostics.values() for d in c.values()):
            raise ValueError("outer coverage mismatch")
        directory = args.output / "final-cv"
        directory.mkdir()
        chosen, cv = select_cv(
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
            raise ValueError("unexpected number of fits")
        prediction_path = args.output / "outer-predictions.parquet"
        pq.write_table(pa.concat_tables(predictions), prediction_path, compression="zstd")
        checks = {args.dataset / n: sha for n, sha in hashes.items()}
        checks.update({Path(__file__).with_name(n): sha for n, sha in plan["code_sha256"].items()})
        checks[args.output / "plan.json"] = plan_hash
        if any(file_sha256(p) != sha for p, sha in checks.items()):
            raise ValueError("source/code changed during fitting")
        result = {
            "status": "completed",
            "elapsed_seconds": perf_counter() - started,
            "plan_sha256": plan_hash,
            "fits_executed": fits,
            "selected": chosen["name"],
            "summaries": {
                cohort: {m: ranking.aggregate(d) for m, d in value.items()}
                for cohort, value in diagnostics.items()
            },
            "per_event_horizon": diagnostics,
            "outer": outer,
            "final_cv_macro_ap": cv,
            "final_positive_weight": resolved["parameters"]["scale_pos_weight"],
            "final_training_event_shares": shares,
            "selected_model": model_audit,
            "outer_predictions_sha256": file_sha256(prediction_path),
            "final_source_audit": {"all_hashes_match": True, "files_checked": len(checks)},
            "score_semantics": plan["score_semantics"],
            "comparison_limit": plan["comparison_limit"],
            "validation_read": False,
            "calibration_read": False,
            "test_evaluated": False,
            "probability_calibrated": False,
            "operational_use": False,
        }
        common.write_json(args.output / "report.json", result)
        return {k: result[k] for k in ("status", "fits_executed", "selected", "summaries")}
    except Exception as exc:
        common.write_json(
            args.output / "failure.json",
            {"exception_type": type(exc).__name__, "fits_attempted": fits, "nontrain_read": False},
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--plan-only", action="store_true")
    modes.add_argument("--run-frozen", action="store_true")
    print(json.dumps(run(parser.parse_args())))


if __name__ == "__main__":
    main()
