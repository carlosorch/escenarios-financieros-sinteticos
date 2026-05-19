from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .model_selection import DEFAULT_VALIDATION_WEIGHTS, score_validation_diagnostics, select_best_seed


RESULT_FILES: tuple[tuple[str, str], ...] = (
    ("metadata.json", "Configuracion real de la corrida, versiones y metadatos del experimento."),
    ("seed_ranking.csv", "Ranking de semillas y variantes usando solo diagnosticos de validacion."),
    ("best_seed.json", "Semilla y variante elegidas con la justificacion de seleccion."),
    ("best_seed_portfolio_metrics.csv", "Metricas financieras del seed ganador; se usan solo para reportar, no para seleccionar."),
    ("diagnostic_summary_by_seed.csv", "Diagnosticos distribucionales y temporales por semilla y variante en train."),
    ("validation_diagnostic_summary_by_seed.csv", "Diagnosticos equivalentes pero medidos sobre validacion; alimentan el ranking."),
    ("portfolio_metrics_by_seed.csv", "Metricas de cartera por semilla, variante y modelo en test."),
    ("diagnostic_summary.csv", "Resumen agregado de diagnosticos por variante."),
    ("validation_diagnostic_summary.csv", "Resumen agregado de diagnosticos de validacion por variante."),
    ("portfolio_metrics.csv", "Resumen agregado de metricas de cartera por modelo."),
    ("training_history_by_seed.csv", "Historico de perdida durante el entrenamiento de TimeGAN por semilla."),
)

RANKING_COLUMNS: tuple[str, ...] = (
    "rank",
    "seed",
    "variant",
    "validation_score",
    "mean_jensen_shannon",
    "mean_wasserstein",
    "correlation_matrix_error",
    "autocorrelation_error",
    "absolute_autocorrelation_error",
    "mean_abs_kurtosis_error",
)

PORTFOLIO_COLUMNS: tuple[str, ...] = (
    "seed",
    "variant",
    "model",
    "cumulative_return",
    "annualized_return",
    "annualized_volatility",
    "sharpe_ratio",
    "max_drawdown",
    "value_at_risk",
    "conditional_value_at_risk",
    "weight_entropy",
    "weight_concentration",
)

CORRELATION_WEIGHT_GRID: tuple[float, ...] = (0.5, 1.0, 1.5, 2.0, 3.0)


def _format_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    view = frame.head(max_rows) if max_rows is not None else frame
    if view.empty:
        return "(sin filas)"
    try:
        return view.to_markdown(index=False)
    except Exception:
        return view.to_string(index=False)


def _format_kv_rows(items: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for key, value in items.items():
        if isinstance(value, (dict, list, tuple)):
            rendered = json.dumps(value, ensure_ascii=False)
        else:
            rendered = value
        rows.append({"campo": key, "valor": rendered})
    return pd.DataFrame(rows)


def _load_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path)


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _summarize_training_history(history: pd.DataFrame) -> pd.DataFrame:
    summary = (
        history.sort_values(["seed", "epoch"]).groupby("seed", as_index=False).agg(
            epochs=("epoch", "max"),
            autoencoder_loss_start=("autoencoder_loss", "first"),
            autoencoder_loss_end=("autoencoder_loss", "last"),
            supervisor_loss_end=("supervisor_loss", "last"),
            generator_loss_end=("generator_loss", "last"),
            discriminator_loss_end=("discriminator_loss", "last"),
        )
    )
    summary["autoencoder_loss_delta"] = summary["autoencoder_loss_end"] - summary["autoencoder_loss_start"]
    return summary


