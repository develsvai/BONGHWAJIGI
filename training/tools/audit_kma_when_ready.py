"""Bounded post-training diagnostics for one completed Korean research dataset."""

import argparse
import json
import subprocess
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from bonghwa_training.download import file_sha256
from bonghwa_training.prediction_evidence import export
from bonghwa_training.ranking_audit import audit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--unit", required=True)
    p.add_argument("--dataset", required=True, type=Path)
    p.add_argument("--config", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    deadline = time.monotonic() + 180 * 60
    while time.monotonic() < deadline:
        state = subprocess.check_output(
            ["systemctl", "--user", "show", args.unit, "-p", "ActiveState", "--value"], text=True
        ).strip()
        if state not in ("active", "activating", "deactivating", "reloading"):
            break
        time.sleep(15)
    else:
        raise TimeoutError("연구 학습 완료 대기 180분 초과")
    properties = subprocess.check_output(
        [
            "systemctl",
            "--user",
            "show",
            args.unit,
            "-p",
            "Result",
            "-p",
            "ExecMainStatus",
            "-p",
            "LoadState",
        ],
        text=True,
    )
    values = dict(line.split("=", 1) for line in properties.splitlines() if "=" in line)
    if values.get("LoadState") == "loaded" and (
        values.get("Result") != "success" or values.get("ExecMainStatus") != "0"
    ):
        raise RuntimeError("연구 학습 성공을 확인하지 못했습니다.")
    digest = file_sha256(args.config)
    # Transient units can be unloaded after success. Require a durable receipt emitted
    # only after training and restoration; absence of a unit is never success evidence.
    receipts = [
        json.loads(path.read_text()) for path in args.dataset.glob("hourly-*-completion.json")
    ]
    receipts = [r for r in receipts if r["config_sha256"] == digest]
    if len(receipts) != 1:
        raise ValueError("해당 설정의 학습·서빙 복구 완료 영수증이 정확히 하나여야 합니다.")
    receipt = receipts[0]
    candidates = []
    for run in Path("data/artifacts/xgboost").glob("hourly-*"):
        if (run / "plan.json").is_file() and (run / "report.json").is_file():
            if json.loads((run / "plan.json").read_text())["config_sha256"] == digest:
                candidates.append(run)
    if len(candidates) != 1:
        raise ValueError("해당 설정의 완료 학습이 정확히 하나여야 합니다.")
    run = candidates[0]
    if receipt["run"] != str(run) or receipt["report_sha256"] != file_sha256(run / "report.json"):
        raise ValueError("완료 영수증과 학습 결과 SHA가 다릅니다.")
    args.output.mkdir(parents=True, exist_ok=False)
    audit(run, args.dataset, args.config, args.output / "ranking-audit.json")
    cfg = json.loads(args.config.read_text())
    replays = []
    for event in cfg["events"]:
        if event["split"] != "validation":
            continue
        # Fixed offset, not selected using scores or future labels.
        issue = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00")) + timedelta(
            hours=4, minutes=cfg["assumed_input_delay_minutes"]
        )
        try:
            result = export(
                SimpleNamespace(
                    run=run,
                    dataset=args.dataset,
                    raw=Path("data/raw/korea-wildfire"),
                    static=Path("data/processed/korea-hindcast-v2"),
                    event=event["id"],
                    issue=issue.isoformat(),
                    output=args.output / event["id"],
                )
            )
            replays.append(
                {"event": event["id"], "coverage": result["coverage"], "status": "exported"}
            )
        except ValueError as exc:
            # Fail the diagnostic on integrity errors, not on a genuinely absent scan.
            if "해당 시각의 입력이 없습니다" not in str(exc):
                raise
            replays.append({"event": event["id"], "status": "unavailable", "reason": str(exc)})
    result = {
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "run": str(run),
        "dataset": str(args.dataset),
        "config_sha256": digest,
        "replay_issue_rule": "event start + 4 hours + assumed input delay",
        "replays": replays,
        "operational_use": False,
        "test_evaluated": False,
        "training_completion_receipt": receipt,
    }
    (args.output / "completion.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
