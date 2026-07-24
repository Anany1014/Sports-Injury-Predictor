"""
Tests for Two-Stage Cascade Classifier.
"""
from __future__ import annotations

from pathlib import Path
import joblib
import numpy as np
import pytest

from model.src.models.two_stage_cascade import TwoStageCascadeClassifier

ROOT = Path(__file__).parents[2]
ARTIFACTS_DIR = ROOT / "model" / "artifacts"


def test_two_stage_cascade_fit_and_predict() -> None:
    np.random.seed(42)
    X_dummy = np.random.randn(100, 10)
    y_dummy = np.array([0] * 80 + [1] * 20)

    cascade = TwoStageCascadeClassifier(t1=0.15, t2=0.40, random_state=42)
    cascade.fit(X_dummy, y_dummy, scale_pos_w=1.0)

    preds = cascade.predict(X_dummy)
    probas = cascade.predict_proba(X_dummy)

    assert len(preds) == 100
    assert probas.shape == (100, 2)
    assert set(np.unique(preds)).issubset({0, 1})


def test_saved_cascade_artifacts() -> None:
    assert (ARTIFACTS_DIR / "cascade_stage1.joblib").exists()
    assert (ARTIFACTS_DIR / "cascade_stage2.joblib").exists()

    cascade = TwoStageCascadeClassifier.load(ARTIFACTS_DIR)
    assert isinstance(cascade, TwoStageCascadeClassifier)
    assert hasattr(cascade.stage1_model, "predict_proba")
    assert hasattr(cascade.stage2_model, "predict_proba")
