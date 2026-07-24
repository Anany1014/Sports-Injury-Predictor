"""
Tests for data ingestion: schema validation, quality checks, and file loading.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from model.src.data.ingest import basic_quality_checks, validate_schema, REQUIRED_COLUMNS


@pytest.fixture()
def valid_df() -> pd.DataFrame:
    """Minimal valid DataFrame with all required columns."""
    return pd.DataFrame(
        {col: [1] for col in REQUIRED_COLUMNS}
    )


def test_validate_schema_passes_with_all_columns(valid_df: pd.DataFrame) -> None:
    validate_schema(valid_df)  # should not raise


def test_validate_schema_raises_on_missing_column(valid_df: pd.DataFrame) -> None:
    df = valid_df.drop(columns=["injured"])
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_schema(df)


def test_basic_quality_checks_removes_duplicates() -> None:
    df = pd.DataFrame({col: [1, 1] for col in REQUIRED_COLUMNS})
    result = basic_quality_checks(df)
    assert len(result) == 1


def test_basic_quality_checks_removes_null_target() -> None:
    df = pd.DataFrame({col: [1, None] for col in REQUIRED_COLUMNS})
    df["injured"] = [1, None]
    result = basic_quality_checks(df)
    assert result["injured"].notna().all()
