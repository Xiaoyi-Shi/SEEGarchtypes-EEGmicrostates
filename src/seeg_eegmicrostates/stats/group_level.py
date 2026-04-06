from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd

from seeg_eegmicrostates.stats.multiple_testing import benjamini_hochberg


def _sign_flip_p_value(values: np.ndarray, seed: int, n_permutations: int = 2048) -> float:
    if values.size == 0:
        return 1.0
    observed = abs(values.mean())
    rng = np.random.default_rng(seed)
    null_means = np.empty(n_permutations, dtype=float)
    for index in range(n_permutations):
        signs = rng.choice((-1.0, 1.0), size=values.size)
        null_means[index] = abs((values * signs).mean())
    return float((np.sum(null_means >= observed) + 1) / (n_permutations + 1))


def _repeated_measures_f_statistic(matrix: np.ndarray) -> float:
    if matrix.ndim != 2 or matrix.shape[0] < 2 or matrix.shape[1] < 2:
        return 0.0
    grand_mean = float(matrix.mean())
    subject_means = matrix.mean(axis=1, keepdims=True)
    state_means = matrix.mean(axis=0, keepdims=True)
    ss_state = float(matrix.shape[0] * np.sum((state_means - grand_mean) ** 2))
    ss_error = float(np.sum((matrix - subject_means - state_means + grand_mean) ** 2))
    df_state = matrix.shape[1] - 1
    df_error = (matrix.shape[0] - 1) * (matrix.shape[1] - 1)
    if df_state <= 0 or df_error <= 0:
        return 0.0
    ms_state = ss_state / df_state
    ms_error = ss_error / df_error
    if ms_error == 0.0:
        return 0.0 if ms_state == 0.0 else float("inf")
    return float(ms_state / ms_error)


def _within_subject_permutation_p_value(matrix: np.ndarray, seed: int, n_permutations: int = 2048) -> float:
    if matrix.ndim != 2 or matrix.shape[0] < 2 or matrix.shape[1] < 2:
        return 1.0
    observed = _repeated_measures_f_statistic(matrix)
    rng = np.random.default_rng(seed)
    null_values = np.empty(n_permutations, dtype=float)
    for index in range(n_permutations):
        permuted = np.empty_like(matrix)
        for row_index in range(matrix.shape[0]):
            permuted[row_index] = matrix[row_index, rng.permutation(matrix.shape[1])]
        null_values[index] = _repeated_measures_f_statistic(permuted)
    return float((np.sum(null_values >= observed) + 1) / (n_permutations + 1))
