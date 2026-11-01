import numpy as np
import pytest

from bonghwa_training.censored_ranking import aggregate, summarize


def evaluate(y, p, issues=None):
    return summarize(
        y, p, np.zeros(len(y)) if issues is None else issues, np.arange(len(y)), np.zeros(len(y))
    )


def test_unknown_candidates_consume_real_review_budget():
    y = [-1, 1] + [0] * 8
    p = [0.99, 0.9] + [0.1] * 8
    result = evaluate(y, p)
    assert result["known_only_metrics"]["average_precision"] == 1
    b = result["budget"]
    assert b["selected_rows"] == b["selected_unknown"] == 1
    assert b["true_positives"] == b["observed_positive_recall"] == 0
    assert b["precision_known_selected"] is None
    assert b["precision_lower_bound"] == 0 and b["precision_upper_bound"] == 1


def test_label_changes_do_not_change_selection_count_or_missing_score_selection():
    p = [0.1, np.nan, 0.9, 0.8]
    a, b = evaluate([-1, 0, 1, 0], p), evaluate([1, -1, 0, -1], p)
    for key in ("selected_rows", "selected_missing_score_rows", "issues"):
        assert a["budget"][key] == b["budget"][key]
    assert a["budget"]["true_positives"] == 1
    assert b["budget"]["false_positives"] == 1


def test_each_issue_uses_its_own_ceil_budget():
    result = evaluate([1, 0, 0, 1, -1], [0.1, 0.2, 0.3, 0.9, 0.1], [1, 1, 1, 2, 2])
    b = result["budget"]
    assert b["issues"] == 2 and b["selected_rows"] == 2
    assert b["true_positives"] == b["false_positives"] == 1
    assert b["observed_positive_recall"] == 0.5


def test_single_class_unknown_and_empty_cells_are_retained():
    cells = {
        "a": {"1": evaluate([-1, -1], [0.2, 0.1])},
        "b": {"1": evaluate([0, 0], [0.5, 0.7]), "3": evaluate([], [])},
    }
    report = aggregate(cells)
    assert report["macro_known_event_horizon_ap"] is None
    assert report["total_cells"] == 3 and report["budget"]["candidate_rows"] == 4
    assert report["budget"]["unknown_rows"] == 2


def test_duplicate_coordinates_within_issue_and_invalid_labels_fail():
    with pytest.raises(ValueError, match="중복"):
        summarize([0, 1], [0.1, 0.2], [0, 0], [1, 1], [1, 1])
    with pytest.raises(ValueError, match="정답"):
        evaluate([2, 0], [0.1, 0.2])
