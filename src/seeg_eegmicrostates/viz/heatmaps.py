from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_group_effects_heatmap(group_df: pd.DataFrame, output_path: str | Path, *, title: str = "Group activity effects") -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8, 4))
    if group_df.empty:
        axis.set_title("No group effects available")
    else:
        pivot = group_df.pivot(index="microstate", columns="region", values="mean_effect").sort_index()
        image = axis.imshow(pivot.to_numpy(), aspect="auto", cmap="RdBu_r")
        axis.set_xticks(range(pivot.shape[1]))
        axis.set_xticklabels(pivot.columns, rotation=90)
        axis.set_yticks(range(pivot.shape[0]))
        axis.set_yticklabels(pivot.index)
        axis.set_title(title)
        figure.colorbar(image, ax=axis, shrink=0.8)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_group_metric_heatmap(
    group_df: pd.DataFrame,
    output_path: str | Path,
    *,
    title: str,
    value_column: str,
    unit_column: str = "region",
    row_column: str | None = None,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8, 4))
    if group_df.empty:
        axis.set_title(f"No {title.lower()} available")
    else:
        data = group_df.copy()
        if row_column is None:
            data = data.assign(metric="overall")
            row_key = "metric"
        elif row_column == "contrast":
            data = data.assign(contrast=data.apply(lambda row: f"{row.microstate_a}-{row.microstate_b}", axis=1))
            row_key = "contrast"
        else:
            row_key = row_column
        pivot = data.pivot(index=row_key, columns=unit_column, values=value_column).sort_index()
        image = axis.imshow(pivot.to_numpy(), aspect="auto", cmap="RdBu_r")
        axis.set_xticks(range(pivot.shape[1]))
        axis.set_xticklabels(pivot.columns, rotation=90)
        axis.set_yticks(range(pivot.shape[0]))
        axis.set_yticklabels(pivot.index)
        axis.set_title(title)
        figure.colorbar(image, ax=axis, shrink=0.8)
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
    pair_a_key = "region_a"
    pair_b_key = "region_b"
    regions = sorted(set(group_df[pair_a_key]).union(group_df[pair_b_key]))
    n_cols = min(2, len(microstates))
    n_rows = int(np.ceil(len(microstates) / n_cols))
    figure, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4.5 * n_rows), squeeze=False)
    axes_list = list(axes.flat)
    vmax = float(np.nanmax(np.abs(group_df["mean_effect"].to_numpy(dtype=float)))) if not group_df.empty else 1.0
    if vmax == 0.0:
        vmax = 1.0

    for axis, microstate in zip(axes_list, microstates):
        subset = group_df[group_df["microstate"] == microstate]
        matrix = pd.DataFrame(np.nan, index=regions, columns=regions, dtype=float)
        for index in range(len(regions)):
            matrix.iat[index, index] = 0.0
        for row in subset.itertuples(index=False):
            left = getattr(row, pair_a_key)
            right = getattr(row, pair_b_key)
            matrix.loc[left, right] = float(row.mean_effect)
            matrix.loc[right, left] = float(row.mean_effect)
        image = axis.imshow(matrix.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
        axis.set_xticks(range(len(regions)))
        axis.set_xticklabels(regions, rotation=90)
        axis.set_yticks(range(len(regions)))
        axis.set_yticklabels(regions)
        axis.set_title(f"State {microstate}")
    for axis in axes_list[len(microstates) :]:
        axis.axis("off")
    if title:
        figure.suptitle(title)
    figure.colorbar(image, ax=axes_list, shrink=0.8, label="Connectivity effect")
    figure.subplots_adjust(left=0.12, right=0.88, bottom=0.18, top=0.88 if title else 0.94, wspace=0.35, hspace=0.35)
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_connectivity_omnibus_matrix(
    group_df: pd.DataFrame,
    output_path: str | Path,
    *,
    value_column: str = "statistic",
    title: str | None = None,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8, 6))
    if group_df.empty:
        axis.set_title("No connectivity omnibus results available")
        figure.tight_layout()
        figure.savefig(path, dpi=150)
        plt.close(figure)
        return path
    pair_a_key = "region_a"
    pair_b_key = "region_b"
    regions = sorted(set(group_df[pair_a_key]).union(group_df[pair_b_key]))
    matrix = pd.DataFrame(np.nan, index=regions, columns=regions, dtype=float)
    for index in range(len(regions)):
        matrix.iat[index, index] = 0.0
    for row in group_df.itertuples(index=False):
        left = getattr(row, pair_a_key)
        right = getattr(row, pair_b_key)
        value = float(getattr(row, value_column))
        matrix.loc[left, right] = value
        matrix.loc[right, left] = value
    image = axis.imshow(matrix.to_numpy(), aspect="auto", cmap="viridis")
    axis.set_xticks(range(len(regions)))
    axis.set_xticklabels(regions, rotation=90)
    axis.set_yticks(range(len(regions)))
    axis.set_yticklabels(regions)
    axis.set_title(title or "Connectivity omnibus results")
    figure.colorbar(image, ax=axis, shrink=0.8, label=value_column)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_connectivity_posthoc_matrices(
    group_df: pd.DataFrame,
    output_path: str | Path,
    *,
    value_column: str = "mean_effect",
    title: str | None = None,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if group_df.empty:
        figure, axis = plt.subplots(figsize=(8, 4))
        axis.set_title("No connectivity post-hoc results available")
        figure.tight_layout()
        figure.savefig(path, dpi=150)
        plt.close(figure)
        return path
    pair_a_key = "region_a"
    pair_b_key = "region_b"
    regions = sorted(set(group_df[pair_a_key]).union(group_df[pair_b_key]))
    contrasts = sorted(group_df[["microstate_a", "microstate_b"]].drop_duplicates().itertuples(index=False, name=None))
    n_cols = min(2, len(contrasts))
    n_rows = int(np.ceil(len(contrasts) / n_cols))
    figure, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4.5 * n_rows), squeeze=False)
    axes_list = list(axes.flat)
    vmax = float(np.nanmax(np.abs(group_df[value_column].to_numpy(dtype=float)))) if not group_df.empty else 1.0
    if vmax == 0.0:
        vmax = 1.0
    for axis, (state_a, state_b) in zip(axes_list, contrasts):
        subset = group_df[(group_df["microstate_a"] == state_a) & (group_df["microstate_b"] == state_b)]
        matrix = pd.DataFrame(np.nan, index=regions, columns=regions, dtype=float)
        for index in range(len(regions)):
            matrix.iat[index, index] = 0.0
        for row in subset.itertuples(index=False):
            left = getattr(row, pair_a_key)
            right = getattr(row, pair_b_key)
            value = float(getattr(row, value_column))
            matrix.loc[left, right] = value
            matrix.loc[right, left] = value
        image = axis.imshow(matrix.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
        axis.set_xticks(range(len(regions)))
        axis.set_xticklabels(regions, rotation=90)
        axis.set_yticks(range(len(regions)))
        axis.set_yticklabels(regions)
        axis.set_title(f"State {state_a} vs {state_b}")
    for axis in axes_list[len(contrasts) :]:
        axis.axis("off")
    if title:
        figure.suptitle(title)
    figure.colorbar(image, ax=axes_list, shrink=0.8, label=value_column)
    figure.subplots_adjust(left=0.12, right=0.88, bottom=0.18, top=0.88 if title else 0.94, wspace=0.35, hspace=0.35)
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_transition_effect_heatmap(
    group_df: pd.DataFrame,
    output_path: str | Path,
    *,
    title: str = "Transition coupling effects",
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(10, 5))
    if group_df.empty:
        axis.set_title("No transition coupling effects available")
    else:
        transition_labels = group_df.apply(lambda row: f"{row.from_state}->{row.to_state}", axis=1)
        pivot = (
            group_df.assign(transition=transition_labels)
            .pivot(index="transition", columns="region", values="mean_effect")
            .sort_index()
        )
        image = axis.imshow(pivot.to_numpy(), aspect="auto", cmap="RdBu_r")
        axis.set_xticks(range(pivot.shape[1]))
        axis.set_xticklabels(pivot.columns, rotation=90)
        axis.set_yticks(range(pivot.shape[0]))
        axis.set_yticklabels(pivot.index)
        axis.set_title(title)
        figure.colorbar(image, ax=axis, shrink=0.8)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_direct_coupling_lag_curve(
    group_df: pd.DataFrame,
    output_path: str | Path,
    *,
    title: str = "Direct EEG-SEEG state coupling",
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8, 4))
    if group_df.empty:
        axis.set_title("No direct state-coupling effects available")
    else:
        data = group_df.sort_values(["backend", "lag_ms"] if "backend" in group_df.columns else ["lag_ms"])
        if "backend" in data.columns:
            iterator = data.groupby("backend")
        else:
            iterator = [("direct", data)]
        for backend, group in iterator:
            axis.plot(group["lag_ms"], group["mean_effect"], marker="o", label=str(backend))
        axis.axhline(0.0, color="black", linewidth=0.8, linestyle="--")
        axis.set_xlabel("Lag (ms)")
        axis.set_ylabel("Mean effect")
        axis.set_title(title)
        if "backend" in data.columns and data["backend"].nunique() > 1:
            axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_state_transition_matrix(
    group_df: pd.DataFrame,
    output_path: str | Path,
    *,
    title: str = "Transition state coupling",
    value_column: str = "mean_effect",
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(6, 5))
    if group_df.empty:
        axis.set_title("No transition state-coupling effects available")
    else:
        pivot = group_df.pivot(index="from_state", columns="to_state", values=value_column).sort_index().sort_index(axis=1)
        image = axis.imshow(pivot.to_numpy(), aspect="auto", cmap="RdBu_r")
        axis.set_xticks(range(pivot.shape[1]))
        axis.set_xticklabels(pivot.columns)
        axis.set_yticks(range(pivot.shape[0]))
        axis.set_yticklabels(pivot.index)
        axis.set_xlabel("EEG to_state")
        axis.set_ylabel("EEG from_state")
        axis.set_title(title)
        figure.colorbar(image, ax=axis, shrink=0.8)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path
