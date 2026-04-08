from __future__ import annotations

from itertools import permutations
import math

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from seeg_eegmicrostates._utils import contiguous_runs
from seeg_eegmicrostates.coupling.exploratory import build_state_transition_table


SUPPORTED_FIELD_STATE_PEAK_METRICS: tuple[str, ...] = ("rms", "spatial-std")
SUPPORTED_FIELD_STATE_NORMALIZATIONS: tuple[str, ...] = ("zscore", "robust-zscore")
SUPPORTED_FIELD_ARCHETYPE_SPACES: tuple[str, ...] = ("yeo17", "aal3")
DEFAULT_FIELD_STATE_PEAK_METRIC = "rms"
DEFAULT_FIELD_STATE_NORMALIZATION = "zscore"
DEFAULT_FIELD_STATE_SURROGATES = 128
DEFAULT_FIELD_STATE_MAX_PEAK_MAPS = 5000
DEFAULT_FINE_FIELD_LAG_WINDOW_MS = 40


def normalize_field_peak_metric(metric: str) -> str:
    value = str(metric).strip().lower().replace("_", "-")
    aliases = {
        "rms": "rms",
        "std": "spatial-std",
        "spatial-std": "spatial-std",
        "spatial-stddev": "spatial-std",
    }
    normalized = aliases.get(value, value)
    if normalized not in SUPPORTED_FIELD_STATE_PEAK_METRICS:
        supported = ", ".join(SUPPORTED_FIELD_STATE_PEAK_METRICS)
        raise ValueError(f"Unsupported SEEG field-state peak metric '{metric}'. Expected one of: {supported}.")
    return normalized


def normalize_field_normalization(strategy: str) -> str:
    value = str(strategy).strip().lower().replace("_", "-")
    aliases = {
        "zscore": "zscore",
        "z": "zscore",
        "robust-zscore": "robust-zscore",
        "robust": "robust-zscore",
        "mad-zscore": "robust-zscore",
    }
    normalized = aliases.get(value, value)
    if normalized not in SUPPORTED_FIELD_STATE_NORMALIZATIONS:
        supported = ", ".join(SUPPORTED_FIELD_STATE_NORMALIZATIONS)
        raise ValueError(f"Unsupported SEEG field-state normalization '{strategy}'. Expected one of: {supported}.")
    return normalized


def normalize_field_archetype_space(space: str) -> str:
    value = str(space).strip().lower().replace("_", "-")
    aliases = {
        "yeo17": "yeo17",
        "yeo-17": "yeo17",
        "aal3": "aal3",
        "aal-3": "aal3",
        "aal": "aal3",
    }
    normalized = aliases.get(value, value)
    if normalized not in SUPPORTED_FIELD_ARCHETYPE_SPACES:
        supported = ", ".join(SUPPORTED_FIELD_ARCHETYPE_SPACES)
        raise ValueError(f"Unsupported SEEG field-state archetype space '{space}'. Expected one of: {supported}.")
    return normalized


def _channel_columns(channel_df: pd.DataFrame) -> list[str]:
    return [column for column in channel_df.columns if column != "time_sec"]


