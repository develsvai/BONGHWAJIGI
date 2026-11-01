"""고정 모델로 미사용 국외 사건을 한 번 평가한다. 평가 후 튜닝하지 않는다."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import xgboost as xgb
from scipy.special import expit

from bonghwa_training.download import file_sha256
from bonghwa_training.goes_build import FEATURES
from bonghwa_training.goes_release import verify_release
from bonghwa_training.goes_train import horizon_metrics, load
from bonghwa_training.risk_metrics import at_threshold, logits


def evaluate(dataset: Path, config: Path, release: Path, output: Path):
    receipt = verify_release(release, config)
    if output.exists():
        raise FileExistsError("기존 최종 평가를 덮어쓸 수 없습니다.")
    cfg = json.loads(config.read_text())
    if file_sha256(dataset / "config.json") != file_sha256(config):
        raise ValueError("최종 자료 구축 계약 불일치")
    run = Path(receipt["run_path"])
    original = json.loads((run / "report.json").read_text())
    selected = original["experiments"][original["selected"]]
    x, y = load(dataset, cfg, "test", selected["features"])
    horizons = x[:, selected["features"].index("horizon_hours")]
    model = xgb.Booster()
    model.load_model(receipt["model_path"])
    model.set_param({"device": "cpu", "nthread": 4})
    p = model.inplace_predict(x)
    # 임계값은 validation에서 정한 값을 그대로 적용한다.
    thresholds = {
        str(h): [
            {
                "validation_maximum_fpr_requested": point["maximum_fpr_requested"],
                "frozen_raw_threshold": point["threshold"],
                **at_threshold(y[horizons == h], p[horizons == h], point["threshold"]),
            }
            for point in selected["validation_operating_points"][str(h)]
        ]
        for h in (1, 3, 6)
    }
    all_x, _ = load(dataset, cfg, "test", list(FEATURES))
    baseline = np.exp(-all_x[:, FEATURES.index("distance_fire_km")] / horizons)
    result = {
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "frozen_release_sha256": file_sha256(release),
        "selected": original["selected"],
        "raw": horizon_metrics(y, p, horizons),
        "distance_baseline": horizon_metrics(y, baseline, horizons),
        "frozen_validation_thresholds": thresholds,
        "test_events": [e["id"] for e in cfg["events"] if e["split"] == "test"],
        "test_event_count": sum(e["split"] == "test" for e in cfg["events"]),
        "test_files_sha256": {
            e["id"]: file_sha256(dataset / f"{e['id']}.parquet")
            for e in cfg["events"]
            if e["split"] == "test"
        },
        "operational_use": False,
        "limitations": original["limitations"]
        + [
            "미사용 사건 1개만의 평가. 이 결과에 맞춘 재튜닝은 별도 새 평가 사건이 필요함",
            "국내·GK2A에 대한 성능이나 개인 피해 확률을 입증하지 않음",
        ],
    }
    calibration = original["calibration"]
    if "coefficient" in calibration:
        calibrated = expit(
            calibration["coefficient"] * logits(p).ravel() + calibration["intercept"]
        )
        result["calibrated"] = horizon_metrics(y, calibrated, horizons)
    with output.open("x") as dst:
        dst.write(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--release", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    evaluate(a.dataset, a.config, a.release, a.output)


if __name__ == "__main__":
    main()
