import importlib.util
import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import xgboost as xgb

from bonghwa_training import expanded_generalization_experiment as expanded
from bonghwa_training.download import file_sha256

SPEC = importlib.util.spec_from_file_location(
    "compare_kma_generations", Path(__file__).parents[1] / "tools/compare_kma_generations.py"
)
comparison = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(comparison)
FEATURES = ["distance_fire_km", "distance_recent_fire_60m_km", "horizon_hours"]


def write_json(path, value):
    path.write_text(json.dumps(value) + "\n")


def read_json(path):
    return json.loads(path.read_text())


def modify(path, **updates):
    value = read_json(path)
    value.update(updates)
    write_json(path, value)
    return value


def rebind_metadata(args):
    """Fixture setup only: keep outer hashes valid when testing an inner contract."""
    for run, dataset in (
        (args["previous_run"], args["previous_dataset"]),
        (args["current_run"], args["dataset"]),
    ):
        digest = file_sha256(dataset / "config.json")
        modify(dataset / "report.json", config_sha256=digest)
        modify(run / "plan.json", config_sha256=digest)
        modify(run / "report.json", plan_sha256=file_sha256(run / "plan.json"))
    run = args["cv_run"]
    modify(run / "plan.json", config_sha256=file_sha256(args["dataset"] / "config.json"))
    modify(run / "selection.json", plan_sha256=file_sha256(run / "plan.json"))
    modify(
        run / "report.json",
        plan_sha256=file_sha256(run / "plan.json"),
        selection_sha256=file_sha256(run / "selection.json"),
    )


