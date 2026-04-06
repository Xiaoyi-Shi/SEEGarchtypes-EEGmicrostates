from __future__ import annotations

import pandas as pd


def _label_from_value(value: object) -> str | None:
    if pd.isna(value):
        return None
    normalized = str(value).strip()
    if not normalized or normalized.upper() == "N/A":
        return None
    return normalized


def _network_from_schaefer_label(label: str) -> str:
    head = label.split()[0]
    return head.split("_", 1)[0]


def _region_from_label(value: object, *, parcellation_name: str) -> str | None:
    label = _label_from_value(value)
    if label is None:
        return None
    if str(parcellation_name).strip().lower() in {"yeo7", "yeo17"}:
        return _network_from_schaefer_label(label)
    return label


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
    parcellation_name: str = "aal3",
) -> pd.DataFrame:
    label_map = dict(zip(atlas_df["Channel"], atlas_df[atlas_column], strict=False))
    rows: list[dict[str, object]] = []
    for bipolar_channel in bipolar_names:
        parsed = _parse_bipolar_channel(bipolar_channel)
        if parsed is None:
            continue
        contact_a, contact_b = parsed
        region_a = _region_from_label(label_map.get(contact_a), parcellation_name=parcellation_name)
        region_b = _region_from_label(label_map.get(contact_b), parcellation_name=parcellation_name)
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
                "parcellation_name": parcellation_name,
            }
        )
    return pd.DataFrame(rows)
