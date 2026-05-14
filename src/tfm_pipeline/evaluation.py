from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon
from scipy.stats import entropy, wasserstein_distance


EPSILON = 1e-12


def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    annualized_log_return = float(returns.mean() * periods_per_year)
    return float(np.expm1(annualized_log_return))


def annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    return float(returns.std(ddof=1) * np.sqrt(periods_per_year))


def sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    ann_return = annualized_return(returns, periods_per_year)
    ann_vol = annualized_volatility(returns, periods_per_year)
    if ann_vol < EPSILON:
        return np.nan
    return float((ann_return - risk_free_rate) / ann_vol)


def max_drawdown(returns: pd.Series) -> float:
    wealth = np.exp(returns.cumsum())
    drawdown = wealth / wealth.cummax() - 1.0
    return float(drawdown.min())


def value_at_risk(returns: pd.Series, confidence_level: float = 0.95) -> float:
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be between 0 and 1")
    return float(returns.quantile(1.0 - confidence_level))


def conditional_value_at_risk(returns: pd.Series, confidence_level: float = 0.95) -> float:
    threshold = value_at_risk(returns, confidence_level)
    tail_returns = returns[returns <= threshold]
    if tail_returns.empty:
        return threshold
    return float(tail_returns.mean())


def portfolio_metrics(
    returns: pd.Series,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
    var_confidence_level: float = 0.95,
) -> dict[str, float]:
    return {
        "cumulative_return": float(np.expm1(returns.sum())),
        "annualized_return": annualized_return(returns, periods_per_year),
        "annualized_volatility": annualized_volatility(returns, periods_per_year),
        "sharpe_ratio": sharpe_ratio(returns, risk_free_rate, periods_per_year),
        "max_drawdown": max_drawdown(returns),
        "value_at_risk": value_at_risk(returns, var_confidence_level),
        "conditional_value_at_risk": conditional_value_at_risk(returns, var_confidence_level),
    }


def weight_entropy(weights: np.ndarray) -> float:
    weights = np.asarray(weights, dtype=float)
    weights = np.clip(weights, EPSILON, 1.0)
    return float(entropy(weights))


def weight_concentration(weights: np.ndarray) -> float:
    weights = np.asarray(weights, dtype=float)
    return float(np.sum(weights**2))


def histogram_probabilities(
    real: np.ndarray,
    synthetic: np.ndarray,
    bins: int = 50,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    lower = min(float(np.min(real)), float(np.min(synthetic)))
    upper = max(float(np.max(real)), float(np.max(synthetic)))
    edges = np.linspace(lower, upper, bins + 1)
    real_hist, _ = np.histogram(real, bins=edges, density=False)
    synthetic_hist, _ = np.histogram(synthetic, bins=edges, density=False)
    real_prob = real_hist.astype(float) + EPSILON
    synthetic_prob = synthetic_hist.astype(float) + EPSILON
    real_prob /= real_prob.sum()
    synthetic_prob /= synthetic_prob.sum()
    return real_prob, synthetic_prob, edges


def distribution_metrics(real: np.ndarray, synthetic: np.ndarray, bins: int = 50) -> dict[str, float]:
    real = np.asarray(real, dtype=float).ravel()
    synthetic = np.asarray(synthetic, dtype=float).ravel()
    real_prob, synthetic_prob, _ = histogram_probabilities(real, synthetic, bins=bins)
    return {
        "mean_error": float(np.mean(synthetic) - np.mean(real)),
        "volatility_error": float(np.std(synthetic, ddof=1) - np.std(real, ddof=1)),
        "kl_divergence": float(entropy(real_prob, synthetic_prob)),
        "jensen_shannon": float(jensenshannon(real_prob, synthetic_prob) ** 2),
        "real_entropy": float(entropy(real_prob)),
        "synthetic_entropy": float(entropy(synthetic_prob)),
        "wasserstein": float(wasserstein_distance(real, synthetic)),
    }


def correlation_matrix_error(real: pd.DataFrame, synthetic: pd.DataFrame) -> float:
    real_corr = real.corr().to_numpy()
    synthetic_corr = synthetic.corr().to_numpy()
    return float(np.linalg.norm(real_corr - synthetic_corr, ord="fro"))


def autocorrelation_error(real: pd.DataFrame, synthetic: pd.DataFrame, lag: int = 1, absolute: bool = False) -> float:
    if lag < 1:
        raise ValueError("lag must be at least 1")
    real_values = real.abs() if absolute else real
    synthetic_values = synthetic.abs() if absolute else synthetic
    real_autocorr = real_values.apply(lambda series: series.autocorr(lag=lag))
    synthetic_autocorr = synthetic_values.apply(lambda series: series.autocorr(lag=lag))
    differences = (real_autocorr - synthetic_autocorr).dropna()
    if differences.empty:
        return float("nan")
    return float(np.sqrt(np.mean(np.square(differences))))


def distribution_summary(real: pd.DataFrame, synthetic: pd.DataFrame) -> pd.DataFrame:
    rows = []
    quantiles = (0.01, 0.05, 0.5, 0.95, 0.99)
    for asset in real.columns:
        real_series = real[asset]
        synthetic_series = synthetic[asset]
        row = {
            "asset": asset,
            "real_mean": float(real_series.mean()),
            "synthetic_mean": float(synthetic_series.mean()),
            "real_volatility": float(real_series.std(ddof=1)),
            "synthetic_volatility": float(synthetic_series.std(ddof=1)),
            "real_skewness": float(real_series.skew()),
            "synthetic_skewness": float(synthetic_series.skew()),
            "real_kurtosis": float(real_series.kurtosis()),
            "synthetic_kurtosis": float(synthetic_series.kurtosis()),
            "real_min": float(real_series.min()),
            "synthetic_min": float(synthetic_series.min()),
            "real_max": float(real_series.max()),
            "synthetic_max": float(synthetic_series.max()),
        }
        for quantile in quantiles:
            label = int(quantile * 100)
            row[f"real_q{label}"] = float(real_series.quantile(quantile))
            row[f"synthetic_q{label}"] = float(synthetic_series.quantile(quantile))
        rows.append(row)
    return pd.DataFrame(rows)
