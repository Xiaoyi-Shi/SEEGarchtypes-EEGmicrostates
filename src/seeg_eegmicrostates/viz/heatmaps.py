from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd

_PAPER_FACE = "#f7f8fb"
_GRID_COLOR = "#d7deea"
_TEXT_COLOR = "#1f2933"
_DIVERGING_CMAP = "RdBu_r"
_SEQUENTIAL_CMAP = "viridis"


def _paper_figure(
    output_path: str | Path,
    *,
    figsize: tuple[float, float],
) -> tuple[Path, plt.Figure, plt.Axes | np.ndarray]:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(figsize=figsize)
    figure.patch.set_facecolor("white")
    return path, figure, axes


def _style_axis(axis: plt.Axes, *, title: str | None = None, xlabel: str | None = None, ylabel: str | None = None) -> None:
    axis.set_facecolor(_PAPER_FACE)
    axis.tick_params(colors=_TEXT_COLOR, labelcolor=_TEXT_COLOR)
    for spine in axis.spines.values():
        spine.set_color(_GRID_COLOR)
    if title:
        axis.set_title(title, color=_TEXT_COLOR, fontsize=11, fontweight="semibold")
    if xlabel:
        axis.set_xlabel(xlabel, color=_TEXT_COLOR)
    if ylabel:
        axis.set_ylabel(ylabel, color=_TEXT_COLOR)


def _figure_colorbar(figure: plt.Figure, image, *, axis, label: str | None = None) -> None:
    colorbar = figure.colorbar(image, ax=axis, shrink=0.82, pad=0.02)
    if label:
        colorbar.set_label(label, color=_TEXT_COLOR)
    colorbar.outline.set_edgecolor(_GRID_COLOR)
    colorbar.ax.tick_params(colors=_TEXT_COLOR)


def _ordered_pivot(data: pd.DataFrame, *, index: str, columns: str, values: str) -> pd.DataFrame:
    return data.pivot(index=index, columns=columns, values=values).sort_index().sort_index(axis=1)


def plot_group_effects_heatmap(group_df: pd.DataFrame, output_path: str | Path, *, title: str = "Group activity effects") -> Path:
    path, figure, axis = _paper_figure(output_path, figsize=(8.6, 4.4))
    if group_df.empty:
        _style_axis(axis, title="No group effects available")
    else:
        pivot = _ordered_pivot(group_df, index="microstate", columns="region", values="mean_effect")
        vmax = float(np.nanmax(np.abs(pivot.to_numpy(dtype=float))))
        if not np.isfinite(vmax) or vmax == 0.0:
            vmax = 1.0
        image = axis.imshow(pivot.to_numpy(dtype=float), aspect="auto", cmap=_DIVERGING_CMAP, vmin=-vmax, vmax=vmax)
        axis.set_xticks(range(pivot.shape[1]))
        axis.set_xticklabels(pivot.columns, rotation=90)
        axis.set_yticks(range(pivot.shape[0]))
        axis.set_yticklabels(pivot.index)
        _style_axis(axis, title=title, xlabel="Region", ylabel="Microstate")
        _figure_colorbar(figure, image, axis=axis, label="Mean effect")
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
    path, figure, axis = _paper_figure(output_path, figsize=(8.6, 4.4))
    if group_df.empty:
        _style_axis(axis, title=f"No {title.lower()} available")
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
        pivot = _ordered_pivot(data, index=row_key, columns=unit_column, values=value_column)
        values = pivot.to_numpy(dtype=float)
        finite = values[np.isfinite(values)]
        use_diverging = finite.size > 0 and np.nanmin(finite) < 0.0
        cmap = _DIVERGING_CMAP if use_diverging else _SEQUENTIAL_CMAP
        image_kwargs: dict[str, float] = {}
        if use_diverging:
            vmax = float(np.nanmax(np.abs(finite)))
            if not np.isfinite(vmax) or vmax == 0.0:
                vmax = 1.0
            image_kwargs = {"vmin": -vmax, "vmax": vmax}
        image = axis.imshow(values, aspect="auto", cmap=cmap, **image_kwargs)
        axis.set_xticks(range(pivot.shape[1]))
        axis.set_xticklabels(pivot.columns, rotation=90)
        axis.set_yticks(range(pivot.shape[0]))
        axis.set_yticklabels(pivot.index)
        _style_axis(axis, title=title, xlabel=unit_column.replace("_", " "), ylabel=row_key.replace("_", " "))
        _figure_colorbar(figure, image, axis=axis, label=value_column.replace("_", " "))
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


