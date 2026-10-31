"""고정 v4 거리 단조 제약 실험. 학습 기간그룹 CV로만 기존 모델과 세 후보를 비교한다."""

import argparse
import copy
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import xgboost as xgb

from bonghwa_training import expanded_generalization_experiment as expanded
from bonghwa_training import expanded_oof_calibration as frozen
from bonghwa_training.download import file_sha256

REFERENCE = "depth4_positive_sqrt"
DISTANCES = frozenset(("distance_fire_km", "distance_recent_fire_60m_km",
                       "distance_fire_30m_km", "distance_fire_60m_km"))
CLOCK = frozenset(("utc_hour_sin", "utc_hour_cos"))


def make_candidates(reference, features, context_features):
    if (reference["name"] != REFERENCE or reference["features"] != features
        or len(features) != 34 or len(set(features)) != 34
        or len(set(context_features)) != 13 or not set(context_features).issubset(features)
        or not (DISTANCES | CLOCK | {"horizon_hours"}).issubset(features)):
        raise ValueError("고정 context34/거리/기준 후보 계약 불일치")
    definitions = [
        ("distance_monotone_all", features, 4, "training_fold_sqrt"),
        ("distance_monotone_observations",
         [f for f in features if f not in set(context_features) | CLOCK], 4, "training_fold_sqrt"),
        ("distance_only_depth3", ["distance_fire_km", "distance_recent_fire_60m_km",
                                  "horizon_hours"], 3, "unit"),
    ]
    cases = [copy.deepcopy(reference)]
    for name, columns, depth, weight_rule in definitions:
        candidate = copy.deepcopy(reference)
        candidate.update(name=name, features=list(columns), positive_weight_rule=weight_rule,
                         monotone_constraints=[1 if f == "horizon_hours" else
                                               -1 if f in DISTANCES else 0 for f in columns])
        candidate["parameters"].update(max_depth=depth, scale_pos_weight=1.0)
        cases.append(candidate)
    return cases


def select_candidate(candidates, cv):
    if any(cv[c["name"]]["status"] != "completed" for c in candidates):
        raise ValueError("실패한 후보가 있으면 선택할 수 없습니다.")
    scores = [cv[c["name"]]["mean_event_horizon_ap"] for c in candidates]
    if any(v is None or not np.isfinite(v) for v in scores):
        raise ValueError("유한한 공통 CV AP가 필요합니다.")
    # Reference is deliberately first: exactly tied CV evidence does not replace it.
    return candidates[int(np.argmax(scores))]


def verify_reference(events, ids, groups, cells, source_plan, source_report, candidate, features):
    if ({e: d["sha256"] for e, d in events.items()} != source_plan["source_hashes"] or
        {e: d["report_sha256"] for e, d in events.items()} != source_plan["event_report_hashes"] or
        groups != source_plan["period_groups"] or
        [{"event": e, "horizon_hours": h} for e, h in cells] != source_plan["eligible_cv_cells"]):
        raise ValueError("기준 CV 학습 원본/기간그룹/평가 셀 불일치")
    resolved = expanded.resolve_candidate(candidate, events, ids)
    if resolved != source_report["models"][REFERENCE]["candidate"]:
        raise ValueError("기준 최종 모델의 학습 매개변수 불일치")
    original = source_report["cv"][REFERENCE]
    if set(original["folds"]) != set(groups):
        raise ValueError("기준 CV fold 목록 불일치")
    diagnostics = {}
    for group, held_ids in groups.items():
        train_ids = [e for e in ids if e not in held_ids]
        fold = original["folds"][group]
        weight = expanded.resolve_candidate(candidate, events, train_ids)["parameters"][
            "scale_pos_weight"]
        if (fold["status"] != "completed" or fold["held_out_events"] != held_ids
            or fold["training_events"] != train_ids or fold["resolved_positive_weight"] != weight
            or set(fold["held_out"]) != set(held_ids)):
            raise ValueError("기준 CV fold의 학습/제외 사건 또는 가중치 불일치")
        for event_id in held_ids:
            d = events[event_id]
            for h in expanded.HORIZONS:
                metric = fold["held_out"][event_id][str(h)]
                y = d["y"][d["h"] == h]
                if metric["rows"] != len(y) or metric["positives"] != int(y.sum()):
                    raise ValueError("기준 CV 지표의 대상 행/양성 수 불일치")
            diagnostics[event_id] = fold["held_out"][event_id]
    score = expanded.mean_ap(diagnostics, cells)
    if not np.isclose(score, original["mean_event_horizon_ap"], rtol=0, atol=1e-12):
        raise ValueError("기준 CV 공통 셀 AP 집계 불일치")
    return {**original, "reused_frozen_cv": True}


