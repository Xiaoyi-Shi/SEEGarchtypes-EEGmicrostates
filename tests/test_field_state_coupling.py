from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from seeg_eegmicrostates._utils import read_dataframe, write_dataframe
from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.coupling import (
    align_eeg_and_field_state_labels,
    align_eeg_topography_to_archetypes,
    compute_subject_archetype_conditioned_eeg_maps,
    compute_subject_archetype_state_preference,
    compute_subject_archetype_template_similarity,
    compute_subject_field_state_coupling,
    compute_subject_field_state_to_eeg_switching,
    compute_subject_gfp_controlled_field_state_to_eeg_switching,
    compute_subject_gfp_controlled_field_state_profiles,
    compute_subject_transition_field_state_coupling,
    derive_group_field_state_archetypes,
    derive_seeg_field_state_artifacts,
    project_field_state_templates_to_common_space,
    summarize_group_archetype_conditioned_eeg_maps,
    summarize_group_archetype_template_similarity,
    summarize_group_field_state_model_order,
    summarize_subject_field_state_model_order,
)
from seeg_eegmicrostates.workflows import pipelines


def _eeg_labels() -> pd.DataFrame:
    times = [index * 0.004 for index in range(16)]
    return pd.DataFrame(
        {
            "patient_id": ["sub-01"] * 16,
            "time_sec": times,
            "sample": list(range(16)),
            "microstate": [0, 0, 1, 1, 2, 2, 3, 3, 0, 0, 1, 1, 2, 2, 3, 3],
            "corr": [0.9] * 16,
        }
    )


def _gfp_trace() -> pd.DataFrame:
    times = [index * 0.004 for index in range(16)]
    values = [0.1, 0.4, 0.8, 0.7, 0.2, 0.6, 0.9, 0.8, 0.2, 0.5, 0.9, 0.7, 0.3, 0.6, 1.0, 0.8]
    return pd.DataFrame(
        {
            "patient_id": ["sub-01"] * 16,
            "time_sec": times,
            "sample": list(range(16)),
            "gfp": values,
        }
    )


def _eeg_topography_trace() -> pd.DataFrame:
    times = [index * 0.004 for index in range(16)]
    archetype_a = [0.8, 0.6, -0.5, -0.7]
    archetype_b = [-0.6, -0.7, 0.8, 0.5]
    rows = [archetype_a if index % 4 < 2 else archetype_b for index in range(16)]
    return pd.DataFrame(
        {
            "patient_id": ["sub-01"] * 16,
            "time_sec": times,
            "sample": list(range(16)),
            "Fp1": [row[0] for row in rows],
            "Fp2": [row[1] for row in rows],
            "F3": [row[2] for row in rows],
            "F4": [row[3] for row in rows],
        }
    )


def _archetype_assignments() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "patient_id": ["sub-01", "sub-01"],
            "field_state": [0, 1],
            "peak_metric": ["rms", "rms"],
            "normalization": ["zscore", "zscore"],
            "n_states": [2, 2],
            "min_duration_ms": [4, 4],
            "comparison_space": ["yeo17", "yeo17"],
            "assigned_archetype": [0, 1],
            "assignment_similarity": [0.9, 0.85],
            "orientation_sign": [1.0, 1.0],
        }
    )


def _eeg_template_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "microstate": [0, 1],
            "Fp1": [0.8, -0.6],
            "Fp2": [0.6, -0.7],
            "F3": [-0.5, 0.8],
            "F4": [-0.7, 0.5],
        }
    )


def _eeg_transitions() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "patient_id": ["sub-01", "sub-01", "sub-01"],
            "transition_id": [0, 1, 2],
            "event_sec": [0.008, 0.024, 0.04],
            "from_state": [0, 1, 2],
            "to_state": [1, 2, 3],
            "from_start_sec": [0.0, 0.016, 0.032],
            "from_end_sec": [0.004, 0.02, 0.036],
            "to_start_sec": [0.008, 0.024, 0.04],
            "to_end_sec": [0.012, 0.028, 0.044],
            "from_duration_sec": [0.004, 0.004, 0.004],
            "to_duration_sec": [0.004, 0.004, 0.004],
        }
    )


def _channel_signals() -> pd.DataFrame:
    times = [index * 0.004 for index in range(16)]
    patterns = [
        [0.0, 0.0, 0.0, 0.0],
        [2.0, -1.0, -2.0, 1.0],
        [0.0, 0.0, 0.0, 0.0],
        [-2.0, 1.0, 2.0, -1.0],
        [0.0, 0.0, 0.0, 0.0],
        [1.0, 2.0, -1.0, -2.0],
        [0.0, 0.0, 0.0, 0.0],
        [-1.0, -2.0, 1.0, 2.0],
        [0.0, 0.0, 0.0, 0.0],
        [2.2, -1.1, -2.2, 1.1],
        [0.0, 0.0, 0.0, 0.0],
        [-2.2, 1.1, 2.2, -1.1],
        [0.0, 0.0, 0.0, 0.0],
        [1.2, 2.1, -1.2, -2.1],
        [0.0, 0.0, 0.0, 0.0],
        [-1.2, -2.1, 1.2, 2.1],
    ]
    return pd.DataFrame(
        {
            "time_sec": times,
            "bp1": [row[0] for row in patterns],
            "bp2": [row[1] for row in patterns],
            "bp3": [row[2] for row in patterns],
            "bp4": [row[3] for row in patterns],
        }
    )


def _atlas_table() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Channel": ["A1", "A2", "B1", "B2"],
            "AAL3": ["Frontal", "Frontal", "Temporal", "Temporal"],
            "cortex_319663V:Schaefer_200_17net": ["DefaultA_01", "DefaultA_02", "ContA_01", "ContA_02"],
        }
    )


def _subject_template_df(patient_id: str, *, sign_flip_first: bool = False) -> pd.DataFrame:
    first = [-1.0, -0.9, 0.8, 0.7] if sign_flip_first else [1.0, 0.9, -0.8, -0.7]
    second = [0.7, 0.6, 1.0, 0.9]
    return pd.DataFrame(
        {
            "patient_id": [patient_id, patient_id],
            "field_state": [0, 1],
            "peak_metric": ["rms", "rms"],
            "normalization": ["zscore", "zscore"],
            "n_states": [2, 2],
            "min_duration_ms": [4, 4],
            "n_channels": [4, 4],
            "n_peak_maps": [8, 8],
            "A1-A2": [first[0], second[0]],
            "A2-A1": [first[1], second[1]],
            "B1-B2": [first[2], second[2]],
            "B2-B1": [first[3], second[3]],
        }
    )


def _field_artifacts(cfg: AnalysisConfig) -> dict[str, pd.DataFrame]:
    return derive_seeg_field_state_artifacts(
        _channel_signals(),
        patient_id="sub-01",
        peak_metric="rms",
        normalization="zscore",
        n_states=2,
        min_duration_ms=4,
        min_peak_distance_ms=4,
        seed=cfg.random_seed,
    )


