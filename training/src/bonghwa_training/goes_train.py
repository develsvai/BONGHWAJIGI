"""1·3·6시간 관측 접근 위험의 사건 분리 GPU 연구. 국내 운영 모델이 아니다."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import pyarrow.parquet as pq
import xgboost as xgb
from sklearn.linear_model import LogisticRegression

from bonghwa_training.download import file_sha256
from bonghwa_training.goes_build import FEATURES
from bonghwa_training.risk_metrics import logits, operating_points
from bonghwa_training.train import gpu_lease, metrics


def load(dataset: Path, cfg: dict, split: str, features: list[str]):
    xs, ys = [], []
    for event in cfg["events"]:
        if event["split"] != split:
            continue
        path = dataset / f"{event['id']}.parquet"
        report = json.loads((dataset / f"{event['id']}-report.json").read_text())
        if report["sha256"] != file_sha256(path):
            raise ValueError("시간별 학습 데이터 SHA 불일치")
        table = pq.read_table(
            path,
            columns=[
                *features,
                "fire_within_horizon",
                "issue_epoch_seconds",
                "max_input_available_epoch_seconds",
            ],
        )
        if np.any(
            table["max_input_available_epoch_seconds"].to_numpy()
            > table["issue_epoch_seconds"].to_numpy()
        ):
            raise ValueError("입력 발행 시각의 미래 누출")
        xs.append(np.column_stack([table[k].to_numpy() for k in features]))
        ys.append(table["fire_within_horizon"].to_numpy())
    return np.concatenate(xs), np.concatenate(ys)


def horizon_metrics(y, p, h):
    return {str(hours): metrics(y[h == hours], p[h == hours]) for hours in (1, 3, 6)}


def train(args):
    started = perf_counter()
    cfg = json.loads(args.config.read_text())
    if file_sha256(args.config) != file_sha256(args.dataset / "config.json"):
        raise ValueError("원본/구축/학습 계약이 다릅니다.")
    args.output.mkdir(parents=True, exist_ok=False)
    features = list(FEATURES)
    x, y = load(args.dataset, cfg, "train", features)
    vx, vy = load(args.dataset, cfg, "validation", features)
    h, vh = x[:, -1], vx[:, -1]
    for hours in (1, 3, 6):
        if len(np.unique(y[h == hours])) != 2 or len(np.unique(vy[vh == hours])) != 2:
            raise ValueError(f"{hours}시간 정답의 양성/음성이 부족합니다.")
    history_columns = [
        f for f in features if not any(term in f for term in ("30m", "60m", "last_hour"))
    ]
    cases = [
        ("spatial_depth3", 3, history_columns, 1.0),
        ("history_depth3", 3, features, 1.0),
        ("history_depth5", 5, features, 1.0),
        ("history_weighted", 4, features, float(np.sqrt((y == 0).sum() / y.sum()))),
    ]
    common = {
        "objective": "binary:logistic",
        "tree_method": "hist",
        "device": args.device,
        "eval_metric": ["logloss", "aucpr"],
        "eta": 0.05,
        "min_child_weight": 5,
        "lambda": 20,
        "subsample": 0.8,
        "colsample_bytree": 0.9,
        "max_bin": 256,
        "seed": 47,
        "nthread": 4,
    }
    plan = {
        "config_sha256": file_sha256(args.config),
        "features": features,
        "train_rows": len(y),
        "train_positives": int(y.sum()),
        "validation_rows": len(vy),
        "cases": [
            {"name": n, "depth": depth, "features": cols, "scale_pos_weight": weight}
            for n, depth, cols, weight in cases
        ],
        "parameters": common,
        "maximum_rounds": args.rounds,
        "early_stopping": 40,
        "selection": "사건 validation의 1·3·6시간 AP 산술평균. 최종 사건은 미열람",
        "monotonicity": "동일 입력에서 예측 기간이 길어져도 누적 위험은 감소하지 않음",
        "source_hashes": {
            e["id"]: file_sha256(args.dataset / f"{e['id']}.parquet")
            for e in cfg["events"]
            if e["split"] != "test"
        },
    }
    (args.output / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
    results = {}
    for name, depth, cols, weight in cases:
        indices = [features.index(f) for f in cols]
        tx, val = np.ascontiguousarray(x[:, indices]), np.ascontiguousarray(vx[:, indices])
        matrix = {"feature_names": cols, "nthread": 4, "max_bin": 256}
        training = xgb.QuantileDMatrix(tx, label=y, **matrix)
        validation = xgb.QuantileDMatrix(val, label=vy, ref=training, **matrix)
        history = {}
        parameters = {
            **common,
            "max_depth": depth,
            "scale_pos_weight": weight,
            "monotone_constraints": tuple(1 if f == "horizon_hours" else 0 for f in cols),
        }
        model = xgb.train(
            parameters,
            training,
            num_boost_round=args.rounds,
            evals=[(training, "train"), (validation, "validation")],
            evals_result=history,
            verbose_eval=50,
            callbacks=[
                xgb.callback.EarlyStopping(
                    rounds=40,
                    data_name="validation",
                    metric_name="aucpr",
                    maximize=True,
                    save_best=True,
                )
            ],
        )
        actual = json.loads(model.save_config())["learner"]["generic_param"]["device"]
        if args.device == "cuda" and not actual.startswith("cuda"):
            raise ValueError("CUDA 학습이 CPU로 대체됐습니다.")
        before = model.inplace_predict(val)
        model_path = args.output / f"{name}.ubj"
        model.save_model(model_path)
        cpu = xgb.Booster()
        cpu.load_model(model_path)
        cpu.set_param({"device": "cpu", "nthread": 4})
        p = cpu.inplace_predict(val)
        np.testing.assert_allclose(before, p, rtol=1e-5, atol=1e-6)
        by_horizon = horizon_metrics(vy, p, vh)
        results[name] = {
            "validation": by_horizon,
            "selection_score": float(
                np.mean([v["average_precision"] for v in by_horizon.values()])
            ),
            "validation_operating_points": {
                str(hours): operating_points(vy[vh == hours], p[vh == hours]) for hours in (1, 3, 6)
            },
            "model_sha256": file_sha256(model_path),
            "features": cols,
            "device": actual,
            "best_trees": model.num_boosted_rounds(),
            "executed_rounds": len(history["train"]["aucpr"]),
            "cpu_reload_max_abs_difference": float(np.max(np.abs(before - p))),
            "feature_gain": cpu.get_score(importance_type="gain"),
        }
        (args.output / f"{name}-history.json").write_text(json.dumps(history, indent=2) + "\n")
        print(json.dumps({"experiment": name, "validation": by_horizon}), flush=True)
    winner = max(results, key=lambda k: results[k]["selection_score"])
    selected = results[winner]
    model = xgb.Booster()
    model.load_model(args.output / f"{winner}.ubj")
    model.set_param({"device": "cpu", "nthread": 4})
    # 같은 입력에서 기간만 바꿔 누적 확률의 순서를 검증한다.
    probe = vx[: min(len(vx), 8192), [features.index(f) for f in selected["features"]]].copy()
    predictions = []
    for horizon in (1, 3, 6):
        probe[:, selected["features"].index("horizon_hours")] = horizon
        predictions.append(model.inplace_predict(probe))
    if np.any(np.diff(np.array(predictions), axis=0) < -1e-6):
        raise ValueError("누적 확률의 예측 기간 단조성 위반")
    cx, cy = load(args.dataset, cfg, "calibration", selected["features"])
    cp = model.inplace_predict(cx)
    calibration = {"status": "정답 부족으로 보류", "positives": int(cy.sum())}
    if cy.sum() >= 50 and (cy == 0).sum() >= 50:
        calibrator = LogisticRegression(C=1e6, max_iter=1000).fit(logits(cp), cy)
        slope, intercept = float(calibrator.coef_[0, 0]), float(calibrator.intercept_[0])
        if slope > 0:
            calibration = {
                "status": "연구용 sigmoid 보정 적합",
                "coefficient": slope,
                "intercept": intercept,
                "fit_rows": len(cy),
                "fit_positives": int(cy.sum()),
                "limitation": "보정 사건 1개. 실제 보정 성능은 미사용 사건에서 평가해야 함",
            }
    dist = vx[:, features.index("distance_fire_km")]
    baseline = np.exp(-dist / vh)
    report = {
        "profile": cfg["profile"],
        "trained_at_utc": datetime.now(UTC).isoformat(),
        "plan_sha256": file_sha256(args.output / "plan.json"),
        "selected": winner,
        "experiments": results,
        "calibration": calibration,
        "validation_distance_baseline": horizon_metrics(vy, baseline, vh),
        "validation_train_prior": horizon_metrics(vy, np.full(len(vy), y.mean()), vh),
        "monotonicity_verified": True,
        "test_evaluated": False,
        "operational_use": False,
        "target": cfg["target"],
        "elapsed_seconds": round(perf_counter() - started, 3),
        "limitations": [
            "국외 자동 위성 관측의 연구 결과이며 국내 검증 전",
            "학습3/튜닝1/보정1 사건. 격자·시점 수를 독립 사건 수로 해석할 수 없음",
            "기상·연료·지형·진화 활동 및 사용자 취약성 입력 없음",
            "고신뢰 열 이상 관측은 실제 화선 도달·사람 피해의 정답이 아님",
            "미래 관측 불가 정답 제외로 선택 편향이 있음",
            "임계값은 연구용 누락/오경보 진단이며 대응 레벨 결정이 아님",
        ],
    }
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
    print(
        json.dumps({"selected": winner, "elapsed_seconds": report["elapsed_seconds"]}), flush=True
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--rounds", type=int, default=800)
    parser.add_argument(
        "--gpu-lock", type=Path, default=Path.home() / ".cache/bonghwajigi/gpu.lock"
    )
    args = parser.parse_args()
    if args.device == "cuda":
        with gpu_lease(args.gpu_lock):
            train(args)
    else:
        train(args)


if __name__ == "__main__":
    main()
