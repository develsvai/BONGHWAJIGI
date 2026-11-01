"""NDWS의 공식 분할과 관측 마스크를 보존하는 픽셀 단위 학습 테이블."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from scipy import ndimage

from bonghwa_training.download import DATASET, VERSION, file_sha256
from bonghwa_training.records import iter_records

SIDE = 64
BASE_FEATURES = (
    "elevation",
    "pdsi",
    "NDVI",
    "pr",
    "sph",
    "th",
    "tmmn",
    "tmmx",
    "vs",
    "erc",
    "population",
    "PrevFireMask",
)
DERIVED_FEATURES = (
    "previous_fire_unknown",
    "previous_fire_neighbors_8",
    "observed_neighbors_8",
    "distance_to_observed_fire_within_patch_km",
    "patch_has_observed_fire",
    "wind_direction_sin",
    "wind_direction_cos",
    "physical_qc_invalid_count",
)
FEATURES = BASE_FEATURES + DERIVED_FEATURES
TARGET = "fire_next_day"
SPLITS = {"train": "train", "eval": "validation", "test": "test"}
SCHEMA = pa.schema(
    [(name, pa.float32()) for name in FEATURES]
    + [
        (TARGET, pa.int8()),
        ("patch_id", pa.string()),
        ("source_file", pa.string()),
        ("source_record", pa.int32()),
        ("pixel_row", pa.uint8()),
        ("pixel_col", pa.uint8()),
    ],
    metadata={
        b"dataset": b"NDWS-v2-bootstrap",
        b"target": b"next daily satellite fire observation; not personal impact",
        b"feature_names": json.dumps(FEATURES).encode(),
    },
)


def check_patch(arrays: dict[str, np.ndarray]) -> None:
    if set(arrays) != {*BASE_FEATURES, "FireMask"}:
        raise ValueError("원본 필드가 NDWS의 12개 입력과 FireMask 정답과 다릅니다.")
    if any(values.shape != (SIDE * SIDE,) for values in arrays.values()):
        raise ValueError("64×64 패치 크기가 아닙니다.")
    for name in ("PrevFireMask", "FireMask"):
        if not np.isin(arrays[name], [-1, 0, 1]).all():
            raise ValueError(f"{name}: 허용되지 않은 화재 관측 마스크 값입니다.")


def patch_id(arrays: dict[str, np.ndarray]) -> str:
    """정답을 제외한 모든 원본 입력으로 동일 패치를 찾는다."""
    digest = hashlib.sha256()
    for name in BASE_FEATURES:
        digest.update(name.encode())
        digest.update(arrays[name].astype("<f4", copy=False).tobytes())
    return digest.hexdigest()


def clean_inputs(arrays: dict[str, np.ndarray]) -> tuple[dict, dict]:
    features = {name: values.copy() for name, values in arrays.items() if name in BASE_FEATURES}
    invalid = {name: ~np.isfinite(values) for name, values in features.items()}
    for name in ("pr", "vs", "erc", "population"):
        invalid[name] |= features[name] < 0
    invalid["sph"] |= (features["sph"] < 0) | (features["sph"] > 1)
    invalid["th"] |= (features["th"] < 0) | (features["th"] > 360)
    for name in ("tmmn", "tmmx"):
        invalid[name] |= features[name] <= 0
    reversed_temperature = features["tmmn"] > features["tmmx"]
    invalid["tmmn"] |= reversed_temperature
    invalid["tmmx"] |= reversed_temperature
    for name, values in features.items():
        values[invalid[name]] = np.nan
    return features, invalid


def make_features(arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    check_patch(arrays)
    features, invalid = clean_inputs(arrays)
    features["physical_qc_invalid_count"] = np.sum(list(invalid.values()), axis=0, dtype=np.float32)
    previous = arrays["PrevFireMask"].reshape(SIDE, SIDE)
    burning = previous == 1
    observed = previous != -1
    kernel = np.ones((3, 3), dtype=np.float32)
    kernel[1, 1] = 0
    features["PrevFireMask"][~observed.ravel()] = np.nan
    features["previous_fire_unknown"] = (~observed).ravel().astype(np.float32)
    features["previous_fire_neighbors_8"] = ndimage.convolve(
        burning.astype(np.float32), kernel, mode="constant", cval=0
    ).ravel()
    features["observed_neighbors_8"] = ndimage.convolve(
        observed.astype(np.float32), kernel, mode="constant", cval=0
    ).ravel()
    distance = (
        ndimage.distance_transform_edt(~burning).astype(np.float32)
        if burning.any()
        else np.full((SIDE, SIDE), np.nan, dtype=np.float32)
    )
    features["distance_to_observed_fire_within_patch_km"] = distance.ravel()
    features["patch_has_observed_fire"] = np.full(SIDE * SIDE, burning.any(), dtype=np.float32)
    radians = np.deg2rad(features["th"])
    features["wind_direction_sin"] = np.sin(radians)
    features["wind_direction_cos"] = np.cos(radians)
    return features


def select_patches(patches: list[dict]) -> tuple[set[tuple[str, int]], dict]:
    """분할 간 동일 입력은 양쪽 모두 격리하고, 분할 내부 중복은 최초 것만 쓴다."""
    groups = defaultdict(list)
    for patch in patches:
        groups[patch["patch_id"]].append(patch)
    selected = set()
    cross_split_groups = 0
    cross_split_patches = 0
    within_split_duplicates = 0
    for group in groups.values():
        if len({item["split"] for item in group}) > 1:
            cross_split_groups += 1
            cross_split_patches += len(group)
        else:
            seen_targets = set()
            for item in group:
                target_digest = item["target_sha256"]
                if target_digest in seen_targets:
                    within_split_duplicates += 1
                else:
                    selected.add((item["source_file"], item["source_record"]))
                    seen_targets.add(target_digest)
    return selected, {
        "fingerprint": "sha256 of ordered 12 raw input float32 arrays; label excluded",
        "cross_split_duplicate_groups": cross_split_groups,
        "cross_split_patches_quarantined": cross_split_patches,
        "within_split_duplicate_patches_removed": within_split_duplicates,
        "same_input_different_target_groups": sum(
            len({item["target_sha256"] for item in group}) > 1 for group in groups.values()
        ),
        "event_or_near_duplicate_independence_verified": False,
    }


def make_table(arrays: dict[str, np.ndarray], item: dict, index: int) -> pa.Table:
    features = make_features(arrays)
    valid = arrays["FireMask"] != -1
    size = int(valid.sum())
    row, col = np.indices((SIDE, SIDE), dtype=np.uint8)
    data = {name: features[name][valid] for name in FEATURES}
    data.update(
        {
            TARGET: arrays["FireMask"][valid].astype(np.int8),
            "patch_id": [patch_id(arrays)] * size,
            "source_file": [item["filename"]] * size,
            "source_record": np.full(size, index, dtype=np.int32),
            "pixel_row": row.ravel()[valid],
            "pixel_col": col.ravel()[valid],
        }
    )
    return pa.Table.from_pydict(data, schema=SCHEMA)


def update_statistics(stats: dict, table: pa.Table) -> None:
    stats["rows"] += table.num_rows
    counts = Counter(table[TARGET].to_pylist())
    for label in (0, 1):
        stats["labels"][str(label)] += counts[label]
    for name in FEATURES:
        values = table[name].to_numpy()
        finite = values[np.isfinite(values)]
        record = stats["features"][name]
        record["missing"] += int(np.isnan(values).sum())
        if finite.size:
            low, high = float(finite.min()), float(finite.max())
            record["min"] = low if record["min"] is None else min(low, record["min"])
            record["max"] = high if record["max"] is None else max(high, record["max"])


def build_dataset(raw: Path, output: Path) -> dict:
    manifest = json.loads((raw / "manifest.json").read_text())
    if manifest["dataset"] != DATASET or manifest["version"] != VERSION:
        raise ValueError("검토한 NDWS 버전 2가 아닙니다.")
    if set(item["official_split"] for item in manifest["files"]) != set(SPLITS):
        raise ValueError("학습·검증·평가 원본을 모두 확보해야 합니다.")
    patches = []
    files = manifest["files"]
    for item in files:
        name = item["filename"]
        if Path(name).name != name:
            raise ValueError("원본 파일명에 경로가 포함되어 있습니다.")
        path = raw / name
        if path.stat().st_size != item["bytes"] or file_sha256(path) != item["sha256"]:
            raise ValueError(f"원본 SHA256 또는 길이 불일치: {name}")
        count = 0
        for index, arrays in iter_records(path):
            check_patch(arrays)
            patches.append(
                {
                    "source_file": name,
                    "source_record": index,
                    "split": SPLITS[item["official_split"]],
                    "patch_id": patch_id(arrays),
                    "target_sha256": hashlib.sha256(arrays["FireMask"].tobytes()).hexdigest(),
                }
            )
            count += 1
        print(json.dumps({"scanned": name, "patches": count}), flush=True)
    selected, duplicates = select_patches(patches)
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "profile": "ndws_v2_us_next_daily_fire_observation_1km_bootstrap",
        "build_version": 2,
        "source_manifest": manifest,
        "source_manifest_sha256": file_sha256(raw / "manifest.json"),
        "feature_names": list(FEATURES),
        "target": TARGET,
        "official_split_mapping": SPLITS,
        "negative_sampling": "none; all observed target pixels retained",
        "duplicate_audit": duplicates,
        "raw_patch_count": len(patches),
        "splits": {},
        "limitations": [
            "United States historical satellite observations; not validated for South Korea",
            "Next daily observed fire presence; not hourly arrival, "
            "personal harm or response level",
            "Masks -1 are unobserved; target -1 excluded, previous -1 becomes NaN with flag",
            "No dates, event IDs or coordinates in downloaded records; "
            "event/time audit unavailable",
            "Official week split is inherited; spatial/event separation cannot be guaranteed",
            "Distance is within each nominal 1km patch grid, not global nearest fire distance",
            "Daily aggregated covariates are retrospective; operational availability is not proven",
            "Observation non-detection and cloud exclusion may bias satellite target coverage",
            "Source resolution differs across features; 1km grid does not add source detail",
            "Physical QC masks negative rain/speed/ERC/population, invalid humidity/direction, "
            "nonpositive or reversed Kelvin temperatures; no learned imputation or clipping",
            "Only first shard per split by default; "
            "selected subset is not a representative full corpus",
        ],
    }
    for split in SPLITS.values():
        path = output / f"{split}.parquet"
        stats = {
            "rows": 0,
            "raw_patches": 0,
            "kept_patches": 0,
            "excluded_unknown_target_pixels": 0,
            "quarantined_or_duplicate_pixels": 0,
            "labels": {"0": 0, "1": 0},
            "features": {name: {"missing": 0, "min": None, "max": None} for name in FEATURES},
            "raw_input_qc": {
                name: {"invalid": 0, "min": None, "max": None} for name in BASE_FEATURES
            },
        }
        buffer = []
        with pq.ParquetWriter(path, SCHEMA, compression="zstd") as writer:
            for item in files:
                if SPLITS[item["official_split"]] != split:
                    continue
                for index, arrays in iter_records(raw / item["filename"]):
                    stats["raw_patches"] += 1
                    if (item["filename"], index) not in selected:
                        stats["quarantined_or_duplicate_pixels"] += SIDE * SIDE
                        continue
                    stats["kept_patches"] += 1
                    _, invalid = clean_inputs(arrays)
                    for name in BASE_FEATURES:
                        quality = stats["raw_input_qc"][name]
                        quality["invalid"] += int(invalid[name].sum())
                        finite = arrays[name][np.isfinite(arrays[name])]
                        if finite.size:
                            low, high = float(finite.min()), float(finite.max())
                            quality["min"] = (
                                low if quality["min"] is None else min(low, quality["min"])
                            )
                            quality["max"] = (
                                high if quality["max"] is None else max(high, quality["max"])
                            )
                    stats["excluded_unknown_target_pixels"] += int((arrays["FireMask"] == -1).sum())
                    table = make_table(arrays, item, index)
                    update_statistics(stats, table)
                    if table.num_rows:
                        buffer.append(table)
                    if len(buffer) >= 32:
                        writer.write_table(pa.concat_tables(buffer))
                        buffer.clear()
            if buffer:
                writer.write_table(pa.concat_tables(buffer))
        if not stats["rows"] or not all(stats["labels"].values()):
            raise ValueError(f"{split}에 유효한 두 종류 정답이 모두 있어야 합니다.")
        stats["positive_fraction"] = stats["labels"]["1"] / stats["rows"]
        stats["file"] = path.name
        stats["bytes"] = path.stat().st_size
        stats["sha256"] = file_sha256(path)
        report["splits"][split] = stats
        print(
            json.dumps({"built": split, "rows": stats["rows"], "labels": stats["labels"]}),
            flush=True,
        )
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def iter_training_batches(path: Path, batch_size: int = 65536):
    """ID·좌표 인덱스·정답 컬럼을 학습 입력에 섞지 않는 배치 로더."""
    for batch in pq.ParquetFile(path).iter_batches(
        batch_size=batch_size, columns=[*FEATURES, TARGET]
    ):
        x = np.column_stack([batch.column(name).to_numpy() for name in FEATURES])
        y = batch.column(TARGET).to_numpy()
        yield x, y


def verify_dataset(output: Path) -> dict:
    report = json.loads((output / "report.json").read_text())
    if report["feature_names"] != list(FEATURES) or report["target"] != TARGET:
        raise ValueError("학습 입력 또는 정답 계약이 다릅니다.")
    verified = {}
    for split, expected in report["splits"].items():
        path = output / expected["file"]
        if file_sha256(path) != expected["sha256"] or path.stat().st_size != expected["bytes"]:
            raise ValueError(f"변환 자료 SHA256 또는 길이 불일치: {split}")
        if not pq.ParquetFile(path).schema_arrow.equals(SCHEMA, check_metadata=True):
            raise ValueError("Parquet 스키마가 학습 계약과 다릅니다.")
        counts = Counter()
        for x, y in iter_training_batches(path):
            if x.dtype != np.float32 or np.isinf(x).any() or not np.isin(y, [0, 1]).all():
                raise ValueError("학습 배치에 무한대 입력 또는 잘못된 정답이 있습니다.")
            labels, amounts = np.unique(y, return_counts=True)
            counts.update(
                {str(label): int(amount) for label, amount in zip(labels, amounts, strict=True)}
            )
        if dict(counts) != expected["labels"] or sum(counts.values()) != expected["rows"]:
            raise ValueError("보고서의 정답 분포와 실제 학습 자료가 다릅니다.")
        verified[split] = {"rows": sum(counts.values()), "labels": dict(counts)}
    print(json.dumps({"verified": verified}), flush=True)
    return verified