def test_derive_seeg_field_state_artifacts_returns_templates_labels_and_profiles(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    artifacts = _field_artifacts(cfg)

    assert not artifacts["trace"].empty
    assert not artifacts["peaks"].empty
    assert not artifacts["peak_maps"].empty
    assert not artifacts["templates"].empty
    assert not artifacts["labels"].empty
    assert not artifacts["profiles"].empty
    assert not artifacts["transition_profiles"].empty
    assert artifacts["templates"]["field_state"].nunique() == 2


def test_subject_field_state_model_order_summary_reports_fit_and_stability(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    artifacts = _field_artifacts(cfg)
    peak_maps = artifacts["peak_maps"].copy()
    peak_maps["foreign_patient_only_channel"] = float("nan")

    summary = summarize_subject_field_state_model_order(
        peak_maps,
        artifacts["templates"],
        artifacts["profiles"],
        patient_id="sub-01",
        stability_seed=cfg.random_seed,
    )

    assert summary.loc[0, "n_states"] == 2
    assert summary.loc[0, "mean_template_fit"] > 0.0
    assert summary.loc[0, "split_half_stability"] > 0.0
    assert summary.loc[0, "min_state_occupancy"] > 0.0
    assert summary.loc[0, "min_state_peak_fraction"] > 0.0


def test_group_field_state_model_order_summary_aggregates_subject_support() -> None:
    subject_df = pd.DataFrame(
        {
            "patient_id": ["sub-01", "sub-02", "sub-01", "sub-02"],
            "peak_metric": ["rms"] * 4,
            "normalization": ["zscore"] * 4,
            "n_states": [2, 2, 4, 4],
            "min_duration_ms": [4] * 4,
            "fit_gain_from_prev_k": [pd.NA, pd.NA, 0.05, 0.04],
            "mean_template_fit": [0.80, 0.82, 0.85, 0.86],
            "split_half_stability": [0.70, 0.72, 0.78, 0.79],
            "min_state_occupancy": [0.40, 0.38, 0.20, 0.18],
            "min_state_peak_fraction": [0.41, 0.39, 0.19, 0.17],
            "occupancy_entropy": [0.98, 0.97, 0.92, 0.91],
        }
    )

    summary = summarize_group_field_state_model_order(subject_df, retained_k=4)

    assert summary["n_states"].tolist() == [2, 4]
    assert summary.loc[summary["n_states"] == 4, "retained_main_text_default"].iloc[0]
    assert summary.loc[summary["n_states"] == 4, "n_subjects"].iloc[0] == 2
    assert summary.loc[summary["n_states"] == 4, "median_fit_gain_from_prev_k"].iloc[0] > 0.0


def test_sign_flipped_peak_maps_match_the_same_field_state(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    peak_maps = _field_artifacts(cfg)["peak_maps"].sort_values("sample").reset_index(drop=True)

    label_a = int(peak_maps.loc[0, "field_state"])
    label_a_flipped = int(peak_maps.loc[1, "field_state"])
    label_b = int(peak_maps.loc[2, "field_state"])
    label_b_flipped = int(peak_maps.loc[3, "field_state"])

    assert label_a == label_a_flipped
    assert label_b == label_b_flipped
    assert label_a != label_b


def test_project_field_state_templates_to_common_space_and_archetypes_are_sign_invariant() -> None:
    mapping = pd.DataFrame(
        {
            "patient_id": ["sub-01", "sub-01", "sub-01", "sub-01"],
            "bipolar_channel": ["A1-A2", "A2-A1", "B1-B2", "B2-B1"],
            "region": ["DefaultA", "DefaultA", "ContA", "ContA"],
            "valid_same_region": [True, True, True, True],
        }
    )
    first = project_field_state_templates_to_common_space(
        _subject_template_df("sub-01", sign_flip_first=False),
        mapping,
        patient_id="sub-01",
        comparison_space="yeo17",
    )
    second = project_field_state_templates_to_common_space(
        _subject_template_df("sub-02", sign_flip_first=True),
        mapping.assign(patient_id="sub-02"),
        patient_id="sub-02",
        comparison_space="yeo17",
    )

    projections = pd.concat([first, second], ignore_index=True)
    summaries = derive_group_field_state_archetypes(
        projections,
        comparison_space="yeo17",
        n_states=2,
        seed=42,
        min_subjects=2,
    )

    assert set(summaries["assignments"]["assigned_archetype"]) == {0, 1}
    assert summaries["support"]["n_subjects"].tolist() == [2, 2]
    assert not summaries["archetypes"].empty


def test_derive_group_field_state_archetypes_filters_sparse_support() -> None:
    projections = pd.DataFrame(
        {
            "patient_id": ["sub-01", "sub-01", "sub-02", "sub-02"],
            "field_state": [0, 1, 0, 1],
            "peak_metric": ["rms"] * 4,
            "normalization": ["zscore"] * 4,
            "n_states": [2] * 4,
            "min_duration_ms": [4] * 4,
            "n_channels": [2] * 4,
            "n_peak_maps": [8] * 4,
            "comparison_space": ["yeo17"] * 4,
            "orientation_sign": [1.0] * 4,
            "n_mapped_channels": [4] * 4,
            "n_common_units": [2] * 4,
            "DefaultA": [1.0, 0.7, 1.0, 0.7],
            "ContA": [-1.0, 0.9, -1.0, 0.9],
        }
    )

    summaries = derive_group_field_state_archetypes(
        projections,
        comparison_space="yeo17",
        n_states=2,
        seed=42,
        min_subjects=3,
    )

    assert summaries["archetypes"].empty
    assert summaries["support"].empty


def test_compute_subject_field_state_coupling_supports_zero_lag_and_grid(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    aligned = align_eeg_and_field_state_labels(
        _eeg_labels(),
        _field_artifacts(cfg)["labels"],
        patient_id="sub-01",
    )
    effects = compute_subject_field_state_coupling(
        aligned,
        patient_id="sub-01",
        lag_samples=[-1, 0, 1],
        sample_period_sec=0.004,
        n_surrogates=8,
        seed=cfg.random_seed,
    )

    assert sorted(effects["lag_ms"].tolist()) == [-4, 0, 4]
    assert set(effects.columns) >= {"peak_metric", "normalization", "observed_coupling", "effect_mean_diff"}


def test_compute_subject_transition_field_state_coupling_returns_switch_and_destination_rows(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    effects = compute_subject_transition_field_state_coupling(
        _eeg_transitions(),
        _field_artifacts(cfg)["labels"],
        patient_id="sub-01",
        window_sec=0.012,
        n_surrogates=8,
        seed=cfg.random_seed,
    )

    assert set(effects["response_kind"]) == {"any-switch", "destination-state"}
    assert not effects.empty


def test_compute_subject_field_state_to_eeg_switching_returns_switch_and_destination_rows(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    effects = compute_subject_field_state_to_eeg_switching(
        _field_artifacts(cfg)["labels"],
        _eeg_labels(),
        patient_id="sub-01",
        window_sec=0.012,
        n_surrogates=8,
        seed=cfg.random_seed,
    )

    assert set(effects["response_kind"]) == {"any-switch", "destination-state"}
    assert not effects.empty


def test_compute_subject_gfp_controlled_field_state_profiles_returns_adjusted_switch_rates(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    aligned = pipelines.align_eeg_gfp_and_field_state_labels(
        _eeg_labels(),
        _gfp_trace(),
        _field_artifacts(cfg)["labels"],
        patient_id="sub-01",
    )
    profiles = compute_subject_gfp_controlled_field_state_profiles(aligned, patient_id="sub-01")

    assert set(profiles.columns) >= {"microstate", "adjusted_switch_rate", "raw_switch_rate", "gfp_beta"}
    assert not profiles.empty


def test_compute_subject_gfp_controlled_field_state_to_eeg_switching_returns_adjusted_switch_rates(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    artifacts = _field_artifacts(cfg)
    aligned = pipelines.align_eeg_gfp_and_field_state_labels(
        _eeg_labels(),
        _gfp_trace(),
        artifacts["labels"],
        patient_id="sub-01",
    )
    transitions = pipelines.build_state_transition_table(
        artifacts["labels"].rename(columns={"field_state": "microstate"})[["time_sec", "microstate"]],
        patient_id="sub-01",
    )
    effects = compute_subject_gfp_controlled_field_state_to_eeg_switching(
        transitions,
        aligned,
        patient_id="sub-01",
        window_sec=0.012,
        sample_period_sec=0.004,
    )

    assert set(effects.columns) >= {"from_state", "to_state", "effect_mean_diff", "gfp_beta"}
    assert not effects.empty


def test_align_eeg_topography_to_archetypes_and_conditioned_maps(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    aligned = align_eeg_topography_to_archetypes(
        _eeg_topography_trace(),
        _eeg_labels(),
        _field_artifacts(cfg)["labels"],
        _archetype_assignments(),
        patient_id="sub-01",
    )
    conditioned = compute_subject_archetype_conditioned_eeg_maps(aligned, patient_id="sub-01")
    grouped = summarize_group_archetype_conditioned_eeg_maps(conditioned, min_subjects=1)

    assert not aligned.empty
    assert set(aligned["assigned_archetype"]) == {0, 1}
    assert conditioned["assigned_archetype"].tolist() == [0, 1]
    assert not grouped.empty


def test_compute_archetype_similarity_and_state_preference_preserves_distributed_relationships() -> None:
    aligned = pd.DataFrame(
        {
            "patient_id": ["sub-01"] * 8,
            "time_sec": [index * 0.004 for index in range(8)],
            "sample": list(range(8)),
            "microstate": [0, 0, 0, 1, 1, 1, 1, 0],
            "corr": [0.9] * 8,
            "field_state": [0, 0, 0, 1, 1, 1, 1, 0],
            "assigned_archetype": [0, 0, 0, 1, 1, 1, 1, 0],
            "assignment_similarity": [0.9] * 8,
            "comparison_space": ["yeo17"] * 8,
            "peak_metric": ["rms"] * 8,
            "normalization": ["zscore"] * 8,
            "n_states": [2] * 8,
            "min_duration_ms": [4] * 8,
            "Fp1": [0.8, 0.7, 0.9, -0.6, -0.7, -0.5, -0.6, 0.75],
            "Fp2": [0.6, 0.5, 0.55, -0.7, -0.6, -0.8, -0.65, 0.58],
            "F3": [-0.5, -0.45, -0.52, 0.8, 0.75, 0.7, 0.78, -0.49],
            "F4": [-0.7, -0.65, -0.72, 0.5, 0.45, 0.55, 0.52, -0.68],
        }
    )
    conditioned = compute_subject_archetype_conditioned_eeg_maps(aligned, patient_id="sub-01")
    similarity = compute_subject_archetype_template_similarity(conditioned, _eeg_template_df(), patient_id="sub-01")
    group_similarity = summarize_group_archetype_template_similarity(similarity, min_subjects=1)
    preference = compute_subject_archetype_state_preference(aligned, patient_id="sub-01")

    best_matches = (
        similarity.sort_values(["assigned_archetype", "similarity"], ascending=[True, False])
        .groupby("assigned_archetype")
        .head(1)
        .sort_values("assigned_archetype")
    )
    assert best_matches["microstate"].tolist() == [0, 1]
    assert not group_similarity.empty
    assert set(preference["microstate"]) == {0, 1}
    assert preference["conditional_probability"].between(0.0, 1.0).all()


def test_run_exploratory_field_state_coupling_stage_writes_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    labels_path = tmp_path / "labels.parquet"
    artifacts = _field_artifacts(cfg)
    field_paths = {
        "trace": tmp_path / "field_trace.parquet",
        "peaks": tmp_path / "field_peaks.parquet",
        "peak_maps": tmp_path / "field_peak_maps.parquet",
        "templates": tmp_path / "field_templates.parquet",
        "labels": tmp_path / "field_labels.parquet",
        "profiles": tmp_path / "field_profiles.parquet",
        "transition_profiles": tmp_path / "field_transition_profiles.parquet",
    }
    write_dataframe(_eeg_labels(), labels_path)
    for key, path in field_paths.items():
        write_dataframe(artifacts[key], path)

    monkeypatch.setattr(pipelines, "run_eeg_states_stage", lambda *_args, **_kwargs: {"labels": labels_path, "gfp_trace": tmp_path / "unused.parquet", "gfp_peaks": tmp_path / "unused2.parquet"})
    monkeypatch.setattr(
        pipelines,
        "_ensure_seeg_field_state_artifacts",
        lambda *_args, **_kwargs: ("field-state-shared", field_paths),
    )
    monkeypatch.setattr(pipelines, "_eligible_rows", lambda *_args, **_kwargs: pd.DataFrame({"patient_id": ["sub-01"]}))

    outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="field-state-coupling",
        field_state_count=2,
        field_surrogates=8,
        min_subjects=1,
    )

    subject_df = read_dataframe(outputs["subject_effects"])
    group_df = read_dataframe(outputs["group_effects"])
    assert outputs["field_templates"] == field_paths["templates"]
    assert subject_df["lag_ms"].tolist() == [0]
    assert group_df["lag_ms"].tolist() == [0]


def test_run_exploratory_field_state_archetypes_stage_writes_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    projection_path = tmp_path / "field_archetype_projections.parquet"
    projections = pd.DataFrame(
        {
            "patient_id": ["sub-01", "sub-01", "sub-02", "sub-02"],
            "field_state": [0, 1, 0, 1],
            "peak_metric": ["rms"] * 4,
            "normalization": ["zscore"] * 4,
            "n_states": [2] * 4,
            "min_duration_ms": [4] * 4,
            "n_channels": [2] * 4,
            "n_peak_maps": [8] * 4,
            "comparison_space": ["yeo17"] * 4,
            "orientation_sign": [1.0] * 4,
            "n_mapped_channels": [4] * 4,
            "n_common_units": [2] * 4,
            "DefaultA": [1.0, 0.7, 1.0, 0.7],
            "ContA": [-1.0, 0.9, -1.0, 0.9],
        }
    )
    write_dataframe(projections, projection_path)

    monkeypatch.setattr(
        pipelines,
        "_ensure_seeg_field_state_archetype_artifacts",
        lambda *_args, **_kwargs: ("field-state-archetype-shared", {"projections": projection_path}),
    )

    outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="field-state-archetypes",
        field_state_count=2,
        field_min_duration_ms=4,
        min_subjects=1,
    )

    assignments = read_dataframe(outputs["assignments"])
    archetypes = read_dataframe(outputs["archetypes"])
    support = read_dataframe(outputs["support"])
    assert not assignments.empty
    assert not archetypes.empty
    assert not support.empty


def test_run_exploratory_archetype_conditioned_eeg_topography_stage_writes_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    labels_path = tmp_path / "labels.parquet"
    artifacts = _field_artifacts(cfg)
    field_paths = {
        "trace": tmp_path / "field_trace.parquet",
        "peaks": tmp_path / "field_peaks.parquet",
        "peak_maps": tmp_path / "field_peak_maps.parquet",
        "templates": tmp_path / "field_templates.parquet",
        "labels": tmp_path / "field_labels.parquet",
        "profiles": tmp_path / "field_profiles.parquet",
        "transition_profiles": tmp_path / "field_transition_profiles.parquet",
    }
    assignments_path = tmp_path / "field_archetype_assignments.parquet"
    archetypes_path = tmp_path / "field_archetypes.parquet"
    support_path = tmp_path / "field_archetype_support.parquet"
    write_dataframe(_eeg_labels(), labels_path)
    for key, path in field_paths.items():
        write_dataframe(artifacts[key], path)
    write_dataframe(_archetype_assignments(), assignments_path)
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["yeo17", "yeo17"],
                "field_state": [0, 1],
                "peak_metric": ["rms", "rms"],
                "normalization": ["zscore", "zscore"],
                "n_states": [2, 2],
                "min_duration_ms": [4, 4],
                "n_channels": [2, 2],
                "n_peak_maps": [8, 8],
                "comparison_space": ["yeo17", "yeo17"],
                "orientation_sign": [1.0, 1.0],
                "n_mapped_channels": [4, 4],
                "n_common_units": [2, 2],
                "DefaultA": [1.0, 0.5],
                "ContA": [-1.0, 0.7],
            }
        ),
        archetypes_path,
    )
    write_dataframe(
        pd.DataFrame(
            {
                "comparison_space": ["yeo17", "yeo17"],
                "field_state": [0, 1],
                "peak_metric": ["rms", "rms"],
                "normalization": ["zscore", "zscore"],
                "n_states": [2, 2],
                "min_duration_ms": [4, 4],
                "n_subjects": [1, 1],
                "n_state_assignments": [1, 1],
                "mean_similarity": [0.9, 0.85],
                "median_similarity": [0.9, 0.85],
                "min_similarity": [0.9, 0.85],
            }
        ),
        support_path,
    )

    class _Model:
        def __init__(self) -> None:
            self.cluster_centers_ = _eeg_template_df()[["Fp1", "Fp2", "F3", "F4"]].to_numpy(dtype=float)
            self.info = {"ch_names": ["Fp1", "Fp2", "F3", "F4"]}

    monkeypatch.setattr(
        pipelines,
        "run_eeg_states_stage",
        lambda *_args, **_kwargs: {"labels": labels_path, "model": tmp_path / "unused_model.fif", "gfp_trace": tmp_path / "unused.parquet", "gfp_peaks": tmp_path / "unused2.parquet"},
    )
    monkeypatch.setattr(
        pipelines,
        "_ensure_seeg_field_state_artifacts",
        lambda *_args, **_kwargs: ("field-state-shared", field_paths),
    )
    monkeypatch.setattr(
        pipelines,
        "run_exploratory_field_state_archetypes_stage",
        lambda *_args, **_kwargs: {"assignments": assignments_path, "archetypes": archetypes_path, "support": support_path},
    )
    monkeypatch.setattr(pipelines, "load_microstate_model", lambda *_args, **_kwargs: _Model())
    monkeypatch.setattr(pipelines, "_load_patient_eeg_topography_trace", lambda *_args, **_kwargs: _eeg_topography_trace())
    monkeypatch.setattr(pipelines, "_eligible_rows", lambda *_args, **_kwargs: pd.DataFrame({"patient_id": ["sub-01"]}))

    outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="archetype-conditioned-eeg-topography",
        field_state_count=2,
        field_min_duration_ms=4,
        field_archetype_space="yeo17",
        fine_lag_window_ms=8,
        transition_window_sec=0.012,
        field_surrogates=8,
        min_subjects=1,
    )

    assert not read_dataframe(outputs["subject_maps"]).empty
    assert not read_dataframe(outputs["group_maps"]).empty
    assert not read_dataframe(outputs["group_similarity"]).empty
    assert not read_dataframe(outputs["group_preference"]).empty
    assert not read_dataframe(outputs["group_fine_lag"]).empty
    assert not read_dataframe(outputs["group_transition_effects"]).empty


def test_run_exploratory_fine_lag_field_state_coupling_stage_writes_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    labels_path = tmp_path / "labels.parquet"
    artifacts = _field_artifacts(cfg)
    field_paths = {
        "trace": tmp_path / "field_trace.parquet",
        "peaks": tmp_path / "field_peaks.parquet",
        "peak_maps": tmp_path / "field_peak_maps.parquet",
        "templates": tmp_path / "field_templates.parquet",
        "labels": tmp_path / "field_labels.parquet",
        "profiles": tmp_path / "field_profiles.parquet",
        "transition_profiles": tmp_path / "field_transition_profiles.parquet",
    }
    write_dataframe(_eeg_labels(), labels_path)
    for key, path in field_paths.items():
        write_dataframe(artifacts[key], path)

    monkeypatch.setattr(
        pipelines,
        "run_eeg_states_stage",
        lambda *_args, **_kwargs: {"labels": labels_path, "gfp_trace": tmp_path / "unused.parquet", "gfp_peaks": tmp_path / "unused2.parquet"},
    )
    monkeypatch.setattr(
        pipelines,
        "_ensure_seeg_field_state_artifacts",
        lambda *_args, **_kwargs: ("field-state-shared", field_paths),
    )
    monkeypatch.setattr(pipelines, "_eligible_rows", lambda *_args, **_kwargs: pd.DataFrame({"patient_id": ["sub-01"]}))

    outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="fine-lag-field-state-coupling",
        field_state_count=2,
        field_min_duration_ms=4,
        field_surrogates=8,
        fine_lag_window_ms=8,
        min_subjects=1,
    )

    subject_df = read_dataframe(outputs["subject_effects"])
    subject_peaks = read_dataframe(outputs["subject_peaks"])
    assert subject_df["lag_ms"].tolist() == [-8, -4, 0, 4, 8]
    assert not subject_peaks.empty


def test_run_exploratory_field_state_to_eeg_switching_stage_writes_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    labels_path = tmp_path / "labels.parquet"
    gfp_trace_path = tmp_path / "gfp_trace.parquet"
    artifacts = _field_artifacts(cfg)
    field_paths = {
        "trace": tmp_path / "field_trace.parquet",
        "peaks": tmp_path / "field_peaks.parquet",
        "peak_maps": tmp_path / "field_peak_maps.parquet",
        "templates": tmp_path / "field_templates.parquet",
        "labels": tmp_path / "field_labels.parquet",
        "profiles": tmp_path / "field_profiles.parquet",
        "transition_profiles": tmp_path / "field_transition_profiles.parquet",
    }
    write_dataframe(_eeg_labels(), labels_path)
    write_dataframe(_gfp_trace(), gfp_trace_path)
    for key, path in field_paths.items():
        write_dataframe(artifacts[key], path)

    monkeypatch.setattr(
        pipelines,
        "run_eeg_states_stage",
        lambda *_args, **_kwargs: {"labels": labels_path, "gfp_trace": gfp_trace_path, "gfp_peaks": tmp_path / "unused2.parquet"},
    )
    monkeypatch.setattr(
        pipelines,
        "_ensure_seeg_field_state_artifacts",
        lambda *_args, **_kwargs: ("field-state-shared", field_paths),
    )
    monkeypatch.setattr(pipelines, "_eligible_rows", lambda *_args, **_kwargs: pd.DataFrame({"patient_id": ["sub-01"]}))

    outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="field-state-to-eeg-switching",
        field_state_count=2,
        field_min_duration_ms=4,
        field_surrogates=8,
        transition_window_sec=0.012,
        min_subjects=1,
    )
    gfp_outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="gfp-controlled-field-state-to-eeg-switching",
        field_state_count=2,
        field_min_duration_ms=4,
        transition_window_sec=0.012,
        min_subjects=1,
    )

    subject_df = read_dataframe(outputs["subject_effects"])
    group_df = read_dataframe(outputs["group_effects"])
    gfp_subject_df = read_dataframe(gfp_outputs["subject_effects"])
    gfp_group_df = read_dataframe(gfp_outputs["group_effects"])
    assert not subject_df.empty
    assert not group_df.empty
    assert not gfp_subject_df.empty
    assert not gfp_group_df.empty


