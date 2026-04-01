from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.vq import kmeans2
from scipy.signal import find_peaks

from seeg_eegmicrostates._utils import contiguous_runs, ensure_directory, zscore_columns
from seeg_eegmicrostates.config import AnalysisConfig


def compute_band_limited_network_signals(
    raw_bp,
    mapping_df: pd.DataFrame,
    cfg: AnalysisConfig,
    *,
    patient_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    band = raw_bp.copy()
    band.filter(cfg.band_limited_range[0], cfg.band_limited_range[1], verbose="ERROR")
    band.resample(cfg.seeg_resample_hz, verbose="ERROR")
    frame = pd.DataFrame(band.get_data().T, columns=band.ch_names)
    frame.insert(0, "time_sec", band.times.astype(float))
    channel_columns = [column for column in frame.columns if column != "time_sec"]
    frame = zscore_columns(frame, channel_columns)

    from seeg_eegmicrostates.seeg.network import aggregate_channel_dataframe_by_network

    network_df, coverage_df = aggregate_channel_dataframe_by_network(frame, mapping_df, patient_id=patient_id)
    network_columns = [column for column in network_df.columns if column != "time_sec"]
    network_df = zscore_columns(network_df, network_columns)
    return network_df, coverage_df


def _nearest_centroid_labels(data: np.ndarray, centroids: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    centered_data = data - data.mean(axis=0, keepdims=True)
    centered_centroids = centroids - centroids.mean(axis=1, keepdims=True)
    data_norm = np.linalg.norm(centered_data, axis=0)
    centroid_norm = np.linalg.norm(centered_centroids, axis=1)
    denominator = np.outer(centroid_norm, data_norm)
    denominator[denominator == 0] = 1.0
    scores = np.abs(centered_centroids @ centered_data / denominator)
    labels = scores.argmax(axis=0)
    confidence = scores.max(axis=0)
    return labels.astype(int), confidence.astype(float)


def _smooth_labels(labels: np.ndarray, min_segment_length: int) -> np.ndarray:
    if min_segment_length <= 1:
        return labels.copy()
    smoothed = labels.copy()
    changed = True
    while changed:
        changed = False
        for start, end, label in contiguous_runs(smoothed):
            if end - start >= min_segment_length:
                continue
            previous_label = smoothed[start - 1] if start > 0 else None
            next_label = smoothed[end] if end < smoothed.size else None
            replacement = previous_label if previous_label is not None else next_label
            if replacement is not None and replacement != label:
                smoothed[start:end] = replacement
                changed = True
    return smoothed


def fit_network_microstates(
    network_df: pd.DataFrame,
    cfg: AnalysisConfig,
    *,
    patient_id: str,
) -> tuple[dict[str, object], pd.DataFrame]:
    network_columns = [column for column in network_df.columns if column != "time_sec"]
    if not network_columns:
        raise ValueError(f"No valid network columns available for patient {patient_id}.")
    matrix = network_df[network_columns].to_numpy(dtype=float).T
    global_field_power = matrix.std(axis=0)
    min_distance = max(1, int(round(cfg.gfp_min_peak_distance_ms * cfg.seeg_resample_hz / 1000.0)))
    peak_indices, _ = find_peaks(global_field_power, distance=min_distance)
    if peak_indices.size < cfg.microstate_k:
        peak_indices = np.arange(matrix.shape[1], dtype=int)
    rng = np.random.default_rng(cfg.random_seed)
    peak_vectors = matrix[:, peak_indices].T
    centroids, _ = kmeans2(
        peak_vectors,
        cfg.microstate_k,
        iter=cfg.microstate_max_iter,
        minit="points",
        rng=rng,
    )
    labels, confidence = _nearest_centroid_labels(matrix, centroids)
    min_samples = max(1, int(round(cfg.min_microstate_duration_ms * cfg.seeg_resample_hz / 1000.0)))
    labels = _smooth_labels(labels, min_samples)
    model = {
        "patient_id": patient_id,
        "network_names": np.asarray(network_columns),
        "cluster_centers": np.asarray(centroids),
        "n_clusters": int(cfg.microstate_k),
    }
    labels_df = pd.DataFrame(
        {
            "patient_id": patient_id,
            "time_sec": network_df["time_sec"].to_numpy(dtype=float),
            "sample": np.arange(network_df.shape[0], dtype=int),
            "microstate": labels,
            "corr": confidence,
        }
    )
    return model, labels_df


def save_network_microstate_model(model: dict[str, object], path: str | Path) -> Path:
    output_path = Path(path)
    ensure_directory(output_path.parent)
    np.savez(output_path, **model)
    return output_path
