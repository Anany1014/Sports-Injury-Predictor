"""
Tests for feature engineering functions.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
import pytest

from model.src.features.engineering import (
    add_recovery_score,
    add_injury_history_features,
)


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "athlete_id": ["A1", "A1"],
        "date": pd.to_datetime(["2026-01-01", "2026-01-08"]),
        "sleep_hours": [7.0, 8.0],
        "hrv_ms": [60.0, 70.0],
        "soreness_score": [3.0, 2.0],
        "rest_days": [1, 2],
        "prior_injuries": [3, 1],
        "days_since_last_injury": [20, 100],
        "weekly_volume_hrs": [10.0, 12.0],
    })


def test_recovery_score_range(sample_df: pd.DataFrame) -> None:
    df = add_recovery_score(sample_df)
    assert df["recovery_score"].between(0, 1).all(), "Recovery score must be in [0, 1]"


def test_high_injury_history_flag(sample_df: pd.DataFrame) -> None:
    df = add_injury_history_features(sample_df)
    # First row has 3 prior_injuries → high_injury_history = 1
    assert df["high_injury_history"].iloc[0] == 1
    assert df["high_injury_history"].iloc[1] == 0


def test_recent_injury_flag(sample_df: pd.DataFrame) -> None:
    df = add_injury_history_features(sample_df)
    # First row: 20 days since injury → recent
    assert df["recent_injury"].iloc[0] == 1
    assert df["recent_injury"].iloc[1] == 0