def test_run_exploratory_gfp_controlled_field_state_switching_stage_writes_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    labels_path = tmp_path / "labels.parquet"
    gfp_trace_path = tmp_path / "gfp_trace.parquet"
    gfp_peaks_path = tmp_path / "gfp_peaks.parquet"
    transitions_path = tmp_path / "transitions.parquet"
    artifacts = _field_artifacts(cfg)
    field_paths = {
        "trace": tmp_path / "field_trace.parquet",
        "peaks": tmp_path / "field_peaks.parquet",
        "peak_maps": tmp_path / "field_peak_maps.parquet",
        "templates": tmp_path / "field_templates.parquet",
        "labels": tmp_path / "field_labels.parquet",
        "profiles": tmp_path / "field_profiles.parquet",
        "transition_profiles": tmp_path / "field_transition_profiles.parquet",
    }
    write_dataframe(_eeg_labels(), labels_path)
    write_dataframe(_gfp_trace(), gfp_trace_path)
    write_dataframe(pd.DataFrame({"patient_id": ["sub-01"], "peak_id": [0], "event_sec": [0.008], "sample": [2], "gfp": [0.8]}), gfp_peaks_path)
    write_dataframe(_eeg_transitions(), transitions_path)
    for key, path in field_paths.items():
        write_dataframe(artifacts[key], path)

    monkeypatch.setattr(
        pipelines,
        "run_eeg_states_stage",
        lambda *_args, **_kwargs: {"labels": labels_path, "gfp_trace": gfp_trace_path, "gfp_peaks": gfp_peaks_path},
    )
    monkeypatch.setattr(
        pipelines,
        "_ensure_exploratory_event_tables",
        lambda *_args, **_kwargs: {"events": tmp_path / "events.parquet", "transitions": transitions_path},
    )
    monkeypatch.setattr(
        pipelines,
        "_ensure_seeg_field_state_artifacts",
        lambda *_args, **_kwargs: ("field-state-shared", field_paths),
    )
    monkeypatch.setattr(pipelines, "_eligible_rows", lambda *_args, **_kwargs: pd.DataFrame({"patient_id": ["sub-01"]}))

    outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="gfp-controlled-field-state-switching",
        field_state_count=2,
        transition_window_sec=0.012,
        min_subjects=1,
    )

    subject_profiles = read_dataframe(outputs["subject_profiles"])
    group_omnibus = read_dataframe(outputs["group_omnibus"])
    subject_transition = read_dataframe(outputs["subject_transition_effects"])
    group_transition = read_dataframe(outputs["group_transition_effects"])
    assert set(subject_profiles.columns) >= {"adjusted_switch_rate", "gfp_beta"}
    assert not group_omnibus.empty
    assert not subject_transition.empty
    assert not group_transition.empty


