from __future__ import annotations

import pandas as pd


def aggregate_channel_dataframe_by_network(
    channel_df: pd.DataFrame,
    mapping_df: pd.DataFrame,
    *,
    patient_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid = mapping_df[mapping_df["valid_same_network"]].copy()
    if valid.empty:
        return pd.DataFrame({"time_sec": channel_df["time_sec"]}), pd.DataFrame(
            columns=["patient_id", "network", "n_bipolar_channels"]
        )
    network_series: dict[str, pd.Series] = {}
    coverage_rows: list[dict[str, object]] = []
    for network, group in valid.groupby("network"):
        channels = [channel for channel in group["bipolar_channel"] if channel in channel_df.columns]
        if not channels:
            continue
        network_series[str(network)] = channel_df[channels].mean(axis=1)
        coverage_rows.append(
            {
                "patient_id": patient_id,
                "network": str(network),
                "n_bipolar_channels": len(channels),
            }
        )
    network_df = pd.DataFrame({"time_sec": channel_df["time_sec"]})
    for network in sorted(network_series):
        network_df[network] = network_series[network]
    coverage_df = pd.DataFrame(coverage_rows)
    return network_df, coverage_df
