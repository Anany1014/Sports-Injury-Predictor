"""
model.src.models.train
~~~~~~~~~~~~~~~~~~~~~~~
Train a sports injury prediction model with MLflow tracking.

Supports: XGBoost, LightGBM, Random Forest, Logistic Regression.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from xgboost import XGBClassifier

from model.src.utils import env, get_logger, training_cfg

logger = get_logger(__name__)

TARGET = "injured"
RANDOM_STATE = training_cfg["data"]["random_state"]


# ---------------------------------------------------------------------------
# Model factory
# ---------------------------------------------------------------------------
def build_model(model_type: str) -> Any:
    """Instantiate a model based on config."""
    if model_type == "xgboost":
        params = training_cfg["xgboost"]
        return XGBClassifier(**params, use_label_encoder=False, verbosity=0)
    elif model_type == "lightgbm":
        from lightgbm import LGBMClassifier
        return LGBMClassifier(**training_cfg["lightgbm"])
    elif model_type == "random_forest":
        return RandomForestClassifier(
            n_estimators=300, class_weight="balanced", random_state=RANDOM_STATE
        )
    elif model_type == "logistic_regression":
        return LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_STATE)
    else:
        raise ValueError(f"Unknown model type: {model_type}")


# ---------------------------------------------------------------------------
# Training pipeline
# ---------------------------------------------------------------------------
def train(
    features_path: Path | None = None,
    artifacts_dir: Path | None = None,
) -> dict[str, float]:
    """
    Train the injury prediction model.

    Steps:
      1. Load feature-engineered data
      2. Split into train/test
      3. Apply SMOTE to training set
      4. Cross-validate
      5. Final fit on full training data
      6. Save model + log to MLflow

    Args:
        features_path:  Parquet of feature-engineered data.
        artifacts_dir:  Directory to save model artifacts.

    Returns:
        Dict of training metrics.
    """
    features_path = features_path or (env.data_processed_dir / "features.parquet")
    artifacts_dir = artifacts_dir or env.artifacts_dir
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading features from {features_path}")
    df = pd.read_parquet(features_path)

    X = df.drop(columns=[TARGET])
    y = df[TARGET]

    logger.info(f"Class distribution — Injured: {y.sum()} | Not injured: {(y == 0).sum()}")

    # Train/test split
    cfg = training_cfg["data"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=cfg["test_size"],
        random_state=cfg["random_state"],
        stratify=y if cfg["stratify"] else None,
    )

    # SMOTE oversampling on training set
    logger.info("Applying SMOTE to balance training classes …")
    smote = SMOTE(random_state=RANDOM_STATE)
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)

    model_type: str = training_cfg["model"]["type"]
    model = build_model(model_type)

    # ── MLflow run ────────────────────────────────────────────────────────────
    mlflow.set_tracking_uri(env.mlflow_tracking_uri)
    mlflow.set_experiment(env.mlflow_experiment_name)

    with mlflow.start_run(run_name=training_cfg["mlflow"]["run_name"]) as run:
        logger.info(f"MLflow run id: {run.info.run_id}")

        # Cross-validation
        cv_cfg = training_cfg["cv"]
        cv = StratifiedKFold(n_splits=cv_cfg["n_splits"], shuffle=True, random_state=RANDOM_STATE)
        cv_roc = cross_val_score(model, X_train_res, y_train_res, cv=cv, scoring="roc_auc")
        cv_pr  = cross_val_score(model, X_train_res, y_train_res, cv=cv, scoring="average_precision")

        logger.info(f"CV ROC-AUC : {cv_roc.mean():.4f} ± {cv_roc.std():.4f}")
        logger.info(f"CV PR-AUC  : {cv_pr.mean():.4f}  ± {cv_pr.std():.4f}")

        # Final fit
        model.fit(X_train_res, y_train_res)

        # Persist test split for evaluation step
        test_data = X_test.copy()
        test_data[TARGET] = y_test.values
        test_data.to_parquet(artifacts_dir / "test_split.parquet", index=False)

        # Save model
        model_path = artifacts_dir / "model.joblib"
        joblib.dump(model, model_path)
        logger.info(f"Model saved → {model_path}")

        # Save feature names
        feature_names = list(X.columns)
        joblib.dump(feature_names, artifacts_dir / "feature_names.joblib")

        # Log to MLflow
        metrics = {
            "cv_roc_auc_mean": float(cv_roc.mean()),
            "cv_roc_auc_std":  float(cv_roc.std()),
            "cv_pr_auc_mean":  float(cv_pr.mean()),
            "cv_pr_auc_std":   float(cv_pr.std()),
        }
        mlflow.log_params(training_cfg[model_type])
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, artifact_path="model")

    logger.info("Training complete ✓")
    return metrics


if __name__ == "__main__":
    train()
