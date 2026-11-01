"""연구용 임계값 진단. 사용자 대응 레벨과는 별개다."""

import numpy as np
from sklearn.metrics import confusion_matrix, roc_curve


def at_threshold(y, p, threshold):
    tn, fp, fn, tp = confusion_matrix(y, p >= threshold, labels=[0, 1]).ravel()
    return {
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
        "precision": float(tp / (tp + fp)) if tp + fp else 0,
        "recall": float(tp / (tp + fn)) if tp + fn else 0,
        "false_positive_rate": float(fp / (fp + tn)) if fp + tn else 0,
    }


def operating_points(y, p, maximum_fpr=(0.01, 0.05)):
    fpr, tpr, thresholds = roc_curve(y, p, drop_intermediate=False)
    result = []
    for maximum in maximum_fpr:
        choices = np.where((fpr <= maximum) & np.isfinite(thresholds))[0]
        best = choices[np.argmax(tpr[choices])]
        threshold = float(thresholds[best])
        result.append(
            {
                "maximum_fpr_requested": maximum,
                "threshold": threshold,
                **at_threshold(y, p, threshold),
            }
        )
    return result


def logits(p):
    p = np.clip(p, 1e-7, 1 - 1e-7)
    return np.log(p / (1 - p)).reshape(-1, 1)