def test_run_exploratory_field_state_stage_reuses_cached_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    branch = pipelines._exploratory_branch(
        cfg,
        "field-state-coupling",
        params={
            "peak_metric": "rms",
            "normalization": "zscore",
            "state_count": cfg.microstate_k,
            "min_duration_ms": cfg.min_microstate_duration_ms,
            "surrogates": 128,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    field_paths = {
        "trace": tmp_path / "field_trace.parquet",
        "peaks": tmp_path / "field_peaks.parquet",
        "peak_maps": tmp_path / "field_peak_maps.parquet",
        "templates": tmp_path / "field_templates.parquet",
        "labels": tmp_path / "field_labels.parquet",
        "profiles": tmp_path / "field_profiles.parquet",
        "transition_profiles": tmp_path / "field_transition_profiles.parquet",
    }
    for path in field_paths.values():
        write_dataframe(pd.DataFrame({"patient_id": ["sub-01"]}), path)
    monkeypatch.setattr(
        pipelines,
        "_ensure_seeg_field_state_artifacts",
        lambda *_args, **_kwargs: ("field-state-shared", field_paths),
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", "subject_field_state_coupling", ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", "group_field_state_coupling", ext="parquet", branch=branch),
    }
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "peak_metric": ["rms"],
                "normalization": ["zscore"],
                "n_states": [cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms],
                "lag_samples": [0],
                "lag_ms": [0],
                "n_samples": [10],
                "observed_coupling": [0.4],
                "null_mean_coupling": [0.1],
                "effect_mean_diff": [0.3],
                "p_perm": [0.05],
            }
        ),
        cached["subject_effects"],
    )
    write_dataframe(
        pd.DataFrame(
            {
                "peak_metric": ["rms"],
                "normalization": ["zscore"],
                "n_states": [cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms],
                "lag_ms": [0],
                "n_subjects": [7],
                "mean_effect": [0.3],
                "median_effect": [0.3],
                "p_perm": [0.05],
                "q_fdr": [0.05],
            }
        ),
        cached["group_effects"],
    )

    outputs = pipelines.run_exploratory_coupling_stage(cfg, analysis="field-state-coupling")
    assert outputs["field_templates"] == field_paths["templates"]
    assert outputs["subject_effects"] == cached["subject_effects"]
    assert outputs["group_effects"] == cached["group_effects"]
    assert outputs["subject_effects_excel"].exists()
    assert outputs["group_effects_excel"].exists()


