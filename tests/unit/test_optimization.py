from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tfm_pipeline.optimization import (
    equal_weights,
    mean_variance_weights,
    mean_variance_weights_from_estimates,
    minimum_variance_weights,
    portfolio_returns,
)


class TestEqualWeights:
    def test_sum_to_one(self) -> None:
        for n in [2, 5, 10]:
            w = equal_weights(n)
            assert pytest.approx(w.sum()) == 1.0
            assert pytest.approx(w.min()) == pytest.approx(w.max())

    def test_non_negative(self) -> None:
        w = equal_weights(5)
        assert (w >= 0).all()


class TestPortfolioReturns:
    def test_basic(self) -> None:
        returns = pd.DataFrame(
            {
                "a": [0.01, -0.02, 0.03],
                "b": [0.0, 0.01, -0.01],
            }
        )
        weights = np.array([0.5, 0.5])
        result = portfolio_returns(returns, weights)
        expected = pd.Series([0.005, -0.005, 0.01], name="portfolio_return")
        pd.testing.assert_series_equal(result, expected)

    def test_full_weight(self) -> None:
        returns = pd.DataFrame({"a": [0.01, 0.02], "b": [0.03, 0.04]})
        weights = np.array([1.0, 0.0])
        result = portfolio_returns(returns, weights)
        expected = pd.Series([0.01, 0.02], name="portfolio_return")
        pd.testing.assert_series_equal(result, expected)


class TestMinimumVarianceWeights:
    def test_sum_to_one(self) -> None:
        returns = pd.DataFrame(np.random.default_rng(0).normal(0, 0.02, size=(200, 4)), columns=list("abcd"))
        w = minimum_variance_weights(returns, periods_per_year=252)
        assert pytest.approx(w.sum()) == 1.0

    def test_long_only(self) -> None:
        returns = pd.DataFrame(np.random.default_rng(0).normal(0, 0.02, size=(200, 4)), columns=list("abcd"))
        w = minimum_variance_weights(returns, periods_per_year=252)
        assert (w >= -1e-8).all()  # allow tiny numerical negatives


class TestMeanVarianceWeights:
    def test_sum_to_one(self) -> None:
        returns = pd.DataFrame(np.random.default_rng(0).normal(0.0005, 0.02, size=(200, 4)), columns=list("abcd"))
        w = mean_variance_weights(returns, risk_aversion=1.0, periods_per_year=252)
        assert pytest.approx(w.sum()) == 1.0

    def test_long_only(self) -> None:
        returns = pd.DataFrame(np.random.default_rng(0).normal(0.0005, 0.02, size=(200, 4)), columns=list("abcd"))
        w = mean_variance_weights(returns, risk_aversion=1.0, periods_per_year=252)
        assert (w >= -1e-8).all()


class TestMeanVarianceWeightsFromEstimates:
    def test_sum_to_one(self) -> None:
        mean = np.array([0.05, 0.03, 0.02])
        cov = np.array([[0.04, 0.01, 0.01], [0.01, 0.03, 0.01], [0.01, 0.01, 0.02]])
        w = mean_variance_weights_from_estimates(mean, cov, risk_aversion=1.0)
        assert pytest.approx(w.sum()) == 1.0

    def test_long_only(self) -> None:
        mean = np.array([0.05, 0.03, 0.02])
        cov = np.array([[0.04, 0.01, 0.01], [0.01, 0.03, 0.01], [0.01, 0.01, 0.02]])
        w = mean_variance_weights_from_estimates(mean, cov, risk_aversion=1.0)
        assert (w >= -1e-8).all()
