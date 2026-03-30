from __future__ import annotations

import pandas as pd


def align_network_timeseries_to_labels(
    label_df: pd.DataFrame,
    network_df: pd.DataFrame,
    *,
    patient_id: str,
    tolerance_ms: float = 5.0,
) -> pd.DataFrame:
    labels = label_df.sort_values("time_sec")[["time_sec", "microstate", "corr"]].copy()
    wide = network_df.sort_values("time_sec").copy()
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


def align_label_table_to_wide_network_timeseries(
    label_df: pd.DataFrame,
    network_df: pd.DataFrame,
    *,
    patient_id: str,
    tolerance_ms: float = 5.0,
) -> pd.DataFrame:
    labels = label_df.sort_values("time_sec")[["time_sec", "microstate", "corr"]].copy()
    aligned = pd.merge_asof(
        labels,
        network_df.sort_values("time_sec").copy(),
        on="time_sec",
        direction="nearest",
        tolerance=tolerance_ms / 1000.0,
    ).dropna()
    aligned.insert(0, "patient_id", patient_id)
    aligned["microstate"] = aligned["microstate"].astype(int)
    return aligned.reset_index(drop=True)


def align_label_table_to_network_timeseries(
    label_df: pd.DataFrame,
    network_df: pd.DataFrame,
    *,
    patient_id: str,
    tolerance_ms: float = 5.0,
) -> pd.DataFrame:
    aligned = align_label_table_to_wide_network_timeseries(
        label_df,
        network_df,
        patient_id=patient_id,
        tolerance_ms=tolerance_ms,
    )
    long = aligned.melt(
        id_vars=["patient_id", "time_sec", "microstate", "corr"],
        var_name="network",
        value_name="value",
    )
    return long.dropna(subset=["value"]).reset_index(drop=True)


def align_modal_microstates(
    eeg_labels_df: pd.DataFrame,
    seeg_labels_df: pd.DataFrame,
    *,
    patient_id: str,
    tolerance_ms: float = 5.0,
) -> pd.DataFrame:
    eeg = eeg_labels_df.sort_values("time_sec")[["time_sec", "microstate"]].rename(columns={"microstate": "eeg_state"})
    seeg = seeg_labels_df.sort_values("time_sec")[["time_sec", "microstate"]].rename(columns={"microstate": "seeg_state"})
    aligned = pd.merge_asof(
        eeg,
        seeg,
        on="time_sec",
        direction="nearest",
        tolerance=tolerance_ms / 1000.0,
    ).dropna()
    aligned.insert(0, "patient_id", patient_id)
    aligned["eeg_state"] = aligned["eeg_state"].astype(int)
    aligned["seeg_state"] = aligned["seeg_state"].astype(int)
    return aligned.reset_index(drop=True)
