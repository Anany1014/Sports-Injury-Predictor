"""
model.src.data.preprocess
~~~~~~~~~~~~~~~~~~~~~~~~~~
Preprocessing pipeline for Sports Injury Predictor datasets.

Steps (in order):
  1. Remove duplicate rows
  2. Impute missing numeric values  → median strategy
  3. Impute missing categorical values → mode strategy
  4. One-hot encode categorical columns
  5. Standardise numeric columns (StandardScaler)

Supports two modes:
  fit=True  → learns all statistics/parameters, saves artifacts  (training)
  fit=False → loads saved artifacts and transforms only          (inference)

Supported datasets (auto-detected by column presence):
  • injury_data.csv               — biometrics dataset
  • day_approach_maskedID_timeseries.csv — rolling training-load dataset

Usage:
    # From project root — processes injury_data.csv by default
    python -m model.src.data.preprocess

    # Specify a different CSV
    python -m model.src.data.preprocess --csv data/day_approach_maskedID_timeseries.csv
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from model.src.utils import env, get_logger

logger = get_logger(__name__)

# ── Column schema for both known datasets ─────────────────────────────────────

# injury_data.csv
INJURY_DATA_TARGET   = "Likelihood_of_Injury"
INJURY_DATA_NUMERIC  = [
    "Player_Age", "Player_Weight", "Player_Height",
    "Previous_Injuries", "Training_Intensity", "Recovery_Time",
]
INJURY_DATA_CATEGORICAL: list[str] = []          # purely numeric dataset

# timeseries dataset — all 73 columns are numeric
TIMESERIES_TARGET = "injury"

SEP = "=" * 65


# ── Helper ────────────────────────────────────────────────────────────────────

def _banner(title: str) -> None:
    logger.info(SEP)
    logger.info(f"  {title}")
    logger.info(SEP)


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Remove duplicates
# ─────────────────────────────────────────────────────────────────────────────

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop exact duplicate rows (all columns match).

    Returns a deduplicated DataFrame and logs how many rows were removed.
    """
    _banner("STEP 1 — Remove Duplicates")
    n_before = len(df)
    df = df.drop_duplicates()
    n_removed = n_before - len(df)

    if n_removed:
        logger.info(f"  Removed {n_removed:,} duplicate rows.")
    else:
        logger.info("  ✅  No duplicate rows found.")

    logger.info(f"  Shape after dedup: {df.shape}")
    return df.reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 & 3: Impute missing values
# ─────────────────────────────────────────────────────────────────────────────

