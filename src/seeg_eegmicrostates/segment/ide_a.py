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


def build_ide_a_segments(annotation_info: pd.DataFrame) -> pd.DataFrame:
    ide_a = annotation_info[
        (annotation_info["status1"].astype(str) == "IDE") & (annotation_info["status2"].astype(str) == "A")
    ].copy()
    rows: list[dict[str, object]] = []
    for row in ide_a.to_dict(orient="records"):
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
                "state": "IDE_A",
                "start_sec": start_sec if usable else pd.NA,
                "end_sec": end_sec if usable else pd.NA,
                "duration_sec": duration_sec if usable else pd.NA,
                "usable_segment": usable,
            }
        )
    return pd.DataFrame(rows)
