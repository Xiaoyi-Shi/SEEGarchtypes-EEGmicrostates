from __future__ import annotations

import numpy as np
import pandas as pd

from seeg_eegmicrostates.stats.subject_level import cohen_d


def compute_subject_microstate_network_effects(aligned_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (patient_id, network), group in aligned_df.groupby(["patient_id", "network"]):
        values = group["value"].to_numpy(dtype=float)
        labels = group["microstate"].to_numpy(dtype=int)
        for microstate in sorted(group["microstate"].unique()):
            on_values = values[labels == microstate]
            off_values = values[labels != microstate]
            if on_values.size == 0 or off_values.size == 0:
                continue
            rows.append(
                {
                    "patient_id": patient_id,
                    "network": network,
                    "microstate": int(microstate),
                    "effect_mean_diff": float(on_values.mean() - off_values.mean()),
                    "effect_cohens_d": float(cohen_d(on_values, off_values)),
                    "n_state_samples": int(on_values.size),
                    "n_nonstate_samples": int(off_values.size),
                }
            )
    return pd.DataFrame(rows)


def _greedy_state_mapping(contingency: pd.DataFrame) -> dict[int, int]:
    mapping: dict[int, int] = {}
    for eeg_state, group in contingency.groupby("eeg_state"):
        best = group.sort_values("count", ascending=False).iloc[0]
        mapping[int(eeg_state)] = int(best["seeg_state"])
    return mapping


def compute_cross_modal_state_summaries(
    aligned_states_df: pd.DataFrame,
    *,
    lag_window_samples: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    contingency = (
        aligned_states_df.groupby(["patient_id", "eeg_state", "seeg_state"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )
    summary_rows: list[dict[str, object]] = []
    for patient_id, group in aligned_states_df.groupby("patient_id"):
        patient_contingency = contingency[contingency["patient_id"] == patient_id]
        mapping = _greedy_state_mapping(patient_contingency)
        eeg = group["eeg_state"].to_numpy(dtype=int)
        seeg = group["seeg_state"].to_numpy(dtype=int)
        mapped = np.array([mapping.get(label, -1) for label in eeg], dtype=int)
        exact_overlap = float(np.mean(mapped == seeg)) if seeg.size else 0.0
        best_lag = 0
        best_overlap = exact_overlap
        for lag in range(-lag_window_samples, lag_window_samples + 1):
            if lag == 0:
                continue
            if lag > 0:
                compare_left = mapped[:-lag]
                compare_right = seeg[lag:]
            else:
                compare_left = mapped[-lag:]
                compare_right = seeg[:lag]
            if compare_left.size == 0:
                continue
            overlap = float(np.mean(compare_left == compare_right))
            if overlap > best_overlap:
                best_overlap = overlap
                best_lag = lag
        summary_rows.append(
            {
                "patient_id": patient_id,
                "overlap": exact_overlap,
                "best_lag_samples": int(best_lag),
                "best_lag_overlap": float(best_overlap),
            }
        )
    return contingency, pd.DataFrame(summary_rows)
