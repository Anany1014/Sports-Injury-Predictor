#!/usr/bin/env python3
"""
model/evaluate_all_models.py
===================================
Master Model Evaluation Suite for Sports Injury Predictor.

Evaluates all model training approaches across the repository and outputs:
  - Precision (%)
  - Recall (%)
  - F1 Score
  - AUC-ROC
  - PR-AUC
  - Accuracy (%)

Runs on:
  python3 model/evaluate_all_models.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Dependency guard for environment switching
missing_deps = []
try:
    import joblib
except ModuleNotFoundError:
    missing_deps.append("joblib")

try:
    import pandas as pd
    import numpy as np
except ModuleNotFoundError:
    missing_deps.append("pandas/numpy")

try:
    import sklearn
except ModuleNotFoundError:
    missing_deps.append("scikit-learn")

if missing_deps:
    anaconda_python = "/opt/anaconda3/bin/python3"
    if os.path.exists(anaconda_python) and sys.executable != anaconda_python:
        os.execv(anaconda_python, [anaconda_python] + sys.argv)

    print("=" * 85)
    print(f"  DEPENDENCY WARNING: Missing Python module(s): {', '.join(missing_deps)}")
    print("=" * 85)
    print(f"  Current Python Interpreter: {sys.executable}\n")
    print("  Please execute using your project's active Python environment:")
    print("    /opt/anaconda3/bin/python3 model/evaluate_all_models.py")
    print("    -or-")
    print("    python3 model/evaluate_all_models.py\n")
    print("  Or install missing dependencies into your current interpreter:")
    print("    pip install joblib pandas scikit-learn xgboost lightgbm imbalanced-learn")
    print("=" * 85)
    sys.exit(1)
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from imblearn.under_sampling import RandomUnderSampler

ROOT = Path(__file__).parents[1]
DATA_PATH = ROOT / "data" / "day_approach_maskedID_timeseries.csv"
INJURY_DATA_PATH = ROOT / "data" / "raw" / "injury_data.csv"
ARTIFACTS_DIR = ROOT / "model" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_COL = "injury"
DROP_COLS = ["Athlete ID", "Date"]
RANDOM_STATE = 42
SEP = "=" * 105


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer sport-science training load features."""
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


def load_and_split_data():
    """Load time-series dataset and generate GroupShuffleSplit test set."""
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

    return {
        "X_train_res": X_train_res,
        "y_train_res": y_train_res,
        "X_test": X_test,
        "X_test_s": X_test_s,
        "y_test": y_test,
        "scale_pos_w": scale_pos_w,
        "feature_cols": feature_cols,
    }


def evaluate_model(name: str, y_test: np.ndarray, y_proba: np.ndarray, threshold: float = 0.50) -> dict:
    """Compute Precision, Recall, F1, AUC-ROC, PR-AUC, and Accuracy metrics."""
    y_pred = (y_proba >= threshold).astype(int)

    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    acc = float(accuracy_score(y_test, y_pred))

    try:
        auc_roc = float(roc_auc_score(y_test, y_proba))
    except Exception:
        auc_roc = 0.5

    try:
        pr_auc = float(average_precision_score(y_test, y_proba))
    except Exception:
        pr_auc = 0.0

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

    return {
        "Training Approach": name,
        "Threshold": round(threshold, 2),
        "Precision %": round(prec * 100, 2),
        "Recall %": round(rec * 100, 2),
        "F1 Score": round(f1, 4),
        "AUC-ROC": round(auc_roc, 4),
        "PR-AUC": round(pr_auc, 4),
        "Accuracy %": round(acc * 100, 2),
        "True Positives": int(tp),
        "False Positives": int(fp),
    }