def plot_effect_curve(
    group_df: pd.DataFrame,
    output_path: str | Path,
    *,
    title: str,
    x_column: str,
    x_label: str,
    y_column: str = "mean_effect",
    hue_column: str | None = None,
    y_label: str = "Mean effect",
    empty_title: str = "No effects available",
    subject_df: pd.DataFrame | None = None,
    subject_x_column: str | None = None,
    subject_y_column: str | None = None,
) -> Path:
    path, figure, axis = _paper_figure(output_path, figsize=(8.6, 4.4))
    if group_df.empty or x_column not in group_df.columns or y_column not in group_df.columns:
        _style_axis(axis, title=empty_title)
    else:
        sort_columns = [column for column in [hue_column, x_column] if column is not None and column in group_df.columns]
        data = group_df.sort_values(sort_columns if sort_columns else [x_column])
        if hue_column and hue_column in data.columns:
            iterator = data.groupby(hue_column)
        else:
            iterator = [("effect", data)]
        for label, subset in iterator:
            axis.plot(subset[x_column], subset[y_column], marker="o", linewidth=2.0, markersize=4.0, label=str(label))
        if (
            subject_df is not None
            and subject_x_column is not None
            and subject_y_column is not None
            and subject_x_column in subject_df.columns
            and subject_y_column in subject_df.columns
            and not subject_df.empty
        ):
            ribbon = (
                subject_df.groupby(subject_x_column)[subject_y_column]
                .quantile([0.25, 0.75])
                .unstack(fill_value=np.nan)
                .rename(columns={0.25: "q25", 0.75: "q75"})
                .sort_index()
            )
            if not ribbon.empty:
                axis.fill_between(
                    ribbon.index.to_numpy(dtype=float),
                    ribbon["q25"].to_numpy(dtype=float),
                    ribbon["q75"].to_numpy(dtype=float),
                    color="#bfd0ef",
                    alpha=0.35,
                    linewidth=0.0,
                    label="Patient IQR" if hue_column is None else None,
                )
        axis.axhline(0.0, color="#475569", linewidth=1.0, linestyle="--")
        axis.grid(True, color=_GRID_COLOR, linewidth=0.8, alpha=0.9)
        _style_axis(axis, title=title, xlabel=x_label, ylabel=y_label)
        if hue_column and hue_column in data.columns and data[hue_column].nunique() > 1:
            axis.legend(frameon=False)
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
    return plot_effect_curve(
        group_df,
        output_path,
        title=title,
        x_column="lag_ms",
        x_label="Lag (ms)",
        hue_column="backend" if "backend" in group_df.columns else None,
        empty_title="No direct state-coupling effects available",
    )


