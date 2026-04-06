from __future__ import annotations

import numpy as np
import pandas as pd

from seeg_eegmicrostates.coupling import (
    compute_subject_microstate_connectivity_profiles,
    compute_subject_microstate_region_profiles,
)
from seeg_eegmicrostates.stats import (
    run_group_profile_omnibus_statistics,
    run_group_profile_posthoc_statistics,
)


def test_compute_subject_microstate_region_profiles_returns_four_state_means() -> None:
    aligned = pd.DataFrame(
        {
            "patient_id": ["sub-01"] * 8,
            "time_sec": np.arange(8, dtype=float) / 10.0,
            "microstate": [0, 0, 1, 1, 2, 2, 3, 3],
            "corr": np.ones(8, dtype=float),
            "region": ["Right Hippocampus"] * 8,
            "value": [1.0, 3.0, 2.0, 4.0, 5.0, 7.0, 6.0, 8.0],
        }
    )

    profiles = compute_subject_microstate_region_profiles(aligned)

    assert profiles["microstate"].tolist() == [0, 1, 2, 3]
    assert profiles["state_mean"].tolist() == [2.0, 3.0, 6.0, 7.0]
    assert profiles["n_state_samples"].tolist() == [2, 2, 2, 2]


def test_compute_subject_microstate_connectivity_profiles_returns_statewise_connectivity() -> None:
    aligned = pd.DataFrame(
        {
            "patient_id": ["sub-01"] * 16,
            "time_sec": np.arange(16, dtype=float) / 10.0,
            "microstate": np.repeat([0, 1, 2, 3], 4),
            "corr": np.ones(16, dtype=float),
            "Right Hippocampus": np.tile([0.0, 1.0, 0.0, 1.0], 4),
            "Right Amygdala": np.tile([0.0, 1.0, 0.0, 1.0], 4),
            "Left Hippocampus": np.tile([1.0, 0.0, -1.0, 0.0], 4),
        }
    )

    profiles = compute_subject_microstate_connectivity_profiles(aligned, min_samples=4, method="corr")

    pair = profiles[
        (profiles["microstate"] == 0)
        & (profiles["region_a"] == "Right Hippocampus")
        & (profiles["region_b"] == "Right Amygdala")
    ].iloc[0]
    assert pair["method"] == "corr"
    assert pair["state_connectivity"] == 1.0
    assert pair["n_state_samples"] == 4


def test_run_group_profile_omnibus_statistics_detects_state_dependence() -> None:
    profiles = pd.DataFrame(
        {
            "patient_id": np.repeat([f"sub-{index:02d}" for index in range(1, 9)], 4),
            "region": ["Right Hippocampus"] * 32,
            "microstate": list(np.tile([0, 1, 2, 3], 8)),
            "state_mean": list(np.tile([0.0, 0.0, 2.0, 2.0], 8)),
        }
    )

    omnibus = run_group_profile_omnibus_statistics(
        profiles,
        group_keys=["region"],
        value_column="state_mean",
        seed=7,
        min_subjects=4,
    )

    row = omnibus.iloc[0]
    assert row["region"] == "Right Hippocampus"
    assert row["n_subjects"] == 8
    assert row["statistic"] > 0.0
    assert row["p_perm"] < 0.05


def test_run_group_profile_posthoc_statistics_detects_pairwise_difference() -> None:
    profiles = pd.DataFrame(
        {
            "patient_id": np.repeat([f"sub-{index:02d}" for index in range(1, 9)], 4),
            "region": ["Right Hippocampus"] * 32,
            "microstate": list(np.tile([0, 1, 2, 3], 8)),
            "state_mean": list(np.tile([0.0, 1.0, 0.0, 1.0], 8)),
        }
    )

    posthoc = run_group_profile_posthoc_statistics(
        profiles,
        group_keys=["region"],
        value_column="state_mean",
        seed=11,
        min_subjects=4,
    )

    row = posthoc[
        (posthoc["region"] == "Right Hippocampus")
        & (posthoc["microstate_a"] == 0)
        & (posthoc["microstate_b"] == 1)
    ].iloc[0]
    assert row["n_subjects"] == 8
    assert row["mean_effect"] == 1.0
    assert row["p_perm"] < 0.05
