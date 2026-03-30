from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from pycrostates.cluster import ModKMeans
from pycrostates.io import ChData
from pycrostates.preprocessing import extract_gfp_peaks

from seeg_eegmicrostates._utils import contiguous_runs, ensure_directory
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
) -> dict[str, object]:
    first_patient_id = next(iter(sorted(preprocessed_raws)))
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
    return {
        "branch": branch,
        "channel_names": np.asarray(pooled.info["ch_names"]),
        "cluster_centers": np.asarray(estimator.cluster_centers_),
        "cluster_names": np.asarray(estimator.cluster_names),
        "gev": float(estimator.GEV_),
        "n_clusters": int(cfg.microstate_k),
        "sfreq": float(preprocessed_raws[first_patient_id].info["sfreq"]),
        "random_seed": int(cfg.random_seed),
    }


def save_microstate_model(model: dict[str, object], path: str | Path) -> Path:
    output_path = Path(path)
    ensure_directory(output_path.parent)
    np.savez(output_path, **model)
    return output_path


def load_microstate_model(path: str | Path) -> dict[str, object]:
    with np.load(Path(path), allow_pickle=False) as payload:
        return {key: payload[key] for key in payload.files}


def _absolute_correlation_labels(data: np.ndarray, templates: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    centered_data = data - data.mean(axis=0, keepdims=True)
    centered_templates = templates - templates.mean(axis=1, keepdims=True)
    data_norm = np.linalg.norm(centered_data, axis=0)
    template_norm = np.linalg.norm(centered_templates, axis=1)
    denominator = np.outer(template_norm, data_norm)
    denominator[denominator == 0] = 1.0
    correlations = np.abs(centered_templates @ centered_data / denominator)
    labels = correlations.argmax(axis=0)
    scores = correlations.max(axis=0)
    return labels.astype(int), scores.astype(float)


def smooth_microstate_labels(labels: np.ndarray, min_segment_length: int) -> np.ndarray:
    if min_segment_length <= 1:
        return labels.copy()
    smoothed = labels.copy()
    changed = True
    while changed:
        changed = False
        for start, end, label in contiguous_runs(smoothed):
            run_length = end - start
            if run_length >= min_segment_length:
                continue
            previous_label = smoothed[start - 1] if start > 0 else None
            next_label = smoothed[end] if end < smoothed.size else None
            replacement = None
            if previous_label is not None and next_label is not None and previous_label == next_label:
                replacement = int(previous_label)
            elif previous_label is not None:
                replacement = int(previous_label)
            elif next_label is not None:
                replacement = int(next_label)
            if replacement is not None and replacement != label:
                smoothed[start:end] = replacement
                changed = True
    return smoothed


def label_microstates(raw19, model: dict[str, object], cfg: AnalysisConfig, *, patient_id: str) -> pd.DataFrame:
    templates = np.asarray(model["cluster_centers"], dtype=float)
    data = raw19.get_data(picks="all")
    labels, scores = _absolute_correlation_labels(data, templates)
    min_samples = max(1, int(round(cfg.min_microstate_duration_ms * raw19.info["sfreq"] / 1000.0)))
    smoothed = smooth_microstate_labels(labels, min_samples)
    return pd.DataFrame(
        {
            "patient_id": patient_id,
            "time_sec": raw19.times.astype(float),
            "sample": np.arange(raw19.n_times, dtype=int),
            "microstate": smoothed.astype(int),
            "corr": scores.astype(float),
        }
    )
