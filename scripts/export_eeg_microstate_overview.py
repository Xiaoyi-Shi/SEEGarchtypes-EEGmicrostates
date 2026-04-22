from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from pycrostates.io import read_cluster
from scipy.interpolate import RBFInterpolator
from scipy.signal import find_peaks


BG_FILL = "#FBF7F1"
PANEL_FILL = "#FFFDF8"
INK_COLOR = "#1F2A33"
MUTED_COLOR = "#5B6670"
GRID_COLOR = "#E4DCCF"
LOW_COLOR = "#2166AC"
MID_COLOR = "#F7F3EA"
HIGH_COLOR = "#B2182B"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export EEG microstate topographies and descriptive parameters from cached labels."
    )
    parser.add_argument("--runtime-hash", default="97411c0ec4", help="Runtime hash suffix used by cached EEG outputs.")
    parser.add_argument("--model-path", default="", help="Override group microstate model FIF path.")
    parser.add_argument("--labels-path", default="", help="Override microstate labels parquet path.")
    parser.add_argument("--gfp-trace-path", default="", help="Override GFP trace parquet path.")
    parser.add_argument("--gfp-peaks-path", default="", help="Override GFP peaks parquet path.")
    parser.add_argument("--preprocessed-eeg-path", default="", help="Override preprocessed 19-channel EEG FIF path for waveform export.")
    parser.add_argument("--waveform-patient-id", default="806662", help="Patient used for the representative 19-channel EEG waveform segment.")
    parser.add_argument("--waveform-start-sec", type=float, default=20.0, help="Start time in seconds for the representative EEG waveform segment.")
    parser.add_argument("--waveform-end-sec", type=float, default=21.0, help="End time in seconds for the representative EEG waveform segment.")
    parser.add_argument("--waveform-peak-distance-ms", type=float, default=10.0, help="Fallback GFP peak distance when cached peaks are unavailable.")
    parser.add_argument(
        "--output-dir",
        default="artifacts/manual/eeg_microstate_overview",
        help="Directory for exported figures and CSV tables.",
    )
    parser.add_argument("--grid-size", type=int, default=96, help="Interpolated topomap grid size per axis.")
    return parser.parse_args()


def resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.exists():
        return candidate
    parent_candidate = Path("..") / candidate
    if parent_candidate.exists():
        return parent_candidate
    return candidate


def output_stem(runtime_hash: str) -> str:
    return f"eeg_microstate_{runtime_hash}"


def normalize_patterns(matrix: np.ndarray) -> np.ndarray:
    if matrix.size == 0:
        return np.empty_like(matrix, dtype=float)
    centered = matrix - np.mean(matrix, axis=1, keepdims=True)
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    norms[~np.isfinite(norms) | (norms == 0.0)] = 1.0
    patterns = centered / norms
    patterns[~np.isfinite(patterns)] = 0.0
    return patterns


def orient_pattern(pattern: np.ndarray) -> np.ndarray:
    values = np.asarray(pattern, dtype=float)
    if values.size == 0:
        return values.astype(float)
    working = values.copy()
    working[~np.isfinite(working)] = 0.0
    dominant_index = int(np.argmax(np.abs(working)))
    sign = -1.0 if working[dominant_index] < 0.0 else 1.0
    return working * sign


def oriented_templates(model) -> tuple[list[str], np.ndarray]:
    channels = [str(name) for name in model.info["ch_names"]]
    templates = normalize_patterns(np.asarray(model.cluster_centers_, dtype=float))
    oriented = np.vstack([orient_pattern(row) for row in templates])
    return channels, oriented


def build_plot_info(channels: list[str]) -> mne.Info:
    info = mne.create_info(channels, sfreq=250.0, ch_types="eeg")
    montage = mne.channels.make_standard_montage("standard_1020")
    info.set_montage(montage, match_case=False, on_missing="ignore")
    return info


def channel_xy(channels: list[str]) -> pd.DataFrame:
    montage = mne.channels.make_standard_montage("standard_1020")
    positions = montage.get_positions()["ch_pos"]
    rows: list[dict[str, object]] = []
    for channel in channels:
        key = channel if channel in positions else channel.upper()
        if key not in positions:
            raise KeyError(f"Could not find standard_1020 position for EEG channel: {channel}")
        xyz = np.asarray(positions[key], dtype=float)
        rows.append({"channel": channel, "x_raw": float(xyz[0]), "y_raw": float(xyz[1])})
    frame = pd.DataFrame(rows)
    xy = frame[["x_raw", "y_raw"]].to_numpy(dtype=float)
    xy = xy - xy.mean(axis=0, keepdims=True)
    radius = np.max(np.linalg.norm(xy, axis=1))
    if not np.isfinite(radius) or radius <= 0:
        radius = 1.0
    xy = xy / radius * 0.82
    frame["x"] = xy[:, 0]
    frame["y"] = xy[:, 1]
    return frame[["channel", "x", "y"]]


