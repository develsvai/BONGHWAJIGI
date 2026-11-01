"""사건·기간 그룹 nested CV로 과거 화선의 1/3/6h 접근 분류를 비교한다.

사후 미국 위성 경계 연구이며 국내 개인 영향 확률이 아니다. 기존 2021
validation은 이미 노출된 개발 검증이다. 행 무작위 분할·test 재튜닝은 하지 않는다.
"""

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import perf_counter

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import xgboost as xgb
from scipy.optimize import minimize
from scipy.special import expit, logit

from bonghwa_training.approach_train import (
    FEATURES as LEGACY,
)
from bonghwa_training.approach_train import (
    HORIZONS,
    evaluate,
    known_labels,
    validate_intervals,
    write_json,
)
from bonghwa_training.download import file_sha256 as sha

FLAGS = {
    "operational_use": False,
    "retrospective_proxy_only": True,
    "source_asof_verified": False,
    "personal_harm_probability": False,
    "test_evaluated": False,
    "validation_previously_exposed": True,
}


def temporal_clusters(metadata):
    """Cluster overlapping fixed 78h event windows using metadata, never labels."""
    ordered = sorted(metadata, key=lambda e: (e["start_utc"], e["id"]))
    clusters, until, number = {}, None, -1
    for event in ordered:
        start = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00"))
        if start.tzinfo is None or start.year not in (2019, 2020):
            raise ValueError("훈련 cluster는 2019/2020 UTC metadata만 허용")
        if event["id"] in clusters:
            raise ValueError("중복 사건")
        if until is None or start > until:
            number += 1
            until = start + timedelta(hours=78)
        else:
            until = max(until, start + timedelta(hours=78))
        clusters[event["id"]] = f"period_{number:02d}"
    return clusters


def folds(names, clusters, count):
    grouped = {}
    for name in sorted(names):
        grouped.setdefault(clusters[name], []).append(name)
    if len(grouped) < count:
        raise ValueError("독립 시간 그룹이 CV fold보다 적음")
    bins = [[] for _ in range(count)]
    for _, group in sorted(grouped.items(), key=lambda x: (-len(x[1]), x[0])):
        slot = min(range(count), key=lambda i: (len(bins[i]), i))
        bins[slot].extend(group)
    result = []
    for held in bins:
        train = sorted(set(names) - set(held))
        if {clusters[n] for n in train} & {clusters[n] for n in held}:
            raise ValueError("기간 그룹이 훈련/평가에 중복")
        result.append((train, sorted(held)))
    return result


def load_events(dataset, config, split):
    if split not in ("train", "validation"):
        raise ValueError("허용하지 않은 데이터 구획")
    feature_names = config["feature_names"]
    if list(feature_names[:7]) != list(LEGACY) or len(set(feature_names)) != len(feature_names):
        raise ValueError("기존 7개 입력 및 신규 고유 feature 계약 필요")
    events = {}
    for meta in config["events"]:
        if meta.get("locked") or meta.get("split") != split:
            continue
        name = meta["id"]
        year = datetime.fromisoformat(meta["start_utc"].replace("Z", "+00:00")).year
        if (split == "train" and year not in (2019, 2020)) or (
            split == "validation" and year != 2021
        ):
            raise ValueError("연도 분할 위반")
        if Path(name).name != name or name in events:
            raise ValueError("사건 ID 중복/경로 오류")
        path = dataset / f"{name}.parquet"
        receipt = json.loads((dataset / f"{name}-report.json").read_text())
        if sha(path) != receipt["sha256"]:
            raise ValueError("데이터 해시 불일치")
        table = pq.read_table(path)
        if len(table) != receipt["rows"] or not len(table):
            raise ValueError("데이터 행 수 불일치")
        if set(table["event_id"].to_pylist()) != {name} or set(table["split"].to_pylist()) != {
            split
        }:
            raise ValueError("실제 행의 사건/구획 불일치")
        if any(table["current_approach"].to_pylist()):
            raise ValueError("현재 이미 접근한 지점 제외 필요")
        identities = list(
            zip(table["issue_time_utc"].to_pylist(), table["target_id"].to_pylist(), strict=True)
        )
        if len(set(identities)) != len(table):
            raise ValueError("중복 시점/대상 행")
        lower, upper = [
            table[c].to_numpy().astype(float) for c in ("label_lower_hours", "label_upper_hours")
        ]
        validate_intervals(lower, upper)
        x = np.column_stack([table[f].to_numpy() for f in feature_names]).astype("float32")
        if np.isinf(x).any() or not np.isfinite(x[:, 0]).all() or np.any(x[:, 0] <= 0):
            raise ValueError("feature 무한대/거리 오류")
        events[name] = {
            "x": x,
            "lower": lower,
            "upper": upper,
            "table": table,
            "sha256": receipt["sha256"],
        }
    if not events:
        raise ValueError("유효 사건 없음")
    return events


