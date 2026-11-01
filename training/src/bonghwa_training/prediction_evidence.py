"""Past-only Korean fire-observation replay; produces research evidence, never response levels."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pyarrow as pa
import xgboost as xgb
from scipy.spatial import cKDTree

from bonghwa_training.download import file_sha256
from bonghwa_training.goes_build import input_snapshot, utc
from bonghwa_training.hourly_context import CONTEXT, Weather, context_for_table
from bonghwa_training.kma_event import read_event


def iso(epoch):
    return datetime.fromtimestamp(float(epoch), UTC).isoformat()


def finite(value):
    return float(value) if np.isfinite(value) else None


def score_horizons(model, features, values):
    """All horizons use exactly the same past input, including candidates with unknown outcomes."""
    if model.feature_names != features or "horizon_hours" not in features:
        raise ValueError("모델 피처 이름/순서가 계약과 다릅니다.")
    count = len(next(iter(values.values())))
    result = []
    for hours in (1, 3, 6):
        matrix = np.column_stack(
            [np.full(count, hours) if f == "horizon_hours" else values[f] for f in features]
        ).astype(np.float32)
        if np.isinf(matrix).any():
            raise ValueError("입력에 무한대 값이 있습니다.")
        scores = model.inplace_predict(matrix)
        if not np.isfinite(scores).all() or np.any((scores < 0) | (scores > 1)):
            raise ValueError("모델 점수가 유효하지 않습니다.")
        result.append(scores)
    result = np.column_stack(result)
    if np.any(np.diff(result, axis=1) < -1e-6):
        raise ValueError("1·3·6시간 누적 점수 단조성 위반")
    return result


def verified_run(run, dataset):
    report = json.loads((run / "report.json").read_text())
    plan = json.loads((run / "plan.json").read_text())
    cfg = json.loads((dataset / "config.json").read_text())
    data = json.loads((dataset / "report.json").read_text())
    if report["plan_sha256"] != file_sha256(run / "plan.json"):
        raise ValueError("학습 계획 SHA 불일치")
    if not plan["config_sha256"] == data["config_sha256"] == file_sha256(dataset / "config.json"):
        raise ValueError("모델/데이터 설정 SHA 불일치")
    if cfg.get("reader") != "gk2a" or report.get("operational_use") is not False:
        raise ValueError("국내 연구 전용 계약이 아닙니다.")
    name = report["selected"]
    if Path(name).name != name:
        raise ValueError("잘못된 모델 파일 이름")
    selected = report["experiments"][name]
    model_path = run / f"{name}.ubj"
    if file_sha256(model_path) != selected["model_sha256"]:
        raise ValueError("모델 SHA 불일치")
    model = xgb.Booster()
    model.load_model(model_path)
    model.set_param({"device": "cpu", "nthread": 2})
    return report, cfg, data, selected, model


def export(args):
    report, cfg, data, selected, model = verified_run(args.run, args.dataset)
    event = next(e for e in cfg["events"] if e["id"] == args.event)
    moment = utc(args.issue)
    if moment.tzinfo is None:
        raise ValueError("발행 시각에 UTC offset이 필요합니다.")
    if event["split"] == "test" or event.get("locked") or moment.year >= 2025:
        raise ValueError("잠긴 국내 최종 평가 사건은 재생할 수 없습니다.")
    issue = moment.timestamp()
    delay = cfg["assumed_input_delay_minutes"] * 60
    start = utc(event["start_utc"]).timestamp()
    if not start <= issue - delay < start + event["hours"] * 3600:
        raise ValueError("발행 시각이 사건 계약 범위 밖입니다.")
    raw = args.raw / "gk2a-ff"
    manifest_path = raw / event["id"] / "manifest.json"
    event_report = json.loads((args.dataset / f"{event['id']}-report.json").read_text())
    if file_sha256(manifest_path) != event_report["source_manifest_sha256"]:
        raise ValueError("재생 원본 manifest가 학습 자료와 다릅니다.")
    # The reader filters on assumed availability BEFORE opening any observation pixels.
    obs = read_event(raw, event, cfg, maximum_issue_epoch_seconds=issue)
    states, _, _, starts, _, available, grid, _ = obs
    if not len(starts) or available[-1] != issue:
        raise ValueError("해당 시각의 입력이 없습니다. 이전 관측으로 현재를 추정하지 않습니다.")
    snapshot = input_snapshot(obs, cfg, len(starts) - 1)
    manifest = json.loads(manifest_path.read_text())
    records = [
        r
        for r in manifest["files"]
        if utc(r["requested_observation_utc"]).timestamp() + delay <= issue
    ]
    records.sort(key=lambda r: r["requested_observation_utc"])
    latest = records[-1]
    actual = latest["schema"]["global_attributes"]
    features = selected["features"]
    registry_sha = file_sha256(args.raw / "weather/stations.json")
    if data.get("weather_station_registry_sha256", registry_sha) != registry_sha:
        raise ValueError("기상 관측소 등록부 SHA 불일치")
    rows, cols = (np.array([], dtype=int), np.array([], dtype=int))
    values, scores = {}, np.empty((0, 3))
    if snapshot is not None:
        rows, cols, values = snapshot
        table = pa.table(
            {
                **{k: np.asarray(v, dtype=np.float32) for k, v in values.items()},
                "latitude": grid["latitude"][rows, cols],
                "longitude": grid["longitude"][rows, cols],
                "issue_epoch_seconds": np.full(len(rows), issue),
            }
        )
        if set(features) & set(CONTEXT):
            static_path = args.static / "grid.npz"
            if file_sha256(static_path) != data["static_grid_sha256"]:
                raise ValueError("지형 자료 SHA 불일치")
            static = np.load(static_path)
            mask = static["country"]
            tree = cKDTree(np.column_stack((static["easting_m"][mask], static["northing_m"][mask])))
            weather = Weather(args.raw, moment.year)
            if weather.hashes != data["weather_files_sha256"][str(moment.year)]:
                raise ValueError("기상 자료 SHA 불일치")
            values.update(context_for_table(table, static, tree, weather))
            static.close()
        # Float32 matches the stored training representation; nulls remain missing, not zero.
        values = {k: np.asarray(v, dtype=np.float32) for k, v in values.items()}
        scores = score_horizons(model, features, values)
    candidate_index = {(int(r), int(c)): i for i, (r, c) in enumerate(zip(rows, cols, strict=True))}
    ranks = np.empty(scores.shape, dtype=int)
    for h in range(3):
        order = np.lexsort((cols, rows, -scores[:, h]))
        ranks[order, h] = np.arange(1, len(rows) + 1)
    cells = []
    for r, c in zip(*np.where(grid["inside_bbox"]), strict=True):
        state = int(states[-1, r, c])
        i = candidate_index.get((int(r), int(c)))
        reason = (
            "CURRENT_FIRE_OBSERVED"
            if state == 1
            else ("OBSERVATION_UNKNOWN" if state == -1 else "OUTSIDE_VISIBLE_FIRE_CANDIDATE_SCOPE")
        )
        cell = {
            "cell_id": f"{event['id']}:crop:{r}:{c}",
            "crop_row": int(r),
            "crop_col": int(c),
            "latitude": float(grid["latitude"][r, c]),
            "longitude": float(grid["longitude"][r, c]),
            "current_observation_state": {
                1: "fire_observed",
                0: "observed_nonfire_land",
                -1: "unknown",
            }[state],
            "status": "research_score" if i is not None else "unavailable",
            "reason_codes": [] if i is not None else [reason],
            "predictions": [
                {
                    "horizon_hours": h,
                    "raw_model_score": float(scores[i, j]) if i is not None else None,
                    "rank_within_snapshot": int(ranks[i, j]) if i is not None else None,
                    "calibrated_probability": None,
                }
                for j, h in enumerate((1, 3, 6))
            ],
        }
        if i is not None:
            cell["observed_features"] = {
                f: finite(values[f][i]) for f in features if f != "horizon_hours"
            }
            cell["missing_feature_names"] = [
                f for f, v in cell["observed_features"].items() if v is None
            ]
            cell["evidence_text_ko"] = (
                f"관측 시각 {iso(starts[-1])}. 이 약 2km 격자에서 비화재 육지가 관측됐으며, "
                "영역 내 가장 가까운 확정 화재 관측점은 "
                f"{values['distance_fire_km'][i]:.1f}km 떨어져 있습니다. "
                "1·3·6시간 연구 점수는 추가 확인 후보를 정렬하는 값이며 "
                "개인 피해 확률과 대응 단계는 미산출입니다."
            )
        cells.append(cell)
    evidence = {
        "schema_version": "wildfire-research-evidence-v1",
        "purpose": "historical_research",
        "operational_use": False,
        "used_for_response_level": False,
        "source_scope": "as_of_candidates",
        "future_outcome_pixels_read": False,
        "generated_at": datetime.now(UTC).isoformat(),
        "event_id": event["id"],
        "dataset_split": event["split"],
        "issue_at": iso(issue),
        "target": {
            "code": "gk2a_fire_observation_within_horizon",
            "meaning": cfg["target"],
            "spatial_unit": "nominal_2km_grid_cell",
            "horizons_hours": [1, 3, 6],
            "personal_harm_probability": None,
            "fire_arrival_time": None,
        },
        "model": {
            "run_id": args.run.name,
            "experiment": report["selected"],
            "sha256": selected["model_sha256"],
            "profile": report["profile"],
            "config_sha256": file_sha256(args.dataset / "config.json"),
            "report_sha256": file_sha256(args.run / "report.json"),
            "calibration_fitted": report["calibration_fitted"],
            "calibration_independently_validated": False,
            "calibration_applied": False,
        },
        "observation": {
            "observed_at": iso(starts[-1]),
            "historical_received_at": None,
            "archive_retrieved_at": latest["retrieved_at_utc"],
            "input_time_basis": "assumed_delay_not_actual_release",
            "source_product": "GK2A_FF_KO",
            "algorithm_version": actual.get("algorithm_version"),
            "processing_environment": actual.get("processing_environment"),
            "past_files_read": len(records),
            "source_manifest_sha256": file_sha256(manifest_path),
            "input_files": [
                {"observation_utc": r["requested_observation_utc"], "sha256": r["sha256"]}
                for r in records
            ],
        },
        "provenance": {
            "dataset_report_sha256": file_sha256(args.dataset / "report.json"),
            "static_grid_sha256": data.get("static_grid_sha256"),
            "weather_files_sha256": data.get("weather_files_sha256", {}).get(str(moment.year)),
            "weather_station_registry_sha256": registry_sha,
            "weather_station_registry_bound_at_training": "weather_station_registry_sha256" in data,
            "weather_time_basis": cfg.get("weather_time_basis"),
            "source_sha256": {
                name: file_sha256(Path(__file__).with_name(name))
                for name in (
                    "prediction_evidence.py",
                    "goes_build.py",
                    "hourly_context.py",
                    "kma_event.py",
                )
            },
        },
        "coverage": {
            "bbox": event["bbox"],
            "cells": len(cells),
            "scored_cells": len(rows),
            "unknown_cells": int(((states[-1] == -1) & grid["inside_bbox"]).sum()),
            "observed_fire_cells": int(((states[-1] == 1) & grid["inside_bbox"]).sum()),
        },
        "allowed_uses": ["historical_replay", "research_ranking", "additional_evidence_review"],
        "limitations": [
            "Scores and ranks are uncalibrated; no personal harm probability or response level.",
            "Unknown/cloud/outside-scope cells are unavailable, never zero risk.",
            "Ranks use the same issue/horizon/model; ties use crop row/col.",
            "Distance/change use detected points in this crop; they are not fire-front speed.",
            "Availability uses assumed delay; operating-product equivalence is unverified.",
            "Labels were future-observability selected; full-candidate skill is unverified.",
            "No user location or profile is matched; grid-cell outputs are not personal exposure.",
            *cfg.get("limitations", []),
        ],
        "cells": cells,
    }
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, allow_nan=False) + "\n"
    )
    geo = {
        "type": "FeatureCollection",
        "operational_use": False,
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [c["longitude"], c["latitude"]]},
                "properties": {
                    k: v
                    for k, v in c.items()
                    if k not in ("latitude", "longitude", "observed_features")
                },
            }
            for c in cells
        ],
    }
    (args.output / "cells.geojson").write_text(
        json.dumps(geo, ensure_ascii=False, allow_nan=False) + "\n"
    )
    preview = {k: v for k, v in evidence.items() if k != "cells"}
    preview["top_candidates_by_horizon"] = {
        str(h): sorted(
            [c for c in cells if c["status"] == "research_score"],
            key=lambda c: c["predictions"][j]["rank_within_snapshot"],
        )[:5]
        for j, h in enumerate((1, 3, 6))
    }
    (args.output / "summary.json").write_text(
        json.dumps(preview, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {"output": str(args.output), "coverage": evidence["coverage"]}, ensure_ascii=False
        )
    )
    return evidence


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("run", "dataset", "raw", "static", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--event", required=True)
    p.add_argument("--issue", required=True, help="UTC offset을 포함한 과거 발행 시각")
    export(p.parse_args())


if __name__ == "__main__":
    main()
