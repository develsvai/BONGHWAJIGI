"""GOFER 재구성 경계 접근시간의 고정 AFT 비교. 개인 위험/국내 운영 확률이 아니다."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import xgboost as xgb
from scipy.special import ndtr
from sklearn.metrics import average_precision_score, log_loss

from bonghwa_training.download import file_sha256

FEATURES = (
    "distance_km",
    "prior_distance_km",
    "closing_speed_kmh",
    "history_elapsed_hours",
    "elapsed_event_hours",
    "perimeter_area_km2",
    "perimeter_growth_km2_per_h",
)
HORIZONS = (1, 3, 6)
SIGMA = 1.0
ROUNDS = 100


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def known_labels(lower, upper, horizon):
    """접근 구간 (lower, upper]가 기간을 걸치면 정답 미상으로 남긴다."""
    lower, upper = np.asarray(lower), np.asarray(upper)
    positive = np.isfinite(upper) & (upper <= horizon)
    negative = lower >= horizon
    if np.any(positive & negative):
        raise ValueError("퇴화/충돌 구간 정답")
    return positive | negative, positive.astype(np.int8)


def validate_intervals(lower, upper):
    lower, upper = np.asarray(lower), np.asarray(upper)
    if (
        lower.ndim != 1
        or lower.shape != upper.shape
        or not np.isfinite(lower).all()
        or np.isnan(upper).any()
        or np.any(lower < 0)
        or np.any(upper <= lower)
        or np.any(np.isinf(upper) & (lower <= 0))
    ):
        raise ValueError("현재 미접근 위치의 양수 접근시간 구간 계약 위반")


def cdf(margins, horizons=HORIZONS, sigma=SIGMA):
    if sigma <= 0 or not np.isfinite(sigma):
        raise ValueError("양수 유한 AFT scale 필요")
    margins = np.asarray(margins, dtype=float)
    horizons = np.asarray(horizons, dtype=float)
    if not np.isfinite(margins).all() or np.any(horizons <= 0):
        raise ValueError("AFT margin 또는 horizon 오류")
    return ndtr((np.log(horizons)[None, :] - margins[:, None]) / sigma)


def constant_speed_arrival(distance, speed, radius_km):
    """현재 화선까지 거리가 아닌 연구 접근 반경까지 남은 거리로 시간을 계산한다."""
    remaining = np.maximum(np.asarray(distance) - radius_km, 0)
    speed = np.asarray(speed)
    return np.divide(remaining, speed, out=np.full(speed.shape, np.inf), where=speed > 0)


def load_events(dataset, config, split):
    if split not in ("train", "validation"):
        raise ValueError("이번 pilot은 train/validation만 허용")
    events = {}
    for event in config["events"]:
        if event.get("locked") or event.get("split") != split:
            continue  # test 경로는 열지 않는다.
        name = event["id"]
        if not name or Path(name).name != name or name in events:
            raise ValueError("사건 ID 중복 또는 경로 오류")
        date = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00"))
        if date.year not in (2019, 2020, 2021):
            raise ValueError("GOFER pilot의 2019~2021 경계 밖")
        expected_split = "validation" if date.year == 2021 else "train"
        if split != expected_split:
            raise ValueError("고정 연도별 train/validation 분할 위반")
        path = dataset / f"{name}.parquet"
        report = json.loads((dataset / f"{name}-report.json").read_text())
        if report["sha256"] != file_sha256(path):
            raise ValueError("자료 SHA 불일치")
        table = pq.read_table(path)
        n = len(table)
        if n != report["rows"]:
            raise ValueError("자료 행 수 불일치")
        if not n:
            continue
        for column, expected in (("event_id", name), ("split", split)):
            if set(table[column].to_pylist()) != {expected}:
                raise ValueError("사건/분할 metadata 불일치")
        if any(table["current_approach"].to_pylist()):
            raise ValueError("이미 접근한 위치는 미래 모델에서 분리해야 함")
        lower = table["label_lower_hours"].to_numpy().astype(float)
        upper = table["label_upper_hours"].to_numpy().astype(float)
        validate_intervals(lower, upper)
        x = np.column_stack([table[f].to_numpy() for f in FEATURES]).astype(float)
        if np.isinf(x).any() or not np.isfinite(x[:, 0]).all() or np.any(x[:, 0] <= 0):
            raise ValueError("입력 무한대/현재 거리 오류")
        identities = list(
            zip(table["issue_time_utc"].to_pylist(), table["target_id"].to_pylist(), strict=True)
        )
        if len(set(identities)) != n:
            raise ValueError("동일 사건·시점·위치 중복")
        events[name] = {
            "x": x,
            "lower": lower,
            "upper": upper,
            "table": table,
            "event": event,
            "sha256": report["sha256"],
        }
    if not events:
        raise ValueError(f"{split} 유효 사건 없음")
    return events


def candidates():
    shared = {
        "objective": "survival:aft",
        "eval_metric": "aft-nloglik",
        "aft_loss_distribution": "normal",
        "aft_loss_distribution_scale": SIGMA,
        "tree_method": "hist",
        "device": "cpu",
        "nthread": 2,
        "seed": 47,
        "max_depth": 3,
        "eta": 0.05,
        "min_child_weight": 5,
        "lambda": 20,
        "subsample": 1.0,
        "colsample_bytree": 1.0,
    }
    return [
        {"name": "aft_distance", "features": [FEATURES[0]], "parameters": shared.copy()},
        {"name": "aft_history", "features": list(FEATURES), "parameters": shared.copy()},
    ]


def matrix(events, feature_names, *, with_labels=True):
    indices = [FEATURES.index(f) for f in feature_names]
    dmatrix = xgb.DMatrix(
        np.concatenate([e["x"][:, indices] for e in events.values()]),
        feature_names=feature_names,
    )
    if with_labels:
        dmatrix.set_float_info(
            "label_lower_bound", np.concatenate([e["lower"] for e in events.values()])
        )
        dmatrix.set_float_info(
            "label_upper_bound", np.concatenate([e["upper"] for e in events.values()])
        )
    return dmatrix


def priors(events):
    lower = np.concatenate([e["lower"] for e in events.values()])
    upper = np.concatenate([e["upper"] for e in events.values()])
    result = {}
    for h in HORIZONS:
        known, y = known_labels(lower, upper, h)
        if not known.any():
            raise ValueError("학습 prior를 계산할 알려진 정답 없음")
        result[str(h)] = {"probability": float(y[known].mean()), "known_rows": int(known.sum())}
    return result


def scores(y, prediction, probability):
    if not len(y):
        return {
            "rows": 0,
            "positives": 0,
            "average_precision": None,
            "brier": None,
            "logloss": None,
        }
    if not np.isfinite(prediction).all():
        raise ValueError("평가 점수 미상")
    result = {
        "rows": len(y),
        "positives": int(y.sum()),
        "average_precision": float(average_precision_score(y, prediction))
        if len(np.unique(y)) == 2
        else None,
        "brier": None,
        "logloss": None,
    }
    if probability:
        if np.any((prediction < 0) | (prediction > 1)):
            raise ValueError("CDF 범위 오류")
        result["brier"] = float(np.mean((prediction - y) ** 2))
        result["logloss"] = float(log_loss(y, np.clip(prediction, 1e-7, 1 - 1e-7), labels=[0, 1]))
    return result


def evaluate(events, predictions, probability=True):
    per_event, pooled = {}, {}
    for name, event in events.items():
        per_event[name] = {}
        p = predictions[name]
        if p.shape != (len(event["lower"]), len(HORIZONS)):
            raise ValueError("예측 shape 불일치")
        for index, h in enumerate(HORIZONS):
            known, y = known_labels(event["lower"], event["upper"], h)
            result = scores(y[known], p[known, index], probability)
            result["unknown_rows"] = int((~known).sum())
            per_event[name][str(h)] = result
    for index, h in enumerate(HORIZONS):
        labels, values = [], []
        for name, event in events.items():
            known, y = known_labels(event["lower"], event["upper"], h)
            labels.append(y[known])
            values.append(predictions[name][known, index])
        pooled[str(h)] = scores(np.concatenate(labels), np.concatenate(values), probability)
    eligible_ap = [
        v["average_precision"]
        for e in per_event.values()
        for v in e.values()
        if v["average_precision"] is not None
    ]
    briers = [v["brier"] for e in per_event.values() for v in e.values() if v["brier"] is not None]
    return {
        "events": per_event,
        "pooled_horizons": pooled,
        "macro_eligible_event_horizon_ap": float(np.mean(eligible_ap)) if eligible_ap else None,
        "eligible_ap_cells": len(eligible_ap),
        "macro_nonempty_event_horizon_brier": float(np.mean(briers)) if briers else None,
        "evaluation_note": "Known labels only; interval/censoring selection may bias metrics",
    }


def run(dataset, output):
    started = perf_counter()
    dataset, output = Path(dataset), Path(output)
    config = json.loads((dataset / "config.json").read_text())
    if config.get("feature_names") != list(FEATURES):
        raise ValueError("고정 7개 피처 계약 불일치")
    radius_km = config["settings"]["radius_km"]
    if not np.isfinite(radius_km) or radius_km <= 0:
        raise ValueError("접근 반경은 양수 유한값이어야 함")
    # Metadata 분할은 실제 자료를 열기 전에 검사한다.
    groups = {}
    ids = set()
    for event in config["events"]:
        if event.get("locked") or event.get("split") not in ("train", "validation"):
            continue
        if event["id"] in ids:
            raise ValueError("중복 사건")
        ids.add(event["id"])
        group = event["period_group"]
        if groups.setdefault(group, event["split"]) != event["split"]:
            raise ValueError("연관 기간그룹이 train/validation에 중복")
    output.mkdir(parents=True, exist_ok=False)
    definitions = candidates()
    plan = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "dataset_config_sha256": file_sha256(dataset / "config.json"),
        "source_sha256": file_sha256(Path(__file__)),
        "target": "GOFER reconstructed-perimeter first approach, not personal harm",
        "radius_km": radius_km,
        "retrospective_proxy_only": True,
        "source_asof_verified": False,
        "personal_harm_probability": False,
        "dataset_source": config.get("source"),
        "dataset_settings": config["settings"],
        "horizons_hours": list(HORIZONS),
        "candidates": definitions,
        "rounds": ROUNDS,
        "selection": "None; two fixed models are compared without validation-based tuning",
        "probability_calibrated": False,
        "operational_use": False,
        "test_evaluated": False,
    }
    write_json(output / "plan.json", plan)
    training = load_events(dataset, config, "train")
    train_prior = priors(training)
    models, fit_reports = {}, {}
    for candidate in definitions:
        dtrain = matrix(training, candidate["features"])
        history = {}
        model = xgb.train(
            candidate["parameters"],
            dtrain,
            num_boost_round=ROUNDS,
            evals=[(dtrain, "train")],
            evals_result=history,
            verbose_eval=False,
        )
        path = output / f"{candidate['name']}.ubj"
        model.save_model(path)
        reloaded = xgb.Booster()
        reloaded.load_model(path)
        margins = model.predict(dtrain, output_margin=True)
        reload_margin = reloaded.predict(dtrain, output_margin=True)
        diff = float(np.max(np.abs(margins - reload_margin)))
        if diff > 1e-6 or not np.isfinite(margins).all():
            raise ValueError("AFT 저장/재로딩 검증 실패")
        models[candidate["name"]] = reloaded
        fit_reports[candidate["name"]] = {
            "model_sha256": file_sha256(path),
            "reload_margin_max_abs_difference": diff,
            "history": history,
            "saved_trees": reloaded.num_boosted_rounds(),
        }
    receipt = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "plan_sha256": file_sha256(output / "plan.json"),
        "training_hashes": {name: e["sha256"] for name, e in training.items()},
        "training_prior": train_prior,
        "models": fit_reports,
        "validation_data_read_before_receipt": False,
        "read_order_scope": "Trainer parquet reads only; builder label counts already available",
    }
    write_json(output / "fit-receipt.json", receipt)
    validation = load_events(dataset, config, "validation")
    results = {}
    prediction_table = []
    for candidate in definitions:
        predictions = {}
        for name, event in validation.items():
            margin = models[candidate["name"]].predict(
                matrix({name: event}, candidate["features"], with_labels=False), output_margin=True
            )
            prediction = cdf(margin)
            if np.any(np.diff(prediction, axis=1) < 0):
                raise ValueError("누적 접근 확률의 기간 단조성 오류")
            predictions[name] = prediction
            columns = {
                key: event["table"][key] for key in ("event_id", "issue_time_utc", "target_id")
            }
            columns["model"] = [candidate["name"]] * len(margin)
            for index, h in enumerate(HORIZONS):
                columns[f"model_cdf_{h}h"] = prediction[:, index]
            prediction_table.append(pa.table(columns))
        results[candidate["name"]] = evaluate(validation, predictions)
    baseline = {
        name: np.tile([train_prior[str(h)]["probability"] for h in HORIZONS], (len(e["lower"]), 1))
        for name, e in validation.items()
    }
    results["constant_training_known_prior"] = evaluate(validation, baseline)
    distance = {name: np.repeat(-e["x"][:, :1], 3, axis=1) for name, e in validation.items()}
    results["negative_current_distance"] = evaluate(validation, distance, probability=False)
    eta = {}
    for name, e in validation.items():
        speed = e["x"][:, FEATURES.index("closing_speed_kmh")]
        time = constant_speed_arrival(e["x"][:, 0], speed, radius_km)
        eta[name] = (time[:, None] <= np.asarray(HORIZONS)[None, :]).astype(float)
    results["constant_closing_speed_projection"] = evaluate(validation, eta)
    pq.write_table(pa.concat_tables(prediction_table), output / "validation-predictions.parquet")
    report = {
        **plan,
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "xgboost": xgb.__version__,
        "plan_sha256": file_sha256(output / "plan.json"),
        "fit_receipt_sha256": file_sha256(output / "fit-receipt.json"),
        "prediction_sha256": file_sha256(output / "validation-predictions.parquet"),
        "training_rows": sum(len(e["lower"]) for e in training.values()),
        "validation_rows": sum(len(e["lower"]) for e in validation.values()),
        "training_events": list(training),
        "validation_events": list(validation),
        "validation_hashes": {name: e["sha256"] for name, e in validation.items()},
        "models": fit_reports,
        "validation": results,
        "elapsed_seconds": round(perf_counter() - started, 3),
        "limitations": [
            "US reconstructed perimeters; not ground-truth arrival or Korea validation",
            "Past timestamps do not resolve GOFER retrospective processing or input availability",
            "No future weather or fuel inputs in this geometry-only pilot",
            "Fixed lognormal residual scale; no independent calibration validation",
            "AFT has no never-arrival component; do not extrapolate beyond studied 1-6h horizons",
            "Repeated locations/issues are dependent; event-level evidence remains limited",
            "Only known labels evaluated; unknown interval/censored rows reported separately",
            "Radius and grid are research definitions, not user safety thresholds",
        ],
    }
    write_json(output / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.dataset, args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "training_rows": report["training_rows"],
                "validation_rows": report["validation_rows"],
                "elapsed_seconds": report["elapsed_seconds"],
            }
        )
    )


if __name__ == "__main__":
    main()
