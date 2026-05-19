from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_VALIDATION_WEIGHTS: dict[str, float] = {
    "mean_jensen_shannon": 1.0,
    "mean_wasserstein": 1.0,
    "correlation_matrix_error": 1.5,
    "autocorrelation_error": 1.0,
    "absolute_autocorrelation_error": 1.0,
    "mean_abs_kurtosis_error": 1.0,
}


def _normalization_divisor(series: pd.Series) -> float:
    median = float(series.median())
    if not np.isfinite(median) or np.isclose(median, 0.0):
        return 1.0
    return abs(median)


def score_validation_diagnostics(
    diagnostics: pd.DataFrame,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    weights = weights or DEFAULT_VALIDATION_WEIGHTS
    metric_columns = list(weights.keys())
    missing_columns = [column for column in metric_columns if column not in diagnostics.columns]
    if missing_columns:
        missing_list = ", ".join(missing_columns)
        raise ValueError(f"Missing validation diagnostic columns: {missing_list}")

    scored = diagnostics.copy()
    normalization_factors: dict[str, float] = {}
    for column in metric_columns:
        divisor = _normalization_divisor(scored[column])
        normalization_factors[column] = divisor
        scored[f"{column}_normalized"] = scored[column] / divisor

    scored["validation_score"] = 0.0
    for column, weight in weights.items():
        scored["validation_score"] += scored[f"{column}_normalized"] * weight

    scored = scored.sort_values(
        ["validation_score"] + [column for column in ("seed", "variant") if column in scored.columns]
    ).reset_index(drop=True)
    scored.insert(0, "rank", np.arange(1, len(scored) + 1))
    scored.attrs["metrics_used"] = metric_columns
    scored.attrs["normalization_factors"] = normalization_factors
    scored.attrs["weights"] = weights
    return scored


def select_best_seed(scored_diagnostics: pd.DataFrame) -> dict[str, Any]:
    if "validation_score" not in scored_diagnostics.columns:
        raise ValueError("scored_diagnostics must include a validation_score column")
    if scored_diagnostics.empty:
        raise ValueError("scored_diagnostics must not be empty")

    ordered = scored_diagnostics.sort_values(
        ["validation_score"] + [column for column in ("seed", "variant") if column in scored_diagnostics.columns]
    ).reset_index(drop=True)
    best_row = ordered.iloc[0].to_dict()
    if "seed" in best_row:
        try:
            best_row["seed"] = int(best_row["seed"])
        except (TypeError, ValueError):
            pass
    if "validation_score" in best_row:
        try:
            best_row["validation_score"] = float(best_row["validation_score"])
        except (TypeError, ValueError):
            pass
    metrics_used = scored_diagnostics.attrs.get("metrics_used")
    if metrics_used is None:
        metrics_used = [column[: -len("_normalized")] for column in scored_diagnostics.columns if column.endswith("_normalized")]
    best_row["selection_basis"] = "validation diagnostics only; test metrics were not used for selection"
    best_row["metrics_used"] = metrics_used
    return best_row


def best_seed_selection_to_json(selection: dict[str, Any]) -> str:
    return json.dumps(selection, indent=2, default=str)