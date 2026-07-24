"""
model/src/data/eda.py
~~~~~~~~~~~~~~~~~~~~~
Exploratory Data Analysis for the Sports Injury Predictor datasets.

Loads both available CSVs and displays:
  1. Dataset info (shape, dtypes, memory)
  2. Missing values (count + percentage)
  3. Summary statistics (numeric + categorical)

Usage:
    python -m model.src.data.eda
    python -m model.src.data.eda --file data/injury_data.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# ── Paths to both available datasets ─────────────────────────────────────────
ROOT = Path(__file__).parents[3]   # project root: model/src/data → model/src → model → root
DATASETS: dict[str, Path] = {
    "Injury Data (biometrics)":        ROOT / "data" / "injury_data.csv",
    "Timeseries Data (training load)": ROOT / "data" / "day_approach_maskedID_timeseries.csv",
}

# ── Display helpers ───────────────────────────────────────────────────────────
SEP = "=" * 70
SEP_THIN = "-" * 70


def section(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def subsection(title: str) -> None:
    print(f"\n{SEP_THIN}")
    print(f"  {title}")
    print(SEP_THIN)


# ── Core display functions ────────────────────────────────────────────────────

def show_dataset_info(df: pd.DataFrame, name: str) -> None:
    """Print shape, dtypes, and memory usage."""
    section(f"📋  DATASET INFO — {name}")

    print(f"\n  Shape         : {df.shape[0]:,} rows  ×  {df.shape[1]} columns")
    mem_mb = df.memory_usage(deep=True).sum() / 1024 ** 2
    print(f"  Memory usage  : {mem_mb:.2f} MB")

    subsection("Column dtypes")
    dtype_counts = df.dtypes.value_counts()
    for dtype, count in dtype_counts.items():
        print(f"  {str(dtype):<15} : {count} column(s)")

    subsection("All columns with dtype")
    dtype_df = pd.DataFrame({
        "Column":    df.columns,
        "Dtype":     df.dtypes.values,
        "Non-Null":  df.notna().sum().values,
        "Null":      df.isna().sum().values,
    })
    print(dtype_df.to_string(index=False))


def show_missing_values(df: pd.DataFrame) -> None:
    """Print missing value counts and percentages per column."""
    section("🔍  MISSING VALUES")

    total_rows = len(df)
    missing = df.isna().sum()
    missing = missing[missing > 0]

    if missing.empty:
        print("\n  ✅  No missing values found!\n")
        return

    mv_df = pd.DataFrame({
        "Column":      missing.index,
        "Missing":     missing.values,
        "Percentage":  (missing.values / total_rows * 100).round(2),
    }).sort_values("Percentage", ascending=False)

    print(f"\n  {len(missing)} column(s) have missing values "
          f"(out of {df.shape[1]} total):\n")
    print(mv_df.to_string(index=False))

    total_missing = df.isna().sum().sum()
    total_cells   = df.size
    print(f"\n  Total missing cells : {total_missing:,} / {total_cells:,} "
          f"({total_missing / total_cells * 100:.2f}%)")


def show_summary_statistics(df: pd.DataFrame) -> None:
    """Print describe() for numeric and categorical columns separately."""
    section("📊  SUMMARY STATISTICS")

    # ── Numeric columns ───────────────────────────────────────────────────────
    num_df = df.select_dtypes(include="number")
    if not num_df.empty:
        subsection(f"Numeric columns  ({num_df.shape[1]})")
        stats = num_df.describe(percentiles=[0.25, 0.5, 0.75]).T
        stats.insert(0, "column", stats.index)
        stats = stats.reset_index(drop=True)
        # Round floats for readability
        float_cols = stats.select_dtypes(include="float").columns
        stats[float_cols] = stats[float_cols].round(4)
        print(stats.to_string(index=False))

    # ── Categorical / object columns ──────────────────────────────────────────
    cat_df = df.select_dtypes(include=["object", "category", "bool"])
    if not cat_df.empty:
        subsection(f"Categorical / object columns  ({cat_df.shape[1]})")
        cat_stats = cat_df.describe().T
        cat_stats.insert(0, "column", cat_stats.index)
        cat_stats = cat_stats.reset_index(drop=True)
        print(cat_stats.to_string(index=False))

    # ── Target column distribution (if present) ───────────────────────────────
    target_candidates = [c for c in df.columns if c.lower() in
                         {"injury", "injured", "likelihood_of_injury"}]
    for target_col in target_candidates:
        subsection(f"Target column: '{target_col}'")
        counts     = df[target_col].value_counts()
        pct        = df[target_col].value_counts(normalize=True) * 100
        dist = pd.DataFrame({"Value": counts.index, "Count": counts.values,
                             "Percentage": pct.values.round(2)})
        print(dist.to_string(index=False))


# ── Main runner ───────────────────────────────────────────────────────────────

def analyse(file_path: Path, label: str) -> None:
    """Load one CSV and run all three display functions."""
    if not file_path.exists():
        print(f"\n⚠️   File not found, skipping: {file_path}")
        return

    print(f"\n{'#' * 70}")
    print(f"  DATASET: {label}")
    print(f"  FILE   : {file_path.name}")
    print(f"{'#' * 70}")

    df = pd.read_csv(file_path)

    show_dataset_info(df, label)
    show_missing_values(df)
    show_summary_statistics(df)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="EDA for Sports Injury Predictor datasets"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to a specific CSV file. If omitted, analyses all known datasets.",
    )
    args = parser.parse_args()

    pd.set_option("display.max_columns", 30)
    pd.set_option("display.width", 120)
    pd.set_option("display.float_format", "{:.4f}".format)

    if args.file:
        p = Path(args.file)
        analyse(p, p.stem.replace("_", " ").title())
    else:
        for label, path in DATASETS.items():
            analyse(path, label)

    print(f"\n{'=' * 70}")
    print("  ✅  EDA complete.")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
