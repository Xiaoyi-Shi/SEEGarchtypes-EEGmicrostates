from __future__ import annotations

import pandas as pd


def _network_from_label(value: object) -> str | None:
    if pd.isna(value):
        return None
    return str(value).split("_")[0]


def _parse_bipolar_channel(name: str) -> tuple[str, str] | None:
    if "-" not in name:
        return None
    left, right = name.split("-", 1)
    return left, right


def build_same_network_bipolar_map(
    atlas_df: pd.DataFrame,
    bipolar_names: list[str],
    *,
    patient_id: str,
    atlas_column: str = "cortex_319663V:Schaefer_200_17net",
) -> pd.DataFrame:
    label_map = dict(zip(atlas_df["Channel"], atlas_df[atlas_column], strict=False))
    rows: list[dict[str, object]] = []
    for bipolar_channel in bipolar_names:
        parsed = _parse_bipolar_channel(bipolar_channel)
        if parsed is None:
            continue
        contact_a, contact_b = parsed
        network_a = _network_from_label(label_map.get(contact_a))
        network_b = _network_from_label(label_map.get(contact_b))
        valid = network_a is not None and network_a == network_b
        rows.append(
            {
                "patient_id": patient_id,
                "bipolar_channel": bipolar_channel,
                "contact_a": contact_a,
                "contact_b": contact_b,
                "network_a": network_a,
                "network_b": network_b,
                "network": network_a if valid else pd.NA,
                "valid_same_network": valid,
                "atlas_column": atlas_column,
            }
        )
    return pd.DataFrame(rows)
