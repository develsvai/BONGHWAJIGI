"""고정 v3와 v4 모델을 같은 2023 검증 행에서 재평가한다. 재학습·선택은 하지 않는다."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import xgboost as xgb

from bonghwa_training import expanded_generalization_experiment as expanded
from bonghwa_training import ranking_audit
from bonghwa_training.download import file_sha256


def compare(previous_run, previous_dataset, current_run, dataset, cv_run, output):
    previous = ranking_audit.verify_inputs(
        previous_run, previous_dataset, previous_dataset / "config.json"
    )
    current = ranking_audit.verify_inputs(current_run, dataset, dataset / "config.json")
    old_report, old_plan, old_cfg, old_model, old_path, _ = previous
    report, current_plan, cfg, current_model, current_path, validation = current
    if old_cfg["profile"] != "kor_gk2a_10min_approach_hindcast_1_3_6h_v3_context_v1":
        raise ValueError("비교 기준은 고정 v3 국내 context 자료여야 합니다.")
    if cfg["profile"] != expanded.PROFILE + "_context_v1":
        raise ValueError("비교 대상은 고정 v4 국내 context 자료여야 합니다.")
    allowed_changes = {"profile", "events", "expansion_plan", "limitations", "model_selection"}
    for name in set(old_cfg) | set(cfg):
        if name not in allowed_changes and old_cfg.get(name) != cfg.get(name):
            raise ValueError(f"v3/v4의 입력·정답 계약이 달라졌습니다: {name}")
    # 과거 행을 재구성하며 정답/피처가 바뀌지 않았는지 SHA로 확인한다.
    shared = {}
    current_events = {event["id"]: event for event in cfg["events"]}
    for event in old_cfg["events"]:
        if event["split"] not in ("train", "validation"):
            continue
        expanded.common.guard_event(event, event["split"])
        ident = event["id"]
        if current_events.get(ident) != event:
            raise ValueError("기존 사건의 입력 범위/분할이 바뀌었습니다.")
        digest = file_sha256(dataset / f"{ident}.parquet")
        if digest != old_plan["source_hashes"][ident]:
            raise ValueError(f"기존 사건 Parquet가 동일하지 않습니다: {ident}")
        shared[ident] = digest
    cv = json.loads((cv_run / "report.json").read_text())
    cv_plan = json.loads((cv_run / "plan.json").read_text())
    selection = json.loads((cv_run / "selection.json").read_text())
    if (
        cv["plan_sha256"] != file_sha256(cv_run / "plan.json")
        or cv["selection_sha256"] != file_sha256(cv_run / "selection.json")
        or cv_plan["config_sha256"] != file_sha256(dataset / "config.json")
        or selection["selected"] != cv["selected"]
        or selection["plan_sha256"] != file_sha256(cv_run / "plan.json")
        or cv["training_horizon_priors"] != cv_plan["training_horizon_priors"]
    ):
        raise ValueError("교차검증의 자료/선택 계약이 다릅니다.")
    ranking_audit._safe_name(cv["selected"])
    candidates = {candidate["name"]: candidate for candidate in cv_plan["candidates"]}
    for name, digest in selection["cv_result_sha256"].items():
        ranking_audit._safe_name(name)
        if name not in candidates or digest != file_sha256(cv_run / f"{name}-cv.json"):
            raise ValueError("교차검증 선택 근거의 SHA가 다릅니다.")
    if set(selection["cv_result_sha256"]) != set(candidates):
        raise ValueError("교차검증 선택 후보가 빠졌습니다.")
    if (
        cv["selected"] not in candidates
        or cv["models"][cv["selected"]]["candidate"]["features"]
        != candidates[cv["selected"]]["features"]
    ):
        raise ValueError("교차검증 선택 모델의 입력 계획이 다릅니다.")
    for event in cfg["events"]:
        if event["split"] != "train":
            continue
        expanded.common.guard_event(event, "train")
        ident = event["id"]
        digest = file_sha256(dataset / f"{ident}.parquet")
        if (
            digest != cv_plan["source_hashes"][ident]
            or digest != current_plan["source_hashes"][ident]
        ):
            raise ValueError("v4 GPU/CPU 학습 원본 SHA가 다릅니다.")
    features = [f for f in cfg["feature_names"] if f not in cfg.get("drop_features", [])]
    events = {e["id"]: expanded.load_event(dataset, e, features, "validation") for e in validation}
    if {e: d["sha256"] for e, d in events.items()} != cv["validation_source_hashes"]:
        raise ValueError("교차검증 보고서와 실제 비교 검증 행이 다릅니다.")
    if any(d["sha256"] != current_plan["source_hashes"][e] for e, d in events.items()):
        raise ValueError("v4 GPU 모델과 실제 비교 검증 행이 다릅니다.")
    model_specs = {
        "previous_v3": (old_path, old_model["features"], old_model["model_sha256"]),
        "expanded_v4_exploratory": (
            current_path,
            current_model["features"],
            current_model["model_sha256"],
        ),
        "expanded_v4_group_cv": (
            cv_run / f"{cv['selected']}.ubj",
            cv["models"][cv["selected"]]["candidate"]["features"],
            cv["models"][cv["selected"]]["model_sha256"],
        ),
    }
    results = expanded.distance_diagnostics(events, features)
    results["constant_training_prior"] = {
        event_id: expanded.evaluate(
            data,
            expanded.prior_scores(data["h"], cv_plan["training_horizon_priors"]),
            probability=True,
        )
        for event_id, data in events.items()
    }
    for name, (path, columns, digest) in model_specs.items():
        if digest != file_sha256(path) or any(f not in features for f in columns):
            raise ValueError("비교 모델의 SHA/피처가 다릅니다.")
        model = xgb.Booster()
        model.load_model(path)
        model.set_param({"device": "cpu", "nthread": 2})
        if model.feature_names != columns:
            raise ValueError("실제 모델의 피처 순서가 다릅니다.")
        indices = [features.index(f) for f in columns]
        results[name] = {
            event_id: expanded.evaluate(
                data,
                model.inplace_predict(data["x"][:, indices]) if len(data["y"]) else np.array([]),
                probability=True,
            )
            for event_id, data in events.items()
        }
    cells = expanded.eligible_cells(events)
    result = {
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "source_sha256": file_sha256(Path(__file__)),
        "dataset_config_sha256": file_sha256(dataset / "config.json"),
        "model_sha256": {name: spec[2] for name, spec in model_specs.items()},
        "selected_names": {
            "previous_v3": old_report["selected"],
            "expanded_v4_exploratory": report["selected"],
            "expanded_v4_group_cv": cv["selected"],
        },
        "shared_v3_parquets_exactly_identical": shared,
        "validation_source_sha256": {e: d["sha256"] for e, d in events.items()},
        "validation_inventory": expanded.inventory(events),
        "eligible_cells": [{"event": e, "horizon_hours": h} for e, h in cells],
        "mean_event_horizon_ap": {
            name: expanded.mean_ap(result, cells) for name, result in results.items()
        },
        "validation": results,
        "probability_calibrated": False,
        "test_evaluated": False,
        "operational_use": False,
        "limitations": [
            "2023 validation was used for exploratory model selection; not an independent test.",
            "No fitting or model selection occurs in this matched-cohort comparison.",
            "AP macro averages exclude empty/single-class event-horizon cells equally.",
            "Shared dates and repeated observations cannot be counted as independent fires.",
            "Satellite observation scores do not establish personal harm or alert accuracy.",
        ],
    }
    expanded.common.write_json(output, result)
    print(json.dumps(result["mean_event_horizon_ap"]), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("previous-run", "previous-dataset", "current-run", "dataset", "cv-run", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    compare(**vars(parser.parse_args()))


if __name__ == "__main__":
    main()
