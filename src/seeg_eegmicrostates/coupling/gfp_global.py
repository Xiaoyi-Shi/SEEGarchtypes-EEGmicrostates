from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.signal import hilbert


SUPPORTED_GFP_GLOBAL_METRICS: tuple[str, ...] = ("rms", "envelope-rms", "spatial-std")
SUPPORTED_GFP_GLOBAL_WEIGHTINGS: tuple[str, ...] = ("equal", "sqrt-channel-count")
DEFAULT_GFP_GLOBAL_METRIC = "rms"
DEFAULT_GFP_GLOBAL_WEIGHTING = "equal"
DEFAULT_GFP_GLOBAL_SURROGATES = 128
DEFAULT_GFP_PEAK_WINDOW_SEC = 0.5
YEO17_CORE_NETWORKS: tuple[str, ...] = (
    "DefaultB",
    "ContB",
    "SalVentAttnA",
    "SomMotB",
    "TempPar",
    "LimbicA",
    "DorsAttnA",
    "SalVentAttnB",
    "DefaultC",
    "DefaultA",
    "LimbicB",
)
YEO17_CORE_SCOPE = "yeo17-core"


def normalize_global_metric_definition(metric: str) -> str:
    value = str(metric).strip().lower().replace("_", "-")
    aliases = {
        "rms": "rms",
        "envelope": "envelope-rms",
        "envelope-rms": "envelope-rms",
        "env-rms": "envelope-rms",
        "spatial-std": "spatial-std",
        "spatial-stddev": "spatial-std",
        "std": "spatial-std",
    }
    normalized = aliases.get(value, value)
    if normalized not in SUPPORTED_GFP_GLOBAL_METRICS:
        supported = ", ".join(SUPPORTED_GFP_GLOBAL_METRICS)
        raise ValueError(f"Unsupported global metric definition '{metric}'. Expected one of: {supported}.")
    return normalized


def normalize_global_weighting_strategy(weighting: str) -> str:
    value = str(weighting).strip().lower().replace("_", "-")
    aliases = {
        "equal": "equal",
        "sqrt-channel-count": "sqrt-channel-count",
        "sqrt-channels": "sqrt-channel-count",
        "sqrt": "sqrt-channel-count",
    }
    normalized = aliases.get(value, value)
    if normalized not in SUPPORTED_GFP_GLOBAL_WEIGHTINGS:
        supported = ", ".join(SUPPORTED_GFP_GLOBAL_WEIGHTINGS)
        raise ValueError(f"Unsupported global weighting strategy '{weighting}'. Expected one of: {supported}.")
    return normalized


def global_metric_label(metric_definition: str, weighting_strategy: str) -> str:
    return f"{normalize_global_metric_definition(metric_definition)}__{normalize_global_weighting_strategy(weighting_strategy)}"
def _region_columns(region_df: pd.DataFrame) -> list[str]:
    return [column for column in region_df.columns if column != "time_sec"]


def _zscore_matrix(matrix: np.ndarray) -> np.ndarray:
    centered = matrix - np.nanmean(matrix, axis=0, keepdims=True)
    scales = np.nanstd(centered, axis=0, ddof=0, keepdims=True)
    scales[~np.isfinite(scales) | (scales == 0.0)] = 1.0
    normalized = centered / scales
    normalized[~np.isfinite(normalized)] = 0.0
    return normalized


def _weighted_rms(matrix: np.ndarray, weights: np.ndarray) -> np.ndarray:
    return np.sqrt(np.sum((matrix**2) * weights[None, :], axis=1) / float(weights.sum()))


def _weighted_std(matrix: np.ndarray, weights: np.ndarray) -> np.ndarray:
    mean = np.sum(matrix * weights[None, :], axis=1, keepdims=True) / float(weights.sum())
    variance = np.sum(((matrix - mean) ** 2) * weights[None, :], axis=1) / float(weights.sum())
    return np.sqrt(np.maximum(variance, 0.0))


def _coverage_lookup(coverage_df: pd.DataFrame) -> dict[str, float]:
    if coverage_df.empty:
        return {}
    coverage = coverage_df.groupby("region", sort=False)["n_bipolar_channels"].sum()
    return {str(region): float(count) for region, count in coverage.items()}