def test_run_exploratory_fine_lag_stage_reuses_cached_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    branch = pipelines._exploratory_branch(
        cfg,
        "fine-lag-field-state-coupling",
        params={
            "peak_metric": "rms",
            "normalization": "zscore",
            "state_count": cfg.microstate_k,
            "min_duration_ms": cfg.min_microstate_duration_ms,
            "fine_lag_window_ms": 40,
            "surrogates": 128,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    field_paths = {
        "trace": tmp_path / "field_trace.parquet",
        "peaks": tmp_path / "field_peaks.parquet",
        "peak_maps": tmp_path / "field_peak_maps.parquet",
        "templates": tmp_path / "field_templates.parquet",
        "labels": tmp_path / "field_labels.parquet",
        "profiles": tmp_path / "field_profiles.parquet",
        "transition_profiles": tmp_path / "field_transition_profiles.parquet",
    }
    for path in field_paths.values():
        write_dataframe(pd.DataFrame({"patient_id": ["sub-01"]}), path)
    monkeypatch.setattr(
        pipelines,
        "_ensure_seeg_field_state_artifacts",
        lambda *_args, **_kwargs: ("field-state-shared", field_paths),
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", "subject_fine_lag_field_state_coupling", ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", "group_fine_lag_field_state_coupling", ext="parquet", branch=branch),
        "subject_peaks": cfg.cache_path("coupling", "subject_fine_lag_field_state_peaks", ext="parquet", branch=branch),
        "group_peak_summary": cfg.cache_path("stats", "group_fine_lag_field_state_peak_summary", ext="parquet", branch=branch),
    }
    for path in cached.values():
        write_dataframe(pd.DataFrame({"patient_id": ["sub-01"]}), path)

    outputs = pipelines.run_exploratory_coupling_stage(cfg, analysis="fine-lag-field-state-coupling")
    assert outputs["subject_effects"] == cached["subject_effects"]
    assert outputs["group_effects"] == cached["group_effects"]
    assert outputs["subject_peaks"] == cached["subject_peaks"]
    assert outputs["group_peak_summary"] == cached["group_peak_summary"]


def test_run_exploratory_field_state_model_order_stage_reuses_cached_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    branch = pipelines._exploratory_branch(
        cfg,
        "field-state-model-order-evaluation",
        params={
            "peak_metric": "rms",
            "normalization": "zscore",
            "min_duration_ms": cfg.min_microstate_duration_ms,
            "candidate_ks": "2-3-4-5-6-7",
        },
    )
    cached = {
        "subject_summary": cfg.cache_path("coupling", "subject_field_state_model_order", ext="parquet", branch=branch),
        "group_summary": cfg.cache_path("stats", "group_field_state_model_order", ext="parquet", branch=branch),
    }
    write_dataframe(pd.DataFrame({"patient_id": ["sub-01"], "n_states": [4]}), cached["subject_summary"])
    write_dataframe(pd.DataFrame({"n_states": [4], "n_subjects": [7]}), cached["group_summary"])

    outputs = pipelines.run_exploratory_coupling_stage(cfg, analysis="field-state-model-order-evaluation")

    assert outputs["subject_summary"] == cached["subject_summary"]
    assert outputs["group_summary"] == cached["group_summary"]
    assert outputs["subject_summary_excel"].exists()
    assert outputs["group_summary_excel"].exists()


def test_render_reports_discovers_field_state_outputs(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", run_timestamp="20260407_190000")
    artifact_branch = pipelines._exploratory_branch(
        cfg,
        "field-state-shared",
        params={
            "peak_metric": "rms",
            "normalization": "zscore",
            "state_count": cfg.microstate_k,
            "min_duration_ms": cfg.min_microstate_duration_ms,
        },
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01", "sub-01"],
                "field_state": [0, 1],
                "peak_metric": ["rms", "rms"],
                "normalization": ["zscore", "zscore"],
                "n_states": [2, 2],
                "min_duration_ms": [cfg.min_microstate_duration_ms, cfg.min_microstate_duration_ms],
                "n_channels": [4, 4],
                "n_peak_maps": [2, 2],
                "bp1": [1.0, -1.0],
                "bp2": [-1.0, 1.0],
                "bp3": [-0.5, 0.5],
                "bp4": [0.5, -0.5],
            }
        ),
        cfg.cache_path("coupling", "field_state_templates", ext="parquet", branch=artifact_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01", "sub-01"],
                "peak_metric": ["rms", "rms"],
                "normalization": ["zscore", "zscore"],
                "n_states": [2, 2],
                "min_duration_ms": [cfg.min_microstate_duration_ms, cfg.min_microstate_duration_ms],
                "field_state": [0, 1],
                "occupancy": [0.4, 0.6],
                "mean_dwell_sec": [0.012, 0.016],
                "n_samples": [6, 10],
                "n_runs": [3, 4],
            }
        ),
        cfg.cache_path("coupling", "field_state_profiles", ext="parquet", branch=artifact_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01", "sub-01"],
                "peak_metric": ["rms", "rms"],
                "normalization": ["zscore", "zscore"],
                "n_states": [2, 2],
                "min_duration_ms": [cfg.min_microstate_duration_ms, cfg.min_microstate_duration_ms],
                "from_state": [0, 1],
                "to_state": [1, 0],
                "n_transitions": [3, 2],
                "transition_probability": [0.75, 0.5],
            }
        ),
        cfg.cache_path("coupling", "field_state_transition_profiles", ext="parquet", branch=artifact_branch),
    )

    coupling_branch = pipelines._exploratory_branch(
        cfg,
        "field-state-coupling",
        params={
            "peak_metric": "rms",
            "normalization": "zscore",
            "state_count": cfg.microstate_k,
            "min_duration_ms": cfg.min_microstate_duration_ms,
            "surrogates": 128,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "peak_metric": ["rms"],
                "normalization": ["zscore"],
                "n_states": [cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms],
                "lag_samples": [0],
                "lag_ms": [0],
                "n_samples": [12],
                "observed_coupling": [0.6],
                "null_mean_coupling": [0.2],
                "effect_mean_diff": [0.4],
                "p_perm": [0.02],
            }
        ),
        cfg.cache_path("coupling", "subject_field_state_coupling", ext="parquet", branch=coupling_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "peak_metric": ["rms"],
                "normalization": ["zscore"],
                "n_states": [cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms],
                "lag_ms": [0],
                "n_subjects": [7],
                "mean_effect": [0.4],
                "median_effect": [0.4],
                "p_perm": [0.02],
                "q_fdr": [0.02],
            }
        ),
        cfg.cache_path("stats", "group_field_state_coupling", ext="parquet", branch=coupling_branch),
    )

    gfp_branch = pipelines._exploratory_branch(
        cfg,
        "gfp-controlled-field-state-switching",
        params={
            "peak_metric": "rms",
            "normalization": "zscore",
            "state_count": cfg.microstate_k,
            "min_duration_ms": cfg.min_microstate_duration_ms,
            "transition_window_sec": cfg.direct_transition_window_sec,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"] * 4,
                "peak_metric": ["rms"] * 4,
                "normalization": ["zscore"] * 4,
                "n_states": [cfg.microstate_k] * 4,
                "min_duration_ms": [cfg.min_microstate_duration_ms] * 4,
                "microstate": [0, 1, 2, 3],
                "adjusted_switch_rate": [0.1, 0.2, 0.15, 0.25],
                "raw_switch_rate": [0.1, 0.2, 0.15, 0.25],
                "n_state_samples": [10, 10, 10, 10],
                "mean_state_gfp": [0.2, 0.4, 0.3, 0.5],
                "gfp_beta": [0.4, 0.4, 0.4, 0.4],
            }
        ),
        cfg.cache_path("coupling", "subject_gfp_controlled_field_state_switching", ext="parquet", branch=gfp_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "peak_metric": ["rms"],
                "normalization": ["zscore"],
                "n_states": [cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms],
                "n_subjects": [7],
                "statistic": [4.2],
                "p_perm": [0.01],
                "mean_state_0": [0.1],
                "mean_state_1": [0.2],
                "mean_state_2": [0.15],
                "mean_state_3": [0.25],
                "q_fdr": [0.01],
            }
        ),
        cfg.cache_path("stats", "group_gfp_controlled_field_state_switching_omnibus", ext="parquet", branch=gfp_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "peak_metric": ["rms"],
                "normalization": ["zscore"],
                "n_states": [cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms],
                "microstate_a": [0],
                "microstate_b": [1],
                "n_subjects": [7],
                "mean_state_a": [0.1],
                "mean_state_b": [0.2],
                "mean_effect": [0.1],
                "median_effect": [0.1],
                "p_perm": [0.02],
                "q_fdr": [0.02],
            }
        ),
        cfg.cache_path("stats", "group_gfp_controlled_field_state_switching_posthoc", ext="parquet", branch=gfp_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "peak_metric": ["rms"],
                "normalization": ["zscore"],
                "n_states": [cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms],
                "from_state": [0],
                "to_state": [1],
                "n_events": [4],
                "n_samples": [40],
                "pre_switch_rate": [0.2],
                "post_switch_rate": [0.5],
                "effect_mean_diff": [0.3],
                "gfp_beta": [0.4],
            }
        ),
        cfg.cache_path("coupling", "subject_gfp_controlled_field_state_transition_switching", ext="parquet", branch=gfp_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "peak_metric": ["rms"],
                "normalization": ["zscore"],
                "n_states": [cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms],
                "from_state": [0],
                "to_state": [1],
                "n_subjects": [7],
                "mean_effect": [0.3],
                "median_effect": [0.3],
                "p_perm": [0.02],
                "q_fdr": [0.02],
            }
        ),
        cfg.cache_path("stats", "group_gfp_controlled_field_state_transition_switching", ext="parquet", branch=gfp_branch),
    )

    archetype_branch = pipelines._exploratory_branch(
        cfg,
        "field-state-archetypes",
        params={
            "peak_metric": "rms",
            "normalization": "zscore",
            "state_count": cfg.microstate_k,
            "min_duration_ms": cfg.min_microstate_duration_ms,
            "comparison_space": "yeo17",
            "min_subjects": cfg.min_group_subjects,
        },
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01", "sub-02"],
                "field_state": [0, 1],
                "peak_metric": ["rms", "rms"],
                "normalization": ["zscore", "zscore"],
                "n_states": [cfg.microstate_k, cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms, cfg.min_microstate_duration_ms],
                "comparison_space": ["yeo17", "yeo17"],
                "assigned_archetype": [0, 1],
                "assignment_similarity": [0.9, 0.8],
                "orientation_sign": [1.0, 1.0],
            }
        ),
        cfg.cache_path("coupling", "field_state_archetype_assignments", ext="parquet", branch=archetype_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["yeo17", "yeo17"],
                "field_state": [0, 1],
                "peak_metric": ["rms", "rms"],
                "normalization": ["zscore", "zscore"],
                "n_states": [cfg.microstate_k, cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms, cfg.min_microstate_duration_ms],
                "n_channels": [2, 2],
                "n_peak_maps": [16, 16],
                "comparison_space": ["yeo17", "yeo17"],
                "orientation_sign": [1.0, 1.0],
                "n_mapped_channels": [4, 4],
                "n_common_units": [2, 2],
                "DefaultA": [1.0, 0.5],
                "ContA": [-1.0, 0.7],
            }
        ),
        cfg.cache_path("coupling", "field_state_archetypes", ext="parquet", branch=archetype_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01", "sub-02"],
                "field_state": [0, 1],
                "peak_metric": ["rms", "rms"],
                "normalization": ["zscore", "zscore"],
                "n_states": [cfg.microstate_k, cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms, cfg.min_microstate_duration_ms],
                "comparison_space": ["yeo17", "yeo17"],
                "orientation_sign": [1.0, 1.0],
                "n_mapped_channels": [4, 4],
                "n_common_units": [2, 2],
                "DefaultA": [1.0, 0.5],
                "ContA": [-1.0, 0.7],
            }
        ),
        cfg.cache_path("coupling", "field_state_archetype_projections", ext="parquet", branch=archetype_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "comparison_space": ["yeo17", "yeo17"],
                "field_state": [0, 1],
                "peak_metric": ["rms", "rms"],
                "normalization": ["zscore", "zscore"],
                "n_states": [cfg.microstate_k, cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms, cfg.min_microstate_duration_ms],
                "n_subjects": [8, 8],
                "n_state_assignments": [8, 8],
                "mean_similarity": [0.85, 0.81],
                "median_similarity": [0.84, 0.8],
                "min_similarity": [0.7, 0.68],
            }
        ),
        cfg.cache_path("stats", "field_state_archetype_support", ext="parquet", branch=archetype_branch),
    )

    fine_lag_branch = pipelines._exploratory_branch(
        cfg,
        "fine-lag-field-state-coupling",
        params={
            "peak_metric": "rms",
            "normalization": "zscore",
            "state_count": cfg.microstate_k,
            "min_duration_ms": cfg.min_microstate_duration_ms,
            "fine_lag_window_ms": 40,
            "surrogates": 128,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"] * 5,
                "peak_metric": ["rms"] * 5,
                "normalization": ["zscore"] * 5,
                "n_states": [cfg.microstate_k] * 5,
                "min_duration_ms": [cfg.min_microstate_duration_ms] * 5,
                "lag_samples": [-2, -1, 0, 1, 2],
                "lag_ms": [-8, -4, 0, 4, 8],
                "n_samples": [12] * 5,
                "observed_coupling": [0.4, 0.45, 0.6, 0.44, 0.41],
                "null_mean_coupling": [0.2] * 5,
                "effect_mean_diff": [0.2, 0.25, 0.4, 0.24, 0.21],
                "p_perm": [0.05] * 5,
            }
        ),
        cfg.cache_path("coupling", "subject_fine_lag_field_state_coupling", ext="parquet", branch=fine_lag_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "peak_metric": ["rms"] * 5,
                "normalization": ["zscore"] * 5,
                "n_states": [cfg.microstate_k] * 5,
                "min_duration_ms": [cfg.min_microstate_duration_ms] * 5,
                "lag_ms": [-8, -4, 0, 4, 8],
                "n_subjects": [7] * 5,
                "mean_effect": [0.2, 0.25, 0.4, 0.24, 0.21],
                "median_effect": [0.2, 0.25, 0.4, 0.24, 0.21],
                "p_perm": [0.05] * 5,
                "q_fdr": [0.05] * 5,
            }
        ),
        cfg.cache_path("stats", "group_fine_lag_field_state_coupling", ext="parquet", branch=fine_lag_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01", "sub-02"],
                "peak_metric": ["rms", "rms"],
                "normalization": ["zscore", "zscore"],
                "n_states": [cfg.microstate_k, cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms, cfg.min_microstate_duration_ms],
                "peak_lag_samples": [0, 1],
                "peak_lag_ms": [0, 4],
                "peak_effect_mean_diff": [0.4, 0.35],
                "peak_observed_coupling": [0.6, 0.58],
                "peak_null_mean_coupling": [0.2, 0.23],
                "peak_p_perm": [0.05, 0.05],
                "peak_width_ms": [8.0, 12.0],
                "n_lags": [5, 5],
            }
        ),
        cfg.cache_path("coupling", "subject_fine_lag_field_state_peaks", ext="parquet", branch=fine_lag_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "peak_metric": ["rms", "rms", "rms"],
                "normalization": ["zscore", "zscore", "zscore"],
                "n_states": [cfg.microstate_k] * 3,
                "min_duration_ms": [cfg.min_microstate_duration_ms] * 3,
                "summary_kind": ["peak_lag_ms", "peak_effect_mean_diff", "peak_width_ms"],
                "n_subjects": [7] * 3,
                "mean_effect": [0.0, 0.38, 10.0],
                "median_effect": [0.0, 0.38, 10.0],
                "p_perm": [0.05] * 3,
                "q_fdr": [0.05] * 3,
            }
        ),
        cfg.cache_path("stats", "group_fine_lag_field_state_peak_summary", ext="parquet", branch=fine_lag_branch),
    )

    seeg_led_branch = pipelines._exploratory_branch(
        cfg,
        "field-state-to-eeg-switching",
        params={
            "peak_metric": "rms",
            "normalization": "zscore",
            "state_count": cfg.microstate_k,
            "min_duration_ms": cfg.min_microstate_duration_ms,
            "transition_window_sec": cfg.direct_transition_window_sec,
            "surrogates": 128,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "peak_metric": ["rms"],
                "normalization": ["zscore"],
                "n_states": [cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms],
                "from_state": [0],
                "to_state": [1],
                "response_kind": ["any-switch"],
                "response_state": [-1],
                "n_events": [4],
                "observed_coupling": [0.6],
                "null_mean_coupling": [0.2],
                "effect_mean_diff": [0.4],
                "p_perm": [0.02],
            }
        ),
        cfg.cache_path("coupling", "subject_field_state_to_eeg_switching", ext="parquet", branch=seeg_led_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "peak_metric": ["rms"],
                "normalization": ["zscore"],
                "n_states": [cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms],
                "from_state": [0],
                "to_state": [1],
                "response_kind": ["any-switch"],
                "response_state": [-1],
                "n_subjects": [7],
                "mean_effect": [0.4],
                "median_effect": [0.4],
                "p_perm": [0.02],
                "q_fdr": [0.02],
            }
        ),
        cfg.cache_path("stats", "group_field_state_to_eeg_switching", ext="parquet", branch=seeg_led_branch),
    )

    gfp_seeg_led_branch = pipelines._exploratory_branch(
        cfg,
        "gfp-controlled-field-state-to-eeg-switching",
        params={
            "peak_metric": "rms",
            "normalization": "zscore",
            "state_count": cfg.microstate_k,
            "min_duration_ms": cfg.min_microstate_duration_ms,
            "transition_window_sec": cfg.direct_transition_window_sec,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "peak_metric": ["rms"],
                "normalization": ["zscore"],
                "n_states": [cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms],
                "from_state": [0],
                "to_state": [1],
                "n_events": [4],
                "n_samples": [40],
                "pre_switch_rate": [0.2],
                "post_switch_rate": [0.5],
                "effect_mean_diff": [0.3],
                "gfp_beta": [0.4],
            }
        ),
        cfg.cache_path("coupling", "subject_gfp_controlled_field_state_to_eeg_switching", ext="parquet", branch=gfp_seeg_led_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "peak_metric": ["rms"],
                "normalization": ["zscore"],
                "n_states": [cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms],
                "from_state": [0],
                "to_state": [1],
                "n_subjects": [7],
                "mean_effect": [0.3],
                "median_effect": [0.3],
                "p_perm": [0.02],
                "q_fdr": [0.02],
            }
        ),
        cfg.cache_path("stats", "group_gfp_controlled_field_state_to_eeg_switching", ext="parquet", branch=gfp_seeg_led_branch),
    )

    outputs = pipelines.export_paper_tables(cfg)
    output_paths = list(outputs.values())
    assert outputs["paper_manifest_csv"].exists()
    assert outputs["paper_manifest_excel"].exists()
    assert any(path.parent.name == "main_tables" and "subject_field_state_profiles" in path.name for path in output_paths)
    assert any(path.parent.name == "main_tables" and "field_state_synchronous_coupling" in path.name for path in output_paths)
    assert any(path.parent.name == "main_tables" and "field_state_fine_lag_synchrony" in path.name for path in output_paths)
    assert any(path.parent.name == "main_tables" and "group_field_state_archetypes" in path.name for path in output_paths)
    assert any(path.parent.name == "supplementary_tables" and "field_state_archetype_assignments" in path.name for path in output_paths)
    assert any(path.parent.name == "supplementary_tables" and "field_state_to_eeg_switching" in path.name for path in output_paths)
    assert any(path.parent.name == "supplementary_tables" and "gfp_controlled_field_state_to_eeg_switching" in path.name for path in output_paths)
    assert not any(path.parent.name.endswith("figures") for path in output_paths)
    assert not any("gfp_controlled_field_state_switching" in path.name for path in output_paths)


