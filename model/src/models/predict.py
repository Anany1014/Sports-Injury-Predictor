"""
model.src.models.predict
~~~~~~~~~~~~~~~~~~~~~~~~~
Load the trained model and run inference on new athlete data.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from model.src.utils import env, get_logger

logger = get_logger(__name__)


class InjuryPredictor:
    """Wraps a trained model with preprocessing artifacts for inference."""

    def __init__(self, artifacts_dir: Path | None = None) -> None:
        self.artifacts_dir = artifacts_dir or env.artifacts_dir
        self._model = None
        self._encoders: dict | None = None
        self._scaler = None
        self._feature_names: list[str] | None = None

    def load(self) -> "InjuryPredictor":
        """Load all saved artifacts from disk."""
        d = self.artifacts_dir
        
        # Load model with fallback options
        if (d / "model.pkl").exists():
            self._model = joblib.load(d / "model.pkl")
        elif (d / "model.joblib").exists():
            self._model = joblib.load(d / "model.joblib")
        elif (d / "xgboost_injury_model.joblib").exists():
            self._model = joblib.load(d / "xgboost_injury_model.joblib")
        else:
            raise FileNotFoundError("No trained model file (model.pkl / model.joblib) found in artifacts.")

        # Load encoders
        if (d / "encoders.joblib").exists():
            self._encoders = joblib.load(d / "encoders.joblib")
        elif (d / "ohe_encoder.joblib").exists():
            self._encoders = joblib.load(d / "ohe_encoder.joblib")
        else:
            self._encoders = None

        # Load scaler
        if (d / "scaler.joblib").exists():
            self._scaler = joblib.load(d / "scaler.joblib")
        elif (d / "feature_scaler.joblib").exists():
            self._scaler = joblib.load(d / "feature_scaler.joblib")
        else:
            self._scaler = None

        # Load feature names
        if (d / "feature_names.joblib").exists():
            self._feature_names = joblib.load(d / "feature_names.joblib")
        else:
            self._feature_names = []

        logger.info("Artifacts loaded ✓")
        return self

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run inference on a raw DataFrame of athlete records.
        """
        assert self._model is not None, "Call .load() before .predict()"

        df_out = df.copy()

        # If model expects pre-aligned features
        if self._feature_names:
            X = pd.DataFrame(index=df.index)
            for col in self._feature_names:
                if col in df.columns:
                    X[col] = df[col]
                else:
                    X[col] = 0.0
        else:
            X = df_out.select_dtypes(include=[np.number]).copy()

        # Scale if scaler is loaded
        if self._scaler is not None and hasattr(self._scaler, "transform"):
            try:
                X_scaled = self._scaler.transform(X)
            except Exception:
                X_scaled = X.values
        else:
            X_scaled = X.values

        probas = self._model.predict_proba(X_scaled)[:, 1]
        df_out["injury_probability"] = np.round(probas, 4)
        df_out["injury_risk_label"] = pd.cut(
            probas,
            bins=[-0.01, 0.25, 0.60, 1.01],
            labels=["LOW", "MEDIUM", "HIGH"],
            include_lowest=True,
        )
        return df_out

    def predict_single(self, record: dict[str, Any]) -> dict[str, Any]:
        """Run inference on a single athlete record dict."""
        df = pd.DataFrame([record])
        result = self.predict(df)
        return {
            "injury_probability": float(result["injury_probability"].iloc[0]),
            "injury_risk_label": str(result["injury_risk_label"].iloc[0]),
        }
