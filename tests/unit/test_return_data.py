from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from tfm_pipeline.config import ExperimentConfig
from tfm_pipeline.experiment_data import ReturnData, prepare_return_data


def test_prepare_return_data_no_window_requirement(monkeypatch: pytest.MonkeyPatch) -> None:
    """Baseline prep must not fail when validation is too short for windows."""
    dummy_prices = pd.DataFrame(
        {
            "AAPL": np.linspace(100, 200, 200),
            "MSFT": np.linspace(200, 300, 200),
        },
        index=pd.date_range("2020-01-01", periods=200),
    )

    import tfm_pipeline.experiment_data as exp_data_module

    monkeypatch.setattr(exp_data_module, "download_adjusted_close", lambda config: dummy_prices)

    config = ExperimentConfig(
        assets=("AAPL", "MSFT"),
        start_date=date(2020, 1, 1),
        end_date=dummy_prices.index[-1].date(),
        train_end=date(2020, 6, 1),
        validation_end=date(2020, 6, 5),  # very short validation
        window_size=30,
    )
    data = prepare_return_data(config)

    assert isinstance(data, ReturnData)
    assert not data.splits.train.empty
    assert not data.splits.validation.empty
    assert not data.splits.test.empty
