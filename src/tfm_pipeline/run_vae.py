from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import ExperimentConfig
from .data import (
    compute_log_returns,
    denormalize_windows,
    download_adjusted_close,
    fit_normalization,
    match_training_volatility,
    make_windows,
    normalize_returns,
    split_returns,
    windows_to_frame,
)
from .models.vae import fit_vae, sample_vae
from .synthetic_evaluation import (
    evaluate_portfolios,
    evaluate_synthetic_returns,
    write_portfolio_weights,
)


def run(output_dir: Path = Path("results/vae")) -> tuple[pd.DataFrame, pd.DataFrame]:
    config = ExperimentConfig()
    output_dir.mkdir(parents=True, exist_ok=True)

    prices = download_adjusted_close(config)
    returns = compute_log_returns(prices)
    splits = split_returns(returns, config)

    stats = fit_normalization(splits.train)
    normalized_train = normalize_returns(splits.train, stats)
    normalized_validation = normalize_returns(splits.validation, stats)

    train_windows = make_windows(normalized_train, config.window_size)
    validation_windows = make_windows(normalized_validation, config.window_size)

    distribution_reports = []
    summary_reports = []
    portfolio_reports = []
    beta_reports = []

    for beta in config.vae_beta_grid:
        beta_label = f"beta_{beta:g}".replace("-", "m").replace(".", "p")
        model, history = fit_vae(
            train_windows=train_windows,
            validation_windows=validation_windows,
            hidden_dim=config.vae_hidden_dim,
            latent_dim=config.vae_latent_dim,
            epochs=config.vae_epochs,
            batch_size=config.vae_batch_size,
            learning_rate=config.vae_learning_rate,
            beta=beta,
            seed=config.random_seed,
            patience=config.vae_patience,
        )

        normalized_synthetic_windows = sample_vae(
            model=model,
            n_scenarios=config.synthetic_scenarios,
            window_size=config.window_size,
            n_assets=len(config.assets),
            seed=config.random_seed + 1,
        )
        synthetic_windows = denormalize_windows(normalized_synthetic_windows, stats)
        synthetic_returns = windows_to_frame(synthetic_windows, splits.train.columns)
        calibrated_returns = match_training_volatility(synthetic_returns, splits.train)

        synthetic_returns.to_csv(output_dir / f"synthetic_returns_{beta_label}.csv", index=False)
        calibrated_returns.to_csv(output_dir / f"synthetic_returns_{beta_label}_vol_calibrated.csv", index=False)

        training_history = pd.DataFrame(
            {
                "epoch": range(1, len(history.train_loss) + 1),
                "beta": beta,
                "best_epoch": history.best_epoch,
                "train_loss": history.train_loss,
                "train_reconstruction_loss": history.train_reconstruction_loss,
                "train_kl_loss": history.train_kl_loss,
                "validation_loss": history.validation_loss,
                "validation_reconstruction_loss": history.validation_reconstruction_loss,
                "validation_kl_loss": history.validation_kl_loss,
            }
        )
        training_history.to_csv(output_dir / f"training_history_{beta_label}.csv", index=False)

        for variant, variant_returns in {
            f"vae_raw_{beta_label}": synthetic_returns,
            f"vae_vol_calibrated_{beta_label}": calibrated_returns,
        }.items():
            distribution_report, summary_report = evaluate_synthetic_returns(splits.train, variant_returns, variant)
            portfolio_report, portfolio_weights = evaluate_portfolios(
                train_returns=splits.train,
                synthetic_returns=variant_returns,
                test_returns=splits.test,
                variant=variant,
                config=config,
            )
            distribution_reports.append(distribution_report)
            summary_reports.append(summary_report)
            portfolio_reports.append(portfolio_report)
            write_portfolio_weights(output_dir, portfolio_weights, config.assets)

            all_row = distribution_report.loc[distribution_report["asset"] == "ALL"].iloc[0]
            beta_reports.append(
                {
                    "variant": variant,
                    "beta": beta,
                    "best_epoch": history.best_epoch,
                    "final_epoch": len(history.train_loss),
                    "best_validation_loss": min(history.validation_loss),
                    "all_jensen_shannon": all_row["jensen_shannon"],
                    "all_wasserstein": all_row["wasserstein"],
                    "all_volatility_error": all_row["volatility_error"],
                    "correlation_matrix_error": all_row["correlation_matrix_error"],
                }
            )

    distribution_report = pd.concat(distribution_reports, ignore_index=True)
    summary_report = pd.concat(summary_reports, ignore_index=True)
    portfolio_report = pd.concat(portfolio_reports, ignore_index=True)
    beta_report = pd.DataFrame(beta_reports)

    distribution_report.to_csv(output_dir / "distribution_metrics.csv", index=False)
    summary_report.to_csv(output_dir / "distribution_summary.csv", index=False)
    portfolio_report.to_csv(output_dir / "portfolio_metrics.csv", index=False)
    beta_report.to_csv(output_dir / "beta_grid_summary.csv", index=False)

    return distribution_report, portfolio_report


if __name__ == "__main__":
    distribution, portfolio = run()
    print("Distribution metrics")
    print(distribution.to_string(index=False))
    print("\nPortfolio metrics")
    print(portfolio.to_string(index=False))
