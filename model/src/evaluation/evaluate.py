"""
model.src.evaluation.evaluate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Compute and log comprehensive evaluation metrics for the trained model.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    auc,
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)

from model.src.utils import env, get_logger

logger = get_logger(__name__)

TARGET = "injured"


def plot_roc_curve(y_true: np.ndarray, y_prob: np.ndarray, out_dir: Path) -> None:
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(fpr, tpr, color="#6C63FF", lw=2, label=f"ROC AUC = {roc_auc:.3f}")
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.set(xlabel="False Positive Rate", ylabel="True Positive Rate", title="ROC Curve")
    ax.legend()
    path = out_dir / "roc_curve.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"ROC curve saved → {path}")


def plot_pr_curve(y_true: np.ndarray, y_prob: np.ndarray, out_dir: Path) -> None:
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    pr_auc = average_precision_score(y_true, y_prob)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.step(recall, precision, color="#FF6584", lw=2, where="post", label=f"PR AUC = {pr_auc:.3f}")
    ax.set(xlabel="Recall", ylabel="Precision", title="Precision-Recall Curve", ylim=[0, 1.05])
    ax.legend()
    path = out_dir / "pr_curve.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"PR curve saved → {path}")


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, out_dir: Path) -> None:
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    fig.colorbar(im)
    ax.set(
        xticks=[0, 1], yticks=[0, 1],
        xticklabels=["Not Injured", "Injured"],
        yticklabels=["Not Injured", "Injured"],
        ylabel="True label", xlabel="Predicted label",
        title="Confusion Matrix",
    )
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black")
    path = out_dir / "confusion_matrix.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Confusion matrix saved → {path}")


def evaluate(
    test_path: Path | None = None,
    artifacts_dir: Path | None = None,
) -> dict[str, float]:
    """
    Load the trained model and test split, compute all metrics, save plots.

    Returns:
        Dict of evaluation metrics.
    """
    artifacts_dir = artifacts_dir or env.artifacts_dir
    test_path     = test_path or (artifacts_dir / "test_split.parquet")
    plots_dir     = artifacts_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading test data from {test_path}")
    df_test = pd.read_parquet(test_path)
    X_test  = df_test.drop(columns=[TARGET])
    y_test  = df_test[TARGET].values

    model = joblib.load(artifacts_dir / "model.joblib")
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    # Metrics
    metrics = {
        "roc_auc":         float(roc_auc_score(y_test, y_prob)),
        "pr_auc":          float(average_precision_score(y_test, y_prob)),
        "accuracy":        float((y_pred == y_test).mean()),
    }

    logger.info("── Evaluation Results ─────────────────────────────")
    for k, v in metrics.items():
        logger.info(f"  {k:25s}: {v:.4f}")
    logger.info("\n" + classification_report(y_test, y_pred, target_names=["Not Injured", "Injured"]))

    # Plots
    plot_roc_curve(y_test, y_prob, plots_dir)
    plot_pr_curve(y_test, y_prob, plots_dir)
    plot_confusion_matrix(y_test, y_pred, plots_dir)

    # Persist metrics JSON
    metrics_path = artifacts_dir / "metrics.json"
    with metrics_path.open("w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved → {metrics_path}")

    return metrics


if __name__ == "__main__":
    evaluate()