def _field_template_channel_columns(template_df: pd.DataFrame) -> list[str]:
    metadata_columns = {
        "patient_id",
        "field_state",
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
    return [column for column in template_df.columns if column not in metadata_columns]


def _robust_mad(values: np.ndarray, axis: int, keepdims: bool) -> np.ndarray:
    median = np.nanmedian(values, axis=axis, keepdims=True)
    mad = np.nanmedian(np.abs(values - median), axis=axis, keepdims=keepdims)
    return 1.4826 * mad


def _normalize_channels(matrix: np.ndarray, strategy: str) -> np.ndarray:
    normalized_strategy = normalize_field_normalization(strategy)
    if matrix.size == 0:
        return np.empty_like(matrix, dtype=float)
    if normalized_strategy == "robust-zscore":
        centers = np.nanmedian(matrix, axis=0, keepdims=True)
        scales = _robust_mad(matrix, axis=0, keepdims=True)
    else:
        centers = np.nanmean(matrix, axis=0, keepdims=True)
        scales = np.nanstd(matrix, axis=0, ddof=0, keepdims=True)
    scales = np.asarray(scales, dtype=float)
    scales[~np.isfinite(scales) | (scales == 0.0)] = 1.0
    normalized = (matrix - centers) / scales
    normalized[~np.isfinite(normalized)] = 0.0
    return normalized


def _map_patterns(matrix: np.ndarray) -> np.ndarray:
    if matrix.size == 0:
        return np.empty_like(matrix, dtype=float)
    centered = matrix - np.mean(matrix, axis=1, keepdims=True)
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    norms[~np.isfinite(norms) | (norms == 0.0)] = 1.0
    patterns = centered / norms
    patterns[~np.isfinite(patterns)] = 0.0
    return patterns


def _compute_peak_metric(matrix: np.ndarray, metric: str) -> np.ndarray:
    normalized_metric = normalize_field_peak_metric(metric)
    if matrix.size == 0:
        return np.empty(0, dtype=float)
    if normalized_metric == "spatial-std":
        return np.std(matrix, axis=1, ddof=0)
    return np.sqrt(np.mean(matrix**2, axis=1))


def _sample_period_sec(times: np.ndarray) -> float:
    if times.size < 2:
        return 0.0
    return float(np.median(np.diff(times.astype(float))))


def _peak_distance_samples(sample_period_sec: float, min_peak_distance_ms: int) -> int:
    if sample_period_sec <= 0.0:
        return 1
    return max(1, int(round(float(min_peak_distance_ms) / 1000.0 / sample_period_sec)))


def _absolute_similarity(patterns: np.ndarray, templates: np.ndarray) -> np.ndarray:
    if patterns.size == 0 or templates.size == 0:
        return np.empty((patterns.shape[0], templates.shape[0]), dtype=float)
    return np.abs(patterns @ templates.T)


def _orient_pattern(pattern: np.ndarray) -> tuple[np.ndarray, float]:
    values = np.asarray(pattern, dtype=float)
    if values.size == 0:
        return values.astype(float), 1.0
    finite = np.isfinite(values)
    if not finite.any():
        return np.zeros_like(values, dtype=float), 1.0
    working = values.copy()
    working[~finite] = 0.0
    dominant_index = int(np.argmax(np.abs(working)))
    sign = -1.0 if working[dominant_index] < 0.0 else 1.0
    return working * sign, sign


def project_field_state_templates_to_common_space(
    template_df: pd.DataFrame,
    mapping_df: pd.DataFrame,
    *,
    patient_id: str,
    comparison_space: str,
) -> pd.DataFrame:
    normalized_space = normalize_field_archetype_space(comparison_space)
    columns = [
        "patient_id",
        "field_state",
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
    ]
    if template_df.empty or mapping_df.empty:
        return pd.DataFrame(columns=columns)
    channel_columns = _field_template_channel_columns(template_df)
    valid_mapping = mapping_df[mapping_df["valid_same_region"]].copy()
    valid_mapping = valid_mapping[valid_mapping["bipolar_channel"].isin(channel_columns)]
    if valid_mapping.empty:
        return pd.DataFrame(columns=columns)
    rows: list[dict[str, object]] = []
    common_units = sorted(valid_mapping["region"].dropna().astype(str).unique().tolist())
    for row_values in template_df.to_dict(orient="records"):
        projected_row: dict[str, object] = {
            "patient_id": patient_id,
            "field_state": int(row_values["field_state"]),
            "peak_metric": str(row_values["peak_metric"]),
            "normalization": str(row_values["normalization"]),
            "n_states": int(row_values["n_states"]),
            "min_duration_ms": int(row_values["min_duration_ms"]),
            "n_channels": int(row_values["n_channels"]),
            "n_peak_maps": int(row_values["n_peak_maps"]),
            "comparison_space": normalized_space,
            "orientation_sign": 1.0,
            "n_mapped_channels": int(valid_mapping.shape[0]),
            "n_common_units": int(len(common_units)),
        }
        vector = np.full(len(common_units), np.nan, dtype=float)
        for index, unit in enumerate(common_units):
            channels = valid_mapping.loc[valid_mapping["region"].astype(str) == unit, "bipolar_channel"].astype(str).tolist()
            if not channels:
                continue
            values = np.asarray([float(row_values[channel]) for channel in channels], dtype=float)
            vector[index] = float(np.nanmean(values)) if np.isfinite(values).any() else np.nan
        filled = np.nan_to_num(vector, nan=0.0)
        oriented, sign = _orient_pattern(_map_patterns(filled[None, :])[0])
        projected_row["orientation_sign"] = float(sign)
        for index, unit in enumerate(common_units):
            projected_row[unit] = float(oriented[index])
        rows.append(projected_row)
    return pd.DataFrame(rows, columns=[*columns, *common_units])


def _best_unique_archetype_assignment(similarity: np.ndarray) -> np.ndarray:
    if similarity.ndim != 2 or similarity.size == 0:
        return np.empty(0, dtype=int)
    n_rows, n_cols = similarity.shape
    if n_rows == 1:
        return np.array([int(np.argmax(similarity[0]))], dtype=int)
    if n_rows <= n_cols and n_cols <= 8:
        best_score = float("-inf")
        best_assignment: tuple[int, ...] | None = None
        for candidate in permutations(range(n_cols), n_rows):
            score = float(sum(similarity[row_index, column_index] for row_index, column_index in enumerate(candidate)))
            if score > best_score:
                best_score = score
                best_assignment = tuple(int(item) for item in candidate)
        if best_assignment is not None:
            return np.asarray(best_assignment, dtype=int)
    used: set[int] = set()
    assignment = np.full(n_rows, -1, dtype=int)
    row_order = np.argsort(-np.max(similarity, axis=1))
    for row_index in row_order:
        for column_index in np.argsort(-similarity[row_index]):
            candidate = int(column_index)
            if candidate in used:
                continue
            assignment[row_index] = candidate
            used.add(candidate)
            break
        if assignment[row_index] < 0:
            assignment[row_index] = int(np.argmax(similarity[row_index]))
    return assignment


def derive_group_field_state_archetypes(
    projection_df: pd.DataFrame,
    *,
    comparison_space: str,
    n_states: int,
    seed: int,
    min_subjects: int,
) -> dict[str, pd.DataFrame]:
    normalized_space = normalize_field_archetype_space(comparison_space)
    projection_columns = [
        "patient_id",
        "field_state",
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
    ]
    assignment_columns = [
        "patient_id",
        "field_state",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "comparison_space",
        "assigned_archetype",
        "assignment_similarity",
        "orientation_sign",
    ]
    support_columns = [
        "comparison_space",
        "field_state",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "n_subjects",
        "n_state_assignments",
        "mean_similarity",
        "median_similarity",
        "min_similarity",
    ]
    if projection_df.empty:
        return {
            "projections": pd.DataFrame(columns=projection_columns),
            "assignments": pd.DataFrame(columns=assignment_columns),
            "archetypes": pd.DataFrame(columns=projection_columns),
            "support": pd.DataFrame(columns=support_columns),
        }
    data = projection_df.copy()
    common_columns = _field_template_channel_columns(data)
    if not common_columns:
        empty_projection = pd.DataFrame(columns=projection_columns)
        return {
            "projections": empty_projection,
            "assignments": pd.DataFrame(columns=assignment_columns),
            "archetypes": pd.DataFrame(columns=projection_columns),
            "support": pd.DataFrame(columns=support_columns),
        }
    matrix = data[common_columns].fillna(0.0).to_numpy(dtype=float)
    oriented_patterns = np.empty_like(matrix, dtype=float)
    orientation_signs = np.ones(matrix.shape[0], dtype=float)
    for index, pattern in enumerate(matrix):
        oriented, sign = _orient_pattern(_map_patterns(pattern[None, :])[0])
        oriented_patterns[index] = oriented
        orientation_signs[index] = sign
    data["comparison_space"] = normalized_space
    data["orientation_sign"] = orientation_signs
    for index, column in enumerate(common_columns):
        data[column] = oriented_patterns[:, index]
    archetype_templates, _, _ = _stable_field_state_templates(oriented_patterns, n_states=n_states, seed=seed)
    if archetype_templates.size == 0:
        empty_archetypes = pd.DataFrame(columns=projection_columns)
        return {
            "projections": data,
            "assignments": pd.DataFrame(columns=assignment_columns),
            "archetypes": empty_archetypes,
            "support": pd.DataFrame(columns=support_columns),
        }
    assignment_rows: list[dict[str, object]] = []
    assigned_patterns: dict[int, list[np.ndarray]] = {index: [] for index in range(archetype_templates.shape[0])}
    assigned_similarities: dict[int, list[float]] = {index: [] for index in range(archetype_templates.shape[0])}
    assigned_subjects: dict[int, set[str]] = {index: set() for index in range(archetype_templates.shape[0])}
    for patient_id, group in data.groupby("patient_id", sort=True):
        patient_matrix = group[common_columns].fillna(0.0).to_numpy(dtype=float)
        similarity = _absolute_similarity(patient_matrix, archetype_templates)
        assignment = _best_unique_archetype_assignment(similarity)
        for row_index, (_, source_row) in enumerate(group.reset_index(drop=True).iterrows()):
            archetype_index = int(assignment[row_index])
            assignment_similarity = float(similarity[row_index, archetype_index])
            assignment_rows.append(
                {
                    "patient_id": str(patient_id),
                    "field_state": int(source_row["field_state"]),
                    "peak_metric": str(source_row["peak_metric"]),
                    "normalization": str(source_row["normalization"]),
                    "n_states": int(source_row["n_states"]),
                    "min_duration_ms": int(source_row["min_duration_ms"]),
                    "comparison_space": normalized_space,
                    "assigned_archetype": archetype_index,
                    "assignment_similarity": assignment_similarity,
                    "orientation_sign": float(source_row["orientation_sign"]),
                }
            )
            assigned_patterns[archetype_index].append(patient_matrix[row_index])
            assigned_similarities[archetype_index].append(assignment_similarity)
            assigned_subjects[archetype_index].add(str(patient_id))
    recomputed_templates = archetype_templates.copy()
    for archetype_index in range(recomputed_templates.shape[0]):
        members = assigned_patterns[archetype_index]
        if not members:
            continue
        recomputed_templates[archetype_index] = _map_patterns(np.mean(np.vstack(members), axis=0, keepdims=True))[0]
    assignment_df = pd.DataFrame(assignment_rows, columns=assignment_columns)
    archetype_rows: list[dict[str, object]] = []
    support_rows: list[dict[str, object]] = []
    reference = data.iloc[0]
    for archetype_index in range(recomputed_templates.shape[0]):
        n_subjects = int(len(assigned_subjects[archetype_index]))
        similarities = np.asarray(assigned_similarities[archetype_index], dtype=float)
        if n_subjects < int(min_subjects):
            continue
        archetype_row: dict[str, object] = {
            "patient_id": normalized_space,
            "field_state": int(archetype_index),
            "peak_metric": str(reference["peak_metric"]),
            "normalization": str(reference["normalization"]),
            "n_states": int(reference["n_states"]),
            "min_duration_ms": int(reference["min_duration_ms"]),
            "n_channels": int(len(common_columns)),
            "n_peak_maps": int(len(assigned_patterns[archetype_index])),
            "comparison_space": normalized_space,
            "orientation_sign": 1.0,
            "n_mapped_channels": int(reference["n_mapped_channels"]),
            "n_common_units": int(len(common_columns)),
        }
        for index, column in enumerate(common_columns):
            archetype_row[column] = float(recomputed_templates[archetype_index, index])
        archetype_rows.append(archetype_row)
        support_rows.append(
            {
                "comparison_space": normalized_space,
                "field_state": int(archetype_index),
                "peak_metric": str(reference["peak_metric"]),
                "normalization": str(reference["normalization"]),
                "n_states": int(reference["n_states"]),
                "min_duration_ms": int(reference["min_duration_ms"]),
                "n_subjects": n_subjects,
                "n_state_assignments": int(len(assigned_patterns[archetype_index])),
                "mean_similarity": float(similarities.mean()) if similarities.size else 0.0,
                "median_similarity": float(np.median(similarities)) if similarities.size else 0.0,
                "min_similarity": float(similarities.min()) if similarities.size else 0.0,
            }
        )
    archetype_df = pd.DataFrame(archetype_rows, columns=[*projection_columns, *common_columns])
    support_df = pd.DataFrame(support_rows, columns=support_columns)
    return {
        "projections": data[[*projection_columns, *common_columns]].reset_index(drop=True),
        "assignments": assignment_df.reset_index(drop=True),
        "archetypes": archetype_df.reset_index(drop=True),
        "support": support_df.reset_index(drop=True),
    }


def _stable_field_state_templates(
    peak_patterns: np.ndarray,
    *,
    n_states: int,
    seed: int,
    max_iter: int = 50,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if peak_patterns.shape[0] == 0:
        return (
            np.empty((0, peak_patterns.shape[1] if peak_patterns.ndim == 2 else 0), dtype=float),
            np.empty(0, dtype=int),
            np.empty(0, dtype=float),
        )
    cluster_count = max(1, min(int(n_states), int(peak_patterns.shape[0])))
    if cluster_count == 1:
        template = _map_patterns(np.mean(peak_patterns, axis=0, keepdims=True))
        scores = _absolute_similarity(peak_patterns, template)
        return template, np.zeros(peak_patterns.shape[0], dtype=int), scores[:, 0]
    rng = np.random.default_rng(seed)
    initial_indices = rng.choice(peak_patterns.shape[0], size=cluster_count, replace=False)
    templates = peak_patterns[initial_indices].copy()
    labels = np.zeros(peak_patterns.shape[0], dtype=int)
    scores = np.zeros(peak_patterns.shape[0], dtype=float)
    for _ in range(max_iter):
        similarity = _absolute_similarity(peak_patterns, templates)
        updated_labels = np.argmax(similarity, axis=1).astype(int)
        updated_templates = templates.copy()
        for state in range(cluster_count):
            members = peak_patterns[updated_labels == state]
            if members.size == 0:
                updated_templates[state] = peak_patterns[int(rng.integers(0, peak_patterns.shape[0]))]
                continue
            signs = np.sign(members @ templates[state])
            signs[signs == 0.0] = 1.0
            aligned = members * signs[:, None]
            updated_templates[state] = _map_patterns(aligned.mean(axis=0, keepdims=True))[0]
        if np.array_equal(updated_labels, labels) and np.allclose(updated_templates, templates):
            templates = updated_templates
            labels = updated_labels
            scores = similarity[np.arange(similarity.shape[0]), labels]
            break
        templates = updated_templates
        labels = updated_labels
        scores = similarity[np.arange(similarity.shape[0]), labels]
    sort_keys = tuple(templates[:, index] for index in reversed(range(templates.shape[1])))
    order = np.lexsort(sort_keys)
    remap = {int(old): int(new) for new, old in enumerate(order.tolist())}
    ordered_templates = templates[order]
    ordered_labels = np.array([remap[int(label)] for label in labels], dtype=int)
    ordered_scores = _absolute_similarity(peak_patterns, ordered_templates)[np.arange(peak_patterns.shape[0]), ordered_labels]
    return ordered_templates, ordered_labels, ordered_scores


def _smooth_short_runs(labels: np.ndarray, scores: np.ndarray, min_samples: int) -> np.ndarray:
    if labels.size == 0 or min_samples <= 1:
        return labels
    smoothed = labels.copy()
    while True:
        changed = False
        runs = contiguous_runs(smoothed)
        if len(runs) <= 1:
            return smoothed
        for index, (start, end, label) in enumerate(runs):
            if end - start >= min_samples:
                continue
            previous_label = int(runs[index - 1][2]) if index > 0 else None
            next_label = int(runs[index + 1][2]) if index < len(runs) - 1 else None
            replacement: int | None = None
            if previous_label is not None and next_label is not None and previous_label == next_label:
                replacement = previous_label
            else:
                candidates = [candidate for candidate in (previous_label, next_label) if candidate is not None]
                if candidates:
                    replacement = max(candidates, key=lambda candidate: float(scores[start:end, int(candidate)].mean()))
            if replacement is None or replacement == label:
                continue
            smoothed[start:end] = int(replacement)
            changed = True
            break
        if not changed:
            return smoothed


def build_seeg_field_metric_trace(
    channel_df: pd.DataFrame,
    *,
    patient_id: str,
    peak_metric: str,
    normalization: str,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "time_sec",
        "sample",
        "peak_metric_value",
        "peak_metric",
        "normalization",
        "n_channels_used",
    ]
    if channel_df.empty:
        return pd.DataFrame(columns=columns)
    channels = _channel_columns(channel_df)
    if len(channels) < 2:
        return pd.DataFrame(columns=columns)
    values = channel_df[channels].to_numpy(dtype=float)
    valid = np.isfinite(values).any(axis=0) & (np.nanstd(values, axis=0, ddof=0) > 0.0)
    if int(valid.sum()) < 2:
        return pd.DataFrame(columns=columns)
    normalized_values = _normalize_channels(values[:, valid], normalization)
    metric_values = _compute_peak_metric(normalized_values, peak_metric)
    return pd.DataFrame(
        {
            "patient_id": patient_id,
            "time_sec": channel_df["time_sec"].to_numpy(dtype=float),
            "sample": np.arange(channel_df.shape[0], dtype=int),
            "peak_metric_value": metric_values.astype(float),
            "peak_metric": normalize_field_peak_metric(peak_metric),
            "normalization": normalize_field_normalization(normalization),
            "n_channels_used": int(valid.sum()),
        },
        columns=columns,
    )


def build_seeg_field_peak_table(
    trace_df: pd.DataFrame,
    *,
    patient_id: str,
    min_peak_distance_ms: int,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "peak_id",
        "event_sec",
        "sample",
        "peak_metric_value",
        "peak_metric",
        "normalization",
        "n_channels_used",
    ]
    if trace_df.empty:
        return pd.DataFrame(columns=columns)
    sample_period = _sample_period_sec(trace_df["time_sec"].to_numpy(dtype=float))
    peak_indices, _ = find_peaks(
        trace_df["peak_metric_value"].to_numpy(dtype=float),
        distance=_peak_distance_samples(sample_period, min_peak_distance_ms),
    )
    if peak_indices.size == 0:
        return pd.DataFrame(columns=columns)
    selected = trace_df.iloc[peak_indices]
    return pd.DataFrame(
        {
            "patient_id": patient_id,
            "peak_id": np.arange(peak_indices.size, dtype=int),
            "event_sec": selected["time_sec"].to_numpy(dtype=float),
            "sample": selected["sample"].to_numpy(dtype=int),
            "peak_metric_value": selected["peak_metric_value"].to_numpy(dtype=float),
            "peak_metric": selected["peak_metric"].to_numpy(dtype=str),
            "normalization": selected["normalization"].to_numpy(dtype=str),
            "n_channels_used": selected["n_channels_used"].to_numpy(dtype=int),
        },
        columns=columns,
    )


def _field_state_profile_rows(
    labels: np.ndarray,
    *,
    patient_id: str,
    peak_metric: str,
    normalization: str,
    n_states: int,
    min_duration_ms: int,
    sample_period_sec: float,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "field_state",
        "occupancy",
        "mean_dwell_sec",
        "n_samples",
        "n_runs",
    ]
    if labels.size == 0:
        return pd.DataFrame(columns=columns)
    runs = contiguous_runs(labels.astype(int))
    rows: list[dict[str, object]] = []
    for field_state in sorted(set(labels.astype(int).tolist())):
        dwell_lengths = [end - start for start, end, label in runs if int(label) == int(field_state)]
        rows.append(
            {
                "patient_id": patient_id,
                "peak_metric": peak_metric,
                "normalization": normalization,
                "n_states": int(n_states),
                "min_duration_ms": int(min_duration_ms),
                "field_state": int(field_state),
                "occupancy": float(np.mean(labels == field_state)),
                "mean_dwell_sec": float(np.mean(dwell_lengths) * sample_period_sec) if dwell_lengths else 0.0,
                "n_samples": int(np.sum(labels == field_state)),
                "n_runs": int(len(dwell_lengths)),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def _field_state_transition_rows(
    label_df: pd.DataFrame,
    *,
    patient_id: str,
    peak_metric: str,
    normalization: str,
    n_states: int,
    min_duration_ms: int,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "from_state",
        "to_state",
        "n_transitions",
        "transition_probability",
    ]
    if label_df.empty:
        return pd.DataFrame(columns=columns)
    transitions = build_state_transition_table(
        label_df.rename(columns={"field_state": "microstate"})[["time_sec", "microstate"]],
        patient_id=patient_id,
    )
    if transitions.empty:
        return pd.DataFrame(columns=columns)
    source_counts = transitions.groupby("from_state").size()
    rows: list[dict[str, object]] = []
    for (from_state, to_state), group in transitions.groupby(["from_state", "to_state"]):
        total = int(source_counts.loc[int(from_state)])
        rows.append(
            {
                "patient_id": patient_id,
                "peak_metric": peak_metric,
                "normalization": normalization,
                "n_states": int(n_states),
                "min_duration_ms": int(min_duration_ms),
                "from_state": int(from_state),
                "to_state": int(to_state),
                "n_transitions": int(group.shape[0]),
                "transition_probability": float(group.shape[0] / total) if total else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def derive_seeg_field_state_artifacts(
    channel_df: pd.DataFrame,
    *,
    patient_id: str,
    peak_metric: str,
    normalization: str,
    n_states: int,
    min_duration_ms: int,
    min_peak_distance_ms: int,
    seed: int,
    max_peak_maps: int = DEFAULT_FIELD_STATE_MAX_PEAK_MAPS,
) -> dict[str, pd.DataFrame]:
    normalized_metric = normalize_field_peak_metric(peak_metric)
    normalized_strategy = normalize_field_normalization(normalization)
    trace_columns = [
        "patient_id",
        "time_sec",
        "sample",
        "peak_metric_value",
        "peak_metric",
        "normalization",
        "n_channels_used",
    ]
    peak_columns = [
        "patient_id",
        "peak_id",
        "event_sec",
        "sample",
        "peak_metric_value",
        "peak_metric",
        "normalization",
        "n_channels_used",
    ]
    peak_map_columns = [
        "patient_id",
        "peak_id",
        "event_sec",
        "sample",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "peak_metric_value",
        "field_state",
        "corr",
    ]
    label_columns = [
        "patient_id",
        "time_sec",
        "sample",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "field_state",
        "corr",
    ]
    template_columns = [
        "patient_id",
        "field_state",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "n_channels",
        "n_peak_maps",
    ]
    empty = {
        "trace": pd.DataFrame(columns=trace_columns),
        "peaks": pd.DataFrame(columns=peak_columns),
        "peak_maps": pd.DataFrame(columns=peak_map_columns),
        "templates": pd.DataFrame(columns=template_columns),
        "labels": pd.DataFrame(columns=label_columns),
        "profiles": pd.DataFrame(
            columns=["patient_id", "peak_metric", "normalization", "n_states", "min_duration_ms", "field_state", "occupancy", "mean_dwell_sec", "n_samples", "n_runs"]
        ),
        "transition_profiles": pd.DataFrame(
            columns=["patient_id", "peak_metric", "normalization", "n_states", "min_duration_ms", "from_state", "to_state", "n_transitions", "transition_probability"]
        ),
    }
    if channel_df.empty:
        return empty
    channels = _channel_columns(channel_df)
    if len(channels) < 2:
        return empty
    values = channel_df[channels].to_numpy(dtype=float)
    valid = np.isfinite(values).any(axis=0) & (np.nanstd(values, axis=0, ddof=0) > 0.0)
    selected_channels = [channel for channel, is_valid in zip(channels, valid, strict=False) if is_valid]
    if len(selected_channels) < 2:
        return empty
    normalized_values = _normalize_channels(values[:, valid], normalized_strategy)
    patterns = _map_patterns(normalized_values)
    times = channel_df["time_sec"].to_numpy(dtype=float)
    sample_period_sec = _sample_period_sec(times)
    normalized_df = pd.DataFrame({"time_sec": times})
    for index, channel in enumerate(selected_channels):
        normalized_df[channel] = normalized_values[:, index]
    trace_df = build_seeg_field_metric_trace(
        normalized_df,
        patient_id=patient_id,
        peak_metric=normalized_metric,
        normalization=normalized_strategy,
    )
    peak_df = build_seeg_field_peak_table(
        trace_df,
        patient_id=patient_id,
        min_peak_distance_ms=min_peak_distance_ms,
    )
    if peak_df.empty:
        return {**empty, "trace": trace_df, "peaks": peak_df}

    peak_indices = peak_df["sample"].to_numpy(dtype=int)
    if peak_indices.size > max(1, int(max_peak_maps)):
        rng = np.random.default_rng(seed)
        sampled_order = np.sort(rng.choice(peak_indices.size, size=int(max_peak_maps), replace=False))
        peak_df = peak_df.iloc[sampled_order].reset_index(drop=True)
        peak_df["peak_id"] = np.arange(peak_df.shape[0], dtype=int)
        peak_indices = peak_df["sample"].to_numpy(dtype=int)
    peak_patterns = patterns[peak_indices]
    templates, peak_labels, peak_scores = _stable_field_state_templates(
        peak_patterns,
        n_states=n_states,
        seed=seed,
    )
    similarity = _absolute_similarity(patterns, templates)
    continuous_labels = np.argmax(similarity, axis=1).astype(int)
    min_samples = _peak_distance_samples(sample_period_sec, int(min_duration_ms))
    smoothed_labels = _smooth_short_runs(continuous_labels, similarity, min_samples)
    smoothed_scores = similarity[np.arange(similarity.shape[0]), smoothed_labels]
    resolved_states = int(templates.shape[0]) if templates.size else 0

    peak_maps_df = peak_df.copy()
    peak_maps_df["peak_metric"] = normalized_metric
    peak_maps_df["normalization"] = normalized_strategy
    peak_maps_df["n_states"] = int(resolved_states)
    peak_maps_df["min_duration_ms"] = int(min_duration_ms)
    for index, channel in enumerate(selected_channels):
        peak_maps_df[channel] = peak_patterns[:, index]
    peak_maps_df["field_state"] = peak_labels.astype(int)
    peak_maps_df["corr"] = peak_scores.astype(float)

    template_rows: list[dict[str, object]] = []
    for field_state in range(resolved_states):
        row: dict[str, object] = {
            "patient_id": patient_id,
            "field_state": int(field_state),
            "peak_metric": normalized_metric,
            "normalization": normalized_strategy,
            "n_states": int(resolved_states),
            "min_duration_ms": int(min_duration_ms),
            "n_channels": int(len(selected_channels)),
            "n_peak_maps": int(np.sum(peak_labels == field_state)),
        }
        for index, channel in enumerate(selected_channels):
            row[channel] = float(templates[field_state, index])
        template_rows.append(row)
    template_df = pd.DataFrame(template_rows)

    label_df = pd.DataFrame(
        {
            "patient_id": patient_id,
            "time_sec": times,
            "sample": np.arange(times.size, dtype=int),
            "peak_metric": normalized_metric,
            "normalization": normalized_strategy,
            "n_states": int(resolved_states),
            "min_duration_ms": int(min_duration_ms),
            "field_state": smoothed_labels.astype(int),
            "corr": smoothed_scores.astype(float),
        }
    )
    profile_df = _field_state_profile_rows(
        smoothed_labels,
        patient_id=patient_id,
        peak_metric=normalized_metric,
        normalization=normalized_strategy,
        n_states=resolved_states,
        min_duration_ms=min_duration_ms,
        sample_period_sec=sample_period_sec,
    )
    transition_profile_df = _field_state_transition_rows(
        label_df[["time_sec", "field_state"]].copy(),
        patient_id=patient_id,
        peak_metric=normalized_metric,
        normalization=normalized_strategy,
        n_states=resolved_states,
        min_duration_ms=min_duration_ms,
    )
    return {
        "trace": trace_df,
        "peaks": peak_df,
        "peak_maps": peak_maps_df,
        "templates": template_df,
        "labels": label_df,
        "profiles": profile_df,
        "transition_profiles": transition_profile_df,
    }


def align_eeg_and_field_state_labels(
    eeg_label_df: pd.DataFrame,
    field_label_df: pd.DataFrame,
    *,
    patient_id: str,
    tolerance_ms: float = 5.0,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "time_sec",
        "microstate",
        "corr",
        "field_state",
        "field_corr",
        "sample",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
    ]
    if eeg_label_df.empty or field_label_df.empty:
        return pd.DataFrame(columns=columns)
    labels = eeg_label_df.sort_values("time_sec")[["time_sec", "microstate", "corr"]].copy()
    aligned = pd.merge_asof(
        labels,
        field_label_df.sort_values("time_sec")[["time_sec", "field_state", "corr", "sample", "peak_metric", "normalization", "n_states", "min_duration_ms"]]
        .rename(columns={"corr": "field_corr"})
        .copy(),
        on="time_sec",
        direction="nearest",
        tolerance=tolerance_ms / 1000.0,
    ).dropna(subset=["field_state"])
    aligned.insert(0, "patient_id", patient_id)
    aligned["microstate"] = aligned["microstate"].astype(int)
    aligned["field_state"] = aligned["field_state"].astype(int)
    aligned["sample"] = aligned["sample"].astype(int)
    aligned["n_states"] = aligned["n_states"].astype(int)
    aligned["min_duration_ms"] = aligned["min_duration_ms"].astype(int)
    return aligned.reset_index(drop=True)


def align_eeg_gfp_and_field_state_labels(
    eeg_label_df: pd.DataFrame,
    gfp_trace_df: pd.DataFrame,
    field_label_df: pd.DataFrame,
    *,
    patient_id: str,
    tolerance_ms: float = 5.0,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "time_sec",
        "sample",
        "microstate",
        "corr",
        "gfp",
        "field_state",
        "field_corr",
        "switch_indicator",
        "field_switch_indicator",
        "eeg_switch_indicator",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
    ]
    if eeg_label_df.empty or gfp_trace_df.empty or field_label_df.empty:
        return pd.DataFrame(columns=columns)
    gfp_aligned = pd.merge_asof(
        eeg_label_df.sort_values("time_sec")[["time_sec", "sample", "microstate", "corr"]].copy(),
        gfp_trace_df.sort_values("time_sec")[["time_sec", "gfp"]].copy(),
        on="time_sec",
        direction="nearest",
        tolerance=tolerance_ms / 1000.0,
    )
    aligned = pd.merge_asof(
        gfp_aligned,
        field_label_df.sort_values("time_sec")[["time_sec", "field_state", "corr", "peak_metric", "normalization", "n_states", "min_duration_ms"]]
        .rename(columns={"corr": "field_corr"})
        .copy(),
        on="time_sec",
        direction="nearest",
        tolerance=tolerance_ms / 1000.0,
    ).dropna(subset=["gfp", "field_state"])
    aligned.insert(0, "patient_id", patient_id)
    aligned["sample"] = aligned["sample"].astype(int)
    aligned["microstate"] = aligned["microstate"].astype(int)
    aligned["field_state"] = aligned["field_state"].astype(int)
    aligned["n_states"] = aligned["n_states"].astype(int)
    aligned["min_duration_ms"] = aligned["min_duration_ms"].astype(int)
    aligned = aligned.sort_values("time_sec").reset_index(drop=True)
    aligned["field_switch_indicator"] = (aligned["field_state"].diff().fillna(0) != 0).astype(float)
    aligned["eeg_switch_indicator"] = (aligned["microstate"].diff().fillna(0) != 0).astype(float)
    aligned["switch_indicator"] = aligned["field_switch_indicator"]
    if not aligned.empty:
        aligned.loc[0, "field_switch_indicator"] = 0.0
        aligned.loc[0, "eeg_switch_indicator"] = 0.0
        aligned.loc[0, "switch_indicator"] = 0.0
    return aligned[columns]


def build_eeg_topography_trace(raw19, *, patient_id: str) -> pd.DataFrame:
    channels = [str(name) for name in raw19.ch_names]
    columns = ["patient_id", "time_sec", "sample", *channels]
    if raw19.n_times == 0 or not channels:
        return pd.DataFrame(columns=columns)
    data = raw19.get_data(picks="all").T.astype(float)
    normalized = _map_patterns(data)
    oriented = np.empty_like(normalized)
    for index in range(normalized.shape[0]):
        oriented[index], _ = _orient_pattern(normalized[index])
    trace = pd.DataFrame(
        {
            "patient_id": patient_id,
            "time_sec": raw19.times.astype(float),
            "sample": np.arange(raw19.n_times, dtype=int),
        }
    )
    for channel_index, channel in enumerate(channels):
        trace[channel] = oriented[:, channel_index]
    return trace[columns]


def build_eeg_microstate_template_table(model) -> pd.DataFrame:
    channels = [str(name) for name in model.info["ch_names"]]
    columns = ["microstate", *channels]
    templates = np.asarray(model.cluster_centers_, dtype=float)
    if templates.size == 0:
        return pd.DataFrame(columns=columns)
    normalized = _map_patterns(templates)
    oriented = np.empty_like(normalized)
    for index in range(normalized.shape[0]):
        oriented[index], _ = _orient_pattern(normalized[index])
    rows: list[dict[str, object]] = []
    for microstate_index in range(oriented.shape[0]):
        row: dict[str, object] = {"microstate": int(microstate_index)}
        for channel_index, channel in enumerate(channels):
            row[channel] = float(oriented[microstate_index, channel_index])
        rows.append(row)
    return pd.DataFrame(rows, columns=columns)


def _eeg_topography_channel_columns(frame: pd.DataFrame) -> list[str]:
    metadata_columns = {
        "patient_id",
        "time_sec",
        "sample",
        "microstate",
        "corr",
        "field_state",
        "field_corr",
        "assigned_archetype",
        "assignment_similarity",
        "comparison_space",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
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
        "n_lags",
        "peak_lag_samples",
        "peak_lag_ms",
        "peak_effect_mean_diff",
        "peak_observed_coupling",
        "peak_null_mean_coupling",
        "peak_p_perm",
        "peak_width_ms",
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
    return [column for column in frame.columns if column not in metadata_columns]


def align_eeg_topography_to_archetypes(
    eeg_topography_df: pd.DataFrame,
    eeg_label_df: pd.DataFrame,
    field_label_df: pd.DataFrame,
    assignment_df: pd.DataFrame,
    *,
    patient_id: str,
    tolerance_ms: float = 5.0,
) -> pd.DataFrame:
    channel_columns = _eeg_topography_channel_columns(eeg_topography_df)
    columns = [
        "patient_id",
        "time_sec",
        "sample",
        "microstate",
        "corr",
        "field_state",
        "assigned_archetype",
        "assignment_similarity",
        "comparison_space",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        *channel_columns,
    ]
    if eeg_topography_df.empty or eeg_label_df.empty or field_label_df.empty or assignment_df.empty:
        return pd.DataFrame(columns=columns)
    patient_assignments = assignment_df[assignment_df["patient_id"].astype(str) == str(patient_id)].copy()
    if patient_assignments.empty:
        return pd.DataFrame(columns=columns)
    archetype_labels = field_label_df.merge(
        patient_assignments[
            ["patient_id", "field_state", "assigned_archetype", "assignment_similarity", "comparison_space"]
        ].copy(),
        on=["patient_id", "field_state"],
        how="inner",
    )
    if archetype_labels.empty:
        return pd.DataFrame(columns=columns)
    eeg_with_maps = pd.merge_asof(
        eeg_label_df.sort_values("time_sec")[["time_sec", "sample", "microstate", "corr"]].copy(),
        eeg_topography_df.sort_values("time_sec")[["time_sec", *channel_columns]].copy(),
        on="time_sec",
        direction="nearest",
        tolerance=tolerance_ms / 1000.0,
    ).dropna(subset=channel_columns[:1] if channel_columns else ["time_sec"])
    aligned = pd.merge_asof(
        eeg_with_maps.sort_values("time_sec"),
        archetype_labels.sort_values("time_sec")[
            [
                "time_sec",
                "field_state",
                "assigned_archetype",
                "assignment_similarity",
                "comparison_space",
                "peak_metric",
                "normalization",
                "n_states",
                "min_duration_ms",
            ]
        ].copy(),
        on="time_sec",
        direction="nearest",
        tolerance=tolerance_ms / 1000.0,
    ).dropna(subset=["assigned_archetype"])
    if aligned.empty:
        return pd.DataFrame(columns=columns)
    aligned.insert(0, "patient_id", patient_id)
    aligned["sample"] = aligned["sample"].astype(int)
    aligned["microstate"] = aligned["microstate"].astype(int)
    aligned["field_state"] = aligned["field_state"].astype(int)
    aligned["assigned_archetype"] = aligned["assigned_archetype"].astype(int)
    aligned["n_states"] = aligned["n_states"].astype(int)
    aligned["min_duration_ms"] = aligned["min_duration_ms"].astype(int)
    return aligned[columns].reset_index(drop=True)


def compute_subject_archetype_conditioned_eeg_maps(
    aligned_df: pd.DataFrame,
    *,
    patient_id: str,
) -> pd.DataFrame:
    channel_columns = _eeg_topography_channel_columns(aligned_df)
    columns = [
        "patient_id",
        "comparison_space",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "assigned_archetype",
        "n_samples",
        "n_unique_eeg_states",
        *channel_columns,
    ]
    if aligned_df.empty or not channel_columns:
        return pd.DataFrame(columns=columns)
    rows: list[dict[str, object]] = []
    for archetype, group in aligned_df.groupby("assigned_archetype", sort=True):
        row: dict[str, object] = {
            "patient_id": patient_id,
            "comparison_space": str(group["comparison_space"].iloc[0]),
            "peak_metric": str(group["peak_metric"].iloc[0]),
            "normalization": str(group["normalization"].iloc[0]),
            "n_states": int(group["n_states"].iloc[0]),
            "min_duration_ms": int(group["min_duration_ms"].iloc[0]),
            "assigned_archetype": int(archetype),
            "n_samples": int(group.shape[0]),
            "n_unique_eeg_states": int(group["microstate"].nunique()),
        }
        means = group[channel_columns].mean(axis=0)
        normalized_map, _ = _orient_pattern(_map_patterns(means.to_numpy(dtype=float)[None, :])[0])
        for channel_index, channel in enumerate(channel_columns):
            row[channel] = float(normalized_map[channel_index])
        rows.append(row)
    return pd.DataFrame(rows, columns=columns)


def summarize_group_archetype_conditioned_eeg_maps(
    subject_map_df: pd.DataFrame,
    *,
    min_subjects: int,
) -> pd.DataFrame:
    channel_columns = _eeg_topography_channel_columns(subject_map_df)
    columns = [
        "patient_id",
        "comparison_space",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "assigned_archetype",
        "n_subjects",
        "total_samples",
        *channel_columns,
    ]
    if subject_map_df.empty or not channel_columns:
        return pd.DataFrame(columns=columns)
    rows: list[dict[str, object]] = []
    group_keys = ["comparison_space", "peak_metric", "normalization", "n_states", "min_duration_ms", "assigned_archetype"]
    for keys, group in subject_map_df.groupby(group_keys, sort=True):
        n_subjects = int(group["patient_id"].astype(str).nunique())
        if n_subjects < int(min_subjects):
            continue
        row: dict[str, object] = {
            "patient_id": "group",
            "comparison_space": str(keys[0]),
            "peak_metric": str(keys[1]),
            "normalization": str(keys[2]),
            "n_states": int(keys[3]),
            "min_duration_ms": int(keys[4]),
            "assigned_archetype": int(keys[5]),
            "n_subjects": n_subjects,
            "total_samples": int(group["n_samples"].sum()),
        }
        means = group[channel_columns].mean(axis=0)
        normalized_map, _ = _orient_pattern(_map_patterns(means.to_numpy(dtype=float)[None, :])[0])
        for channel_index, channel in enumerate(channel_columns):
            row[channel] = float(normalized_map[channel_index])
        rows.append(row)
    return pd.DataFrame(rows, columns=columns)


def compute_subject_archetype_template_similarity(
    conditioned_map_df: pd.DataFrame,
    template_df: pd.DataFrame,
    *,
    patient_id: str,
) -> pd.DataFrame:
    conditioned_channels = _eeg_topography_channel_columns(conditioned_map_df)
    template_channels = _eeg_topography_channel_columns(template_df)
    channel_columns = [column for column in template_channels if column in conditioned_channels]
    columns = [
        "patient_id",
        "comparison_space",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "assigned_archetype",
        "microstate",
        "n_samples",
        "similarity",
    ]
    if conditioned_map_df.empty or template_df.empty or not channel_columns:
        return pd.DataFrame(columns=columns)
    conditioned_matrix = conditioned_map_df[channel_columns].to_numpy(dtype=float)
    template_matrix = template_df[channel_columns].to_numpy(dtype=float)
    similarity = _absolute_similarity(conditioned_matrix, template_matrix)
    rows: list[dict[str, object]] = []
    for row_index, conditioned_row in conditioned_map_df.reset_index(drop=True).iterrows():
        for template_index, template_row in template_df.reset_index(drop=True).iterrows():
            rows.append(
                {
                    "patient_id": patient_id,
                    "comparison_space": str(conditioned_row["comparison_space"]),
                    "peak_metric": str(conditioned_row["peak_metric"]),
                    "normalization": str(conditioned_row["normalization"]),
                    "n_states": int(conditioned_row["n_states"]),
                    "min_duration_ms": int(conditioned_row["min_duration_ms"]),
                    "assigned_archetype": int(conditioned_row["assigned_archetype"]),
                    "microstate": int(template_row["microstate"]),
                    "n_samples": int(conditioned_row["n_samples"]),
                    "similarity": float(similarity[row_index, template_index]),
                }
            )
    return pd.DataFrame(rows, columns=columns)


def summarize_group_archetype_template_similarity(
    subject_similarity_df: pd.DataFrame,
    *,
    min_subjects: int,
) -> pd.DataFrame:
    columns = [
        "comparison_space",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "assigned_archetype",
        "microstate",
        "n_subjects",
        "mean_similarity",
        "median_similarity",
        "min_similarity",
    ]
    if subject_similarity_df.empty:
        return pd.DataFrame(columns=columns)
    rows: list[dict[str, object]] = []
    group_keys = ["comparison_space", "peak_metric", "normalization", "n_states", "min_duration_ms", "assigned_archetype", "microstate"]
    for keys, group in subject_similarity_df.groupby(group_keys, sort=True):
        n_subjects = int(group["patient_id"].astype(str).nunique())
        if n_subjects < int(min_subjects):
            continue
        values = group["similarity"].to_numpy(dtype=float)
        rows.append(
            {
                "comparison_space": str(keys[0]),
                "peak_metric": str(keys[1]),
                "normalization": str(keys[2]),
                "n_states": int(keys[3]),
                "min_duration_ms": int(keys[4]),
                "assigned_archetype": int(keys[5]),
                "microstate": int(keys[6]),
                "n_subjects": n_subjects,
                "mean_similarity": float(values.mean()) if values.size else 0.0,
                "median_similarity": float(np.median(values)) if values.size else 0.0,
                "min_similarity": float(values.min()) if values.size else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def compute_subject_archetype_state_preference(
    aligned_df: pd.DataFrame,
    *,
    patient_id: str,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "comparison_space",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "assigned_archetype",
        "microstate",
        "n_samples",
        "joint_samples",
        "conditional_probability",
        "baseline_probability",
        "effect_mean_diff",
    ]
    if aligned_df.empty:
        return pd.DataFrame(columns=columns)
    data = aligned_df[(aligned_df["microstate"] >= 0) & (aligned_df["assigned_archetype"] >= 0)].copy()
    if data.empty:
        return pd.DataFrame(columns=columns)
    baseline = data["microstate"].value_counts(normalize=True).to_dict()
    states = sorted(int(value) for value in data["microstate"].unique().tolist())
    rows: list[dict[str, object]] = []
    for archetype, group in data.groupby("assigned_archetype", sort=True):
        state_probabilities = group["microstate"].value_counts(normalize=True).to_dict()
        state_counts = group["microstate"].value_counts().to_dict()
        for state in states:
            observed = float(state_probabilities.get(int(state), 0.0))
            baseline_probability = float(baseline.get(int(state), 0.0))
            rows.append(
                {
                    "patient_id": patient_id,
                    "comparison_space": str(group["comparison_space"].iloc[0]),
                    "peak_metric": str(group["peak_metric"].iloc[0]),
                    "normalization": str(group["normalization"].iloc[0]),
                    "n_states": int(group["n_states"].iloc[0]),
                    "min_duration_ms": int(group["min_duration_ms"].iloc[0]),
                    "assigned_archetype": int(archetype),
                    "microstate": int(state),
                    "n_samples": int(group.shape[0]),
                    "joint_samples": int(state_counts.get(int(state), 0)),
                    "conditional_probability": observed,
                    "baseline_probability": baseline_probability,
                    "effect_mean_diff": float(observed - baseline_probability),
                }
            )
    return pd.DataFrame(rows, columns=columns)


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


def compute_subject_field_state_coupling(
    aligned_df: pd.DataFrame,
    *,
    patient_id: str,
    lag_samples: list[int],
    sample_period_sec: float,
    n_surrogates: int,
    seed: int,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
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
    field_states = aligned_df["field_state"].to_numpy(dtype=int)
    if eeg_states.size < 2 or field_states.size < 2:
        return pd.DataFrame(columns=columns)
    peak_metric = str(aligned_df["peak_metric"].iloc[0])
    normalization = str(aligned_df["normalization"].iloc[0])
    n_states = int(aligned_df["n_states"].iloc[0])
    min_duration_ms = int(aligned_df["min_duration_ms"].iloc[0])
    surrogate_count = max(1, int(n_surrogates))
    max_shift = max(2, field_states.size)
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for lag in sorted(set(int(value) for value in lag_samples)):
        left, right = _lag_pair(eeg_states, field_states, lag)
        if left.size < 2 or right.size < 2:
            continue
        observed = _normalized_mutual_information(left, right)
        null_values = np.empty(surrogate_count, dtype=float)
        for index in range(surrogate_count):
            shifted = np.roll(field_states, int(rng.integers(1, max_shift)))
            shifted_left, shifted_right = _lag_pair(eeg_states, shifted, lag)
            null_values[index] = _normalized_mutual_information(shifted_left, shifted_right)
        rows.append(
            {
                "patient_id": patient_id,
                "peak_metric": peak_metric,
                "normalization": normalization,
                "n_states": n_states,
                "min_duration_ms": min_duration_ms,
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


def summarize_subject_fine_lag_profile(
    coupling_df: pd.DataFrame,
    *,
    patient_id: str,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "peak_lag_samples",
        "peak_lag_ms",
        "peak_effect_mean_diff",
        "peak_observed_coupling",
        "peak_null_mean_coupling",
        "peak_p_perm",
        "peak_width_ms",
        "n_lags",
    ]
    if coupling_df.empty:
        return pd.DataFrame(columns=columns)
    data = coupling_df.sort_values("lag_samples").reset_index(drop=True)
    peak_index = int(data["effect_mean_diff"].astype(float).idxmax())
    peak_row = data.loc[peak_index]
    effect_values = data["effect_mean_diff"].to_numpy(dtype=float)
    peak_effect = float(peak_row["effect_mean_diff"])
    threshold = peak_effect * 0.5 if peak_effect > 0.0 else peak_effect
    left = peak_index
    right = peak_index
    while left > 0 and effect_values[left - 1] >= threshold:
        left -= 1
    while right + 1 < effect_values.size and effect_values[right + 1] >= threshold:
        right += 1
    width_ms = float(data.loc[right, "lag_ms"] - data.loc[left, "lag_ms"]) if right > left else 0.0
    return pd.DataFrame(
        [
            {
                "patient_id": patient_id,
                "peak_metric": str(peak_row["peak_metric"]),
                "normalization": str(peak_row["normalization"]),
                "n_states": int(peak_row["n_states"]),
                "min_duration_ms": int(peak_row["min_duration_ms"]),
                "peak_lag_samples": int(peak_row["lag_samples"]),
                "peak_lag_ms": int(peak_row["lag_ms"]),
                "peak_effect_mean_diff": peak_effect,
                "peak_observed_coupling": float(peak_row["observed_coupling"]),
                "peak_null_mean_coupling": float(peak_row["null_mean_coupling"]),
                "peak_p_perm": float(peak_row["p_perm"]),
                "peak_width_ms": width_ms,
                "n_lags": int(data.shape[0]),
            }
        ],
        columns=columns,
    )


def compute_subject_transition_field_state_coupling(
    eeg_transition_df: pd.DataFrame,
    field_label_df: pd.DataFrame,
    *,
    patient_id: str,
    window_sec: float,
    n_surrogates: int,
    seed: int,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "from_state",
        "to_state",
        "response_kind",
        "response_state",
        "n_events",
        "observed_coupling",
        "null_mean_coupling",
        "effect_mean_diff",
        "p_perm",
    ]
    if eeg_transition_df.empty or field_label_df.empty:
        return pd.DataFrame(columns=columns)
    field_states = field_label_df.sort_values("time_sec").reset_index(drop=True)
    transitions = build_state_transition_table(
        field_states.rename(columns={"field_state": "microstate"})[["time_sec", "microstate"]],
        patient_id=patient_id,
    )
    if transitions.empty:
        return pd.DataFrame(columns=columns)
    peak_metric = str(field_states["peak_metric"].iloc[0])
    normalization = str(field_states["normalization"].iloc[0])
    n_states = int(field_states["n_states"].iloc[0])
    min_duration_ms = int(field_states["min_duration_ms"].iloc[0])

    def _response_rates(candidate_transitions: pd.DataFrame) -> dict[tuple[int, int, str, int], tuple[int, float]]:
        result: dict[tuple[int, int, str, int], tuple[int, float]] = {}
        transition_times = candidate_transitions["event_sec"].to_numpy(dtype=float)
        destination_states = candidate_transitions["to_state"].to_numpy(dtype=int)
        available_destination_states = sorted(set(destination_states.tolist()))
        for (from_state, to_state), group in eeg_transition_df.groupby(["from_state", "to_state"]):
            event_times = group["event_sec"].to_numpy(dtype=float)
            if event_times.size == 0:
                continue
            switch_matches = [
                bool(np.any((transition_times >= event_time) & (transition_times < event_time + window_sec)))
                for event_time in event_times
            ]
            result[(int(from_state), int(to_state), "any-switch", -1)] = (int(event_times.size), float(np.mean(switch_matches)))
            for destination_state in available_destination_states:
                destination_matches = [
                    bool(
                        np.any(
                            (transition_times >= event_time)
                            & (transition_times < event_time + window_sec)
                            & (destination_states == int(destination_state))
                        )
                    )
                    for event_time in event_times
                ]
                result[(int(from_state), int(to_state), "destination-state", int(destination_state))] = (
                    int(event_times.size),
                    float(np.mean(destination_matches)),
                )
        return result

    observed_rates = _response_rates(transitions)
    if not observed_rates:
        return pd.DataFrame(columns=columns)

    surrogate_count = max(1, int(n_surrogates))
    labels = field_states["field_state"].to_numpy(dtype=int)
    max_shift = max(2, labels.size)
    rng = np.random.default_rng(seed)
    null_values: dict[tuple[int, int, str, int], list[float]] = {key: [] for key in observed_rates}
    for _ in range(surrogate_count):
        shifted_states = field_states.copy()
        shifted_states["field_state"] = np.roll(labels, int(rng.integers(1, max_shift)))
        shifted_transitions = build_state_transition_table(
            shifted_states.rename(columns={"field_state": "microstate"})[["time_sec", "microstate"]],
            patient_id=patient_id,
        )
        shifted_rates = _response_rates(shifted_transitions)
        for key in null_values:
            null_values[key].append(float(shifted_rates.get(key, (0, 0.0))[1]))

    rows: list[dict[str, object]] = []
    for (from_state, to_state, response_kind, response_state), (n_events, observed_rate) in observed_rates.items():
        surrogate_rates = np.asarray(null_values[(from_state, to_state, response_kind, response_state)], dtype=float)
        rows.append(
            {
                "patient_id": patient_id,
                "peak_metric": peak_metric,
                "normalization": normalization,
                "n_states": n_states,
                "min_duration_ms": min_duration_ms,
                "from_state": int(from_state),
                "to_state": int(to_state),
                "response_kind": response_kind,
                "response_state": int(response_state),
                "n_events": int(n_events),
                "observed_coupling": float(observed_rate),
                "null_mean_coupling": float(surrogate_rates.mean()),
                "effect_mean_diff": float(observed_rate - surrogate_rates.mean()),
                "p_perm": float((np.sum(surrogate_rates >= observed_rate) + 1) / (surrogate_count + 1)),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def compute_subject_field_state_to_eeg_switching(
    field_label_df: pd.DataFrame,
    eeg_label_df: pd.DataFrame,
    *,
    patient_id: str,
    window_sec: float,
    n_surrogates: int,
    seed: int,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "from_state",
        "to_state",
        "response_kind",
        "response_state",
        "n_events",
        "observed_coupling",
        "null_mean_coupling",
        "effect_mean_diff",
        "p_perm",
    ]
    if field_label_df.empty or eeg_label_df.empty:
        return pd.DataFrame(columns=columns)
    field_states = field_label_df.sort_values("time_sec").reset_index(drop=True)
    field_transitions = build_state_transition_table(
        field_states.rename(columns={"field_state": "microstate"})[["time_sec", "microstate"]],
        patient_id=patient_id,
    )
    eeg_transitions = build_state_transition_table(
        eeg_label_df.sort_values("time_sec")[["time_sec", "microstate"]],
        patient_id=patient_id,
    )
    if field_transitions.empty or eeg_transitions.empty:
        return pd.DataFrame(columns=columns)
    peak_metric = str(field_states["peak_metric"].iloc[0])
    normalization = str(field_states["normalization"].iloc[0])
    n_states = int(field_states["n_states"].iloc[0])
    min_duration_ms = int(field_states["min_duration_ms"].iloc[0])

    def _response_rates(candidate_transitions: pd.DataFrame) -> dict[tuple[int, int, str, int], tuple[int, float]]:
        result: dict[tuple[int, int, str, int], tuple[int, float]] = {}
        transition_times = candidate_transitions["event_sec"].to_numpy(dtype=float)
        destination_states = candidate_transitions["to_state"].to_numpy(dtype=int)
        available_destination_states = sorted(set(destination_states.tolist()))
        for (from_state, to_state), group in field_transitions.groupby(["from_state", "to_state"]):
            event_times = group["event_sec"].to_numpy(dtype=float)
            if event_times.size == 0:
                continue
            switch_matches = [
                bool(np.any((transition_times >= event_time) & (transition_times < event_time + window_sec)))
                for event_time in event_times
            ]
            result[(int(from_state), int(to_state), "any-switch", -1)] = (int(event_times.size), float(np.mean(switch_matches)))
            for destination_state in available_destination_states:
                destination_matches = [
                    bool(
                        np.any(
                            (transition_times >= event_time)
                            & (transition_times < event_time + window_sec)
                            & (destination_states == int(destination_state))
                        )
                    )
                    for event_time in event_times
                ]
                result[(int(from_state), int(to_state), "destination-state", int(destination_state))] = (
                    int(event_times.size),
                    float(np.mean(destination_matches)),
                )
        return result

    observed_rates = _response_rates(eeg_transitions)
    if not observed_rates:
        return pd.DataFrame(columns=columns)
    eeg_states = eeg_label_df.sort_values("time_sec")["microstate"].to_numpy(dtype=int)
    max_shift = max(2, eeg_states.size)
    surrogate_count = max(1, int(n_surrogates))
    rng = np.random.default_rng(seed)
    null_values: dict[tuple[int, int, str, int], list[float]] = {key: [] for key in observed_rates}
    for _ in range(surrogate_count):
        shifted_eeg = eeg_label_df.sort_values("time_sec").copy()
        shifted_eeg["microstate"] = np.roll(eeg_states, int(rng.integers(1, max_shift)))
        shifted_transitions = build_state_transition_table(shifted_eeg[["time_sec", "microstate"]], patient_id=patient_id)
        shifted_rates = _response_rates(shifted_transitions)
        for key in null_values:
            null_values[key].append(float(shifted_rates.get(key, (0, 0.0))[1]))
    rows: list[dict[str, object]] = []
    for (from_state, to_state, response_kind, response_state), (n_events, observed_rate) in observed_rates.items():
        surrogate_rates = np.asarray(null_values[(from_state, to_state, response_kind, response_state)], dtype=float)
        rows.append(
            {
                "patient_id": patient_id,
                "peak_metric": peak_metric,
                "normalization": normalization,
                "n_states": n_states,
                "min_duration_ms": min_duration_ms,
                "from_state": int(from_state),
                "to_state": int(to_state),
                "response_kind": response_kind,
                "response_state": int(response_state),
                "n_events": int(n_events),
                "observed_coupling": float(observed_rate),
                "null_mean_coupling": float(surrogate_rates.mean()),
                "effect_mean_diff": float(observed_rate - surrogate_rates.mean()),
                "p_perm": float((np.sum(surrogate_rates >= observed_rate) + 1) / (surrogate_count + 1)),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def _fit_linear_model(y: np.ndarray, *predictors: np.ndarray) -> np.ndarray:
    design = [np.ones(y.size, dtype=float)]
    for predictor in predictors:
        values = np.asarray(predictor, dtype=float)
        if values.ndim == 1:
            design.append(values)
        else:
            design.extend(values.T)
    matrix = np.column_stack(design)
    coefficients, _, _, _ = np.linalg.lstsq(matrix, y, rcond=None)
    return coefficients


def compute_subject_gfp_controlled_field_state_profiles(
    aligned_df: pd.DataFrame,
    *,
    patient_id: str,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "microstate",
        "adjusted_switch_rate",
        "raw_switch_rate",
        "n_state_samples",
        "mean_state_gfp",
        "gfp_beta",
    ]
    if aligned_df.empty:
        return pd.DataFrame(columns=columns)
    data = aligned_df[
        np.isfinite(aligned_df["gfp"])
        & np.isfinite(aligned_df["switch_indicator"])
        & (aligned_df["microstate"] >= 0)
        & (aligned_df["field_state"] >= 0)
    ].copy()
    if data.empty:
        return pd.DataFrame(columns=columns)
    states = sorted(data["microstate"].unique().tolist())
    if len(states) < 2:
        return pd.DataFrame(columns=columns)
    y = data["switch_indicator"].to_numpy(dtype=float)
    centered_gfp = data["gfp"].to_numpy(dtype=float) - float(data["gfp"].mean())
    dummy_matrix = np.column_stack([(data["microstate"].to_numpy(dtype=int) == state).astype(float) for state in states[1:]])
    coefficients = _fit_linear_model(y, centered_gfp, dummy_matrix)
    intercept = float(coefficients[0])
    gfp_beta = float(coefficients[1])
    rows: list[dict[str, object]] = []
    peak_metric = str(data["peak_metric"].iloc[0])
    normalization = str(data["normalization"].iloc[0])
    n_states = int(data["n_states"].iloc[0])
    min_duration_ms = int(data["min_duration_ms"].iloc[0])
    for state_index, state in enumerate(states):
        state_mask = data["microstate"] == state
        adjusted_value = intercept if state_index == 0 else intercept + float(coefficients[state_index + 1])
        rows.append(
            {
                "patient_id": patient_id,
                "peak_metric": peak_metric,
                "normalization": normalization,
                "n_states": n_states,
                "min_duration_ms": min_duration_ms,
                "microstate": int(state),
                "adjusted_switch_rate": float(adjusted_value),
                "raw_switch_rate": float(data.loc[state_mask, "switch_indicator"].mean()),
                "n_state_samples": int(state_mask.sum()),
                "mean_state_gfp": float(data.loc[state_mask, "gfp"].mean()),
                "gfp_beta": gfp_beta,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def compute_subject_gfp_controlled_field_state_transition_effects(
    transition_df: pd.DataFrame,
    aligned_df: pd.DataFrame,
    *,
    patient_id: str,
    window_sec: float,
    sample_period_sec: float,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "from_state",
        "to_state",
        "n_events",
        "n_samples",
        "pre_switch_rate",
        "post_switch_rate",
        "effect_mean_diff",
        "gfp_beta",
    ]
    if transition_df.empty or aligned_df.empty or sample_period_sec <= 0.0:
        return pd.DataFrame(columns=columns)
    trace = aligned_df.sort_values("time_sec").reset_index(drop=True).reset_index(names="trace_index")
    transition_map = pd.merge_asof(
        transition_df.sort_values("event_sec")[["event_sec", "from_state", "to_state"]].copy(),
        trace[["trace_index", "time_sec"]].copy(),
        left_on="event_sec",
        right_on="time_sec",
        direction="nearest",
        tolerance=sample_period_sec / 2.0 + 0.002,
    ).dropna(subset=["trace_index"])
    if transition_map.empty:
        return pd.DataFrame(columns=columns)
    peak_metric = str(trace["peak_metric"].iloc[0])
    normalization = str(trace["normalization"].iloc[0])
    n_states = int(trace["n_states"].iloc[0])
    min_duration_ms = int(trace["min_duration_ms"].iloc[0])
    window_samples = max(1, int(round(float(window_sec) / sample_period_sec)))
    rows: list[dict[str, object]] = []
    for (from_state, to_state), group in transition_map.groupby(["from_state", "to_state"]):
        window_frames: list[pd.DataFrame] = []
        for event_index in group["trace_index"].astype(int):
            start = max(0, event_index - window_samples)
            stop = min(len(trace), event_index + window_samples)
            if stop - start < 2:
                continue
            window = trace.iloc[start:stop].copy()
            relative = np.arange(start - event_index, stop - event_index, dtype=int)
            window["post_indicator"] = (relative >= 0).astype(float)
            window_frames.append(window)
        if not window_frames:
            continue
        model_df = pd.concat(window_frames, ignore_index=True)
        if model_df["post_indicator"].nunique() < 2:
            continue
        y = model_df["switch_indicator"].to_numpy(dtype=float)
        centered_gfp = model_df["gfp"].to_numpy(dtype=float) - float(model_df["gfp"].mean())
        post_indicator = model_df["post_indicator"].to_numpy(dtype=float)
        coefficients = _fit_linear_model(y, centered_gfp, post_indicator)
        intercept = float(coefficients[0])
        gfp_beta = float(coefficients[1])
        post_beta = float(coefficients[2])
        rows.append(
            {
                "patient_id": patient_id,
                "peak_metric": peak_metric,
                "normalization": normalization,
                "n_states": n_states,
                "min_duration_ms": min_duration_ms,
                "from_state": int(from_state),
                "to_state": int(to_state),
                "n_events": int(group.shape[0]),
                "n_samples": int(model_df.shape[0]),
                "pre_switch_rate": intercept,
                "post_switch_rate": intercept + post_beta,
                "effect_mean_diff": post_beta,
                "gfp_beta": gfp_beta,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def compute_subject_gfp_controlled_field_state_to_eeg_switching(
    field_transition_df: pd.DataFrame,
    aligned_df: pd.DataFrame,
    *,
    patient_id: str,
    window_sec: float,
    sample_period_sec: float,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "from_state",
        "to_state",
        "n_events",
        "n_samples",
        "pre_switch_rate",
        "post_switch_rate",
        "effect_mean_diff",
        "gfp_beta",
    ]
    if field_transition_df.empty or aligned_df.empty or sample_period_sec <= 0.0:
        return pd.DataFrame(columns=columns)
    trace = aligned_df.sort_values("time_sec").reset_index(drop=True).reset_index(names="trace_index")
    transition_map = pd.merge_asof(
        field_transition_df.sort_values("event_sec")[["event_sec", "from_state", "to_state"]].copy(),
        trace[["trace_index", "time_sec"]].copy(),
        left_on="event_sec",
        right_on="time_sec",
        direction="nearest",
        tolerance=sample_period_sec / 2.0 + 0.002,
    ).dropna(subset=["trace_index"])
    if transition_map.empty:
        return pd.DataFrame(columns=columns)
    peak_metric = str(trace["peak_metric"].iloc[0])
    normalization = str(trace["normalization"].iloc[0])
    n_states = int(trace["n_states"].iloc[0])
    min_duration_ms = int(trace["min_duration_ms"].iloc[0])
    window_samples = max(1, int(round(float(window_sec) / sample_period_sec)))
    rows: list[dict[str, object]] = []
    for (from_state, to_state), group in transition_map.groupby(["from_state", "to_state"]):
        window_frames: list[pd.DataFrame] = []
        for event_index in group["trace_index"].astype(int):
            start = max(0, event_index - window_samples)
            stop = min(len(trace), event_index + window_samples)
            if stop - start < 2:
                continue
            window = trace.iloc[start:stop].copy()
            relative = np.arange(start - event_index, stop - event_index, dtype=int)
            window["post_indicator"] = (relative >= 0).astype(float)
            window_frames.append(window)
        if not window_frames:
            continue
        model_df = pd.concat(window_frames, ignore_index=True)
        if model_df["post_indicator"].nunique() < 2:
            continue
        y = model_df["eeg_switch_indicator"].to_numpy(dtype=float)
        centered_gfp = model_df["gfp"].to_numpy(dtype=float) - float(model_df["gfp"].mean())
        post_indicator = model_df["post_indicator"].to_numpy(dtype=float)
        coefficients = _fit_linear_model(y, centered_gfp, post_indicator)
        intercept = float(coefficients[0])
        gfp_beta = float(coefficients[1])
        post_beta = float(coefficients[2])
        rows.append(
            {
                "patient_id": patient_id,
                "peak_metric": peak_metric,
                "normalization": normalization,
                "n_states": n_states,
                "min_duration_ms": min_duration_ms,
                "from_state": int(from_state),
                "to_state": int(to_state),
                "n_events": int(group.shape[0]),
                "n_samples": int(model_df.shape[0]),
                "pre_switch_rate": intercept,
                "post_switch_rate": intercept + post_beta,
                "effect_mean_diff": post_beta,
                "gfp_beta": gfp_beta,
            }
        )
    return pd.DataFrame(rows, columns=columns)