@pytest.fixture
def inputs(tmp_path):
    args = {
        name: tmp_path / name
        for name in ("previous_run", "previous_dataset", "current_run", "dataset", "cv_run")
    }
    for path in args.values():
        path.mkdir()
    args["output"] = tmp_path / "comparison.json"
    events = [
        {"id": name, "split": split, "start_utc": date + "T00:00:00Z", "hours": 12}
        for name, split, date in [
            ("train_a", "train", "2020-04-25"),
            ("train_b", "train", "2021-02-21"),
            ("train_c", "train", "2022-02-28"),
            ("train_d", "train", "2022-03-04"),
            ("validation", "validation", "2023-04-02"),
            ("train_extra", "train", "2022-05-31"),
            ("empty", "validation", "2023-04-03"),
            ("positive_only", "validation", "2023-03-08"),
        ]
    ]
    forbidden = [
        {
            "id": "forbidden_calibration",
            "split": "calibration",
            "start_utc": "2023-04-10T00:00:00Z",
            "hours": 12,
        },
        {
            "id": "forbidden_test_2025",
            "split": "test",
            "start_utc": "2025-03-22T00:00:00Z",
            "hours": 12,
            "locked": True,
        },
    ]
    cfg = {
        "profile": expanded.CONTEXT_PROFILE,
        "feature_names": FEATURES,
        "reader": "gk2a",
        "horizons_hours": [1, 3, 6],
        "events": events + forbidden,
    }
    old_cfg = {
        **cfg,
        "profile": "kor_gk2a_10min_approach_hindcast_1_3_6h_v3_context_v1",
        "events": events[:5] + forbidden,
    }
    write_json(args["dataset"] / "config.json", cfg)
    write_json(args["previous_dataset"] / "config.json", old_cfg)
    sources = {}
    for event in events:
        size = 0 if event["id"] == "empty" else 12
        start = expanded.datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00"))
        y = np.tile([0, 1, 0, 1], 3)[:size]
        if event["id"] == "positive_only":
            y[:] = 1
        table = pa.table(
            {
                "distance_fire_km": np.tile([4.0, 1.0, 3.0, 2.0], 3)[:size],
                "distance_recent_fire_60m_km": np.tile([3.0, 2.0, 4.0, 1.0], 3)[:size],
                "horizon_hours": np.repeat([1, 3, 6], 4)[:size],
                "fire_within_horizon": y,
                "issue_epoch_seconds": np.full(size, start.timestamp() + 900),
                "max_input_available_epoch_seconds": np.full(size, start.timestamp()),
                "row": np.tile([1, 2, 3, 4], 3)[:size],
                "col": np.zeros(size),
            }
        )
        path = args["dataset"] / f"{event['id']}.parquet"
        pq.write_table(table, path)
        sources[event["id"]] = file_sha256(path)
        write_json(
            path.with_name(f"{event['id']}-report.json"),
            {
                "event": event,
                "rows": size,
                "sha256": sources[event["id"]],
                "unusable_reason": "no eligible rows" if not size else None,
            },
        )
        if event in events[:5]:
            (args["previous_dataset"] / path.name).write_bytes(path.read_bytes())
    training = pq.read_table(args["dataset"] / "train_a.parquet")

    def save_model(run, name, columns):
        x = np.column_stack([training[f].to_numpy() for f in columns])
        model = xgb.train(
            {
                "device": "cpu",
                "nthread": 2,
                "seed": 47,
                "objective": "binary:logistic",
                "max_depth": 2,
                "min_child_weight": 0,
                "eta": 0.3,
            },
            xgb.DMatrix(
                x,
                label=training["fire_within_horizon"].to_numpy(),
                feature_names=columns,
                nthread=2,
            ),
            num_boost_round=4,
        )
        path = run / f"{name}.ubj"
        model.save_model(path)
        return file_sha256(path)

    for run, dataset, config, columns in (
        (args["previous_run"], args["previous_dataset"], old_cfg, FEATURES[::-1]),
        (args["current_run"], args["dataset"], cfg, FEATURES),
    ):
        digest = save_model(run, "frozen", columns)
        write_json(dataset / "report.json", {"config_sha256": "pending", "features": FEATURES})
        write_json(
            run / "plan.json",
            {
                "config_sha256": "pending",
                "features": FEATURES,
                "cases": [{"name": "frozen", "features": columns}],
                "source_hashes": {
                    e["id"]: sources[e["id"]]
                    for e in config["events"]
                    if e["split"] in ("train", "validation")
                },
            },
        )
        write_json(
            run / "report.json",
            {
                "plan_sha256": "pending",
                "profile": config["profile"],
                "selected": "frozen",
                "experiments": {"frozen": {"features": columns, "model_sha256": digest}},
            },
        )
    run = args["cv_run"]
    candidate = {"name": "chosen", "features": FEATURES}
    priors = {
        str(h): {"training_rows": 20, "training_positives": 10, "score": 0.5} for h in (1, 3, 6)
    }
    digest = save_model(run, "chosen", FEATURES)
    write_json(run / "chosen-cv.json", {"mean_event_horizon_ap": 0.7})
    write_json(
        run / "plan.json",
        {
            "config_sha256": "pending",
            "candidates": [candidate],
            "training_horizon_priors": priors,
            "source_hashes": {e["id"]: sources[e["id"]] for e in events if e["split"] == "train"},
        },
    )
    write_json(
        run / "selection.json",
        {
            "selected": "chosen",
            "plan_sha256": "pending",
            "cv_result_sha256": {"chosen": file_sha256(run / "chosen-cv.json")},
        },
    )
    write_json(
        run / "report.json",
        {
            "plan_sha256": "pending",
            "selection_sha256": "pending",
            "selected": "chosen",
            "models": {"chosen": {"candidate": candidate, "model_sha256": digest}},
            "training_horizon_priors": priors,
            "validation_source_hashes": {
                e["id"]: sources[e["id"]] for e in events if e["split"] == "validation"
            },
        },
    )
    rebind_metadata(args)
    return args


