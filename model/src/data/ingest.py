"""
model.src.data.ingest
~~~~~~~~~~~~~~~~~~~~~~
Load and validate raw athlete data from CSV / Parquet sources.
Produces a validated DataFrame saved to the processed directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from model.src.utils import env, get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Column schema — used for validation
# ---------------------------------------------------------------------------
REQUIRED_COLUMNS: list[str] = [
    "athlete_id",
    "date",
    "sport",
    "position",
    "age",
    "weight_kg",
    "height_cm",
    # Training load
    "weekly_volume_hrs",
    "weekly_intensity_score",
    # Recovery
    "sleep_hours",
    "hrv_ms",
    "soreness_score",
    "rest_days",
    # Injury history
    "prior_injuries",
    "days_since_last_injury",
    # Target
    "injured",
]


def load_raw_data(file_path: Path) -> pd.DataFrame:
    """Load a CSV or Parquet file into a DataFrame."""
    suffix = file_path.suffix.lower()
    logger.info(f"Loading raw data from: {file_path}")

    if suffix == ".csv":
        df = pd.read_csv(file_path, parse_dates=["date"])
    elif suffix in {".parquet", ".pq"}:
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    logger.info(f"Loaded {len(df):,} rows × {df.shape[1]} columns")
    return df


def validate_schema(df: pd.DataFrame) -> None:
    """Raise ValueError if any required columns are missing."""
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    logger.info("Schema validation passed ✓")


def basic_quality_checks(df: pd.DataFrame) -> pd.DataFrame:
    """Drop complete duplicates and rows where the target is null."""
    n_before = len(df)
    df = df.drop_duplicates()
    df = df.dropna(subset=["injured"])
    logger.info(f"Removed {n_before - len(df):,} duplicate/null-target rows")
    return df


def ingest(raw_file: str | Path | None = None) -> pd.DataFrame:
    """
    Full ingestion pipeline: load → validate → basic QC → save.

    Args:
        raw_file: Path to the raw data file. Defaults to the first CSV/Parquet
                  found in ``DATA_RAW_DIR``.

    Returns:
        Validated, lightly-cleaned DataFrame.
    """
    raw_dir = env.data_raw_dir

    if raw_file is None:
        candidates = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.parquet"))
        if not candidates:
            raise FileNotFoundError(
                f"No CSV/Parquet files found in {raw_dir}. "
                "Place your raw data there and re-run."
            )
        raw_file = candidates[0]
        logger.info(f"Auto-detected raw file: {raw_file}")

    df = load_raw_data(Path(raw_file))
    validate_schema(df)
    df = basic_quality_checks(df)

    # Persist a validated snapshot
    out_path = env.data_processed_dir / "ingested.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    logger.info(f"Saved ingested data → {out_path}")

    return df


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    raw_file_arg = sys.argv[1] if len(sys.argv) > 1 else None
    ingest(raw_file=raw_file_arg)
