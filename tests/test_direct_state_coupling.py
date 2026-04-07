from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from seeg_eegmicrostates._utils import write_dataframe, read_dataframe
from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.coupling import (
    compute_subject_direct_state_coupling,
    compute_subject_transition_state_coupling,
    derive_direct_seeg_state_artifacts,
)
from seeg_eegmicrostates.workflows import pipelines


def _eeg_labels() -> pd.DataFrame:
    times = [index * 0.004 for index in range(12)]
    return pd.DataFrame(
        {
            "patient_id": ["sub-01"] * 12,
            "time_sec": times,
            "sample": list(range(12)),
            "microstate": [0, 0, 1, 1, 2, 2, 1, 1, 0, 0, 2, 2],
            "corr": [0.9] * 12,
        }
    )


def _region_signals() -> pd.DataFrame:
    times = [index * 0.004 for index in range(12)]
    return pd.DataFrame(
        {
            "time_sec": times,
            "Right Hippocampus": [0.0, 0.1, 1.0, 1.1, 2.0, 2.1, 1.0, 1.1, 0.0, 0.1, 2.0, 2.1],
            "Right Amygdala": [2.0, 2.1, 1.0, 1.1, 0.0, 0.1, 1.0, 1.1, 2.0, 2.1, 0.0, 0.1],
        }
    )


def _direct_state_labels(cfg: AnalysisConfig) -> pd.DataFrame:
    _, labels = derive_direct_seeg_state_artifacts(
        _region_signals(),
        patient_id="sub-01",
        backend=cfg.direct_state_backend,
        n_states=cfg.microstate_k,
        n_components=2,
        seed=cfg.random_seed,
    )
    return labels