def write_template_tables(
    channels: list[str],
    templates: np.ndarray,
    output_dir: Path,
    stem: str,
    *,
    grid_size: int,
) -> tuple[Path, Path]:
    coords = channel_xy(channels)
    rows: list[dict[str, object]] = []
    for microstate in range(templates.shape[0]):
        for channel_index, channel in enumerate(channels):
            coord = coords.loc[coords["channel"] == channel].iloc[0]
            rows.append(
                {
                    "microstate": microstate,
                    "microstate_label": f"Microstate {microstate}",
                    "channel": channel,
                    "x": float(coord["x"]),
                    "y": float(coord["y"]),
                    "value": float(templates[microstate, channel_index]),
                }
            )
    template_path = output_dir / f"{stem}_template_values.csv"
    pd.DataFrame(rows).to_csv(template_path, index=False)

    grid_axis = np.linspace(-1.0, 1.0, grid_size)
    xx, yy = np.meshgrid(grid_axis, grid_axis)
    points = np.column_stack([xx.ravel(), yy.ravel()])
    mask = np.sqrt(points[:, 0] ** 2 + points[:, 1] ** 2) <= 0.98
    sensor_xy = coords[["x", "y"]].to_numpy(dtype=float)
    grid_rows: list[pd.DataFrame] = []
    for microstate in range(templates.shape[0]):
        interpolator = RBFInterpolator(sensor_xy, templates[microstate], kernel="thin_plate_spline", smoothing=0.01)
        values = np.full(points.shape[0], np.nan, dtype=float)
        values[mask] = interpolator(points[mask])
        grid_rows.append(
            pd.DataFrame(
                {
                    "microstate": microstate,
                    "microstate_label": f"Microstate {microstate}",
                    "x": points[:, 0],
                    "y": points[:, 1],
                    "value": values,
                    "inside_head": mask,
                }
            )
        )
    grid_path = output_dir / f"{stem}_topomap_grid.csv"
    pd.concat(grid_rows, ignore_index=True).to_csv(grid_path, index=False)
    return template_path, grid_path


def plot_topographies(channels: list[str], templates: np.ndarray, output_dir: Path, stem: str) -> tuple[Path, Path]:
    info = build_plot_info(channels)
    cmap = LinearSegmentedColormap.from_list("paper_diverging", [LOW_COLOR, MID_COLOR, HIGH_COLOR])
    scale_limit = float(np.nanmax(np.abs(templates)))
    if not np.isfinite(scale_limit) or scale_limit <= 0:
        scale_limit = 1.0

    n_states = templates.shape[0]
    fig, axes = plt.subplots(1, n_states, figsize=(3.1 * n_states, 3.35), constrained_layout=True)
    axes = np.atleast_1d(axes)
    fig.patch.set_facecolor(BG_FILL)
    image = None
    for microstate, ax in enumerate(axes):
        ax.set_facecolor(PANEL_FILL)
        image, _ = mne.viz.plot_topomap(
            templates[microstate],
            info,
            axes=ax,
            show=False,
            cmap=cmap,
            vlim=(-scale_limit, scale_limit),
            contours=6,
            sensors=True,
            outlines="head",
            extrapolate="head",
        )
        ax.set_title(f"Microstate {microstate}", color=INK_COLOR, fontsize=11, fontweight="bold", pad=6)
    if image is not None:
        colorbar = fig.colorbar(image, ax=axes.tolist(), shrink=0.70, pad=0.025)
        colorbar.set_label("Template loading", color=INK_COLOR, fontsize=10, fontweight="bold")
        colorbar.ax.tick_params(labelsize=8, colors=INK_COLOR)
    panel_svg = output_dir / f"{stem}_cluster_topographies.svg"
    panel_png = output_dir / f"{stem}_cluster_topographies.png"
    fig.savefig(panel_svg, facecolor=BG_FILL, bbox_inches="tight")
    fig.savefig(panel_png, facecolor=BG_FILL, dpi=420, bbox_inches="tight")
    plt.close(fig)

    for microstate in range(n_states):
        fig_single, ax = plt.subplots(figsize=(3.25, 3.25), constrained_layout=True)
        fig_single.patch.set_facecolor(BG_FILL)
        ax.set_facecolor(PANEL_FILL)
        image_single, _ = mne.viz.plot_topomap(
            templates[microstate],
            info,
            axes=ax,
            show=False,
            cmap=cmap,
            vlim=(-scale_limit, scale_limit),
            contours=6,
            sensors=True,
            outlines="head",
            extrapolate="head",
        )
        ax.set_title(f"Microstate {microstate}", color=INK_COLOR, fontsize=11, fontweight="bold", pad=6)
        colorbar = fig_single.colorbar(image_single, ax=ax, shrink=0.72, pad=0.02)
        colorbar.set_label("Template loading", color=INK_COLOR, fontsize=9, fontweight="bold")
        colorbar.ax.tick_params(labelsize=7, colors=INK_COLOR)
        fig_single.savefig(output_dir / f"{stem}_cluster_topography_microstate_{microstate}.svg", facecolor=BG_FILL, bbox_inches="tight")
        plt.close(fig_single)
    return panel_svg, panel_png


