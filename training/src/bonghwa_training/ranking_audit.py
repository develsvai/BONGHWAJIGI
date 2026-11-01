"""고정 모델의 validation 후보 검토 순위 진단. 경보·대응 임계값을 정하지 않는다."""

import argparse
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

from bonghwa_training.download import file_sha256

BUDGET_PERCENTAGES = (1, 5, 10, 20)
HORIZONS = (1, 3, 6)
HOLDOUT_START = datetime(2025, 1, 1, tzinfo=UTC).timestamp()


def _ratio(numerator, denominator):
    return float(numerator / denominator) if denominator else None


def _ranking_scores(scores):
    """결측 순위는 최하위로 두고 동점은 좌표로만 해소한다."""
    scores = np.asarray(scores, dtype=float)
    if np.isinf(scores).any():
        raise ValueError("무한 순위 점수는 허용하지 않습니다.")
    return np.where(np.isnan(scores), -np.inf, scores)


def select_candidates(scores, rows, cols, percent):
    """한 시점·한 예측 기간의 위치별 순위. 정답을 인수로 받지 않는다."""
    scores, rows, cols = np.asarray(scores), np.asarray(rows), np.asarray(cols)
    if not (scores.ndim == rows.ndim == cols.ndim == 1):
        raise ValueError("후보 자료는 1차원이어야 합니다.")
    if not (len(scores) == len(rows) == len(cols)) or not 0 < percent <= 100:
        raise ValueError("후보 길이 또는 검토 비율이 잘못됐습니다.")
    if not np.isfinite(rows).all() or not np.isfinite(cols).all():
        raise ValueError("후보 좌표가 유효하지 않습니다.")
    if len(np.unique(np.column_stack((rows, cols)), axis=0)) != len(rows):
        raise ValueError("동일 시점·기간에 중복 후보 좌표가 있습니다.")
    order = np.lexsort((cols, rows, -_ranking_scores(scores)))
    size = math.ceil(len(scores) * percent / 100)
    return order[:size], order


def workload_metrics(y, scores, issues, rows, cols, percent):
    """시점마다 같은 비율을 검토한 뒤 횟수를 합산한다. 미래 시점끼리 순위화하지 않는다."""
    y, scores, issues, rows, cols = map(np.asarray, (y, scores, issues, rows, cols))
    if not all(v.ndim == 1 and len(v) == len(y) for v in (y, scores, issues, rows, cols)):
        raise ValueError("후보 배열의 길이/차원이 일치하지 않습니다.")
    if not np.isin(y, [0, 1]).all() or not np.isfinite(issues).all():
        raise ValueError("이진 정답 또는 시점이 유효하지 않습니다.")
    totals = {
        "requested_percent_per_issue": percent,
        "issues": 0,
        "eligible_candidates": len(y),
        "examined_candidates": 0,
        "true_positives": 0,
        "total_positives": int(y.sum()),
        "random_budget_expected_true_positives": 0.0,
        "issues_with_score_ties": 0,
        "issues_with_boundary_ties": 0,
        "boundary_tie_candidates": 0,
        "missing_score_candidates": int(np.isnan(scores).sum()),
        "examined_missing_score_candidates": 0,
    }
    for issue in np.unique(issues):
        indices = np.flatnonzero(issues == issue)
        chosen, order = select_candidates(scores[indices], rows[indices], cols[indices], percent)
        ranked = _ranking_scores(scores[indices])[order]
        size, population = len(chosen), len(indices)
        totals["issues"] += 1
        totals["examined_candidates"] += size
        totals["true_positives"] += int(y[indices[chosen]].sum())
        totals["random_budget_expected_true_positives"] += size * float(y[indices].mean())
        totals["examined_missing_score_candidates"] += int(np.isnan(scores[indices[chosen]]).sum())
        totals["issues_with_score_ties"] += int(len(np.unique(ranked)) < population)
        if size < population and ranked[size - 1] == ranked[size]:
            totals["issues_with_boundary_ties"] += 1
            totals["boundary_tie_candidates"] += int((ranked == ranked[size - 1]).sum())
    totals.update(
        actual_examined_fraction=_ratio(totals["examined_candidates"], len(y)),
        precision=_ratio(totals["true_positives"], totals["examined_candidates"]),
        recall=_ratio(totals["true_positives"], totals["total_positives"]),
        lift_over_random_budget=_ratio(
            totals["true_positives"], totals["random_budget_expected_true_positives"]
        ),
    )
    return totals


