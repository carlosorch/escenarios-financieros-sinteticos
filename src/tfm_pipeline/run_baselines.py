from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import ExperimentConfig
from .data import compute_log_returns, download_adjusted_close, split_returns
from .evaluation import portfolio_metrics, weight_concentration, weight_entropy
from .experiment_data import prepare_experiment_data
from .metadata import write_metadata
from .optimization import (
    equal_weights,
    mean_variance_weights,
    minimum_variance_weights,
    portfolio_returns,
)


def run(config: ExperimentConfig | None = None, output_dir: Path = Path("results/baselines")) -> pd.DataFrame:
    config = config or ExperimentConfig()
    output_dir.mkdir(parents=True, exist_ok=True)

    data = prepare_experiment_data(config)
    splits = data.splits

    weights = {
        "equal_weight": equal_weights(len(config.assets)),
        "minimum_variance": minimum_variance_weights(
            splits.train,
            periods_per_year=config.trading_days_per_year,
        ),
        "markowitz": mean_variance_weights(
            splits.train,
            periods_per_year=config.trading_days_per_year,
        ),
    }

    rows = []
    for name, model_weights in weights.items():
        test_returns = portfolio_returns(splits.test, model_weights)
        row = {
            "model": name,
            **portfolio_metrics(
                test_returns,
                periods_per_year=config.trading_days_per_year,
                risk_free_rate=config.risk_free_rate,
            ),
            "weight_entropy": weight_entropy(model_weights),
            "weight_concentration": weight_concentration(model_weights),
        }
        rows.append(row)

        with (output_dir / f"{name}_weights.json").open("w", encoding="utf-8") as file:
            json.dump(dict(zip(config.assets, model_weights.tolist())), file, indent=2)

    metrics = pd.DataFrame(rows)
    metrics.to_csv(output_dir / "portfolio_metrics.csv", index=False)
    data.returns.to_csv(output_dir / "log_returns.csv")
    write_metadata(output_dir, config, extra={"runner": "run_baselines"})
    return metrics


if __name__ == "__main__":
    print(run().to_string(index=False))
