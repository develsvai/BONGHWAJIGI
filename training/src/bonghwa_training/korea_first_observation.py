"""Train-only GK2A observation cohorts, preserving unknown future outcomes.

Reconstruct every original input-time candidate, then attach observation audits.
No observation transition is a physical ignition/arrival or survival-time label.
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from scipy.spatial import cKDTree

from bonghwa_training import goes_build, hourly_context, kma_event
from bonghwa_training.download import file_sha256

TRAIN_IDS = frozenset(
    "andong_2020 andong_2021 hapcheon_2022 uljin_2022 ulju_2020 goseong_2020 "
    "yeongdeok_2022 yeongwol_2022 gangneung_donghae_2022 bonghwa_2022 "
    "yanggu_2022 gunwi_2022 uljin_may_2022 miryang_2022".split()
)
PROFILE = "kor_gk2a_first_future_observation_train_only_v1"
SOURCE_PROFILE = "kor_gk2a_10min_approach_hindcast_1_3_6h_v4_expanded_context_v1"
STATIC_SHA = "e31c0ed8bc1df421f6201b0aca0af0ea1f9e52b1a878d3fa93cfeb0086f9c60a"
REGISTRY_SHA = "df0645691d7c1ff7d7457b46b16636f37cce73b98f3a908c20428b230d1f8927"
HORIZONS = (1, 3, 6)
CADENCE = 600
ADDITIONAL_FEATURES = [
    "actual_history_30m_minutes",
    "actual_history_60m_minutes",
    "actual_closing_speed_30m_kmh",
    "actual_closing_speed_60m_kmh",
    *[
        f"history_{minutes}m_{name}"
        for minutes in (60, 120)
        for name in ("clear_count", "fire_count", "unknown_count", "source_coverage_fraction")
    ],
]


def write_json(path, value):
    with path.open("x") as output:
        output.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def at_times(states, starts, requested, rr, cc):
    """Missing scheduled files stay unknown, never interpolate a state."""
    requested = np.asarray(requested, dtype=float)
    indices = np.searchsorted(starts, requested)
    exists = indices < len(starts)
    exists[exists] &= starts[indices[exists]] == requested[exists]
    values = np.full((len(requested), len(rr)), -1, dtype=np.int8)
    values[exists] = states[indices[exists]][:, rr, cc]
    return values, exists


def input_history(observations, cfg, index, rr, cc, base):
    state, _, _, starts, ends, available, _, _ = observations
    scan, issue = starts[index], available[index]
    valid = (available <= issue) & (ends <= issue)
    if not valid[index] or np.any(np.diff(starts) <= 0):
        raise ValueError("invalid input-time observation ordering")
    extra, histories = {}, {}
    for minutes in (60, 120):
        requested = np.arange(scan - minutes * 60, scan + 1, CADENCE)
        values, exists = at_times(state[valid], starts[valid], requested, rr, cc)
        prefix = f"history_{minutes}m_"
        for name, code in (("clear", 0), ("fire", 1), ("unknown", -1)):
            extra[prefix + name + "_count"] = (values == code).sum(axis=0)
        extra[prefix + "source_coverage_fraction"] = np.full(len(rr), exists.mean())
        histories[minutes] = {
            "all_clear": np.all(values == 0, axis=0),
            "observed_fire": np.any(values == 1, axis=0),
            "source_complete": np.full(len(rr), exists.all()),
        }
    for minutes in (30, 60):
        prior = np.flatnonzero(valid & (ends <= issue - minutes * 60))
        elapsed = np.nan
        if len(prior) and ends[prior[-1]] >= issue - (minutes + 10) * 60:
            elapsed = (ends[index] - ends[prior[-1]]) / 60
            if elapsed <= 0:
                raise ValueError("nonpositive actual history interval")
        extra[f"actual_history_{minutes}m_minutes"] = np.full(len(rr), elapsed)
        extra[f"actual_closing_speed_{minutes}m_kmh"] = (
            (base[f"distance_fire_{minutes}m_km"] - base["distance_fire_km"]) * 60 / elapsed
        )
    flags = {
        "cohort_primary_clear60": histories[60]["all_clear"] & ~histories[120]["observed_fire"],
        "cohort_sensitivity_clear120": histories[120]["all_clear"],
        "history_fire_observed_120m": histories[120]["observed_fire"],
        "history_120m_source_complete": histories[120]["source_complete"],
        "history_clear60": histories[60]["all_clear"],
    }
    return extra, flags


def observation_outcome(observations, index, rr, cc, horizon):
    """Outcome/audit only. None of these columns can enter feature_names or cohorts."""
    states, _, _, starts, _, available, _, _ = observations
    scan, issue = starts[index], available[index]
    end = issue + horizon * 3600
    requested = np.arange((np.floor(issue / CADENCE) + 1) * CADENCE, end + 1, CADENCE)
    values, exists = at_times(states, starts, requested, rr, cc)
    if len(requested) != horizon * 6:
        raise ValueError("unexpected future scan schedule")
    positive = np.any(values == 1, axis=0)
    known_negative = np.all(values == 0, axis=0)
    target = np.where(positive, 1, np.where(known_negative, 0, -1)).astype(np.int8)
    first_index = np.argmax(values == 1, axis=0)
    first_fire = np.where(positive, requested[first_index], np.nan)
    last_clear = np.full(len(rr), scan)
    for j, time in enumerate(requested):
        last_clear[(values[j] == 0) & positive & (time < first_fire)] = time
    lower = np.where(positive, last_clear, np.nan)
    # Post-issue sampled clear follow-up only; the blind-gap audit is excluded.
    # This ends at the first unknown/fire scan, not at the last later clear scan.
    censor_end = np.full(len(rr), scan)
    still_clear = np.ones(len(rr), dtype=bool)
    for j, time in enumerate(requested):
        still_clear &= values[j] == 0
        censor_end[still_clear] = time
    blind_times = np.arange(scan + CADENCE, issue + 1, CADENCE)
    blind, blind_exists = at_times(states, starts, blind_times, rr, cc)
    unavailable = (starts > scan) & (starts <= issue) & (available <= issue)
    if unavailable.any():
        raise ValueError("blind-gap audit unexpectedly contains available observations")
    return {
        "observed_fire_within_horizon": target,
        "target_known": target >= 0,
        "audit_future_clear_count": (values == 0).sum(axis=0),
        "audit_future_fire_count": (values == 1).sum(axis=0),
        "audit_future_unknown_count": (values == -1).sum(axis=0),
        "audit_future_source_complete": np.full(len(rr), exists.all()),
        "audit_first_future_fire_observed_epoch_seconds": first_fire,
        "audit_first_future_fire_observed_lead_hours": (first_fire - issue) / 3600,
        "audit_observation_transition_lower_epoch_seconds": lower,
        "audit_observation_transition_upper_epoch_seconds": first_fire,
        "audit_observation_transition_lower_lead_hours": (lower - issue) / 3600,
        "audit_observation_transition_upper_lead_hours": (first_fire - issue) / 3600,
        "audit_transition_lower_before_issue": positive & (lower < issue),
        "audit_contiguous_clear_followup_end_epoch_seconds": censor_end,
        "audit_contiguous_clear_followup_lead_hours": (censor_end - issue) / 3600,
        "audit_blind_gap_fire_observed": np.any(blind == 1, axis=0),
        "audit_blind_gap_fully_clear": np.all(blind == 0, axis=0)
        & np.full(len(rr), blind_exists.all()),
        "audit_future_status": np.where(
            positive,
            "positive_observation",
            np.where(known_negative, "clear_sampled_horizon", "unknown_followup"),
        ),
        "survival_training_eligible": np.zeros(len(rr), dtype=bool),
    }


def preflight(args):
    cfg = json.loads(args.config.read_text())
    if cfg.get("profile") != SOURCE_PROFILE or cfg.get("reader") != "gk2a":
        raise ValueError("fixed source context profile required")
    for name, expected in (
        ("horizons_hours", [1, 3, 6]),
        ("source_cadence_minutes", 10),
        ("input_interval_minutes", 20),
        ("candidate_distance_km", 30),
        ("assumed_input_delay_minutes", 15),
    ):
        if cfg.get(name) != expected:
            raise ValueError("fixed original candidate/time convention changed")
    training = [e for e in cfg["events"] if e.get("split") == "train"]
    if len(training) != 14 or {e["id"] for e in training} != TRAIN_IDS:
        raise ValueError("exact 14 train-window allowlist required")
    if file_sha256(args.config) != file_sha256(args.reference / "config.json"):
        raise ValueError("reference config mismatch")
    source_hashes = {
        str(args.config): file_sha256(args.config),
        str(args.reference / "config.json"): file_sha256(args.config),
    }
    manifests = {}
    for event in training:
        start = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00"))
        if start.tzinfo is None or start.year not in (2020, 2021, 2022) or event.get("locked"):
            raise ValueError("non-train year or locked event")
        path = args.raw / event["id"] / "manifest.json"
        manifest = json.loads(path.read_text())
        if manifest["event"] != event:
            raise ValueError("raw manifest event contract changed")
        source_hashes[str(path)] = file_sha256(path)
        times = []
        for record in manifest["files"]:
            time = datetime.fromisoformat(record["requested_observation_utc"])
            raw_path = Path(record["path"])
            expected = args.raw / f"gk2a-ff-ko-{time:%Y%m%d%H%M}Z.nc"
            if (
                time.tzinfo is None
                or time.year not in (2020, 2021, 2022)
                or not start.timestamp() - 3600 <= time.timestamp() < start.timestamp() + 19 * 3600
                or raw_path.is_symlink()
                or raw_path.resolve() != expected.resolve()
            ):
                raise ValueError("raw source outside fixed train time/path allowlist")
            if file_sha256(raw_path) != record["sha256"]:
                raise ValueError("raw source SHA mismatch")
            source_hashes[str(raw_path)] = record["sha256"]
            times.append(time.timestamp())
        if not times or len(times) != len(set(times)) or any(t % CADENCE for t in times):
            raise ValueError("invalid source scan schedule")
        ref_path = args.reference / f"{event['id']}.parquet"
        report_path = args.reference / f"{event['id']}-report.json"
        report = json.loads(report_path.read_text())
        if report["event"] != event or file_sha256(ref_path) != report["sha256"]:
            raise ValueError("immutable v4 reference contract mismatch")
        if report["source_manifest_sha256"] != source_hashes[str(path)]:
            raise ValueError("v4 source manifest changed")
        source_hashes[str(ref_path)] = report["sha256"]
        source_hashes[str(report_path)] = file_sha256(report_path)
        manifests[event["id"]] = {
            "frames": len(times),
            "first_scan_epoch_seconds": min(times),
            "last_scan_epoch_seconds": max(times),
            "manifest_sha256": source_hashes[str(path)],
        }
    if file_sha256(args.static / "grid.npz") != STATIC_SHA:
        raise ValueError("original static grid SHA mismatch")
    if file_sha256(args.weather_raw / "weather/stations.json") != REGISTRY_SHA:
        raise ValueError("original station registry SHA mismatch")
    source_hashes[str(args.static / "grid.npz")] = STATIC_SHA
    source_hashes[str(args.weather_raw / "weather/stations.json")] = REGISTRY_SHA
    for year in (2020, 2021, 2022):
        path = args.weather_raw / f"weather-manifest-{year}.json"
        source_hashes[str(path)] = file_sha256(path)
        for record in json.loads(path.read_text()):
            if "sha256" not in record:
                continue
            name = Path(record["path"]).name
            if not name.endswith(f"-{year}.gz"):
                raise ValueError("weather source year mismatch")
            weather_path = args.weather_raw / "weather" / str(year) / name
            if file_sha256(weather_path) != record["sha256"]:
                raise ValueError("weather source SHA mismatch")
            source_hashes[str(weather_path)] = record["sha256"]
    features = [f for f in cfg["feature_names"] if f not in cfg["drop_features"]]
    if len(features) != 34 or any(f.startswith("audit_") for f in features):
        raise ValueError("fixed 34 input features required")
    cfg = {**cfg, "events": training}
    sources = [
        Path(__file__),
        Path(goes_build.__file__),
        Path(hourly_context.__file__),
        Path(kma_event.__file__),
        Path(__file__).with_name("download.py"),
    ]
    plan = {
        "profile": PROFILE,
        "source_config_sha256": file_sha256(args.config),
        "source_hashes": source_hashes,
        "code_sha256": {p.name: file_sha256(p) for p in sources},
        "train_events": training,
        "manifests": manifests,
        "base_features": features,
        "feature_names": features + ADDITIONAL_FEATURES,
        "primary_cohort": (
            "7 scheduled scans [last_available_scan-60m,last_available_scan] all clear; "
            "no observed fire in preceding120m"
        ),
        "sensitivity_cohort": (
            "13 scheduled scans [last_available_scan-120m,last_available_scan] all clear"
        ),
        "cohort_time_basis": (
            "only source available<=issue; scan+15m assumed availability, "
            "not historical measured publication time"
        ),
        "history_missing": (
            "missing file or unknown pixel stays unknown; "
            "source coverage and observed-fire history retained"
        ),
        "target": (
            "any confirmed future sampled GK2A fire=1; "
            "every scheduled future scan present/clear=0; otherwise -1"
        ),
        "transition_interval": (
            "last clear scan to first future positive observation; "
            "not an ignition/arrival interval; negative lower leads retained"
        ),
        "censor_audit": (
            "post-issue sampled schedule only; blind-gap excluded; contiguous clear "
            "followup stops at first unknown/fire; later clear cannot fill that gap"
        ),
        "blind_gap": (
            "last available scan to issue is15m; "
            "retrospective gap fire audit cannot affect inputs/cohorts"
        ),
        "candidate_rule": (
            "original current-clear/current-fire-distance<=30km, every20m, "
            "original12h event windows; all candidates x1/3/6h retained"
        ),
        "context_rule": (
            "regenerate existing static and past-only2020/21/22 ISD for all input candidates; "
            "never join future-selected v4 feature missingness"
        ),
        "original_reference": (
            "v4 source immutable; old identity/known label/base34 feature equivalence "
            "audited after construction"
        ),
        "survival_training_eligible": False,
        "validation_read": False,
        "calibration_read": False,
        "test_evaluated": False,
        "probability_calibrated": False,
        "operational_use": False,
    }
    return cfg, plan


def reference_lookup(reference, event, features):
    path = reference / f"{event['id']}.parquet"
    table = pq.read_table(
        path, columns=[*features, "fire_within_horizon", "row", "col", "issue_epoch_seconds"]
    )
    identity = list(
        zip(
            table["issue_epoch_seconds"].to_pylist(),
            table["horizon_hours"].to_pylist(),
            table["row"].to_pylist(),
            table["col"].to_pylist(),
            strict=True,
        )
    )
    if len(set(identity)) != len(identity):
        raise ValueError("duplicate original v4 row")
    return {key: i for i, key in enumerate(identity)}, table


def build_event(args, cfg, plan, event, grid, tree, weather):
    observations = kma_event.read_event(args.raw, event, cfg)
    states, _, _, starts, _, available, source_grid, _ = observations
    if np.any(np.diff(starts) <= 0) or np.any(available != starts + 900):
        raise ValueError("unexpected source time convention")
    original, reference = reference_lookup(args.reference, event, plan["base_features"])
    reference_x = np.column_stack([reference[f].to_numpy() for f in plan["base_features"]])
    reference_y = reference["fire_within_horizon"].to_numpy()
    seen = set()
    initial = datetime.fromisoformat(event["start_utc"].replace("Z", "+00:00")).timestamp()
    path = args.output / f"{event['id']}.parquet"
    writer = None
    stats = {
        "event": event,
        "anchors": 0,
        "rows": 0,
        "original_v4_rows": len(reference),
        "matched_v4_rows": 0,
        "base_feature_max_abs_difference": 0.0,
        "horizons": {str(h): {} for h in HORIZONS},
    }
    for index, scan in enumerate(starts):
        if not initial <= scan < initial + event["hours"] * 3600 or scan % 1200:
            continue
        snapshot = goes_build.input_snapshot(observations, cfg, index)
        if snapshot is None:
            continue
        rr, cc, base = snapshot
        issue, count = available[index], len(rr)
        extra, flags = input_history(observations, cfg, index, rr, cc, base)
        coordinates = {
            "latitude": source_grid["latitude"][rr, cc],
            "longitude": source_grid["longitude"][rr, cc],
            "row": rr.astype(np.int32),
            "col": cc.astype(np.int32),
            "issue_epoch_seconds": np.full(count, issue),
            "max_input_available_epoch_seconds": np.full(count, issue),
            "last_available_scan_epoch_seconds": np.full(count, scan),
            "pre_issue_blind_gap_minutes": np.full(count, (issue - scan) / 60),
        }
        # Match original v4: base geometry was serialized as float32 before context.
        context_input = {name: np.asarray(value, dtype=np.float32) for name, value in base.items()}
        context = hourly_context.context_for_table(
            pa.table({**context_input, **coordinates}), grid, tree, weather
        )
        inputs = {
            name: np.asarray(value, dtype=np.float32)
            for name, value in {**base, **context, **extra}.items()
        }
        for horizon in HORIZONS:
            columns = {
                **inputs,
                "horizon_hours": np.full(count, horizon, dtype=np.float32),
                **coordinates,
                **flags,
            }
            # Labels are attached only after input/cohort construction is complete.
            columns.update(observation_outcome(observations, index, rr, cc, horizon))
            identities = [
                (issue, horizon, int(row), int(col)) for row, col in zip(rr, cc, strict=True)
            ]
            matches = np.array([original.get(key, -1) for key in identities])
            known = columns["target_known"]
            if not np.array_equal(matches >= 0, known):
                raise ValueError("original v4 known-row membership changed")
            selected = matches[known]
            if not np.array_equal(
                reference_y[selected], columns["observed_fire_within_horizon"][known]
            ):
                raise ValueError("original v4 target changed")
            x = np.column_stack([columns[f] for f in plan["base_features"]])[known]
            old_x = reference_x[selected]
            if not np.array_equal(np.isnan(x), np.isnan(old_x)) or not np.allclose(
                x, old_x, rtol=0, atol=1e-6, equal_nan=True
            ):
                raise ValueError("original v4 input feature mismatch")
            finite = np.isfinite(x) & np.isfinite(old_x)
            if finite.any():
                stats["base_feature_max_abs_difference"] = max(
                    stats["base_feature_max_abs_difference"],
                    float(np.max(np.abs(x[finite] - old_x[finite]))),
                )
            for key, matched in zip(identities, matches, strict=True):
                if matched >= 0:
                    if key in seen:
                        raise ValueError("duplicate rebuilt reference row")
                    seen.add(key)
            columns["audit_old_v4_row_matched"] = matches >= 0
            columns["audit_old_v4_target"] = np.where(
                known, columns["observed_fire_within_horizon"], -1
            )
            columns["input_time_basis"] = ["assumed_delay_not_actual_release"] * count
            table = pa.table(columns)
            if writer is None:
                writer = pq.ParquetWriter(path, table.schema, compression="zstd")
            writer.write_table(table)
            stats["rows"] += count
            cell = stats["horizons"][str(horizon)]
            for cohort, mask in (
                ("all_candidates", np.ones(count, bool)),
                ("primary_clear60", flags["cohort_primary_clear60"]),
                ("sensitivity_clear120", flags["cohort_sensitivity_clear120"]),
                ("prior_fire_120m", flags["history_fire_observed_120m"]),
            ):
                counts = cell.setdefault(
                    cohort,
                    {
                        "rows": 0,
                        "positive": 0,
                        "negative": 0,
                        "unknown": 0,
                        "blind_gap_fire_observed": 0,
                        "source120_incomplete": 0,
                    },
                )
                counts["rows"] += int(mask.sum())
                for name, value in (("positive", 1), ("negative", 0), ("unknown", -1)):
                    counts[name] += int(
                        (mask & (columns["observed_fire_within_horizon"] == value)).sum()
                    )
                counts["blind_gap_fire_observed"] += int(
                    (mask & columns["audit_blind_gap_fire_observed"]).sum()
                )
                counts["source120_incomplete"] += int(
                    (mask & ~flags["history_120m_source_complete"]).sum()
                )
        stats["anchors"] += 1
    if writer is not None:
        writer.close()
    else:
        # A fully empty event must remain explicit and must not be fabricated as negatives.
        raise ValueError("no input candidates; empty event schema requires explicit handling")
    if len(seen) != len(reference):
        raise ValueError("not all original train rows were preserved")
    stats.update(
        matched_v4_rows=len(seen),
        sha256=file_sha256(path),
        survival_training_eligible=False,
        operational_use=False,
    )
    write_json(args.output / f"{event['id']}-report.json", stats)
    return stats


def build(args):
    cfg, plan = preflight(args)
    if args.plan_only:
        args.output.mkdir(parents=True, exist_ok=False)
        write_json(
            args.output / "plan.json", {"created_at_utc": datetime.now(UTC).isoformat(), **plan}
        )
        return {"status": "plan_frozen", "train_events": len(cfg["events"])}
    frozen = json.loads((args.output / "plan.json").read_text())
    frozen.pop("created_at_utc")
    if frozen != plan:
        raise ValueError("frozen plan/source changed")
    plan_sha = file_sha256(args.output / "plan.json")
    write_json(
        args.output / "started.json",
        {"at_utc": datetime.now(UTC).isoformat(), "plan_sha256": plan_sha},
    )
    output_cfg = {
        **cfg,
        "profile": PROFILE,
        "feature_names": plan["feature_names"],
        "target_column": "observed_fire_within_horizon",
        "unknown_target_value": -1,
        "input_feature_allowlist": plan["feature_names"],
        "survival_training_eligible": False,
        "operational_use": False,
    }
    write_json(args.output / "config.json", output_cfg)
    grid = np.load(args.static / "grid.npz")
    mask = grid["country"]
    tree = cKDTree(np.column_stack((grid["easting_m"][mask], grid["northing_m"][mask])))
    weather, reports = {}, {}
    try:
        for event in cfg["events"]:
            year = int(event["start_utc"][:4])
            if year not in weather:
                weather[year] = hourly_context.Weather(args.weather_raw, year)
            reports[event["id"]] = build_event(args, cfg, plan, event, grid, tree, weather[year])
            print(
                json.dumps(
                    {
                        "event": event["id"],
                        "rows": reports[event["id"]]["rows"],
                        "completed": len(reports),
                    }
                ),
                flush=True,
            )
        checks = {
            **plan["source_hashes"],
            **{
                str(Path(__file__).with_name(name)): sha
                for name, sha in plan["code_sha256"].items()
            },
            str(args.output / "plan.json"): plan_sha,
        }
        if any(file_sha256(Path(path)) != digest for path, digest in checks.items()):
            raise ValueError("source/code/plan changed during build")
        report = {
            "profile": PROFILE,
            "status": "completed",
            "plan_sha256": plan_sha,
            "events": reports,
            "rows": sum(r["rows"] for r in reports.values()),
            "matched_v4_rows": sum(r["matched_v4_rows"] for r in reports.values()),
            "feature_names": plan["feature_names"],
            "source_files_rechecked": len(checks),
            "config_sha256": file_sha256(args.output / "config.json"),
            "validation_read": False,
            "calibration_read": False,
            "test_evaluated": False,
            "survival_training_eligible": False,
            "operational_use": False,
        }
        write_json(args.output / "report.json", report)
        return {k: report[k] for k in ("status", "rows", "matched_v4_rows")}
    except Exception as exc:
        write_json(
            args.output / "failure.json",
            {
                "exception_type": type(exc).__name__,
                "completed_events": list(reports),
                "nontrain_read": False,
            },
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "weather-raw", "static", "reference", "config", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan-only", action="store_true")
    mode.add_argument("--build-frozen", action="store_true")
    print(json.dumps(build(parser.parse_args())))


if __name__ == "__main__":
    main()
