from __future__ import annotations

import numpy as np
import pandas as pd

from seeg_eegmicrostates._utils import contiguous_runs
from seeg_eegmicrostates.coupling.exploratory import build_state_transition_table


SEIZURE_IDENTIFIER_COLUMNS: tuple[str, ...] = (
    "patient_id",
    "seizure_id",
    "seizure_type",
    "recording_state",
    "stage",
    "stage_order",
    "segment_id",
)


def _sample_period_sec(times: np.ndarray) -> float:
    if times.size < 2:
        return 0.0
    return float(np.median(np.diff(np.sort(times.astype(float)))))


def _duration_sec(times: np.ndarray) -> float:
    if times.size == 0:
        return 0.0
    if times.size == 1:
        return 0.0
    return max(0.0, float(np.max(times) - np.min(times)))


def summarize_stage_state_metrics(
    label_df: pd.DataFrame,
    *,
    state_column: str,
    metric_family: str,
    state_output_column: str | None = None,
) -> pd.DataFrame:
    output_state = state_output_column or state_column
    columns = [
        *SEIZURE_IDENTIFIER_COLUMNS,
        "metric_family",
        output_state,
        "occupancy",
        "mean_dwell_sec",
        "n_samples",
        "n_runs",
        "occurrence_per_min",
        "mean_confidence",
    ]
    if label_df.empty:
        return pd.DataFrame(columns=columns)
    rows: list[dict[str, object]] = []
    grouped = label_df.dropna(subset=[state_column]).groupby(list(SEIZURE_IDENTIFIER_COLUMNS), dropna=False, sort=True)
    for keys, group in grouped:
        identifiers = dict(zip(SEIZURE_IDENTIFIER_COLUMNS, keys, strict=False))
        labels = group[state_column].to_numpy(dtype=int)
        times = group["time_sec"].to_numpy(dtype=float)
        if labels.size == 0:
            continue
        sample_period = _sample_period_sec(times)
        duration = max(_duration_sec(times), float(labels.size) * sample_period)
        runs = contiguous_runs(labels)
        confidence_column = "corr" if "corr" in group.columns else "assignment_similarity"
        for state in sorted(set(labels.tolist())):
            state_mask = labels == int(state)
            dwell_lengths = [end - start for start, end, label in runs if int(label) == int(state)]
            state_confidence = group.loc[state_mask, confidence_column] if confidence_column in group.columns else pd.Series(dtype=float)
            row = {
                **identifiers,
                "metric_family": metric_family,
                output_state: int(state),
                "occupancy": float(np.mean(state_mask)),
                "mean_dwell_sec": float(np.mean(dwell_lengths) * sample_period) if dwell_lengths else 0.0,
                "n_samples": int(state_mask.sum()),
                "n_runs": int(len(dwell_lengths)),
                "occurrence_per_min": float(len(dwell_lengths) / duration * 60.0) if duration > 0.0 else 0.0,
                "mean_confidence": float(state_confidence.dropna().mean()) if not state_confidence.dropna().empty else float("nan"),
            }
            rows.append(row)
    return pd.DataFrame(rows, columns=columns)


def summarize_stage_transition_metrics(
    label_df: pd.DataFrame,
    *,
    state_column: str,
    metric_family: str,
) -> pd.DataFrame:
    columns = [
        *SEIZURE_IDENTIFIER_COLUMNS,
        "metric_family",
        "from_state",
        "to_state",
        "n_transitions",
        "transition_probability",
    ]
    if label_df.empty:
        return pd.DataFrame(columns=columns)
    rows: list[dict[str, object]] = []
    for keys, group in label_df.dropna(subset=[state_column]).groupby(list(SEIZURE_IDENTIFIER_COLUMNS), dropna=False, sort=True):
        identifiers = dict(zip(SEIZURE_IDENTIFIER_COLUMNS, keys, strict=False))
        transition_input = group[["time_sec", state_column]].rename(columns={state_column: "microstate"})
        transitions = build_state_transition_table(transition_input, patient_id=str(identifiers["segment_id"]))
        if transitions.empty:
            continue
        source_counts = transitions.groupby("from_state").size()
        for (from_state, to_state), transition_group in transitions.groupby(["from_state", "to_state"], sort=True):
            total = int(source_counts.loc[int(from_state)])
            rows.append(
                {
                    **identifiers,
                    "metric_family": metric_family,
                    "from_state": int(from_state),
                    "to_state": int(to_state),
                    "n_transitions": int(transition_group.shape[0]),
                    "transition_probability": float(transition_group.shape[0] / total) if total else 0.0,
                }
            )
    return pd.DataFrame(rows, columns=columns)


