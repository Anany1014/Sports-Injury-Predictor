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


SPORT_RISK_MULTIPLIERS = {
    'Rugby': 1.25,
    'Football': 1.15,
    'Basketball': 1.15,
    'Cricket': 1.18,
    'Baseball': 1.12,
    'Running': 1.10,
    'Tennis': 1.05,
    'Badminton': 1.02,
    'Fitness Training': 1.00,
    'Swimming': 0.82,
    'Cycling': 0.85,
}

POSITION_RISK_MULTIPLIERS = {
    'Forward (Prop/Hooker/Lock)': 1.20,
    'Back (Scrum-half/Fly-half/Center/Wing)': 1.10,
    'Goalkeeper': 0.80,
    'Central Midfielder': 1.15,
    'Winger': 1.12,
    'Striker / Forward': 1.10,
    'Center Back': 1.05,
    'Fullback': 1.10,
    'Point Guard': 1.12,
    'Center': 1.15,
    'Power Forward': 1.10,
    'Small Forward': 1.08,
    'Shooting Guard': 1.05,
    'Fast Bowler': 1.30,
    'All-Rounder': 1.15,
    'Wicketkeeper': 1.08,
    'Batsman': 0.90,
    'Spin Bowler': 1.00,
    'Pitcher': 1.25,
    'Catcher': 1.15,
    'Outfielder': 1.05,
    'Infielder': 1.00,
    'Marathoner': 1.15,
    'Sprinter': 1.12,
    'Trail Runner': 1.10,
    'Middle Distance': 1.05,
    'Climber': 1.05,
    'Road Racer': 1.00,
    'Time Trialist': 0.95,
    'Sprint / Butterfly / Backstroke / Breaststroke': 1.05,
    'Freestyle / Distance': 0.95,
}


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

    def _compute_calibrated_probability(self, row: pd.Series) -> float:
        vol = float(row.get('weekly_volume_hrs', 14.5))
        intensity = float(row.get('weekly_intensity_score', 7.5))
        sleep = float(row.get('sleep_hours', 7.5))
        hrv = float(row.get('hrv_ms', 58.0))
        soreness = float(row.get('soreness_score', 4.0))
        rest = int(row.get('rest_days', 1))
        priors = int(row.get('prior_injuries', 1))
        days_since = float(row.get('days_since_last_injury', 90.0))
        sport = str(row.get('sport', '')).strip()
        position = str(row.get('position', '')).strip()

        # 1. Workload Exertion Index
        vol_ratio = min(2.0, vol / 14.0)
        intensity_ratio = intensity / 10.0
        rest_penalty = max(0.0, (2.0 - rest) / 2.0) * 0.15
        workload_score = (vol_ratio * 0.35 + intensity_ratio * 0.50 + rest_penalty)

        # 2. Recovery Deficit
        sleep_deficit = max(0.0, (8.0 - sleep) / 8.0)
        hrv_deficit = max(0.0, (70.0 - hrv) / 70.0)
        soreness_deficit = soreness / 10.0
        recovery_deficit = min(1.0, max(0.0, sleep_deficit * 0.35 + hrv_deficit * 0.35 + soreness_deficit * 0.30))

        # 3. Prior Injury Risk Factor
        recency_weight = np.exp(-days_since / 90.0)
        history_factor = min(1.0, (priors * 0.15) * (0.4 + 0.6 * recency_weight))

        # 4. Sport & Position Biomechanical Risk Factor
        sport_mod = SPORT_RISK_MULTIPLIERS.get(sport, 1.0)
        pos_mod = POSITION_RISK_MULTIPLIERS.get(position, 1.0)
        if pos_mod == 1.0 and position:
            for k, v in POSITION_RISK_MULTIPLIERS.items():
                if k.lower() in position.lower() or position.lower() in k.lower():
                    pos_mod = v
                    break

        biomechanical_factor = (sport_mod * pos_mod - 1.0)

        # Logit z combination
        z = (workload_score * 2.2 + recovery_deficit * 2.0 + history_factor * 1.5 + biomechanical_factor * 2.0) - 2.2
        prob = 1.0 / (1.0 + np.exp(-z))
        return round(float(prob), 4)

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run inference on a raw DataFrame of athlete records.
        """
        assert self._model is not None, "Call .load() before .predict()"

        df_out = df.copy()
        is_biometric_input = any(c in df.columns for c in ["weekly_volume_hrs", "weekly_intensity_score", "sleep_hours", "hrv_ms", "soreness_score"])

        if is_biometric_input:
            probas = df.apply(self._compute_calibrated_probability, axis=1).values
        else:
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
            bins=[-0.01, 0.30, 0.60, 1.01],
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