def _build_weight_sensitivity(validation_by_seed: pd.DataFrame) -> pd.DataFrame | None:
    if validation_by_seed is None or validation_by_seed.empty:
        return None

    rows = []
    for correlation_weight in CORRELATION_WEIGHT_GRID:
        weights = dict(DEFAULT_VALIDATION_WEIGHTS)
        weights["correlation_matrix_error"] = correlation_weight
        scored = score_validation_diagnostics(validation_by_seed, weights=weights)
        best = select_best_seed(scored)
        rows.append(
            {
                "correlation_matrix_error_weight": correlation_weight,
                "best_rank": best["rank"],
                "seed": best["seed"],
                "variant": best["variant"],
                "validation_score": best["validation_score"],
                "mean_jensen_shannon": best["mean_jensen_shannon"],
                "mean_wasserstein": best["mean_wasserstein"],
                "correlation_matrix_error": best["correlation_matrix_error"],
                "autocorrelation_error": best["autocorrelation_error"],
                "absolute_autocorrelation_error": best["absolute_autocorrelation_error"],
                "mean_abs_kurtosis_error": best["mean_abs_kurtosis_error"],
            }
        )
    return pd.DataFrame(rows)


def build_report(results_dir: Path = Path("results/timegan_multiseed"), top_n: int = 10) -> str:
    metadata = _load_json(results_dir / "metadata.json")
    seed_ranking = _load_csv(results_dir / "seed_ranking.csv")
    best_seed = _load_json(results_dir / "best_seed.json")
    best_seed_portfolio = _load_csv(results_dir / "best_seed_portfolio_metrics.csv")
    validation_by_seed = _load_csv(results_dir / "validation_diagnostic_summary_by_seed.csv")
    validation_aggregate = _load_csv(results_dir / "validation_diagnostic_summary.csv")
    portfolio_aggregate = _load_csv(results_dir / "portfolio_metrics.csv")
    diagnostics_by_seed = _load_csv(results_dir / "diagnostic_summary_by_seed.csv")
    diagnostics_aggregate = _load_csv(results_dir / "diagnostic_summary.csv")
    training_history = _load_csv(results_dir / "training_history_by_seed.csv")

    lines: list[str] = []
    lines.append("# Resumen de resultados - TimeGAN multiseed")
    lines.append("")
    lines.append("Este reporte sintetiza los artefactos de `results/timegan_multiseed`.")
    lines.append("")

    lines.append("## Que hace cada fichero")
    file_rows = []
    for filename, purpose in RESULT_FILES:
        file_rows.append(
            {
                "fichero": filename,
                "estado": "ok" if (results_dir / filename).exists() else "falta",
                "uso": purpose,
            }
        )
    lines.append(_format_table(pd.DataFrame(file_rows)))
    lines.append("")

    if metadata:
        lines.append("## Configuracion real de la corrida")
        config = metadata.get("config", {})
        key_config = {
            "assets": ", ".join(config.get("assets", [])),
            "start_date": config.get("start_date"),
            "train_end": config.get("train_end"),
            "validation_end": config.get("validation_end"),
            "end_date": config.get("end_date"),
            "window_size": config.get("window_size"),
            "random_seed": config.get("random_seed"),
            "timegan_hidden_dim": config.get("timegan_hidden_dim"),
            "timegan_noise_dim": config.get("timegan_noise_dim"),
            "timegan_epochs": config.get("timegan_epochs"),
            "timegan_batch_size": config.get("timegan_batch_size"),
            "timegan_learning_rate": config.get("timegan_learning_rate"),
            "timegan_gamma": config.get("timegan_gamma"),
            "timegan_supervised_weight": config.get("timegan_supervised_weight"),
            "timegan_reconstruction_weight": config.get("timegan_reconstruction_weight"),
            "timegan_seeds": ", ".join(str(seed) for seed in config.get("timegan_seeds", [])),
            "synthetic_scenarios": config.get("synthetic_scenarios"),
            "mean_shrinkage_alpha": config.get("mean_shrinkage_alpha"),
        }
        lines.append(_format_table(_format_kv_rows(key_config)))
        lines.append("")

        libraries = metadata.get("libraries", {})
        if libraries:
            lines.append("### Librerias detectadas")
            library_rows = []
            for name, values in libraries.items():
                row = {"libreria": name}
                row.update(values)
                library_rows.append(row)
            lines.append(_format_table(pd.DataFrame(library_rows)))
            lines.append("")

    if best_seed:
        lines.append("## Seleccion final")
        selection_rows = _format_kv_rows(best_seed)
        lines.append(_format_table(selection_rows))
        lines.append("")

    if seed_ranking is not None and not seed_ranking.empty:
        lines.append("## Ranking de semillas")
        ranking_cols = [column for column in RANKING_COLUMNS if column in seed_ranking.columns]
        lines.append(_format_table(seed_ranking[ranking_cols], max_rows=top_n))
        lines.append("")

    if best_seed_portfolio is not None and not best_seed_portfolio.empty:
        lines.append("## Cartera del seed ganador")
        portfolio_cols = [column for column in PORTFOLIO_COLUMNS if column in best_seed_portfolio.columns]
        lines.append(_format_table(best_seed_portfolio[portfolio_cols]))
        lines.append("")

    if validation_by_seed is not None and not validation_by_seed.empty:
        lines.append("## Diagnosticos de validacion por seed")
        lines.append(_format_table(validation_by_seed, max_rows=top_n))
        lines.append("")

    if validation_aggregate is not None and not validation_aggregate.empty:
        lines.append("## Diagnostico agregado de validacion")
        lines.append(_format_table(validation_aggregate))
        lines.append("")

    sensitivity = _build_weight_sensitivity(validation_by_seed)
    if sensitivity is not None and not sensitivity.empty:
        lines.append("## Sensibilidad del ranking al peso de correlation_matrix_error")
        lines.append(
            "Se mantiene el resto de pesos fijo y solo cambia el peso de correlation_matrix_error para ver si el ranking es estable."
        )
        lines.append(_format_table(sensitivity))
        lines.append("")

    if portfolio_aggregate is not None and not portfolio_aggregate.empty:
        lines.append("## Metricas agregadas de cartera")
        lines.append(_format_table(portfolio_aggregate.sort_values("sharpe_ratio_mean", ascending=False)))
        lines.append("")

    if diagnostics_by_seed is not None and not diagnostics_by_seed.empty:
        lines.append("## Diagnosticos en train por seed")
        lines.append(_format_table(diagnostics_by_seed, max_rows=top_n))
        lines.append("")

    if diagnostics_aggregate is not None and not diagnostics_aggregate.empty:
        lines.append("## Diagnostico agregado en train")
        lines.append(_format_table(diagnostics_aggregate))
        lines.append("")

    if training_history is not None and not training_history.empty:
        lines.append("## Resumen del entrenamiento")
        lines.append(_format_table(_summarize_training_history(training_history)))
        lines.append("")

    lines.append("## Lectura rapida del proyecto")
    lines.append(
        "- Se entrena TimeGAN con varias semillas y dos variantes: `timegan_raw` y `timegan_mean_vol_calibrated`."
    )
    lines.append(
        "- La seleccion usa solo diagnosticos de validacion: Jensen-Shannon, Wasserstein, error de correlacion, autocorrelacion, autocorrelacion absoluta y kurtosis."
    )
    lines.append(
        "- Las metricas financieras de test (`sharpe_ratio`, `annualized_return`, `max_drawdown`, `value_at_risk`, `conditional_value_at_risk`) se usan solo para reportar el seed elegido."
    )
    lines.append("")

    return "\n".join(lines)


def run(results_dir: Path = Path("results/timegan_multiseed"), output_path: Path | None = None, top_n: int = 10) -> Path:
    report = build_report(results_dir=results_dir, top_n=top_n)
    output_path = output_path or (results_dir / "report.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(report)
    return output_path


if __name__ == "__main__":
    path = run()
    print(f"\nReport written to {path}")