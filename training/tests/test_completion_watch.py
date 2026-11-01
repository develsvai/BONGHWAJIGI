import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from bonghwa_training.download import file_sha256


def _write_json(path, value):
    path.write_text(json.dumps(value) + "\n")


@pytest.fixture
def completion_watch(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / "tools" / "audit_kma_when_ready.py"
    spec = importlib.util.spec_from_file_location("audit_kma_when_ready_for_test", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.chdir(tmp_path)
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    config = tmp_path / "config.json"
    _write_json(
        config,
        {
            "assumed_input_delay_minutes": 15,
            "events": [
                {"id": "train_not_exported", "split": "train"},
                {
                    "id": "validation_2023",
                    "split": "validation",
                    "start_utc": "2023-04-02T02:00:00Z",
                },
                {"id": "calibration_not_exported", "split": "calibration"},
                {"id": "test_2025_not_exported", "split": "test"},
            ],
        },
    )
    run = Path("data/artifacts/xgboost/hourly-test-completed")
    run.mkdir(parents=True)
    _write_json(run / "plan.json", {"config_sha256": file_sha256(config)})
    _write_json(run / "report.json", {"selected": "fixed_model", "operational_use": False})
    receipt = {
        "run": str(run),
        "config_sha256": file_sha256(config),
        "report_sha256": file_sha256(run / "report.json"),
    }
    output = tmp_path / "diagnostic"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(source),
            "--unit",
            "completed-research.service",
            "--dataset",
            str(dataset),
            "--config",
            str(config),
            "--output",
            str(output),
        ],
    )
    calls = []

    def audit(*args):
        calls.append(("audit", args))
        _write_json(args[-1], {"validation_only": True})

    def export(args):
        calls.append(("export", args))
        return {"coverage": {"eligible_candidates": 2}}

    def no_wait(_):
        raise AssertionError("Terminal lifecycle tests must not sleep")

    monkeypatch.setattr(module, "audit", audit)
    monkeypatch.setattr(module, "export", export)
    monkeypatch.setattr(module.time, "sleep", no_wait)
    return SimpleNamespace(
        module=module,
        dataset=dataset,
        config=config,
        run=run,
        receipt=receipt,
        output=output,
        calls=calls,
    )


def _terminal_unit(watch, monkeypatch, *, loaded=False, result="success", exit_status="0"):
    def check_output(command, *, text):
        assert text is True
        assert command[:4] == ["systemctl", "--user", "show", "completed-research.service"]
        if "ActiveState" in command:
            return "inactive\n"
        assert command[4:] == ["-p", "Result", "-p", "ExecMainStatus", "-p", "LoadState"]
        return (
            f"Result={result}\nExecMainStatus={exit_status}\n"
            f"LoadState={'loaded' if loaded else 'not-found'}\n"
        )

    monkeypatch.setattr(watch.module.subprocess, "check_output", check_output)


def test_unloaded_unit_without_receipt_is_not_success(completion_watch, monkeypatch):
    watch = completion_watch
    # Unloaded units may misleadingly retain success/zero defaults. Neither proves completion.
    _terminal_unit(watch, monkeypatch)
    with pytest.raises(ValueError, match="완료 영수증"):
        watch.module.main()
    assert watch.calls == []
    assert not watch.output.exists()


def test_unloaded_unit_with_matching_receipt_runs_validation_only(completion_watch, monkeypatch):
    watch = completion_watch
    _terminal_unit(watch, monkeypatch)
    _write_json(watch.dataset / "hourly-test-completion.json", watch.receipt)
    watch.module.main()
    assert [name for name, _ in watch.calls] == ["audit", "export"]
    audit_args = watch.calls[0][1]
    assert audit_args == (
        watch.run,
        watch.dataset,
        watch.config,
        watch.output / "ranking-audit.json",
    )
    replay = watch.calls[1][1]
    assert replay.event == "validation_2023"
    assert replay.issue == "2023-04-02T06:15:00+00:00"
    result = json.loads((watch.output / "completion.json").read_text())
    assert result["training_completion_receipt"] == watch.receipt
    assert result["test_evaluated"] is False
    assert result["operational_use"] is False
    assert result["replays"] == [
        {"event": "validation_2023", "coverage": {"eligible_candidates": 2}, "status": "exported"}
    ]


@pytest.mark.parametrize(
    ("result", "exit_status"), [("exit-code", "1"), ("success", "1"), ("timeout", "0")]
)
def test_failed_loaded_unit_refuses_even_with_receipt(
    completion_watch, monkeypatch, result, exit_status
):
    watch = completion_watch
    _terminal_unit(watch, monkeypatch, loaded=True, result=result, exit_status=exit_status)
    _write_json(watch.dataset / "hourly-test-completion.json", watch.receipt)
    with pytest.raises(RuntimeError, match="성공을 확인하지 못했습니다"):
        watch.module.main()
    assert watch.calls == []
    assert not watch.output.exists()


@pytest.mark.parametrize("changed", ["config_sha256", "report_sha256", "run"])
def test_mismatched_receipt_refuses(completion_watch, monkeypatch, changed):
    watch = completion_watch
    _terminal_unit(watch, monkeypatch)
    bad = {**watch.receipt, changed: "different-value"}
    _write_json(watch.dataset / "hourly-test-completion.json", bad)
    with pytest.raises(ValueError):
        watch.module.main()
    assert watch.calls == []
    assert not watch.output.exists()


def test_ambiguous_matching_receipts_refuse(completion_watch, monkeypatch):
    watch = completion_watch
    _terminal_unit(watch, monkeypatch)
    for name in ("hourly-first-completion.json", "hourly-second-completion.json"):
        _write_json(watch.dataset / name, watch.receipt)
    with pytest.raises(ValueError, match="정확히 하나"):
        watch.module.main()
    assert watch.calls == []
    assert not watch.output.exists()
