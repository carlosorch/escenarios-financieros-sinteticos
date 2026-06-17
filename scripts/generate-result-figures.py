from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
MEDIA = ROOT / "media"
MEDIA.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid", context="paper", font_scale=1.0)


def savefig(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close()


def pct(series: pd.Series) -> pd.Series:
    return series * 100.0


def plot_baselines() -> None:
    df = pd.read_csv(RESULTS / "baselines" / "portfolio_metrics.csv")
    label_map = {
        "equal_weight": "Equiponderada",
        "minimum_variance": "Mín. varianza",
        "markowitz": "Markowitz",
        "ledoit_wolf_minimum_variance": "LW mín. var.",
        "ledoit_wolf_markowitz": "LW Markowitz",
    }
    df["modelo"] = df["model"].map(label_map)
    long = df.melt(
        id_vars="modelo",
        value_vars=["annualized_return", "annualized_volatility", "sharpe_ratio"],
        var_name="métrica",
        value_name="valor",
    )
    long["métrica"] = long["métrica"].map(
        {
            "annualized_return": "Rent. anual.",
            "annualized_volatility": "Vol. anual.",
            "sharpe_ratio": "Sharpe",
        }
    )
    long.loc[long["métrica"].isin(["Rent. anual.", "Vol. anual."]), "valor"] *= 100.0

    plt.figure(figsize=(9.2, 4.8))
    ax = sns.barplot(data=long, x="modelo", y="valor", hue="métrica", palette="viridis")
    ax.set_xlabel("")
    ax.set_ylabel("Valor (% para rentabilidad/volatilidad; ratio para Sharpe)")
    ax.set_title("Baselines fuera de muestra")
    ax.tick_params(axis="x", rotation=20)
    savefig(MEDIA / "result_baselines_oos.png")


def plot_ledoit_wolf_delta() -> None:
    df = pd.read_csv(RESULTS / "baselines" / "portfolio_metrics.csv").set_index("model")
    pairs = {
        "Mín. varianza": ("ledoit_wolf_minimum_variance", "minimum_variance"),
        "Markowitz": ("ledoit_wolf_markowitz", "markowitz"),
    }
    rows = []
    for label, (robust, base) in pairs.items():
        for metric, metric_label, scale in [
            ("annualized_return", "Rent. anual.", 100.0),
            ("annualized_volatility", "Vol. anual.", 100.0),
            ("sharpe_ratio", "Sharpe", 1.0),
            ("max_drawdown", "Drawdown", 100.0),
        ]:
            rows.append(
                {
                    "estrategia": label,
                    "métrica": metric_label,
                    "delta": (df.loc[robust, metric] - df.loc[base, metric]) * scale,
                }
            )
    delta = pd.DataFrame(rows)
    plt.figure(figsize=(8.6, 4.6))
    ax = sns.barplot(data=delta, x="métrica", y="delta", hue="estrategia", palette="mako")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("")
    ax.set_ylabel("Cambio Ledoit-Wolf menos baseline")
    ax.set_title("Impacto incremental de Ledoit-Wolf")
    savefig(MEDIA / "result_ledoit_wolf_comparison.png")


def plot_timegan_validation_score() -> None:
    ranking = pd.read_csv(RESULTS / "timegan_multiseed" / "seed_ranking.csv").head(10).copy()
    ranking["configuración"] = ranking["seed"].astype(str) + " · " + ranking["variant"].str.replace("timegan_", "", regex=False)
    plt.figure(figsize=(9.0, 5.2))
    ax = sns.barplot(data=ranking, y="configuración", x="validation_score", hue="configuración", palette="crest", legend=False)
    ax.set_xlabel("Validation score (menor es mejor)")
    ax.set_ylabel("")
    ax.set_title("Ranking de validación TimeGAN")
    savefig(MEDIA / "result_timegan_validation_score.png")


def plot_timegan_distances() -> None:
    ranking = pd.read_csv(RESULTS / "timegan_multiseed" / "seed_ranking.csv").head(5).copy()
    ranking["configuración"] = ranking["seed"].astype(str) + " · " + ranking["variant"].str.replace("timegan_", "", regex=False)
    long = ranking.melt(
        id_vars="configuración",
        value_vars=["mean_jensen_shannon", "mean_wasserstein", "correlation_matrix_error"],
        var_name="métrica",
        value_name="valor",
    )
    long["métrica"] = long["métrica"].map(
        {
            "mean_jensen_shannon": "Jensen-Shannon",
            "mean_wasserstein": "Wasserstein",
            "correlation_matrix_error": "Error correlación",
        }
    )
    grid = sns.catplot(
        data=long,
        kind="bar",
        x="valor",
        y="configuración",
        hue="configuración",
        col="métrica",
        sharex=False,
        height=4.2,
        aspect=0.85,
        palette="flare",
        legend=False,
    )
    grid.set_axis_labels("Valor", "")
    grid.set_titles("{col_name}")
    grid.figure.suptitle("Distancias real-sintético en validación", y=1.04)
    grid.figure.savefig(MEDIA / "result_timegan_real_synthetic_distances.png", dpi=220, bbox_inches="tight")
    plt.close(grid.figure)


def plot_timegan_metric_heatmap() -> None:
    ranking = pd.read_csv(RESULTS / "timegan_multiseed" / "seed_ranking.csv").head(5).copy()
    ranking["configuración"] = ranking["seed"].astype(str) + " · " + ranking["variant"].str.replace("timegan_", "", regex=False)
    metrics = [
        "mean_jensen_shannon",
        "mean_wasserstein",
        "correlation_matrix_error",
        "autocorrelation_error",
        "absolute_autocorrelation_error",
        "mean_abs_kurtosis_error",
    ]
    labels = ["JS", "Wass.", "Corr.", "Autocorr.", "Autocorr. abs.", "Kurtosis"]
    values = ranking.set_index("configuración")[metrics]
    normalized = values.divide(values.max(axis=0), axis=1)
    plt.figure(figsize=(9.2, 4.8))
    ax = sns.heatmap(
        normalized,
        annot=values.rename(columns=dict(zip(metrics, labels))),
        fmt=".3f",
        cmap="YlGnBu_r",
        cbar_kws={"label": "Valor normalizado por métrica"},
    )
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_title("Métricas real-sintético TimeGAN (menor es mejor)")
    savefig(MEDIA / "result_timegan_real_synthetic_metrics.png")


def plot_timegan_sharpe() -> None:
    df = pd.read_csv(RESULTS / "timegan_multiseed" / "portfolio_metrics.csv")
    keep = df[df["model"].str.contains("minimum_variance|shrunk_mean_synthetic_covariance", regex=True)].copy()
    label_map = {
        "timegan_raw_minimum_variance": "Raw mín. var.",
        "timegan_mean_vol_calibrated_minimum_variance": "Calibrada mín. var.",
        "timegan_raw_shrunk_mean_synthetic_covariance": "Raw media contraída",
        "timegan_mean_vol_calibrated_shrunk_mean_synthetic_covariance": "Calibrada media contraída",
    }
    keep["modelo"] = keep["model"].map(label_map)
    keep = keep.dropna(subset=["modelo"])
    keep = keep.sort_values("sharpe_ratio_mean", ascending=False)

    plt.figure(figsize=(8.8, 4.8))
    ax = plt.gca()
    ax.barh(keep["modelo"], keep["sharpe_ratio_mean"], xerr=keep["sharpe_ratio_std"], color=sns.color_palette("crest", len(keep)))
    baseline = pd.read_csv(RESULTS / "baselines" / "portfolio_metrics.csv")
    eq_sharpe = float(baseline.loc[baseline["model"] == "equal_weight", "sharpe_ratio"].iloc[0])
    ax.axvline(eq_sharpe, color="black", linestyle="--", linewidth=1.0, label="Equiponderada")
    ax.set_xlabel("Sharpe medio ± desviación típica")
    ax.set_ylabel("")
    ax.set_title("Sharpe multi-semilla de carteras TimeGAN")
    ax.legend(loc="lower right")
    savefig(MEDIA / "result_timegan_sharpe_multiseed.png")


if __name__ == "__main__":
    plot_baselines()
    plot_ledoit_wolf_delta()
    plot_timegan_validation_score()
    plot_timegan_distances()
    plot_timegan_metric_heatmap()
    plot_timegan_sharpe()
    print("Result figures written to media/")
