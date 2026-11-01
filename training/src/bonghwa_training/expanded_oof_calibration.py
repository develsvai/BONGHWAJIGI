"""고정 v4 선택 후보의 학습 기간그룹 OOF 점수로 한 번만 sigmoid를 적합한다."""

import argparse
import json
import warnings
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import sklearn
import xgboost as xgb
from scipy.special import expit
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

from bonghwa_training import expanded_generalization_experiment as expanded
from bonghwa_training.download import file_sha256

EPSILON = 1e-7
SIGMOID_PARAMETERS = {
    "C": 1.0,
    "class_weight": None,
    "solver": "lbfgs",
    "max_iter": 1000,
    "random_state": 47,
}


def read_json(path):
    return json.loads(path.read_text())


def logit_scores(p):
    p = np.asarray(p, dtype=np.float64)
    if p.ndim != 1 or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("원시 점수는 유한한 0~1 일차원 배열이어야 합니다.")
    clipped = np.clip(p, EPSILON, 1 - EPSILON)
    return np.log(clipped / (1 - clipped)).reshape(-1, 1)


def fit_sigmoid(p, y):
    """OOF 점수와 학습 정답만 받는다. 미수렴/비양의 기울기는 사용을 보류한다."""
    x = logit_scores(p)
    y = np.asarray(y)
    if y.ndim != 1 or len(y) != len(x) or not np.isin(y, [0, 1]).all():
        raise ValueError("sigmoid 학습 정답 계약 오류")
    if len(np.unique(y)) != 2:
        return {
            "status": "withheld",
            "calibration_fitted": False,
            "reason": "both_classes_required",
        }
    try:
        with warnings.catch_warnings(record=True) as seen, threadpool_limits(limits=2):
            warnings.simplefilter("always", ConvergenceWarning)
            model = LogisticRegression(**SIGMOID_PARAMETERS).fit(x, y)
        slope, intercept = float(model.coef_[0, 0]), float(model.intercept_[0])
        converged = not any(issubclass(w.category, ConvergenceWarning) for w in seen)
        converged = converged and int(model.n_iter_[0]) < SIGMOID_PARAMETERS["max_iter"]
        finite = np.isfinite([slope, intercept]).all()
        accepted = finite and converged and slope > 0
        return {
            "status": "fitted_research_only" if accepted else "withheld",
            "calibration_fitted": True,
            "slope": slope if np.isfinite(slope) else None,
            "intercept": intercept if np.isfinite(intercept) else None,
            "iterations": int(model.n_iter_[0]),
            "converged": bool(converged),
            "reason": None
            if accepted
            else (
                "nonfinite_coefficients"
                if not finite
                else "nonconvergence"
                if not converged
                else "nonpositive_slope"
            ),
        }
    except (ValueError, RuntimeError, FloatingPointError) as exc:
        return {
            "status": "withheld",
            "calibration_fitted": False,
            "reason": "sigmoid_fit_failed",
            "error_type": type(exc).__name__,
        }


def transform(p, calibration):
    if calibration["status"] != "fitted_research_only" or calibration["slope"] <= 0:
        raise ValueError("사용 보류된 보정기는 적용할 수 없습니다.")
    return expit(calibration["slope"] * logit_scores(p).ravel() + calibration["intercept"])


def assign_oof(predictions, coverage, event_id, indices, scores):
    indices, scores = np.asarray(indices), np.asarray(scores)
    logit_scores(scores)
    if (
        indices.ndim != 1
        or len(indices) != len(scores)
        or not np.issubdtype(indices.dtype, np.integer)
        or len(np.unique(indices)) != len(indices)
        or np.any(indices < 0)
        or np.any(indices >= len(coverage[event_id]))
        or np.any(coverage[event_id][indices] != 0)
    ):
        raise ValueError("OOF 행 중복/범위/길이 오류")
    predictions[event_id][indices] = scores
    coverage[event_id][indices] += 1


def check_coverage(predictions, coverage):
    for event_id, counts in coverage.items():
        if not np.all(counts == 1) or not np.isfinite(predictions[event_id]).all():
            raise ValueError("OOF 행 누락 또는 중복")