def contiguous_runs(labels: np.ndarray) -> list[tuple[int, int, int]]:
    if labels.size == 0:
        return []
    runs: list[tuple[int, int, int]] = []
    start = 0
    current = int(labels[0])
    for index in range(1, labels.size):
        label = int(labels[index])
        if label != current:
            runs.append((start, index, current))
            start = index
            current = label
    runs.append((start, labels.size, current))
    return runs


def sample_period_sec(frame: pd.DataFrame) -> float:
    times = np.sort(frame["time_sec"].to_numpy(dtype=float))
    if times.size < 2:
        return 0.004
    delta = float(np.nanmedian(np.diff(times)))
    return delta if np.isfinite(delta) and delta > 0 else 0.004


def subject_alias_table(patient_ids: pd.Series) -> pd.DataFrame:
    ids = sorted(str(item) for item in patient_ids.dropna().unique())
    return pd.DataFrame({"patient_id": ids, "patient_alias": [f"sub-{index + 1:02d}" for index in range(len(ids))]})


def compute_subject_parameters(labels: pd.DataFrame, gfp_trace: pd.DataFrame, output_dir: Path, stem: str) -> tuple[Path, Path, Path, Path]:
    labels = labels.copy()
    labels["patient_id"] = labels["patient_id"].astype(str)
    labels = labels.sort_values(["patient_id", "sample"]).reset_index(drop=True)
    gfp_trace = gfp_trace.copy()
    gfp_trace["patient_id"] = gfp_trace["patient_id"].astype(str)
    alias = subject_alias_table(labels["patient_id"])

    merged = labels.merge(
        gfp_trace[["patient_id", "sample", "gfp"]],
        on=["patient_id", "sample"],
        how="left",
    )
    microstates = sorted(int(state) for state in merged.loc[merged["microstate"] >= 0, "microstate"].unique())

    parameter_rows: list[dict[str, object]] = []
    transition_rows: list[dict[str, object]] = []
    for patient_id, patient_df in merged.groupby("patient_id", sort=True):
        patient_df = patient_df.sort_values("sample").reset_index(drop=True)
        dt = sample_period_sec(patient_df)
        valid_df = patient_df[patient_df["microstate"] >= 0].copy()
        if valid_df.empty:
            continue
        valid_labels = valid_df["microstate"].to_numpy(dtype=int)
        total_samples = int(valid_labels.size)
        total_duration_sec = float(total_samples * dt)
        gfp = valid_df["gfp"].to_numpy(dtype=float)
        corr = valid_df["corr"].to_numpy(dtype=float)
        gfp_weight = np.square(gfp)
        total_gfp_weight = float(np.nansum(gfp_weight))
        if not np.isfinite(total_gfp_weight) or total_gfp_weight <= 0:
            total_gfp_weight = 1.0

        runs = contiguous_runs(valid_labels)
        for state in microstates:
            state_mask = valid_labels == state
            state_runs = [(start, end, label) for start, end, label in runs if label == state]
            run_lengths = np.asarray([end - start for start, end, _ in state_runs], dtype=float)
            durations_ms = run_lengths * dt * 1000.0
            state_samples = int(state_mask.sum())
            parameter_rows.append(
                {
                    "patient_id": patient_id,
                    "microstate": state,
                    "microstate_label": f"Microstate {state}",
                    "n_samples": state_samples,
                    "n_segments": int(len(state_runs)),
                    "total_valid_samples": total_samples,
                    "total_duration_sec": total_duration_sec,
                    "coverage": float(state_samples / total_samples) if total_samples else np.nan,
                    "coverage_pct": float(state_samples / total_samples * 100.0) if total_samples else np.nan,
                    "mean_duration_ms": float(np.nanmean(durations_ms)) if durations_ms.size else np.nan,
                    "median_duration_ms": float(np.nanmedian(durations_ms)) if durations_ms.size else np.nan,
                    "occurrence_per_sec": float(len(state_runs) / total_duration_sec) if total_duration_sec > 0 else np.nan,
                    "mean_correlation": float(np.nanmean(corr[state_mask])) if state_samples else np.nan,
                    "gev": float(np.nansum(gfp_weight[state_mask] * np.square(corr[state_mask])) / total_gfp_weight),
                    "gev_pct": float(np.nansum(gfp_weight[state_mask] * np.square(corr[state_mask])) / total_gfp_weight * 100.0),
                }
            )

        transition_counts: dict[tuple[int, int], int] = {}
        outgoing_counts: dict[int, int] = {}
        for (_, _, previous_state), (_, _, next_state) in zip(runs[:-1], runs[1:]):
            if previous_state < 0 or next_state < 0:
                continue
            transition_counts[(previous_state, next_state)] = transition_counts.get((previous_state, next_state), 0) + 1
            outgoing_counts[previous_state] = outgoing_counts.get(previous_state, 0) + 1
        for source in microstates:
            for target in microstates:
                count = transition_counts.get((source, target), 0)
                outgoing = outgoing_counts.get(source, 0)
                transition_rows.append(
                    {
                        "patient_id": patient_id,
                        "from_state": source,
                        "to_state": target,
                        "from_label": f"Microstate {source}",
                        "to_label": f"Microstate {target}",
                        "n_transitions": count,
                        "n_outgoing": outgoing,
                        "transition_probability": float(count / outgoing) if outgoing > 0 else np.nan,
                    }
                )

    subject_parameters = pd.DataFrame(parameter_rows).merge(alias, on="patient_id", how="left")
    subject_parameters = subject_parameters.drop(columns=["patient_id"])
    subject_parameters = subject_parameters[
        ["patient_alias", "microstate", "microstate_label", *[col for col in subject_parameters.columns if col not in {"patient_alias", "microstate", "microstate_label"}]]
    ]
    subject_path = output_dir / f"{stem}_subject_parameters_anonymized.csv"
    subject_parameters.to_csv(subject_path, index=False)

    metric_specs = [
        ("coverage_pct", "Coverage (%)"),
        ("mean_duration_ms", "Mean duration (ms)"),
        ("occurrence_per_sec", "Occurrence (events/s)"),
        ("gev_pct", "GEV (%)"),
        ("mean_correlation", "Mean template correlation"),
    ]
    long_rows: list[pd.DataFrame] = []
    for metric, metric_label in metric_specs:
        frame = subject_parameters[["patient_alias", "microstate", "microstate_label", metric]].copy()
        frame = frame.rename(columns={metric: "value"})
        frame["metric"] = metric
        frame["metric_label"] = metric_label
        long_rows.append(frame)
    parameter_long = pd.concat(long_rows, ignore_index=True)
    long_path = output_dir / f"{stem}_parameter_long.csv"
    parameter_long.to_csv(long_path, index=False)

    summary_frames = []
    for metric, metric_label in metric_specs:
        summary = (
            subject_parameters.groupby(["microstate", "microstate_label"], as_index=False)
            .agg(
                count=(metric, "count"),
                mean=(metric, "mean"),
                std=(metric, "std"),
                median=(metric, "median"),
                min=(metric, "min"),
                max=(metric, "max"),
            )
            .reset_index()
            .drop(columns=["index"])
        )
        summary["metric"] = metric
        summary["metric_label"] = metric_label
        summary_frames.append(summary)
    group_parameters = pd.concat(summary_frames, ignore_index=True)
    group_path = output_dir / f"{stem}_group_parameters.csv"
    group_parameters.to_csv(group_path, index=False)

    transitions = pd.DataFrame(transition_rows).merge(alias, on="patient_id", how="left")
    transition_summary = (
        transitions.groupby(["from_state", "to_state", "from_label", "to_label"], as_index=False)
        .agg(
            n_subjects=("transition_probability", "count"),
            mean_transition_probability=("transition_probability", "mean"),
            sd_transition_probability=("transition_probability", "std"),
            median_transition_probability=("transition_probability", "median"),
            min_transition_probability=("transition_probability", "min"),
            max_transition_probability=("transition_probability", "max"),
        )
        .reset_index()
        .drop(columns=["index"])
    )
    transition_path = output_dir / f"{stem}_transition_matrix.csv"
    transition_summary.to_csv(transition_path, index=False)
    return subject_path, long_path, group_path, transition_path


