"""
model/src/models/train_balanced_timeseries.py
===============================================
High-Recall Injury Prevention Pipeline (Dataset 2)
===============================================

In Sports Medicine AI:
  • Missed Injury (False Negative)  = High Risk (Severe athlete injury / season-ending tear)
  • False Alarm (False Positive)    = Low Risk  (Athlete takes a rest day or modified load)

Therefore, our primary goal is to **MAXIMIZE RECALL (80% – 98%+)** to catch nearly ALL real injury risks before they happen.

Injury Prevention Modes:
  1. Max Safety Mode    (Threshold = 0.05) → **98.7% Recall** (Catches 74 / 75 injuries)
  2. Early Warning Mode (Threshold = 0.15) → **93.3% Recall** (Catches 70 / 75 injuries)
  3. High Alert Mode    (Threshold = 0.25) → **74.7% Recall** (Catches 56 / 75 injuries)
  4. Balanced Mode      (Threshold = 0.45) → **40.0% Recall** (Catches 30 / 75 injuries)

Run:
    python -m model.src.models.train_balanced_timeseries
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
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


def main() -> None:
    logger.info(SEP)
    logger.info("  HIGH-RECALL INJURY PREVENTION PIPELINE (Dataset 2)")
    logger.info("  Goal: Maximize Recall (Up to 98.7%) to Prevent Athlete Injuries")
    logger.info(SEP)

    df = pd.read_csv(DATA_PATH)
    df = engineer_features(df)

    feature_cols = [c for c in df.columns if c not in DROP_COLS + [TARGET_COL]]

    groups = df["Athlete ID"].values
    X = df[feature_cols].values
    y = df[TARGET_COL].values

    # Athlete-grouped split (80/20)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_STATE)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    logger.info(f"  Total Test Rows: {len(X_test):,}  |  Total Test Injuries: {y_test.sum()}")

    # 1. Majority Undersampling (1:2 ratio)
    rus = RandomUnderSampler(sampling_strategy=0.5, random_state=RANDOM_STATE)
    X_train_res, y_train_res = rus.fit_resample(X_train, y_train)

    # 2. Train HistGradientBoosting
    model = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.03,
        max_depth=6,
        class_weight="balanced",
        random_state=RANDOM_STATE,
    )
    model.fit(X_train_res, y_train_res)

    y_proba = model.predict_proba(X_test)[:, 1]

    # Evaluate High-Recall Tiers
    modes = [
        ("Max Safety Mode", 0.05),
        ("Early Warning Mode", 0.15),
        ("High Alert Mode", 0.25),
        ("Balanced Mode", 0.45),
    ]

    logger.info(SEP)
    logger.info("  INJURY PREVENTION SAFETY TIERS")
    logger.info(SEP)
    logger.info(
        f"  {'Safety Mode':<20} {'Threshold':<10} {'Recall (Injuries Caught)':<26} {'Caught / Total':<16} {'False Alarms':<14}"
    )
    logger.info(f"  {'-'*88}")

    total_injuries = y_test.sum()
    results = {}

    for mode_name, th in modes:
        y_pred = (y_proba >= th).astype(int)
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()
        rec = tp / total_injuries
        prec = precision_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        logger.info(
            f"  {mode_name:<20} {th:<10.2f} {rec*100:<25.1f}% {tp:>3} / {total_injuries:<11} {fp:<14,}"
        )
        results[mode_name] = {
            "threshold": th,
            "recall": round(float(rec), 4),
            "precision": round(float(prec), 4),
            "f1": round(float(f1), 4),
            "injuries_caught": int(tp),
            "total_injuries": int(total_injuries),
            "false_alarms": int(fp),
        }

    logger.info(SEP)
    logger.info(f"  ✅ High-Recall Model saved → model/artifacts/high_recall_ts_model.joblib")
    logger.info(SEP)

    joblib.dump(model, ARTIFACTS_DIR / "high_recall_ts_model.joblib")
    joblib.dump(feature_cols, ARTIFACTS_DIR / "high_recall_features.joblib")

    with (ARTIFACTS_DIR / "high_recall_report.json").open("w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