def verify(args):
    """완료된 연구 artifact metadata만 읽는다. validation 사건 파일은 열지 않는다."""
    cfg = read_json(args.config)
    digest = file_sha256(args.config)
    run = args.run
    report, plan, selection = (
        read_json(run / name) for name in ("report.json", "plan.json", "selection.json")
    )
    if (
        cfg.get("profile") not in expanded.ALLOWED_PROFILES
        or cfg.get("reader") != "gk2a"
        or cfg.get("horizons_hours") != [1, 3, 6]
        or digest != file_sha256(args.dataset / "config.json")
        or digest != plan["config_sha256"]
        or plan["profile"] != cfg["profile"]
        or report["profile"] != cfg["profile"]
        or report["plan_sha256"] != file_sha256(run / "plan.json")
        or selection["plan_sha256"] != file_sha256(run / "plan.json")
        or report["selection_sha256"] != file_sha256(run / "selection.json")
        or plan["xgboost_version"] != xgb.__version__
    ):
        raise ValueError("고정 v4 자료/계획/선택/XGBoost 버전 계약 불일치")
    features = [f for f in cfg["feature_names"] if f not in cfg.get("drop_features", [])]
    candidates = expanded.make_candidates(features)
    if plan["features"] != features or plan["candidates"] != candidates:
        raise ValueError("선택 후보의 고정 입력/매개변수 계약 불일치")
    for name, digest in plan["code_sha256"].items():
        expanded.ranking_audit._safe_name(name)
        if digest != file_sha256(Path(expanded.__file__).with_name(name)):
            raise ValueError("OOF 재현 학습 코드 SHA 불일치")
    expected_code = {
        "expanded_generalization_experiment.py",
        "generalization_experiment.py",
        "ranking_audit.py",
        "download.py",
        "risk_metrics.py",
    }
    if cfg["profile"] == expanded.CONTEXT_PROFILE:
        expected_code.add("hourly_context.py")
    if not expected_code.issubset(plan["code_sha256"]):
        raise ValueError("OOF 재현 학습 코드 SHA 누락")
    if set(selection["cv_result_sha256"]) != {c["name"] for c in candidates}:
        raise ValueError("후보별 CV 선택 근거 누락")
    cv = {}
    for candidate in candidates:
        name = candidate["name"]
        path = run / f"{name}-cv.json"
        cv[name] = read_json(path)
        if (
            file_sha256(path) != selection["cv_result_sha256"][name]
            or cv[name] != report["cv"][name]
            or cv[name]["status"] != "completed"
            or cv[name]["mean_event_horizon_ap"] is None
            or not np.isfinite(cv[name]["mean_event_horizon_ap"])
        ):
            raise ValueError("CV 선택 결과 SHA/상태 불일치")
    selected = max(candidates, key=lambda c: cv[c["name"]]["mean_event_horizon_ap"])
    name = selected["name"]
    if report["selected"] != name or selection["selected"] != name:
        raise ValueError("기존 CV 선택 후보가 고정 선택 규칙과 다릅니다.")
    model_path = run / f"{name}.ubj"
    if report["models"][name]["model_sha256"] != file_sha256(model_path):
        raise ValueError("선택 모델 SHA 불일치")
    model = xgb.Booster()
    model.load_model(model_path)
    model.set_param({"device": "cpu", "nthread": 2})
    if (
        model.feature_names != features
        or model.num_boosted_rounds() != expanded.ROUNDS
        or json.loads(model.save_config())["learner"]["objective"]["name"] != "binary:logistic"
    ):
        raise ValueError("선택 모델 feature/반복 횟수/objective 불일치")
    training = [e for e in cfg["events"] if e["split"] == "train"]
    validation = [e for e in cfg["events"] if e["split"] == "validation"]
    if (
        not training
        or not validation
        or len({e["id"] for e in cfg["events"]}) != len(cfg["events"])
    ):
        raise ValueError("학습/검증 사건 목록 오류")
    for event in training + validation:
        expanded.common.guard_event(event, event["split"])
    return cfg, report, plan, selection, selected, features, model, training, validation