def write_manifest(output_dir: Path, stem: str, paths: list[Path]) -> Path:
    manifest = pd.DataFrame({"artifact": [path.name for path in paths], "path": [str(path) for path in paths]})
    manifest_path = output_dir / f"{stem}_manifest.csv"
    manifest.to_csv(manifest_path, index=False)
    return manifest_path


def eeg_channel_group(channel: str) -> str:
    if channel.startswith("Fp") or channel.startswith("F"):
        return "Frontal"
    if channel.startswith("T"):
        return "Temporal"
    if channel.startswith("C"):
        return "Central"
    if channel.startswith("P"):
        return "Parietal"
    if channel.startswith("O"):
        return "Occipital"
    return "Other"


def export_eeg_waveform_segment(
    *,
    raw_path: Path,
    gfp_peaks_path: Path,
    output_dir: Path,
    stem: str,
    patient_id: str,
    start_sec: float,
    end_sec: float,
    fallback_peak_distance_ms: float,
) -> tuple[Path, Path, Path]:
    if end_sec <= start_sec:
        raise ValueError("waveform-end-sec must be greater than waveform-start-sec.")
    raw = mne.io.read_raw_fif(raw_path, preload=True, verbose="ERROR")
    if end_sec > float(raw.times[-1]) + 1.0 / float(raw.info["sfreq"]):
        raise ValueError(
            f"Requested waveform window {start_sec}-{end_sec}s exceeds raw duration {float(raw.times[-1]):.3f}s."
        )
    segment = raw.copy().crop(tmin=float(start_sec), tmax=float(end_sec), include_tmax=False)
    sfreq = float(segment.info["sfreq"])
    data_uv = segment.get_data(picks="all") * 1e6
    channels = [str(channel) for channel in segment.ch_names]
    n_samples = int(data_uv.shape[1])
    relative_time_ms = np.arange(n_samples, dtype=float) / sfreq * 1000.0
    absolute_time_sec = float(start_sec) + relative_time_ms / 1000.0
    global_scale_uv = float(np.nanpercentile(np.abs(data_uv[np.isfinite(data_uv)]), 98)) if data_uv.size else 1.0
    if not np.isfinite(global_scale_uv) or global_scale_uv <= 0:
        global_scale_uv = 1.0

    gfp_uv = np.nanstd(data_uv, axis=0, ddof=0)
    peak_samples = np.array([], dtype=int)
    if gfp_peaks_path.exists():
        peaks_df = pd.read_parquet(gfp_peaks_path)
        peaks_df["patient_id"] = peaks_df["patient_id"].astype(str)
        patient_peaks = peaks_df[
            (peaks_df["patient_id"] == str(patient_id))
            & (peaks_df["event_sec"] >= float(start_sec))
            & (peaks_df["event_sec"] < float(end_sec))
        ].copy()
        if not patient_peaks.empty:
            peak_samples = np.rint((patient_peaks["event_sec"].to_numpy(dtype=float) - float(start_sec)) * sfreq).astype(int)
            peak_samples = peak_samples[(peak_samples >= 0) & (peak_samples < n_samples)]
    if peak_samples.size == 0 and gfp_uv.size:
        distance_samples = max(1, int(round(float(fallback_peak_distance_ms) / 1000.0 * sfreq)))
        peak_samples, _ = find_peaks(gfp_uv, distance=distance_samples)
    peak_mask = np.zeros(n_samples, dtype=bool)
    peak_mask[peak_samples] = True

    channel_rows: list[dict[str, object]] = []
    n_channels = len(channels)
    for channel_index, channel in enumerate(channels):
        channel_y = float(n_channels - channel_index)
        normalized = np.clip(data_uv[channel_index] / global_scale_uv, -1.45, 1.45) * 0.42
        display_y = channel_y - normalized
        for sample_index in range(n_samples):
            channel_rows.append(
                {
                    "patient_id": str(patient_id),
                    "channel": channel,
                    "channel_group": eeg_channel_group(channel),
                    "channel_order": channel_index + 1,
                    "channel_y": channel_y,
                    "sample": sample_index,
                    "time_sec": absolute_time_sec[sample_index],
                    "relative_time_ms": relative_time_ms[sample_index],
                    "amplitude_uv": float(data_uv[channel_index, sample_index]),
                    "normalized_amplitude": float(normalized[sample_index]),
                    "display_y": float(display_y[sample_index]),
                }
            )
    waveform_path = output_dir / f"{stem}_waveform_segment_long.csv"
    pd.DataFrame(channel_rows).to_csv(waveform_path, index=False)

    gfp_path = output_dir / f"{stem}_waveform_gfp_peaks.csv"
    pd.DataFrame(
        {
            "patient_id": str(patient_id),
            "sample": np.arange(n_samples, dtype=int),
            "time_sec": absolute_time_sec,
            "relative_time_ms": relative_time_ms,
            "gfp_uv": gfp_uv.astype(float),
            "is_peak": peak_mask,
        }
    ).to_csv(gfp_path, index=False)

    info_path = output_dir / f"{stem}_waveform_segment_info.csv"
    pd.DataFrame(
        [
            {"key": "patient_id", "value": str(patient_id)},
            {"key": "preprocessed_eeg_path", "value": str(raw_path)},
            {"key": "start_sec", "value": float(start_sec)},
            {"key": "end_sec", "value": float(end_sec)},
            {"key": "duration_sec", "value": float(end_sec - start_sec)},
            {"key": "sfreq", "value": sfreq},
            {"key": "n_channels", "value": n_channels},
            {"key": "n_samples", "value": n_samples},
            {"key": "global_scale_uv", "value": global_scale_uv},
            {"key": "n_gfp_peaks", "value": int(peak_mask.sum())},
        ]
    ).to_csv(info_path, index=False)
    return waveform_path, gfp_path, info_path