def test_export_paper_tables_includes_field_state_model_order_outputs(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", run_timestamp="20260409_010000")
    branch = pipelines._exploratory_branch(
        cfg,
        "field-state-model-order-evaluation",
        params={
            "peak_metric": "rms",
            "normalization": "zscore",
            "min_duration_ms": cfg.min_microstate_duration_ms,
            "candidate_ks": "2-3-4-5-6-7",
        },
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01", "sub-01"],
                "peak_metric": ["rms", "rms"],
                "normalization": ["zscore", "zscore"],
                "n_states": [2, 4],
                "min_duration_ms": [cfg.min_microstate_duration_ms, cfg.min_microstate_duration_ms],
                "n_channels": [4, 4],
                "n_peak_maps_total": [20, 20],
                "mean_template_fit": [0.80, 0.85],
                "median_template_fit": [0.80, 0.85],
                "min_template_fit": [0.70, 0.75],
                "fit_gain_from_prev_k": [pd.NA, 0.05],
                "split_half_stability": [0.72, 0.81],
                "min_state_occupancy": [0.42, 0.18],
                "max_state_occupancy": [0.58, 0.31],
                "min_state_peak_fraction": [0.40, 0.17],
                "max_state_peak_fraction": [0.60, 0.33],
                "occupancy_entropy": [0.98, 0.92],
                "k_range": ["2-7", "2-7"],
                "retained_main_text_default": [False, True],
            }
        ),
        cfg.cache_path("coupling", "subject_field_state_model_order", ext="parquet", branch=branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "peak_metric": ["rms", "rms"],
                "normalization": ["zscore", "zscore"],
                "n_states": [2, 4],
                "min_duration_ms": [cfg.min_microstate_duration_ms, cfg.min_microstate_duration_ms],
                "k_range": ["2-7", "2-7"],
                "retained_main_text_default": [False, True],
                "n_subjects": [7, 7],
                "mean_template_fit": [0.80, 0.85],
                "median_template_fit": [0.80, 0.85],
                "mean_fit_gain_from_prev_k": [pd.NA, 0.05],
                "median_fit_gain_from_prev_k": [pd.NA, 0.05],
                "mean_split_half_stability": [0.72, 0.81],
                "median_split_half_stability": [0.72, 0.81],
                "mean_min_state_occupancy": [0.42, 0.18],
                "median_min_state_occupancy": [0.42, 0.18],
                "mean_min_state_peak_fraction": [0.40, 0.17],
                "median_min_state_peak_fraction": [0.40, 0.17],
                "mean_occupancy_entropy": [0.98, 0.92],
                "median_occupancy_entropy": [0.98, 0.92],
            }
        ),
        cfg.cache_path("stats", "group_field_state_model_order", ext="parquet", branch=branch),
    )

    outputs = pipelines.export_paper_tables(cfg)
    output_paths = list(outputs.values())

    assert any(path.parent.name == "supplementary_tables" and "field_state_model_order_subject" in path.name for path in output_paths)
    assert any(path.parent.name == "supplementary_tables" and "field_state_model_order_group" in path.name for path in output_paths)


