from __future__ import annotations

import argparse
from pathlib import Path
import re
from typing import Any

import numpy as np
import pandas as pd

from seeg_eegmicrostates.coupling import (
    build_seeg_field_metric_trace,
    build_seeg_field_peak_table,
    normalize_field_normalization,
)
from seeg_eegmicrostates.config import YEO17_PARCELLATION_COLUMN, YEO17_PARCELLATION_NAME
from seeg_eegmicrostates.io import load_atlas_table
from seeg_eegmicrostates.seeg import build_same_region_bipolar_map
from seeg_eegmicrostates.seeg.preprocess import load_and_crop_bipolar_seeg


DEFAULT_OUTPUT_DIR = Path("artifacts/manual/seeg_peak_segments")
DEFAULT_MIN_PEAK_DISTANCE_MS = 10
DEFAULT_UNMAPPED_REGION = "Unmapped"
YEO17_NETWORK_ORDER: tuple[str, ...] = (
    "VisualA",
    "VisualB",
    "SomMotA",
    "SomMotB",
    "DorsAttnA",
    "DorsAttnB",
    "SalVentAttnA",
    "SalVentAttnB",
    "LimbicA",
    "LimbicB",
    "ContA",
    "ContB",
    "ContC",
    "DefaultA",
    "DefaultB",
    "DefaultC",
    "TempPar",
)


