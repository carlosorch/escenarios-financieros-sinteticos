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
    aggregate_by_model,
    diagnostic_summary,
    evaluate_portfolios,
    evaluate_synthetic_returns,
)


def run(output_dir: Path = Path("results/timegan_multiseed")) -> tuple[pd.DataFrame, pd.DataFrame]:
    config = ExperimentConfig()
    output_dir.mkdir(parents=True, exist_ok=True)

    prices = download_adjusted_close(config)
    returns = compute_log_returns(prices)
    splits = split_returns(returns, config)
    stats = fit_normalization(splits.train)
    normalized_train = normalize_returns(splits.train, stats)
    train_windows = make_windows(normalized_train, config.window_size)

    all_diagnostics = []
    all_validation_diagnostics = []
    all_portfolios = []
    all_training_history = []

    for seed in config.timegan_seeds:
        print(f"Running TimeGAN seed: {seed}")
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
            seed=seed,
        )
        normalized_synthetic_windows = sample_timegan(
            model=model,
            n_scenarios=config.synthetic_scenarios,
            window_size=config.window_size,
            seed=seed + 2,
        )
        synthetic_windows = denormalize_windows(normalized_synthetic_windows, stats)
        synthetic_returns = windows_to_frame(synthetic_windows, splits.train.columns)
        calibrated_returns = match_training_volatility(synthetic_returns, splits.train)

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
            portfolio_report, _ = evaluate_portfolios(
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

        diagnostics = diagnostic_summary(
            pd.concat(distribution_reports, ignore_index=True),
            pd.concat(summary_reports, ignore_index=True),
        )
        validation_diagnostics = diagnostic_summary(
            pd.concat(validation_distribution_reports, ignore_index=True),
            pd.concat(validation_summary_reports, ignore_index=True),
        )
        portfolios = pd.concat(portfolio_reports, ignore_index=True)

        diagnostics.insert(0, "seed", seed)
        validation_diagnostics.insert(0, "seed", seed)
        portfolios.insert(0, "seed", seed)
        all_diagnostics.append(diagnostics)
        all_validation_diagnostics.append(validation_diagnostics)
        all_portfolios.append(portfolios)
        all_training_history.append(
            pd.DataFrame(
                {
                    "seed": seed,
                    "epoch": range(1, len(history.autoencoder_loss) + 1),
                    "autoencoder_loss": history.autoencoder_loss,
                    "supervisor_loss": history.supervisor_loss,
                    "generator_loss": history.generator_loss,
                    "discriminator_loss": history.discriminator_loss,
                }
            )
        )

    diagnostics = pd.concat(all_diagnostics, ignore_index=True)
    validation_diagnostics = pd.concat(all_validation_diagnostics, ignore_index=True)
    portfolios = pd.concat(all_portfolios, ignore_index=True)
    training_history = pd.concat(all_training_history, ignore_index=True)

    diagnostics.to_csv(output_dir / "diagnostic_summary_by_seed.csv", index=False)
    validation_diagnostics.to_csv(output_dir / "validation_diagnostic_summary_by_seed.csv", index=False)
    portfolios.to_csv(output_dir / "portfolio_metrics_by_seed.csv", index=False)
    training_history.to_csv(output_dir / "training_history_by_seed.csv", index=False)

    diagnostic_aggregate = aggregate_by_model(diagnostics, ["variant"])
    validation_diagnostic_aggregate = aggregate_by_model(validation_diagnostics, ["variant"])
    portfolio_aggregate = aggregate_by_model(portfolios, ["model"])
    diagnostic_aggregate.to_csv(output_dir / "diagnostic_summary.csv", index=False)
    validation_diagnostic_aggregate.to_csv(output_dir / "validation_diagnostic_summary.csv", index=False)
    portfolio_aggregate.to_csv(output_dir / "portfolio_metrics.csv", index=False)

    return validation_diagnostic_aggregate, portfolio_aggregate


if __name__ == "__main__":
    run()
    print("Multi-seed TimeGAN outputs written to results/timegan_multiseed")
