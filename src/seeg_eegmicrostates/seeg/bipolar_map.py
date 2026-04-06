from __future__ import annotations

import pandas as pd


def _region_from_label(value: object) -> str | None:
    if pd.isna(value):
        return None
    normalized = str(value).strip()
    if not normalized or normalized.upper() == "N/A":
        return None
    return normalized


def _parse_bipolar_channel(name: str) -> tuple[str, str] | None:
    if "-" not in name:
        return None
    left, right = name.split("-", 1)
    return left, right


def build_same_region_bipolar_map(
    atlas_df: pd.DataFrame,
    bipolar_names: list[str],
    *,
    patient_id: str,
    atlas_column: str = "AAL3",
) -> pd.DataFrame:
    label_map = dict(zip(atlas_df["Channel"], atlas_df[atlas_column], strict=False))
    rows: list[dict[str, object]] = []
    for bipolar_channel in bipolar_names:
        parsed = _parse_bipolar_channel(bipolar_channel)
        if parsed is None:
            continue
        contact_a, contact_b = parsed
        region_a = _region_from_label(label_map.get(contact_a))
        region_b = _region_from_label(label_map.get(contact_b))
        valid = region_a is not None and region_a == region_b
        rows.append(
            {
                "patient_id": patient_id,
                "bipolar_channel": bipolar_channel,
                "contact_a": contact_a,
                "contact_b": contact_b,
                "region_a": region_a,
                "region_b": region_b,
                "region": region_a if valid else pd.NA,
                "valid_same_region": valid,
                "atlas_column": atlas_column,
            }
        )
    return pd.DataFrame(rows)
