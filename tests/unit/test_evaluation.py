from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tfm_pipeline.evaluation import (
    annualized_return,
    annualized_volatility,
    correlation_matrix_error,
    distribution_metrics,
    histogram_probabilities,
    max_drawdown,
    portfolio_metrics,
    sharpe_ratio,
    weight_concentration,
    weight_entropy,
)


class TestAnnualizedReturn:
    def test_zero_returns(self) -> None:
        series = pd.Series([0.0, 0.0, 0.0])
        assert annualized_return(series, periods_per_year=252) == pytest.approx(0.0)

    def test_positive_log_return(self) -> None:
        # 1% daily log return -> simple annualized
        series = pd.Series([np.log(1.01)] * 252)
        result = annualized_return(series, periods_per_year=252)
        assert result == pytest.approx(1.01 ** 252 - 1, rel=1e-6)

    def test_negative_log_return(self) -> None:
        series = pd.Series([np.log(0.99)] * 252)
        result = annualized_return(series, periods_per_year=252)
        assert result < 0


class TestAnnualizedVolatility:
    def test_zero_volatility(self) -> None:
        series = pd.Series([0.01] * 100)
        assert annualized_volatility(series, periods_per_year=252) == pytest.approx(0.0)

    def test_positive_volatility(self) -> None:
        series = pd.Series([0.01, -0.01, 0.01, -0.01])
        result = annualized_volatility(series, periods_per_year=252)
        assert result > 0


class TestSharpeRatio:
    def test_zero_volatility_returns_nan(self) -> None:
        series = pd.Series([0.01] * 100)
        assert np.isnan(sharpe_ratio(series, risk_free_rate=0.0, periods_per_year=252))

    def test_positive_sharpe(self) -> None:
        rng = np.random.default_rng(0)
        series = pd.Series(rng.normal(0.001, 0.02, size=252))
        result = sharpe_ratio(series, risk_free_rate=0.0, periods_per_year=252)
        assert result > 0


class TestMaxDrawdown:
    def test_no_drawdown(self) -> None:
        series = pd.Series([0.001] * 100)
        assert max_drawdown(series) == pytest.approx(0.0, abs=1e-9)

    def test_single_drawdown(self) -> None:
        series = pd.Series([0.0, 0.0, np.log(0.9)])
        result = max_drawdown(series)
        assert result == pytest.approx(-0.1, rel=1e-6)


class TestPortfolioMetrics:
    def test_basic_shape(self) -> None:
        series = pd.Series([0.001] * 100)
        metrics = portfolio_metrics(series, periods_per_year=252, risk_free_rate=0.0)
        expected_keys = {
            "cumulative_return",
            "annualized_return",
            "annualized_volatility",
            "sharpe_ratio",
            "max_drawdown",
        }
        assert set(metrics.keys()) == expected_keys
        assert all(isinstance(v, float) for v in metrics.values())


class TestWeightEntropy:
    def test_uniform_weights_max_entropy(self) -> None:
        weights = np.array([0.25, 0.25, 0.25, 0.25])
        assert weight_entropy(weights) > 0

    def test_single_asset_zero_entropy(self) -> None:
        weights = np.array([1.0, 0.0, 0.0])
        assert weight_entropy(weights) == pytest.approx(0.0, abs=1e-9)


class TestWeightConcentration:
    def test_equal_weights(self) -> None:
        weights = np.array([0.25, 0.25, 0.25, 0.25])
        assert weight_concentration(weights) == pytest.approx(4 * 0.25**2)

    def test_single_asset(self) -> None:
        weights = np.array([1.0, 0.0, 0.0])
        assert weight_concentration(weights) == pytest.approx(1.0)


class TestHistogramProbabilities:
    def test_basic_properties(self) -> None:
        real = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        synthetic = np.array([0.5, 1.5, 2.5, 3.5])
        real_prob, synthetic_prob, edges = histogram_probabilities(real, synthetic, bins=10)
        assert len(real_prob) == len(edges) - 1
        assert pytest.approx(real_prob.sum()) == 1.0
        assert pytest.approx(synthetic_prob.sum()) == 1.0


class TestDistributionMetrics:
    def test_identical_distributions(self) -> None:
        arr = np.random.default_rng(0).normal(size=1000)
        metrics = distribution_metrics(arr, arr.copy(), bins=50)
        assert metrics["mean_error"] == pytest.approx(0.0, abs=1e-9)
        assert metrics["volatility_error"] == pytest.approx(0.0, abs=1e-9)
        assert metrics["wasserstein"] == pytest.approx(0.0, abs=1e-9)

    def test_different_means(self) -> None:
        real = np.zeros(1000)
        synthetic = np.ones(1000)
        metrics = distribution_metrics(real, synthetic, bins=50)
        assert metrics["mean_error"] == pytest.approx(1.0)


class TestCorrelationMatrixError:
    def test_identical(self) -> None:
        df = pd.DataFrame(np.random.default_rng(0).normal(size=(100, 3)), columns=["a", "b", "c"])
        assert correlation_matrix_error(df, df.copy()) == pytest.approx(0.0, abs=1e-9)

    def test_different(self) -> None:
        df1 = pd.DataFrame(np.random.default_rng(0).normal(size=(100, 3)), columns=["a", "b", "c"])
        df2 = pd.DataFrame(np.random.default_rng(1).normal(size=(100, 3)), columns=["a", "b", "c"])
        error = correlation_matrix_error(df1, df2)
        assert error > 0
