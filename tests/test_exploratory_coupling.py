from __future__ import annotations

import pandas as pd

from seeg_eegmicrostates.coupling import (
    build_microstate_event_table,
    build_state_transition_table,
    compute_subject_event_locked_region_effects,
    compute_subject_windowed_region_coupling,
    compute_windowed_region_metrics,
    compute_windowed_state_metrics,
)
from seeg_eegmicrostates.stats import run_group_scalar_statistics


def test_event_and_transition_tables_follow_contiguous_microstate_runs() -> None:
    labels = pd.DataFrame(
        {
            "time_sec": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
            "microstate": [0, 0, 1, 1, 1, 0],
        }
    )
    events = build_microstate_event_table(labels, patient_id="sub-01")
    transitions = build_state_transition_table(labels, patient_id="sub-01")

    assert len(events) == 6
    assert set(events["event_type"]) == {"onset", "offset"}
    assert pd.isna(events.loc[(events["event_type"] == "onset") & (events["event_sec"] == 0.0), "previous_state"]).iloc[0]
    assert transitions[["from_state", "to_state"]].to_dict(orient="records") == [
        {"from_state": 0, "to_state": 1},
        {"from_state": 1, "to_state": 0},
    ]


def test_event_locked_region_effects_compute_pre_post_means() -> None:
    event_df = pd.DataFrame({"event_sec": [0.2, 0.4], "microstate": [1, 0]})
    region_df = pd.DataFrame(
        {
            "time_sec": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
            "Right Hippocampus": [0.0, 0.0, 1.0, 1.0, 2.0, 2.0],
            "Right Amygdala": [2.0, 2.0, 1.0, 1.0, 0.0, 0.0],
        }
    )

    event_effects, summary = compute_subject_event_locked_region_effects(
        event_df,
        region_df,
        patient_id="sub-01",
        window_sec=0.2,
        event_keys=("microstate",),
    )

    hippocampus = summary[(summary["microstate"] == 1) & (summary["region"] == "Right Hippocampus")].iloc[0]
    amygdala = summary[(summary["microstate"] == 1) & (summary["region"] == "Right Amygdala")].iloc[0]
    assert len(event_effects) == 4
    assert hippocampus["pre_value"] == 0.0
    assert hippocampus["post_value"] == 1.0
    assert hippocampus["effect_mean_diff"] == 1.0
    assert amygdala["effect_mean_diff"] == -1.0


def test_windowed_metrics_support_subject_level_coupling_estimates() -> None:
    label_df = pd.DataFrame(
        {
            "time_sec": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
            "microstate": [0, 0, 1, 1, 0, 1],
        }
    )
    region_df = pd.DataFrame(
        {
            "time_sec": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
            "Right Hippocampus": [0.0, 0.0, 1.0, 1.0, 0.2, 0.9],
            "Right Amygdala": [1.0, 1.0, 0.0, 0.0, 0.8, 0.1],
        }
    )

    state_windows = compute_windowed_state_metrics(label_df, patient_id="sub-01", window_sec=2.0, step_sec=1.0)
    region_windows = compute_windowed_region_metrics(region_df, patient_id="sub-01", window_sec=2.0, step_sec=1.0)
    coupling = compute_subject_windowed_region_coupling(state_windows, region_windows)

    hippocampus = coupling[(coupling["microstate"] == 1) & (coupling["region"] == "Right Hippocampus")].iloc[0]
    assert state_windows["window_start_sec"].nunique() == 5
    assert region_windows["region"].nunique() == 2
    assert hippocampus["n_windows"] >= 3
    assert hippocampus["effect_mean_diff"] > 0


def test_group_scalar_statistics_respect_minimum_subject_support() -> None:
    subject_summary = pd.DataFrame(
        {
            "patient_id": ["sub-01", "sub-02", "sub-03"],
            "from_state": [0, 0, 1],
            "to_state": [1, 1, 2],
            "region": ["Right Hippocampus", "Right Hippocampus", "Right Amygdala"],
            "effect_mean_diff": [0.2, 0.4, 0.9],
        }
    )

    group_df = run_group_scalar_statistics(
        subject_summary,
        group_keys=["from_state", "to_state", "region"],
        value_column="effect_mean_diff",
        seed=42,
        min_subjects=2,
    )

    assert len(group_df) == 1
    assert group_df.iloc[0]["from_state"] == 0
    assert group_df.iloc[0]["to_state"] == 1
    assert group_df.iloc[0]["region"] == "Right Hippocampus"
    assert group_df.iloc[0]["n_subjects"] == 2