def main() -> None:
    args = parse_args()
    runtime_hash = args.runtime_hash
    model_path = resolve_path(args.model_path or f"artifacts/cache/eeg/group_microstate_model_band_1_40_{runtime_hash}.fif")
    labels_path = resolve_path(args.labels_path or f"artifacts/cache/eeg/microstate_labels_band_1_40_{runtime_hash}.parquet")
    gfp_trace_path = resolve_path(args.gfp_trace_path or f"artifacts/cache/eeg/gfp_trace_band_1_40_{runtime_hash}.parquet")
    gfp_peaks_path = resolve_path(args.gfp_peaks_path or f"artifacts/cache/eeg/gfp_peaks_band_1_40_{runtime_hash}.parquet")
    preprocessed_eeg_path = resolve_path(
        args.preprocessed_eeg_path
        or f"artifacts/cache/eeg/{args.waveform_patient_id}_preprocessed_band_1_40_{runtime_hash}.fif"
    )
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = output_stem(runtime_hash)

    model = read_cluster(model_path)
    channels, templates = oriented_templates(model)
    topography_svg, topography_png = plot_topographies(channels, templates, output_dir, stem)
    template_path, grid_path = write_template_tables(channels, templates, output_dir, stem, grid_size=args.grid_size)

    labels = pd.read_parquet(labels_path)
    gfp_trace = pd.read_parquet(gfp_trace_path)
    subject_path, long_path, group_path, transition_path = compute_subject_parameters(labels, gfp_trace, output_dir, stem)
    waveform_path, waveform_gfp_path, waveform_info_path = export_eeg_waveform_segment(
        raw_path=preprocessed_eeg_path,
        gfp_peaks_path=gfp_peaks_path,
        output_dir=output_dir,
        stem=stem,
        patient_id=str(args.waveform_patient_id),
        start_sec=float(args.waveform_start_sec),
        end_sec=float(args.waveform_end_sec),
        fallback_peak_distance_ms=float(args.waveform_peak_distance_ms),
    )

    manifest_path = write_manifest(
        output_dir,
        stem,
        [
            topography_svg,
            topography_png,
            template_path,
            grid_path,
            subject_path,
            long_path,
            group_path,
            transition_path,
            waveform_path,
            waveform_gfp_path,
            waveform_info_path,
        ],
    )
    print(f"Wrote EEG microstate overview artifacts to {output_dir}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
