"""
model/src/models/explain_shap.py
================================
SHAP (Shapley Additive exPlanations) Module for Sports Injury Prediction.

Explains:
  1. LOCAL PREDICTIONS  : Which specific features pushed a PARTICULAR athlete into High Injury Risk?
  2. GLOBAL EXPLANATION : Which features contribute most across ALL predictions overall?

Usage:
    python -m model.src.models.explain_shap
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from model.src.utils import get_logger

logger = get_logger(__name__)

ROOT = Path(__file__).parents[3]
DATA_PATH = ROOT / "data" / "day_approach_maskedID_timeseries.csv"
ARTIFACTS_DIR = ROOT / "model" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_COL = "injury"
DROP_COLS = ["Athlete ID", "Date"]
RANDOM_STATE = 42
SEP = "=" * 75


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


def explain_prediction_with_shap(
    model: XGBClassifier,
    X_test_df: pd.DataFrame,
    sample_index: int = 0,
) -> dict:
    """
    Explain a SINGLE prediction using TreeSHAP.
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_test_df)

    sample_shap = shap_values[sample_index]
    feature_names = X_test_df.columns
    feature_vals = X_test_df.iloc[sample_index].values
    shap_val_array = sample_shap.values

    # Pair features with SHAP contribution
    shap_df = pd.DataFrame({
        "Feature": feature_names,
        "Value": feature_vals,
        "SHAP_Contribution": shap_val_array,
    })

    # Sort by absolute impact
    shap_df["Abs_Impact"] = shap_df["SHAP_Contribution"].abs()
    shap_df = shap_df.sort_values(by="Abs_Impact", ascending=False).drop(columns=["Abs_Impact"])

    return {
        "base_value": float(sample_shap.base_values),
        "prediction_prob": float(model.predict_proba(X_test_df.iloc[[sample_index]])[0, 1]),
        "top_contributions": shap_df.head(10).to_dict(orient="records"),
    }


def main() -> None:
    logger.info(SEP)
    logger.info("  SHAP MODEL EXPLAINABILITY PIPELINE (TreeSHAP)")
    logger.info("  Explaining Global & Local Feature Contributions for Injury Prediction")
    logger.info(SEP)

    df = pd.read_csv(DATA_PATH)
    df = engineer_features(df)

    feature_cols = [c for c in df.columns if c not in DROP_COLS + [TARGET_COL]]

    groups = df["Athlete ID"].values
    X = df[feature_cols]
    y = df[TARGET_COL]

    # Split
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_STATE)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))

    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    # Scale
    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=feature_cols)
    X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=feature_cols)

    scale_pos_w = (y_train == 0).sum() / max(y_train.sum(), 1)

    # Train XGBoost for TreeSHAP
    model = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.03,
        scale_pos_weight=scale_pos_w,
        random_state=RANDOM_STATE,
        verbosity=0,
    )
    model.fit(X_train_scaled, y_train)

    logger.info(f"  Model trained. Evaluating TreeSHAP on {len(X_test_scaled):,} test instances...")

    # 1. SHAP TreeExplainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_test_scaled)

    # 2. Local Predictions: Find an actual INJURED case in the test set
    injured_test_indices = np.where(y_test.values == 1)[0]
    sample_idx = int(injured_test_indices[0]) if len(injured_test_indices) > 0 else 0

    local_explanation = explain_prediction_with_shap(model, X_test_scaled, sample_index=sample_idx)

    logger.info("\n" + SEP)
    logger.info(f"  LOCAL SHAP EXPLANATION (Athlete Sample #{sample_idx} - ACTUAL INJURY DAY)")
    logger.info(SEP)
    logger.info(f"  Base Expected Value (Prior Risk) : {local_explanation['base_value']:.4f}")
    logger.info(f"  Model Predicted Injury Prob      : {local_explanation['prediction_prob']:.4f}")
    logger.info("\n  Top 10 Feature Contributions to THIS Specific Injury Prediction:")
    logger.info(f"  {'Rank':<5} {'Feature':<35} {'Value':<12} {'SHAP Impact':<12} Direction")
    logger.info(f"  {'-'*75}")

    for rank, item in enumerate(local_explanation["top_contributions"], 1):
        contrib = item["SHAP_Contribution"]
        direction = "🔴 INCREASES Injury Risk" if contrib > 0 else "🟢 DECREASES Injury Risk"
        logger.info(f"  {rank:<5} {item['Feature']:<35} {item['Value']:<12.3f} {contrib:<+12.4f} {direction}")

    # 3. Global SHAP Summary
    logger.info("\n" + SEP)
    logger.info("  GLOBAL SHAP SUMMARY (Overall Top Features across All Predictions)")
    logger.info(SEP)

    mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
    global_df = pd.DataFrame({
        "Feature": feature_cols,
        "Mean_|SHAP|_Impact": mean_abs_shap,
    }).sort_values(by="Mean_|SHAP|_Impact", ascending=False).reset_index(drop=True)

    logger.info(f"  {'Rank':<5} {'Feature':<35} {'Mean |SHAP| Impact':<20}")
    logger.info(f"  {'-'*60}")
    for rank, row in global_df.head(10).iterrows():
        logger.info(f"  {rank+1:<5} {row['Feature']:<35} {row['Mean_|SHAP|_Impact']:<20.4f}")

    # 4. Save SHAP Summary Plot
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values.values, X_test_scaled, feature_names=feature_cols, show=False, max_display=12)
    plt.title("SHAP Feature Importance (Summary Plot)", fontsize=14)
    plt.tight_layout()
    plot_path = ARTIFACTS_DIR / "shap_summary_plot.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close()

    logger.info(f"\n  ✅ SHAP Summary Plot saved → {plot_path}")

    # Export report
    report = {
        "sample_index_explained": sample_idx,
        "local_explanation": local_explanation,
        "global_top_10_shap_impact": global_df.head(10).to_dict(orient="records"),
    }
    with (ARTIFACTS_DIR / "shap_explanation_report.json").open("w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"  ✅ SHAP Explanation Report saved → model/artifacts/shap_explanation_report.json")
    logger.info(SEP)


if __name__ == "__main__":
    main()
