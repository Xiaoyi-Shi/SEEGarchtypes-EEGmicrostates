from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from pycrostates.cluster import ModKMeans
from pycrostates.io import ChData, read_cluster
from pycrostates.preprocessing import extract_gfp_peaks
from scipy.signal import find_peaks

from seeg_eegmicrostates._utils import ensure_directory
from seeg_eegmicrostates.config import AnalysisConfig


def _peak_distance_samples(cfg: AnalysisConfig, sfreq: float) -> int:
    return max(1, int(round(cfg.gfp_min_peak_distance_ms * sfreq / 1000.0)))


def extract_subject_gfp_peaks(raw19, cfg: AnalysisConfig) -> ChData:
    return extract_gfp_peaks(
        raw19,
        picks="all",
        min_peak_distance=_peak_distance_samples(cfg, raw19.info["sfreq"]),
        reject_by_annotation=True,
    )


def build_eeg_gfp_trace(raw19, *, patient_id: str) -> pd.DataFrame:
    data = raw19.get_data(picks="all")
    gfp = np.std(data, axis=0, ddof=0)
    return pd.DataFrame(
        {
            "patient_id": patient_id,
            "time_sec": raw19.times.astype(float),
            "sample": np.arange(raw19.n_times, dtype=int),
            "gfp": gfp.astype(float),
        }
    )


def build_eeg_gfp_peak_table(
    gfp_trace_df: pd.DataFrame,
    cfg: AnalysisConfig,
    *,
    patient_id: str,
    sfreq: float,
) -> pd.DataFrame:
    columns = ["patient_id", "peak_id", "event_sec", "sample", "gfp"]
    if gfp_trace_df.empty:
        return pd.DataFrame(columns=columns)
    peak_indices, _ = find_peaks(
        gfp_trace_df["gfp"].to_numpy(dtype=float),
        distance=_peak_distance_samples(cfg, float(sfreq)),
    )
    if peak_indices.size == 0:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        {
            "patient_id": patient_id,
            "peak_id": np.arange(peak_indices.size, dtype=int),
            "event_sec": gfp_trace_df.iloc[peak_indices]["time_sec"].to_numpy(dtype=float),
            "sample": gfp_trace_df.iloc[peak_indices]["sample"].to_numpy(dtype=int),
            "gfp": gfp_trace_df.iloc[peak_indices]["gfp"].to_numpy(dtype=float),
        }
    )


def _sample_chdata(chdata: ChData, sample_size: int, seed: int) -> ChData:
    data = chdata.get_data()
    n_maps = data.shape[1]
    if n_maps <= sample_size:
        return chdata.copy()
    rng = np.random.default_rng(seed)
    indices = np.sort(rng.choice(n_maps, size=sample_size, replace=False))
    subset = data[:, indices]
    return ChData(subset, chdata.info)


def _concatenate_chdata(instances: list[ChData]) -> ChData:
    if not instances:
        raise ValueError("At least one ChData instance is required for microstate fitting.")
    combined = np.concatenate([instance.get_data() for instance in instances], axis=1)
    return ChData(combined, instances[0].info)


def fit_group_microstate_model(
    preprocessed_raws: dict[str, object],
    cfg: AnalysisConfig,
    *,
    branch: str,
) -> ModKMeans:
    _ = branch
    peak_sets: list[ChData] = []
    for offset, patient_id in enumerate(sorted(preprocessed_raws)):
        peaks = extract_subject_gfp_peaks(preprocessed_raws[patient_id], cfg)
        sampled = _sample_chdata(peaks, cfg.gfp_peak_sample_size, cfg.random_seed + offset)
        peak_sets.append(sampled)
    pooled = _concatenate_chdata(peak_sets)
    estimator = ModKMeans(
        n_clusters=cfg.microstate_k,
        n_init=cfg.microstate_n_init,
        max_iter=cfg.microstate_max_iter,
        random_state=cfg.random_seed,
    )
    estimator.fit(pooled, picks="all")
    return estimator


def save_microstate_model(model: ModKMeans, path: str | Path) -> Path:
    output_path = Path(path)
    ensure_directory(output_path.parent)
    model.save(output_path)
    return output_path


def load_microstate_model(path: str | Path) -> ModKMeans:
    model = read_cluster(Path(path))
    if not isinstance(model, ModKMeans):
        raise TypeError(f"Expected a ModKMeans template file, got {type(model).__name__}.")
    return model


def validate_microstate_model_channels(
    model: ModKMeans,
    expected_channels: tuple[str, ...],
    *,
    alternate_channels: tuple[str, ...] | None = None,
) -> None:
    model_channels = tuple(str(name) for name in model.info["ch_names"])
    allowed_layouts = [tuple(expected_channels)]
    if alternate_channels is not None:
        allowed_layouts.append(tuple(alternate_channels))
    allowed_sets = [set(layout) for layout in allowed_layouts]
    if any(set(model_channels) == allowed for allowed in allowed_sets):
        return
    layout_names = ["restored 19-channel EEG layout"]
    if alternate_channels is not None:
        layout_names.insert(0, "shared 11-channel EEG layout")
    raise ValueError(
        "Template file is incompatible with the allowed EEG template layouts. "
        f"Supported layouts: {', '.join(layout_names)}. "
        f"Found channels: {', '.join(model_channels)}."
    )


def _absolute_correlation_scores(data: np.ndarray, templates: np.ndarray) -> np.ndarray:
    centered_data = data - data.mean(axis=0, keepdims=True)
    centered_templates = templates - templates.mean(axis=1, keepdims=True)
    data_norm = np.linalg.norm(centered_data, axis=0)
    template_norm = np.linalg.norm(centered_templates, axis=1)
    denominator = np.outer(template_norm, data_norm)
    denominator[denominator == 0] = 1.0
    return np.abs(centered_templates @ centered_data / denominator)


def label_microstates(raw19, model: ModKMeans, cfg: AnalysisConfig, *, patient_id: str) -> pd.DataFrame:
    min_samples = max(1, int(round(cfg.min_microstate_duration_ms * raw19.info["sfreq"] / 1000.0)))
    segmentation = model.predict(
        raw19,
        factor=0,
        min_segment_length=min_samples,
        reject_edges=False,
        reject_by_annotation=True,
    )
    labels = segmentation.labels.astype(int)
    data = raw19.get_data(picks=model.info["ch_names"])
    scores = _absolute_correlation_scores(data, model.cluster_centers_)
    confidence = np.full(labels.shape, np.nan, dtype=float)
    valid = labels >= 0
    if np.any(valid):
        indices = np.flatnonzero(valid)
        confidence[indices] = scores[labels[indices], indices]
    return pd.DataFrame(
        {
            "patient_id": patient_id,
            "time_sec": raw19.times.astype(float),
            "sample": np.arange(raw19.n_times, dtype=int),
            "microstate": labels,
            "corr": confidence,
        }
    )
