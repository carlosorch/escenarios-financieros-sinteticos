from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import ExperimentConfig
from .data import DatasetSplits, NormalizationStats, denormalize_windows, match_training_volatility, windows_to_frame
from .experiment_data import ExperimentData, prepare_experiment_data
from .metadata import write_metadata
from .models.timegan import fit_timegan, sample_timegan
from .synthetic_evaluation import (
    aggregate_by_model,
    diagnostic_summary,
    evaluate_portfolios,
    evaluate_synthetic_returns,
)


def _run_timegan_seed(
    seed: int,
    config: ExperimentConfig,
    train_windows: np.ndarray,
    splits: DatasetSplits,
    stats: NormalizationStats,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run TimeGAN for a single seed and return all reports."""
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

    max_history = max(
        len(history.autoencoder_loss),
        len(history.supervisor_loss),
        len(history.generator_loss),
        len(history.discriminator_loss),
    )
    training_history = pd.DataFrame(
        {
            "seed": seed,
            "epoch": range(1, max_history + 1),
            "autoencoder_loss": history.autoencoder_loss,
            "supervisor_loss": history.supervisor_loss,
            "generator_loss": history.generator_loss,
            "discriminator_loss": history.discriminator_loss,
        }
    )

    return diagnostics, validation_diagnostics, portfolios, training_history, pd.concat(distribution_reports, ignore_index=True)


def run(config: ExperimentConfig | None = None, output_dir: Path = Path("results/timegan_multiseed")) -> tuple[pd.DataFrame, pd.DataFrame]:
    config = config or ExperimentConfig()
    output_dir.mkdir(parents=True, exist_ok=True)

    data = prepare_experiment_data(config)
    splits = data.splits
    train_windows = data.train_windows
    stats = data.normalization_stats

    all_diagnostics = []
    all_validation_diagnostics = []
    all_portfolios = []
    all_training_history = []

    for seed in config.timegan_seeds:
        diagnostics, validation_diagnostics, portfolios, training_history, _ = _run_timegan_seed(
            seed=seed,
            config=config,
            train_windows=train_windows,
            splits=splits,
            stats=stats,
        )
        all_diagnostics.append(diagnostics)
        all_validation_diagnostics.append(validation_diagnostics)
        all_portfolios.append(portfolios)
        all_training_history.append(training_history)

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
    write_metadata(output_dir, config, extra={"runner": "run_timegan_multiseed"})

    return validation_diagnostic_aggregate, portfolio_aggregate


if __name__ == "__main__":
    run()
    print("Multi-seed TimeGAN outputs written to results/timegan_multiseed")