def standard_metrics(y, scores, *, probability=False):
    """경보 임계값 없이 계산한다. 거리 점수를 확률로 해석하지 않는다."""
    y, scores = np.asarray(y), np.asarray(scores, dtype=float)
    values = {
        "rows": len(y),
        "positives": int(y.sum()),
        "positive_fraction": _ratio(y.sum(), len(y)),
    }
    missing = np.isnan(scores)
    values["missing_score_candidates"] = int(missing.sum())
    # sklearn에는 유한 점수를 주되 결측은 모든 관측 점수보다 낮은 동일 순위로 둔다.
    ranked = _ranking_scores(scores)
    if missing.any():
        observed = ranked[~missing]
        ranked[missing] = (
            float(observed.min() - max(1, np.abs(observed).max())) if len(observed) else 0
        )
    both = len(np.unique(y)) == 2
    values["average_precision"] = float(average_precision_score(y, ranked)) if both else None
    values["roc_auc"] = float(roc_auc_score(y, ranked)) if both else None
    if probability:
        if missing.any() or np.any((scores < 0) | (scores > 1)):
            raise ValueError("모델 출력은 유한한 0~1 점수여야 합니다.")
        values["brier"] = float(brier_score_loss(y, scores)) if len(y) else None
        values["logloss"] = float(log_loss(y, scores, labels=[0, 1])) if len(y) else None
    return values


def _json(path):
    return json.loads(path.read_text())


def _safe_name(name):
    if not isinstance(name, str) or not name or name in (".", "..") or Path(name).name != name:
        raise ValueError("파일 식별자는 단일 이름이어야 합니다.")
    return name


def verify_inputs(run: Path, dataset: Path, config: Path):
    """공유 metadata만 확인한다. validation 이외의 Parquet/사건 보고서는 열지 않는다."""
    report, plan, cfg = _json(run / "report.json"), _json(run / "plan.json"), _json(config)
    if report["plan_sha256"] != file_sha256(run / "plan.json"):
        raise ValueError("보고서의 학습 계획 SHA 불일치")
    config_sha = file_sha256(config)
    if config_sha != file_sha256(dataset / "config.json") or config_sha != plan["config_sha256"]:
        raise ValueError("학습/자료/요청 config SHA 불일치")
    dataset_report = _json(dataset / "report.json")
    if dataset_report["config_sha256"] != config_sha:
        raise ValueError("자료 보고서의 config SHA 불일치")
    selected = _safe_name(report["selected"])
    experiment = report["experiments"][selected]
    cases = [case for case in plan["cases"] if case["name"] == selected]
    features = experiment["features"]
    if len(cases) != 1 or cases[0]["features"] != features:
        raise ValueError("선택 모델의 학습 계획 feature 불일치")
    if not features or len(set(features)) != len(features) or "horizon_hours" not in features:
        raise ValueError("선택 모델 feature 목록이 유효하지 않습니다.")
    declared = cfg.get("feature_names", dataset_report["features"])
    expected = [name for name in declared if name not in cfg.get("drop_features", [])]
    if plan["features"] != expected or any(f not in expected for f in features):
        raise ValueError("config/학습 feature 불일치")
    if report["profile"] != cfg["profile"]:
        raise ValueError("자료/모델 profile 불일치")
    model_path = run / f"{selected}.ubj"
    if file_sha256(model_path) != experiment["model_sha256"]:
        raise ValueError("선택 모델 SHA 불일치")
    events = [event for event in cfg["events"] if event["split"] == "validation"]
    if not events or len({e["id"] for e in events}) != len(events):
        raise ValueError("validation 사건 목록이 없거나 중복됐습니다.")
    for event in events:
        _safe_name(event["id"])
        start = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00"))
        if start.tzinfo is None or start.timestamp() >= HOLDOUT_START or event.get("locked"):
            raise ValueError("잠긴 사건 또는 2025년 이후 자료는 평가할 수 없습니다.")
    return report, plan, cfg, experiment, model_path, events


