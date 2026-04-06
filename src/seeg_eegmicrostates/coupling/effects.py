from __future__ import annotations

import pandas as pd

from seeg_eegmicrostates.stats.subject_level import cohen_d


def compute_subject_microstate_region_effects(aligned_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (patient_id, region), group in aligned_df.groupby(["patient_id", "region"]):
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
                    "region": region,
                    "microstate": int(microstate),
                    "effect_mean_diff": float(on_values.mean() - off_values.mean()),
                    "effect_cohens_d": float(cohen_d(on_values, off_values)),
                    "n_state_samples": int(on_values.size),
                    "n_nonstate_samples": int(off_values.size),
                }
            )
    return pd.DataFrame(rows)


def compute_subject_microstate_region_profiles(aligned_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if aligned_df.empty:
        return pd.DataFrame(columns=["patient_id", "region", "microstate", "state_mean", "state_std", "n_state_samples"])
    for (patient_id, region, microstate), group in aligned_df.groupby(["patient_id", "region", "microstate"]):
        values = group["value"].to_numpy(dtype=float)
        if values.size == 0:
            continue
        rows.append(
            {
                "patient_id": str(patient_id),
                "region": str(region),
                "microstate": int(microstate),
                "state_mean": float(values.mean()),
                "state_std": float(values.std(ddof=0)) if values.size > 1 else 0.0,
                "n_state_samples": int(values.size),
            }
        )
    return pd.DataFrame(rows)