def test_derive_direct_seeg_state_artifacts_returns_features_and_labels(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    features, labels = derive_direct_seeg_state_artifacts(
        _region_signals(),
        patient_id="sub-01",
        backend=cfg.direct_state_backend,
        n_states=cfg.microstate_k,
        n_components=2,
        seed=cfg.random_seed,
    )
    assert "component_1" in features.columns
    assert "component_2" in features.columns
    assert "seeg_state" in labels.columns
    assert labels["seeg_state"].nunique() >= 2


def test_compute_subject_direct_state_coupling_supports_zero_lag_and_lag_grid(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    labels = _direct_state_labels(cfg)
    aligned = pipelines.align_eeg_and_seeg_state_labels(_eeg_labels(), labels, patient_id="sub-01")
    effects = compute_subject_direct_state_coupling(
        aligned,
        patient_id="sub-01",
        backend=cfg.direct_state_backend,
        n_states=cfg.microstate_k,
        lag_samples=[-1, 0, 1],
        sample_period_sec=0.004,
        n_surrogates=8,
        seed=cfg.random_seed,
    )
    assert sorted(effects["lag_ms"].tolist()) == [-4, 0, 4]
    assert set(effects.columns) >= {"observed_coupling", "null_mean_coupling", "effect_mean_diff", "p_perm"}


def test_compute_subject_transition_state_coupling_returns_transition_rows(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    transition_df = pd.DataFrame(
        {
            "patient_id": ["sub-01", "sub-01"],
            "transition_id": [0, 1],
            "event_sec": [0.008, 0.032],
            "from_state": [0, 1],
            "to_state": [1, 0],
        }
    )
    effects = compute_subject_transition_state_coupling(
        transition_df,
        _direct_state_labels(cfg),
        patient_id="sub-01",
        backend=cfg.direct_state_backend,
        n_states=cfg.microstate_k,
        window_sec=0.012,
        n_surrogates=8,
        seed=cfg.random_seed,
    )
    assert set(effects.columns) >= {"from_state", "to_state", "observed_coupling", "effect_mean_diff"}
    assert not effects.empty


def test_run_exploratory_direct_state_coupling_stage_writes_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    eeg_labels_path = tmp_path / "eeg_labels.parquet"
    feature_path = tmp_path / "direct_features.parquet"
    label_path = tmp_path / "direct_labels.parquet"
    write_dataframe(_eeg_labels(), eeg_labels_path)
    write_dataframe(pd.DataFrame({"patient_id": ["sub-01"]}), feature_path)
    write_dataframe(_direct_state_labels(cfg), label_path)

    monkeypatch.setattr(pipelines, "run_eeg_states_stage", lambda *_args, **_kwargs: {"labels": eeg_labels_path})
    monkeypatch.setattr(
        pipelines,
        "_ensure_direct_state_artifacts",
        lambda *_args, **_kwargs: ("direct-state-shared", {"features": feature_path, "labels": label_path}),
    )
    monkeypatch.setattr(pipelines, "_eligible_rows", lambda *_args, **_kwargs: pd.DataFrame({"patient_id": ["sub-01"]}))

    outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="direct-state-coupling",
        direct_components=2,
        direct_surrogates=8,
        min_subjects=1,
    )

    subject_df = read_dataframe(outputs["subject_effects"])
    group_df = read_dataframe(outputs["group_effects"])
    assert outputs["state_features"] == feature_path
    assert outputs["state_labels"] == label_path
    assert subject_df["lag_ms"].tolist() == [0]
    assert group_df["lag_ms"].tolist() == [0]


def test_run_exploratory_lagged_state_coupling_stage_writes_multiple_lags(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    eeg_labels_path = tmp_path / "eeg_labels.parquet"
    feature_path = tmp_path / "direct_features.parquet"
    label_path = tmp_path / "direct_labels.parquet"
    write_dataframe(_eeg_labels(), eeg_labels_path)
    write_dataframe(pd.DataFrame({"patient_id": ["sub-01"]}), feature_path)
    write_dataframe(_direct_state_labels(cfg), label_path)

    monkeypatch.setattr(pipelines, "run_eeg_states_stage", lambda *_args, **_kwargs: {"labels": eeg_labels_path})
    monkeypatch.setattr(
        pipelines,
        "_ensure_direct_state_artifacts",
        lambda *_args, **_kwargs: ("direct-state-shared", {"features": feature_path, "labels": label_path}),
    )
    monkeypatch.setattr(pipelines, "_eligible_rows", lambda *_args, **_kwargs: pd.DataFrame({"patient_id": ["sub-01"]}))

    outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="lagged-state-coupling",
        direct_components=2,
        max_lag_ms=8,
        lag_step_ms=4,
        direct_surrogates=8,
        min_subjects=1,
    )

    subject_df = read_dataframe(outputs["subject_effects"])
    assert sorted(subject_df["lag_ms"].tolist()) == [-8, -4, 0, 4, 8]


def test_run_exploratory_transition_state_coupling_stage_writes_transition_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    transition_path = tmp_path / "eeg_transitions.parquet"
    feature_path = tmp_path / "direct_features.parquet"
    label_path = tmp_path / "direct_labels.parquet"
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01", "sub-01"],
                "transition_id": [0, 1],
                "event_sec": [0.008, 0.032],
                "from_state": [0, 1],
                "to_state": [1, 0],
                "from_start_sec": [0.0, 0.016],
                "from_end_sec": [0.004, 0.028],
                "to_start_sec": [0.008, 0.032],
                "to_end_sec": [0.012, 0.036],
                "from_duration_sec": [0.004, 0.012],
                "to_duration_sec": [0.004, 0.004],
            }
        ),
        transition_path,
    )
    write_dataframe(pd.DataFrame({"patient_id": ["sub-01"]}), feature_path)
    write_dataframe(_direct_state_labels(cfg), label_path)

    monkeypatch.setattr(
        pipelines,
        "_ensure_exploratory_event_tables",
        lambda *_args, **_kwargs: {"events": tmp_path / "events.parquet", "transitions": transition_path},
    )
    monkeypatch.setattr(
        pipelines,
        "_ensure_direct_state_artifacts",
        lambda *_args, **_kwargs: ("direct-state-shared", {"features": feature_path, "labels": label_path}),
    )
    monkeypatch.setattr(pipelines, "_eligible_rows", lambda *_args, **_kwargs: pd.DataFrame({"patient_id": ["sub-01"]}))

    outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="transition-state-coupling",
        direct_components=2,
        transition_window_sec=0.012,
        direct_surrogates=8,
        min_subjects=1,
    )

    subject_df = read_dataframe(outputs["subject_effects"])
    assert set(subject_df.columns) >= {"from_state", "to_state", "effect_mean_diff"}
    assert not subject_df.empty
