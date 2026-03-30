from __future__ import annotations

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


def run_group_permutation_statistics(effect_df: pd.DataFrame, *, seed: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (microstate, network), group in effect_df.groupby(["microstate", "network"]):
        values = group["effect_mean_diff"].to_numpy(dtype=float)
        rows.append(
            {
                "microstate": int(microstate),
                "network": str(network),
                "n_subjects": int(values.size),
                "mean_effect": float(values.mean()) if values.size else 0.0,
                "median_effect": float(np.median(values)) if values.size else 0.0,
                "p_perm": _sign_flip_p_value(values, seed + int(microstate)),
            }
        )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["q_fdr"] = benjamini_hochberg(result["p_perm"])
    return result.sort_values(["microstate", "network"]).reset_index(drop=True)


def run_group_connectivity_statistics(
    effect_df: pd.DataFrame,
    *,
    seed: int,
    min_subjects: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if effect_df.empty:
        return pd.DataFrame(rows)
    group_keys = ["microstate", "network_a", "network_b"]
    if "method" in effect_df.columns:
        group_keys = ["method", *group_keys]
    for offset, (keys, group) in enumerate(effect_df.groupby(group_keys)):
        if "method" in effect_df.columns:
            method, microstate, network_a, network_b = keys
        else:
            microstate, network_a, network_b = keys
            method = "corr"
        values = group["effect_mean_diff"].to_numpy(dtype=float)
        if values.size < min_subjects:
            continue
        rows.append(
            {
                "method": str(method),
                "microstate": int(microstate),
                "network_a": str(network_a),
                "network_b": str(network_b),
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
    return result.sort_values(["method", "microstate", "network_a", "network_b"]).reset_index(drop=True)