def _select_core_networks(region_df: pd.DataFrame, coverage_df: pd.DataFrame) -> tuple[list[str], dict[str, float]]:
    available_columns = set(_region_columns(region_df))
    coverage_lookup = _coverage_lookup(coverage_df)
    selected = [network for network in YEO17_CORE_NETWORKS if network in available_columns and network in coverage_lookup]
    return selected, coverage_lookup


def _metric_weights(networks: Iterable[str], coverage_lookup: dict[str, float], weighting_strategy: str) -> np.ndarray:
    normalized = normalize_global_weighting_strategy(weighting_strategy)
    weights: list[float] = []
    for network in networks:
        channels = max(1.0, float(coverage_lookup.get(network, 1.0)))
        if normalized == "equal":
            weights.append(1.0)
        else:
            weights.append(math.sqrt(channels))
    result = np.asarray(weights, dtype=float)
    if result.size == 0:
        return result
    result[~np.isfinite(result) | (result <= 0.0)] = 1.0
    return result


def derive_seeg_global_metric_trace(
    region_df: pd.DataFrame,
    coverage_df: pd.DataFrame,
    *,
    patient_id: str,
    metric_definition: str,
    weighting_strategy: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    normalized_metric = normalize_global_metric_definition(metric_definition)
    normalized_weighting = normalize_global_weighting_strategy(weighting_strategy)
    trace_columns = [
        "patient_id",
        "time_sec",
        "sample",
        "global_metric",
        "metric_definition",
        "weighting_strategy",
        "network_scope",
        "n_networks_used",
    ]
    support_columns = [
        "patient_id",
        "region",
        "metric_definition",
        "weighting_strategy",
        "network_scope",
        "n_bipolar_channels",
        "weight",
        "is_selected",
    ]
    if region_df.empty:
        return pd.DataFrame(columns=trace_columns), pd.DataFrame(columns=support_columns)
    selected_networks, coverage_lookup = _select_core_networks(region_df, coverage_df)
    support_rows = [
        {
            "patient_id": patient_id,
            "region": network,
            "metric_definition": normalized_metric,
            "weighting_strategy": normalized_weighting,
            "network_scope": YEO17_CORE_SCOPE,
            "n_bipolar_channels": float(coverage_lookup.get(network, 0.0)),
            "weight": 0.0,
            "is_selected": False,
        }
        for network in YEO17_CORE_NETWORKS
    ]
    if len(selected_networks) < 2:
        return pd.DataFrame(columns=trace_columns), pd.DataFrame(support_rows, columns=support_columns)
    weights = _metric_weights(selected_networks, coverage_lookup, normalized_weighting)
    values = _zscore_matrix(region_df[selected_networks].to_numpy(dtype=float))
    if normalized_metric == "envelope-rms":
        values = np.abs(hilbert(values, axis=0))
        metric_values = _weighted_rms(values, weights)
    elif normalized_metric == "spatial-std":
        metric_values = _weighted_std(values, weights)
    else:
        metric_values = _weighted_rms(values, weights)
    weight_lookup = {network: float(weight) for network, weight in zip(selected_networks, weights, strict=False)}
    for row in support_rows:
        if row["region"] in weight_lookup:
            row["weight"] = weight_lookup[row["region"]]
            row["is_selected"] = True
    trace_df = pd.DataFrame(
        {
            "patient_id": patient_id,
            "time_sec": region_df["time_sec"].to_numpy(dtype=float),
            "sample": np.arange(region_df.shape[0], dtype=int),
            "global_metric": metric_values.astype(float),
            "metric_definition": normalized_metric,
            "weighting_strategy": normalized_weighting,
            "network_scope": YEO17_CORE_SCOPE,
            "n_networks_used": int(len(selected_networks)),
        }
    )
    return trace_df, pd.DataFrame(support_rows, columns=support_columns)


def align_gfp_and_global_traces(
    gfp_trace_df: pd.DataFrame,
    global_trace_df: pd.DataFrame,
    *,
    patient_id: str,
    tolerance_ms: float = 5.0,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "time_sec",
        "eeg_sample",
        "seeg_sample",
        "gfp",
        "global_metric",
        "metric_definition",
        "weighting_strategy",
        "network_scope",
        "n_networks_used",
    ]
    if gfp_trace_df.empty or global_trace_df.empty:
        return pd.DataFrame(columns=columns)
    left = gfp_trace_df.sort_values("time_sec")[["time_sec", "sample", "gfp"]].rename(columns={"sample": "eeg_sample"})
    right = global_trace_df.sort_values("time_sec")[
        ["time_sec", "sample", "global_metric", "metric_definition", "weighting_strategy", "network_scope", "n_networks_used"]
    ].rename(columns={"sample": "seeg_sample"})
    aligned = pd.merge_asof(
        left,
        right,
        on="time_sec",
        direction="nearest",
        tolerance=tolerance_ms / 1000.0,
    ).dropna(subset=["global_metric"])
    aligned.insert(0, "patient_id", patient_id)
    aligned["eeg_sample"] = aligned["eeg_sample"].astype(int)
    aligned["seeg_sample"] = aligned["seeg_sample"].astype(int)
    aligned["n_networks_used"] = aligned["n_networks_used"].astype(int)
    return aligned.reset_index(drop=True)


def align_microstate_to_gfp_and_global(
    label_df: pd.DataFrame,
    gfp_trace_df: pd.DataFrame,
    global_trace_df: pd.DataFrame,
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
        "global_metric",
        "metric_definition",
        "weighting_strategy",
        "network_scope",
        "n_networks_used",
    ]
    if label_df.empty:
        return pd.DataFrame(columns=columns)
    gfp_aligned = pd.merge_asof(
        label_df.sort_values("time_sec")[["time_sec", "sample", "microstate", "corr"]].copy(),
        gfp_trace_df.sort_values("time_sec")[["time_sec", "gfp"]].copy(),
        on="time_sec",
        direction="nearest",
        tolerance=tolerance_ms / 1000.0,
    )
    aligned = pd.merge_asof(
        gfp_aligned,
        global_trace_df.sort_values("time_sec")[
            ["time_sec", "global_metric", "metric_definition", "weighting_strategy", "network_scope", "n_networks_used"]
        ].copy(),
        on="time_sec",
        direction="nearest",
        tolerance=tolerance_ms / 1000.0,
    ).dropna(subset=["gfp", "global_metric"])
    aligned.insert(0, "patient_id", patient_id)
    aligned["sample"] = aligned["sample"].astype(int)
    aligned["microstate"] = aligned["microstate"].astype(int)
    aligned["n_networks_used"] = aligned["n_networks_used"].astype(int)
    return aligned.reset_index(drop=True)


def _pearson_correlation(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 3 or right.size < 3 or left.size != right.size:
        return 0.0
    if np.allclose(left, left[0]) or np.allclose(right, right[0]):
        return 0.0
    return float(np.corrcoef(left, right)[0, 1])


def _lag_pair(left: np.ndarray, right: np.ndarray, lag_samples: int) -> tuple[np.ndarray, np.ndarray]:
    if lag_samples > 0:
        if lag_samples >= left.size:
            return np.empty(0, dtype=float), np.empty(0, dtype=float)
        return left[:-lag_samples], right[lag_samples:]
    if lag_samples < 0:
        lag = abs(lag_samples)
        if lag >= left.size:
            return np.empty(0, dtype=float), np.empty(0, dtype=float)
        return left[lag:], right[:-lag]
    return left, right


def compute_subject_gfp_global_coupling(
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
        "metric_definition",
        "weighting_strategy",
        "network_scope",
        "lag_samples",
        "lag_ms",
        "n_samples",
        "n_networks_used",
        "observed_coupling",
        "null_mean_coupling",
        "effect_mean_diff",
        "p_perm",
    ]
    if aligned_df.empty:
        return pd.DataFrame(columns=columns)
    eeg_gfp = aligned_df["gfp"].to_numpy(dtype=float)
    seeg_global = aligned_df["global_metric"].to_numpy(dtype=float)
    if eeg_gfp.size < 3 or seeg_global.size < 3:
        return pd.DataFrame(columns=columns)
    metric_definition = str(aligned_df["metric_definition"].iloc[0])
    weighting_strategy = str(aligned_df["weighting_strategy"].iloc[0])
    network_scope = str(aligned_df["network_scope"].iloc[0])
    n_networks_used = int(aligned_df["n_networks_used"].iloc[0])
    rows: list[dict[str, object]] = []
    surrogate_count = max(1, int(n_surrogates))
    max_shift = max(2, seeg_global.size)
    rng = np.random.default_rng(seed)
    for lag in sorted(set(int(value) for value in lag_samples)):
        left, right = _lag_pair(eeg_gfp, seeg_global, lag)
        if left.size < 3:
            continue
        observed = _pearson_correlation(left, right)
        null_values = np.empty(surrogate_count, dtype=float)
        for index in range(surrogate_count):
            shifted = np.roll(seeg_global, int(rng.integers(1, max_shift)))
            shifted_left, shifted_right = _lag_pair(eeg_gfp, shifted, lag)
            null_values[index] = _pearson_correlation(shifted_left, shifted_right)
        rows.append(
            {
                "patient_id": patient_id,
                "metric_definition": metric_definition,
                "weighting_strategy": weighting_strategy,
                "network_scope": network_scope,
                "lag_samples": int(lag),
                "lag_ms": int(round(lag * sample_period_sec * 1000.0)),
                "n_samples": int(left.size),
                "n_networks_used": n_networks_used,
                "observed_coupling": float(observed),
                "null_mean_coupling": float(null_values.mean()),
                "effect_mean_diff": float(observed - null_values.mean()),
                "p_perm": float((np.sum(null_values >= observed) + 1) / (surrogate_count + 1)),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def compute_subject_peak_centered_global_trajectory(
    peak_df: pd.DataFrame,
    aligned_df: pd.DataFrame,
    *,
    patient_id: str,
    window_sec: float,
    sample_period_sec: float,
    n_surrogates: int,
    seed: int,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "metric_definition",
        "weighting_strategy",
        "network_scope",
        "offset_samples",
        "offset_ms",
        "n_events",
        "n_networks_used",
        "observed_coupling",
        "null_mean_coupling",
        "effect_mean_diff",
        "p_perm",
    ]
    if peak_df.empty or aligned_df.empty or sample_period_sec <= 0.0:
        return pd.DataFrame(columns=columns)
    event_map = pd.merge_asof(
        peak_df.sort_values("event_sec")[["event_sec"]].copy(),
        aligned_df.sort_values("time_sec").reset_index(drop=True).reset_index(names="trace_index")[["trace_index", "time_sec"]].copy(),
        left_on="event_sec",
        right_on="time_sec",
        direction="nearest",
        tolerance=sample_period_sec / 2.0 + 0.002,
    ).dropna(subset=["trace_index"])
    indices = event_map["trace_index"].to_numpy(dtype=int)
    if indices.size == 0:
        return pd.DataFrame(columns=columns)
    global_trace = aligned_df["global_metric"].to_numpy(dtype=float)
    metric_definition = str(aligned_df["metric_definition"].iloc[0])
    weighting_strategy = str(aligned_df["weighting_strategy"].iloc[0])
    network_scope = str(aligned_df["network_scope"].iloc[0])
    n_networks_used = int(aligned_df["n_networks_used"].iloc[0])
    window_samples = max(1, int(round(float(window_sec) / sample_period_sec)))
    offsets = np.arange(-window_samples, window_samples + 1, dtype=int)
    surrogate_count = max(1, int(n_surrogates))
    max_shift = max(2, global_trace.size)
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []

    def _collect(trace: np.ndarray, offset_samples: int) -> np.ndarray:
        locations = indices + int(offset_samples)
        valid = locations[(locations >= 0) & (locations < trace.size)]
        if valid.size == 0:
            return np.empty(0, dtype=float)
        return trace[valid]

    for offset in offsets.tolist():
        observed_values = _collect(global_trace, offset)
        if observed_values.size == 0:
            continue
        observed = float(observed_values.mean())
        null_values = np.empty(surrogate_count, dtype=float)
        for index in range(surrogate_count):
            shifted = np.roll(global_trace, int(rng.integers(1, max_shift)))
            shifted_values = _collect(shifted, offset)
            null_values[index] = float(shifted_values.mean()) if shifted_values.size else 0.0
        null_mean = float(null_values.mean())
        deviations = np.abs(null_values - null_mean)
        observed_deviation = abs(observed - null_mean)
        rows.append(
            {
                "patient_id": patient_id,
                "metric_definition": metric_definition,
                "weighting_strategy": weighting_strategy,
                "network_scope": network_scope,
                "offset_samples": int(offset),
                "offset_ms": int(round(offset * sample_period_sec * 1000.0)),
                "n_events": int(observed_values.size),
                "n_networks_used": n_networks_used,
                "observed_coupling": observed,
                "null_mean_coupling": null_mean,
                "effect_mean_diff": float(observed - null_mean),
                "p_perm": float((np.sum(deviations >= observed_deviation) + 1) / (surrogate_count + 1)),
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


def compute_subject_gfp_controlled_microstate_profiles(
    aligned_df: pd.DataFrame,
    *,
    patient_id: str,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "global_metric_label",
        "metric_definition",
        "weighting_strategy",
        "network_scope",
        "microstate",
        "adjusted_global_metric",
        "raw_global_metric",
        "n_state_samples",
        "mean_state_gfp",
        "gfp_beta",
        "n_networks_used",
    ]
    if aligned_df.empty:
        return pd.DataFrame(columns=columns)
    data = aligned_df[np.isfinite(aligned_df["gfp"]) & np.isfinite(aligned_df["global_metric"]) & (aligned_df["microstate"] >= 0)].copy()
    if data.empty:
        return pd.DataFrame(columns=columns)
    states = sorted(data["microstate"].unique().tolist())
    if len(states) < 2:
        return pd.DataFrame(columns=columns)
    y = data["global_metric"].to_numpy(dtype=float)
    centered_gfp = data["gfp"].to_numpy(dtype=float) - float(data["gfp"].mean())
    dummy_matrix = np.column_stack([(data["microstate"].to_numpy(dtype=int) == state).astype(float) for state in states[1:]])
    coefficients = _fit_linear_model(y, centered_gfp, dummy_matrix)
    intercept = float(coefficients[0])
    gfp_beta = float(coefficients[1])
    rows: list[dict[str, object]] = []
    metric_definition = str(data["metric_definition"].iloc[0])
    weighting_strategy = str(data["weighting_strategy"].iloc[0])
    network_scope = str(data["network_scope"].iloc[0])
    n_networks_used = int(data["n_networks_used"].iloc[0])
    metric_label = global_metric_label(metric_definition, weighting_strategy)
    for state_index, state in enumerate(states):
        state_mask = data["microstate"] == state
        adjusted_value = intercept if state_index == 0 else intercept + float(coefficients[state_index + 1])
        rows.append(
            {
                "patient_id": patient_id,
                "global_metric_label": metric_label,
                "metric_definition": metric_definition,
                "weighting_strategy": weighting_strategy,
                "network_scope": network_scope,
                "microstate": int(state),
                "adjusted_global_metric": float(adjusted_value),
                "raw_global_metric": float(data.loc[state_mask, "global_metric"].mean()),
                "n_state_samples": int(state_mask.sum()),
                "mean_state_gfp": float(data.loc[state_mask, "gfp"].mean()),
                "gfp_beta": gfp_beta,
                "n_networks_used": n_networks_used,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def compute_subject_gfp_controlled_transition_effects(
    transition_df: pd.DataFrame,
    aligned_df: pd.DataFrame,
    *,
    patient_id: str,
    window_sec: float,
    sample_period_sec: float,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "global_metric_label",
        "metric_definition",
        "weighting_strategy",
        "network_scope",
        "from_state",
        "to_state",
        "n_events",
        "n_samples",
        "pre_value",
        "post_value",
        "effect_mean_diff",
        "gfp_beta",
        "n_networks_used",
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
    metric_definition = str(trace["metric_definition"].iloc[0])
    weighting_strategy = str(trace["weighting_strategy"].iloc[0])
    network_scope = str(trace["network_scope"].iloc[0])
    n_networks_used = int(trace["n_networks_used"].iloc[0])
    metric_label = global_metric_label(metric_definition, weighting_strategy)
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
        y = model_df["global_metric"].to_numpy(dtype=float)
        centered_gfp = model_df["gfp"].to_numpy(dtype=float) - float(model_df["gfp"].mean())
        post_indicator = model_df["post_indicator"].to_numpy(dtype=float)
        coefficients = _fit_linear_model(y, centered_gfp, post_indicator)
        intercept = float(coefficients[0])
        gfp_beta = float(coefficients[1])
        post_beta = float(coefficients[2])
        rows.append(
            {
                "patient_id": patient_id,
                "global_metric_label": metric_label,
                "metric_definition": metric_definition,
                "weighting_strategy": weighting_strategy,
                "network_scope": network_scope,
                "from_state": int(from_state),
                "to_state": int(to_state),
                "n_events": int(group.shape[0]),
                "n_samples": int(model_df.shape[0]),
                "pre_value": intercept,
                "post_value": intercept + post_beta,
                "effect_mean_diff": post_beta,
                "gfp_beta": gfp_beta,
                "n_networks_used": n_networks_used,
            }
        )
    return pd.DataFrame(rows, columns=columns)
