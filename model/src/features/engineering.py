"""
model.src.features.engineering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Derive sport-science features from cleaned athlete data.

Key additions:
- Acute:Chronic Workload Ratio (ACWR)  — primary injury-risk metric
- Rolling averages of volume and intensity
- Recovery score composite
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from model.src.utils import env, get_logger, training_cfg

logger = get_logger(__name__)

ROLLING_WINDOWS: list[int] = training_cfg["features"]["rolling_window_days"]
DROP_COLS: list[str] = training_cfg["features"]["drop_columns"]


# ---------------------------------------------------------------------------
# Individual feature builders
# ---------------------------------------------------------------------------
def add_acwr(df: pd.DataFrame, acute_days: int = 7, chronic_days: int = 28) -> pd.DataFrame:
    """
    Add Acute:Chronic Workload Ratio per athlete.

    ACWR = (mean load over acute window) / (mean load over chronic window)
    Values > 1.5 are associated with significantly higher injury risk.
    """
    df = df.copy().sort_values(["athlete_id", "date"])

    def _acwr(group: pd.DataFrame) -> pd.Series:
        acute = group["weekly_volume_hrs"].rolling(acute_days, min_periods=1).mean()
        chronic = group["weekly_volume_hrs"].rolling(chronic_days, min_periods=1).mean()
        return acute / chronic.replace(0, np.nan)

    df["acwr"] = df.groupby("athlete_id", group_keys=False).apply(_acwr)
    df["acwr"] = df["acwr"].fillna(1.0)
    return df


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add rolling mean & std for volume and intensity over multiple windows."""
    df = df.copy().sort_values(["athlete_id", "date"])
    for window in ROLLING_WINDOWS:
        for col in ["weekly_volume_hrs", "weekly_intensity_score"]:
            df[f"{col}_roll{window}_mean"] = (
                df.groupby("athlete_id")[col]
                .transform(lambda x: x.rolling(window, min_periods=1).mean())
            )
            df[f"{col}_roll{window}_std"] = (
                df.groupby("athlete_id")[col]
                .transform(lambda x: x.rolling(window, min_periods=1).std().fillna(0))
            )
    logger.info(f"Added rolling features for windows: {ROLLING_WINDOWS}")
    return df


def add_recovery_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Composite recovery score (0–1).
    Higher = better recovery = lower injury risk.
    Combines sleep, HRV, soreness, and rest days.
    """
    df = df.copy()
    # Normalize each component to [0, 1] relative to plausible ranges
    sleep_norm = (df["sleep_hours"].clip(4, 10) - 4) / 6          # 4-10h range
    hrv_norm = (df["hrv_ms"].clip(20, 100) - 20) / 80             # 20-100ms range
    soreness_inv = 1 - (df["soreness_score"].clip(0, 10) / 10)    # lower soreness is better
    rest_norm = (df["rest_days"].clip(0, 3) / 3)                  # 0-3 days range

    df["recovery_score"] = (sleep_norm * 0.3 + hrv_norm * 0.3 + soreness_inv * 0.25 + rest_norm * 0.15)
    return df


def add_injury_history_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derived features from injury history columns."""
    df = df.copy()
    df["high_injury_history"] = (df["prior_injuries"] >= 3).astype(int)
    df["recent_injury"] = (df["days_since_last_injury"] < 30).astype(int)
    df["log_days_since_injury"] = np.log1p(df["days_since_last_injury"])
    return df


def drop_non_feature_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove ID and date columns that are not model features."""
    cols_to_drop = [c for c in DROP_COLS if c in df.columns]
    df = df.drop(columns=cols_to_drop)
    logger.info(f"Dropped columns: {cols_to_drop}")
    return df


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def engineer_features(
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> pd.DataFrame:
    """
    Run the full feature-engineering pipeline.

    Args:
        input_path:  Preprocessed Parquet file.
        output_path: Where to save the feature-engineered Parquet.

    Returns:
        Feature-rich DataFrame ready for model training.
    """
    input_path = input_path or (env.data_processed_dir / "preprocessed.parquet")
    output_path = output_path or (env.data_processed_dir / "features.parquet")

    logger.info(f"Reading preprocessed data from {input_path}")
    df = pd.read_parquet(input_path)

    df = add_acwr(df)
    df = add_rolling_features(df)
    df = add_recovery_score(df)
    df = add_injury_history_features(df)
    df = drop_non_feature_columns(df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Feature engineering done → {output_path}  shape={df.shape}")
    logger.info(f"Features: {list(df.columns)}")
    return df


if __name__ == "__main__":
    engineer_features()
