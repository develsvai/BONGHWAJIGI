import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("xgboost")
pytest.importorskip("sklearn")

from test_dataset import patch, write_record  # noqa: E402

from bonghwa_training.build import build_dataset  # noqa: E402
from bonghwa_training.download import DATASET, VERSION, file_sha256  # noqa: E402
from bonghwa_training.train import fit, gpu_lease  # noqa: E402


def test_real_fit_saves_reloadable_best_model_and_leaves_test_unevaluated(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    manifest = {"dataset": DATASET, "version": VERSION, "files": []}
    for index, split in enumerate(("train", "eval", "test")):
        path = raw / f"{split}.tfrecord"
        write_record(path, patch(index + 1))
        manifest["files"].append(
            {
                "filename": path.name,
                "official_split": split,
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    (raw / "manifest.json").write_text(json.dumps(manifest))
    dataset = tmp_path / "dataset"
    build_dataset(raw, dataset)
    args = argparse.Namespace(
        dataset=dataset,
        output=tmp_path / "model",
        device="cpu",
        rounds=3,
        early_stopping=1,
        threads=1,
        max_rows=None,
        evaluate_test=False,
    )
    result = fit(args)
    assert result["test_evaluated"] is False
    assert "test" not in result
    assert result["cpu_reload_probe_max_abs_difference"] == 0
    assert 1 <= result["saved_trees"] <= 3
    assert result["operational_use"] is False
    assert result["probability_calibrated"] is False
    assert (args.output / "model.ubj").is_file()
    assert result["validation"]["persistence_unknown_previous_excluded"] == 1
    with pytest.raises(FileExistsError):
        fit(args)


def test_gpu_lock_conflict_and_exception_release(tmp_path):
    path = tmp_path / "gpu.lock"
    with gpu_lease(path), pytest.raises(RuntimeError, match="잠금"):
        with gpu_lease(path):
            pytest.fail("서빙 잠금과 겹치는 학습이 실행됐습니다.")
    with pytest.raises(ValueError), gpu_lease(path):
        raise ValueError("훈련 오류")
    with gpu_lease(path):
        pass


@pytest.mark.parametrize("training_exit", [0, 42])
def test_wrapper_restores_active_serving_after_success_or_failure(tmp_path, training_exit):
    project = tmp_path / "project"
    tools = project / "training/tools"
    tools.mkdir(parents=True)
    source = Path(__file__).resolve().parents[1] / "tools/train_gpu.sh"
    shutil.copyfile(source, tools / "train_gpu.sh")
    python = project / "training/.venv/bin/python"
    python.parent.mkdir(parents=True)
    python.write_text(
        '#!/bin/sh\ncase "$*" in\n*bonghwa_training.train*) exit "$TRAIN_EXIT";;\n'
        "*bonghwa_training.cli*) exit 0;;\nesac\nexit 99\n"
    )
    python.chmod(0o755)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    control = bin_dir / "systemctl"
    control.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$CONTROL_LOG"\nexit 0\n')
    control.chmod(0o755)
    log = tmp_path / "control.log"
    env = {
        **os.environ,
        "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
        "CONTROL_LOG": str(log),
        "TRAIN_EXIT": str(training_exit),
    }
    result = subprocess.run(["bash", str(tools / "train_gpu.sh")], env=env, capture_output=True)
    assert result.returncode == training_exit
    calls = log.read_text().splitlines()
    assert "--user stop bonghwajigi-gpu.service" in calls
    assert calls[-1] == "--user start bonghwajigi-gpu.service"
