"""미사용 사건을 열기 전 모델·보정·계약을 고정한다."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from bonghwa_training.download import file_sha256


def verify_release(path: Path, config: Path) -> dict:
    receipt = json.loads(path.read_text())
    if receipt["config_sha256"] != file_sha256(config):
        raise ValueError("고정된 자료 계약이 바뀌었습니다.")
    for name, digest in receipt["frozen_files"].items():
        if file_sha256(Path(name)) != digest:
            raise ValueError("고정된 모델/보정/학습 계획이 바뀌었습니다.")
    return receipt


def freeze(run: Path, config: Path, output: Path):
    report = json.loads((run / "report.json").read_text())
    plan = json.loads((run / "plan.json").read_text())
    if report["test_evaluated"] or plan["config_sha256"] != file_sha256(config):
        raise ValueError("미사용 사건 평가를 위한 고정 조건이 맞지 않습니다.")
    model = run / f"{report['selected']}.ubj"
    if report["experiments"][report["selected"]]["model_sha256"] != file_sha256(model):
        raise ValueError("선택 모델 SHA 불일치")
    receipt = {
        "frozen_at_utc": datetime.now(UTC).isoformat(),
        "config_sha256": file_sha256(config),
        "model_path": str(model.resolve()),
        "run_path": str(run.resolve()),
        "frozen_files": {
            str(p.resolve()): file_sha256(p)
            for p in (model, run / "report.json", run / "plan.json")
        },
        "purpose": "미사용 국외 사건 1회 평가. 국내 운영 승인과는 별개",
    }
    with output.open("x") as dst:
        dst.write(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    freeze(a.run, a.config, a.output)


if __name__ == "__main__":
    main()
