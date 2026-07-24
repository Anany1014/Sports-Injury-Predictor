"""
Tests for the stratified train/test split.

Verifies:
  - Correct 80/20 size ratio
  - Class distribution is preserved (stratification quality)
  - No data leakage between train and test
  - Reproducibility with same seed
  - Edge cases: small datasets, error on bad target
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from model.src.data.split import stratified_split


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def balanced_df() -> pd.DataFrame:
    """500 rows per class — perfectly balanced."""
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "feature_a": rng.normal(size=1000),
        "feature_b": rng.uniform(size=1000),
        "target":    ([0] * 500 + [1] * 500),
    })


@pytest.fixture()
def imbalanced_df() -> pd.DataFrame:
    """Mirrors the timeseries dataset: ~98.6% class-0, ~1.4% class-1."""
    rng = np.random.default_rng(1)
    n = 1000
    labels = [0] * 986 + [1] * 14
    return pd.DataFrame({
        "feature_a": rng.normal(size=n),
        "target":    labels,
    })


# ── Size correctness ──────────────────────────────────────────────────────────

class TestSplitSize:
    def test_train_is_80_percent(self, balanced_df: pd.DataFrame) -> None:
        train, test = stratified_split(balanced_df, "target", test_size=0.2)
        assert len(train) == 800

    def test_test_is_20_percent(self, balanced_df: pd.DataFrame) -> None:
        train, test = stratified_split(balanced_df, "target", test_size=0.2)
        assert len(test) == 200

    def test_total_rows_preserved(self, balanced_df: pd.DataFrame) -> None:
        train, test = stratified_split(balanced_df, "target", test_size=0.2)
        assert len(train) + len(test) == len(balanced_df)

    def test_custom_test_size(self, balanced_df: pd.DataFrame) -> None:
        train, test = stratified_split(balanced_df, "target", test_size=0.3)
        assert len(test) == 300
        assert len(train) == 700


# ── Stratification quality ────────────────────────────────────────────────────

class TestStratification:
    def test_balanced_class_ratio_in_train(self, balanced_df: pd.DataFrame) -> None:
        train, _ = stratified_split(balanced_df, "target", test_size=0.2)
        ratio = train["target"].mean()
        assert abs(ratio - 0.5) < 0.02, f"Train class-1 ratio should be ~0.5, got {ratio}"

    def test_balanced_class_ratio_in_test(self, balanced_df: pd.DataFrame) -> None:
        _, test = stratified_split(balanced_df, "target", test_size=0.2)
        ratio = test["target"].mean()
        assert abs(ratio - 0.5) < 0.02, f"Test class-1 ratio should be ~0.5, got {ratio}"

    def test_imbalanced_ratio_preserved_in_train(self, imbalanced_df: pd.DataFrame) -> None:
        full_ratio = imbalanced_df["target"].mean()
        train, _   = stratified_split(imbalanced_df, "target", test_size=0.2)
        train_ratio = train["target"].mean()
        assert abs(train_ratio - full_ratio) < 0.01, (
            f"Train ratio {train_ratio:.4f} drifted too far from full {full_ratio:.4f}"
        )

    def test_imbalanced_ratio_preserved_in_test(self, imbalanced_df: pd.DataFrame) -> None:
        full_ratio = imbalanced_df["target"].mean()
        _, test    = stratified_split(imbalanced_df, "target", test_size=0.2)
        test_ratio = test["target"].mean()
        assert abs(test_ratio - full_ratio) < 0.02, (
            f"Test ratio {test_ratio:.4f} drifted too far from full {full_ratio:.4f}"
        )

    def test_class_counts_correct_balanced(self, balanced_df: pd.DataFrame) -> None:
        train, test = stratified_split(balanced_df, "target", test_size=0.2)
        # 500 of each class; 80% → 400 each in train, 100 each in test
        assert train["target"].value_counts()[0] == 400
        assert train["target"].value_counts()[1] == 400
        assert test["target"].value_counts()[0] == 100
        assert test["target"].value_counts()[1] == 100


# ── No data leakage ───────────────────────────────────────────────────────────

class TestNoLeakage:
    def test_train_test_rows_are_disjoint(self, balanced_df: pd.DataFrame) -> None:
        train, test = stratified_split(balanced_df, "target", test_size=0.2)
        # Using feature values as a proxy for row identity
        train_tuples = set(map(tuple, train[["feature_a", "feature_b"]].values))
        test_tuples  = set(map(tuple, test[["feature_a", "feature_b"]].values))
        overlap = train_tuples & test_tuples
        assert len(overlap) == 0, f"Data leakage: {len(overlap)} rows appear in both splits"

    def test_index_reset_no_gaps(self, balanced_df: pd.DataFrame) -> None:
        train, test = stratified_split(balanced_df, "target", test_size=0.2)
        assert list(train.index) == list(range(len(train)))
        assert list(test.index)  == list(range(len(test)))


# ── Reproducibility ───────────────────────────────────────────────────────────

class TestReproducibility:
    def test_same_seed_same_split(self, balanced_df: pd.DataFrame) -> None:
        train1, test1 = stratified_split(balanced_df, "target", random_state=42)
        train2, test2 = stratified_split(balanced_df, "target", random_state=42)
        pd.testing.assert_frame_equal(train1, train2)
        pd.testing.assert_frame_equal(test1,  test2)

    def test_different_seed_different_split(self, balanced_df: pd.DataFrame) -> None:
        train1, _ = stratified_split(balanced_df, "target", random_state=42)
        train2, _ = stratified_split(balanced_df, "target", random_state=99)
        # Different seeds should (almost certainly) produce different row orders
        assert not train1["feature_a"].equals(train2["feature_a"])


# ── Feature columns preserved ─────────────────────────────────────────────────

class TestColumns:
    def test_all_feature_cols_in_train(self, balanced_df: pd.DataFrame) -> None:
        train, _ = stratified_split(balanced_df, "target")
        assert set(balanced_df.columns) == set(train.columns)

    def test_all_feature_cols_in_test(self, balanced_df: pd.DataFrame) -> None:
        _, test = stratified_split(balanced_df, "target")
        assert set(balanced_df.columns) == set(test.columns)

    def test_target_present_in_both(self, balanced_df: pd.DataFrame) -> None:
        train, test = stratified_split(balanced_df, "target")
        assert "target" in train.columns
        assert "target" in test.columns


# ── Error handling ────────────────────────────────────────────────────────────

class TestErrors:
    def test_raises_on_missing_target_col(self, balanced_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="not found in DataFrame"):
            stratified_split(balanced_df, "nonexistent_column")

    def test_raises_on_single_class(self) -> None:
        df = pd.DataFrame({"x": [1.0, 2.0, 3.0], "target": [0, 0, 0]})
        with pytest.raises(ValueError, match="at least 2 classes"):
            stratified_split(df, "target")
