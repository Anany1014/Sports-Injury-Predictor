"""
Comprehensive Unit Tests for the Preprocessing Pipeline.

Tests all 5 individual transformation steps and the end-to-end `preprocess()` pipeline:
  1. remove_duplicates
  2. impute_numeric   (median)
  3. impute_categorical (mode)
  4. one_hot_encode
  5. standardise_numeric
  6. End-to-end pipeline execution and artifact persistence
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from model.src.data.preprocess import (
    impute_categorical,
    impute_numeric,
    one_hot_encode,
    preprocess,
    remove_duplicates,
    standardise_numeric,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def sample_raw_df() -> pd.DataFrame:
    return pd.DataFrame({
        "age":      [25.0, np.nan, 30.0, 22.0, 25.0],
        "weight":   [70.0, 80.0, np.nan, 65.0, 70.0],
        "sport":    ["Football", None, "Basketball", "Football", "Football"],
        "target":   [0, 1, 0, 1, 0],
    })


# ── Step 1: remove_duplicates ─────────────────────────────────────────────────

class TestRemoveDuplicates:
    def test_removes_exact_duplicates(self) -> None:
        df = pd.DataFrame({"a": [1, 1, 2], "b": [10, 10, 20]})
        result = remove_duplicates(df)
        assert len(result) == 2

    def test_no_duplicates_unchanged(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        result = remove_duplicates(df)
        assert len(result) == 3

    def test_index_reset_after_dedup(self) -> None:
        df = pd.DataFrame({"a": [1, 1, 2]})
        result = remove_duplicates(df)
        assert list(result.index) == list(range(len(result)))


# ── Step 2: impute_numeric (median) ───────────────────────────────────────────

class TestImputeNumeric:
    def test_fills_nan_with_median(self) -> None:
        df = pd.DataFrame({"age": [25.0, np.nan, 30.0, 22.0]})
        result, medians = impute_numeric(df, ["age"], fit=True)
        assert result["age"].isna().sum() == 0
        assert medians["age"] == 25.0

    def test_fit_false_uses_provided_medians(self) -> None:
        medians = {"age": 28.0}
        df_test = pd.DataFrame({"age": [np.nan, 35.0]})
        result, _ = impute_numeric(df_test, ["age"], medians=medians, fit=False)
        assert result["age"].iloc[0] == 28.0


# ── Step 3: impute_categorical (mode) ─────────────────────────────────────────

class TestImputeCategorical:
    def test_fills_nan_with_mode(self) -> None:
        df = pd.DataFrame({"sport": ["Football", None, "Football", "Basketball"]})
        result, modes = impute_categorical(df, ["sport"], fit=True)
        assert result["sport"].isna().sum() == 0
        assert modes["sport"] == "Football"

    def test_fit_false_uses_provided_modes(self) -> None:
        modes = {"sport": "Soccer"}
        df_test = pd.DataFrame({"sport": [None, "Rugby"]})
        result, _ = impute_categorical(df_test, ["sport"], modes=modes, fit=False)
        assert result["sport"].iloc[0] == "Soccer"


# ── Step 4: one_hot_encode ────────────────────────────────────────────────────

class TestOneHotEncode:
    def test_encodes_categorical_cols(self) -> None:
        df = pd.DataFrame({
            "sport": ["Football", "Basketball", "Football"],
            "target": [0, 1, 0],
        })
        result, encoder = one_hot_encode(df, ["sport"], fit=True)
        assert "sport" not in result.columns
        assert "target" in result.columns
        ohe_cols = [c for c in result.columns if c.startswith("sport_")]
        assert len(ohe_cols) == 1

    def test_inference_mode_uses_fitted_encoder(self) -> None:
        df_train = pd.DataFrame({"sport": ["Football", "Basketball"]})
        df_test = pd.DataFrame({"sport": ["Football"]})
        _, encoder = one_hot_encode(df_train, ["sport"], fit=True)
        result, _ = one_hot_encode(df_test, ["sport"], encoder=encoder, fit=False)
        assert "sport" not in result.columns


# ── Step 5: standardise_numeric ───────────────────────────────────────────────

class TestStandardiseNumeric:
    def test_output_has_zero_mean_and_unit_std(self) -> None:
        df = pd.DataFrame({
            "age": [20.0, 30.0, 40.0],
            "target": [0, 1, 0],
        })
        result, scaler = standardise_numeric(df, ["age"], target_col="target", fit=True)
        assert abs(result["age"].mean()) < 1e-10
        assert abs(result["age"].std(ddof=0) - 1.0) < 1e-6
        assert result["target"].tolist() == [0, 1, 0]


# ── End-to-end Pipeline Test ──────────────────────────────────────────────────

class TestEndToEndPipeline:
    def test_pipeline_fit_and_transform(self, sample_raw_df: pd.DataFrame) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            art_dir = Path(tmp_dir)

            # Fit mode
            df_proc = preprocess(
                sample_raw_df,
                fit=True,
                artifacts_dir=art_dir,
            )

            assert len(df_proc) == 4  # 1 duplicate removed
            assert df_proc.isna().sum().sum() == 0
            assert (art_dir / "ohe_encoder.joblib").exists()
            assert (art_dir / "scaler.joblib").exists()

            # Inference mode
            df_new = pd.DataFrame({
                "age": [24.0],
                "weight": [75.0],
                "sport": ["Football"],
                "target": [0],
            })
            df_proc_new = preprocess(
                df_new,
                fit=False,
                artifacts_dir=art_dir,
            )
            assert len(df_proc_new) == 1
            assert df_proc_new.isna().sum().sum() == 0
