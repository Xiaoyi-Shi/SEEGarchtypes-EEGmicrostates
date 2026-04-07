from __future__ import annotations

import math

import numpy as np
import pandas as pd

from seeg_eegmicrostates.coupling.exploratory import build_state_transition_table


SUPPORTED_DIRECT_STATE_BACKENDS: tuple[str, ...] = ("pca-kmeans",)


def normalize_direct_state_backend(backend: str) -> str:
    value = str(backend).strip().lower().replace("_", "-")
    aliases = {
        "pca": "pca-kmeans",
        "pca-kmeans": "pca-kmeans",
    }
    normalized = aliases.get(value, value)
    if normalized not in SUPPORTED_DIRECT_STATE_BACKENDS:
        supported = ", ".join(SUPPORTED_DIRECT_STATE_BACKENDS)
        raise ValueError(f"Unsupported direct state backend '{backend}'. Expected one of: {supported}.")
    return normalized


def _region_columns(region_df: pd.DataFrame) -> list[str]:
    return [column for column in region_df.columns if column != "time_sec"]


def _zscore_matrix(matrix: np.ndarray) -> np.ndarray:
    centered = matrix - np.nanmean(matrix, axis=0, keepdims=True)
    scales = np.nanstd(centered, axis=0, ddof=0, keepdims=True)
    scales[~np.isfinite(scales) | (scales == 0.0)] = 1.0
    normalized = centered / scales
    normalized[~np.isfinite(normalized)] = 0.0
    return normalized


def _pca_reduce(matrix: np.ndarray, n_components: int) -> np.ndarray:
    if matrix.size == 0:
        return np.empty((0, 0), dtype=float)
    centered = _zscore_matrix(matrix)
    component_count = max(1, min(int(n_components), centered.shape[0], centered.shape[1]))
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    basis = vt[:component_count].T
    return centered @ basis


def _stable_kmeans(data: np.ndarray, *, n_clusters: int, seed: int, max_iter: int = 50) -> np.ndarray:
    if data.shape[0] == 0:
        return np.empty(0, dtype=int)
    cluster_count = max(1, min(int(n_clusters), data.shape[0]))
    if cluster_count == 1:
        return np.zeros(data.shape[0], dtype=int)
    rng = np.random.default_rng(seed)
    initial = rng.choice(data.shape[0], size=cluster_count, replace=False)
    centroids = data[initial].copy()
    labels = np.zeros(data.shape[0], dtype=int)
    for _ in range(max_iter):
        distances = np.sum((data[:, None, :] - centroids[None, :, :]) ** 2, axis=2)
        labels = np.argmin(distances, axis=1).astype(int)
        updated = centroids.copy()
        for index in range(cluster_count):
            members = data[labels == index]
            if members.size:
                updated[index] = members.mean(axis=0)
            else:
                updated[index] = data[rng.integers(0, data.shape[0])]
        if np.allclose(updated, centroids):
            centroids = updated
            break
        centroids = updated
    sort_keys = tuple(centroids[:, idx] for idx in reversed(range(centroids.shape[1])))
    order = np.lexsort(sort_keys)
    remap = {int(old): int(new) for new, old in enumerate(order.tolist())}
    return np.array([remap[int(label)] for label in labels], dtype=int)


