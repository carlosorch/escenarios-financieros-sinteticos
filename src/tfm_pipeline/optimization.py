from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def equal_weights(n_assets: int) -> np.ndarray:
    return np.repeat(1.0 / n_assets, n_assets)


def portfolio_returns(returns: pd.DataFrame, weights: np.ndarray) -> pd.Series:
    return pd.Series(returns.to_numpy() @ weights, index=returns.index, name="portfolio_return")


def minimum_variance_weights(returns: pd.DataFrame, periods_per_year: int = 252) -> np.ndarray:
    cov = returns.cov().to_numpy() * periods_per_year
    n_assets = cov.shape[0]
    initial = equal_weights(n_assets)
    constraints = {"type": "eq", "fun": lambda weights: np.sum(weights) - 1.0}
    bounds = [(0.0, 1.0)] * n_assets

    result = minimize(
        lambda weights: float(weights.T @ cov @ weights),
        initial,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    if not result.success:
        raise RuntimeError(f"Minimum variance optimization failed: {result.message}")
    return result.x


def mean_variance_weights(
    returns: pd.DataFrame,
    risk_aversion: float = 1.0,
    periods_per_year: int = 252,
) -> np.ndarray:
    mean = returns.mean().to_numpy() * periods_per_year
    cov = returns.cov().to_numpy() * periods_per_year
    n_assets = cov.shape[0]
    initial = equal_weights(n_assets)
    constraints = {"type": "eq", "fun": lambda weights: np.sum(weights) - 1.0}
    bounds = [(0.0, 1.0)] * n_assets

    def objective(weights: np.ndarray) -> float:
        expected_return = float(weights @ mean)
        variance = float(weights.T @ cov @ weights)
        return -(expected_return - risk_aversion * variance)

    result = minimize(
        objective,
        initial,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    if not result.success:
        raise RuntimeError(f"Mean-variance optimization failed: {result.message}")
    return result.x


def mean_variance_weights_from_estimates(
    mean: np.ndarray,
    cov: np.ndarray,
    risk_aversion: float = 1.0,
) -> np.ndarray:
    n_assets = len(mean)
    initial = equal_weights(n_assets)
    constraints = {"type": "eq", "fun": lambda weights: np.sum(weights) - 1.0}
    bounds = [(0.0, 1.0)] * n_assets

    def objective(weights: np.ndarray) -> float:
        expected_return = float(weights @ mean)
        variance = float(weights.T @ cov @ weights)
        return -(expected_return - risk_aversion * variance)

    result = minimize(
        objective,
        initial,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    if not result.success:
        raise RuntimeError(f"Mean-variance optimization failed: {result.message}")
    return result.x
