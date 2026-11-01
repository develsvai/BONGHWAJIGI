"""미국 NDWS 연구용 학습. 기본 실행은 test를 평가하지 않는다."""

import argparse
import fcntl
import json
import os
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import xgboost as xgb
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

from bonghwa_training.build import FEATURES, iter_training_batches, verify_dataset
from bonghwa_training.download import file_sha256


@contextmanager
def gpu_lease(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(
                "GPU 서빙/학습이 실행 중입니다. GPU 잠금을 확보하지 못했습니다."
            ) from None
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def load_split(dataset: Path, split: str, report: dict, limit: int | None = None):
    rows = report["splits"][split]["rows"]
    if limit is not None:
        if limit < 1:
            raise ValueError("행 제한은 양수여야 합니다.")
        rows = min(rows, limit)
    x = np.empty((rows, len(FEATURES)), dtype=np.float32)
    y = np.empty(rows, dtype=np.int8)
    offset = 0
    for batch_x, batch_y in iter_training_batches(dataset / f"{split}.parquet"):
        size = min(len(batch_y), rows - offset)
        x[offset : offset + size], y[offset : offset + size] = batch_x[:size], batch_y[:size]
        offset += size
        if offset == rows:
            break
    if offset != rows or not all(np.any(y == label) for label in (0, 1)):
        raise ValueError(f"{split} 행 수 또는 양성/음성 정답을 확인하세요.")
    return x, y


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    if not len(y):
        return {"rows": 0}
    decision = p >= 0.5
    both = len(np.unique(y)) == 2
    return {
        "rows": len(y),
        "positives": int(y.sum()),
        "average_precision": float(average_precision_score(y, p)) if both else None,
        "roc_auc": float(roc_auc_score(y, p)) if both else None,
        "brier": float(brier_score_loss(y, p)),
        "logloss": float(log_loss(y, p, labels=[0, 1])),
        "precision_at_0_5": float(precision_score(y, decision, zero_division=0)),
        "recall_at_0_5": float(recall_score(y, decision, zero_division=0)),
    }


def evaluate(model: xgb.Booster, x, y, prior: float) -> dict:
    probabilities = model.inplace_predict(x)
    previous = x[:, FEATURES.index("PrevFireMask")]
    observed = np.isfinite(previous)
    return {
        "model_all_rows": metrics(y, probabilities),
        "constant_train_prior_all_rows": metrics(y, np.full(len(y), prior)),
        "persistence_observed_previous_only": metrics(y[observed], previous[observed]),
        "model_on_same_persistence_rows": metrics(y[observed], probabilities[observed]),
        "persistence_unknown_previous_excluded": int((~observed).sum()),
        "threshold_note": "0.5 is a diagnostic only; not a response-level threshold",
    }


def fit(args) -> dict:
    started = perf_counter()
    verify_dataset(args.dataset)
    report = json.loads((args.dataset / "report.json").read_text())
    if args.rounds < 1 or args.early_stopping < 1 or args.threads < 1:
        raise ValueError("학습 횟수, 조기 종료와 CPU 스레드는 양수여야 합니다.")
    # 기존 모델을 덮어쓰지 않는다. 검증 실패 시에도 성공 보고서는 생성하지 않는다.
    args.output.mkdir(parents=True, exist_ok=False)
    config = {
        "objective": "binary:logistic",
        "tree_method": "hist",
        "device": args.device,
        "eval_metric": ["logloss", "aucpr"],
        "max_depth": 6,
        "eta": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.9,
        "max_bin": 256,
        "seed": 47,
        "nthread": args.threads,
    }
    (args.output / "parameters.json").write_text(json.dumps(config, indent=2) + "\n")
    print("학습·검증 행을 읽고 있습니다.", flush=True)
    train_x, train_y = load_split(args.dataset, "train", report, args.max_rows)
    validation_x, validation_y = load_split(args.dataset, "validation", report, args.max_rows)
    print(
        json.dumps(
            {
                "train_rows": len(train_y),
                "validation_rows": len(validation_y),
                "features": len(FEATURES),
                "device_requested": args.device,
            }
        ),
        flush=True,
    )
    matrix_args = {"feature_names": list(FEATURES), "nthread": args.threads, "max_bin": 256}
    train = xgb.QuantileDMatrix(train_x, label=train_y, **matrix_args)
    validation = xgb.QuantileDMatrix(validation_x, label=validation_y, ref=train, **matrix_args)
    history = {}
    model = xgb.train(
        config,
        train,
        num_boost_round=args.rounds,
        evals=[(train, "train"), (validation, "validation")],
        evals_result=history,
        verbose_eval=10,
        callbacks=[
            xgb.callback.EarlyStopping(
                rounds=args.early_stopping,
                data_name="validation",
                metric_name="aucpr",
                maximize=True,
                save_best=True,
            )
        ],
    )
    actual_device = json.loads(model.save_config())["learner"]["generic_param"]["device"]
    if args.device == "cuda" and not actual_device.startswith("cuda"):
        raise RuntimeError("CUDA 학습이 CPU로 대체됐습니다. 성공으로 기록하지 않습니다.")
    probe = xgb.DMatrix(validation_x[:4096], feature_names=list(FEATURES))
    before = model.predict(probe)
    model_path = args.output / "model.ubj"
    model.save_model(model_path)
    cpu = xgb.Booster()
    cpu.load_model(model_path)
    cpu.set_param({"device": "cpu", "nthread": args.threads})
    after = cpu.predict(probe)
    np.testing.assert_allclose(before, after, rtol=1e-5, atol=1e-6)
    prior = float(train_y.mean())
    result = {
        "profile": report["profile"],
        "purpose": "preflight" if args.max_rows else "research",
        "trained_at_utc": datetime.now(UTC).isoformat(),
        "xgboost": xgb.__version__,
        "training_device": actual_device,
        "dataset_report_sha256": file_sha256(args.dataset / "report.json"),
        "feature_names": list(FEATURES),
        "target": report["target"],
        "train_rows": len(train_y),
        "train_positive_fraction": prior,
        "maximum_rows_per_split": args.max_rows,
        "rounds_executed": len(history["train"]["aucpr"]),
        "best_iteration": int(model.best_iteration),
        "saved_trees": model.num_boosted_rounds(),
        "cpu_reload_probe_max_abs_difference": float(np.max(np.abs(before - after))),
        "validation": evaluate(cpu, validation_x, validation_y, prior),
        "test_evaluated": args.evaluate_test,
        "probability_calibrated": False,
        "operational_use": False,
        "limitations": report["limitations"],
    }
    if args.evaluate_test:
        test_x, test_y = load_split(args.dataset, "test", report, args.max_rows)
        result["test"] = evaluate(cpu, test_x, test_y, prior)
    result["elapsed_seconds"] = round(perf_counter() - started, 3)
    result["model_sha256"] = file_sha256(model_path)
    (args.output / "history.json").write_text(json.dumps(history, indent=2) + "\n")
    (args.output / "feature-gain.json").write_text(
        json.dumps(model.get_score(importance_type="gain"), indent=2) + "\n"
    )
    (args.output / "report.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--rounds", type=int, default=300)
    parser.add_argument("--early-stopping", type=int, default=30)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--max-rows", type=int, help="사전 실행용: 분할별 첫 N행으로 제한")
    parser.add_argument(
        "--evaluate-test", action="store_true", help="설정 고정 후 최종 평가 때만 지정"
    )
    parser.add_argument(
        "--gpu-lock",
        type=Path,
        default=Path(
            os.environ.get("BONGHWA_GPU_LOCK_PATH", Path.home() / ".cache/bonghwajigi/gpu.lock")
        ),
    )
    args = parser.parse_args()
    if args.device == "cuda":
        with gpu_lease(args.gpu_lock):
            fit(args)
    else:
        fit(args)


if __name__ == "__main__":
    main()