def predict(model, data, features, candidate):
    if not len(data["y"]):
        return np.array([])
    return expanded.common.prediction(model, data, features, candidate["features"])


def save_selected(model, path, events, features, candidate):
    model.save_model(path)
    restored = xgb.Booster()
    restored.load_model(path)
    restored.set_param({"device": "cpu", "nthread": 2})
    columns = candidate["features"]
    if restored.feature_names != columns or restored.num_boosted_rounds() != expanded.ROUNDS:
        raise ValueError("선택 모델의 부분 feature 순서/반복 횟수 불일치")
    indices = [features.index(f) for f in columns]
    difference, probe_rows = 0.0, 0
    for data in events.values():
        if not len(data["y"]):
            continue
        x = np.ascontiguousarray(data["x"][:, indices])
        before, after = model.inplace_predict(x), restored.inplace_predict(x)
        np.testing.assert_allclose(before, after, rtol=1e-6, atol=1e-7)
        difference = max(difference, float(np.max(np.abs(before - after))))
        probe = x[:8192].copy()
        by_horizon = []
        for hours in expanded.HORIZONS:
            probe[:, columns.index("horizon_hours")] = hours
            by_horizon.append(restored.inplace_predict(probe))
        if np.any(np.diff(by_horizon, axis=0) < -1e-6):
            raise ValueError("선택 모델의 기간 단조성 위반")
        # Only prescribed negative distance constraints are probed, holding other inputs fixed.
        for column, constraint in zip(columns, candidate["monotone_constraints"], strict=True):
            if constraint != -1:
                continue
            varying = x[:8192].copy()
            index = columns.index(column)
            valid = np.isfinite(varying[:, index])
            varying = varying[valid]
            if not len(varying):
                continue
            near = restored.inplace_predict(varying)
            varying[:, index] += 1.0
            if np.any(restored.inplace_predict(varying) - near > 1e-6):
                raise ValueError("선택 모델의 거리 단조성 위반")
        probe_rows += len(probe)
    return restored, {
        "model_sha256": file_sha256(path), "candidate": candidate,
        "saved_trees": restored.num_boosted_rounds(),
        "cpu_reload_max_abs_difference": difference,
        "monotonicity_probe_rows": probe_rows, "horizon_monotonicity_verified": True,
        "prescribed_distance_monotonicity_verified": True,
    }


def pooled_workload(diagnostics):
    def combine(cells):
        counts = {name: sum(c[name] for c in cells) for name in (
            "eligible_candidates", "examined_candidates", "true_positives", "total_positives",
            "random_budget_expected_true_positives", "issues_with_boundary_ties"
        )}
        counts.update(
            precision=expanded.ranking_audit._ratio(counts["true_positives"],
                                                   counts["examined_candidates"]),
            recall=expanded.ranking_audit._ratio(counts["true_positives"], counts["total_positives"]),
            lift_over_random_budget=expanded.ranking_audit._ratio(
                counts["true_positives"], counts["random_budget_expected_true_positives"]),
        )
        return counts

    return {
        "per_horizon": {str(h): combine([d[str(h)]["top_10_percent_per_issue"]
                                         for d in diagnostics.values()])
                        for h in expanded.HORIZONS},
        "all_horizons_repeated_decisions": combine([
            d[str(h)]["top_10_percent_per_issue"] for d in diagnostics.values()
            for h in expanded.HORIZONS]),
        "interpretation": "budgets selected separately per event/issue/horizon before summing; "
                          "repeated decisions are not independent cells, incidents or alerts",
    }


