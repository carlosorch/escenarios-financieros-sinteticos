from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import ExperimentConfig
from .evaluation import (
    correlation_matrix_error,
    distribution_metrics,
    distribution_summary,
    portfolio_metrics,
    weight_concentration,
    weight_entropy,
)
from .optimization import (
    mean_variance_weights,
    mean_variance_weights_from_estimates,
    minimum_variance_weights,
    portfolio_returns,
)


def evaluate_synthetic_returns(
    real_returns: pd.DataFrame,
    synthetic_returns: pd.DataFrame,
    variant: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    distribution_rows = []
    for asset in real_returns.columns:
        row = {"variant": variant, "asset": asset}
        row.update(distribution_metrics(real_returns[asset].to_numpy(), synthetic_returns[asset].to_numpy()))
        distribution_rows.append(row)
    distribution_rows.append(
        {
            "variant": variant,
            "asset": "ALL",
            **distribution_metrics(real_returns.to_numpy(), synthetic_returns.to_numpy()),
            "correlation_matrix_error": correlation_matrix_error(real_returns, synthetic_returns),
        }
    )
    summary = distribution_summary(real_returns, synthetic_returns)
    summary.insert(0, "variant", variant)
    return pd.DataFrame(distribution_rows), summary


def diagnostic_summary(
    distribution_report: pd.DataFrame,
    summary_report: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for variant, metrics in distribution_report.groupby("variant"):
        asset_metrics = metrics[metrics["asset"] != "ALL"]
        all_metrics = metrics[metrics["asset"] == "ALL"].iloc[0]
        variant_summary = summary_report[summary_report["variant"] == variant]
        rows.append(
            {
                "variant": variant,
                "mean_abs_mean_error": float(asset_metrics["mean_error"].abs().mean()),
                "mean_abs_volatility_error": float(asset_metrics["volatility_error"].abs().mean()),
                "mean_jensen_shannon": float(asset_metrics["jensen_shannon"].mean()),
                "mean_wasserstein": float(asset_metrics["wasserstein"].mean()),
                "correlation_matrix_error": float(all_metrics["correlation_matrix_error"]),
                "mean_abs_skewness_error": float(
                    (variant_summary["synthetic_skewness"] - variant_summary["real_skewness"]).abs().mean()
                ),
                "mean_abs_kurtosis_error": float(
                    (variant_summary["synthetic_kurtosis"] - variant_summary["real_kurtosis"]).abs().mean()
                ),
            }
        )
    return pd.DataFrame(rows)


def aggregate_by_model(results: pd.DataFrame, id_columns: list[str]) -> pd.DataFrame:
    metric_columns = [column for column in results.columns if column not in id_columns]
    numeric_metric_columns = [column for column in metric_columns if np.issubdtype(results[column].dtype, np.number)]
    grouped = results.groupby(id_columns, as_index=False)[numeric_metric_columns]
    mean = grouped.mean().add_suffix("_mean")
    std = grouped.std(ddof=1).add_suffix("_std")
    for column in id_columns:
        mean = mean.rename(columns={f"{column}_mean": column})
        std = std.rename(columns={f"{column}_std": column})
    return mean.merge(std, on=id_columns, how="left")


def evaluate_portfolios(
    train_returns: pd.DataFrame,
    synthetic_returns: pd.DataFrame,
    test_returns: pd.DataFrame,
    variant: str,
    config: ExperimentConfig,
) -> tuple[pd.DataFrame, dict[str, object]]:
    historical_mean = train_returns.mean().to_numpy() * config.trading_days_per_year
    cross_sectional_mean = historical_mean.mean()
    shrunk_historical_mean = (
        config.mean_shrinkage_alpha * historical_mean
        + (1.0 - config.mean_shrinkage_alpha) * cross_sectional_mean
    )
    synthetic_cov = synthetic_returns.cov().to_numpy() * config.trading_days_per_year
    portfolio_weights = {
        f"{variant}_minimum_variance": minimum_variance_weights(
            synthetic_returns,
            periods_per_year=config.trading_days_per_year,
        ),
        f"{variant}_markowitz": mean_variance_weights(
            synthetic_returns,
            periods_per_year=config.trading_days_per_year,
        ),
        f"{variant}_historical_mean_synthetic_covariance": mean_variance_weights_from_estimates(
            historical_mean,
            synthetic_cov,
        ),
        f"{variant}_shrunk_mean_synthetic_covariance": mean_variance_weights_from_estimates(
            shrunk_historical_mean,
            synthetic_cov,
        ),
    }
    rows = []
    for name, weights in portfolio_weights.items():
        test_portfolio_returns = portfolio_returns(test_returns, weights)
        rows.append(
            {
                "model": name,
                **portfolio_metrics(
                    test_portfolio_returns,
                    periods_per_year=config.trading_days_per_year,
                    risk_free_rate=config.risk_free_rate,
                ),
                "weight_entropy": weight_entropy(weights),
                "weight_concentration": weight_concentration(weights),
            }
        )
    return pd.DataFrame(rows), portfolio_weights


def write_portfolio_weights(
    output_dir: Path,
    portfolio_weights: dict[str, object],
    assets: tuple[str, ...],
) -> None:
    for name, weights in portfolio_weights.items():
        with (output_dir / f"{name}_weights.json").open("w", encoding="utf-8") as file:
            json.dump(dict(zip(assets, weights.tolist())), file, indent=2)
