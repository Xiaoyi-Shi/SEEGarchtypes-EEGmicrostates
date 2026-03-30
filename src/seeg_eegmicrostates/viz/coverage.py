from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_coverage_summary(coverage_df: pd.DataFrame, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8, 4))
    if coverage_df.empty:
        axis.set_title("No coverage summary available")
    else:
        summary = coverage_df.groupby("network", as_index=False)["n_bipolar_channels"].sum().sort_values("n_bipolar_channels")
        axis.barh(summary["network"], summary["n_bipolar_channels"], color="#4C78A8")
        axis.set_xlabel("Bipolar channels")
        axis.set_title("Yeo17 network coverage")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path