def _sanitize_token(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_").lower()
    return cleaned or "segment"


def _default_patient_id(seeg_path: Path) -> str:
    stem = seeg_path.name
    if stem.endswith(".fif.gz"):
        stem = stem[: -len(".fif.gz")]
    elif stem.endswith(".fif"):
        stem = stem[: -len(".fif")]
    return stem


def _segment_stem(patient_id: str, start_sec: float, end_sec: float) -> str:
    start_ms = int(round(float(start_sec) * 1000.0))
    end_ms = int(round(float(end_sec) * 1000.0))
    return f"{_sanitize_token(patient_id)}_{start_ms:07d}ms_{end_ms:07d}ms"


def _validate_window(start_sec: float, end_sec: float) -> tuple[float, float]:
    start = float(start_sec)
    end = float(end_sec)
    if not np.isfinite(start) or not np.isfinite(end):
        raise ValueError("start_sec and end_sec must be finite numbers.")
    if end <= start:
        raise ValueError("end_sec must be greater than start_sec.")
    return start, end


def _build_channel_df(seeg_path: Path, start_sec: float, end_sec: float) -> pd.DataFrame:
    raw = load_and_crop_bipolar_seeg(seeg_path, start_sec=start_sec, end_sec=end_sec)
    data = raw.get_data()
    frame = pd.DataFrame(data.T, columns=list(raw.ch_names))
    frame.insert(0, "time_sec", raw.times.astype(float) + float(start_sec))
    return frame


def _channel_columns(channel_df: pd.DataFrame) -> list[str]:
    return [column for column in channel_df.columns if column != "time_sec"]


def _robust_mad(values: np.ndarray, axis: int = 0) -> np.ndarray:
    median = np.nanmedian(values, axis=axis, keepdims=True)
    mad = np.nanmedian(np.abs(values - median), axis=axis)
    return 1.4826 * mad


def _standardize_channel_df(channel_df: pd.DataFrame, normalization: str) -> pd.DataFrame:
    standardized = pd.DataFrame({"time_sec": channel_df["time_sec"].to_numpy(dtype=float)})
    channel_columns = _channel_columns(channel_df)
    if not channel_columns:
        return standardized
    values = channel_df[channel_columns].to_numpy(dtype=float)
    strategy = normalize_field_normalization(normalization)
    if strategy == "robust-zscore":
        centers = np.nanmedian(values, axis=0, keepdims=True)
        scales = _robust_mad(values, axis=0)[None, :]
    else:
        centers = np.nanmean(values, axis=0, keepdims=True)
        scales = np.nanstd(values, axis=0, ddof=0, keepdims=True)
    scales = np.asarray(scales, dtype=float)
    scales[~np.isfinite(scales) | (scales == 0.0)] = 1.0
    normalized = (values - centers) / scales
    normalized[~np.isfinite(normalized)] = 0.0
    for index, channel in enumerate(channel_columns):
        standardized[channel] = normalized[:, index]
    return standardized


def _resolve_atlas_path(seeg_path: Path, atlas_path: str | Path | None) -> Path | None:
    if atlas_path is not None:
        resolved = Path(atlas_path)
        if not resolved.exists():
            raise FileNotFoundError(f"Atlas file not found: {resolved}")
        return resolved
    for parent in (seeg_path.parent, *seeg_path.parents):
        candidate = parent / "MNI" / "Atlas.tsv"
        if candidate.exists():
            return candidate
        sibling_candidate = parent.parent / "MNI" / "Atlas.tsv"
        if sibling_candidate.exists():
            return sibling_candidate
    return None


def _network_sort_key(region: str) -> tuple[int, str]:
    normalized = str(region)
    if normalized == DEFAULT_UNMAPPED_REGION:
        return (len(YEO17_NETWORK_ORDER) + 1, normalized)
    if normalized in YEO17_NETWORK_ORDER:
        return (YEO17_NETWORK_ORDER.index(normalized), normalized)
    return (len(YEO17_NETWORK_ORDER), normalized)


def _build_channel_layout(
    channel_df: pd.DataFrame,
    *,
    patient_id: str,
    atlas_path: Path | None,
    atlas_column: str,
    parcellation_name: str,
) -> pd.DataFrame:
    channel_order = _channel_columns(channel_df)
    base = pd.DataFrame({"bipolar_channel": channel_order})
    if atlas_path is None:
        layout_df = base.copy()
        layout_df["patient_id"] = patient_id
        layout_df["contact_a"] = pd.NA
        layout_df["contact_b"] = pd.NA
        layout_df["region"] = DEFAULT_UNMAPPED_REGION
        layout_df["valid_same_region"] = False
        layout_df["atlas_path"] = pd.NA
        layout_df["atlas_column"] = atlas_column
        layout_df["parcellation_name"] = parcellation_name
        layout_df["channel_order"] = np.arange(layout_df.shape[0], dtype=int)
        return layout_df
    atlas_df = load_atlas_table(atlas_path)
    mapping_df = build_same_region_bipolar_map(
        atlas_df,
        channel_order,
        patient_id=patient_id,
        atlas_column=atlas_column,
        parcellation_name=parcellation_name,
    )
    layout_df = base.merge(mapping_df, on="bipolar_channel", how="left")
    layout_df["patient_id"] = layout_df["patient_id"].fillna(patient_id)
    layout_df["region"] = layout_df["region"].fillna(DEFAULT_UNMAPPED_REGION)
    layout_df["valid_same_region"] = layout_df["valid_same_region"].fillna(False).astype(bool)
    layout_df["atlas_path"] = str(atlas_path)
    layout_df["atlas_column"] = atlas_column
    layout_df["parcellation_name"] = parcellation_name
    layout_df = layout_df.sort_values(
        by=["region", "bipolar_channel"],
        key=lambda series: series.map(_network_sort_key) if series.name == "region" else series.astype(str),
        kind="stable",
    ).reset_index(drop=True)
    layout_df["channel_order"] = np.arange(layout_df.shape[0], dtype=int)
    return layout_df


def _select_export_layout(channel_layout_df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    mapped = channel_layout_df[channel_layout_df["valid_same_region"]].copy().reset_index(drop=True)
    if mapped.shape[0] >= 2:
        mapped["channel_order"] = np.arange(mapped.shape[0], dtype=int)
        return mapped, True
    fallback = channel_layout_df.copy().reset_index(drop=True)
    fallback["channel_order"] = np.arange(fallback.shape[0], dtype=int)
    return fallback, False


def _build_segment_matrix(
    channel_df: pd.DataFrame,
    trace_df: pd.DataFrame,
    peak_df: pd.DataFrame,
    *,
    spatial_std_row_name: str = "spatial_std_raw",
    rms_row_name: str = "rms_raw",
) -> pd.DataFrame:
    channel_columns = _channel_columns(channel_df)
    point_columns = [f"point_{index:05d}" for index in range(channel_df.shape[0])]
    sample_values = channel_df[channel_columns].to_numpy(dtype=float)
    peak_mask = np.zeros(channel_df.shape[0], dtype=int)
    if not peak_df.empty:
        peak_indices = peak_df["sample"].to_numpy(dtype=int)
        peak_indices = peak_indices[(peak_indices >= 0) & (peak_indices < peak_mask.size)]
        peak_mask[peak_indices] = 1
    rows: list[list[Any]] = []
    for channel in channel_columns:
        rows.append([channel, *channel_df[channel].to_numpy(dtype=float).tolist()])
    rows.extend(
        [
            ["time_sec", *channel_df["time_sec"].to_numpy(dtype=float).tolist()],
            [
                "relative_time_ms",
                *((channel_df["time_sec"].to_numpy(dtype=float) - float(channel_df["time_sec"].iloc[0])) * 1000.0).tolist(),
            ],
            ["sample_index", *np.arange(channel_df.shape[0], dtype=int).tolist()],
            ["peak_metric_value", *trace_df["peak_metric_value"].to_numpy(dtype=float).tolist()],
            [spatial_std_row_name, *np.nanstd(sample_values, axis=1, ddof=0).tolist()],
            [rms_row_name, *np.sqrt(np.nanmean(sample_values**2, axis=1)).tolist()],
            ["is_peak_sample", *peak_mask.tolist()],
        ]
    )
    return pd.DataFrame(rows, columns=["row_name", *point_columns])


def _build_segment_info(
    *,
    patient_id: str,
    seeg_path: Path,
    start_sec: float,
    end_sec: float,
    channel_df: pd.DataFrame,
    trace_df: pd.DataFrame,
    peak_df: pd.DataFrame,
    peak_metric: str,
    normalization: str,
    min_peak_distance_ms: int,
    input_channel_df: pd.DataFrame,
    full_channel_layout_df: pd.DataFrame,
    export_channel_layout_df: pd.DataFrame,
    atlas_path: Path | None,
    atlas_column: str,
    parcellation_name: str,
    mapping_filter_applied: bool,
    channel_normalization: str,
) -> pd.DataFrame:
    sample_period_sec = 0.0
    if channel_df.shape[0] > 1:
        sample_period_sec = float(np.median(np.diff(channel_df["time_sec"].to_numpy(dtype=float))))
    return pd.DataFrame(
        [
            {"key": "patient_id", "value": patient_id},
            {"key": "seeg_path", "value": str(seeg_path)},
            {"key": "start_sec", "value": float(start_sec)},
            {"key": "end_sec", "value": float(end_sec)},
            {"key": "duration_sec", "value": float(end_sec - start_sec)},
            {"key": "n_input_channels", "value": int(len(_channel_columns(input_channel_df)))},
            {"key": "n_channels", "value": int(len(_channel_columns(channel_df)))},
            {"key": "n_samples", "value": int(channel_df.shape[0])},
            {"key": "sample_period_sec", "value": sample_period_sec},
            {"key": "peak_metric", "value": peak_metric},
            {"key": "normalization", "value": normalization},
            {"key": "min_peak_distance_ms", "value": int(min_peak_distance_ms)},
            {"key": "n_detected_peaks", "value": int(peak_df.shape[0])},
            {"key": "n_channels_used_for_metric", "value": int(trace_df["n_channels_used"].iloc[0]) if not trace_df.empty else 0},
            {"key": "atlas_path", "value": str(atlas_path) if atlas_path is not None else pd.NA},
            {"key": "atlas_column", "value": atlas_column},
            {"key": "parcellation_name", "value": parcellation_name},
            {"key": "channel_normalization", "value": channel_normalization},
            {"key": "mapping_filter_applied", "value": bool(mapping_filter_applied)},
            {"key": "n_mapped_channels", "value": int(full_channel_layout_df["valid_same_region"].sum())},
            {"key": "n_export_channels", "value": int(export_channel_layout_df.shape[0])},
            {"key": "n_region_groups", "value": int(export_channel_layout_df["region"].nunique())},
        ]
    )


def _plot_segment_waveform(
    channel_df: pd.DataFrame,
    peak_df: pd.DataFrame,
    trace_df: pd.DataFrame,
    channel_layout_df: pd.DataFrame,
    *,
    patient_id: str,
    title_suffix: str,
    output_paths: list[Path],
) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ordered_channels = channel_layout_df["bipolar_channel"].astype(str).tolist()
    values = channel_df[ordered_channels].to_numpy(dtype=float).T
    times = channel_df["time_sec"].to_numpy(dtype=float)
    for output_path in output_paths:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    if values.size == 0:
        raise ValueError("No channel data available for plotting.")

    finite = values[np.isfinite(values)]
    global_scale = float(np.nanpercentile(np.abs(finite), 98)) if finite.size else 1.0
    if not np.isfinite(global_scale) or global_scale <= 0.0:
        global_scale = 1.0
    waveform_values = np.clip(values / global_scale, -1.5, 1.5) * 0.42

    width = max(10.0, min(28.0, values.shape[1] / 28.0))
    height = max(6.0, min(20.0, values.shape[0] / 2.0))
    with plt.rc_context({"svg.fonttype": "none"}):
        fig, (trace_ax, main_ax) = plt.subplots(
            2,
            1,
            figsize=(width, height),
            sharex=True,
            gridspec_kw={"height_ratios": [1, max(4, values.shape[0])]},
        )
        trace_values = trace_df["peak_metric_value"].to_numpy(dtype=float)
        trace_ax.plot(times, trace_values, color="#9f1239", linewidth=1.0)
        trace_ax.fill_between(times, 0.0, trace_values, color="#fb7185", alpha=0.25)
        trace_ax.set_ylabel("Peak")
        trace_ax.tick_params(axis="y", labelsize=8)
        region_sequence = channel_layout_df["region"].astype(str).tolist()
        unique_regions = list(dict.fromkeys(region_sequence))
        color_lookup = {
            region: plt.cm.tab20(index % 20)
            for index, region in enumerate(unique_regions)
        }
        baseline_positions = np.arange(len(ordered_channels), dtype=float)
        for index, channel in enumerate(ordered_channels):
            baseline = baseline_positions[index]
            region = region_sequence[index]
            main_ax.plot(
                times,
                baseline - waveform_values[index],
                color=color_lookup[region],
                linewidth=0.8,
                alpha=0.95,
            )
        main_groups = channel_layout_df.groupby("region", sort=False)
        left_ticks: list[float] = []
        left_labels: list[str] = []
        boundaries: list[float] = []
        current_index = 0
        for region, group in main_groups:
            start = current_index
            stop = current_index + group.shape[0]
            left_ticks.append(start + (group.shape[0] - 1) / 2.0)
            left_labels.append(str(region))
            current_index = stop
            boundaries.append(stop - 0.5)
        main_ax.set_yticks(left_ticks)
        main_ax.set_yticklabels(left_labels)
        main_ax.tick_params(axis="y", labelsize=8)
        right_ax = main_ax.twinx()
        main_ax.set_yticks(left_ticks)
        right_ax.set_yticks(baseline_positions)
        right_ax.set_yticklabels(ordered_channels)
        right_ax.tick_params(axis="y", labelsize=6)
        main_ax.set_ylim(-0.75, len(ordered_channels) - 0.25)
        main_ax.invert_yaxis()
        right_ax.set_ylim(main_ax.get_ylim())
        xtick_count = min(10, values.shape[1])
        xticks = np.linspace(times[0], times[-1], xtick_count)
        main_ax.set_xticks(xticks)
        main_ax.set_xticklabels([f"{tick:.2f}" for tick in xticks], rotation=45, ha="right")
        for peak_sample in peak_df.get("sample", pd.Series(dtype=int)).astype(int).tolist():
            if 0 <= peak_sample < times.size:
                peak_time = float(times[peak_sample])
                trace_ax.axvline(peak_time, color="#f59e0b", linewidth=0.8, alpha=0.9)
                main_ax.axvline(peak_time, color="#f59e0b", linewidth=0.8, alpha=0.9)
        for boundary in boundaries[:-1]:
            main_ax.axhline(boundary, color="black", linewidth=0.6, alpha=0.6)
        trace_ax.set_title(f"{patient_id} SEEG segment waveform plot ordered by Yeo17 ({title_suffix})")
        trace_ax.tick_params(axis="x", labelbottom=False)
        main_ax.set_xlabel("Time (s)")
        main_ax.set_ylabel("Yeo17 region")
        right_ax.set_ylabel("Bipolar channel")
        fig.tight_layout()
        for output_path in output_paths:
            if output_path.suffix.lower() == ".svg":
                fig.savefig(output_path)
            else:
                fig.savefig(output_path, dpi=200)
        plt.close(fig)
    return output_paths


def export_seeg_peak_segment(
    *,
    seeg_path: str | Path,
    start_sec: float,
    end_sec: float,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    patient_id: str | None = None,
    peak_metric: str = "rms",
    normalization: str = "zscore",
    min_peak_distance_ms: int = DEFAULT_MIN_PEAK_DISTANCE_MS,
    atlas_path: str | Path | None = None,
    atlas_column: str = YEO17_PARCELLATION_COLUMN,
    parcellation_name: str = YEO17_PARCELLATION_NAME,
) -> dict[str, Path]:
    start_sec, end_sec = _validate_window(start_sec, end_sec)
    seeg_path = Path(seeg_path)
    if not seeg_path.exists():
        raise FileNotFoundError(f"SEEG file not found: {seeg_path}")

    resolved_patient_id = str(patient_id).strip() if patient_id else _default_patient_id(seeg_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = _segment_stem(resolved_patient_id, start_sec, end_sec)
    resolved_atlas_path = _resolve_atlas_path(seeg_path, atlas_path)

    input_channel_df = _build_channel_df(seeg_path, start_sec, end_sec)
    full_channel_layout_df = _build_channel_layout(
        input_channel_df,
        patient_id=resolved_patient_id,
        atlas_path=resolved_atlas_path,
        atlas_column=atlas_column,
        parcellation_name=parcellation_name,
    )
    channel_layout_df, mapping_filter_applied = _select_export_layout(full_channel_layout_df)
    exported_channels = channel_layout_df["bipolar_channel"].astype(str).tolist()
    channel_df = input_channel_df[["time_sec", *exported_channels]].copy()
    standardized_channel_df = _standardize_channel_df(channel_df, normalization)
    trace_df = build_seeg_field_metric_trace(
        channel_df,
        patient_id=resolved_patient_id,
        peak_metric=peak_metric,
        normalization=normalization,
    )
    if trace_df.empty:
        raise ValueError("Unable to compute a SEEG peak trace for this segment. At least two valid bipolar channels are required.")
    peak_df = build_seeg_field_peak_table(
        trace_df,
        patient_id=resolved_patient_id,
        min_peak_distance_ms=min_peak_distance_ms,
    )
    segment_matrix_df = _build_segment_matrix(channel_df, trace_df, peak_df)
    standardized_segment_matrix_df = _build_segment_matrix(
        standardized_channel_df,
        trace_df,
        peak_df,
        spatial_std_row_name=f"spatial_std_{normalize_field_normalization(normalization)}",
        rms_row_name=f"rms_{normalize_field_normalization(normalization)}",
    )
    info_df = _build_segment_info(
        patient_id=resolved_patient_id,
        seeg_path=seeg_path,
        start_sec=start_sec,
        end_sec=end_sec,
        channel_df=channel_df,
        trace_df=trace_df,
        peak_df=peak_df,
        peak_metric=peak_metric,
        normalization=normalization,
        min_peak_distance_ms=min_peak_distance_ms,
        input_channel_df=input_channel_df,
        full_channel_layout_df=full_channel_layout_df,
        export_channel_layout_df=channel_layout_df,
        atlas_path=resolved_atlas_path,
        atlas_column=atlas_column,
        parcellation_name=parcellation_name,
        mapping_filter_applied=mapping_filter_applied,
        channel_normalization=normalize_field_normalization(normalization),
    )

    output_paths = {
        "segment_info": output_dir / f"{stem}_segment_info.csv",
        "segment_matrix": output_dir / f"{stem}_segment_matrix.csv",
        "standardized_segment_matrix": output_dir / f"{stem}_standardized_segment_matrix.csv",
        "peak_summary": output_dir / f"{stem}_peak_summary.csv",
        "peak_trace": output_dir / f"{stem}_peak_trace.csv",
        "channel_layout": output_dir / f"{stem}_channel_layout.csv",
        "bundle": output_dir / f"{stem}_segment_bundle.xlsx",
        "waveform": output_dir / f"{stem}_segment_waveform.png",
        "waveform_svg": output_dir / f"{stem}_segment_waveform.svg",
        "standardized_waveform": output_dir / f"{stem}_standardized_waveform.png",
        "standardized_waveform_svg": output_dir / f"{stem}_standardized_waveform.svg",
    }

    info_df.to_csv(output_paths["segment_info"], index=False, encoding="utf-8")
    segment_matrix_df.to_csv(output_paths["segment_matrix"], index=False, encoding="utf-8")
    standardized_segment_matrix_df.to_csv(output_paths["standardized_segment_matrix"], index=False, encoding="utf-8")
    peak_df.to_csv(output_paths["peak_summary"], index=False, encoding="utf-8")
    trace_df.to_csv(output_paths["peak_trace"], index=False, encoding="utf-8")
    channel_layout_df.to_csv(output_paths["channel_layout"], index=False, encoding="utf-8")
    with pd.ExcelWriter(output_paths["bundle"], engine="openpyxl") as writer:
        info_df.to_excel(writer, index=False, sheet_name="segment_info")
        segment_matrix_df.to_excel(writer, index=False, sheet_name="segment_matrix")
        standardized_segment_matrix_df.to_excel(writer, index=False, sheet_name="standardized_segment_matrix")
        peak_df.to_excel(writer, index=False, sheet_name="peak_summary")
        trace_df.to_excel(writer, index=False, sheet_name="peak_trace")
        channel_layout_df.to_excel(writer, index=False, sheet_name="channel_layout")
    _plot_segment_waveform(
        channel_df,
        peak_df,
        trace_df,
        channel_layout_df,
        patient_id=resolved_patient_id,
        title_suffix="raw amplitude",
        output_paths=[output_paths["waveform"], output_paths["waveform_svg"]],
    )
    _plot_segment_waveform(
        standardized_channel_df,
        peak_df,
        trace_df,
        channel_layout_df,
        patient_id=resolved_patient_id,
        title_suffix=f"{normalize_field_normalization(normalization)} standardized",
        output_paths=[output_paths["standardized_waveform"], output_paths["standardized_waveform_svg"]],
    )
    return output_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export a specified SEEG time segment into a channel-by-sample matrix, "
            "append derived peak rows, and generate a waveform plot plus peak summary."
        )
    )
    parser.add_argument("--seeg-path", required=True, help="Path to the bipolar SEEG FIF file.")
    parser.add_argument("--start-sec", required=True, type=float, help="Segment start time in seconds.")
    parser.add_argument("--end-sec", required=True, type=float, help="Segment end time in seconds.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for exported CSV/XLSX/PNG outputs. Default: {DEFAULT_OUTPUT_DIR.as_posix()}",
    )
    parser.add_argument("--patient-id", help="Optional patient identifier. Defaults to the input file stem.")
    parser.add_argument(
        "--atlas-path",
        type=Path,
        help="Optional path to Atlas.tsv. If omitted, the script will look for a sibling patient MNI/Atlas.tsv.",
    )
    parser.add_argument(
        "--peak-metric",
        default="rms",
        choices=("rms", "spatial-std"),
        help="Peak metric applied to normalized bipolar channels.",
    )
    parser.add_argument(
        "--normalization",
        default="zscore",
        choices=("zscore", "robust-zscore"),
        help="Channel normalization applied before the peak metric is computed.",
    )
    parser.add_argument(
        "--min-peak-distance-ms",
        type=int,
        default=DEFAULT_MIN_PEAK_DISTANCE_MS,
        help=f"Minimum peak distance in milliseconds. Default: {DEFAULT_MIN_PEAK_DISTANCE_MS}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_paths = export_seeg_peak_segment(
        seeg_path=args.seeg_path,
        start_sec=args.start_sec,
        end_sec=args.end_sec,
        output_dir=args.output_dir,
        patient_id=args.patient_id,
        peak_metric=args.peak_metric,
        normalization=args.normalization,
        min_peak_distance_ms=args.min_peak_distance_ms,
        atlas_path=args.atlas_path,
    )
    for name, path in output_paths.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
