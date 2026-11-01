"""고정 v4의 학습 기간그룹 CV. 검증 사건은 선택 후 한 번만 읽는 CPU 연구."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import pyarrow.parquet as pq
import xgboost as xgb

from bonghwa_training import generalization_experiment as common
from bonghwa_training import ranking_audit
from bonghwa_training.download import file_sha256

PROFILE = "kor_gk2a_10min_approach_hindcast_1_3_6h_v4_expanded"
CONTEXT_PROFILE = PROFILE + "_context_v1"
ALLOWED_PROFILES = frozenset((PROFILE, CONTEXT_PROFILE))
HORIZONS = (1, 3, 6)
ROUNDS = 100
POSITIVE_WEIGHT_CAP = 100.0
BASELINES = {
    "negative_current_fire_distance": "distance_fire_km",
    "negative_recent_fire_distance": "distance_recent_fire_60m_km",
}


def make_candidates(features):
    if (
        not features
        or len(set(features)) != len(features)
        or not {"horizon_hours", *BASELINES.values()}.issubset(features)
    ):
        raise ValueError("중복 feature 또는 필수 기간/거리 feature 누락")
    parameters = {
        "objective": "binary:logistic",
        "tree_method": "hist",
        "device": "cpu",
        "nthread": 2,
        "seed": 47,
        "scale_pos_weight": 1.0,
        "subsample": 0.8,
        "colsample_bytree": 0.9,
        "max_bin": 256,
        "eval_metric": "logloss",
        "max_depth": 4,
        "min_child_weight": 5,
        "lambda": 20,
        "gamma": 0,
        "eta": 0.05,
        "max_delta_step": 0,
    }
    definitions = [
        ("depth4_unit", "unit", False, {}),
        ("depth4_positive3", "fixed3", False, {}),
        ("depth4_positive_sqrt", "training_fold_sqrt", False, {}),
        ("depth4_equal_events", "unit", True, {}),
        (
            "depth2_regularized_equal_events",
            "unit",
            True,
            {
                "max_depth": 2,
                "min_child_weight": 25,
                "lambda": 100,
                "gamma": 1,
                "eta": 0.03,
                "max_delta_step": 1,
            },
        ),
    ]
    return [
        {
            "name": name,
            "parameters": {
                **parameters,
                **changes,
                "scale_pos_weight": 3.0 if rule == "fixed3" else 1.0,
            },
            "positive_weight_rule": rule,
            "positive_weight_cap": POSITIVE_WEIGHT_CAP,
            "equal_event_mass": equal,
            "features": list(features),
            "rounds": ROUNDS,
            "monotone_constraints": [int(f == "horizon_hours") for f in features],
        }
        for name, rule, equal, changes in definitions
    ]


def period_group(event):
    """정답을 보지 않고 정한 날짜 그룹. 동해안 3월4~5일은 같은 묶음이다."""
    start = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00"))
    day = start.astimezone(UTC).date().isoformat()
    return "2022-03-04_05" if day in ("2022-03-04", "2022-03-05") else day


def load_event(dataset, event, features, allowed_split):
    common.guard_event(event, allowed_split)
    date = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00")).astimezone(UTC)
    if (allowed_split == "train" and date.year not in (2020, 2021, 2022)) or (
        allowed_split == "validation" and date.year != 2023
    ):
        raise ValueError("v4 학습2020~2022/validation2023 연도 계약 불일치")
    start = date.timestamp()
    if start + (event["hours"] + max(HORIZONS) + 1) * 3600 >= common.HOLDOUT_START:
        raise ValueError("2025년 정답 구간에 걸치는 사건 계약")
    path = dataset / f"{event['id']}.parquet"
    report_path = dataset / f"{event['id']}-report.json"
    report = json.loads(report_path.read_text())
    digest = file_sha256(path)
    if digest != report["sha256"] or report["event"] != event:
        raise ValueError("사건 자료 SHA 또는 계약 불일치")
    columns = [
        *features,
        "fire_within_horizon",
        "issue_epoch_seconds",
        "max_input_available_epoch_seconds",
        "row",
        "col",
    ]
    table = pq.read_table(path, columns=columns)
    x = np.column_stack([table[name].to_numpy() for name in features])
    y = table["fire_within_horizon"].to_numpy()
    h = x[:, features.index("horizon_hours")]
    issues, available, rows, cols = (
        table[name].to_numpy()
        for name in ("issue_epoch_seconds", "max_input_available_epoch_seconds", "row", "col")
    )
    if len(y) != report["rows"] or not np.isin(y, [0, 1]).all():
        raise ValueError("사건 행 수 또는 이진 정답 오류")
    if not np.isin(h, HORIZONS).all() or np.isinf(x).any():
        raise ValueError("예측 기간 또는 입력 feature 오류")
    if (
        not all(np.isfinite(v).all() for v in (issues, available, rows, cols))
        or np.any(available > issues)
        or np.any(issues < start)
        or np.any(issues >= start + (event["hours"] + 1) * 3600)
        or np.any(issues + h * 3600 >= common.HOLDOUT_START)
    ):
        raise ValueError("사건 시각 범위/입력 누출/좌표 오류")
    identity = np.column_stack((issues, h, rows, cols))
    if len(np.unique(identity, axis=0)) != len(y):
        raise ValueError("동일 사건·시점·기간·격자의 중복 행")
    return {
        "x": x,
        "y": y,
        "h": h,
        "issues": issues,
        "rows": rows,
        "cols": cols,
        "sha256": digest,
        "report_sha256": file_sha256(report_path),
        "event": event,
        "empty_reason": report.get("unusable_reason") if not len(y) else None,
    }


def resolve_candidate(candidate, events, training_ids):
    """양성 가중치는 이번 적합의 학습 행에서만 산출한다."""
    y = np.concatenate([events[e]["y"] for e in training_ids])
    positive, negative = int(y.sum()), int((y == 0).sum())
    if not positive or not negative:
        raise ValueError("학습 fold에 양성/음성이 모두 필요합니다.")
    rule = candidate["positive_weight_rule"]
    weight = {
        "unit": 1.0,
        "fixed3": 3.0,
        "training_fold_sqrt": min(POSITIVE_WEIGHT_CAP, float(np.sqrt(negative / positive))),
    }[rule]
    return {
        **candidate,
        "parameters": {**candidate["parameters"], "scale_pos_weight": weight},
        "training_positive_rows": positive,
        "training_negative_rows": negative,
    }


def fit(events, training_ids, features, candidate):
    resolved = resolve_candidate(candidate, events, training_ids)
    model, shares = common.fit(events, training_ids, features, resolved)
    for event_id in training_ids:
        y = events[event_id]["y"]
        sample_weight = shares[event_id]["weight_sum"] / len(y)
        shares[event_id]["positive_rows"] = int(y.sum())
        shares[event_id]["class_adjusted_weight_sum"] = float(
            sample_weight * ((y == 0).sum() + y.sum() * resolved["parameters"]["scale_pos_weight"])
        )
    total = sum(s["class_adjusted_weight_sum"] for s in shares.values())
    for share in shares.values():
        share["class_adjusted_weight_share"] = share["class_adjusted_weight_sum"] / total
    return model, shares, resolved


def evaluate(data, scores, *, probability):
    results = {}
    for hours in HORIZONS:
        mask = data["h"] == hours
        y, p = data["y"][mask], scores[mask]
        both = len(np.unique(y)) == 2
        metrics = ranking_audit.standard_metrics(y, p, probability=probability)
        metrics.setdefault("brier", None)
        metrics.setdefault("logloss", None)
        results[str(hours)] = {
            **metrics,
            "eligible_for_ap_comparison": both,
            "exclusion_reason": None if both else "both_classes_required",
            "top_10_percent_per_issue": ranking_audit.workload_metrics(
                y, p, data["issues"][mask], data["rows"][mask], data["cols"][mask], 10
            ),
        }
    return results


def distance_diagnostics(events, features):
    return {
        name: {
            e: evaluate(d, -d["x"][:, features.index(column)], probability=False)
            for e, d in events.items()
        }
        for name, column in BASELINES.items()
    }


def eligible_cells(events):
    return [
        (e, h)
        for e, d in events.items()
        for h in HORIZONS
        if len(np.unique(d["y"][d["h"] == h])) == 2
    ]


def training_horizon_priors(events, training_ids):
    """단위 가중 학습 정답의 기간별 비율. 검증 정답/모델 출력은 받지 않는다."""
    if not training_ids or len(set(training_ids)) != len(training_ids):
        raise ValueError("prior 산출에 고유한 학습 사건 목록이 필요합니다.")
    for event_id in training_ids:
        if events[event_id]["event"]["split"] != "train":
            raise ValueError("prior는 학습 사건 정답만 사용할 수 있습니다.")
    priors = {}
    for hours in HORIZONS:
        labels = np.concatenate([events[e]["y"][events[e]["h"] == hours] for e in training_ids])
        if not len(labels):
            raise ValueError(f"{hours}시간 prior에 필요한 학습 정답이 없습니다.")
        priors[str(hours)] = {
            "training_rows": len(labels),
            "training_positives": int(labels.sum()),
            "score": float(labels.mean()),
        }
    return priors


def prior_scores(horizons, priors):
    if not np.isin(horizons, HORIZONS).all():
        raise ValueError("prior 적용 예측 기간 오류")
    return np.asarray([priors[str(int(h))]["score"] for h in horizons], dtype=float)


def mean_ap(diagnostics, cells):
    return (
        float(np.mean([diagnostics[e][str(h)]["average_precision"] for e, h in cells]))
        if cells
        else None
    )


def inventory(events):
    return {
        e: {
            "rows": len(d["y"]),
            "positives": int(d["y"].sum()),
            "period_group": period_group(d["event"]),
            "empty_reason": d["empty_reason"],
            "horizons": {
                str(h): {
                    "rows": int((d["h"] == h).sum()),
                    "positives": int(d["y"][d["h"] == h].sum()),
                    "both_classes": len(np.unique(d["y"][d["h"] == h])) == 2,
                }
                for h in HORIZONS
            },
        }
        for e, d in events.items()
    }


def save_model(model, path, events, ids, features, candidate):
    model.save_model(path)
    restored = xgb.Booster()
    restored.load_model(path)
    restored.set_param({"device": "cpu", "nthread": 2})
    if restored.feature_names != features or restored.num_boosted_rounds() != ROUNDS:
        raise ValueError("저장 모델의 feature/고정 반복 횟수 불일치")
    max_difference, checked_rows = 0.0, 0
    for event_id in ids:
        x = events[event_id]["x"]
        before, after = model.inplace_predict(x), restored.inplace_predict(x)
        np.testing.assert_allclose(before, after, rtol=1e-6, atol=1e-7)
        max_difference = max(max_difference, float(np.max(np.abs(before - after))))
        probe = x[: min(len(x), 8192)].copy()
        p = []
        for hours in HORIZONS:
            probe[:, features.index("horizon_hours")] = hours
            p.append(restored.inplace_predict(probe))
        if np.any(np.diff(np.asarray(p), axis=0) < -1e-6):
            raise ValueError("기간 단조성 위반")
        checked_rows += len(probe)
    return restored, {
        "model_sha256": file_sha256(path),
        "candidate": candidate,
        "saved_trees": restored.num_boosted_rounds(),
        "cpu_reload_max_abs_difference": max_difference,
        "monotonicity_probe_rows": checked_rows,
        "monotonicity_verified": True,
    }


def experiment(args):
    started = perf_counter()
    cfg = json.loads(args.config.read_text())
    digest = file_sha256(args.config)
    if (
        digest != file_sha256(args.dataset / "config.json")
        or cfg.get("profile") not in ALLOWED_PROFILES
        or cfg.get("reader") != "gk2a"
        or cfg.get("horizons_hours") != list(HORIZONS)
    ):
        raise ValueError("고정 국내 v4 관측/context 자료 계약 불일치")
    features = [f for f in cfg["feature_names"] if f not in cfg.get("drop_features", [])]
    if cfg["profile"] == CONTEXT_PROFILE and (
        not cfg.get("context_features") or not set(cfg["context_features"]).issubset(features)
    ):
        raise ValueError("context profile의 환경 feature 계약 누락")
    candidates = make_candidates(features)
    training = [e for e in cfg["events"] if e["split"] == "train"]
    validation = [e for e in cfg["events"] if e["split"] == "validation"]
    if len({e["id"] for e in cfg["events"]}) != len(cfg["events"]):
        raise ValueError("중복 사건 ID")
    if not training or not validation:
        raise ValueError("학습/validation 사건 계약 누락")
    for event in training + validation:
        common.guard_event(event, event["split"])
    events = {e["id"]: load_event(args.dataset, e, features, "train") for e in training}
    ids = [e for e, d in events.items() if len(d["y"])]
    groups = {
        g: [e for e in ids if period_group(events[e]["event"]) == g]
        for g in sorted({period_group(events[e]["event"]) for e in ids})
    }
    cells = eligible_cells(events)
    if len(groups) < 2 or not cells:
        raise ValueError("기간그룹 2개 이상과 양성/음성 사건·기간 셀이 필요합니다.")
    priors = training_horizon_priors(events, ids)
    args.output.mkdir(parents=True, exist_ok=False)
    source_files = [
        Path(__file__),
        Path(common.__file__),
        Path(ranking_audit.__file__),
        Path(__file__).with_name("download.py"),
        Path(__file__).with_name("risk_metrics.py"),
    ]
    if cfg["profile"] == CONTEXT_PROFILE:
        source_files.append(Path(__file__).with_name("hourly_context.py"))
    plan = {
        "profile": cfg["profile"],
        "input_variant": "context" if cfg["profile"] == CONTEXT_PROFILE else "observations",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config_sha256": digest,
        "code_sha256": {p.name: file_sha256(p) for p in source_files},
        "xgboost_version": xgb.__version__,
        "source_hashes": {e: d["sha256"] for e, d in events.items()},
        "event_report_hashes": {e: d["report_sha256"] for e, d in events.items()},
        "features": features,
        "feature_count": len(features),
        "candidates": candidates,
        "train_events": inventory(events),
        "training_horizon_priors": priors,
        "prior_source_rule": "unweighted labels from train events only, before validation read",
        "period_groups": groups,
        "group_rule": "UTC start date; 2022-03-04 and 2022-03-05 combined before fitting",
        "eligible_cv_cells": [{"event": e, "horizon_hours": h} for e, h in cells],
        "cv_selection": "mean AP of identical eligible event-horizon cells; first wins ties",
        "candidate_failure_rule": "persist every candidate; any failed fold aborts selection",
        "validation_events_not_yet_read_in_this_run": [e["id"] for e in validation],
        "prior_validation_exposure": "earlier exploratory v3/v4 studies may inspect 2023 data",
        "maximum_fit_count": len(candidates) * len(groups) + 2,
        "rounds_per_fit": ROUNDS,
        "early_stopping": False,
        "validation_tuning": False,
        "top_percent_per_issue": 10,
        "weight_share_semantics": (
            "weight_sum/share are before class weighting; class_adjusted_weight_sum/share "
            "also apply scale_pos_weight to positive rows"
        ),
        "calibration_read": False,
        "test_evaluated": False,
        "operational_use": False,
    }
    common.write_json(args.output / "plan.json", plan)
    baselines = distance_diagnostics(events, features)
    cv = {}
    for candidate in candidates:
        folds, diagnostics = {}, {}
        for group, held_ids in groups.items():
            training_ids = [e for e in ids if e not in held_ids]
            try:
                model, shares, resolved = fit(events, training_ids, features, candidate)
                held = {
                    e: evaluate(events[e], model.inplace_predict(events[e]["x"]), probability=True)
                    for e in held_ids
                }
                diagnostics.update(held)
                folds[group] = {
                    "status": "completed",
                    "held_out_events": held_ids,
                    "training_events": training_ids,
                    "resolved_positive_weight": resolved["parameters"]["scale_pos_weight"],
                    "training_positive_rows": resolved["training_positive_rows"],
                    "training_negative_rows": resolved["training_negative_rows"],
                    "training_event_shares": shares,
                    "held_out": held,
                }
            except (ValueError, RuntimeError, xgb.core.XGBoostError) as exc:
                folds[group] = {
                    "status": "failed",
                    "held_out_events": held_ids,
                    "training_events": training_ids,
                    "error_type": type(exc).__name__,
                    "reason": str(exc),
                }
        failed = any(f["status"] != "completed" for f in folds.values())
        score = None if failed else mean_ap(diagnostics, cells)
        cv[candidate["name"]] = {
            "status": "failed" if failed else "completed",
            "folds": folds,
            "mean_event_horizon_ap": score,
        }
        common.write_json(args.output / f"{candidate['name']}-cv.json", cv[candidate["name"]])
        print(json.dumps({"candidate": candidate["name"], "cv_mean_ap": score}), flush=True)
    if any(r["status"] == "failed" for r in cv.values()):
        common.write_json(
            args.output / "failure.json",
            {
                "cv": cv,
                "status": "cv_failed_no_selection",
                "validation_read": False,
            },
        )
        raise RuntimeError("실패한 CV fold가 있어 선택과 validation 평가를 중단합니다.")
    selected = max(candidates, key=lambda c: cv[c["name"]]["mean_event_horizon_ap"])
    common.write_json(
        args.output / "selection.json",
        {
            "selected": selected["name"],
            "selected_at_utc": datetime.now(UTC).isoformat(),
            "plan_sha256": file_sha256(args.output / "plan.json"),
            "cv_result_sha256": {
                c["name"]: file_sha256(args.output / f"{c['name']}-cv.json") for c in candidates
            },
            "validation_read_before_selection_in_this_run": False,
            "mean_event_horizon_ap": cv[selected["name"]]["mean_event_horizon_ap"],
            "distance_baseline_mean_event_horizon_ap": {
                name: mean_ap(result, cells) for name, result in baselines.items()
            },
        },
    )
    models, model_reports = {}, {}
    for candidate in {c["name"]: c for c in (candidates[0], selected)}.values():
        model, shares, resolved = fit(events, ids, features, candidate)
        models[candidate["name"]], details = save_model(
            model, args.output / f"{candidate['name']}.ubj", events, ids, features, resolved
        )
        model_reports[candidate["name"]] = {**details, "training_event_shares": shares}
    # First validation event report/Parquet reads in this run, after immutable selection.
    val = {e["id"]: load_event(args.dataset, e, features, "validation") for e in validation}
    val_results = distance_diagnostics(val, features)
    val_results["constant_training_prior"] = {
        e: evaluate(d, prior_scores(d["h"], priors), probability=True) for e, d in val.items()
    }
    for name, model in models.items():
        val_results[name] = {
            e: evaluate(
                d,
                model.inplace_predict(d["x"]) if len(d["y"]) else np.array([]),
                probability=True,
            )
            for e, d in val.items()
        }
    val_cells = eligible_cells(val)
    report = {
        "profile": cfg["profile"],
        "input_variant": plan["input_variant"],
        "feature_count": len(features),
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "plan_sha256": file_sha256(args.output / "plan.json"),
        "selection_sha256": file_sha256(args.output / "selection.json"),
        "selected": selected["name"],
        "reference": candidates[0]["name"],
        "models": model_reports,
        "cv": cv,
        "cv_distance_baselines": baselines,
        "training_event_count_requested": len(events),
        "training_event_count_nonempty": len(ids),
        "training_period_group_count": len(groups),
        "training_horizon_priors": priors,
        "eligible_cv_cell_count": len(cells),
        "validation_source_hashes": {e: d["sha256"] for e, d in val.items()},
        "validation_event_report_hashes": {e: d["report_sha256"] for e, d in val.items()},
        "validation_inventory": inventory(val),
        "validation": val_results,
        "validation_eligible_cells": [{"event": e, "horizon_hours": h} for e, h in val_cells],
        "validation_mean_event_horizon_ap": {
            name: mean_ap(result, val_cells) for name, result in val_results.items()
        },
        "elapsed_seconds": round(perf_counter() - started, 3),
        "probability_calibrated": False,
        "operational_use": False,
        "calibration_read": False,
        "test_evaluated": False,
        "limitations": [
            "Winning CV AP is optimistic selection evidence among five candidates, not a test.",
            "2023 validation has prior exploratory exposure; this run alone does not tune on it.",
            "Few period groups and one seed; date grouping cannot prove event independence.",
            "Repeated cells/times/horizons are not independent fires, people, or alerts.",
            "Top10% is per-issue research workload, not an alert or response-level threshold.",
            "Zero-row events and single-class event-horizons are recorded; undefined AP is null.",
            "Distance is a ranking score, not probability; its Brier/logloss are null.",
            "Constant prior uses unweighted training labels per horizon, not model outputs "
            "or validation prevalence; it is not a calibrated operational risk either.",
            "Positive weighting changes score calibration; outputs are not calibrated risk.",
            "Future censored observations define an eligible cohort with selection bias.",
            *cfg.get("limitations", []),
        ],
    }
    common.write_json(args.output / "report.json", report)
    print(
        json.dumps({"selected": selected["name"], "seconds": report["elapsed_seconds"]}), flush=True
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("dataset", "config", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    experiment(parser.parse_args())


if __name__ == "__main__":
    main()