def impute_numeric(
    df: pd.DataFrame,
    numeric_cols: list[str],
    medians: dict[str, float] | None = None,
    fit: bool = True,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """
    Fill missing values in numeric columns with the column **median**.

    Args:
        df:           Input DataFrame.
        numeric_cols: List of numeric column names to impute.
        medians:      Pre-computed medians (used when fit=False).
        fit:          If True, compute medians from df. If False, use provided medians.

    Returns:
        (imputed DataFrame, medians dict)
    """
    _banner("STEP 2 — Impute Numeric (Median)")
    df = df.copy()
    if medians is None:
        medians = {}

    cols_with_nulls = [c for c in numeric_cols if c in df.columns and df[c].isna().any()]

    if not cols_with_nulls:
        logger.info("  ✅  No missing numeric values to impute.")
        if fit:
            medians = {c: float(df[c].median()) for c in numeric_cols if c in df.columns}
        return df, medians

    for col in numeric_cols:
        if col not in df.columns:
            continue
        if fit:
            medians[col] = float(df[col].median())
        fill_val = medians.get(col, 0.0)
        n_missing = int(df[col].isna().sum())
        if n_missing:
            df[col] = df[col].fillna(fill_val)
            logger.info(f"  [{col}]  filled {n_missing} NaN → median={fill_val:.4f}")

    logger.info(f"  Numeric imputation complete. {len(medians)} column(s) tracked.")
    return df, medians


def impute_categorical(
    df: pd.DataFrame,
    categorical_cols: list[str],
    modes: dict[str, Any] | None = None,
    fit: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Fill missing values in categorical columns with the column **mode**.

    Args:
        df:               Input DataFrame.
        categorical_cols: List of categorical column names to impute.
        modes:            Pre-computed modes (used when fit=False).
        fit:              If True, compute modes from df.

    Returns:
        (imputed DataFrame, modes dict)
    """
    _banner("STEP 3 — Impute Categorical (Mode)")
    df = df.copy()
    if modes is None:
        modes = {}

    if not categorical_cols:
        logger.info("  ✅  No categorical columns to impute.")
        return df, modes

    for col in categorical_cols:
        if col not in df.columns:
            continue
        if fit:
            modes[col] = df[col].mode()[0]
        fill_val = modes.get(col)
        n_missing = int(df[col].isna().sum())
        if n_missing and fill_val is not None:
            df[col] = df[col].fillna(fill_val)
            logger.info(f"  [{col}]  filled {n_missing} NaN → mode='{fill_val}'")
        elif not n_missing:
            logger.info(f"  [{col}]  no missing values.")

    return df, modes


# ─────────────────────────────────────────────────────────────────────────────
# Step 4: One-hot encode categorical columns
# ─────────────────────────────────────────────────────────────────────────────

def one_hot_encode(
    df: pd.DataFrame,
    categorical_cols: list[str],
    encoder: OneHotEncoder | None = None,
    fit: bool = True,
) -> tuple[pd.DataFrame, OneHotEncoder | None]:
    """
    One-hot encode categorical columns using sklearn's OneHotEncoder.

    - drop='first'        → avoids multicollinearity (dummy variable trap)
    - handle_unknown='ignore' → safe for unseen categories at inference time

    Args:
        df:               Input DataFrame.
        categorical_cols: Columns to encode (string / object dtype).
        encoder:          Fitted encoder (used when fit=False).
        fit:              If True, fit a new encoder.

    Returns:
        (encoded DataFrame, fitted OneHotEncoder or None if no cat cols)
    """
    _banner("STEP 4 — One-Hot Encode Categorical Columns")
    df = df.copy()

    present_cats = [c for c in categorical_cols if c in df.columns]

    if not present_cats:
        logger.info("  ✅  No categorical columns to encode.")
        return df, encoder

    logger.info(f"  Encoding columns: {present_cats}")

    if fit:
        encoder = OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore")
        encoded_arr = encoder.fit_transform(df[present_cats].astype(str))
    else:
        encoded_arr = encoder.transform(df[present_cats].astype(str))

    ohe_cols = encoder.get_feature_names_out(present_cats)
    ohe_df   = pd.DataFrame(encoded_arr, columns=ohe_cols, index=df.index, dtype=np.float32)

    df = df.drop(columns=present_cats)
    df = pd.concat([df, ohe_df], axis=1)

    logger.info(f"  Generated {len(ohe_cols)} OHE columns: {list(ohe_cols)}")
    logger.info(f"  Shape after encoding: {df.shape}")
    return df, encoder


# ─────────────────────────────────────────────────────────────────────────────
# Step 5: Standardise numeric columns
# ─────────────────────────────────────────────────────────────────────────────

def standardise_numeric(
    df: pd.DataFrame,
    numeric_cols: list[str],
    target_col: str,
    scaler: StandardScaler | None = None,
    fit: bool = True,
) -> tuple[pd.DataFrame, StandardScaler]:
    """
    Apply StandardScaler (zero mean, unit variance) to numeric feature columns.

    The target column is excluded from scaling.

    Args:
        df:           Input DataFrame.
        numeric_cols: Columns to scale (must be in df).
        target_col:   Target/label column — excluded from scaling.
        scaler:       Fitted scaler (used when fit=False).
        fit:          If True, fit and transform. If False, transform only.

    Returns:
        (scaled DataFrame, fitted StandardScaler)
    """
    _banner("STEP 5 — Standardise Numeric Columns")
    df = df.copy()

    cols_to_scale = [c for c in numeric_cols if c in df.columns and c != target_col]

    if not cols_to_scale:
        logger.warning("  No numeric columns found to scale.")
        if scaler is None:
            scaler = StandardScaler()
        return df, scaler

    if fit:
        scaler = StandardScaler()
        df[cols_to_scale] = scaler.fit_transform(df[cols_to_scale])
        means = dict(zip(cols_to_scale, scaler.mean_.round(4)))
        stds  = dict(zip(cols_to_scale, scaler.scale_.round(4)))
        logger.info(f"  Fitted scaler on {len(cols_to_scale)} column(s).")
        logger.info(f"  Means (sample): { {k: means[k] for k in list(means)[:5]} }")
        logger.info(f"  Stds  (sample): { {k: stds[k]  for k in list(stds)[:5]}  }")
    else:
        df[cols_to_scale] = scaler.transform(df[cols_to_scale])
        logger.info(f"  Transformed {len(cols_to_scale)} column(s) using saved scaler.")

    return df, scaler


# ─────────────────────────────────────────────────────────────────────────────
# Dataset detection helper
# ─────────────────────────────────────────────────────────────────────────────

def _detect_dataset(df: pd.DataFrame) -> tuple[list[str], list[str], str]:
    """
    Auto-detect which dataset this is and return (numeric_cols, cat_cols, target).
    Falls back to auto-inference from dtypes for unknown datasets.
    """
    if "Likelihood_of_Injury" in df.columns:
        logger.info("  Detected: injury_data (biometrics) dataset")
        return INJURY_DATA_NUMERIC, INJURY_DATA_CATEGORICAL, INJURY_DATA_TARGET

    if "injury" in df.columns and "nr. sessions" in df.columns:
        logger.info("  Detected: timeseries (training-load) dataset")
        num_cols = [c for c in df.columns if c not in ("injury", "Athlete ID", "Date")]
        return num_cols, [], TIMESERIES_TARGET

    # Generic fallback: auto-infer from dtypes
    logger.warning("  Unknown dataset — auto-inferring column types.")
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    target   = num_cols.pop() if num_cols else ""
    return num_cols, cat_cols, target


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def preprocess(
    csv_path: Path | None = None,
    output_path: Path | None = None,
    artifacts_dir: Path | None = None,
    fit: bool = True,
) -> pd.DataFrame:
    """
    Run the full preprocessing pipeline on a CSV file.

    Pipeline:
        load CSV → remove duplicates → impute numeric (median)
        → impute categorical (mode) → one-hot encode → standardise → save

    Args:
        csv_path:      Path to the raw CSV file.
        output_path:   Where to save the preprocessed Parquet.
        artifacts_dir: Directory to save/load fitted artifacts.
        fit:           True = train mode (fit+transform+save).
                       False = inference mode (load+transform).

    Returns:
        Preprocessed DataFrame (features + target).
    """
    # ── Resolve paths & load ──────────────────────────────────────────────────
    artifacts_dir = Path(artifacts_dir) if artifacts_dir else env.artifacts_dir
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    if isinstance(csv_path, pd.DataFrame):
        df = csv_path.copy()
        file_stem = "in_memory_df"
        output_path = Path(output_path) if output_path else (env.data_processed_dir / "preprocessed.parquet")
    else:
        csv_path = Path(csv_path) if csv_path else (Path("data") / "day_approach_maskedID_timeseries.csv")
        output_path = Path(output_path) if output_path else (env.data_processed_dir / "preprocessed.parquet")
        file_stem = csv_path.stem
        if csv_path.suffix.lower() == ".csv":
            df = pd.read_csv(csv_path)
        else:
            df = pd.read_parquet(csv_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(SEP)
    logger.info(f"  PREPROCESSING PIPELINE — {'FIT' if fit else 'TRANSFORM'} mode")
    logger.info(f"  Output : {output_path}")
    logger.info(SEP)
    logger.info(f"  Loaded {len(df):,} rows × {df.shape[1]} columns")

    # ── Detect dataset schema ─────────────────────────────────────────────────
    numeric_cols, categorical_cols, target_col = _detect_dataset(df)
    logger.info(f"  Target     : {target_col}")
    logger.info(f"  Numeric    : {len(numeric_cols)} columns")
    logger.info(f"  Categorical: {len(categorical_cols)} columns")

    # ── Step 1: Remove duplicates ─────────────────────────────────────────────
    df = remove_duplicates(df)

    # ── Steps 2 & 3: Impute ───────────────────────────────────────────────────
    if fit:
        df, medians = impute_numeric(df, numeric_cols, fit=True)
        df, modes   = impute_categorical(df, categorical_cols, fit=True)
        joblib.dump(medians, artifacts_dir / "impute_medians.joblib")
        joblib.dump(modes,   artifacts_dir / "impute_modes.joblib")
        logger.info("  Saved imputation artifacts.")
    else:
        medians = joblib.load(artifacts_dir / "impute_medians.joblib")
        modes   = joblib.load(artifacts_dir / "impute_modes.joblib")
        df, _   = impute_numeric(df, numeric_cols, medians=medians, fit=False)
        df, _   = impute_categorical(df, categorical_cols, modes=modes, fit=False)

    # ── Step 4: One-hot encode ─────────────────────────────────────────────────
    if fit:
        df, ohe_encoder = one_hot_encode(df, categorical_cols, fit=True)
        if ohe_encoder:
            joblib.dump(ohe_encoder, artifacts_dir / "ohe_encoder.joblib")
            logger.info("  Saved OHE encoder artifact.")
    else:
        if categorical_cols:
            ohe_encoder = joblib.load(artifacts_dir / "ohe_encoder.joblib")
            df, _ = one_hot_encode(df, categorical_cols, encoder=ohe_encoder, fit=False)

    # ── Step 5: Standardise ────────────────────────────────────────────────────
    # After OHE, numeric feature columns = all columns except the target
    all_feature_cols = [c for c in df.columns if c != target_col]

    if fit:
        df, scaler = standardise_numeric(df, all_feature_cols, target_col, fit=True)
        joblib.dump(scaler, artifacts_dir / "scaler.joblib")
        # Save column order for inference alignment
        joblib.dump(all_feature_cols, artifacts_dir / "feature_names.joblib")
        logger.info("  Saved scaler and feature_names artifacts.")
    else:
        scaler   = joblib.load(artifacts_dir / "scaler.joblib")
        feat_names = joblib.load(artifacts_dir / "feature_names.joblib")
        df = df.reindex(columns=feat_names + [target_col], fill_value=0.0)
        df, _ = standardise_numeric(df, feat_names, target_col, scaler=scaler, fit=False)

    # ── Ensure target is integer ───────────────────────────────────────────────
    if target_col in df.columns:
        df[target_col] = df[target_col].astype(int)

    # ── Save ──────────────────────────────────────────────────────────────────
    df.to_parquet(output_path, index=False)
    logger.info(SEP)
    logger.info(f"  ✅  Preprocessing done.")
    logger.info(f"  Final shape : {df.shape}")
    logger.info(f"  Output saved: {output_path}")
    logger.info(SEP)

    # ── Print a concise summary report ────────────────────────────────────────
    _print_summary(df, target_col)

    return df


# ─────────────────────────────────────────────────────────────────────────────
# Summary report
# ─────────────────────────────────────────────────────────────────────────────

def _print_summary(df: pd.DataFrame, target_col: str) -> None:
    """Print a final tabular summary of the preprocessed DataFrame."""
    logger.info("")
    logger.info("  ── POST-PROCESSING SUMMARY ──────────────────────────────")
    logger.info(f"  Rows          : {len(df):,}")
    logger.info(f"  Features      : {df.shape[1] - 1}")
    logger.info(f"  Target column : '{target_col}'")

    remaining_nulls = df.isnull().sum().sum()
    logger.info(f"  Remaining NaNs: {remaining_nulls}")

    if target_col in df.columns:
        vc = df[target_col].value_counts()
        logger.info(f"  Target dist.  :")
        for val, count in vc.items():
            pct = count / len(df) * 100
            logger.info(f"    {val} → {count:,} ({pct:.1f}%)")

    feature_sample = [c for c in df.columns if c != target_col][:5]
    logger.info(f"  Feature sample (first 5): {feature_sample}")
    logger.info("  ─────────────────────────────────────────────────────────")


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess a sports injury CSV dataset")
    parser.add_argument("--csv",    type=str, default=None, help="Path to input CSV file")
    parser.add_argument("--out",    type=str, default=None, help="Path for output Parquet file")
    parser.add_argument("--no-fit", action="store_true",    help="Inference mode: load saved artifacts")
    args = parser.parse_args()

    preprocess(
        csv_path    = Path(args.csv) if args.csv else None,
        output_path = Path(args.out) if args.out else None,
        fit         = not args.no_fit,
    )