def candidates(all_features):
    options = [
        ("distance_d2", ["distance_km"], 2, 120),
        ("legacy_d2", list(LEGACY), 2, 150),
        ("legacy_d3", list(LEGACY), 3, 220),
        ("history_d2", all_features, 2, 150),
        ("history_d3", all_features, 3, 220),
        ("history_d4", all_features, 4, 260),
    ]
    return [
        {"name": name, "features": list(features), "depth": depth, "rounds": rounds}
        for name, features, depth, rounds in options
    ]


def expand(events, feature_names, chosen, labels):
    indices = [feature_names.index(f) for f in chosen]
    arrays, ys, weights = [], [], []
    for event in events.values():
        for h in HORIZONS:
            known, y = known_labels(event["lower"], event["upper"], h)
            keep = known if labels else np.ones(len(known), dtype=bool)
            if not keep.any():
                continue
            arrays.append(np.column_stack((event["x"][keep][:, indices], np.full(keep.sum(), h))))
            if labels:
                ys.append(y[keep])
                weights.append(np.full(keep.sum(), 1.0 / keep.sum()))
    if not arrays:
        raise ValueError("분류용 알려진 정답 없음")
    x = np.concatenate(arrays).astype("float32")
    y = np.concatenate(ys) if labels else None
    weight = np.concatenate(weights) if labels else None
    if labels:
        weight *= len(weight) / weight.sum()
        if len(np.unique(y)) != 2:
            raise ValueError("훈련 구획에 두 클래스 필요")
    return xgb.DMatrix(
        x, label=y, weight=weight, feature_names=[*chosen, "horizon_hours"], nthread=2
    )


def fit(events, feature_names, candidate):
    params = {
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "tree_method": "hist",
        "device": "cpu",
        "nthread": 2,
        "seed": 47,
        "max_depth": candidate["depth"],
        "eta": 0.05,
        "min_child_weight": 10,
        "lambda": 20,
        "alpha": 0.1,
        "max_bin": 256,
        "subsample": 1.0,
        "colsample_bytree": 1.0,
        "monotone_constraints": {"distance_km": -1, "horizon_hours": 1},
    }
    return xgb.train(
        params,
        expand(events, feature_names, candidate["features"], True),
        num_boost_round=candidate["rounds"],
        verbose_eval=False,
    )


def predict(model, events, feature_names, candidate):
    result = {}
    for name, event in events.items():
        d = expand({name: event}, feature_names, candidate["features"], False)
        values = model.predict(d).reshape(3, -1).T
        if (
            not np.isfinite(values).all()
            or np.any((values < 0) | (values > 1))
            or np.any(np.diff(values, axis=1) < -1e-7)
        ):
            raise ValueError("확률 범위/기간 단조성 오류")
        result[name] = values
    return result


def subset(events, names):
    return {n: events[n] for n in names}


def select(events, features, definitions, clusters, count, output, tag):
    split = folds(events, clusters, count)
    scores, predictions = [], {}
    for definition in definitions:
        oof = {}
        for train, held in split:
            model = fit(subset(events, train), features, definition)
            oof.update(predict(model, subset(events, held), features, definition))
        report = evaluate(events, oof)
        scores.append(
            {
                "candidate": definition["name"],
                "macro_ap": report["macro_eligible_event_horizon_ap"],
                "macro_brier": report["macro_nonempty_event_horizon_brier"],
                "eligible_event_horizons": report["eligible_ap_cells"],
            }
        )
        predictions[definition["name"]] = oof
        print(json.dumps({"stage": tag, **scores[-1]}), flush=True)
    chosen = max(range(len(scores)), key=lambda i: (scores[i]["macro_ap"], -i))
    receipt = {
        "folds": [{"train": a, "held": b} for a, b in split],
        "candidates": scores,
        "selected": definitions[chosen]["name"],
        "selection_metric": "eligible_event_horizon_macro_AP",
    }
    write_json(output / f"{tag}-selection.json", receipt)
    return definitions[chosen], predictions[definitions[chosen]["name"]], receipt


