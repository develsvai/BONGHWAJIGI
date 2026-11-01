import json
import struct

import numpy as np
import pytest

from bonghwa_training.build import (
    BASE_FEATURES,
    FEATURES,
    SIDE,
    build_dataset,
    check_patch,
    iter_training_batches,
    make_features,
    make_table,
    patch_id,
    select_patches,
    verify_dataset,
)
from bonghwa_training.download import DATASET, VERSION, file_sha256
from bonghwa_training.records import Example, iter_records, masked_crc32c


def patch(offset=0):
    arrays = {name: np.full(SIDE * SIDE, offset, dtype=np.float32) for name in BASE_FEATURES}
    arrays["PrevFireMask"][:] = 0
    arrays["PrevFireMask"][32 * SIDE + 32] = 1
    arrays["PrevFireMask"][0] = -1
    arrays["PrevFireMask"][2] = -1
    arrays["FireMask"] = np.zeros(SIDE * SIDE, dtype=np.float32)
    arrays["FireMask"][0] = -1
    arrays["FireMask"][1] = 1
    return arrays


def write_record(path, arrays):
    message = Example()
    for key, values in arrays.items():
        message.features.feature[key].float_list.value.extend(values)
    data = message.SerializeToString(deterministic=True)
    size = struct.pack("<Q", len(data))
    path.write_bytes(
        size
        + struct.pack("<I", masked_crc32c(size))
        + data
        + struct.pack("<I", masked_crc32c(data))
    )


def test_real_tfrecord_contract_and_corruption(tmp_path):
    path = tmp_path / "patch.tfrecord"
    expected = patch()
    write_record(path, expected)
    index, actual = next(iter_records(path))
    assert index == 0
    for name in expected:
        np.testing.assert_array_equal(actual[name], expected[name])
    original = path.read_bytes()
    for damaged in (original[:-1], original[:20], original[:15] + b"x" + original[16:]):
        path.write_bytes(damaged)
        with pytest.raises(ValueError):
            list(iter_records(path))


@pytest.mark.parametrize("fault", ["missing", "extra", "shape", "mask"])
def test_unreviewed_raw_contract_fails_closed(fault):
    arrays = patch()
    if fault == "missing":
        del arrays["pdsi"]
    elif fault == "extra":
        arrays["future_weather"] = arrays["pr"]
    elif fault == "shape":
        arrays["pr"] = np.zeros(12)
    else:
        arrays["FireMask"][5] = 2
    with pytest.raises(ValueError):
        check_patch(arrays)


def test_future_label_never_enters_features_or_input_fingerprint():
    arrays = patch()
    changed = {key: value.copy() for key, value in arrays.items()}
    changed["FireMask"][:] = 1
    assert patch_id(arrays) == patch_id(changed)
    for name, value in make_features(arrays).items():
        np.testing.assert_array_equal(value, make_features(changed)[name])
    assert "FireMask" not in FEATURES
    assert "fire_next_day" not in FEATURES


def test_unknown_target_excluded_and_unknown_input_preserved():
    arrays = patch()
    arrays["PrevFireMask"][2] = -1
    table = make_table(arrays, {"filename": "fixture.tfrecord"}, 0)
    assert table.num_rows == SIDE * SIDE - 1
    assert set(table["fire_next_day"].to_pylist()) == {0, 1}
    assert table["fire_next_day"].to_pylist().count(1) == 1
    assert np.isnan(table["PrevFireMask"][1].as_py())
    assert table["previous_fire_unknown"][1].as_py() == 1
    features = make_features(arrays)
    assert features["previous_fire_neighbors_8"][32 * SIDE + 33] == 1
    assert features["distance_to_observed_fire_within_patch_km"][32 * SIDE + 33] == 1
    assert features["observed_neighbors_8"][0] == 3


def test_no_observed_fire_does_not_invent_distance():
    arrays = patch()
    arrays["PrevFireMask"][:] = -1
    features = make_features(arrays)
    assert np.isnan(features["distance_to_observed_fire_within_patch_km"]).all()
    assert not features["patch_has_observed_fire"].any()
    assert not features["observed_neighbors_8"].any()


def test_physical_impossibilities_masked_before_wind_derivation():
    arrays = patch()
    arrays["pr"][2] = -1
    arrays["vs"][2] = -1
    arrays["sph"][2] = 2
    arrays["th"][2] = 500
    arrays["tmmn"][2] = 300
    arrays["tmmx"][2] = 280
    arrays["elevation"][2] = -5
    arrays["NDVI"][2] = -100
    features = make_features(arrays)
    for name in ("pr", "vs", "sph", "th", "tmmn", "tmmx", "wind_direction_sin"):
        assert np.isnan(features[name][2])
    assert features["physical_qc_invalid_count"][2] == 6
    assert features["elevation"][2] == -5
    assert features["NDVI"][2] == -100


def test_cross_split_input_duplicates_quarantined_even_with_different_labels():
    patches = [
        {"patch_id": "a", "split": "train", "source_file": "train", "source_record": 0},
        {"patch_id": "a", "split": "test", "source_file": "test", "source_record": 0},
        {"patch_id": "b", "split": "train", "source_file": "train", "source_record": 1},
        {"patch_id": "b", "split": "train", "source_file": "train", "source_record": 2},
    ]
    for item in patches:
        item["target_sha256"] = "same"
    patches[1]["target_sha256"] = "different"
    selected, report = select_patches(patches)
    assert selected == {("train", 1)}
    assert report["cross_split_patches_quarantined"] == 2
    assert report["within_split_duplicate_patches_removed"] == 1
    assert report["same_input_different_target_groups"] == 1
    patches[3]["target_sha256"] = "different"
    selected, _ = select_patches(patches)
    assert selected == {("train", 1), ("train", 2)}


def test_reproducible_build_and_loader_then_tamper_detection(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    manifest = {"dataset": DATASET, "version": VERSION, "files": []}
    for index, split in enumerate(("train", "eval", "test")):
        path = raw / f"fixture_{split}.tfrecord"
        write_record(path, patch(index))
        manifest["files"].append(
            {
                "filename": path.name,
                "official_split": split,
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    (raw / "manifest.json").write_text(json.dumps(manifest))
    first = build_dataset(raw, tmp_path / "first")
    second = build_dataset(raw, tmp_path / "second")
    assert first == second
    verified = verify_dataset(tmp_path / "first")
    assert set(verified) == {"train", "validation", "test"}
    assert verified["train"]["labels"] == {"0": 4094, "1": 1}
    x, y = next(iter_training_batches(tmp_path / "first" / "train.parquet"))
    assert x.shape == (4095, len(FEATURES))
    assert x.dtype == np.float32
    assert y.shape == (4095,)
    assert np.isnan(x).any()
    path = tmp_path / "first" / "train.parquet"
    with path.open("ab") as output:
        output.write(b"tampered")
    with pytest.raises(ValueError, match="SHA256"):
        verify_dataset(tmp_path / "first")