def plot_state_transition_matrix(
    group_df: pd.DataFrame,
    output_path: str | Path,
    *,
    title: str = "Transition state coupling",
    value_column: str = "mean_effect",
    x_label: str = "EEG to_state",
    y_label: str = "EEG from_state",
) -> Path:
    path, figure, axis = _paper_figure(output_path, figsize=(6.8, 5.4))
    if group_df.empty:
        _style_axis(axis, title="No transition state-coupling effects available")
    else:
        pivot = _ordered_pivot(group_df, index="from_state", columns="to_state", values=value_column)
        values = pivot.to_numpy(dtype=float)
        finite = values[np.isfinite(values)]
        vmax = float(np.nanmax(np.abs(finite))) if finite.size else 1.0
        if not np.isfinite(vmax) or vmax == 0.0:
            vmax = 1.0
        image = axis.imshow(values, aspect="auto", cmap=_DIVERGING_CMAP, vmin=-vmax, vmax=vmax)
        axis.set_xticks(range(pivot.shape[1]))
        axis.set_xticklabels(pivot.columns)
        axis.set_yticks(range(pivot.shape[0]))
        axis.set_yticklabels(pivot.index)
        _style_axis(axis, title=title, xlabel=x_label, ylabel=y_label)
        _figure_colorbar(figure, image, axis=axis, label=value_column.replace("_", " "))
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_subject_state_profile_heatmap(
    profile_df: pd.DataFrame,
    output_path: str | Path,
    *,
    title: str,
    state_column: str,
    value_column: str,
    subject_column: str = "patient_id",
    empty_title: str = "No profiles available",
) -> Path:
    path, figure, axis = _paper_figure(output_path, figsize=(8.6, 4.4))
    if profile_df.empty or state_column not in profile_df.columns or value_column not in profile_df.columns:
        _style_axis(axis, title=empty_title)
    else:
        pivot = _ordered_pivot(profile_df, index=subject_column, columns=state_column, values=value_column)
        values = pivot.to_numpy(dtype=float)
        finite = values[np.isfinite(values)]
        use_diverging = finite.size > 0 and np.nanmin(finite) < 0.0
        cmap = _DIVERGING_CMAP if use_diverging else _SEQUENTIAL_CMAP
        image_kwargs: dict[str, float] = {}
        if use_diverging:
            vmax = float(np.nanmax(np.abs(finite)))
            if not np.isfinite(vmax) or vmax == 0.0:
                vmax = 1.0
            image_kwargs = {"vmin": -vmax, "vmax": vmax}
        image = axis.imshow(values, aspect="auto", cmap=cmap, **image_kwargs)
        axis.set_xticks(range(pivot.shape[1]))
        axis.set_xticklabels(pivot.columns)
        axis.set_yticks(range(pivot.shape[0]))
        axis.set_yticklabels(pivot.index)
        _style_axis(
            axis,
            title=title,
            xlabel=state_column.replace("_", " "),
            ylabel=subject_column.replace("_", " "),
        )
        _figure_colorbar(figure, image, axis=axis, label=value_column.replace("_", " "))
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_subject_template_panels(
    template_df: pd.DataFrame,
    output_path: str | Path,
    *,
    title: str,
    state_column: str = "field_state",
    subject_column: str = "patient_id",
    x_label: str = "Bipolar channel",
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata_columns = {
        subject_column,
        state_column,
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "n_channels",
        "n_peak_maps",
        "comparison_space",
        "orientation_sign",
        "n_mapped_channels",
        "n_common_units",
        "assigned_archetype",
        "assignment_similarity",
        "n_subjects",
        "n_state_assignments",
        "mean_similarity",
        "median_similarity",
        "min_similarity",
    }
    if template_df.empty:
        path, figure, axis = _paper_figure(output_path, figsize=(8.6, 4.4))
        _style_axis(axis, title="No subject-level templates available")
        figure.tight_layout()
        figure.savefig(path, dpi=150)
        plt.close(figure)
        return path
    channel_columns = [column for column in template_df.columns if column not in metadata_columns]
    if not channel_columns:
        path, figure, axis = _paper_figure(output_path, figsize=(8.6, 4.4))
        _style_axis(axis, title="No template channels available")
        figure.tight_layout()
        figure.savefig(path, dpi=150)
        plt.close(figure)
        return path
    patients = sorted(template_df[subject_column].astype(str).unique().tolist())
    n_cols = min(3, max(1, len(patients)))
    n_rows = int(np.ceil(len(patients) / n_cols))
    figure, axes = plt.subplots(n_rows, n_cols, figsize=(5.0 * n_cols, 3.7 * n_rows), squeeze=False)
    figure.patch.set_facecolor("white")
    axes_list = list(axes.flat)
    vmax = float(np.nanmax(np.abs(template_df[channel_columns].to_numpy(dtype=float)))) if channel_columns else 1.0
    if not np.isfinite(vmax) or vmax == 0.0:
        vmax = 1.0
    image = None
    for axis, patient_id in zip(axes_list, patients):
        subset = template_df[template_df[subject_column].astype(str) == patient_id].sort_values(state_column)
        matrix = subset[channel_columns].to_numpy(dtype=float)
        image = axis.imshow(matrix, aspect="auto", cmap=_DIVERGING_CMAP, vmin=-vmax, vmax=vmax)
        axis.set_xticks(range(len(channel_columns)))
        axis.set_xticklabels(channel_columns, rotation=90, fontsize=7)
        axis.set_yticks(range(subset.shape[0]))
        axis.set_yticklabels(subset[state_column].astype(int).tolist())
        _style_axis(axis, title=str(patient_id), xlabel=x_label, ylabel="Field state")
    for axis in axes_list[len(patients) :]:
        axis.axis("off")
    if title:
        figure.suptitle(title, color=_TEXT_COLOR, fontsize=12, fontweight="semibold")
    if image is not None:
        _figure_colorbar(figure, image, axis=axes_list, label="Template loading")
    figure.subplots_adjust(left=0.08, right=0.92, bottom=0.22, top=0.9 if title else 0.96, wspace=0.35, hspace=0.45)
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_eeg_topography_panels(
    topography_df: pd.DataFrame,
    output_path: str | Path,
    *,
    title: str,
    state_column: str = "assigned_archetype",
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata_columns = {
        "patient_id",
        "comparison_space",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "assigned_archetype",
        "field_state",
        "microstate",
        "n_samples",
        "n_unique_eeg_states",
        "n_subjects",
        "total_samples",
        "mean_similarity",
        "median_similarity",
        "min_similarity",
        "joint_samples",
        "conditional_probability",
        "baseline_probability",
        "effect_mean_diff",
        "lag_samples",
        "lag_ms",
        "peak_lag_samples",
        "peak_lag_ms",
        "peak_effect_mean_diff",
        "peak_observed_coupling",
        "peak_null_mean_coupling",
        "peak_p_perm",
        "peak_width_ms",
        "n_lags",
        "response_kind",
        "response_state",
        "n_events",
        "observed_coupling",
        "null_mean_coupling",
        "p_perm",
        "q_fdr",
        "mean_effect",
        "median_effect",
    }
    if topography_df.empty:
        path, figure, axis = _paper_figure(output_path, figsize=(8.6, 4.4))
        _style_axis(axis, title="No EEG topographies available")
        figure.tight_layout()
        figure.savefig(path, dpi=150)
        plt.close(figure)
        return path
    channel_columns = [column for column in topography_df.columns if column not in metadata_columns]
    if not channel_columns:
        path, figure, axis = _paper_figure(output_path, figsize=(8.6, 4.4))
        _style_axis(axis, title="No EEG channels available")
        figure.tight_layout()
        figure.savefig(path, dpi=150)
        plt.close(figure)
        return path
    info = mne.create_info(channel_columns, sfreq=250.0, ch_types="eeg")
    info.set_montage("standard_1020", verbose="ERROR")
    rows = topography_df.sort_values(state_column).reset_index(drop=True)
    n_panels = max(1, rows.shape[0])
    n_cols = min(2, n_panels)
    n_rows = int(np.ceil(n_panels / n_cols))
    figure, axes = plt.subplots(n_rows, n_cols, figsize=(4.6 * n_cols, 4.1 * n_rows), squeeze=False)
    figure.patch.set_facecolor("white")
    axes_list = list(axes.flat)
    vmax = float(np.nanmax(np.abs(rows[channel_columns].to_numpy(dtype=float))))
    if not np.isfinite(vmax) or vmax == 0.0:
        vmax = 1.0
    image = None
    for axis, (_, row) in zip(axes_list, rows.iterrows()):
        values = row[channel_columns].to_numpy(dtype=float)
        image, _ = mne.viz.plot_topomap(
            values,
            info,
            axes=axis,
            show=False,
            vlim=(-vmax, vmax),
            cmap="RdBu_r",
            contours=0,
        )
        state_label = row.get(state_column, "state")
        support_label = ""
        if "n_subjects" in row.index and pd.notna(row["n_subjects"]):
            support_label = f"\nsubjects={int(row['n_subjects'])}"
        elif "n_samples" in row.index and pd.notna(row["n_samples"]):
            support_label = f"\nsamples={int(row['n_samples'])}"
        axis.set_title(f"{state_column} {state_label}{support_label}", color=_TEXT_COLOR, fontsize=10, fontweight="semibold")
    for axis in axes_list[n_panels:]:
        axis.axis("off")
    if title:
        figure.suptitle(title, color=_TEXT_COLOR, fontsize=12, fontweight="semibold")
    if image is not None:
        _figure_colorbar(figure, image, axis=axes_list, label="Sensor loading")
    figure.subplots_adjust(left=0.06, right=0.92, bottom=0.08, top=0.88 if title else 0.94, wspace=0.25, hspace=0.35)
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path