def flatten_known(events, predictions):
    ys, ps, ws = [], [], []
    for name, event in events.items():
        for index, h in enumerate(HORIZONS):
            known, y = known_labels(event["lower"], event["upper"], h)
            if known.any():
                ys.append(y[known])
                ps.append(predictions[name][known, index])
                ws.append(np.full(known.sum(), 1 / known.sum()))
    y, p, w = np.concatenate(ys), np.concatenate(ps), np.concatenate(ws)
    return y, p, w / w.sum()


def fit_calibration(events, predictions):
    y, p, weights = flatten_known(events, predictions)
    x = logit(np.clip(p, 1e-6, 1 - 1e-6))

    def objective(theta):
        a, b = theta
        z = a * x + b
        loss = np.sum(weights * (np.logaddexp(0, z) - y * z)) + 0.001 * (a - 1) ** 2
        residual = weights * (expit(z) - y)
        return loss, np.array([np.sum(residual * x) + 0.002 * (a - 1), np.sum(residual)])

    fitted = minimize(
        objective, [1.0, 0.0], jac=True, method="L-BFGS-B", bounds=[(0.0001, 10), (-20, 20)]
    )
    if not fitted.success or not np.isfinite(fitted.x).all():
        raise ValueError("양의 기울기 보정 적합 실패")
    return {
        "slope": float(fitted.x[0]),
        "intercept": float(fitted.x[1]),
        "method": "shared_positive_slope_sigmoid",
        "weighting": "equal_event_horizon",
        "objective": float(fitted.fun),
        "training_rows": len(y),
        "operational_validated": False,
    }


def calibrate(predictions, model):
    if not 0 < model["slope"] <= 10:
        raise ValueError("양의 보정 기울기 필요")
    result = {
        name: expit(model["slope"] * logit(np.clip(p, 1e-6, 1 - 1e-6)) + model["intercept"])
        for name, p in predictions.items()
    }
    if any(np.any(np.diff(p, axis=1) < -1e-7) for p in result.values()):
        raise ValueError("보정 후 기간 단조성 오류")
    return result


def threshold80(events, predictions):
    """Recall weighted by 1/n(event,h), not mean per-event recall; no new-event guarantee."""
    y, p, w = flatten_known(events, predictions)
    positive = y == 1
    if not positive.any():
        raise ValueError("임계값 학습 양성 없음")
    order = np.argsort(-p[positive], kind="stable")
    mass = np.cumsum(w[positive][order]) / w[positive].sum()
    index = np.searchsorted(mass, 0.8)
    return float(p[positive][order[index]])


def alert_metrics(events, predictions, thresholds):
    result = {}
    for name, event in events.items():
        result[name] = {}
        for i, h in enumerate(HORIZONS):
            known, y = known_labels(event["lower"], event["upper"], h)
            pred = predictions[name][known, i] >= thresholds[name]
            y = y[known].astype(bool)
            tp, fp, fn = int((pred & y).sum()), int((pred & ~y).sum()), int((~pred & y).sum())
            result[name][str(h)] = {
                "threshold": thresholds[name],
                "rows": len(y),
                "positives": int(y.sum()),
                "alerts": int(pred.sum()),
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "recall": tp / (tp + fn) if tp + fn else None,
                "precision": tp / (tp + fp) if tp + fp else None,
                "alert_fraction": float(pred.mean()) if len(pred) else None,
            }
    return result


def distance_scores(events):
    return {n: np.repeat(-e["x"][:, :1], 3, axis=1) for n, e in events.items()}


def cluster_scores(events, predictions, clusters, probability=True):
    result = {}
    for group in sorted(set(clusters[n] for n in events)):
        names = [n for n in events if clusters[n] == group]
        result[group] = evaluate(subset(events, names), subset(predictions, names), probability)
    return result


def dump_predictions(events, raw, calibrated, path):
    tables = []
    for name, event in events.items():
        data = {c: event["table"][c] for c in ("event_id", "issue_time_utc", "target_id")}
        for i, h in enumerate(HORIZONS):
            data[f"raw_{h}h"] = raw[name][:, i]
            data[f"calibrated_{h}h"] = calibrated[name][:, i]
        tables.append(pa.table(data))
    pq.write_table(pa.concat_tables(tables), path, compression="zstd")


