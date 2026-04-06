from __future__ import annotations

import pandas as pd


def align_region_timeseries_to_labels(
    label_df: pd.DataFrame,
    region_df: pd.DataFrame,
    *,
    patient_id: str,
    tolerance_ms: float = 5.0,
) -> pd.DataFrame:
    labels = label_df.sort_values("time_sec")[["time_sec", "microstate", "corr"]].copy()
    wide = region_df.sort_values("time_sec").copy()
    aligned = pd.merge_asof(
        wide,
        labels,
        on="time_sec",
        direction="nearest",
        tolerance=tolerance_ms / 1000.0,
    ).dropna(subset=["microstate"])
    aligned.insert(0, "patient_id", patient_id)
    aligned["microstate"] = aligned["microstate"].astype(int)
    return aligned.reset_index(drop=True)


def align_label_table_to_wide_region_timeseries(
    label_df: pd.DataFrame,
    region_df: pd.DataFrame,
    *,
    patient_id: str,
    tolerance_ms: float = 5.0,
) -> pd.DataFrame:
    labels = label_df.sort_values("time_sec")[["time_sec", "microstate", "corr"]].copy()
    aligned = pd.merge_asof(
        labels,
        region_df.sort_values("time_sec").copy(),
        on="time_sec",
        direction="nearest",
        tolerance=tolerance_ms / 1000.0,
    ).dropna()
    aligned.insert(0, "patient_id", patient_id)
    aligned["microstate"] = aligned["microstate"].astype(int)
    return aligned.reset_index(drop=True)


def align_label_table_to_region_timeseries(
    label_df: pd.DataFrame,
    region_df: pd.DataFrame,
    *,
    patient_id: str,
    tolerance_ms: float = 5.0,
) -> pd.DataFrame:
    aligned = align_label_table_to_wide_region_timeseries(
        label_df,
        region_df,
        patient_id=patient_id,
        tolerance_ms=tolerance_ms,
    )
    long = aligned.melt(
        id_vars=["patient_id", "time_sec", "microstate", "corr"],
        var_name="region",
        value_name="value",
    )
    return long.dropna(subset=["value"]).reset_index(drop=True)
