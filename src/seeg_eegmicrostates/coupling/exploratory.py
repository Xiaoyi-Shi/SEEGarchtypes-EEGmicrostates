from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from seeg_eegmicrostates._utils import contiguous_runs


def _region_columns(region_df: pd.DataFrame) -> list[str]:
    return [column for column in region_df.columns if column != "time_sec"]


def build_microstate_event_table(label_df: pd.DataFrame, *, patient_id: str) -> pd.DataFrame:
    if label_df.empty:
        return pd.DataFrame(
            columns=[
                "patient_id",
                "event_id",
                "event_type",
                "event_sec",
                "microstate",
                "previous_state",
                "next_state",
                "start_sec",
                "end_sec",
                "duration_sec",
                "n_samples",
            ]
        )
    sorted_df = label_df.sort_values("time_sec").reset_index(drop=True)
    times = sorted_df["time_sec"].to_numpy(dtype=float)
    labels = sorted_df["microstate"].to_numpy(dtype=int)
    rows: list[dict[str, object]] = []
    for event_index, (start, end, label) in enumerate(contiguous_runs(labels)):
        start_sec = float(times[start])
        end_sec = float(times[end - 1])
        duration_sec = max(0.0, float(end_sec - start_sec))
        previous_state = int(labels[start - 1]) if start > 0 else pd.NA
        next_state = int(labels[end]) if end < labels.size else pd.NA
        rows.append(
            {
                "patient_id": patient_id,
                "event_id": event_index,
                "event_type": "onset",
                "event_sec": start_sec,
                "microstate": int(label),
                "previous_state": previous_state,
                "next_state": next_state,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "duration_sec": duration_sec,
                "n_samples": int(end - start),
            }
        )
        rows.append(
            {
                "patient_id": patient_id,
                "event_id": event_index,
                "event_type": "offset",
                "event_sec": end_sec,
                "microstate": int(label),
                "previous_state": previous_state,
                "next_state": next_state,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "duration_sec": duration_sec,
                "n_samples": int(end - start),
            }
        )
    return pd.DataFrame(rows)


def build_state_transition_table(label_df: pd.DataFrame, *, patient_id: str) -> pd.DataFrame:
    if label_df.empty:
        return pd.DataFrame(
            columns=[
                "patient_id",
                "transition_id",
                "event_sec",
                "from_state",
                "to_state",
                "from_start_sec",
                "from_end_sec",
                "to_start_sec",
                "to_end_sec",
                "from_duration_sec",
                "to_duration_sec",
            ]
        )
    sorted_df = label_df.sort_values("time_sec").reset_index(drop=True)
    times = sorted_df["time_sec"].to_numpy(dtype=float)
    labels = sorted_df["microstate"].to_numpy(dtype=int)
    runs = contiguous_runs(labels)
    rows: list[dict[str, object]] = []
    for transition_id in range(1, len(runs)):
        previous_start, previous_end, previous_state = runs[transition_id - 1]
        current_start, current_end, current_state = runs[transition_id]
        previous_start_sec = float(times[previous_start])
        previous_end_sec = float(times[previous_end - 1])
        current_start_sec = float(times[current_start])
        current_end_sec = float(times[current_end - 1])
        rows.append(
            {
                "patient_id": patient_id,
                "transition_id": transition_id - 1,
                "event_sec": current_start_sec,
                "from_state": int(previous_state),
                "to_state": int(current_state),
                "from_start_sec": previous_start_sec,
                "from_end_sec": previous_end_sec,
                "to_start_sec": current_start_sec,
                "to_end_sec": current_end_sec,
                "from_duration_sec": max(0.0, float(previous_end_sec - previous_start_sec)),
                "to_duration_sec": max(0.0, float(current_end_sec - current_start_sec)),
            }
        )
    return pd.DataFrame(rows)