def run(dataset, output):
    started = perf_counter()
    config = json.loads((dataset / "config.json").read_text())
    if (
        config.get("target") != "gofer_reconstructed_perimeter_first_approach"
        or config.get("retrospective_proxy_only") is not True
        or config.get("operational_use") is not False
        or config.get("source_asof_verified") is not False
        or config["settings"].get("radius_km") != 2
        or config["settings"].get("max_issue_hours") != 72
        or config["settings"].get("horizon_hours") != 6
    ):
        raise ValueError("고정 GOFER 사후 연구·2km·72h/6h 계약 필요")
    features = config["feature_names"]
    if any(
        f in features
        for f in (
            "event_id",
            "issue_time_utc",
            "target_longitude",
            "target_latitude",
            "year",
            "horizon_hours",
        )
    ):
        raise ValueError("사건/절대시각/좌표를 모델에 사용하지 않음")
    definitions = candidates(features)
    clusters = temporal_clusters([e for e in config["events"] if e["split"] == "train"])
    output.mkdir(parents=True, exist_ok=False)
    plan = FLAGS | {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "dataset_config_sha256": sha(dataset / "config.json"),
        "source_sha256": sha(Path(__file__)),
        "source": config.get("source"),
        "horizons_hours": list(HORIZONS),
        "research_radius_km": config["settings"]["radius_km"],
        "candidates": definitions,
        "period_clusters": clusters,
        "outer_folds": 4,
        "inner_folds": 3,
        "model": "Shared-horizon binary XGBoost; distance decreasing, horizon increasing",
        "selection": "Nested period-group CV macro AP; final4fold CV; no validation tuning",
        "weights": "Every event/horizon equal total weight, no positive class oversampling",
        "calibration": "Positive-slope common sigmoid fitted only on inner OOF; never outer labels",
        "threshold": (
            "Inner-OOF sample-weighted recall80 using 1/n(event,h); "
            "not macro per-event recall; no new-event recall guarantee"
        ),
        "calibration_variant_selection": "None; raw and calibrated both reported",
        "max_booster_fits": 101,
        "nthread": 2,
        "device": "cpu",
        "primary_evidence": (
            "Nested held-period comparison; 2021 is previously exposed development validation"
        ),
        "limitations": config.get("limitations", []),
        "calibration_population": (
            "Equal event/horizon research grid; not a user or operational population probability"
        ),
    }
    write_json(output / "plan.json", plan)
    training = load_events(dataset, config, "train")
    all_raw, all_cal, outer_reports, threshold_sets = (
        {},
        {},
        [],
        {"raw": {}, "calibrated": {}, "distance": {}},
    )
    for index, (train_names, held_names) in enumerate(folds(training, clusters, 4)):
        train, held = subset(training, train_names), subset(training, held_names)
        selected, inner_oof, selection = select(
            train, features, definitions, clusters, 3, output, f"outer{index}-inner"
        )
        mapping = fit_calibration(train, inner_oof)
        inner_cal = calibrate(inner_oof, mapping)
        thresholds = {
            "raw": threshold80(train, inner_oof),
            "calibrated": threshold80(train, inner_cal),
            "distance": threshold80(train, distance_scores(train)),
        }
        model = fit(train, features, selected)
        path = output / f"outer{index}.ubj"
        model.save_model(path)
        raw = predict(model, held, features, selected)
        calibrated = calibrate(raw, mapping)
        all_raw.update(raw)
        all_cal.update(calibrated)
        for kind, threshold in thresholds.items():
            threshold_sets[kind].update(dict.fromkeys(held_names, threshold))
        outer_reports.append(
            {
                "fold": index,
                "train": train_names,
                "held": held_names,
                "selected": selected,
                "selection": selection,
                "calibration": mapping,
                "thresholds": thresholds,
                "model_sha256": sha(path),
            }
        )
        write_json(output / "outer-progress.json", outer_reports)
    baseline = distance_scores(training)
    nested = {
        "raw": evaluate(training, all_raw),
        "calibrated": evaluate(training, all_cal),
        "negative_current_distance": evaluate(training, baseline, False),
        "clusters": {
            "raw": cluster_scores(training, all_raw, clusters),
            "calibrated": cluster_scores(training, all_cal, clusters),
            "distance": cluster_scores(training, baseline, clusters, False),
        },
        "operating_points": {
            "raw": alert_metrics(training, all_raw, threshold_sets["raw"]),
            "calibrated": alert_metrics(training, all_cal, threshold_sets["calibrated"]),
            "distance": alert_metrics(training, baseline, threshold_sets["distance"]),
        },
        "note": (
            "Each outer period excluded from selection, calibration and threshold fit; "
            f"only {len(set(clusters.values()))} temporal clusters; independence unproven"
        ),
    }
    write_json(output / "nested-evaluation.json", nested)
    dump_predictions(training, all_raw, all_cal, output / "nested-predictions.parquet")
    selected, oof, selection = select(training, features, definitions, clusters, 4, output, "final")
    mapping = fit_calibration(training, oof)
    cal_oof = calibrate(oof, mapping)
    thresholds = {
        "raw": threshold80(training, oof),
        "calibrated": threshold80(training, cal_oof),
        "distance": threshold80(training, distance_scores(training)),
    }
    model = fit(training, features, selected)
    path = output / "selected.ubj"
    model.save_model(path)
    reloaded = xgb.Booster()
    reloaded.load_model(path)
    reloaded.set_param({"device": "cpu", "nthread": 2})
    before = predict(model, training, features, selected)
    after = predict(reloaded, training, features, selected)
    reload_difference = max(float(np.max(np.abs(before[n] - after[n]))) for n in training)
    if reload_difference > 1e-7:
        raise ValueError("저장/재로딩 불일치")
    receipt = {
        "plan_sha256": sha(output / "plan.json"),
        "selected": selected,
        "selection": selection,
        "calibration": mapping,
        "thresholds": thresholds,
        "model_sha256": sha(path),
        "training_hashes": {n: e["sha256"] for n, e in training.items()},
        "reload_max_difference": reload_difference,
        "validation_read_before_receipt_in_this_run": False,
        "prior_validation_exposure_acknowledged": True,
    }
    write_json(output / "fit-receipt.json", receipt)
    validation = load_events(dataset, config, "validation")
    raw = predict(reloaded, validation, features, selected)
    calibrated = calibrate(raw, mapping)
    distance = distance_scores(validation)
    result = {
        "raw": evaluate(validation, raw),
        "calibrated": evaluate(validation, calibrated),
        "negative_current_distance": evaluate(validation, distance, False),
        "operating_points": {
            k: alert_metrics(validation, p, dict.fromkeys(validation, thresholds[k]))
            for k, p in (("raw", raw), ("calibrated", calibrated), ("distance", distance))
        },
    }
    dump_predictions(validation, raw, calibrated, output / "validation-predictions.parquet")
    for name, event in (training | validation).items():
        if sha(dataset / f"{name}.parquet") != event["sha256"]:
            raise ValueError("학습 중 원자료 변경")
    if (
        sha(dataset / "config.json") != plan["dataset_config_sha256"]
        or sha(Path(__file__)) != plan["source_sha256"]
    ):
        raise ValueError("실행 중 config/코드 변경")
    report = FLAGS | {
        "plan_sha256": sha(output / "plan.json"),
        "fit_receipt_sha256": sha(output / "fit-receipt.json"),
        "selected": selected,
        "calibration": mapping,
        "thresholds": thresholds,
        "nested_evaluation": nested,
        "validation": result,
        "outer_fits": outer_reports,
        "training_rows": sum(len(e["lower"]) for e in training.values()),
        "validation_rows": sum(len(e["lower"]) for e in validation.values()),
        "validation_hashes": {n: e["sha256"] for n, e in validation.items()},
        "model_sha256": sha(path),
        "reload_max_difference": reload_difference,
        "probability_calibration_fitted": True,
        "probability_operationally_validated": False,
        "xgboost": xgb.__version__,
        "elapsed_seconds": round(perf_counter() - started, 3),
        "completed_at_utc": datetime.now(UTC).isoformat(),
    }
    write_json(output / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.dataset, args.output)
    print(
        json.dumps(
            {"selected": report["selected"]["name"], "elapsed_seconds": report["elapsed_seconds"]}
        )
    )


if __name__ == "__main__":
    main()
