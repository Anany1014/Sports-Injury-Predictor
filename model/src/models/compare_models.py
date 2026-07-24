"""
model/src/models/compare_models.py
===================================
Model Benchmark: Logistic Regression vs. Random Forest vs. XGBoost vs. LightGBM
===================================

Dataset: day_approach_maskedID_timeseries.csv

Compares 4 Classifiers for Injury Prediction:
  1. Logistic Regression
  2. Random Forest
  3. XGBoost
  4. LightGBM

Evaluates each across 4 Safety / Recall Tiers:
  • Max Safety Mode    (Threshold = 0.05)
  • Early Warning Mode (Threshold = 0.15)
  • High Alert Mode    (Threshold = 0.25)
  • Balanced Mode      (Threshold = 0.45)

Run:
    python -m model.src.models.compare_models
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.preprocessing import StandardScaler
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
SEP = "=" * 80


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


def get_models(scale_pos_w: float) -> dict:
    return {
        "Logistic Regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            max_depth=10,
            class_weight="balanced",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
        "XGBoost": XGBClassifier(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_w,
            random_state=RANDOM_STATE,
            verbosity=0,
        ),
        "LightGBM": LGBMClassifier(
            n_estimators=300,
            max_depth=5,
            num_leaves=31,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            is_unbalance=True,
            random_state=RANDOM_STATE,
            verbose=-1,
        ),
    }


def main() -> None:
    logger.info(SEP)
    logger.info("  MODEL BENCHMARK: Logistic Regression vs Random Forest vs XGBoost vs LightGBM")
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

    total_injuries = int(y_test.sum())
    logger.info(f"  Test Set Size: {len(X_test):,} days  |  Actual Test Injuries: {total_injuries}")

    # Standardize
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # Resample training set (1:2 ratio)
    rus = RandomUnderSampler(sampling_strategy=0.5, random_state=RANDOM_STATE)
    X_train_res, y_train_res = rus.fit_resample(X_train_s, y_train)

    scale_pos_w = float((y_train_res == 0).sum() / max(y_train_res.sum(), 1))

    models = get_models(scale_pos_w)
    thresholds = [0.05, 0.15, 0.25, 0.45]
    mode_names = {0.05: "Max Safety (0.05)", 0.15: "Early Warning (0.15)", 0.25: "High Alert (0.25)", 0.45: "Balanced (0.45)"}

    all_results = []

    for name, clf in models.items():
        logger.info(f"\nTraining {name}...")
        clf.fit(X_train_res, y_train_res)

        y_proba = clf.predict_proba(X_test_s)[:, 1]
        roc_auc = roc_auc_score(y_test, y_proba)
        pr_auc = average_precision_score(y_test, y_proba)

        for th in thresholds:
            y_pred = (y_proba >= th).astype(int)
            cm = confusion_matrix(y_test, y_pred)
            tn, fp, fn, tp = cm.ravel()

            rec = tp / total_injuries
            prec = precision_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            acc = accuracy_score(y_test, y_pred)

            all_results.append({
                "Model": name,
                "Mode": mode_names[th],
                "Threshold": th,
                "ROC-AUC": round(float(roc_auc), 4),
                "PR-AUC": round(float(pr_auc), 4),
                "Accuracy": round(float(acc * 100), 1),
                "Recall %": round(float(rec * 100), 1),
                "Precision %": round(float(prec * 100), 2),
                "F1": round(float(f1), 4),
                "Injuries Caught": f"{tp}/{total_injuries}",
                "False Alarms": int(fp),
            })

    results_df = pd.DataFrame(all_results)

    logger.info("\n" + SEP)
    logger.info("  FULL COMPARISON SUMMARY TABLE")
    logger.info(SEP)

    # Print summary by Mode
    for th in thresholds:
        mode_str = mode_names[th]
        sub = results_df[results_df["Threshold"] == th]
        logger.info(f"\n--- {mode_str.upper()} ---")
        logger.info(
            f"{'Model':<22} {'ROC-AUC':<9} {'PR-AUC':<9} {'Recall %':<11} {'Precision %':<13} {'F1':<8} {'Caught':<10} {'False Alarms':<12}"
        )
        logger.info("-" * 95)
        for _, row in sub.iterrows():
            logger.info(
                f"{row['Model']:<22} {row['ROC-AUC']:<9.4f} {row['PR-AUC']:<9.4f} {row['Recall %']:<11.1f}% {row['Precision %']:<13.2f}% {row['F1']:<8.4f} {row['Injuries Caught']:<10} {row['False Alarms']:<12,}"
            )

    # Save artifact
    with (ARTIFACTS_DIR / "model_comparison_report.json").open("w") as f:
        json.dump(all_results, f, indent=2)

    results_df.to_csv(ARTIFACTS_DIR / "model_comparison_report.csv", index=False)
    logger.info(f"\n✅ Benchmark results saved to model/artifacts/model_comparison_report.csv")


if __name__ == "__main__":
    main()