def audit(run: Path, dataset: Path, config: Path, output: Path):
    import xgboost as xgb

    if output.exists():
        raise FileExistsError("기존 순위 진단은 덮어쓸 수 없습니다.")
    report, plan, cfg, experiment, model_path, events = verify_inputs(run, dataset, config)
    model = xgb.Booster()
    model.load_model(model_path)
    model.set_param({"device": "cpu", "nthread": 4})
    features = experiment["features"]
    if model.feature_names != features:
        raise ValueError("저장 모델의 feature 이름/순서 불일치")
    results, sources = {}, {}
    for event in events:
        event_id = event["id"]
        path = dataset / f"{event_id}.parquet"
        event_report = _json(dataset / f"{event_id}-report.json")
        digest = file_sha256(path)
        if digest != plan["source_hashes"][event_id] or digest != event_report["sha256"]:
            raise ValueError("validation Parquet SHA 불일치")
        if event_report["event"] != event:
            raise ValueError("validation 사건 계약 불일치")
        schema = pq.read_schema(path)
        columns = list(
            dict.fromkeys(
                [
                    *features,
                    "distance_fire_km",
                    "fire_within_horizon",
                    "issue_epoch_seconds",
                    "max_input_available_epoch_seconds",
                    "row",
                    "col",
                    *(
                        ["distance_recent_fire_60m_km"]
                        if "distance_recent_fire_60m_km" in schema.names
                        else []
                    ),
                ]
            )
        )
        table = pq.read_table(path, columns=columns)
        values = {name: table[name].to_numpy() for name in columns}
        y, issues = values["fire_within_horizon"], values["issue_epoch_seconds"]
        if len(y) != event_report["rows"] or not np.isin(y, [0, 1]).all():
            raise ValueError("validation 행 수 또는 이진 정답이 유효하지 않습니다.")
        if not np.isfinite(issues).all() or np.any(issues >= HOLDOUT_START):
            raise ValueError("validation 시점은 유한한 2025년 이전 UTC 시각이어야 합니다.")
        available = values["max_input_available_epoch_seconds"]
        if not np.isfinite(available).all() or np.any(available > issues):
            raise ValueError("입력 가용 시각의 미래 누출")
        horizons = values["horizon_hours"]
        if not np.isin(horizons, HORIZONS).all():
            raise ValueError("예측 기간은 1·3·6시간이어야 합니다.")
        if np.any(issues + horizons * 3600 >= HOLDOUT_START):
            raise ValueError("2025년 이후 정답에 걸치는 validation 예측 기간입니다.")
        x = np.column_stack([values[name] for name in features])
        scores = {
            "model": model.inplace_predict(x) if len(y) else np.array([]),
            "negative_current_fire_distance": -values["distance_fire_km"],
        }
        if "distance_recent_fire_60m_km" in values:
            scores["negative_recent_fire_distance"] = -values["distance_recent_fire_60m_km"]
        results[event_id] = {}
        sources[event_id] = digest
        for horizon in HORIZONS:
            mask = horizons == horizon
            results[event_id][str(horizon)] = {
                name: {
                    "standard_metrics": standard_metrics(
                        y[mask], score[mask], probability=name == "model"
                    ),
                    "review_budgets": [
                        workload_metrics(
                            y[mask],
                            score[mask],
                            issues[mask],
                            values["row"][mask],
                            values["col"][mask],
                            percent,
                        )
                        for percent in BUDGET_PERCENTAGES
                    ],
                }
                for name, score in scores.items()
            }
    result = {
        "profile": cfg["profile"],
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "selected": report["selected"],
        "model_sha256": file_sha256(model_path),
        "run_report_sha256": file_sha256(run / "report.json"),
        "plan_sha256": file_sha256(run / "plan.json"),
        "config_sha256": file_sha256(config),
        "diagnostic_source_sha256": file_sha256(Path(__file__)),
        "validation_parquet_sha256": sources,
        "selection_rule": (
            "Within each event, issue UTC timestamp and horizon: ceil(N*percent/100); "
            "descending score, then ascending row, col. Missing baseline score ranks last."
        ),
        "budget_percentages": list(BUDGET_PERCENTAGES),
        "events": results,
        "operational_use": False,
        "test_evaluated": False,
        "limitations": [
            "Retrospective, censored eligible cohort: future cloud/missing observations exclude "
            "unknown targets. Candidate denominator differs by horizon and is not the complete "
            "live population.",
            "Repeated cells and issue times are not independent incidents, people or alerts. "
            "Counts represent research review workload, without temporal deduplication.",
            "Validation selected this model and has been inspected; this is not an independent "
            "test or an unbiased generalization estimate.",
            "Ranking is a research review diagnostic, not calibrated personal harm probability, "
            "response level, evacuation decision or alert threshold.",
            "Requested review percentages are descriptive fixed budgets, not optimized "
            "recommendations. Ceil rounding can exceed requested fractions in small cohorts.",
            "Negative distance baselines are ranking scores, not probabilities. Missing scores "
            "rank last with deterministic coordinate tie breaking; ties may influence measured "
            "utility.",
            "Random-budget expected positives use each issue's eligible prevalence and actual "
            "examined count; lift is not causal benefit or incident-level detection improvement.",
            *report.get("limitations", []),
        ],
    }
    with output.open("x") as destination:
        destination.write(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(
        json.dumps(
            {"output": str(output), "validation_events": list(results), "operational_use": False}
        )
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("run", "dataset", "config", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    audit(args.run, args.dataset, args.config, args.output)


if __name__ == "__main__":
    main()
