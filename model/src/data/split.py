"""
model.src.data.split
~~~~~~~~~~~~~~~~~~~~~
Stratified train/test split for Sports Injury Predictor datasets.

Stratified sampling ensures that the class ratio of the target column
(injured / not injured) is preserved in BOTH the training and test sets —
critical for imbalanced datasets like the timeseries data (1.36% injury rate).

Pipeline step:
    preprocessed CSV / Parquet  →  train split  +  test split

Outputs (saved to data/processed/):
    train.parquet
    test.parquet

And a JSON report:
    model/artifacts/split_report.json

Usage:
    python -m model.src.data.split
    python -m model.src.data.split --csv data/injury_data.csv --test-size 0.2 --seed 42
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from model.src.utils import env, get_logger

logger = get_logger(__name__)

SEP = "=" * 65

# Target column mapping for known datasets
TARGET_MAP: dict[str, str] = {
    "injury_data":                          "Likelihood_of_Injury",
    "day_approach_maskedID_timeseries":     "injury",
    "preprocessed_injury":                  "Likelihood_of_Injury",
}


# ─────────────────────────────────────────────────────────────────────────────
# Target detection
# ─────────────────────────────────────────────────────────────────────────────

def _detect_target(df: pd.DataFrame, file_stem: str) -> str:
    """Return the target column name for a given file stem."""
    for key, col in TARGET_MAP.items():
        if key in file_stem and col in df.columns:
            return col
    # Fallback: last column
    logger.warning(
        f"Could not auto-detect target for '{file_stem}'. "
        f"Using last column: '{df.columns[-1]}'"
    )
    return df.columns[-1]


# ─────────────────────────────────────────────────────────────────────────────
# Core split function
# ─────────────────────────────────────────────────────────────────────────────

def stratified_split(
    df: pd.DataFrame,
    target_col: str,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split a DataFrame into train and test sets using **stratified sampling**.

    Stratification guarantees the class distribution of `target_col` is
    identical (within rounding) in both splits.

    Args:
        df:           Full preprocessed DataFrame.
        target_col:   Name of the binary target column.
        test_size:    Fraction of data for the test set (default 0.20 = 20 %).
        random_state: RNG seed for reproducibility.

    Returns:
        (df_train, df_test) — both include features + target column.

    Raises:
        ValueError: If target_col is missing or has < 2 unique values.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")

    unique_classes = df[target_col].nunique()
    if unique_classes < 2:
        raise ValueError(
            f"Target column '{target_col}' must have at least 2 classes "
            f"to perform a stratified split. Found {unique_classes}."
        )

    X = df.drop(columns=[target_col])
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,          # ← key: preserves class ratios
    )

    df_train = X_train.copy()
    df_train[target_col] = y_train.values

    df_test = X_test.copy()
    df_test[target_col] = y_test.values

    return df_train.reset_index(drop=True), df_test.reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────────────────────────────────────

def _class_dist(series: pd.Series) -> dict[str, dict]:
    """Return class counts and percentages as a dict."""
    vc = series.value_counts().sort_index()
    total = len(series)
    return {
        str(cls): {"count": int(cnt), "pct": round(cnt / total * 100, 2)}
        for cls, cnt in vc.items()
    }


def print_split_report(
    df_full: pd.DataFrame,
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    target_col: str,
    test_size: float,
    random_state: int,
) -> dict:
    """Log a detailed split summary and return a report dict."""
    total      = len(df_full)
    n_train    = len(df_train)
    n_test     = len(df_test)
    n_features = df_full.shape[1] - 1

    full_dist  = _class_dist(df_full[target_col])
    train_dist = _class_dist(df_train[target_col])
    test_dist  = _class_dist(df_test[target_col])

    logger.info(SEP)
    logger.info("  STRATIFIED SPLIT REPORT")
    logger.info(SEP)
    logger.info(f"  Strategy       : stratified (sklearn train_test_split)")
    logger.info(f"  Random seed    : {random_state}")
    logger.info(f"  Test size      : {test_size:.0%}")
    logger.info(f"  Target column  : '{target_col}'")
    logger.info(f"  Total features : {n_features}")
    logger.info(SEP)

    # ── Size table ────────────────────────────────────────────────────────────
    logger.info(f"  {'Split':<12} {'Rows':>7}  {'Share':>7}")
    logger.info(f"  {'-'*30}")
    logger.info(f"  {'Full':<12} {total:>7,}  {'100.00%':>7}")
    logger.info(f"  {'Train':<12} {n_train:>7,}  {n_train/total:>7.2%}")
    logger.info(f"  {'Test':<12} {n_test:>7,}  {n_test/total:>7.2%}")
    logger.info("")

    # ── Class distribution table ───────────────────────────────────────────────
    logger.info(f"  {'Class':<8} {'Full':>12} {'Train':>12} {'Test':>12}")
    logger.info(f"  {'-'*48}")
    all_classes = sorted(full_dist.keys())
    for cls in all_classes:
        fd = full_dist.get(cls,  {"count": 0, "pct": 0.0})
        tr = train_dist.get(cls, {"count": 0, "pct": 0.0})
        te = test_dist.get(cls,  {"count": 0, "pct": 0.0})
        logger.info(
            f"  {cls:<8} "
            f"  {fd['count']:>5,} ({fd['pct']:>5.1f}%) "
            f"  {tr['count']:>5,} ({tr['pct']:>5.1f}%) "
            f"  {te['count']:>5,} ({te['pct']:>5.1f}%)"
        )

    logger.info(SEP)

    # ── Stratification quality check ──────────────────────────────────────────
    logger.info("  STRATIFICATION QUALITY CHECK")
    logger.info(f"  {'Class':<8} {'Full %':>8} {'Train %':>8} {'Test %':>8}  {'Drift':>8}")
    logger.info(f"  {'-'*46}")
    max_drift = 0.0
    for cls in all_classes:
        fp = full_dist.get(cls,  {"pct": 0.0})["pct"]
        tp = train_dist.get(cls, {"pct": 0.0})["pct"]
        ep = test_dist.get(cls,  {"pct": 0.0})["pct"]
        drift = abs(ep - fp)
        max_drift = max(max_drift, drift)
        flag = "✅" if drift < 1.0 else "⚠️ "
        logger.info(f"  {cls:<8} {fp:>8.2f} {tp:>8.2f} {ep:>8.2f}  {drift:>6.2f}pp {flag}")

    overall = "✅  Stratification preserved" if max_drift < 1.0 else "⚠️  Drift detected"
    logger.info(f"\n  {overall}  (max class drift = {max_drift:.2f} pp)")
    logger.info(SEP)

    return {
        "total_rows":    total,
        "train_rows":    n_train,
        "test_rows":     n_test,
        "test_size":     test_size,
        "random_state":  random_state,
        "target_col":    target_col,
        "n_features":    n_features,
        "class_distribution": {
            "full":  full_dist,
            "train": train_dist,
            "test":  test_dist,
        },
        "max_class_drift_pp": round(max_drift, 4),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def split(
    csv_path: Path | None = None,
    output_dir: Path | None = None,
    artifacts_dir: Path | None = None,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Full split pipeline: load → stratified split → save → report.

    Args:
        csv_path:      Path to the raw or preprocessed CSV file.
        output_dir:    Directory to save train.parquet and test.parquet.
        artifacts_dir: Directory to save split_report.json.
        test_size:     Fraction for the test set (default 0.20).
        random_state:  RNG seed for reproducibility (default 42).

    Returns:
        (df_train, df_test)
    """
    csv_path      = csv_path      or (Path("data") / "injury_data.csv")
    output_dir    = output_dir    or env.data_processed_dir
    artifacts_dir = artifacts_dir or env.artifacts_dir

    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # ── Load ──────────────────────────────────────────────────────────────────
    logger.info(SEP)
    logger.info(f"  INPUT FILE : {csv_path}")
    logger.info(SEP)

    suffix = csv_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(csv_path)
    elif suffix in {".parquet", ".pq"}:
        df = pd.read_parquet(csv_path)
    else:
        raise ValueError(f"Unsupported format: {suffix}. Use .csv or .parquet")

    logger.info(f"  Loaded {len(df):,} rows × {df.shape[1]} columns")

    # ── Detect target ─────────────────────────────────────────────────────────
    target_col = _detect_target(df, csv_path.stem)

    # ── Split ─────────────────────────────────────────────────────────────────
    df_train, df_test = stratified_split(df, target_col, test_size, random_state)

    # ── Report ────────────────────────────────────────────────────────────────
    report = print_split_report(df, df_train, df_test, target_col, test_size, random_state)

    # ── Save splits ───────────────────────────────────────────────────────────
    train_path = output_dir / "train.parquet"
    test_path  = output_dir / "test.parquet"

    df_train.to_parquet(train_path, index=False)
    df_test.to_parquet(test_path,   index=False)

    logger.info(f"  ✅  Train split saved → {train_path}  ({len(df_train):,} rows)")
    logger.info(f"  ✅  Test split saved  → {test_path}   ({len(df_test):,} rows)")

    # ── Save report ───────────────────────────────────────────────────────────
    report_path = artifacts_dir / "split_report.json"
    with report_path.open("w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"  📄  Split report saved → {report_path}")
    logger.info(SEP)

    return df_train, df_test


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Stratified 80/20 train-test split for sports injury data"
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Path to input CSV or Parquet (default: data/injury_data.csv)",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of data for the test set (default: 0.2)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Output directory for train/test Parquet files",
    )
    args = parser.parse_args()

    split(
        csv_path      = Path(args.csv) if args.csv else None,
        output_dir    = Path(args.out_dir) if args.out_dir else None,
        test_size     = args.test_size,
        random_state  = args.seed,
    )
