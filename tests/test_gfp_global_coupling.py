from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from seeg_eegmicrostates._utils import read_dataframe, write_dataframe
from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.coupling import derive_seeg_global_metric_trace
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


def _gfp_trace() -> pd.DataFrame:
    times = [index * 0.004 for index in range(12)]
    values = [0.1, 0.2, 0.6, 0.4, 0.3, 0.7, 1.0, 0.8, 0.5, 0.4, 0.9, 0.6]
    return pd.DataFrame(
        {
            "patient_id": ["sub-01"] * 12,
            "time_sec": times,
            "sample": list(range(12)),
            "gfp": values,
        }
    )


def _gfp_peaks() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "patient_id": ["sub-01", "sub-01", "sub-01"],
            "peak_id": [0, 1, 2],
            "event_sec": [0.008, 0.024, 0.04],
            "sample": [2, 6, 10],
            "gfp": [0.6, 1.0, 0.9],
        }
    )


def _global_trace(metric_definition: str = "rms", weighting_strategy: str = "equal") -> pd.DataFrame:
    labels = _eeg_labels()
    gfp = _gfp_trace()["gfp"].to_numpy(dtype=float)
    state_offsets = labels["microstate"].map({0: -0.2, 1: 0.1, 2: 0.35}).to_numpy(dtype=float)
    values = 0.5 * gfp + state_offsets
    return pd.DataFrame(
        {
            "patient_id": ["sub-01"] * len(labels),
            "time_sec": labels["time_sec"].to_list(),
            "sample": labels["sample"].to_list(),
            "global_metric": values,
            "metric_definition": [metric_definition] * len(labels),
            "weighting_strategy": [weighting_strategy] * len(labels),
            "network_scope": ["yeo17-core"] * len(labels),
            "n_networks_used": [3] * len(labels),
        }
    )


def _network_support(metric_definition: str = "rms", weighting_strategy: str = "equal") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "patient_id": ["sub-01"] * 3,
            "region": ["DefaultB", "ContB", "SalVentAttnA"],
            "metric_definition": [metric_definition] * 3,
            "weighting_strategy": [weighting_strategy] * 3,
            "network_scope": ["yeo17-core"] * 3,
            "n_bipolar_channels": [4.0, 3.0, 2.0],
            "weight": [1.0, 1.0, 1.0],
            "is_selected": [True, True, True],
        }
    )


def _transitions() -> pd.DataFrame:
    return pd.DataFrame(
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
    )


def _region_signals() -> pd.DataFrame:
    times = [index * 0.004 for index in range(12)]
    return pd.DataFrame(
        {
            "time_sec": times,
            "DefaultB": np.linspace(-1.0, 1.0, 12),
            "ContB": np.linspace(1.0, -1.0, 12),
            "SalVentAttnA": [0.1, 0.2, 0.7, 0.6, 0.2, 0.4, 0.8, 0.7, 0.2, 0.1, 0.9, 0.5],
        }
    )


def _coverage() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "patient_id": ["sub-01", "sub-01", "sub-01"],
            "region": ["DefaultB", "ContB", "SalVentAttnA"],
            "n_bipolar_channels": [4, 3, 2],
        }
    )


def test_derive_seeg_global_metric_trace_supports_predeclared_metric_family(tmp_path: Path) -> None:
    _ = AnalysisConfig(artifact_root=tmp_path / "artifacts", seeg_parcellation_name="yeo17")
    rms_trace, rms_support = derive_seeg_global_metric_trace(
        _region_signals(),
        _coverage(),
        patient_id="sub-01",
        metric_definition="rms",
        weighting_strategy="equal",
    )
    env_trace, _ = derive_seeg_global_metric_trace(
        _region_signals(),
        _coverage(),
        patient_id="sub-01",
        metric_definition="envelope-rms",
        weighting_strategy="equal",
    )
    weighted_trace, _ = derive_seeg_global_metric_trace(
        _region_signals(),
        _coverage(),
        patient_id="sub-01",
        metric_definition="spatial-std",
        weighting_strategy="sqrt-channel-count",
    )

    assert not rms_trace.empty
    assert rms_trace["n_networks_used"].iloc[0] == 3
    assert rms_support["is_selected"].sum() == 3
    assert not np.allclose(rms_trace["global_metric"], env_trace["global_metric"])
    assert not np.allclose(rms_trace["global_metric"], weighted_trace["global_metric"])


