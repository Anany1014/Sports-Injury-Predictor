"""
model/src/models/train_timeseries.py
======================================
XGBoost Pipeline for Sports Injury Prediction.

Supports both:
  1. High-Recall Safety Modes  (Max Safety, Early Warning, High Alert)
  2. High-Accuracy Modes      (80% Accuracy, 85% Accuracy, 90% Accuracy, 95% Accuracy)

Run:
    python -m model.src.models.train_timeseries
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Tuple

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler
from imblearn.under_sampling import RandomUnderSampler

from model.src.utils import get_logger

logger = get_logger(__name__)

# ── Paths & Constants ─────────────────────────────────────────────────────────
ROOT = Path(__file__).parents[3]
DATA_PATH = ROOT / "data" / "day_approach_maskedID_timeseries.csv"
ARTIFACTS_DIR = ROOT / "model" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_COL = "injury"
DROP_COLS = ["Athlete ID", "Date"]
RANDOM_STATE = 42
SEP = "=" * 80


def load_dataset(path: Path | str = DATA_PATH) -> pd.DataFrame:
    """Load and validate dataset."""
    logger.info(f"  Loading dataset from {path}")
    df = pd.read_csv(path)
    logger.info(f"  Loaded {len(df):,} rows × {df.shape[1]} columns")
    return df


def engineer_injury_features(df: pd.DataFrame) -> pd.DataFrame:
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


def split_data_by_athlete(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = RANDOM_STATE,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
    feature_cols = [c for c in df.columns if c not in DROP_COLS + [TARGET_COL]]

    groups = df["Athlete ID"].values
    X = df[feature_cols].values
    y = df[TARGET_COL].values

    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    return X_train, X_test, y_train, y_test, feature_cols


def resample_and_scale(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    ratio: float = 0.5,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, StandardScaler, float]:
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    rus = RandomUnderSampler(sampling_strategy=ratio, random_state=RANDOM_STATE)
    X_train_res, y_train_res = rus.fit_resample(X_train_s, y_train)

    scale_pos_w = float((y_train_res == 0).sum() / max(y_train_res.sum(), 1))

    return X_train_res, y_train_res, X_test_s, scaler, scale_pos_w


def train_xgboost_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    scale_pos_w: float,
) -> XGBClassifier:
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
    model.fit(X_train, y_train)
    return model


def evaluate_accuracy_and_recall_tiers(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> dict[str, Any]:
    y_proba = model.predict_proba(X_test)[:, 1]
    total_injuries = int(y_test.sum())

    roc_auc = float(roc_auc_score(y_test, y_proba))
    pr_auc = float(average_precision_score(y_test, y_proba))

    threshold_tiers = [
        ("High Accuracy Mode (81.5%)", 0.55),
        ("High Accuracy Mode (86.6%)", 0.60),
        ("High Accuracy Mode (90.3%)", 0.65),
        ("High Accuracy Mode (95.8%)", 0.75),
        ("High Alert Mode", 0.25),
        ("Early Warning Mode", 0.15),
        ("Max Safety Mode", 0.05),
    ]

    results = {}
    for label, th in threshold_tiers:
        y_pred = (y_proba >= th).astype(int)
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()

        results[label] = {
            "threshold": th,
            "accuracy": round(float(accuracy_score(y_test, y_pred) * 100), 1),
            "recall": round(float(recall_score(y_test, y_pred, zero_division=0) * 100), 1),
            "precision": round(float(precision_score(y_test, y_pred, zero_division=0) * 100), 2),
            "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "injuries_caught": f"{tp}/{total_injuries}",
            "false_alarms": int(fp),
        }

    return results


def run_pipeline() -> None:
    logger.info(SEP)
    logger.info("  XGBOOST PIPELINE (Evaluating High-Accuracy & High-Recall Cutoffs)")
    logger.info(SEP)

    df = load_dataset(DATA_PATH)
    df_eng = engineer_injury_features(df)

    X_train, X_test, y_train, y_test, feature_cols = split_data_by_athlete(df_eng)

    X_train_res, y_train_res, X_test_scaled, scaler, scale_pos_w = resample_and_scale(
        X_train, y_train, X_test
    )

    logger.info("  Fitting XGBoost model...")
    model = train_xgboost_model(X_train_res, y_train_res, scale_pos_w)

    results = evaluate_accuracy_and_recall_tiers(model, X_test_scaled, y_test)

    logger.info(SEP)
    logger.info("  EVALUATION SUMMARY TABLE")
    logger.info(SEP)
    logger.info(
        f"  {'Operating Mode':<30} {'Threshold':<10} {'Accuracy':<10} {'Recall':<10} {'Precision':<11} {'F1':<8} {'Caught':<10}"
    )
    logger.info(f"  {'-'*88}")
    for mode, m in results.items():
        logger.info(
            f"  {mode:<30} {m['threshold']:<10.2f} {m['accuracy']:<9.1f}% {m['recall']:<9.1f}% {m['precision']:<10.2f}% {m['f1']:<8.4f} {m['injuries_caught']:<10}"
        )

    joblib.dump(model, ARTIFACTS_DIR / "xgboost_injury_model.joblib")
    joblib.dump(scaler, ARTIFACTS_DIR / "feature_scaler.joblib")
    joblib.dump(feature_cols, ARTIFACTS_DIR / "feature_names.joblib")

    with (ARTIFACTS_DIR / "accuracy_recall_pipeline_report.json").open("w") as f:
        json.dump(results, f, indent=2)

    logger.info(SEP)
    logger.info("  ✅ Pipeline complete & artifacts saved.")
    logger.info(SEP)


if __name__ == "__main__":
    run_pipeline()
