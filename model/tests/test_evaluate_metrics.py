"""
Tests for model evaluation metrics.

Verifies calculation correctness for:
  - Accuracy
  - Precision
  - Recall
  - F1 Score
  - ROC-AUC
  - Confusion Matrix
"""
from __future__ import annotations

import numpy as np
import pytest

from model.src.data.evaluate_metrics import calculate_injury_metrics


def test_perfect_predictions() -> None:
    y_true = [0, 0, 1, 1]
    y_pred = [0, 0, 1, 1]
    y_proba = [0.1, 0.2, 0.8, 0.9]

    metrics = calculate_injury_metrics(y_true, y_pred, y_proba)

    assert metrics["Accuracy"] == 1.0
    assert metrics["Precision"] == 1.0
    assert metrics["Recall"] == 1.0
    assert metrics["F1_Score"] == 1.0
    assert metrics["ROC_AUC"] == 1.0
    assert metrics["True_Positives (TP - Caught Injuries)"] == 2
    assert metrics["False_Negatives (FN - Missed Injuries)"] == 0


def test_high_recall_priority() -> None:
    # 5 actual injuries, model catches all 5 (Recall = 1.0) despite 3 false alarms
    y_true = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    y_pred = [0, 1, 1, 1, 0, 1, 1, 1, 1, 1]

    metrics = calculate_injury_metrics(y_true, y_pred)

    assert metrics["Recall"] == 1.0
    assert metrics["True_Positives (TP - Caught Injuries)"] == 5
    assert metrics["False_Negatives (FN - Missed Injuries)"] == 0
    assert metrics["False_Positives (FP - False Warnings)"] == 3


def test_zero_division_safety() -> None:
    y_true = [0, 0, 0]
    y_pred = [0, 0, 0]

    metrics = calculate_injury_metrics(y_true, y_pred)

    assert metrics["Precision"] == 0.0
    assert metrics["Recall"] == 0.0
    assert metrics["F1_Score"] == 0.0
