from __future__ import annotations

from dataclasses import dataclass
from datetime import date


DEFAULT_ASSETS = (
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "NVDA",
    "JPM",
    "XOM",
    "JNJ",
    "PG",
)


@dataclass(frozen=True)
class ExperimentConfig:
    assets: tuple[str, ...] = DEFAULT_ASSETS
    start_date: date = date(2015, 1, 1)
    end_date: date = date(2026, 5, 12)
    train_end: date = date(2022, 12, 31)
    validation_end: date = date(2024, 6, 30)
    window_size: int = 30
    trading_days_per_year: int = 252
    risk_free_rate: float = 0.0
    random_seed: int = 42
    vae_latent_dim: int = 16
    vae_hidden_dim: int = 128
    vae_epochs: int = 80
    vae_patience: int = 10
    vae_batch_size: int = 64
    vae_learning_rate: float = 1e-3
    vae_beta: float = 1e-3
    vae_beta_grid: tuple[float, ...] = (0.0, 1e-5, 1e-4, 1e-3)
    timegan_hidden_dim: int = 24
    timegan_noise_dim: int = 10
    timegan_epochs: int = 120
    timegan_batch_size: int = 64
    timegan_learning_rate: float = 1e-3
    timegan_gamma: float = 1.0
    timegan_supervised_weight: float = 100.0
    timegan_reconstruction_weight: float = 10.0
    timegan_seeds: tuple[int, ...] = (42, 43, 44, 45, 46)
    synthetic_scenarios: int = 1000
    mean_shrinkage_alpha: float = 0.25
