from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tfm_pipeline.config import ExperimentConfig
from tfm_pipeline.data import (
    DatasetSplits,
    NormalizationStats,
    compute_log_returns,
    denormalize_windows,
    fit_normalization,
    make_windows,
    normalize_returns,
    split_returns,
    windows_to_frame,
)


class TestComputeLogReturns:
    def test_basic(self) -> None:
        prices = pd.DataFrame({"a": [100.0, 101.0, 99.0]})
        returns = compute_log_returns(prices)
        assert len(returns) == 2
        assert returns["a"].iloc[0] == pytest.approx(np.log(101 / 100))
        assert returns["a"].iloc[1] == pytest.approx(np.log(99 / 101))

    def test_drops_na(self) -> None:
        prices = pd.DataFrame({"a": [100.0, 101.0, np.nan]})
        returns = compute_log_returns(prices)
        assert len(returns) == 1


class TestSplitReturns:
    def test_non_overlapping(self) -> None:
        config = ExperimentConfig(
            train_end=pd.Timestamp("2020-12-31").date(),
            validation_end=pd.Timestamp("2021-06-30").date(),
        )
        dates = pd.date_range("2020-01-01", "2022-01-01")
        returns = pd.DataFrame({"a": np.zeros(len(dates))}, index=dates)
        splits = split_returns(returns, config)

        assert not splits.train.empty
        assert not splits.validation.empty
        assert not splits.test.empty
        assert splits.train.index.max() <= pd.Timestamp(config.train_end)
        assert splits.validation.index.min() > pd.Timestamp(config.train_end)
        assert splits.validation.index.max() <= pd.Timestamp(config.validation_end)
        assert splits.test.index.min() > pd.Timestamp(config.validation_end)

    def test_empty_split_raises(self) -> None:
        config = ExperimentConfig(
            train_end=pd.Timestamp("2015-01-01").date(),
            validation_end=pd.Timestamp("2015-01-02").date(),
        )
        dates = pd.date_range("2020-01-01", "2020-12-31")
        returns = pd.DataFrame({"a": np.zeros(len(dates))}, index=dates)
        with pytest.raises(ValueError, match="empty"):
            split_returns(returns, config)


class TestMakeWindows:
    def test_basic(self) -> None:
        returns = pd.DataFrame({"a": np.arange(10, dtype=float)})
        windows = make_windows(returns, window_size=3)
        assert windows.shape == (8, 3, 1)
        np.testing.assert_array_equal(windows[0, :, 0], [0.0, 1.0, 2.0])

    def test_too_short_raises(self) -> None:
        returns = pd.DataFrame({"a": [0.0, 1.0]})
        with pytest.raises(ValueError, match="Not enough rows"):
            make_windows(returns, window_size=3)


class TestNormalization:
    def test_fit_normalization_zero_std(self) -> None:
        train = pd.DataFrame({"a": [1.0, 1.0, 1.0]})
        stats = fit_normalization(train)
        assert stats.std["a"] == 1.0

    def test_normalize_denormalize_roundtrip(self) -> None:
        train = pd.DataFrame({"a": [0.0, 1.0, 2.0, 3.0]})
        stats = fit_normalization(train)
        normalized = normalize_returns(train, stats)
        denormalized = normalized * stats.std["a"] + stats.mean["a"]
        pd.testing.assert_series_equal(denormalized["a"], train["a"], check_names=False)

    def test_denormalize_windows(self) -> None:
        stats = NormalizationStats(mean=pd.Series([1.0]), std=pd.Series([2.0]))
        windows = np.array([[[0.0]], [[1.0]]], dtype=np.float32)
        denorm = denormalize_windows(windows, stats)
        np.testing.assert_array_almost_equal(denorm[:, 0, 0], [1.0, 3.0])


class TestWindowsToFrame:
    def test_basic(self) -> None:
        windows = np.array([[[0.0, 1.0], [2.0, 3.0]], [[4.0, 5.0], [6.0, 7.0]]], dtype=np.float32)
        frame = windows_to_frame(windows, pd.Index(["a", "b"]))
        assert frame.shape == (4, 2)
        assert list(frame.columns) == ["a", "b"]
