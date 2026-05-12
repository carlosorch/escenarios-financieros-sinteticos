from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import ExperimentConfig
from .data import (
    compute_log_returns,
    denormalize_windows,
    download_adjusted_close,
    fit_normalization,
    make_windows,
    match_training_volatility,
    normalize_returns,
    split_returns,
    windows_to_frame,
)
from .models.timegan import fit_timegan, sample_timegan
from .synthetic_evaluation import (
    diagnostic_summary,
    evaluate_portfolios,
    evaluate_synthetic_returns,
    write_portfolio_weights,
)


def run(output_dir: Path = Path("results/timegan")) -> tuple[pd.DataFrame, pd.DataFrame]:
    config = ExperimentConfig()
    output_dir.mkdir(parents=True, exist_ok=True)

    prices = download_adjusted_close(config)
    returns = compute_log_returns(prices)
    splits = split_returns(returns, config)

    stats = fit_normalization(splits.train)
    normalized_train = normalize_returns(splits.train, stats)
    train_windows = make_windows(normalized_train, config.window_size)

    model, history = fit_timegan(
        train_windows=train_windows,
        hidden_dim=config.timegan_hidden_dim,
        noise_dim=config.timegan_noise_dim,
        epochs=config.timegan_epochs,
        batch_size=config.timegan_batch_size,
        learning_rate=config.timegan_learning_rate,
        gamma=config.timegan_gamma,
        supervised_weight=config.timegan_supervised_weight,
        reconstruction_weight=config.timegan_reconstruction_weight,
        seed=config.random_seed,
    )

    normalized_synthetic_windows = sample_timegan(
        model=model,
        n_scenarios=config.synthetic_scenarios,
        window_size=config.window_size,
        seed=config.random_seed + 2,
    )
    synthetic_windows = denormalize_windows(normalized_synthetic_windows, stats)
    synthetic_returns = windows_to_frame(synthetic_windows, splits.train.columns)
    calibrated_returns = match_training_volatility(synthetic_returns, splits.train)

    synthetic_returns.to_csv(output_dir / "synthetic_returns.csv", index=False)
    calibrated_returns.to_csv(output_dir / "synthetic_returns_vol_calibrated.csv", index=False)

    max_history = max(
        len(history.autoencoder_loss),
        len(history.supervisor_loss),
        len(history.generator_loss),
        len(history.discriminator_loss),
    )
    training_history = pd.DataFrame(
        {
            "epoch": range(1, max_history + 1),
            "autoencoder_loss": history.autoencoder_loss,
            "supervisor_loss": history.supervisor_loss,
            "generator_loss": history.generator_loss,
            "discriminator_loss": history.discriminator_loss,
        }
    )
    training_history.to_csv(output_dir / "training_history.csv", index=False)

    distribution_reports = []
    summary_reports = []
    validation_distribution_reports = []
    validation_summary_reports = []
    portfolio_reports = []
    for variant, variant_returns in {
        "timegan_raw": synthetic_returns,
        "timegan_mean_vol_calibrated": calibrated_returns,
    }.items():
        distribution_report, summary_report = evaluate_synthetic_returns(splits.train, variant_returns, variant)
        validation_distribution_report, validation_summary_report = evaluate_synthetic_returns(
            splits.validation,
            variant_returns,
            variant,
        )
        portfolio_report, portfolio_weights = evaluate_portfolios(
            train_returns=splits.train,
            synthetic_returns=variant_returns,
            test_returns=splits.test,
            variant=variant,
            config=config,
        )
        distribution_reports.append(distribution_report)
        summary_reports.append(summary_report)
        validation_distribution_reports.append(validation_distribution_report)
        validation_summary_reports.append(validation_summary_report)
        portfolio_reports.append(portfolio_report)
        write_portfolio_weights(output_dir, portfolio_weights, config.assets)

    distribution_report = pd.concat(distribution_reports, ignore_index=True)
    summary_report = pd.concat(summary_reports, ignore_index=True)
    validation_distribution_report = pd.concat(validation_distribution_reports, ignore_index=True)
    validation_summary_report = pd.concat(validation_summary_reports, ignore_index=True)
    portfolio_report = pd.concat(portfolio_reports, ignore_index=True)
    diagnostics = diagnostic_summary(distribution_report, summary_report)
    validation_diagnostics = diagnostic_summary(validation_distribution_report, validation_summary_report)

    distribution_report.to_csv(output_dir / "distribution_metrics.csv", index=False)
    summary_report.to_csv(output_dir / "distribution_summary.csv", index=False)
    validation_distribution_report.to_csv(output_dir / "validation_distribution_metrics.csv", index=False)
    validation_summary_report.to_csv(output_dir / "validation_distribution_summary.csv", index=False)
    diagnostics.to_csv(output_dir / "diagnostic_summary.csv", index=False)
    validation_diagnostics.to_csv(output_dir / "validation_diagnostic_summary.csv", index=False)
    portfolio_report.to_csv(output_dir / "portfolio_metrics.csv", index=False)

    return distribution_report, portfolio_report


if __name__ == "__main__":
    run()
    print("TimeGAN outputs written to results/timegan")
