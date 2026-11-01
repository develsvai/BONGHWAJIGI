"""합성 데이터로 CUDA 실행·저장·CPU 재로딩만 확인한다. 산불 실모델이 아니다."""

import argparse
import json
from pathlib import Path
from time import perf_counter

from bonghwajigi.common.config import Settings
from bonghwajigi.common.gpu_lock import GpuLease


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="새로 만들 검증 산출물 디렉터리")
    args = parser.parse_args()
    settings = Settings()
    lease = GpuLease(settings.gpu_lock_path)
    lease.acquire()
    try:
        import numpy as np
        import xgboost as xgb

        args.output.mkdir(parents=True, exist_ok=False)
        start = perf_counter()
        rng = np.random.default_rng(47)
        features = rng.normal(size=(5000, 16)).astype(np.float32)
        labels = (features[:, 0] + 0.5 * features[:, 1] > 0).astype(np.float32)
        matrix = xgb.DMatrix(features, label=labels)
        model = xgb.train(
            {
                "device": "cuda",
                "tree_method": "hist",
                "objective": "binary:logistic",
                "max_depth": 3,
                "seed": 47,
                "nthread": 2,
            },
            matrix,
            num_boost_round=20,
        )
        config = json.loads(model.save_config())
        device = config["learner"]["generic_param"]["device"]
        if not device.startswith("cuda"):
            raise RuntimeError("XGBoost가 실제 CUDA 학습을 사용하지 않았습니다.")
        gpu_output = model.predict(matrix)
        path = args.output / "simulation-booster.ubj"
        model.save_model(path)
        cpu = xgb.Booster()
        cpu.load_model(path)
        cpu.set_param({"device": "cpu", "nthread": 2})
        cpu_output = cpu.predict(matrix)
        np.testing.assert_allclose(gpu_output, cpu_output, rtol=1e-5, atol=1e-6)
        report = {
            "mode": "simulation",
            "purpose": "cuda_runtime_check_only",
            "xgboost": xgb.__version__,
            "training_device": device,
            "rows": 5000,
            "features": 16,
            "rounds": 20,
            "cpu_reload_max_abs_difference": float(np.max(np.abs(gpu_output - cpu_output))),
            "elapsed_seconds": round(perf_counter() - start, 3),
            "model": str(path),
            "build_info": xgb.build_info(),
        }
        (args.output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report))
    finally:
        lease.close()


if __name__ == "__main__":
    main()