def test_run_exploratory_gfp_global_coupling_stage_writes_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", seeg_parcellation_name="yeo17")
    labels_path = tmp_path / "labels.parquet"
    gfp_trace_path = tmp_path / "gfp_trace.parquet"
    gfp_peaks_path = tmp_path / "gfp_peaks.parquet"
    global_trace_path = tmp_path / "global_trace.parquet"
    support_path = tmp_path / "network_support.parquet"
    write_dataframe(_eeg_labels(), labels_path)
    write_dataframe(_gfp_trace(), gfp_trace_path)
    write_dataframe(_gfp_peaks(), gfp_peaks_path)
    write_dataframe(_global_trace(), global_trace_path)
    write_dataframe(_network_support(), support_path)

    monkeypatch.setattr(
        pipelines,
        "run_eeg_states_stage",
        lambda *_args, **_kwargs: {"labels": labels_path, "gfp_trace": gfp_trace_path, "gfp_peaks": gfp_peaks_path},
    )
    monkeypatch.setattr(
        pipelines,
        "_ensure_seeg_global_metric_artifacts",
        lambda *_args, **_kwargs: ("gfp-shared", {"global_trace": global_trace_path, "network_support": support_path}),
    )
    monkeypatch.setattr(pipelines, "_eligible_rows", lambda *_args, **_kwargs: pd.DataFrame({"patient_id": ["sub-01"]}))

    outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="gfp-global-coupling",
        global_surrogates=8,
        min_subjects=1,
    )

    subject_df = read_dataframe(outputs["subject_effects"])
    group_df = read_dataframe(outputs["group_effects"])
    assert outputs["global_trace"] == global_trace_path
    assert subject_df["lag_ms"].tolist() == [0]
    assert group_df["lag_ms"].tolist() == [0]


def test_run_exploratory_lagged_gfp_global_coupling_stage_writes_multiple_lags(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", seeg_parcellation_name="yeo17")
    labels_path = tmp_path / "labels.parquet"
    gfp_trace_path = tmp_path / "gfp_trace.parquet"
    gfp_peaks_path = tmp_path / "gfp_peaks.parquet"
    global_trace_path = tmp_path / "global_trace.parquet"
    support_path = tmp_path / "network_support.parquet"
    write_dataframe(_eeg_labels(), labels_path)
    write_dataframe(_gfp_trace(), gfp_trace_path)
    write_dataframe(_gfp_peaks(), gfp_peaks_path)
    write_dataframe(_global_trace(), global_trace_path)
    write_dataframe(_network_support(), support_path)

    monkeypatch.setattr(
        pipelines,
        "run_eeg_states_stage",
        lambda *_args, **_kwargs: {"labels": labels_path, "gfp_trace": gfp_trace_path, "gfp_peaks": gfp_peaks_path},
    )
    monkeypatch.setattr(
        pipelines,
        "_ensure_seeg_global_metric_artifacts",
        lambda *_args, **_kwargs: ("gfp-shared", {"global_trace": global_trace_path, "network_support": support_path}),
    )
    monkeypatch.setattr(pipelines, "_eligible_rows", lambda *_args, **_kwargs: pd.DataFrame({"patient_id": ["sub-01"]}))

    outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="lagged-gfp-global-coupling",
        max_lag_ms=8,
        lag_step_ms=4,
        global_surrogates=8,
        min_subjects=1,
    )

    subject_df = read_dataframe(outputs["subject_effects"])
    assert sorted(subject_df["lag_ms"].tolist()) == [-8, -4, 0, 4, 8]


def test_run_exploratory_peak_gfp_global_coupling_stage_writes_symmetric_offsets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", seeg_parcellation_name="yeo17")
    labels_path = tmp_path / "labels.parquet"
    gfp_trace_path = tmp_path / "gfp_trace.parquet"
    gfp_peaks_path = tmp_path / "gfp_peaks.parquet"
    global_trace_path = tmp_path / "global_trace.parquet"
    support_path = tmp_path / "network_support.parquet"
    write_dataframe(_eeg_labels(), labels_path)
    write_dataframe(_gfp_trace(), gfp_trace_path)
    write_dataframe(_gfp_peaks(), gfp_peaks_path)
    write_dataframe(_global_trace(), global_trace_path)
    write_dataframe(_network_support(), support_path)

    monkeypatch.setattr(
        pipelines,
        "run_eeg_states_stage",
        lambda *_args, **_kwargs: {"labels": labels_path, "gfp_trace": gfp_trace_path, "gfp_peaks": gfp_peaks_path},
    )
    monkeypatch.setattr(
        pipelines,
        "_ensure_seeg_global_metric_artifacts",
        lambda *_args, **_kwargs: ("gfp-shared", {"global_trace": global_trace_path, "network_support": support_path}),
    )
    monkeypatch.setattr(pipelines, "_eligible_rows", lambda *_args, **_kwargs: pd.DataFrame({"patient_id": ["sub-01"]}))

    outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="peak-gfp-global-coupling",
        peak_window_sec=0.008,
        global_surrogates=8,
        min_subjects=1,
    )

    subject_df = read_dataframe(outputs["subject_effects"])
    assert set(subject_df.columns) >= {"offset_ms", "effect_mean_diff"}
    assert subject_df["offset_ms"].min() < 0
    assert subject_df["offset_ms"].max() > 0