def test_export_paper_tables_keeps_only_retained_field_state_shared_branch(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", run_timestamp="20260409_020000")
    retained_branch = pipelines._retained_field_state_artifact_branch(cfg)
    alternate_branch = pipelines._field_state_artifact_branch(
        cfg,
        peak_metric="rms",
        normalization="zscore",
        state_count=2,
        min_duration_ms=cfg.min_microstate_duration_ms,
    )

    def _write_field_state_shared(branch: str, n_states: int) -> None:
        template_df = pd.DataFrame(
            {
                "patient_id": ["sub-01"] * n_states,
                "field_state": list(range(n_states)),
                "peak_metric": ["rms"] * n_states,
                "normalization": ["zscore"] * n_states,
                "n_states": [n_states] * n_states,
                "min_duration_ms": [cfg.min_microstate_duration_ms] * n_states,
                "A1-A2": [0.6 - index * 0.1 for index in range(n_states)],
                "A2-A3": [-0.4 + index * 0.05 for index in range(n_states)],
            }
        )
        profile_df = pd.DataFrame(
            {
                "patient_id": ["sub-01"] * n_states,
                "field_state": list(range(n_states)),
                "occupancy": [1.0 / n_states] * n_states,
                "mean_dwell_sec": [0.1] * n_states,
                "n_samples": [100] * n_states,
                "n_runs": [1] * n_states,
                "peak_metric": ["rms"] * n_states,
                "normalization": ["zscore"] * n_states,
                "n_states": [n_states] * n_states,
                "min_duration_ms": [cfg.min_microstate_duration_ms] * n_states,
            }
        )
        transition_df = pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "from_state": [0],
                "to_state": [min(1, n_states - 1)],
                "n_transitions": [12],
                "transition_probability": [0.5],
                "peak_metric": ["rms"],
                "normalization": ["zscore"],
                "n_states": [n_states],
                "min_duration_ms": [cfg.min_microstate_duration_ms],
            }
        )
        write_dataframe(template_df, cfg.cache_path("coupling", "field_state_templates", ext="parquet", branch=branch))
        write_dataframe(profile_df, cfg.cache_path("coupling", "field_state_profiles", ext="parquet", branch=branch))
        write_dataframe(
            transition_df,
            cfg.cache_path("coupling", "field_state_transition_profiles", ext="parquet", branch=branch),
        )

    _write_field_state_shared(retained_branch, n_states=cfg.microstate_k)
    _write_field_state_shared(alternate_branch, n_states=2)

    outputs = pipelines.export_paper_tables(cfg)
    output_paths = list(outputs.values())

    retained_paths = [
        path
        for path in output_paths
        if path.parent.name == "main_tables" and "subject_field_state_profiles" in path.name
    ]
    assert len(retained_paths) == 2
    assert all(retained_branch in path.name for path in retained_paths)
    assert all(alternate_branch not in path.name for path in output_paths)


