from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import ExperimentConfig
from .data import (
    DatasetSplits,
    NormalizationStats,
    compute_log_returns,
    download_adjusted_close,
    fit_normalization,
    make_windows,
    normalize_returns,
    split_returns,
)


@dataclass(frozen=True)
class ExperimentData:
    """Container for all shared experimental data artifacts."""

    config: ExperimentConfig
    prices: pd.DataFrame
    returns: pd.DataFrame
    splits: DatasetSplits
    normalization_stats: NormalizationStats
    normalized_train: pd.DataFrame
    normalized_validation: pd.DataFrame
    train_windows: np.ndarray
    validation_windows: np.ndarray


def prepare_experiment_data(config: ExperimentConfig) -> ExperimentData:
    """Download prices, compute returns, split, normalise, and window."""
    prices = download_adjusted_close(config)
    returns = compute_log_returns(prices)
    splits = split_returns(returns, config)

    stats = fit_normalization(splits.train)
    normalized_train = normalize_returns(splits.train, stats)
    normalized_validation = normalize_returns(splits.validation, stats)

    train_windows = make_windows(normalized_train, config.window_size)
    validation_windows = make_windows(normalized_validation, config.window_size)

    return ExperimentData(
        config=config,
        prices=prices,
        returns=returns,
        splits=splits,
        normalization_stats=stats,
        normalized_train=normalized_train,
        normalized_validation=normalized_validation,
        train_windows=train_windows,
        validation_windows=validation_windows,
    )
