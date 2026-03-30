from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_group_effects_heatmap(group_df: pd.DataFrame, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8, 4))
    if group_df.empty:
        axis.set_title("No group effects available")
    else:
        pivot = group_df.pivot(index="microstate", columns="network", values="mean_effect").sort_index()
        image = axis.imshow(pivot.to_numpy(), aspect="auto", cmap="RdBu_r")
        axis.set_xticks(range(pivot.shape[1]))
        axis.set_xticklabels(pivot.columns, rotation=90)
        axis.set_yticks(range(pivot.shape[0]))
        axis.set_yticklabels(pivot.index)
        axis.set_title("Group HFA coupling effects")
        figure.colorbar(image, ax=axis, shrink=0.8)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_cross_modal_overlap(summary_df: pd.DataFrame, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8, 4))
    if summary_df.empty:
        axis.set_title("No cross-modal summary available")
    else:
        axis.bar(summary_df["patient_id"], summary_df["overlap"], color="#59A14F")
        axis.set_ylim(0.0, 1.0)
        axis.set_ylabel("Overlap")
        axis.set_title("Cross-modal EEG/SEEG microstate overlap")
        axis.tick_params(axis="x", rotation=90)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_connectivity_effect_matrices(group_df: pd.DataFrame, output_path: str | Path, *, title: str | None = None) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if group_df.empty:
        figure, axis = plt.subplots(figsize=(8, 4))
        axis.set_title("No band-limited connectivity effects available")
        figure.tight_layout()
        figure.savefig(path, dpi=150)
        plt.close(figure)
        return path

    microstates = sorted(group_df["microstate"].unique())
    networks = sorted(set(group_df["network_a"]).union(group_df["network_b"]))
    n_cols = min(2, len(microstates))
    n_rows = int(np.ceil(len(microstates) / n_cols))
    figure, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4.5 * n_rows), squeeze=False)
    axes_list = list(axes.flat)
    vmax = float(np.nanmax(np.abs(group_df["mean_effect"].to_numpy(dtype=float)))) if not group_df.empty else 1.0
    if vmax == 0.0:
        vmax = 1.0

    for axis, microstate in zip(axes_list, microstates):
        subset = group_df[group_df["microstate"] == microstate]
        matrix = pd.DataFrame(np.nan, index=networks, columns=networks, dtype=float)
        np.fill_diagonal(matrix.values, 0.0)
        for row in subset.itertuples(index=False):
            matrix.loc[row.network_a, row.network_b] = float(row.mean_effect)
            matrix.loc[row.network_b, row.network_a] = float(row.mean_effect)
        image = axis.imshow(matrix.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
        axis.set_xticks(range(len(networks)))
        axis.set_xticklabels(networks, rotation=90)
        axis.set_yticks(range(len(networks)))
        axis.set_yticklabels(networks)
        axis.set_title(f"State {microstate}")
    for axis in axes_list[len(microstates) :]:
        axis.axis("off")
    if title:
        figure.suptitle(title)
    figure.colorbar(image, ax=axes_list, shrink=0.8, label="Connectivity effect")
    figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.96) if title else None)
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path