def verify_replay_metrics(actual, expected):
    for hours in expanded.HORIZONS:
        for metric in ("rows", "positives", "average_precision", "brier", "logloss"):
            left, right = actual[str(hours)][metric], expected[str(hours)][metric]
            if left is None and right is None:
                continue
            if left is None or right is None or not np.isclose(left, right, rtol=1e-10, atol=1e-12):
                raise ValueError("선택 후보의 OOF 재현 지표 불일치")


def monotonicity_probe(model, calibration, events, features):
    checked = 0
    for data in events.values():
        if not len(data["y"]):
            continue
        x = data["x"][:8192].copy()
        raw, calibrated = [], []
        for horizon in expanded.HORIZONS:
            x[:, features.index("horizon_hours")] = horizon
            p = model.inplace_predict(x)
            raw.append(p)
            calibrated.append(transform(p, calibration))
        if np.any(np.diff(raw, axis=0) < -1e-6) or np.any(np.diff(calibrated, axis=0) < -1e-6):
            raise ValueError("원시/보정 점수의 기간 단조성 위반")
        checked += len(x)
    return checked


def improvements(results):
    changes = {}
    for event_id, raw in results["raw"].items():
        changes[event_id] = {}
        for hours in expanded.HORIZONS:
            original, calibrated = raw[str(hours)], results["sigmoid"][event_id][str(hours)]
            changes[event_id][str(hours)] = {
                "rows": original["rows"],
                "brier_reduction": (
                    original["brier"] - calibrated["brier"]
                    if original["brier"] is not None
                    else None
                ),
                "logloss_reduction": (
                    original["logloss"] - calibrated["logloss"]
                    if original["logloss"] is not None
                    else None
                ),
                "average_precision_change": (
                    calibrated["average_precision"] - original["average_precision"]
                    if original["average_precision"] is not None
                    else None
                ),
            }
    return changes