def experiment(args):
    started = perf_counter()
    cfg, source_report, source_plan, _, reference, features, old_model, training, validation = (
        frozen.verify(args)
    )
    if cfg["profile"] != expanded.CONTEXT_PROFILE:
        raise ValueError("고정 v4 context 자료에만 허용합니다.")
    candidates = make_candidates(reference, features, cfg.get("context_features", []))
    events = {e["id"]: expanded.load_event(args.dataset, e, features, "train") for e in training}
    ids = [e for e, d in events.items() if len(d["y"])]
    groups = {g: [e for e in ids if expanded.period_group(events[e]["event"]) == g]
              for g in sorted({expanded.period_group(events[e]["event"]) for e in ids})}
    cells = expanded.eligible_cells(events)
    if not cells or len(groups) < 2:
        raise ValueError("평가 가능한 기간그룹/공통 AP 셀이 부족합니다.")
    cv = {REFERENCE: verify_reference(events, ids, groups, cells, source_plan, source_report,
                                      reference, features)}
    priors = expanded.training_horizon_priors(events, ids)
    if priors != source_plan["training_horizon_priors"] or priors != source_report[
        "training_horizon_priors"]:
        raise ValueError("기준 연구의 학습 prior 불일치")
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {
        "created_at_utc": datetime.now(UTC).isoformat(), "profile": cfg["profile"],
        "config_sha256": file_sha256(args.config), "source_run": str(args.run),
        "source_plan_sha256": file_sha256(args.run / "plan.json"),
        "source_selection_sha256": file_sha256(args.run / "selection.json"),
        "source_report_sha256": file_sha256(args.run / "report.json"),
        "reference_model_sha256": source_report["models"][REFERENCE]["model_sha256"],
        "code_sha256": {Path(__file__).name: file_sha256(Path(__file__)),
                        Path(frozen.__file__).name: file_sha256(Path(frozen.__file__)),
                        **source_plan["code_sha256"]},
        "xgboost_version": xgb.__version__, "features": features, "candidates": candidates,
        "training_source_hashes": source_plan["source_hashes"],
        "training_event_report_hashes": source_plan["event_report_hashes"],
        "training_inventory": expanded.inventory(events), "period_groups": groups,
        "eligible_cv_cells": [{"event": e, "horizon_hours": h} for e, h in cells],
        "selection": "mean AP on identical eligible event-horizon cells; reference wins ties",
        "failure_rule": "persist all candidate folds; any failure prevents selection",
        "reference_cv_reused_without_refit": True, "maximum_new_fit_count": 3 * len(groups) + 1,
        "rounds_per_fit": expanded.ROUNDS, "early_stopping": False,
        "validation_tuning": False, "calibration_split_read": False, "test_evaluated": False,
        "operational_use": False,
    }
    expanded.common.write_json(args.output / "plan.json", plan)
    expanded.common.write_json(args.output / f"{REFERENCE}-cv.json", cv[REFERENCE])
    training_baselines = expanded.distance_diagnostics(events, features)
    for candidate in candidates[1:]:
        folds, diagnostics = {}, {}
        for group, held_ids in groups.items():
            train_ids = [e for e in ids if e not in held_ids]
            try:
                model, shares, resolved = expanded.fit(events, train_ids, features, candidate)
                held = {e: expanded.evaluate(events[e], predict(model, events[e], features, candidate),
                                             probability=True) for e in held_ids}
                diagnostics.update(held)
                folds[group] = {
                    "status": "completed", "training_events": train_ids,
                    "held_out_events": held_ids, "training_event_shares": shares,
                    "resolved_positive_weight": resolved["parameters"]["scale_pos_weight"],
                    "held_out": held,
                }
            except (ValueError, RuntimeError, xgb.core.XGBoostError) as exc:
                folds[group] = {"status": "failed", "training_events": train_ids,
                                "held_out_events": held_ids, "error_type": type(exc).__name__,
                                "reason": str(exc)}
        failed = any(f["status"] != "completed" for f in folds.values())
        cv[candidate["name"]] = {"status": "failed" if failed else "completed", "folds": folds,
                                 "mean_event_horizon_ap": None if failed else
                                 expanded.mean_ap(diagnostics, cells)}
        expanded.common.write_json(args.output / f"{candidate['name']}-cv.json", cv[candidate["name"]])
        print(json.dumps({"candidate": candidate["name"],
                          "cv_ap": cv[candidate["name"]]["mean_event_horizon_ap"]}), flush=True)
    if any(c["status"] != "completed" for c in cv.values()):
        expanded.common.write_json(args.output / "failure.json", {
            "status": "cv_failed_no_selection", "cv": cv, "validation_read": False,
            "operational_use": False,
        })
        raise RuntimeError("실패한 후보가 있어 선택과 validation 평가를 중단합니다.")
    selected = select_candidate(candidates, cv)
    expanded.common.write_json(args.output / "selection.json", {
        "selected": selected["name"], "selected_at_utc": datetime.now(UTC).isoformat(),
        "plan_sha256": file_sha256(args.output / "plan.json"),
        "cv_result_sha256": {c["name"]: file_sha256(args.output / f"{c['name']}-cv.json")
                             for c in candidates},
        "validation_event_data_read_before_selection": False,
    })
    if selected["name"] == REFERENCE:
        model = old_model
        model_report = {**source_report["models"][REFERENCE], "reused_without_refit": True}
    else:
        model, shares, resolved = expanded.fit(events, ids, features, selected)
        model, model_report = save_selected(model, args.output / f"{selected['name']}.ubj",
                                            events, features, resolved)
        model_report.update(training_event_shares=shares, reused_without_refit=False)
    val = {e["id"]: expanded.load_event(args.dataset, e, features, "validation") for e in validation}
    if ({e: d["sha256"] for e, d in val.items()} != source_report["validation_source_hashes"] or
        {e: d["report_sha256"] for e, d in val.items()}
        != source_report["validation_event_report_hashes"]):
        raise ValueError("기존 연구와 비교 validation 원본 SHA가 다릅니다.")
    results = expanded.distance_diagnostics(val, features)
    results["constant_training_prior"] = {
        e: expanded.evaluate(d, expanded.prior_scores(d["h"], priors), probability=True)
        for e, d in val.items()
    }
    results[REFERENCE] = source_report["validation"][REFERENCE]
    if set(results[REFERENCE]) != set(val):
        raise ValueError("기존 기준 모델 validation 사건 목록 불일치")
    for e, d in val.items():
        for h in expanded.HORIZONS:
            old = results[REFERENCE][e][str(h)]
            mask = d["h"] == h
            if old["rows"] != int(mask.sum()) or old["positives"] != int(d["y"][mask].sum()):
                raise ValueError("기존 기준 모델의 validation 지표 대상 행 불일치")
    results[selected["name"]] = {
        e: expanded.evaluate(d, predict(model, d, features, selected), probability=True)
        for e, d in val.items()
    }
    validation_cells = expanded.eligible_cells(val)
    result = {
        "profile": cfg["profile"], "completed_at_utc": datetime.now(UTC).isoformat(),
        "plan_sha256": file_sha256(args.output / "plan.json"),
        "selection_sha256": file_sha256(args.output / "selection.json"),
        "selected": selected["name"], "reference": REFERENCE, "selected_model": model_report,
        "cv": cv, "cv_distance_baselines": training_baselines,
        "cv_baseline_mean_event_horizon_ap": {
            name: expanded.mean_ap(value, cells) for name, value in training_baselines.items()},
        "validation": results, "validation_inventory": expanded.inventory(val),
        "validation_source_hashes": {e: d["sha256"] for e, d in val.items()},
        "validation_eligible_cells": [{"event": e, "horizon_hours": h} for e, h in validation_cells],
        "validation_mean_event_horizon_ap": {
            name: expanded.mean_ap(value, validation_cells) for name, value in results.items()},
        "validation_top_10_percent": {name: pooled_workload(value)
                                      for name, value in results.items()},
        "training_horizon_priors": priors, "probability_calibrated": False,
        "calibration_split_read": False, "test_evaluated": False, "operational_use": False,
        "elapsed_seconds": round(perf_counter() - started, 3),
        "limitations": [
            "These distance hypotheses were designed after previous 2023 validation diagnostics; "
            "this remains an exploratory, previously exposed validation comparison.",
            "Candidate selection uses training period-group CV only; winning CV AP is optimistic.",
            "The reference CV is reused from the same frozen rows/groups, not refit or retuned.",
            "Only the selected candidate is newly evaluated on validation; losing candidates "
            "are not evaluated there. Reference validation metrics are frozen source results.",
            "Decreasing distance constraints are modeling assumptions holding other features "
            "fixed, not proof of fire propagation physics.",
            "Pooled top10% counts repeat event/issue/horizon decisions, not independent alerts.",
            "No calibration, response threshold, deployment or locked-2025 evaluation occurs.",
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
    print(json.dumps({"selected": result["selected"],
                      "validation_ap": result["validation_mean_event_horizon_ap"]}), flush=True)


if __name__ == "__main__":
    main()