def summarize_eeg_gfp_by_microstate(label_df: pd.DataFrame, gfp_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        *SEIZURE_IDENTIFIER_COLUMNS,
        "microstate",
        "n_samples",
        "mean_gfp",
        "median_gfp",
        "max_gfp",
    ]
    if label_df.empty or gfp_df.empty:
        return pd.DataFrame(columns=columns)
    merged = label_df.merge(
        gfp_df[[*SEIZURE_IDENTIFIER_COLUMNS, "sample", "gfp"]],
        on=[*SEIZURE_IDENTIFIER_COLUMNS, "sample"],
        how="left",
    )
    rows: list[dict[str, object]] = []
    for keys, group in merged.dropna(subset=["microstate"]).groupby([*SEIZURE_IDENTIFIER_COLUMNS, "microstate"], dropna=False, sort=True):
        *identifier_values, microstate = keys
        identifiers = dict(zip(SEIZURE_IDENTIFIER_COLUMNS, identifier_values, strict=False))
        gfp = group["gfp"].dropna()
        rows.append(
            {
                **identifiers,
                "microstate": int(microstate),
                "n_samples": int(group.shape[0]),
                "mean_gfp": float(gfp.mean()) if not gfp.empty else float("nan"),
                "median_gfp": float(gfp.median()) if not gfp.empty else float("nan"),
                "max_gfp": float(gfp.max()) if not gfp.empty else float("nan"),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def summarize_paired_state_relationships(
    aligned_df: pd.DataFrame,
    *,
    field_column: str = "assigned_archetype",
) -> pd.DataFrame:
    columns = [
        *SEIZURE_IDENTIFIER_COLUMNS,
        "field_metric",
        "field_state",
        "microstate",
        "n_samples",
        "joint_probability",
        "p_microstate_given_field",
        "p_field_given_microstate",
    ]
    if aligned_df.empty:
        return pd.DataFrame(columns=columns)
    data = aligned_df.dropna(subset=[field_column, "microstate"]).copy()
    if data.empty:
        return pd.DataFrame(columns=columns)
    rows: list[dict[str, object]] = []
    for keys, group in data.groupby(list(SEIZURE_IDENTIFIER_COLUMNS), dropna=False, sort=True):
        identifiers = dict(zip(SEIZURE_IDENTIFIER_COLUMNS, keys, strict=False))
        total = float(group.shape[0])
        field_totals = group.groupby(field_column).size()
        micro_totals = group.groupby("microstate").size()
        for (field_state, microstate), pair in group.groupby([field_column, "microstate"], sort=True):
            n_samples = int(pair.shape[0])
            rows.append(
                {
                    **identifiers,
                    "field_metric": field_column,
                    "field_state": int(field_state),
                    "microstate": int(microstate),
                    "n_samples": n_samples,
                    "joint_probability": float(n_samples / total) if total else 0.0,
                    "p_microstate_given_field": float(n_samples / int(field_totals.loc[field_state])),
                    "p_field_given_microstate": float(n_samples / int(micro_totals.loc[microstate])),
                }
            )
    return pd.DataFrame(rows, columns=columns)


def summarize_stage_denominators(
    *,
    segments: pd.DataFrame,
    recording_index: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "metric_family",
        "stage",
        "stage_order",
        "n_patients",
        "n_recordings",
        "n_segments",
        "n_usable_segments",
    ]
    if segments.empty:
        return pd.DataFrame(columns=columns)
    indexed = segments.merge(
        recording_index[
            [
                "patient_id",
                "recording_state",
                "eligible_seeg_stage",
                "eligible_paired_eeg_seeg",
            ]
        ],
        on=["patient_id", "recording_state"],
        how="left",
    )
    families = {
        "seeg_stage": indexed["eligible_seeg_stage"].fillna(False),
        "paired_eeg_seeg": indexed["eligible_paired_eeg_seeg"].fillna(False),
        "eeg_microstate": indexed["eligible_paired_eeg_seeg"].fillna(False),
    }
    rows: list[dict[str, object]] = []
    for metric_family, mask in families.items():
        family = indexed[mask].copy()
        for (stage, stage_order), group in family.groupby(["stage", "stage_order"], sort=True):
            usable = group[group["usable_segment"]]
            rows.append(
                {
                    "metric_family": metric_family,
                    "stage": str(stage),
                    "stage_order": int(stage_order),
                    "n_patients": int(usable["patient_id"].nunique()),
                    "n_recordings": int(usable[["patient_id", "recording_state"]].drop_duplicates().shape[0]),
                    "n_segments": int(group.shape[0]),
                    "n_usable_segments": int(usable.shape[0]),
                }
            )
    return pd.DataFrame(rows, columns=columns)


def patient_level_mean(table: pd.DataFrame, *, value_columns: list[str], extra_keys: list[str]) -> pd.DataFrame:
    if table.empty:
        return pd.DataFrame(columns=["patient_id", *extra_keys, *value_columns, "n_seizures"])
    keys = ["patient_id", *extra_keys]
    aggregations = {column: (column, "mean") for column in value_columns if column in table.columns}
    grouped = (
        table.groupby(keys, dropna=False, as_index=False)
        .agg(**aggregations, n_seizures=("recording_state", "nunique"))
        .reset_index(drop=True)
    )
    return grouped
