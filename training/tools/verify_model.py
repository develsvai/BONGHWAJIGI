"""고정된 모델을 CPU로 다시 읽어 validation 재현과 첫 test 평가를 수행한다."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import xgboost as xgb

from bonghwa_training.build import FEATURES, verify_dataset
from bonghwa_training.download import file_sha256
from bonghwa_training.train import evaluate, load_split


def compare_values(actual, expected):
    if isinstance(expected, dict):
        if actual.keys() != expected.keys():
            raise ValueError("재계산 보고서의 필드가 다릅니다.")
        for key in expected:
            compare_values(actual[key], expected[key])
    elif isinstance(expected, float):
        np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-8)
    elif actual != expected:
        raise ValueError("재계산 보고서와 기존 값이 다릅니다.")


def diagnostics(model, x, y):
    p = model.inplace_predict(x)
    if not np.isfinite(p).all() or not ((p >= 0) & (p <= 1)).all():
        raise ValueError("확률에 비유한 값 또는 범위 밖 값이 있습니다.")
    decision = p >= 0.5
    positive = y == 1
    return {
        "threshold": 0.5,
        "threshold_purpose": "diagnostic only; not an approved alert threshold",
        "true_positive": int((decision & positive).sum()),
        "false_positive": int((decision & ~positive).sum()),
        "false_negative": int((~decision & positive).sum()),
        "true_negative": int((~decision & ~positive).sum()),
        "probability_quantiles": {
            str(q): float(np.quantile(p, q)) for q in (0, 0.5, 0.9, 0.99, 0.999, 1)
        },
    }


def verify_model(run: Path, dataset: Path, output: Path) -> dict:
    if output.resolve() == (run / "report.json").resolve() or output.exists():
        raise ValueError("원본 학습 보고서 또는 기존 검증 결과를 덮어쓰지 않습니다.")
    original = json.loads((run / "report.json").read_text())
    history = json.loads((run / "history.json").read_text())
    dataset_report = json.loads((dataset / "report.json").read_text())
    model_path = run / "model.ubj"
    model_digest = file_sha256(model_path)
    if model_digest != original["model_sha256"]:
        raise ValueError("모델 SHA256이 학습 보고서와 다릅니다.")
    if file_sha256(dataset / "report.json") != original["dataset_report_sha256"]:
        raise ValueError("학습 당시 데이터 보고서와 다릅니다.")
    if original["feature_names"] != list(FEATURES):
        raise ValueError("학습 피처 순서가 다릅니다.")
    if original["test_evaluated"] or original["purpose"] != "research":
        raise ValueError("최초 test 평가할 연구용 학습 산출물이 아닙니다.")
    if original["target"] != dataset_report["target"]:
        raise ValueError("학습 정답 계약이 다릅니다.")
    validation_history = np.asarray(history["validation"]["aucpr"])
    lengths = {len(values) for split in history.values() for values in split.values()}
    if lengths != {original["rounds_executed"]} or not np.isfinite(validation_history).all():
        raise ValueError("회차별 학습 이력의 길이 또는 값이 잘못됐습니다.")
    best = int(np.argmax(validation_history))
    if best != original["best_iteration"]:
        raise ValueError("저장한 최적 회차와 검증 이력이 다릅니다.")
    verify_dataset(dataset)
    model = xgb.Booster()
    model.load_model(model_path)
    model.set_param({"device": "cpu", "nthread": 4})
    if model.feature_names != list(FEATURES) or model.num_boosted_rounds() != best + 1:
        raise ValueError("실제 모델 피처 또는 트리 수가 최적 회차와 다릅니다.")
    if model.num_boosted_rounds() != original["saved_trees"]:
        raise ValueError("실제 모델 트리 수가 보고서와 다릅니다.")
    prior = original["train_positive_fraction"]
    expected_prior = dataset_report["splits"]["train"]["positive_fraction"]
    np.testing.assert_allclose(prior, expected_prior, rtol=0, atol=1e-15)
    result = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "model_sha256": model_digest,
        "original_report_sha256": file_sha256(run / "report.json"),
        "dataset_report_sha256": original["dataset_report_sha256"],
        "saved_trees": model.num_boosted_rounds(),
        "rounds_executed": original["rounds_executed"],
        "best_iteration_zero_based": best,
        "rounds_after_best": len(validation_history) - best - 1,
        "best_validation_aucpr": float(validation_history[best]),
        "original_training_device": original["training_device"],
        "reevaluation_device": "cpu",
        "original_elapsed_seconds": original["elapsed_seconds"],
        "test_evaluated_during_training": False,
        "test_evaluated_in_this_audit": True,
        "model_parameters_changed_or_retrained": False,
        "probability_calibrated": False,
        "operational_use": False,
        "limitations": original["limitations"],
    }
    for split in ("validation", "test"):
        x, y = load_split(dataset, split, dataset_report)
        scores = evaluate(model, x, y, prior)
        if split == "validation":
            compare_values(scores, original["validation"])
            result["original_validation_metrics_reproduced"] = True
        result[split] = scores
        result[f"{split}_diagnostics"] = diagnostics(model, x, y)
        print(json.dumps({"evaluated": split, "metrics": scores["model_all_rows"]}), flush=True)
    if file_sha256(model_path) != model_digest:
        raise ValueError("검증 중 원본 모델 파일이 바뀌었습니다.")
    result["model_unchanged_after_audit"] = True
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"verified": True, "output": str(output), "model_sha256": model_digest}))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify_model(args.run, args.dataset, args.output)


if __name__ == "__main__":
    main()