def derive_direct_seeg_state_artifacts(
    region_df: pd.DataFrame,
    *,
    patient_id: str,
    backend: str,
    n_states: int,
    n_components: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    normalized_backend = normalize_direct_state_backend(backend)
    feature_columns = ["patient_id", "time_sec", "sample", "backend", "n_states", "n_components"]
    label_columns = ["patient_id", "time_sec", "sample", "backend", "n_states", "n_components", "seeg_state"]
    if region_df.empty:
        return pd.DataFrame(columns=feature_columns), pd.DataFrame(columns=label_columns)
    region_columns = _region_columns(region_df)
    if not region_columns:
        return pd.DataFrame(columns=feature_columns), pd.DataFrame(columns=label_columns)
    values = region_df[region_columns].to_numpy(dtype=float)
    reduced = _pca_reduce(values, n_components)
    labels = _stable_kmeans(reduced, n_clusters=n_states, seed=seed)
    component_count = int(reduced.shape[1]) if reduced.ndim == 2 and reduced.size else 0
    features = pd.DataFrame(
        {
            "patient_id": patient_id,
            "time_sec": region_df["time_sec"].to_numpy(dtype=float),
            "sample": np.arange(region_df.shape[0], dtype=int),
            "backend": normalized_backend,
            "n_states": int(max(1, min(n_states, region_df.shape[0]))),
            "n_components": component_count,
        }
    )
    for index in range(component_count):
        features[f"component_{index + 1}"] = reduced[:, index]
    state_labels = features.copy()
    state_labels["seeg_state"] = labels
    return features, state_labels[label_columns]


def align_eeg_and_seeg_state_labels(
    eeg_label_df: pd.DataFrame,
    seeg_state_df: pd.DataFrame,
    *,
    patient_id: str,
    tolerance_ms: float = 5.0,
) -> pd.DataFrame:
    if eeg_label_df.empty or seeg_state_df.empty:
        return pd.DataFrame(columns=["patient_id", "time_sec", "microstate", "corr", "seeg_state", "sample"])
    labels = eeg_label_df.sort_values("time_sec")[["time_sec", "microstate", "corr"]].copy()
    aligned = pd.merge_asof(
        labels,
        seeg_state_df.sort_values("time_sec")[["time_sec", "seeg_state", "sample"]].copy(),
        on="time_sec",
        direction="nearest",
        tolerance=tolerance_ms / 1000.0,
    ).dropna(subset=["seeg_state"])
    aligned.insert(0, "patient_id", patient_id)
    aligned["microstate"] = aligned["microstate"].astype(int)
    aligned["seeg_state"] = aligned["seeg_state"].astype(int)
    aligned["sample"] = aligned["sample"].astype(int)
    return aligned.reset_index(drop=True)


def _normalized_mutual_information(left: np.ndarray, right: np.ndarray) -> float:
    if left.size == 0 or right.size == 0 or left.size != right.size:
        return 0.0
    left_codes, _ = pd.factorize(left)
    right_codes, _ = pd.factorize(right)
    contingency = pd.crosstab(left_codes, right_codes).to_numpy(dtype=float)
    total = contingency.sum()
    if total <= 0.0:
        return 0.0
    pxy = contingency / total
    px = pxy.sum(axis=1, keepdims=True)
    py = pxy.sum(axis=0, keepdims=True)
    mask = pxy > 0.0
    with np.errstate(divide="ignore", invalid="ignore"):
        log_term = np.zeros_like(pxy)
        log_term[mask] = np.log(pxy[mask] / (px @ py)[mask])
    mutual_information = float(np.sum(pxy * log_term))
    entropy_left = float(-np.sum(px[px > 0.0] * np.log(px[px > 0.0])))
    entropy_right = float(-np.sum(py[py > 0.0] * np.log(py[py > 0.0])))
    if entropy_left <= 0.0 or entropy_right <= 0.0:
        return 0.0
    return float(mutual_information / math.sqrt(entropy_left * entropy_right))


def _lag_pair(left: np.ndarray, right: np.ndarray, lag_samples: int) -> tuple[np.ndarray, np.ndarray]:
    if lag_samples > 0:
        if lag_samples >= left.size:
            return np.empty(0, dtype=int), np.empty(0, dtype=int)
        return left[:-lag_samples], right[lag_samples:]
    if lag_samples < 0:
        lag = abs(lag_samples)
        if lag >= left.size:
            return np.empty(0, dtype=int), np.empty(0, dtype=int)
        return left[lag:], right[:-lag]
    return left, right


def compute_subject_direct_state_coupling(
    aligned_df: pd.DataFrame,
    *,
    patient_id: str,
    backend: str,
    n_states: int,
    lag_samples: list[int],
    sample_period_sec: float,
    n_surrogates: int,
    seed: int,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "backend",
        "n_states",
        "lag_samples",
        "lag_ms",
        "n_samples",
        "observed_coupling",
        "null_mean_coupling",
        "effect_mean_diff",
        "p_perm",
    ]
    if aligned_df.empty:
        return pd.DataFrame(columns=columns)
    eeg_states = aligned_df["microstate"].to_numpy(dtype=int)
    seeg_states = aligned_df["seeg_state"].to_numpy(dtype=int)
    if eeg_states.size < 2 or seeg_states.size < 2:
        return pd.DataFrame(columns=columns)
    rows: list[dict[str, object]] = []
    rng = np.random.default_rng(seed)
    surrogate_count = max(1, int(n_surrogates))
    max_shift = max(2, seeg_states.size)
    for lag in sorted(set(int(value) for value in lag_samples)):
        left, right = _lag_pair(eeg_states, seeg_states, lag)
        if left.size < 2 or right.size < 2:
            continue
        observed = _normalized_mutual_information(left, right)
        null_values = np.empty(surrogate_count, dtype=float)
        for index in range(surrogate_count):
            offset = int(rng.integers(1, max_shift))
            shifted = np.roll(seeg_states, offset)
            shifted_left, shifted_right = _lag_pair(eeg_states, shifted, lag)
            null_values[index] = _normalized_mutual_information(shifted_left, shifted_right)
        rows.append(
            {
                "patient_id": patient_id,
                "backend": backend,
                "n_states": int(n_states),
                "lag_samples": int(lag),
                "lag_ms": int(round(lag * sample_period_sec * 1000.0)),
                "n_samples": int(left.size),
                "observed_coupling": float(observed),
                "null_mean_coupling": float(null_values.mean()),
                "effect_mean_diff": float(observed - null_values.mean()),
                "p_perm": float((np.sum(null_values >= observed) + 1) / (surrogate_count + 1)),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def compute_subject_transition_state_coupling(
    eeg_transition_df: pd.DataFrame,
    seeg_state_df: pd.DataFrame,
    *,
    patient_id: str,
    backend: str,
    n_states: int,
    window_sec: float,
    n_surrogates: int,
    seed: int,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "backend",
        "n_states",
        "from_state",
        "to_state",
        "n_events",
        "observed_coupling",
        "null_mean_coupling",
        "effect_mean_diff",
        "p_perm",
    ]
    if eeg_transition_df.empty or seeg_state_df.empty:
        return pd.DataFrame(columns=columns)
    seeg_states = seeg_state_df.sort_values("time_sec").reset_index(drop=True)
    renamed = seeg_states.rename(columns={"seeg_state": "microstate"})
    seeg_transitions = build_state_transition_table(renamed[["time_sec", "microstate"]], patient_id=patient_id)
    if seeg_transitions.empty:
        return pd.DataFrame(columns=columns)

    def _match_rate(candidate_transitions: pd.DataFrame) -> dict[tuple[int, int], tuple[int, float]]:
        transition_times = candidate_transitions["event_sec"].to_numpy(dtype=float)
        results: dict[tuple[int, int], tuple[int, float]] = {}
        for keys, group in eeg_transition_df.groupby(["from_state", "to_state"]):
            event_times = group["event_sec"].to_numpy(dtype=float)
            if event_times.size == 0:
                continue
            matches = [
                bool(np.any((transition_times >= event_sec) & (transition_times < event_sec + window_sec)))
                for event_sec in event_times
            ]
            results[(int(keys[0]), int(keys[1]))] = (int(event_times.size), float(np.mean(matches)))
        return results

    observed_rates = _match_rate(seeg_transitions)
    if not observed_rates:
        return pd.DataFrame(columns=columns)

    rng = np.random.default_rng(seed)
    surrogate_count = max(1, int(n_surrogates))
    null_values: dict[tuple[int, int], list[float]] = {key: [] for key in observed_rates}
    labels = seeg_states["seeg_state"].to_numpy(dtype=int)
    max_shift = max(2, labels.size)
    for _ in range(surrogate_count):
        shifted_states = seeg_states.copy()
        shifted_states["seeg_state"] = np.roll(labels, int(rng.integers(1, max_shift)))
        shifted_transitions = build_state_transition_table(
            shifted_states.rename(columns={"seeg_state": "microstate"})[["time_sec", "microstate"]],
            patient_id=patient_id,
        )
        shifted_rates = _match_rate(shifted_transitions)
        for key in null_values:
            null_values[key].append(float(shifted_rates.get(key, (0, 0.0))[1]))

    rows: list[dict[str, object]] = []
    for (from_state, to_state), (n_events, observed_rate) in observed_rates.items():
        surrogate_rates = np.array(null_values[(from_state, to_state)], dtype=float)
        rows.append(
            {
                "patient_id": patient_id,
                "backend": backend,
                "n_states": int(n_states),
                "from_state": int(from_state),
                "to_state": int(to_state),
                "n_events": int(n_events),
                "observed_coupling": float(observed_rate),
                "null_mean_coupling": float(surrogate_rates.mean()),
                "effect_mean_diff": float(observed_rate - surrogate_rates.mean()),
                "p_perm": float((np.sum(surrogate_rates >= observed_rate) + 1) / (surrogate_count + 1)),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def sample_period_from_times(times: np.ndarray) -> float:
    if times.size < 2:
        return 0.0
    return float(np.median(np.diff(times.astype(float))))