def test_same_validation_rows_with_feature_reordering_empty_and_single_class(inputs, monkeypatch):
    original_open = Path.open

    def guard_open(path, *args, **kwargs):
        assert "forbidden_" not in path.name
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guard_open)
    comparison.compare(**inputs)
    report = read_json(inputs["output"])
    assert len(report["shared_v3_parquets_exactly_identical"]) == 5
    assert len(report["eligible_cells"]) == 3
    assert len(report["validation"]) == 6
    for diagnostics in report["validation"].values():
        assert diagnostics["empty"]["1"]["rows"] == 0
        assert diagnostics["empty"]["1"]["average_precision"] is None
        assert diagnostics["positive_only"]["1"]["average_precision"] is None
        assert diagnostics["validation"]["1"]["rows"] == 4
    assert report["mean_event_horizon_ap"]["previous_v3"] == pytest.approx(
        report["mean_event_horizon_ap"]["expanded_v4_exploratory"]
    )
    prior = report["validation"]["constant_training_prior"]["positive_only"]["1"]
    assert prior["brier"] == pytest.approx(0.25)
    assert prior["logloss"] == pytest.approx(np.log(2))
    assert report["test_evaluated"] is report["operational_use"] is False
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize(
    "event,reason", [("train_extra", "학습 원본 SHA"), ("validation", "실제 비교 검증 행")]
)
def test_current_plan_source_mismatch_rejected_with_valid_outer_plan_hash(inputs, event, reason):
    path = inputs["current_run"] / "plan.json"
    plan = read_json(path)
    plan["source_hashes"][event] = "0" * 64
    write_json(path, plan)
    rebind_metadata(inputs)
    with pytest.raises(ValueError, match=reason):
        comparison.compare(**inputs)
    assert not inputs["output"].exists()


@pytest.mark.parametrize(
    "tamper,reason", [("other_plan", "자료/선택 계약"), ("changed_cv_result", "선택 근거의 SHA")]
)
def test_selection_requires_its_actual_plan_and_cv_results(inputs, tamper, reason):
    run = inputs["cv_run"]
    if tamper == "other_plan":
        modify(run / "selection.json", plan_sha256="0" * 64)
        modify(run / "report.json", selection_sha256=file_sha256(run / "selection.json"))
    else:
        modify(run / "chosen-cv.json", mean_event_horizon_ap=0.99)
    with pytest.raises(ValueError, match=reason):
        comparison.compare(**inputs)
    assert not inputs["output"].exists()


@pytest.mark.parametrize("location", ["shared_previous_event", "new_current_event"])
def test_locked_or_2025_train_event_rejected_before_parquet_access(inputs, monkeypatch, location):
    if location == "shared_previous_event":
        for name in ("previous_dataset", "dataset"):
            path = inputs[name] / "config.json"
            config = read_json(path)
            config["events"][0]["locked"] = True
            write_json(path, config)
        guarded_name = "train_a.parquet"
    else:
        path = inputs["dataset"] / "config.json"
        config = read_json(path)
        event = next(e for e in config["events"] if e["id"] == "forbidden_test_2025")
        event.update(split="train", locked=False)
        write_json(path, config)
        guarded_name = "forbidden_test_2025.parquet"
    rebind_metadata(inputs)
    original_open = Path.open

    def guard_open(path, *args, **kwargs):
        assert path.name != guarded_name, "forbidden data was accessed before its guard"
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guard_open)
    with pytest.raises(ValueError, match="잠긴 사건"):
        comparison.compare(**inputs)
    assert not inputs["output"].exists()


def test_booster_feature_order_must_match_declared_model_metadata(inputs):
    run = inputs["previous_run"]
    plan, report = read_json(run / "plan.json"), read_json(run / "report.json")
    plan["cases"][0]["features"] = FEATURES
    report["experiments"]["frozen"]["features"] = FEATURES
    write_json(run / "plan.json", plan)
    write_json(run / "report.json", report)
    rebind_metadata(inputs)
    with pytest.raises(ValueError, match="실제 모델의 피처 순서"):
        comparison.compare(**inputs)
