from __future__ import annotations

import pandas as pd


def summarize_network_mapping(mapping_df: pd.DataFrame) -> pd.DataFrame:
    if mapping_df.empty:
        return pd.DataFrame(columns=["patient_id", "network", "n_channels"])
    valid = mapping_df[mapping_df["valid_same_network"]].copy()
    if valid.empty:
        return pd.DataFrame(columns=["patient_id", "network", "n_channels"])
    summary = (
        valid.groupby(["patient_id", "network"], as_index=False)["bipolar_channel"]
        .count()
        .rename(columns={"bipolar_channel": "n_channels"})
    )
    return summary.sort_values(["patient_id", "network"]).reset_index(drop=True)
