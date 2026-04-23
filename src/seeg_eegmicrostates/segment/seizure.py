from __future__ import annotations

import math

import pandas as pd


SEIZURE_STAGE_ORDER: tuple[str, ...] = ("pre", "LVFA", "SZ", "post")
DEFAULT_TIMING_TOLERANCE_SEC = 1e-3


def _coerce_time(value: object) -> float | None:
    if pd.isna(value):
        return None
    number = float(value)
    if math.isnan(number):
        return None
    return number


def _patient_id(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _recording_state(status1: object, status2: object) -> str:
    return f"{str(status1).strip().upper()}_{str(status2).strip().upper()}"


def _append_reason(reasons: list[str], reason: str) -> None:
    if reason not in reasons:
        reasons.append(reason)


def _validate_stage_timing(
    *,
    start_sec: float | None,
    end_sec: float | None,
    duration_sec: float | None,
    timing_tolerance_sec: float,
) -> tuple[bool, str, float | None, bool, float]:
    reasons: list[str] = []
    tolerated = False
    mismatch_sec = float("nan")
    if start_sec is None or end_sec is None or duration_sec is None:
        _append_reason(reasons, "missing_stage_timing")
        return False, ";".join(reasons), duration_sec, tolerated, mismatch_sec
    if start_sec < 0.0 or end_sec < 0.0 or duration_sec < 0.0:
        _append_reason(reasons, "negative_stage_timing")
    measured_duration = end_sec - start_sec
    if measured_duration <= 0.0 or duration_sec <= 0.0:
        _append_reason(reasons, "non_positive_duration")
    mismatch_sec = abs(measured_duration - duration_sec)
    if math.isfinite(mismatch_sec) and mismatch_sec > 0.0:
        if mismatch_sec <= timing_tolerance_sec:
            tolerated = True
            _append_reason(reasons, "tolerated_duration_mismatch")
        else:
            _append_reason(reasons, "duration_mismatch")
    usable = not any(reason in {"missing_stage_timing", "negative_stage_timing", "non_positive_duration", "duration_mismatch"} for reason in reasons)
    return usable, ";".join(reasons) if reasons else "ok", measured_duration if usable else duration_sec, tolerated, mismatch_sec


def build_seizure_stage_segments(
    annotation_info: pd.DataFrame,
    *,
    timing_tolerance_sec: float = DEFAULT_TIMING_TOLERANCE_SEC,
) -> pd.DataFrame:
    """Materialize one row per seizure-stage interval from workbook annotations."""

    columns = [
        "patient_id",
        "seizure_id",
        "seizure_type",
        "recording_state",
        "stage",
        "stage_order",
        "start_sec",
        "end_sec",
        "duration_sec",
        "usable_segment",
        "qc_reason",
        "timing_tolerance_sec",
        "timing_mismatch_sec",
        "timing_tolerance_applied",
    ]
    if annotation_info.empty:
        return pd.DataFrame(columns=columns)
    seizure_rows = annotation_info[
        annotation_info["status1"].astype(str).str.strip().str.upper().str.startswith("SZ", na=False)
    ].copy()
    rows: list[dict[str, object]] = []
    for source in seizure_rows.to_dict(orient="records"):
        patient_id = _patient_id(source.get("ID"))
        seizure_id = str(source.get("status1")).strip().upper()
        seizure_type = str(source.get("status2")).strip().upper()
        recording_state = _recording_state(seizure_id, seizure_type)
        previous_end: float | None = None
        for stage_order, stage in enumerate(SEIZURE_STAGE_ORDER):
            prefix = stage
            start_sec = _coerce_time(source.get(f"{prefix}_start"))
            duration_sec = _coerce_time(source.get(f"{prefix}_during"))
            end_sec = _coerce_time(source.get(f"{prefix}_end"))
            usable, qc_reason, resolved_duration, tolerated, mismatch_sec = _validate_stage_timing(
                start_sec=start_sec,
                end_sec=end_sec,
                duration_sec=duration_sec,
                timing_tolerance_sec=timing_tolerance_sec,
            )
            reasons = [] if qc_reason == "ok" else qc_reason.split(";")
            if previous_end is not None and start_sec is not None:
                boundary_delta = start_sec - previous_end
                if boundary_delta < -timing_tolerance_sec:
                    _append_reason(reasons, "stage_order_overlap")
                    usable = False
                elif abs(boundary_delta) <= timing_tolerance_sec and boundary_delta != 0.0:
                    _append_reason(reasons, "tolerated_stage_boundary_mismatch")
                    tolerated = True
            rows.append(
                {
                    "patient_id": patient_id,
                    "seizure_id": seizure_id,
                    "seizure_type": seizure_type,
                    "recording_state": recording_state,
                    "stage": stage,
                    "stage_order": stage_order,
                    "start_sec": start_sec if usable else pd.NA,
                    "end_sec": end_sec if usable else pd.NA,
                    "duration_sec": resolved_duration if usable else pd.NA,
                    "usable_segment": bool(usable),
                    "qc_reason": ";".join(reasons) if reasons else "ok",
                    "timing_tolerance_sec": float(timing_tolerance_sec),
                    "timing_mismatch_sec": mismatch_sec,
                    "timing_tolerance_applied": bool(tolerated),
                }
            )
            if end_sec is not None:
                previous_end = end_sec
    return pd.DataFrame(rows, columns=columns)


def seizure_recording_states(segments: pd.DataFrame) -> pd.DataFrame:
    columns = ["patient_id", "seizure_id", "seizure_type", "recording_state"]
    if segments.empty:
        return pd.DataFrame(columns=columns)
    return (
        segments[columns]
        .drop_duplicates()
        .sort_values(["patient_id", "seizure_id", "seizure_type"])
        .reset_index(drop=True)
    )
