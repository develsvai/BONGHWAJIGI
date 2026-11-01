"""관측 미상 후보도 검토 예산에 포함하는 연구용 순위 진단.

정답 -1은 관측 미상이다. 순위·상위 예산 결정에는 정답을 쓰지 않는다.
알려진 정답만의 AP와 미상 후보를 포함한 검토량을 별도로 보고한다.
"""

import numpy as np

from bonghwa_training.ranking_audit import select_candidates, standard_metrics

COUNTS = (
    "candidate_rows",
    "known_rows",
    "unknown_rows",
    "observed_positives",
    "selected_rows",
    "selected_known",
    "selected_unknown",
    "true_positives",
    "false_positives",
    "missing_score_rows",
    "selected_missing_score_rows",
    "issues",
)


def ratio(a, b):
    return float(a / b) if b else None


def ratios(counts):
    return {
        "known_fraction": ratio(counts["known_rows"], counts["candidate_rows"]),
        "selected_fraction": ratio(counts["selected_rows"], counts["candidate_rows"]),
        "selected_unknown_fraction": ratio(counts["selected_unknown"], counts["selected_rows"]),
        "observed_positive_recall": ratio(counts["true_positives"], counts["observed_positives"]),
        "precision_known_selected": ratio(counts["true_positives"], counts["selected_known"]),
        "precision_lower_bound": ratio(counts["true_positives"], counts["selected_rows"]),
        "precision_upper_bound": ratio(
            counts["true_positives"] + counts["selected_unknown"], counts["selected_rows"]
        ),
    }


def summarize(labels, scores, issues, rows, cols, percent=10):
    labels, scores, issues, rows, cols = [
        np.asarray(x) for x in (labels, scores, issues, rows, cols)
    ]
    if any(x.ndim != 1 or len(x) != len(labels) for x in (labels, scores, issues, rows, cols)):
        raise ValueError("행 배열 크기 불일치")
    if not np.isin(labels, [-1, 0, 1]).all() or not np.isfinite(issues).all():
        raise ValueError("관측 정답/시각 오류")
    if np.isinf(scores).any() or not 0 < percent <= 100:
        raise ValueError("점수/검토 예산 오류")
    known = labels >= 0
    metrics = standard_metrics(labels[known], scores[known], probability=False)
    counts = dict.fromkeys(COUNTS, 0)
    counts.update(
        candidate_rows=len(labels),
        known_rows=int(known.sum()),
        unknown_rows=int((~known).sum()),
        observed_positives=int((labels == 1).sum()),
        missing_score_rows=int(np.isnan(scores).sum()),
    )
    for issue in np.unique(issues):
        index = np.flatnonzero(issues == issue)
        # Crucially include unknown labels; candidate selection has no labels argument.
        chosen, _ = select_candidates(scores[index], rows[index], cols[index], percent)
        selected = index[chosen]
        values = labels[selected]
        counts["issues"] += 1
        counts["selected_rows"] += len(selected)
        counts["selected_known"] += int((values >= 0).sum())
        counts["selected_unknown"] += int((values < 0).sum())
        counts["true_positives"] += int((values == 1).sum())
        counts["false_positives"] += int((values == 0).sum())
        counts["selected_missing_score_rows"] += int(np.isnan(scores[selected]).sum())
    return {
        "known_only_metrics": metrics,
        "budget": {"requested_percent_per_issue": percent, **counts, **ratios(counts)},
        "semantics": (
            "Known-only AP has observation-coverage selection; budget includes unknowns. "
            "Bounds concern encoded observation labels, not real fire or personal harm."
        ),
    }


def aggregate(diagnostics):
    """Aggregate event/horizon cells without discarding zero-positive/unknown cells."""
    cells = [cell for event in diagnostics.values() for cell in event.values()]
    counts = {key: sum(cell["budget"][key] for cell in cells) for key in COUNTS}
    ap = [
        cell["known_only_metrics"]["average_precision"]
        for cell in cells
        if cell["known_only_metrics"]["average_precision"] is not None
    ]
    return {
        "macro_known_event_horizon_ap": float(np.mean(ap)) if ap else None,
        "eligible_ap_cells": len(ap),
        "total_cells": len(cells),
        "budget": counts | ratios(counts),
    }
