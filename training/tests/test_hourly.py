import numpy as np
import pytest

from bonghwa_training.goes_build import chronological_indices, classify, future_target


def test_goes_cloud_and_probability_categories_are_censored():
    mask = np.array([10, 11, 30, 31, 12, 13, 14, 15, 100, 200, 120, 0])
    quality = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 4, 3])
    np.testing.assert_array_equal(
        classify(mask, quality), [1, 1, 1, 1, -1, -1, -1, -1, 0, -1, -1, -1]
    )
    assert classify(np.array([10]), np.array([4]))[0] == -1


def test_missing_future_frames_never_create_negative_labels():
    states = np.array([[0, 0, -1, 1], [0, 1, -1, -1]], dtype=np.int8)
    np.testing.assert_array_equal(future_target(states, complete=True), [0, 1, -1, 1])
    np.testing.assert_array_equal(future_target(states, complete=False), [-1, 1, -1, 1])


def test_fire_evidence_is_monotone_across_nested_horizons():
    states = np.array([[0, -1, 0], [1, -1, 0], [0, 1, 0]], dtype=np.int8)
    one = future_target(states[:1], complete=True)
    three = future_target(states, complete=True)
    assert not np.any((one == 1) & (three == 0))
    np.testing.assert_array_equal(three, [1, 1, 0])


def test_scan_mode_filename_order_and_reprocessed_duplicates():
    # M4 파일이 M6보다 먼저 정렬되는 실제 문제를 재현한다.
    indices = chronological_indices(
        np.array([900, 0, 300, 300]),
        np.array([1050, 150, 450, 450]),
        np.array([1100, 200, 800, 500]),
    )
    np.testing.assert_array_equal(indices, [1, 3, 0])


def test_final_event_needs_unchanged_frozen_model(tmp_path):
    import json

    from bonghwa_training.download import file_sha256
    from bonghwa_training.goes_release import freeze, verify_release

    cfg = tmp_path / "config.json"
    cfg.write_text("{}")
    run = tmp_path / "run"
    run.mkdir()
    model = run / "chosen.ubj"
    model.write_bytes(b"frozen-model")
    (run / "plan.json").write_text(json.dumps({"config_sha256": file_sha256(cfg)}))
    (run / "report.json").write_text(
        json.dumps(
            {
                "test_evaluated": False,
                "selected": "chosen",
                "experiments": {"chosen": {"model_sha256": file_sha256(model)}},
            }
        )
    )
    receipt = tmp_path / "release.json"
    freeze(run, cfg, receipt)
    verify_release(receipt, cfg)
    model.write_bytes(b"changed-model")
    with pytest.raises(ValueError, match="바뀌었습니다"):
        verify_release(receipt, cfg)
