"""
Tests for loading and predicting with joblib-saved model artifacts.
"""
from __future__ import annotations

from pathlib import Path
import joblib
import numpy as np
import pytest

ROOT = Path(__file__).parents[2]
ARTIFACTS_DIR = ROOT / "model" / "artifacts"


def test_joblib_artifacts_exist() -> None:
    assert (ARTIFACTS_DIR / "xgboost_injury_model.joblib").exists()
    assert (ARTIFACTS_DIR / "feature_scaler.joblib").exists()
    assert (ARTIFACTS_DIR / "feature_names.joblib").exists()


def test_load_and_predict_with_joblib() -> None:
    model = joblib.load(ARTIFACTS_DIR / "xgboost_injury_model.joblib")
    scaler = joblib.load(ARTIFACTS_DIR / "feature_scaler.joblib")
    feature_names = joblib.load(ARTIFACTS_DIR / "feature_names.joblib")

    assert hasattr(model, "predict_proba")
    assert hasattr(scaler, "transform")
    assert isinstance(feature_names, list)

    # Mock single athlete day sample input
    n_features = len(feature_names)
    dummy_features = np.random.randn(1, n_features)

    # Predict
    proba = model.predict_proba(dummy_features)[0, 1]

    assert 0.0 <= proba <= 1.0
