from __future__ import annotations

import math

import pandas as pd


def _coerce_positive(value: object) -> float | None:
    if pd.isna(value):
        return None
    number = float(value)
    if math.isnan(number) or number < 0:
        return None
    return number


def build_state_segments(annotation_info: pd.DataFrame, analysis_state: str = "IDE_A") -> pd.DataFrame:
    state_name = str(analysis_state).strip().upper()
    prefix, suffix = state_name.split("_", 1)
    matched = annotation_info[
        (annotation_info["status1"].astype(str) == prefix) & (annotation_info["status2"].astype(str) == suffix)
    ].copy()
    rows: list[dict[str, object]] = []
    for row in matched.to_dict(orient="records"):
        start_sec = _coerce_positive(row.get("rest_start"))
        end_sec = _coerce_positive(row.get("rest_end"))
        duration_sec = _coerce_positive(row.get("rest_during"))
        if end_sec is None and start_sec is not None and duration_sec is not None:
            end_sec = start_sec + duration_sec
        if duration_sec is None and start_sec is not None and end_sec is not None:
            duration_sec = end_sec - start_sec
        usable = start_sec is not None and end_sec is not None and duration_sec is not None and duration_sec > 0
        rows.append(
            {
                "patient_id": str(row["ID"]),
                "state": state_name,
                "start_sec": start_sec if usable else pd.NA,
                "end_sec": end_sec if usable else pd.NA,
                "duration_sec": duration_sec if usable else pd.NA,
                "usable_segment": usable,
            }
        )
    return pd.DataFrame(rows)


def build_ide_a_segments(annotation_info: pd.DataFrame) -> pd.DataFrame:
    return build_state_segments(annotation_info, "IDE_A")