def test_render_reports_discovers_archetype_conditioned_eeg_topography_outputs(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", run_timestamp="20260408_123456")
    branch = pipelines._exploratory_branch(
        cfg,
        "archetype-conditioned-eeg-topography",
        params={
            "peak_metric": "rms",
            "normalization": "zscore",
            "state_count": cfg.microstate_k,
            "min_duration_ms": cfg.min_microstate_duration_ms,
            "comparison_space": "yeo17",
            "fine_lag_window_ms": 40,
            "transition_window_sec": cfg.direct_transition_window_sec,
            "surrogates": 128,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    channel_values_a = {channel: 0.1 + index * 0.02 for index, channel in enumerate(cfg.target19_channels)}
    channel_values_b = {channel: -0.1 - index * 0.02 for index, channel in enumerate(cfg.target19_channels)}
    write_dataframe(
        pd.DataFrame(
            [
                {
                    "patient_id": "group",
                    "comparison_space": "yeo17",
                    "peak_metric": "rms",
                    "normalization": "zscore",
                    "n_states": cfg.microstate_k,
                    "min_duration_ms": cfg.min_microstate_duration_ms,
                    "assigned_archetype": 0,
                    "n_subjects": 8,
                    "total_samples": 100,
                    **channel_values_a,
                },
                {
                    "patient_id": "group",
                    "comparison_space": "yeo17",
                    "peak_metric": "rms",
                    "normalization": "zscore",
                    "n_states": cfg.microstate_k,
                    "min_duration_ms": cfg.min_microstate_duration_ms,
                    "assigned_archetype": 1,
                    "n_subjects": 8,
                    "total_samples": 120,
                    **channel_values_b,
                },
            ]
        ),
        cfg.cache_path("coupling", "group_archetype_conditioned_eeg_maps", ext="parquet", branch=branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01", "sub-01"],
                "comparison_space": ["yeo17", "yeo17"],
                "peak_metric": ["rms", "rms"],
                "normalization": ["zscore", "zscore"],
                "n_states": [cfg.microstate_k, cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms, cfg.min_microstate_duration_ms],
                "assigned_archetype": [0, 1],
                "n_samples": [50, 50],
                **{channel: [channel_values_a[channel], channel_values_b[channel]] for channel in cfg.target19_channels},
            }
        ),
        cfg.cache_path("coupling", "subject_archetype_conditioned_eeg_maps", ext="parquet", branch=branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "comparison_space": ["yeo17"] * 2,
                "peak_metric": ["rms"] * 2,
                "normalization": ["zscore"] * 2,
                "n_states": [cfg.microstate_k] * 2,
                "min_duration_ms": [cfg.min_microstate_duration_ms] * 2,
                "assigned_archetype": [0, 1],
                "microstate": [0, 1],
                "n_subjects": [8, 8],
                "mean_similarity": [0.8, 0.75],
                "median_similarity": [0.8, 0.75],
                "min_similarity": [0.7, 0.7],
            }
        ),
        cfg.cache_path("stats", "group_archetype_eeg_template_similarity", ext="parquet", branch=branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "comparison_space": ["yeo17"] * 2,
                "peak_metric": ["rms"] * 2,
                "normalization": ["zscore"] * 2,
                "n_states": [cfg.microstate_k] * 2,
                "min_duration_ms": [cfg.min_microstate_duration_ms] * 2,
                "assigned_archetype": [0, 1],
                "microstate": [0, 1],
                "n_subjects": [8, 8],
                "mean_effect": [0.2, 0.18],
                "median_effect": [0.2, 0.18],
                "p_perm": [0.02, 0.03],
                "q_fdr": [0.03, 0.03],
            }
        ),
        cfg.cache_path("stats", "group_archetype_eeg_state_preference", ext="parquet", branch=branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "comparison_space": ["yeo17"] * 3,
                "peak_metric": ["rms"] * 3,
                "normalization": ["zscore"] * 3,
                "n_states": [cfg.microstate_k] * 3,
                "min_duration_ms": [cfg.min_microstate_duration_ms] * 3,
                "lag_ms": [-4, 0, 4],
                "n_subjects": [8, 8, 8],
                "mean_effect": [0.1, 0.3, 0.12],
                "median_effect": [0.1, 0.3, 0.12],
                "p_perm": [0.2, 0.02, 0.18],
                "q_fdr": [0.2, 0.06, 0.2],
            }
        ),
        cfg.cache_path("stats", "group_archetype_eeg_fine_lag_coupling", ext="parquet", branch=branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01", "sub-02"],
                "comparison_space": ["yeo17", "yeo17"],
                "peak_metric": ["rms", "rms"],
                "normalization": ["zscore", "zscore"],
                "n_states": [cfg.microstate_k, cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms, cfg.min_microstate_duration_ms],
                "peak_lag_ms": [0, 4],
                "peak_effect_mean_diff": [0.3, 0.25],
                "peak_width_ms": [12.0, 16.0],
            }
        ),
        cfg.cache_path("coupling", "subject_archetype_eeg_fine_lag_peaks", ext="parquet", branch=branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "comparison_space": ["yeo17"] * 3,
                "peak_metric": ["rms"] * 3,
                "normalization": ["zscore"] * 3,
                "n_states": [cfg.microstate_k] * 3,
                "min_duration_ms": [cfg.min_microstate_duration_ms] * 3,
                "summary_kind": ["peak_lag_ms", "peak_effect_mean_diff", "peak_width_ms"],
                "n_subjects": [8, 8, 8],
                "mean_effect": [2.0, 0.28, 14.0],
                "median_effect": [2.0, 0.28, 14.0],
                "p_perm": [0.2, 0.03, 0.01],
                "q_fdr": [0.2, 0.05, 0.03],
            }
        ),
        cfg.cache_path("stats", "group_archetype_eeg_fine_lag_peak_summary", ext="parquet", branch=branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "comparison_space": ["yeo17"],
                "peak_metric": ["rms"],
                "normalization": ["zscore"],
                "n_states": [cfg.microstate_k],
                "min_duration_ms": [cfg.min_microstate_duration_ms],
                "from_state": [0],
                "to_state": [1],
                "response_kind": ["any-switch"],
                "response_state": [-1],
                "n_subjects": [8],
                "mean_effect": [0.22],
                "median_effect": [0.22],
                "p_perm": [0.04],
                "q_fdr": [0.04],
            }
        ),
        cfg.cache_path("stats", "group_archetype_to_eeg_switching", ext="parquet", branch=branch),
    )

    outputs = pipelines.export_paper_tables(cfg)
    output_paths = list(outputs.values())
    assert not any(path.parent.name.endswith("figures") for path in output_paths)
    assert any(path.parent.name == "supplementary_tables" and "archetype_conditioned_eeg_maps" in path.name for path in output_paths)
    assert any(path.parent.name == "main_tables" and "archetype_eeg_template_similarity" in path.name for path in output_paths)
    assert any(path.parent.name == "main_tables" and "archetype_eeg_fine_lag_synchrony" in path.name for path in output_paths)
    assert any(path.parent.name == "supplementary_tables" and "archetype_eeg_state_preference" in path.name for path in output_paths)
    assert any(path.parent.name == "supplementary_tables" and "archetype_to_eeg_switching" in path.name for path in output_paths)
