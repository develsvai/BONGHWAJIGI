"""입력 개선 전후의 후보·정답·기존 피처가 같은지 검사한다."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from bonghwa_training.goes_build import FEATURES


def verify(reference: Path, candidate: Path, output: Path):
    cfg = json.loads((candidate / "config.json").read_text())
    original = json.loads((reference / "config.json").read_text())
    if cfg["events"] != original["events"]:
        raise ValueError("사건 또는 분할이 달라 같은 표본 비교가 아닙니다.")
    identity = ["issue_epoch_seconds", "row", "col", "horizon_hours", "fire_within_horizon"]
    result = {}
    for event in cfg["events"]:
        if event["split"] == "test":
            continue
        name = event["id"] + ".parquet"
        before = pq.read_table(reference / name, columns=identity)
        after = pq.read_table(candidate / name, columns=identity)
        if not before.equals(after):
            raise ValueError(f"후보/정답 표본이 바뀌었습니다: {event['id']}")
        for feature in FEATURES:
            left = pq.read_table(reference / name, columns=[feature])[feature].to_numpy()
            right = pq.read_table(candidate / name, columns=[feature])[feature].to_numpy()
            np.testing.assert_allclose(left, right, rtol=0, atol=0, equal_nan=True)
        values = np.column_stack([before[k].to_numpy() for k in identity])
        result[event["id"]] = {
            "rows": len(before),
            "cohort_sha256": hashlib.sha256(values.tobytes()).hexdigest(),
        }
    output.write_text(
        json.dumps({"same_cohort_and_original_features": True, "events": result}, indent=2) + "\n"
    )
    print(json.dumps(result), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("reference", "candidate", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    verify(a.reference, a.candidate, a.output)


if __name__ == "__main__":
    main()
