"""원본에서 독립 재생성하고 실제 XGBoost 로딩 근거를 작은 보고서로 보존한다."""

import argparse
import json
import shutil
import tempfile
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import numpy as np
import xgboost as xgb

from bonghwa_training.build import FEATURES, build_dataset, iter_training_batches, verify_dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--processed", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    verified = verify_dataset(args.processed)
    original = json.loads((args.processed / "report.json").read_text())
    with tempfile.TemporaryDirectory(prefix="bonghwa-ndws-rebuild-") as directory:
        rebuilt = build_dataset(args.raw, Path(directory))
        if original != rebuilt:
            raise ValueError("독립 재생성한 결과의 통계 또는 파일 해시가 다릅니다.")
        verify_dataset(Path(directory))
    matrices = {}
    for split in original["splits"]:
        x, y = next(iter_training_batches(args.processed / f"{split}.parquet"))
        matrix = xgb.DMatrix(x, label=y, feature_names=list(FEATURES), nthread=2)
        matrices[split] = {
            "rows_checked": matrix.num_row(),
            "columns": matrix.num_col(),
            "missing_input_values": int(np.isnan(x).sum()),
        }
    summary = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "full_dataset_batch_validation": verified,
        "independent_rebuild_report_and_parquet_sha256_match": True,
        "real_xgboost_dmatrix_check": matrices,
        "model_trained": False,
        "versions": {
            name: version(name)
            for name in ("bonghwa-training", "numpy", "scipy", "pyarrow", "protobuf", "xgboost")
        },
    }
    args.reports.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.raw / "manifest.json", args.reports / "source-manifest.json")
    shutil.copyfile(args.processed / "report.json", args.reports / "dataset-report.json")
    (args.reports / "validation-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