def test_run_exploratory_gfp_controlled_microstate_stage_writes_profiles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", seeg_parcellation_name="yeo17")
    labels_path = tmp_path / "labels.parquet"
    gfp_trace_path = tmp_path / "gfp_trace.parquet"
    gfp_peaks_path = tmp_path / "gfp_peaks.parquet"
    global_trace_path = tmp_path / "global_trace.parquet"
    support_path = tmp_path / "network_support.parquet"
    write_dataframe(_eeg_labels(), labels_path)
    write_dataframe(_gfp_trace(), gfp_trace_path)
    write_dataframe(_gfp_peaks(), gfp_peaks_path)
    write_dataframe(_global_trace(), global_trace_path)
    write_dataframe(_network_support(), support_path)

    monkeypatch.setattr(
        pipelines,
        "run_eeg_states_stage",
        lambda *_args, **_kwargs: {"labels": labels_path, "gfp_trace": gfp_trace_path, "gfp_peaks": gfp_peaks_path},
    )
    monkeypatch.setattr(
        pipelines,
        "_ensure_seeg_global_metric_artifacts",
        lambda *_args, **_kwargs: ("gfp-shared", {"global_trace": global_trace_path, "network_support": support_path}),
    )
    monkeypatch.setattr(pipelines, "_eligible_rows", lambda *_args, **_kwargs: pd.DataFrame({"patient_id": ["sub-01"]}))

    outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="gfp-controlled-microstate",
        min_subjects=1,
    )

    subject_df = read_dataframe(outputs["subject_profiles"])
    omnibus_df = read_dataframe(outputs["group_omnibus"])
    posthoc_df = read_dataframe(outputs["group_posthoc"])
    assert set(subject_df.columns) >= {"microstate", "adjusted_global_metric", "gfp_beta"}
    assert not omnibus_df.empty
    assert not posthoc_df.empty


def test_run_exploratory_gfp_controlled_transition_stage_writes_transition_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", seeg_parcellation_name="yeo17")
    labels_path = tmp_path / "labels.parquet"
    gfp_trace_path = tmp_path / "gfp_trace.parquet"
    gfp_peaks_path = tmp_path / "gfp_peaks.parquet"
    global_trace_path = tmp_path / "global_trace.parquet"
    support_path = tmp_path / "network_support.parquet"
    transitions_path = tmp_path / "transitions.parquet"
    write_dataframe(_eeg_labels(), labels_path)
    write_dataframe(_gfp_trace(), gfp_trace_path)
    write_dataframe(_gfp_peaks(), gfp_peaks_path)
    write_dataframe(_global_trace(), global_trace_path)
    write_dataframe(_network_support(), support_path)
    write_dataframe(_transitions(), transitions_path)

    monkeypatch.setattr(
        pipelines,
        "_ensure_exploratory_event_tables",
        lambda *_args, **_kwargs: {"events": tmp_path / "events.parquet", "transitions": transitions_path},
    )
    monkeypatch.setattr(
        pipelines,
        "run_eeg_states_stage",
        lambda *_args, **_kwargs: {"labels": labels_path, "gfp_trace": gfp_trace_path, "gfp_peaks": gfp_peaks_path},
    )
    monkeypatch.setattr(
        pipelines,
        "_ensure_seeg_global_metric_artifacts",
        lambda *_args, **_kwargs: ("gfp-shared", {"global_trace": global_trace_path, "network_support": support_path}),
    )
    monkeypatch.setattr(pipelines, "_eligible_rows", lambda *_args, **_kwargs: pd.DataFrame({"patient_id": ["sub-01"]}))

    outputs = pipelines.run_exploratory_coupling_stage(
        cfg,
        analysis="gfp-controlled-transition",
        transition_window_sec=0.012,
        min_subjects=1,
    )

    subject_df = read_dataframe(outputs["subject_effects"])
    assert set(subject_df.columns) >= {"from_state", "to_state", "effect_mean_diff"}
    assert not subject_df.empty
