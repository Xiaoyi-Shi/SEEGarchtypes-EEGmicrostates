from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from scipy.signal import hilbert


_META_COLUMNS = {"patient_id", "time_sec", "microstate", "corr"}
SUPPORTED_CONNECTIVITY_METHODS: tuple[str, ...] = ("corr", "plv", "wpli")


def normalize_connectivity_method(method: str) -> str:
    value = str(method).strip().lower()
    aliases = {
        "correlation": "corr",
        "pearson": "corr",
        "phase_locking_value": "plv",
        "weighted_phase_lag_index": "wpli",
    }
    normalized = aliases.get(value, value)
    if normalized not in SUPPORTED_CONNECTIVITY_METHODS:
        supported = ", ".join(SUPPORTED_CONNECTIVITY_METHODS)
        raise ValueError(f"Unsupported connectivity method '{method}'. Expected one of: {supported}.")
    return normalized


def connectivity_analysis_branch(method: str) -> str:
    normalized = normalize_connectivity_method(method)
    return f"band_1_40_{normalized}"


def _absolute_correlation(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 2 or right.size < 2:
        return float("nan")
    if float(np.nanstd(left, ddof=0)) == 0.0 or float(np.nanstd(right, ddof=0)) == 0.0:
        return float("nan")
    corr = np.corrcoef(left, right)[0, 1]
    return float(abs(corr))


def _phase_locking_value(left: np.ndarray, right: np.ndarray) -> float:
    delta = np.angle(left) - np.angle(right)
    return float(np.abs(np.mean(np.exp(1j * delta))))


def _weighted_phase_lag_index(left: np.ndarray, right: np.ndarray) -> float:
    imaginary = np.imag(left * np.conj(right))
    denominator = float(np.mean(np.abs(imaginary)))
    if denominator == 0.0:
        return float("nan")
    return float(abs(np.mean(imaginary)) / denominator)


def _pairwise_connectivity(
    matrix: np.ndarray,
    *,
    method: str,
) -> dict[tuple[int, int], float]:
    n_regions = matrix.shape[1]
    results: dict[tuple[int, int], float] = {}
    normalized = normalize_connectivity_method(method)
    if matrix.shape[0] < 2 or n_regions < 2:
        return results
    if normalized == "corr":
        for left_index, right_index in combinations(range(n_regions), 2):
            value = _absolute_correlation(matrix[:, left_index], matrix[:, right_index])
            if np.isnan(value):
                continue
            results[(left_index, right_index)] = value
        return results

    metric = _phase_locking_value if normalized == "plv" else _weighted_phase_lag_index
    for left_index, right_index in combinations(range(n_regions), 2):
        value = metric(matrix[:, left_index], matrix[:, right_index])
        if np.isnan(value):
            continue
        results[(left_index, right_index)] = value
    return results


def compute_subject_microstate_connectivity_effects(
    aligned_df: pd.DataFrame,
    *,
    min_samples: int,
    method: str,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if aligned_df.empty:
        return pd.DataFrame(rows)
    normalized = normalize_connectivity_method(method)
    for patient_id, group in aligned_df.groupby("patient_id"):
        region_columns = [column for column in group.columns if column not in _META_COLUMNS]
        if len(region_columns) < 2:
            continue
        values = group[region_columns].to_numpy(dtype=float)
        phase_ready_values = hilbert(values, axis=0) if normalized in {"plv", "wpli"} else values
        labels = group["microstate"].to_numpy(dtype=int)
        for microstate in sorted(group["microstate"].unique()):
            state_values = phase_ready_values[labels == microstate]
            off_values = phase_ready_values[labels != microstate]
            if state_values.shape[0] < min_samples or off_values.shape[0] < min_samples:
                continue
            state_connectivity = _pairwise_connectivity(state_values, method=normalized)
            off_connectivity = _pairwise_connectivity(off_values, method=normalized)
            for left_index, right_index in combinations(range(len(region_columns)), 2):
                pair_key = (left_index, right_index)
                if pair_key not in state_connectivity or pair_key not in off_connectivity:
                    continue
                state_value = state_connectivity[pair_key]
                off_value = off_connectivity[pair_key]
                rows.append(
                    {
                        "patient_id": str(patient_id),
                        "method": normalized,
                        "microstate": int(microstate),
                        "region_a": str(region_columns[left_index]),
                        "region_b": str(region_columns[right_index]),
                        "state_connectivity": float(state_value),
                        "off_connectivity": float(off_value),
                        "effect_mean_diff": float(state_value - off_value),
                        "n_state_samples": int(state_values.shape[0]),
                        "n_nonstate_samples": int(off_values.shape[0]),
                    }
                )
    return pd.DataFrame(rows)


def compute_subject_microstate_connectivity_profiles(
    aligned_df: pd.DataFrame,
    *,
    min_samples: int,
    method: str,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if aligned_df.empty:
        return pd.DataFrame(rows)
    normalized = normalize_connectivity_method(method)
    for patient_id, group in aligned_df.groupby("patient_id"):
        region_columns = [column for column in group.columns if column not in _META_COLUMNS]
        if len(region_columns) < 2:
            continue
        values = group[region_columns].to_numpy(dtype=float)
        phase_ready_values = hilbert(values, axis=0) if normalized in {"plv", "wpli"} else values
        labels = group["microstate"].to_numpy(dtype=int)
        for microstate in sorted(group["microstate"].unique()):
            state_values = phase_ready_values[labels == microstate]
            if state_values.shape[0] < min_samples:
                continue
            state_connectivity = _pairwise_connectivity(state_values, method=normalized)
            for left_index, right_index in combinations(range(len(region_columns)), 2):
                pair_key = (left_index, right_index)
                if pair_key not in state_connectivity:
                    continue
                rows.append(
                    {
                        "patient_id": str(patient_id),
                        "method": normalized,
                        "microstate": int(microstate),
                        "region_a": str(region_columns[left_index]),
                        "region_b": str(region_columns[right_index]),
                        "state_connectivity": float(state_connectivity[pair_key]),
                        "n_state_samples": int(state_values.shape[0]),
                    }
                )
    return pd.DataFrame(rows)


def compute_subject_event_locked_connectivity_effects(
    event_df: pd.DataFrame,
    region_df: pd.DataFrame,
    *,
    patient_id: str,
    window_sec: float,
    min_samples: int,
    method: str,
    event_keys: tuple[str, ...],
    event_time_column: str = "event_sec",
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if event_df.empty or region_df.empty:
        return pd.DataFrame(rows)
    normalized = normalize_connectivity_method(method)
    region_columns = [column for column in region_df.columns if column != "time_sec"]
    if len(region_columns) < 2:
        return pd.DataFrame(rows)
    times = region_df["time_sec"].to_numpy(dtype=float)
    values = region_df[region_columns].to_numpy(dtype=float)
    for event in event_df.itertuples(index=False):
        event_sec = float(getattr(event, event_time_column))
        pre_values = values[(times >= event_sec - window_sec) & (times < event_sec)]
        post_values = values[(times >= event_sec) & (times < event_sec + window_sec)]
        if pre_values.shape[0] < min_samples or post_values.shape[0] < min_samples:
            continue
        if normalized in {"plv", "wpli"}:
            pre_values = hilbert(pre_values, axis=0)
            post_values = hilbert(post_values, axis=0)
        post_connectivity = _pairwise_connectivity(post_values, method=normalized)
        pre_connectivity = _pairwise_connectivity(pre_values, method=normalized)
        for left_index, right_index in combinations(range(len(region_columns)), 2):
            pair_key = (left_index, right_index)
            if pair_key not in post_connectivity or pair_key not in pre_connectivity:
                continue
            row = {
                "patient_id": str(patient_id),
                "method": normalized,
                "region_a": str(region_columns[left_index]),
                "region_b": str(region_columns[right_index]),
                "state_connectivity": float(post_connectivity[pair_key]),
                "off_connectivity": float(pre_connectivity[pair_key]),
                "effect_mean_diff": float(post_connectivity[pair_key] - pre_connectivity[pair_key]),
                "n_state_samples": int(post_values.shape[0]),
                "n_nonstate_samples": int(pre_values.shape[0]),
            }
            for key in event_keys:
                row[key] = getattr(event, key)
            rows.append(row)
    event_effects = pd.DataFrame(rows)
    if event_effects.empty:
        return event_effects
    group_keys = ["patient_id", "method", *event_keys, "region_a", "region_b"]
    return (
        event_effects.groupby(group_keys, as_index=False)
        .agg(
            n_events=("effect_mean_diff", "size"),
            state_connectivity=("state_connectivity", "mean"),
            off_connectivity=("off_connectivity", "mean"),
            effect_mean_diff=("effect_mean_diff", "mean"),
            n_state_samples=("n_state_samples", "mean"),
            n_nonstate_samples=("n_nonstate_samples", "mean"),
        )
        .reset_index(drop=True)
    )