def run_group_scalar_statistics(
    summary_df: pd.DataFrame,
    *,
    group_keys: list[str],
    value_column: str,
    seed: int,
    min_subjects: int = 1,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if summary_df.empty:
        return pd.DataFrame(rows)
    if group_keys:
        iterator = enumerate(summary_df.groupby(group_keys))
    else:
        iterator = [(0, ((), summary_df))]
    for offset, (keys, group) in iterator:
        values = group[value_column].to_numpy(dtype=float)
        if values.size < min_subjects:
            continue
        if not isinstance(keys, tuple):
            keys = (keys,)
        row: dict[str, object] = {
            "n_subjects": int(values.size),
            "mean_effect": float(values.mean()) if values.size else 0.0,
            "median_effect": float(np.median(values)) if values.size else 0.0,
            "p_perm": _sign_flip_p_value(values, seed + offset),
        }
        for key, value in zip(group_keys, keys, strict=False):
            row[key] = value
        rows.append(row)
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["q_fdr"] = benjamini_hochberg(result["p_perm"])
    return result.sort_values(group_keys if group_keys else ["mean_effect"]).reset_index(drop=True)


def run_group_permutation_statistics(effect_df: pd.DataFrame, *, seed: int, min_subjects: int = 1) -> pd.DataFrame:
    return run_group_scalar_statistics(
        effect_df,
        group_keys=["microstate", "region"],
        value_column="effect_mean_diff",
        seed=seed,
        min_subjects=min_subjects,
    )


def run_group_connectivity_statistics(
    effect_df: pd.DataFrame,
    *,
    seed: int,
    min_subjects: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if effect_df.empty:
        return pd.DataFrame(rows)
    pair_a_key, pair_b_key = "region_a", "region_b"
    group_keys = ["microstate", "region_a", "region_b"]
    if "method" in effect_df.columns:
        group_keys = ["method", *group_keys]
    for offset, (keys, group) in enumerate(effect_df.groupby(group_keys)):
        if "method" in effect_df.columns:
            method, microstate, region_a, region_b = keys
        else:
            microstate, region_a, region_b = keys
            method = "corr"
        values = group["effect_mean_diff"].to_numpy(dtype=float)
        if values.size < min_subjects:
            continue
        rows.append(
            {
                "method": str(method),
                "microstate": int(microstate),
                pair_a_key: str(region_a),
                pair_b_key: str(region_b),
                "n_subjects": int(values.size),
                "mean_effect": float(values.mean()) if values.size else 0.0,
                "median_effect": float(np.median(values)) if values.size else 0.0,
                "mean_state_connectivity": float(group["state_connectivity"].mean()),
                "mean_off_connectivity": float(group["off_connectivity"].mean()),
                "p_perm": _sign_flip_p_value(values, seed + offset),
            }
        )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["q_fdr"] = benjamini_hochberg(result["p_perm"])
    return result.sort_values(["method", "microstate", pair_a_key, pair_b_key]).reset_index(drop=True)


def run_group_profile_omnibus_statistics(
    profile_df: pd.DataFrame,
    *,
    group_keys: list[str],
    value_column: str,
    seed: int,
    min_subjects: int,
    state_column: str = "microstate",
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if profile_df.empty:
        return pd.DataFrame(rows)
    states = sorted(profile_df[state_column].dropna().unique().tolist())
    if len(states) < 2:
        return pd.DataFrame(rows)
    for offset, (keys, group) in enumerate(profile_df.groupby(group_keys)):
        pivot = (
            group.pivot_table(index="patient_id", columns=state_column, values=value_column, aggfunc="mean")
            .reindex(columns=states)
            .dropna()
        )
        if pivot.shape[0] < min_subjects:
            continue
        matrix = pivot.to_numpy(dtype=float)
        if not isinstance(keys, tuple):
            keys = (keys,)
        row: dict[str, object] = {
            "n_subjects": int(matrix.shape[0]),
            "statistic": float(_repeated_measures_f_statistic(matrix)),
            "p_perm": _within_subject_permutation_p_value(matrix, seed + offset),
        }
        for key, value in zip(group_keys, keys, strict=False):
            row[key] = value
        for state in states:
            row[f"mean_state_{int(state)}"] = float(pivot[state].mean())
        rows.append(row)
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["q_fdr"] = benjamini_hochberg(result["p_perm"])
    return result.sort_values(group_keys if group_keys else ["statistic"]).reset_index(drop=True)


def run_group_profile_posthoc_statistics(
    profile_df: pd.DataFrame,
    *,
    group_keys: list[str],
    value_column: str,
    seed: int,
    min_subjects: int,
    state_column: str = "microstate",
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if profile_df.empty:
        return pd.DataFrame(rows)
    states = sorted(profile_df[state_column].dropna().unique().tolist())
    if len(states) < 2:
        return pd.DataFrame(rows)
    for offset, (keys, group) in enumerate(profile_df.groupby(group_keys)):
        pivot = group.pivot_table(index="patient_id", columns=state_column, values=value_column, aggfunc="mean").reindex(columns=states)
        if not isinstance(keys, tuple):
            keys = (keys,)
        for pair_offset, (state_a, state_b) in enumerate(combinations(states, 2)):
            pair_frame = pivot[[state_a, state_b]].dropna()
            if pair_frame.shape[0] < min_subjects:
                continue
            differences = pair_frame[state_b].to_numpy(dtype=float) - pair_frame[state_a].to_numpy(dtype=float)
            row: dict[str, object] = {
                "n_subjects": int(pair_frame.shape[0]),
                "microstate_a": int(state_a),
                "microstate_b": int(state_b),
                "mean_state_a": float(pair_frame[state_a].mean()),
                "mean_state_b": float(pair_frame[state_b].mean()),
                "mean_effect": float(differences.mean()),
                "median_effect": float(np.median(differences)),
                "p_perm": _sign_flip_p_value(differences, seed + offset * 31 + pair_offset),
            }
            for key, value in zip(group_keys, keys, strict=False):
                row[key] = value
            rows.append(row)
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["q_fdr"] = benjamini_hochberg(result["p_perm"])
    sort_keys = [*group_keys, "microstate_a", "microstate_b"] if group_keys else ["microstate_a", "microstate_b"]
    return result.sort_values(sort_keys).reset_index(drop=True)
