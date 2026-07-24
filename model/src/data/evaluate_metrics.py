"""
model/src/data/evaluate_metrics.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Comprehensive Evaluation Metrics for Sports Injury Prediction.

Metrics Calculated:
  1. Accuracy         : (TP + TN) / Total
  2. Precision        : TP / (TP + FP)
  3. Recall (Sensitivity): TP / (TP + FN)  ← CRITICAL for Injury Prediction
  4. F1 Score         : 2 * (Precision * Recall) / (Precision + Recall)
  5. ROC-AUC          : Area under the Receiver Operating Characteristic curve
  6. Confusion Matrix : [[TN, FP], [FN, TP]]

Why RECALL is the Priority Metric in Sports Medicine:
  • False Negative (FN / Missed Injury)  : Severe consequence (Season-ending ACL tear, fracture).
  • False Positive (FP / False Warning)  : Low consequence (Athlete receives extra rest / modified load).
  • High Recall ensures nearly ALL real injury risks are caught early.

Usage:
    python -m model.src.data.evaluate_metrics
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)


def calculate_injury_metrics(
    y_true: np.ndarray | list,
    y_pred: np.ndarray | list,
    y_proba: np.ndarray | list | None = None,
) -> dict[str, float | int]:
    """
    Calculate full evaluation metrics with a focus on Recall for injury prevention.

    Args:
        y_true  : True binary labels (0 = Healthy, 1 = Injured)
        y_pred  : Predicted binary labels (0 = Healthy, 1 = Injured)
        y_proba : Predicted probabilities for class 1 (Injured). Optional.

    Returns:
        Dictionary containing all metrics and confusion matrix values.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    # 1. Accuracy: Overall fraction of correct predictions
    # Formula: Accuracy = (TP + TN) / Total
    accuracy = accuracy_score(y_true, y_pred)

    # 2. Precision: Of all predicted injuries, how many were real?
    # Formula: Precision = TP / (TP + FP)
    precision = precision_score(y_true, y_pred, zero_division=0)

    # 3. Recall (Sensitivity): Of all REAL injuries, how many did we catch?
    # Formula: Recall = TP / (TP + FN)  ← MOST IMPORTANT FOR INJURY PREVENTION
    recall = recall_score(y_true, y_pred, zero_division=0)

    # 4. F1 Score: Harmonic mean balancing Precision and Recall
    # Formula: F1 = 2 * (Precision * Recall) / (Precision + Recall)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    # 5. ROC-AUC: Ranking quality across all probability thresholds
    roc_auc = float(roc_auc_score(y_true, y_proba)) if y_proba is not None else 0.0

    # 6. Confusion Matrix: [[TN, FP], [FN, TP]]
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    return {
        "Accuracy": round(float(accuracy), 4),
        "Precision": round(float(precision), 4),
        "Recall": round(float(recall), 4),
        "F1_Score": round(float(f1), 4),
        "ROC_AUC": round(float(roc_auc), 4),
        "True_Positives (TP - Caught Injuries)": int(tp),
        "False_Negatives (FN - Missed Injuries)": int(fn),
        "False_Positives (FP - False Warnings)": int(fp),
        "True_Negatives (TN - Healthy Correct)": int(tn),
    }


def print_injury_evaluation_report(
    y_true: np.ndarray | list,
    y_pred: np.ndarray | list,
    y_proba: np.ndarray | list | None = None,
    model_name: str = "Sports Injury Predictor",
) -> None:
    """
    Print a detailed, formatted evaluation report highlighting Recall.
    """
    metrics = calculate_injury_metrics(y_true, y_pred, y_proba)

    tp = metrics["True_Positives (TP - Caught Injuries)"]
    fn = metrics["False_Negatives (FN - Missed Injuries)"]
    fp = metrics["False_Positives (FP - False Warnings)"]
    tn = metrics["True_Negatives (TN - Healthy Correct)"]
    total_injuries = tp + fn
    total_samples = tp + fn + fp + tn

    sep = "=" * 70

    print("\n" + sep)
    print(f"  EVALUATION REPORT: {model_name.upper()}")
    print(sep)
    print(f"  Total Athlete Days Evaluated : {total_samples:,}")
    print(f"  Actual Injury Cases           : {total_injuries:,}")
    print(sep)

    print("  KEY METRICS:")
    print(f"    • Accuracy        : {metrics['Accuracy']*100:>6.2f}%   (Overall correctness)")
    print(f"    • Precision       : {metrics['Precision']*100:>6.2f}%   (Of predicted warnings, how many were real)")
    print(f"    • RECALL          : {metrics['Recall']*100:>6.2f}%   ★ KEY METRIC (Caught {tp} of {total_injuries} injuries)")
    print(f"    • F1 Score        : {metrics['F1_Score']:>6.4f}   (Harmonic balance of Precision & Recall)")
    if y_proba is not None:
        print(f"    • ROC-AUC         : {metrics['ROC_AUC']:>6.4f}   (Discrimination & ranking quality)")

    print("\n" + sep)
    print("  CONFUSION MATRIX BREAKDOWN:")
    print(f"                          Predicted Healthy (0)    Predicted Injured (1)")
    print(f"    Actual Healthy (0) :         {tn:>7,} (TN)           {fp:>7,} (FP)")
    print(f"    Actual Injured (1) :         {fn:>7,} (FN)           {tp:>7,} (TP)")
    print(sep)

    print("  CLINICAL RISK INTERPRETATION:")
    print(f"    ✅ INJURIES CAUGHT (TP)   : {tp} / {total_injuries} ({metrics['Recall']*100:.1f}%)")
    print(f"    ⚠️  MISSED INJURIES (FN)   : {fn} (HIGH RISK — Athlete injured without warning!)")
    print(f"    ℹ️  FALSE WARNINGS (FP)   : {fp} (LOW RISK  — Athlete receives unnecessary rest)")

    if metrics['Recall'] >= 0.90:
        print("\n  🛡️  SAFETY STATUS: EXCELLENT — Model catches ≥ 90% of real injury risks!")
    elif metrics['Recall'] >= 0.75:
        print("\n  ⚠️  SAFETY STATUS: GOOD — Model catches ≥ 75% of injury risks. Consider lower threshold.")
    else:
        print("\n  🚨 SAFETY STATUS: HIGH RISK — Recall is below 75%. Lower threshold to prevent injuries!")

    print(sep + "\n")


# ── Demonstration ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Synthetic Example Demonstration: 100 Athlete Days, 10 actual injuries
    np.random.seed(42)
    y_true_example = np.array([0] * 90 + [1] * 10)
    
    # Model predictions optimized for High Recall (catches 9 out of 10 injuries)
    y_proba_example = np.random.uniform(0.0, 0.4, size=100)
    y_proba_example[85:] += 0.45  # Boost probabilities for actual positive cases
    
    threshold = 0.20
    y_pred_example = (y_proba_example >= threshold).astype(int)

    print_injury_evaluation_report(
        y_true=y_true_example,
        y_pred=y_pred_example,
        y_proba=y_proba_example,
        model_name="High-Recall Injury Risk Classifier",
    )
