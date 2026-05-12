from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from tfm_pipeline.config import ExperimentConfig
from tfm_pipeline.experiment_data import ExperimentData, prepare_experiment_data


def test_prepare_experiment_data_structure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Smoke test that prepare_experiment_data produces consistent artifacts."""
    # Patch download to avoid network calls
    dummy_prices = pd.DataFrame(
        {
            "AAPL": np.linspace(100, 200, 1000),
            "MSFT": np.linspace(200, 300, 1000),
        },
        index=pd.date_range("2015-01-01", periods=1000),
    )

    import tfm_pipeline.experiment_data as exp_data_module

    monkeypatch.setattr(exp_data_module, "download_adjusted_close", lambda config: dummy_prices)

    config = ExperimentConfig(
        assets=("AAPL", "MSFT"),
        start_date=date(2015, 1, 1),
        end_date=dummy_prices.index[-1].date(),
        train_end=date(2016, 6, 1),
        validation_end=date(2017, 3, 1),
        window_size=30,
    )
    data = prepare_experiment_data(config)

    assert isinstance(data, ExperimentData)
    assert data.config == config
    assert list(data.prices.columns) == list(config.assets)
    assert list(data.returns.columns) == list(config.assets)
    assert not data.splits.train.empty
    assert not data.splits.validation.empty
    assert not data.splits.test.empty
    assert data.train_windows.shape[1] == config.window_size
    assert data.train_windows.shape[2] == len(config.assets)
    assert data.validation_windows.shape[1] == config.window_size
