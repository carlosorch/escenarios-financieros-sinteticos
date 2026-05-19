from __future__ import annotations

import pandas as pd
import pytest

from tfm_pipeline.model_selection import select_best_seed, score_validation_diagnostics


def _diagnostics_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "seed": 101,
                "variant": "timegan_raw",
                "mean_jensen_shannon": 0.30,
                "mean_wasserstein": 0.40,
                "correlation_matrix_error": 0.90,
                "autocorrelation_error": 0.30,
                "absolute_autocorrelation_error": 0.20,
                "mean_abs_kurtosis_error": 0.50,
                "sharpe_ratio": 9.0,
                "annualized_return": 4.0,
                "max_drawdown": -0.8,
                "value_at_risk": -0.4,
                "conditional_value_at_risk": -0.5,
            },
            {
                "seed": 202,
                "variant": "timegan_mean_vol_calibrated",
                "mean_jensen_shannon": 0.10,
                "mean_wasserstein": 0.20,
                "correlation_matrix_error": 0.30,
                "autocorrelation_error": 0.10,
                "absolute_autocorrelation_error": 0.10,
                "mean_abs_kurtosis_error": 0.10,
                "sharpe_ratio": -99.0,
                "annualized_return": -3.0,
                "max_drawdown": -0.99,
                "value_at_risk": -0.9,
                "conditional_value_at_risk": -1.0,
            },
        ]
    )


def test_ranking_orders_by_lower_validation_score() -> None:
    scored = score_validation_diagnostics(_diagnostics_frame())

    assert list(scored["seed"]) == [202, 101]
    assert list(scored["rank"]) == [1, 2]
    assert scored.iloc[0]["validation_score"] < scored.iloc[1]["validation_score"]


def test_financial_columns_do_not_affect_validation_score() -> None:
    base = _diagnostics_frame()
    altered = base.copy()
    altered["sharpe_ratio"] = [9999.0, -9999.0]
    altered["annualized_return"] = [123.0, -123.0]
    altered["max_drawdown"] = [0.0, -1.0]
    altered["value_at_risk"] = [50.0, -50.0]
    altered["conditional_value_at_risk"] = [75.0, -75.0]

    base_scores = score_validation_diagnostics(base)["validation_score"]
    altered_scores = score_validation_diagnostics(altered)["validation_score"]

    pd.testing.assert_series_equal(base_scores, altered_scores)


def test_missing_required_metric_raises_clear_value_error() -> None:
    diagnostics = _diagnostics_frame().drop(columns=["mean_wasserstein"])

    with pytest.raises(ValueError, match="Missing validation diagnostic columns: mean_wasserstein"):
        score_validation_diagnostics(diagnostics)


def test_constant_metric_scores_without_divide_by_zero() -> None:
    diagnostics = _diagnostics_frame()
    diagnostics["mean_wasserstein"] = 0.0

    scored = score_validation_diagnostics(diagnostics)

    assert scored["mean_wasserstein_normalized"].eq(0.0).all()
    assert scored["validation_score"].notna().all()


def test_best_seed_returns_expected_seed_and_variant() -> None:
    scored = score_validation_diagnostics(_diagnostics_frame())

    best = select_best_seed(scored)

    assert best["seed"] == 202
    assert best["variant"] == "timegan_mean_vol_calibrated"
    assert best["selection_basis"] == "validation diagnostics only; test metrics were not used for selection"
    assert best["metrics_used"] == [
        "mean_jensen_shannon",
        "mean_wasserstein",
        "correlation_matrix_error",
        "autocorrelation_error",
        "absolute_autocorrelation_error",
        "mean_abs_kurtosis_error",
    ]