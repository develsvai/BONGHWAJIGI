"""국내 v3 고정 자료의 4사건 LOEO CPU 연구. validation은 후보 선택 후에만 연다."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import pyarrow.parquet as pq
import xgboost as xgb

from bonghwa_training.download import file_sha256
from bonghwa_training.ranking_audit import standard_metrics
from bonghwa_training.risk_metrics import operating_points

PROFILE = "kor_gk2a_10min_approach_hindcast_1_3_6h_v3_context_v1"
HORIZONS = (1, 3, 6)
ROUNDS = 100
HOLDOUT_START = datetime(2025, 1, 1, tzinfo=UTC).timestamp()
REMOVED_FEATURES = frozenset(
    ("utc_hour_sin", "utc_hour_cos", "weather_station_distance_km", "weather_age_hours")
)


def write_json(path, value):
    with path.open("x") as destination:
        destination.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def make_candidates(features):
    if len(set(features)) != len(features) or "horizon_hours" not in features:
        raise ValueError("중복 feature 또는 horizon_hours 누락")
    if not REMOVED_FEATURES.issubset(features):
        raise ValueError("고정 ablation에 필요한 시각/관측소 feature 누락")
    common = {
        "objective": "binary:logistic",
        "tree_method": "hist",
        "device": "cpu",
        "nthread": 2,
        "seed": 47,
        "scale_pos_weight": 1,
        "subsample": 0.8,
        "colsample_bytree": 0.9,
        "max_bin": 256,
        "eval_metric": "logloss",
    }
    regularized = {
        "max_depth": 2,
        "min_child_weight": 25,
        "lambda": 100,
        "gamma": 1,
        "eta": 0.03,
        "max_delta_step": 1,
    }
    definitions = [
        (
            "reference_depth4",
            {
                "max_depth": 4,
                "min_child_weight": 5,
                "lambda": 20,
                "gamma": 0,
                "eta": 0.05,
                "max_delta_step": 0,
            },
            False,
            features,
        ),
        ("shallow_depth2", regularized, False, features),
        ("shallow_equal_events", regularized, True, features),
        (
            "shallow_no_clock_station",
            regularized,
            True,
            [f for f in features if f not in REMOVED_FEATURES],
        ),
    ]
    return [
        {
            "name": name,
            "parameters": {**common, **parameters},
            "equal_event_mass": equal,
            "features": list(columns),
            "rounds": ROUNDS,
            "monotone_constraints": [1 if f == "horizon_hours" else 0 for f in columns],
        }
        for name, parameters, equal, columns in definitions
    ]


def guard_event(event, allowed_split):
    if allowed_split not in ("train", "validation") or event.get("split") != allowed_split:
        raise ValueError("학습 또는 선택 후 validation 구획만 읽을 수 있습니다.")
    name = event["id"]
    if not name or name in (".", "..") or Path(name).name != name:
        raise ValueError("사건 ID는 단일 이름이어야 합니다.")
    start = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00"))
    if start.tzinfo is None or start.timestamp() >= HOLDOUT_START or event.get("locked"):
        raise ValueError("잠긴 사건 및 2025년 이후 자료는 읽을 수 없습니다.")


def load_event(dataset, event, features, allowed_split):
    guard_event(event, allowed_split)
    path = dataset / f"{event['id']}.parquet"
    report = json.loads((dataset / f"{event['id']}-report.json").read_text())
    digest = file_sha256(path)
    if digest != report["sha256"] or report["event"] != event:
        raise ValueError("사건 자료 SHA 또는 계약 불일치")
    table = pq.read_table(
        path,
        columns=[
            *features,
            "fire_within_horizon",
            "issue_epoch_seconds",
            "max_input_available_epoch_seconds",
        ],
    )
    x = np.column_stack([table[name].to_numpy() for name in features])
    y = table["fire_within_horizon"].to_numpy()
    h = x[:, features.index("horizon_hours")]
    issues, available = (
        table[name].to_numpy()
        for name in ("issue_epoch_seconds", "max_input_available_epoch_seconds")
    )
    if len(y) != report["rows"] or not len(y) or not np.isin(y, [0, 1]).all():
        raise ValueError("사건 행 수 또는 이진 정답이 유효하지 않습니다.")
    if not np.isin(h, HORIZONS).all() or np.isinf(x).any():
        raise ValueError("예측 기간 또는 입력 feature가 유효하지 않습니다.")
    if (
        not np.isfinite(issues).all()
        or not np.isfinite(available).all()
        or np.any(available > issues)
        or np.any(issues + h * 3600 >= HOLDOUT_START)
    ):
        raise ValueError("입력 시각 누출 또는 잠긴 2025년 정답 구간")
    return {"x": x, "y": y, "h": h, "sha256": digest, "event": event}


def sample_weights(groups, equal_events):
    groups = np.asarray(groups)
    if groups.ndim != 1 or not len(groups):
        raise ValueError("학습 행의 사건 그룹이 필요합니다.")
    if not equal_events:
        return np.ones(len(groups), dtype=np.float64)
    _, inverse, counts = np.unique(groups, return_inverse=True, return_counts=True)
    return len(groups) / (len(counts) * counts[inverse])


def stack_training(events, training_ids, features, candidate):
    if not training_ids or len(set(training_ids)) != len(training_ids):
        raise ValueError("학습 사건 목록이 비었거나 중복됐습니다.")
    columns = [features.index(f) for f in candidate["features"]]
    x = np.concatenate([events[e]["x"][:, columns] for e in training_ids])
    y = np.concatenate([events[e]["y"] for e in training_ids])
    groups = np.concatenate([np.repeat(e, len(events[e]["y"])) for e in training_ids])
    return x, y, groups, sample_weights(groups, candidate["equal_event_mass"])


def fit(events, training_ids, features, candidate):
    x, y, groups, weights = stack_training(events, training_ids, features, candidate)
    if len(np.unique(y)) != 2:
        raise ValueError("학습 fold에 양성/음성이 모두 필요합니다.")
    matrix = xgb.DMatrix(x, label=y, weight=weights, feature_names=candidate["features"], nthread=2)
    model = xgb.train(
        {
            **candidate["parameters"],
            "monotone_constraints": tuple(candidate["monotone_constraints"]),
        },
        matrix,
        num_boost_round=ROUNDS,
    )
    if json.loads(model.save_config())["learner"]["generic_param"]["device"] != "cpu":
        raise ValueError("CPU 전용 실험이 다른 장치를 사용했습니다.")
    if model.num_boosted_rounds() != ROUNDS:
        raise ValueError("고정 100회 학습 계약 불일치")
    mass = {
        e: {
            "rows": int((groups == e).sum()),
            "row_share": float((groups == e).mean()),
            "weight_sum": float(weights[groups == e].sum()),
            "weight_share": float(weights[groups == e].sum() / weights.sum()),
        }
        for e in training_ids
    }
    return model, mass


def summarize(y, p, horizons, *, with_operating_points=False):
    result = {}
    for hours in HORIZONS:
        mask = horizons == hours
        both = len(np.unique(y[mask])) == 2
        result[str(hours)] = {
            **standard_metrics(y[mask], p[mask], probability=True),
            "eligible_for_cv_selection": both,
            "exclusion_reason": None if both else "held-out horizon lacks both classes",
        }
        if with_operating_points:
            points = []
            status = "both_classes_required"
            if both:
                try:
                    points = operating_points(y[mask], p[mask])
                    status = "validation_selected_diagnostic_only"
                except ValueError:
                    status = "no_finite_threshold_within_requested_fpr"
            result[str(hours)]["operating_points"] = {"status": status, "points": points}
    return result


def prediction(model, data, features, columns):
    return model.inplace_predict(
        np.ascontiguousarray(data["x"][:, [features.index(f) for f in columns]])
    )


def load_reference(run, config_sha, features):
    report_path, plan_path = run / "report.json", run / "plan.json"
    report, plan = json.loads(report_path.read_text()), json.loads(plan_path.read_text())
    if report["plan_sha256"] != file_sha256(plan_path) or plan["config_sha256"] != config_sha:
        raise ValueError("기준 모델 계획 SHA 또는 자료 계약 불일치")
    name = report["selected"]
    if not name or name in (".", "..") or Path(name).name != name:
        raise ValueError("기준 모델 이름이 유효하지 않습니다.")
    selected = report["experiments"][name]
    path = run / f"{name}.ubj"
    if file_sha256(path) != selected["model_sha256"]:
        raise ValueError("기준 모델 SHA 불일치")
    columns = selected["features"]
    cases = [c for c in plan["cases"] if c["name"] == name]
    if (
        len(cases) != 1
        or cases[0]["features"] != columns
        or not columns
        or len(set(columns)) != len(columns)
        or any(f not in features for f in columns)
    ):
        raise ValueError("기준 모델 feature 계약 불일치")
    model = xgb.Booster()
    model.load_model(path)
    model.set_param({"device": "cpu", "nthread": 2})
    if model.feature_names != columns:
        raise ValueError("기준 저장 모델 feature 순서 불일치")
    return (
        model,
        columns,
        {
            "run": str(run),
            "model_sha256": file_sha256(path),
            "report_sha256": file_sha256(report_path),
            "plan_sha256": file_sha256(plan_path),
            "selected": name,
            "source_hashes": plan["source_hashes"],
        },
    )


def experiment(args):
    started = perf_counter()
    cfg = json.loads(args.config.read_text())
    digest = file_sha256(args.config)
    if digest != file_sha256(args.dataset / "config.json") or cfg["profile"] != PROFILE:
        raise ValueError("고정 국내 context-v3 자료 계약 불일치")
    features = [f for f in cfg["feature_names"] if f not in cfg.get("drop_features", [])]
    candidates = make_candidates(features)
    training = [e for e in cfg["events"] if e["split"] == "train"]
    validation = [e for e in cfg["events"] if e["split"] == "validation"]
    if len(training) != 4 or len(validation) != 1:
        raise ValueError("고정 v3의 학습4/validation1 사건 계약 불일치")
    if len({e["id"] for e in cfg["events"]}) != len(cfg["events"]):
        raise ValueError("중복 사건 ID")
    for e in training + validation:
        guard_event(e, e["split"])
    events = {e["id"]: load_event(args.dataset, e, features, "train") for e in training}
    ids = list(events)
    eligible = [
        (e, h)
        for e in ids
        for h in HORIZONS
        if len(np.unique(events[e]["y"][events[e]["h"] == h])) == 2
    ]
    if not eligible:
        raise ValueError("사건별 CV AP를 계산할 양성/음성 셀이 없습니다.")
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {
        "profile": cfg["profile"],
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config_sha256": digest,
        "source_sha256": file_sha256(Path(__file__)),
        "train_source_hashes": {e: d["sha256"] for e, d in events.items()},
        "train_events": ids,
        "validation_events_not_yet_read": [e["id"] for e in validation],
        "features": features,
        "candidates": candidates,
        "maximum_fit_count": len(candidates) * len(ids) + 1,
        "rounds_per_fit": ROUNDS,
        "early_stopping": False,
        "cv_unit": "leave one training event out; no validation/calibration/test in CV",
        "selection": (
            "unweighted mean AP over the same eligible event-horizon cells; "
            "first candidate wins ties"
        ),
        "candidate_failure_rule": "persist all fold failures and abort selection if any fit fails",
        "eligible_cv_cells": [{"event": e, "horizon_hours": h} for e, h in eligible],
        "excluded_cv_cells": [
            {"event": e, "horizon_hours": h, "reason": "both_classes_required"}
            for e in ids
            for h in HORIZONS
            if (e, h) not in eligible
        ],
        "reference_run": str(args.reference_run) if args.reference_run else None,
    }
    write_json(args.output / "plan.json", plan)
    cv = {}
    for candidate in candidates:
        folds = {}
        for held_out in ids:
            train_ids = [e for e in ids if e != held_out]
            try:
                model, shares = fit(events, train_ids, features, candidate)
                p = prediction(model, events[held_out], features, candidate["features"])
                folds[held_out] = {
                    "status": "completed",
                    "training_event_shares": shares,
                    "horizons": summarize(events[held_out]["y"], p, events[held_out]["h"]),
                }
            except (ValueError, RuntimeError, xgb.core.XGBoostError) as exc:
                folds[held_out] = {
                    "status": "failed",
                    "training_events": train_ids,
                    "error_type": type(exc).__name__,
                    "reason": str(exc),
                }
        failed = any(fold["status"] != "completed" for fold in folds.values())
        score = (
            None
            if failed
            else float(
                np.mean([folds[e]["horizons"][str(h)]["average_precision"] for e, h in eligible])
            )
        )
        cv[candidate["name"]] = {
            "status": "failed" if failed else "completed",
            "folds": folds,
            "mean_event_horizon_ap": score,
        }
        write_json(args.output / f"{candidate['name']}-cv.json", cv[candidate["name"]])
        print(json.dumps({"candidate": candidate["name"], "cv_mean_ap": score}), flush=True)
    if any(result["status"] != "completed" for result in cv.values()):
        write_json(
            args.output / "failure.json",
            {
                "status": "cv_failed_no_selection",
                "cv": cv,
                "validation_read": False,
                "operational_use": False,
            },
        )
        raise RuntimeError("실패한 CV fold가 있어 후보 선택과 validation 평가를 중단합니다.")
    selected = max(candidates, key=lambda c: cv[c["name"]]["mean_event_horizon_ap"])
    receipt = {
        "selected": selected["name"],
        "selected_at_utc": datetime.now(UTC).isoformat(),
        "plan_sha256": file_sha256(args.output / "plan.json"),
        "cv_result_sha256": {
            c["name"]: file_sha256(args.output / f"{c['name']}-cv.json") for c in candidates
        },
        "validation_read_before_selection": False,
    }
    write_json(args.output / "selection.json", receipt)
    model, shares = fit(events, ids, features, selected)
    path = args.output / "selected.ubj"
    model.save_model(path)
    cpu = xgb.Booster()
    cpu.load_model(path)
    cpu.set_param({"device": "cpu", "nthread": 2})
    if cpu.feature_names != selected["features"]:
        raise ValueError("재로딩 모델 feature 순서 불일치")
    x, _, _, _ = stack_training(events, ids, features, selected)
    before, after = model.inplace_predict(x), cpu.inplace_predict(x)
    np.testing.assert_allclose(before, after, rtol=1e-6, atol=1e-7)
    probe = x[: min(len(x), 8192)].copy()
    cumulative = []
    for hours in HORIZONS:
        probe[:, selected["features"].index("horizon_hours")] = hours
        cumulative.append(cpu.inplace_predict(probe))
    if np.any(np.diff(np.asarray(cumulative), axis=0) < -1e-6):
        raise ValueError("기간 단조성 위반")
    # This is deliberately the first validation Parquet read in the run.
    val = {e["id"]: load_event(args.dataset, e, features, "validation") for e in validation}
    diagnostics = {
        e: summarize(
            d["y"],
            prediction(cpu, d, features, selected["features"]),
            d["h"],
            with_operating_points=True,
        )
        for e, d in val.items()
    }
    reference = None
    if args.reference_run:
        old, columns, reference = load_reference(args.reference_run, digest, features)
        for e, d in {**events, **val}.items():
            if reference["source_hashes"].get(e) != d["sha256"]:
                raise ValueError("기준 모델과 현재 사건 자료 SHA 불일치")
        reference["validation"] = {
            e: summarize(
                d["y"], prediction(old, d, features, columns), d["h"], with_operating_points=True
            )
            for e, d in val.items()
        }
    report = {
        "profile": cfg["profile"],
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "plan_sha256": file_sha256(args.output / "plan.json"),
        "selection_sha256": file_sha256(args.output / "selection.json"),
        "model_sha256": file_sha256(path),
        "selected": selected,
        "cv": cv,
        "training_event_count": len(ids),
        "eligible_cv_cell_count": len(eligible),
        "training_event_shares": shares,
        "validation_event_count": len(val),
        "validation_source_hashes": {e: d["sha256"] for e, d in val.items()},
        "validation": diagnostics,
        "reference": reference,
        "saved_trees": cpu.num_boosted_rounds(),
        "cpu_reload_max_abs_difference": float(np.max(np.abs(before - after))),
        "monotonicity_verified": True,
        "monotonicity_probe_rows": len(probe),
        "operational_use": False,
        "probability_calibrated": False,
        "test_evaluated": False,
        "elapsed_seconds": round(perf_counter() - started, 3),
        "limitations": [
            "Four training-event groups and one seed only; event-horizon rows are not "
            "independent incidents.",
            "CV selects among four candidates, so its winning score is optimistic "
            "model-selection evidence, not independent final performance.",
            "Old Hongseong validation was already inspected in earlier work. This run does "
            "not use it for selection, but its diagnostic is not a fresh test.",
            "Fixed 100 rounds and equal event weighting are prespecified research variants, "
            "not validated operational choices.",
            "Unavailable held-out horizon AP cells are explicitly excluded identically "
            "for all candidates; coverage limits remain.",
            "FPR operating points are chosen on diagnostic validation and do not "
            "authorize any response level or alert threshold.",
            *cfg.get("limitations", []),
        ],
    }
    write_json(args.output / "report.json", report)
    print(
        json.dumps({"selected": selected["name"], "elapsed_seconds": report["elapsed_seconds"]}),
        flush=True,
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("dataset", "config", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--reference-run", type=Path)
    experiment(parser.parse_args())


if __name__ == "__main__":
    main()
