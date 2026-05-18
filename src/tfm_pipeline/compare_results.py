from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_portfolio_reports(results_dir: Path = Path("results")) -> pd.DataFrame:
    reports = []
    for path in sorted(results_dir.glob("*/portfolio_metrics.csv")):
        if path.parent.name.endswith("multiseed"):
            continue
        report = pd.read_csv(path)
        report.insert(0, "experiment", path.parent.name)
        reports.append(report)
    if not reports:
        raise FileNotFoundError("No portfolio_metrics.csv files found under results/")
    return pd.concat(reports, ignore_index=True)


def load_multiseed_portfolio_reports(results_dir: Path = Path("results")) -> pd.DataFrame:
    reports = []
    for path in sorted(results_dir.glob("*multiseed/portfolio_metrics.csv")):
        report = pd.read_csv(path)
        report.insert(0, "experiment", path.parent.name)
        reports.append(report)
    if not reports:
        return pd.DataFrame()
    return pd.concat(reports, ignore_index=True)


def run(output_path: Path = Path("results/combined_portfolio_metrics.csv")) -> pd.DataFrame:
    report = load_portfolio_reports(output_path.parent)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(output_path, index=False)
    multiseed_report = load_multiseed_portfolio_reports(output_path.parent)
    if not multiseed_report.empty:
        multiseed_report.to_csv(output_path.parent / "combined_multiseed_portfolio_metrics.csv", index=False)
    return report


if __name__ == "__main__":
    run()
    print("Combined portfolio metrics written to results/")
