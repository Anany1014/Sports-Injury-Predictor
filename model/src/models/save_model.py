"""
model/src/models/save_model.py
==============================
Train and Save the Best Model (XGBoost) Using Joblib.

Artifacts Saved:
  1. model/artifacts/xgboost_injury_model.joblib   (Trained XGBoost Classifier)
  2. model/artifacts/feature_scaler.joblib          (Fitted StandardScaler)
  3. model/artifacts/feature_names.joblib           (Engineered Feature Column Names List)
  4. model/artifacts/model_metadata.json            (Model Config & Hyperparameters)

Usage:
    python -m model.src.models.save_model
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from imblearn.under_sampling import RandomUnderSampler

from model.src.utils import get_logger

logger = get_logger(__name__)

ROOT = Path(__file__).parents[3]
DATA_PATH = ROOT / "data" / "day_approach_maskedID_timeseries.csv"
ARTIFACTS_DIR = ROOT / "model" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_COL = "injury"
DROP_COLS = ["Athlete ID", "Date"]
RANDOM_STATE = 42
SEP = "=" * 70


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    km_cols = [c for c in df.columns if c.startswith("total km")]
    df["weekly_total_km"] = df[km_cols].sum(axis=1)

    z5_cols = [c for c in df.columns if c.startswith("km Z5-T1-T2")]
    spr_cols = [c for c in df.columns if c.startswith("km sprinting")]
    df["weekly_high_intensity_km"] = df[z5_cols].sum(axis=1) + df[spr_cols].sum(axis=1)

    exertion_cols = [c for c in df.columns if c.startswith("perceived exertion")]
    df["mean_perceived_exertion"] = df[exertion_cols].mean(axis=1)

    recovery_cols = [c for c in df.columns if c.startswith("perceived recovery")]
    df["mean_perceived_recovery"] = df[recovery_cols].mean(axis=1)

    df["exertion_recovery_ratio"] = df["mean_perceived_exertion"] / (
        df["mean_perceived_recovery"].replace(0, 0.01)
    )

    df["acute_chronic_exertion"] = df["perceived exertion"] / (
        df["mean_perceived_exertion"].replace(0, 0.01)
    )

    return df


def save_trained_model() -> None:
    logger.info(SEP)
    logger.info("  TRAINING & SAVING BEST MODEL (XGBoost) WITH JOBLIB")
    logger.info(SEP)

    # 1. Load Data
    df = pd.read_csv(DATA_PATH)
    df = engineer_features(df)

    feature_cols = [c for c in df.columns if c not in DROP_COLS + [TARGET_COL]]

    groups = df["Athlete ID"].values
    X = df[feature_cols].values
    y = df[TARGET_COL].values

    # 2. Athlete-grouped split (80/20)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_STATE)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # 3. Fit StandardScaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 4. Resample training set (1:2 ratio)
    rus = RandomUnderSampler(sampling_strategy=0.5, random_state=RANDOM_STATE)
    X_train_res, y_train_res = rus.fit_resample(X_train_scaled, y_train)

    scale_pos_w = float((y_train_res == 0).sum() / max(y_train_res.sum(), 1))

    # 5. Instantiate & Train XGBoost
    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_w,
        random_state=RANDOM_STATE,
        verbosity=0,
    )

    logger.info("  Fitting XGBoost model...")
    model.fit(X_train_res, y_train_res)

    # 6. Define output paths
    model_path = ARTIFACTS_DIR / "xgboost_injury_model.joblib"
    scaler_path = ARTIFACTS_DIR / "feature_scaler.joblib"
    features_path = ARTIFACTS_DIR / "feature_names.joblib"
    metadata_path = ARTIFACTS_DIR / "model_metadata.json"

    # 7. Save artifacts using joblib.dump()
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(feature_cols, features_path)

    metadata = {
        "model_type": "XGBClassifier",
        "library": "xgboost 3.3.0",
        "n_estimators": 300,
        "max_depth": 5,
        "learning_rate": 0.03,
        "scale_pos_weight": scale_pos_w,
        "n_features": len(feature_cols),
        "target_col": TARGET_COL,
        "saved_artifacts": {
            "model": str(model_path),
            "scaler": str(scaler_path),
            "feature_names": str(features_path),
        },
    }

    with metadata_path.open("w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(SEP)
    logger.info("  ✅ ARTIFACTS SUCCESSFULLY SAVED VIA JOBLIB:")
    logger.info(f"    1. Model   → {model_path}")
    logger.info(f"    2. Scaler  → {scaler_path}")
    logger.info(f"    3. Features→ {features_path}")
    logger.info(f"    4. Metadata→ {metadata_path}")
    logger.info(SEP)


if __name__ == "__main__":
    save_trained_model()