def compute_subject_event_locked_region_effects(
    event_df: pd.DataFrame,
    region_df: pd.DataFrame,
    *,
    patient_id: str,
    window_sec: float,
    event_keys: Iterable[str],
    event_time_column: str = "event_sec",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    columns = list(event_keys)
    event_columns = ["patient_id", *columns, "region", "pre_value", "post_value", "effect_mean_diff"]
    summary_columns = ["patient_id", *columns, "region", "n_events", "pre_value", "post_value", "effect_mean_diff"]
    if event_df.empty or region_df.empty:
        return pd.DataFrame(columns=event_columns), pd.DataFrame(columns=summary_columns)
    region_columns = _region_columns(region_df)
    if not region_columns:
        return pd.DataFrame(columns=event_columns), pd.DataFrame(columns=summary_columns)
    rows: list[dict[str, object]] = []
    for event in event_df.itertuples(index=False):
        event_sec = float(getattr(event, event_time_column))
        pre = region_df[(region_df["time_sec"] >= event_sec - window_sec) & (region_df["time_sec"] < event_sec)]
        post = region_df[(region_df["time_sec"] >= event_sec) & (region_df["time_sec"] < event_sec + window_sec)]
        if pre.empty or post.empty:
            continue
        for region in region_columns:
            row = {
                "patient_id": patient_id,
                "region": region,
                "pre_value": float(pre[region].mean()),
                "post_value": float(post[region].mean()),
            }
            row["effect_mean_diff"] = float(row["post_value"] - row["pre_value"])
            for key in columns:
                row[key] = getattr(event, key)
            rows.append(row)
    event_effects = pd.DataFrame(rows, columns=event_columns)
    if event_effects.empty:
        return event_effects, pd.DataFrame(columns=summary_columns)
    summary = (
        event_effects.groupby(["patient_id", *columns, "region"], as_index=False)
        .agg(
            n_events=("effect_mean_diff", "size"),
            pre_value=("pre_value", "mean"),
            post_value=("post_value", "mean"),
            effect_mean_diff=("effect_mean_diff", "mean"),
        )
        .reset_index(drop=True)
    )
    return event_effects, summary


def compute_windowed_state_metrics(
    label_df: pd.DataFrame,
    *,
    patient_id: str,
    window_sec: float,
    step_sec: float | None = None,
) -> pd.DataFrame:
    if label_df.empty:
        return pd.DataFrame(
            columns=["patient_id", "window_start_sec", "window_end_sec", "microstate", "occupancy", "mean_dwell_sec", "n_samples"]
        )
    sorted_df = label_df.sort_values("time_sec").reset_index(drop=True)
    times = sorted_df["time_sec"].to_numpy(dtype=float)
    labels = sorted_df["microstate"].to_numpy(dtype=int)
    sample_period = float(np.median(np.diff(times))) if times.size > 1 else 0.0
    step = float(step_sec or window_sec)
    unique_states = sorted(set(labels.tolist()))
    window_start = float(times.min())
    window_end_limit = float(times.max())
    rows: list[dict[str, object]] = []
    while window_start + window_sec <= window_end_limit + sample_period:
        window_end = window_start + window_sec
        mask = (times >= window_start) & (times < window_end)
        window_labels = labels[mask]
        if window_labels.size:
            runs = contiguous_runs(window_labels)
            for microstate in unique_states:
                dwell_samples = [end - start for start, end, label in runs if label == microstate]
                rows.append(
                    {
                        "patient_id": patient_id,
                        "window_start_sec": float(window_start),
                        "window_end_sec": float(window_end),
                        "microstate": int(microstate),
                        "occupancy": float(np.mean(window_labels == microstate)),
                        "mean_dwell_sec": float(np.mean(dwell_samples) * sample_period) if dwell_samples else 0.0,
                        "n_samples": int(window_labels.size),
                    }
                )
        window_start += step
    return pd.DataFrame(rows)


def compute_windowed_region_metrics(
    region_df: pd.DataFrame,
    *,
    patient_id: str,
    window_sec: float,
    step_sec: float | None = None,
) -> pd.DataFrame:
    if region_df.empty:
        return pd.DataFrame(columns=["patient_id", "window_start_sec", "window_end_sec", "region", "mean_value", "std_value", "n_samples"])
    sorted_df = region_df.sort_values("time_sec").reset_index(drop=True)
    times = sorted_df["time_sec"].to_numpy(dtype=float)
    region_columns = _region_columns(sorted_df)
    step = float(step_sec or window_sec)
    sample_period = float(np.median(np.diff(times))) if times.size > 1 else 0.0
    window_start = float(times.min())
    window_end_limit = float(times.max())
    rows: list[dict[str, object]] = []
    while window_start + window_sec <= window_end_limit + sample_period:
        window_end = window_start + window_sec
        mask = (times >= window_start) & (times < window_end)
        window = sorted_df.loc[mask]
        if not window.empty:
            for region in region_columns:
                rows.append(
                    {
                        "patient_id": patient_id,
                        "window_start_sec": float(window_start),
                        "window_end_sec": float(window_end),
                        "region": region,
                        "mean_value": float(window[region].mean()),
                        "std_value": float(window[region].std(ddof=0)) if window.shape[0] > 1 else 0.0,
                        "n_samples": int(window.shape[0]),
                    }
                )
        window_start += step
    return pd.DataFrame(rows)


def compute_subject_windowed_region_coupling(
    state_window_df: pd.DataFrame,
    region_window_df: pd.DataFrame,
) -> pd.DataFrame:
    if state_window_df.empty or region_window_df.empty:
        return pd.DataFrame(columns=["patient_id", "microstate", "region", "n_windows", "slope", "effect_mean_diff"])
    merged = state_window_df.merge(
        region_window_df,
        on=["patient_id", "window_start_sec", "window_end_sec"],
        how="inner",
    )
    rows: list[dict[str, object]] = []
    for (patient_id, microstate, region), group in merged.groupby(["patient_id", "microstate", "region"]):
        occupancy = group["occupancy"].to_numpy(dtype=float)
        values = group["mean_value"].to_numpy(dtype=float)
        if occupancy.size < 2:
            continue
        if float(np.nanstd(occupancy, ddof=0)) == 0.0 or float(np.nanstd(values, ddof=0)) == 0.0:
            continue
        rows.append(
            {
                "patient_id": str(patient_id),
                "microstate": int(microstate),
                "region": str(region),
                "n_windows": int(group.shape[0]),
                "slope": float(np.polyfit(occupancy, values, deg=1)[0]),
                "effect_mean_diff": float(np.corrcoef(occupancy, values)[0, 1]),
            }
        )
    return pd.DataFrame(rows)
