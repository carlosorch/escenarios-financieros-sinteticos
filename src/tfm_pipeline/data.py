from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import ExperimentConfig


@dataclass(frozen=True)
class DatasetSplits:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


@dataclass(frozen=True)
class NormalizationStats:
    mean: pd.Series
    std: pd.Series


def download_adjusted_close(config: ExperimentConfig) -> pd.DataFrame:
    import yfinance as yf

    raw = yf.download(
        list(config.assets),
        start=config.start_date.isoformat(),
        end=config.end_date.isoformat(),
        auto_adjust=False,
        progress=False,
    )
    if raw.empty:
        raise ValueError("No price data downloaded from Yahoo Finance")

    if isinstance(raw.columns, pd.MultiIndex):
        if "Adj Close" in raw.columns.get_level_values(0):
            prices = raw["Adj Close"]
        else:
            prices = raw["Close"]
    else:
        prices = raw.to_frame(name=config.assets[0]) if isinstance(raw, pd.Series) else raw

    prices = prices.loc[:, list(config.assets)].dropna(how="any")
    prices.index = pd.to_datetime(prices.index)
    return prices


def compute_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    returns = np.log(prices / prices.shift(1))
    return returns.dropna(how="any")


def split_returns(returns: pd.DataFrame, config: ExperimentConfig) -> DatasetSplits:
    train = returns.loc[: config.train_end.isoformat()]
    validation = returns.loc[
        pd.Timestamp(config.train_end) + pd.Timedelta(days=1) : config.validation_end.isoformat()
    ]
    test = returns.loc[pd.Timestamp(config.validation_end) + pd.Timedelta(days=1) :]

    if train.empty or validation.empty or test.empty:
        raise ValueError("One or more temporal splits are empty")

    return DatasetSplits(train=train, validation=validation, test=test)


def make_windows(returns: pd.DataFrame, window_size: int) -> np.ndarray:
    values = returns.to_numpy(dtype=np.float32)
    if len(values) < window_size:
        raise ValueError("Not enough rows to build windows")
    return np.stack([values[i : i + window_size] for i in range(len(values) - window_size + 1)])


def fit_normalization(train: pd.DataFrame) -> NormalizationStats:
    std = train.std(ddof=1).replace(0.0, 1.0)
    return NormalizationStats(mean=train.mean(), std=std)


def normalize_returns(returns: pd.DataFrame, stats: NormalizationStats) -> pd.DataFrame:
    return (returns - stats.mean) / stats.std


def denormalize_windows(windows: np.ndarray, stats: NormalizationStats) -> np.ndarray:
    mean = stats.mean.to_numpy(dtype=np.float32)
    std = stats.std.to_numpy(dtype=np.float32)
    return windows * std.reshape(1, 1, -1) + mean.reshape(1, 1, -1)


def windows_to_frame(windows: np.ndarray, columns: pd.Index) -> pd.DataFrame:
    values = windows.reshape(-1, windows.shape[-1])
    return pd.DataFrame(values, columns=columns)


def match_training_volatility(synthetic: pd.DataFrame, train: pd.DataFrame) -> pd.DataFrame:
    synthetic_std = synthetic.std(ddof=1).replace(0.0, 1.0)
    train_std = train.std(ddof=1).replace(0.0, 1.0)
    centered = synthetic - synthetic.mean()
    return centered * (train_std / synthetic_std) + train.mean()
