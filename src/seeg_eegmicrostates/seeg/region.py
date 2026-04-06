from __future__ import annotations

import pandas as pd


def aggregate_channel_dataframe_by_region(
    channel_df: pd.DataFrame,
    mapping_df: pd.DataFrame,
    *,
    patient_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid = mapping_df[mapping_df["valid_same_region"]].copy()
    if valid.empty:
        return pd.DataFrame({"time_sec": channel_df["time_sec"]}), pd.DataFrame(
            columns=["patient_id", "region", "n_bipolar_channels"]
        )
    region_series: dict[str, pd.Series] = {}
    coverage_rows: list[dict[str, object]] = []
    for region, group in valid.groupby("region"):
        channels = [channel for channel in group["bipolar_channel"] if channel in channel_df.columns]
        if not channels:
            continue
        region_series[str(region)] = channel_df[channels].mean(axis=1)
        coverage_rows.append(
            {
                "patient_id": patient_id,
                "region": str(region),
                "n_bipolar_channels": len(channels),
            }
        )
    region_df = pd.DataFrame({"time_sec": channel_df["time_sec"]})
    for region in sorted(region_series):
        region_df[region] = region_series[region]
    coverage_df = pd.DataFrame(coverage_rows)
    return region_df, coverage_df