def main():
    print(SEP)
    print("  SPORTS INJURY PREDICTOR — MASTER MODEL EVALUATION SUITE")
    print(SEP)

    data = load_and_split_data()
    X_train_res = data["X_train_res"]
    y_train_res = data["y_train_res"]
    X_test_s = data["X_test_s"]
    y_test = data["y_test"]
    scale_pos_w = data["scale_pos_w"]

    print(f"Loaded test dataset: {len(y_test):,} samples | Actual injuries in test set: {int(y_test.sum())}\n")

    # Define all training approaches to evaluate
    training_approaches = [
        ("XGBoost Baseline (th=0.50)", XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.03, scale_pos_weight=scale_pos_w, random_state=RANDOM_STATE, verbosity=0), 0.50),
        ("XGBoost F1-Tuned (th=0.25)", XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.03, scale_pos_weight=scale_pos_w, random_state=RANDOM_STATE, verbosity=0), 0.25),
        ("XGBoost High Recall / Max Safety (th=0.15)", XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.03, scale_pos_weight=scale_pos_w, random_state=RANDOM_STATE, verbosity=0), 0.15),
        ("Balanced HistGradientBoosting (th=0.45)", HistGradientBoostingClassifier(max_iter=300, max_depth=5, random_state=RANDOM_STATE), 0.45),
        ("LightGBM Balanced Classifier (th=0.25)", LGBMClassifier(n_estimators=300, max_depth=5, is_unbalance=True, random_state=RANDOM_STATE, verbose=-1), 0.25),
        ("Random Forest Classifier (th=0.25)", RandomForestClassifier(n_estimators=300, max_depth=10, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1), 0.25),
        ("Logistic Regression Classifier (th=0.15)", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE), 0.15),
    ]

    results = []

    for name, clf, th in training_approaches:
        print(f"Evaluating {name}...")
        clf.fit(X_train_res, y_train_res)
        probas = clf.predict_proba(X_test_s)[:, 1]
        metrics = evaluate_model(name, y_test, probas, threshold=th)
        results.append(metrics)

    # Evaluate pre-saved artifact models if present
    artifact_models = [
        ("Saved Artifact: model.pkl", "model.pkl", 0.25),
        ("Saved Artifact: balanced_ts_model.joblib", "balanced_ts_model.joblib", 0.45),
        ("Saved Artifact: high_perf_xgboost_model.joblib", "high_perf_xgboost_model.joblib", 0.25),
        ("Saved Artifact: optimized_ts_model.joblib", "optimized_ts_model.joblib", 0.25),
        ("Saved Artifact: high_recall_ts_model.joblib", "high_recall_ts_model.joblib", 0.15),
    ]

    for label, filename, th in artifact_models:
        filepath = ARTIFACTS_DIR / filename
        if filepath.exists():
            try:
                m = joblib.load(filepath)
                if hasattr(m, "predict_proba"):
                    probas = m.predict_proba(X_test_s)[:, 1]
                    metrics = evaluate_model(label, y_test, probas, threshold=th)
                    results.append(metrics)
            except Exception:
                pass

    results_df = pd.DataFrame(results)

    # Display evaluation table
    print("\n" + SEP)
    print("  MODEL EVALUATION RESULTS (Precision, Recall, F1, AUC-ROC)")
    print(SEP)
    header = f"{'Training Approach':<44s} | {'Precision':<11s} | {'Recall':<11s} | {'F1 Score':<10s} | {'AUC-ROC':<9s} | {'PR-AUC':<9s} | {'Accuracy':<10s}"
    print(header)
    print("-" * len(header))

    for _, row in results_df.iterrows():
        print(
            f"{row['Training Approach']:<44s} | "
            f"{row['Precision %']:8.2f}%   | "
            f"{row['Recall %']:8.2f}%   | "
            f"{row['F1 Score']:10.4f} | "
            f"{row['AUC-ROC']:9.4f} | "
            f"{row['PR-AUC']:9.4f} | "
            f"{row['Accuracy %']:8.2f}%"
        )

    print("-" * len(header))

    # Save artifact files
    csv_path = ARTIFACTS_DIR / "all_models_evaluation_report.csv"
    results_df.to_csv(csv_path, index=False)

    json_path = ARTIFACTS_DIR / "all_models_evaluation_report.json"
    with json_path.open("w") as f:
        json.dump(results, f, indent=2)

    md_path = ARTIFACTS_DIR / "all_models_evaluation_report.md"
    with md_path.open("w") as f:
        f.write("# Model Training Evaluation Report\n\n")
        f.write(f"Evaluated **{len(results)} model training approaches** across test set ({len(y_test):,} samples, {int(y_test.sum())} injuries).\n\n")
        f.write("| Training Approach | Precision | Recall | F1 Score | AUC-ROC | PR-AUC | Accuracy |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for _, r in results_df.iterrows():
            f.write(f"| **{r['Training Approach']}** | {r['Precision %']:.2f}% | {r['Recall %']:.2f}% | {r['F1 Score']:.4f} | {r['AUC-ROC']:.4f} | {r['PR-AUC']:.4f} | {r['Accuracy %']:.2f}% |\n")

    print(f"\n✅ Evaluation complete. Artifacts saved:")
    print(f"   • CSV  : {csv_path}")
    print(f"   • JSON : {json_path}")
    print(f"   • MD   : {md_path}\n")


if __name__ == "__main__":
    main()
