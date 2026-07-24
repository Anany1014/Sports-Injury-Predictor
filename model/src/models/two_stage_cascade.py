"""
model/src/models/two_stage_cascade.py
======================================
Two-Stage Cascade Architecture for Sports Injury Prediction.

Architecture:
  Stage 1: High-Recall Screening Model (XGBoost @ T1 = 0.15)
           • Goal: Catch 95%+ of ALL real injuries.
           • Output: Filters out ~70% of obvious healthy days.

  Stage 2: High-Precision Refinement Model (Random Forest @ T2 = 0.40)
           • Goal: Evaluates ONLY the flagged candidates from Stage 1.
           • Output: Filters out false alarms.

Run:
    python -m model.src.models.two_stage_cascade
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler
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

    # Per-athlete normalization
    for col in ["total km", "perceived exertion", "perceived recovery"]:
        m = df.groupby("Athlete ID")[col].transform("mean")
        s = df.groupby("Athlete ID")[col].transform("std").replace(0, 1)
        df[f"{col}_ath_zscore"] = (df[col] - m) / s

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

    df["workload_spike"] = df["total km"] - df["total km.1"]
    df["exertion_spike"] = df["perceived exertion"] - df["perceived exertion.1"]

    return df


class TwoStageCascadeClassifier:
    def __init__(self, t1: float = 0.15, t2: float = 0.40, random_state: int = 42):
        self.t1 = t1
        self.t2 = t2
        self.random_state = random_state

        self.stage1_model = XGBClassifier(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=self.random_state,
            verbosity=0,
        )

        self.stage2_model = RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            class_weight="balanced",
            n_jobs=-1,
            random_state=self.random_state,
        )

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, scale_pos_w: float) -> TwoStageCascadeClassifier:
        # Fit Stage 1 (XGBoost)
        self.stage1_model.set_params(scale_pos_weight=scale_pos_w)
        self.stage1_model.fit(X_train, y_train)

        # Stage 1 Predictions on training set
        stage1_train_proba = self.stage1_model.predict_proba(X_train)[:, 1]
        stage1_train_pass_idx = np.where(stage1_train_proba >= self.t1)[0]

        # Fit Stage 2 ONLY on candidates that passed Stage 1
        X_train_stage2 = X_train[stage1_train_pass_idx]
        y_train_stage2 = y_train[stage1_train_pass_idx]

        logger.info(
            f"Stage 1 Training: Passed {len(X_train_stage2):,}/{len(X_train):,} rows to Stage 2 ({y_train_stage2.sum()} injuries)"
        )

        self.stage2_model.fit(X_train_stage2, y_train_stage2)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        stage1_proba = self.stage1_model.predict_proba(X)[:, 1]
        stage1_passed_mask = stage1_proba >= self.t1

        final_preds = np.zeros(len(X), dtype=int)

        if np.any(stage1_passed_mask):
            X_passed = X[stage1_passed_mask]
            stage2_proba = self.stage2_model.predict_proba(X_passed)[:, 1]
            stage2_preds = (stage2_proba >= self.t2).astype(int)

            final_preds[stage1_passed_mask] = stage2_preds

        return final_preds

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        stage1_proba = self.stage1_model.predict_proba(X)[:, 1]
        stage2_proba = np.zeros(len(X))

        stage1_passed_mask = stage1_proba >= self.t1
        if np.any(stage1_passed_mask):
            X_passed = X[stage1_passed_mask]
            stage2_proba[stage1_passed_mask] = self.stage2_model.predict_proba(X_passed)[:, 1]

        cascade_proba = np.where(stage1_passed_mask, 0.5 * (stage1_proba + stage2_proba), stage1_proba * 0.5)
        return np.column_stack([1 - cascade_proba, cascade_proba])

    def save(self, artifacts_dir: Path) -> None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.stage1_model, artifacts_dir / "cascade_stage1.joblib")
        joblib.dump(self.stage2_model, artifacts_dir / "cascade_stage2.joblib")
        joblib.dump({"t1": self.t1, "t2": self.t2}, artifacts_dir / "cascade_config.joblib")

    @classmethod
    def load(cls, artifacts_dir: Path) -> TwoStageCascadeClassifier:
        config = joblib.load(artifacts_dir / "cascade_config.joblib")
        instance = cls(t1=config["t1"], t2=config["t2"])
        instance.stage1_model = joblib.load(artifacts_dir / "cascade_stage1.joblib")
        instance.stage2_model = joblib.load(artifacts_dir / "cascade_stage2.joblib")
        return instance


def main() -> None:
    logger.info(SEP)
    logger.info("  TWO-STAGE CASCADE CLASSIFIER (Dataset 2)")
    logger.info("  Stage 1: High-Recall Screening (XGBoost) → Stage 2: High-Precision Refinement (RF)")
    logger.info(SEP)

    df = pd.read_csv(DATA_PATH)
    df = engineer_features(df)

    feature_cols = [c for c in df.columns if c not in DROP_COLS + [TARGET_COL]]

    groups = df["Athlete ID"].values
    X = df[feature_cols].values
    y = df[TARGET_COL].values

    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_STATE)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    rus = RandomUnderSampler(sampling_strategy=0.5, random_state=RANDOM_STATE)
    X_train_res, y_train_res = rus.fit_resample(X_train_s, y_train)

    scale_pos_w = float((y_train_res == 0).sum() / max(y_train_res.sum(), 1))

    # Evaluate Cascade Configuration Across Cutoff Tiers
    cascade_configs = [
        ("High-Recall Cascade", 0.05, 0.20),
        ("Balanced-Cascade (Dual Acc+Recall)", 0.15, 0.40),
        ("High-Accuracy Cascade", 0.25, 0.55),
    ]

    logger.info(SEP)
    logger.info("  TWO-STAGE CASCADE BENCHMARK RESULTS")
    logger.info(SEP)
    logger.info(
        f"  {'Cascade Configuration':<35} {'Accuracy':<10} {'Recall':<10} {'Precision':<11} {'F1':<8} {'Caught':<10} {'False Alarms':<12}"
    )
    logger.info(f"  {'-'*95}")

    total_injuries = int(y_test.sum())

    for label, t1, t2 in cascade_configs:
        cascade = TwoStageCascadeClassifier(t1=t1, t2=t2, random_state=RANDOM_STATE)
        cascade.fit(X_train_res, y_train_res, scale_pos_w)

        final_preds = cascade.predict(X_test_s)
        cm = confusion_matrix(y_test, final_preds)
        tn, fp, fn, tp = cm.ravel()

        acc = accuracy_score(y_test, final_preds)
        rec = recall_score(y_test, final_preds, zero_division=0)
        prec = precision_score(y_test, final_preds, zero_division=0)
        f1 = f1_score(y_test, final_preds, zero_division=0)

        logger.info(
            f"  {label:<35} {acc*100:<9.1f}% {rec*100:<9.1f}% {prec*100:<10.2f}% {f1:<8.4f} {tp}/{total_injuries:<10} {fp:<12,}"
        )

    # Train and save final cascade model
    final_cascade = TwoStageCascadeClassifier(t1=0.15, t2=0.40, random_state=RANDOM_STATE)
    final_cascade.fit(X_train_res, y_train_res, scale_pos_w)

    final_cascade.save(ARTIFACTS_DIR)
    joblib.dump(scaler, ARTIFACTS_DIR / "two_stage_scaler.joblib")
    joblib.dump(feature_cols, ARTIFACTS_DIR / "two_stage_features.joblib")

    logger.info(SEP)
    logger.info("  ✅ Two-Stage Cascade Model saved → model/artifacts/cascade_stage1.joblib & cascade_stage2.joblib")
    logger.info(SEP)


if __name__ == "__main__":
    main()