def experiment(args):
    started = perf_counter()
    cfg, source_report, source_plan, _, candidate, features, model, training, validation = verify(
        args
    )
    events = {e["id"]: expanded.load_event(args.dataset, e, features, "train") for e in training}
    if {e: d["sha256"] for e, d in events.items()} != source_plan["source_hashes"] or {
        e: d["report_sha256"] for e, d in events.items()
    } != source_plan["event_report_hashes"]:
        raise ValueError("OOF 학습 자료 SHA 불일치")
    ids = [e for e, d in events.items() if len(d["y"])]
    groups = {
        g: [e for e in ids if expanded.period_group(events[e]["event"]) == g]
        for g in sorted({expanded.period_group(events[e]["event"]) for e in ids})
    }
    priors = expanded.training_horizon_priors(events, ids)
    if (
        groups != source_plan["period_groups"]
        or len(groups) < 2
        or priors != source_plan["training_horizon_priors"]
        or priors != source_report["training_horizon_priors"]
        or expanded.resolve_candidate(candidate, events, ids)
        != source_report["models"][candidate["name"]]["candidate"]
    ):
        raise ValueError("OOF 기간그룹/학습 prior/최종 학습 매개변수 불일치")
    folds = source_report["cv"][candidate["name"]]["folds"]
    if set(folds) != set(groups):
        raise ValueError("기존 CV fold 목록 불일치")
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "profile": cfg["profile"],
        "source_run": str(args.run),
        "config_sha256": file_sha256(args.config),
        "source_plan_sha256": file_sha256(args.run / "plan.json"),
        "source_selection_sha256": file_sha256(args.run / "selection.json"),
        "source_report_sha256": file_sha256(args.run / "report.json"),
        "selected_model_sha256": source_report["models"][candidate["name"]]["model_sha256"],
        "source_code_sha256": file_sha256(Path(__file__)),
        "replayed_training_code_sha256": source_plan["code_sha256"],
        "xgboost_version": xgb.__version__,
        "sklearn_version": sklearn.__version__,
        "selected_candidate": candidate,
        "features": features,
        "period_groups": groups,
        "training_source_hashes": source_plan["source_hashes"],
        "training_horizon_priors": priors,
        "train_inventory": expanded.inventory(events),
        "maximum_xgboost_fits": len(groups),
        "rounds_per_fit": expanded.ROUNDS,
        "sigmoid_fits": 1,
        "sigmoid_parameters": SIGMOID_PARAMETERS,
        "sigmoid_input": "one logit of raw OOF probability, unweighted rows",
        "logit_clip_epsilon": EPSILON,
        "cpu_threads": 2,
        "acceptance_rule": "finite coefficients, converged fit, slope strictly positive",
        "validation_tuning": False,
        "calibration_split_read": False,
        "test_evaluated": False,
        "operational_use": False,
    }
    expanded.common.write_json(args.output / "plan.json", plan)
    predictions = {e: np.full(len(d["y"]), np.nan) for e, d in events.items()}
    coverage = {e: np.zeros(len(d["y"]), dtype=np.uint8) for e, d in events.items()}
    replay = {}
    calibration = {"status": "withheld", "calibration_fitted": False}
    try:
        for group, held_ids in groups.items():
            train_ids = [e for e in ids if e not in held_ids]
            old_fold = folds[group]
            resolved = expanded.resolve_candidate(candidate, events, train_ids)
            if (
                old_fold["status"] != "completed"
                or old_fold["held_out_events"] != held_ids
                or old_fold["training_events"] != train_ids
                or old_fold["resolved_positive_weight"]
                != resolved["parameters"]["scale_pos_weight"]
            ):
                raise ValueError("재현 fold의 기간그룹/양성 가중치 불일치")
            fitted, _, _ = expanded.fit(events, train_ids, features, candidate)
            for event_id in held_ids:
                data = events[event_id]
                p = fitted.inplace_predict(data["x"])
                assign_oof(predictions, coverage, event_id, np.arange(len(p)), p)
                actual = expanded.evaluate(data, p, probability=True)
                verify_replay_metrics(actual, old_fold["held_out"][event_id])
            replay[group] = {
                "training_events": train_ids,
                "held_out_events": held_ids,
                "resolved_positive_weight": resolved["parameters"]["scale_pos_weight"],
                "original_metrics_reproduced": True,
            }
            print(json.dumps({"oof_group": group, "status": "reproduced"}), flush=True)
        check_coverage(predictions, coverage)
        ordered_ids = list(events)
        p = np.concatenate([predictions[e] for e in ordered_ids])
        y = np.concatenate([events[e]["y"] for e in ordered_ids])
        np.savez_compressed(
            args.output / "training-oof.npz",
            raw_score=p,
            label=y,
            event_index=np.concatenate(
                [np.full(len(events[e]["y"]), i, dtype=np.int32) for i, e in enumerate(ordered_ids)]
            ),
            source_row_index=np.concatenate([np.arange(len(events[e]["y"])) for e in ordered_ids]),
            horizon_hours=np.concatenate([events[e]["h"] for e in ordered_ids]),
            event_ids=np.asarray(ordered_ids),
        )
        calibration = fit_sigmoid(p, y)
        calibration.update(
            {
                "oof_sha256": file_sha256(args.output / "training-oof.npz"),
                "oof_rows": len(y),
                "oof_positive_rows": int(y.sum()),
                "each_training_row_predicted_once": True,
                "clipped_oof_rows": int(((p < EPSILON) | (p > 1 - EPSILON)).sum()),
            }
        )
        if calibration["status"] == "fitted_research_only":
            calibration["monotonicity_probe_rows"] = monotonicity_probe(
                model, calibration, events, features
            )
            calibration["monotonicity_verified"] = True
    except (ValueError, RuntimeError, xgb.core.XGBoostError) as exc:
        calibration = {
            **calibration,
            "status": "withheld",
            "reason": "oof_replay_or_monotonicity_failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    calibration.update(
        {
            "created_at_utc": datetime.now(UTC).isoformat(),
            "plan_sha256": file_sha256(args.output / "plan.json"),
            "selected_candidate": candidate["name"],
            "replayed_folds": replay,
            "validation_event_data_read_before_receipt": False,
            "calibrated_score_research_only": True,
            "probability_calibrated": False,
            "operational_use": False,
        }
    )
    # This receipt is the fixed calibration choice before any validation event file is opened.
    expanded.common.write_json(args.output / "calibrator.json", calibration)
    if calibration["status"] == "withheld":
        result = {
            **calibration,
            "validation_read": False,
            "calibration_split_read": False,
            "test_evaluated": False,
            "validation_improvement": None,
        }
        expanded.common.write_json(args.output / "report.json", result)
        return result
    val = {
        e["id"]: expanded.load_event(args.dataset, e, features, "validation") for e in validation
    }
    if {e: d["sha256"] for e, d in val.items()} != source_report["validation_source_hashes"] or {
        e: d["report_sha256"] for e, d in val.items()
    } != source_report["validation_event_report_hashes"]:
        raise ValueError("보정 비교 validation 자료 SHA 불일치")
    results = {name: {} for name in ("raw", "sigmoid", "constant_training_prior")}
    precision_diagnostics = {}
    for event_id, data in val.items():
        raw = model.inplace_predict(data["x"]) if len(data["y"]) else np.array([])
        scores = {
            "raw": raw,
            "sigmoid": transform(raw, calibration),
            "constant_training_prior": expanded.prior_scores(data["h"], priors),
        }
        for name, score in scores.items():
            results[name][event_id] = expanded.evaluate(data, score, probability=True)
        precision_diagnostics[event_id] = {}
        for hours in expanded.HORIZONS:
            mask = data["h"] == hours
            values = raw[mask]
            precision_diagnostics[event_id][str(hours)] = {
                "rows": len(values),
                "clipped_raw_rows": int(((values < EPSILON) | (values > 1 - EPSILON)).sum()),
                "unique_raw_scores": len(np.unique(values)),
                "unique_sigmoid_scores": len(np.unique(scores["sigmoid"][mask])),
            }
    changes = improvements(results)
    ap_changes = [
        abs(v["average_precision_change"])
        for event in changes.values()
        for v in event.values()
        if v["average_precision_change"] is not None
    ]
    result = {
        "profile": cfg["profile"],
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "plan_sha256": file_sha256(args.output / "plan.json"),
        "calibrator_sha256": file_sha256(args.output / "calibrator.json"),
        "calibration_fitted": True,
        "status": "evaluated_research_only",
        "calibrated_score_research_only": True,
        "probability_calibrated": False,
        "validation": results,
        "validation_improvement": changes,
        "maximum_absolute_validation_ap_change": max(ap_changes) if ap_changes else None,
        "rank_ap_unchanged_within_1e_10": (
            bool(all(v <= 1e-10 for v in ap_changes)) if ap_changes else None
        ),
        "validation_inventory": expanded.inventory(val),
        "validation_score_precision": precision_diagnostics,
        "validation_source_hashes": {e: d["sha256"] for e, d in val.items()},
        "training_horizon_priors": priors,
        "each_training_row_predicted_once": True,
        "oof_sha256": calibration["oof_sha256"],
        "oof_rows": calibration["oof_rows"],
        "calibration_split_read": False,
        "test_evaluated": False,
        "operational_use": False,
        "elapsed_seconds": round(perf_counter() - started, 3),
        "limitations": [
            "Training OOF rows fit the calibrator; their fit is not independent "
            "calibration evaluation.",
            "The candidate was selected using the same grouped CV, creating selection reuse bias.",
            "2023 validation has prior exploratory exposure and is not an independent final test.",
            "The global sigmoid targets an unweighted censored row mixture, not event-balanced "
            "or operational prevalence.",
            "OOF scores come from smaller fold models, possibly with different class weights; "
            "transfer to the final full-train model is an unverified assumption.",
            "Positive sigmoid slope preserves ordering/period monotonicity mathematically; "
            "fixed logit clipping and floating point ties may change AP numerically.",
            "Positive metric reductions mean improvement on these same exposed validation rows; "
            "no deploy decision or response threshold is selected.",
            *cfg.get("limitations", []),
        ],
    }
    expanded.common.write_json(args.output / "report.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("run", "dataset", "config", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    result = experiment(parser.parse_args())
    print(
        json.dumps(
            {"status": result["status"], "calibration_fitted": result["calibration_fitted"]}
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
