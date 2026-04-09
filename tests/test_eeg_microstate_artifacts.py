from __future__ import annotations

from pathlib import Path

import mne
import numpy as np
import pandas as pd
import pytest
from pycrostates.cluster import ModKMeans
from pycrostates.io import ChData

from seeg_eegmicrostates._utils import read_dataframe
from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.eeg.microstates import (
    label_microstates,
    load_microstate_model,
    save_microstate_model,
    validate_microstate_model_channels,
)
from seeg_eegmicrostates.workflows import render_reports, run_eeg_states_stage
from seeg_eegmicrostates.workflows import pipelines


def _make_raw(cfg: AnalysisConfig, ch_names: tuple[str, ...] | None = None, *, n_times: int = 240) -> mne.io.BaseRaw:
    channels = list(ch_names or cfg.target19_channels)
    info = mne.create_info(channels, sfreq=cfg.eeg_resample_hz, ch_types="eeg")
    rng = np.random.default_rng(17)
    n_clusters = min(cfg.microstate_k, len(channels))
    patterns = rng.standard_normal((n_clusters, len(channels)))
    assignments = np.tile(np.arange(n_clusters), n_times // n_clusters + 1)[:n_times]
    data = patterns[assignments].T + 0.05 * rng.standard_normal((len(channels), n_times))
    raw = mne.io.RawArray(data, info, verbose="ERROR")
    raw.set_montage("standard_1020", verbose="ERROR")
    raw.set_eeg_reference("average", projection=False, verbose="ERROR")
    return raw


def _fit_model(raw: mne.io.BaseRaw, cfg: AnalysisConfig) -> ModKMeans:
    model = ModKMeans(
        n_clusters=min(cfg.microstate_k, raw.info["nchan"]),
        n_init=2,
        max_iter=20,
        random_state=cfg.random_seed,
    )
    model.fit(ChData(raw.get_data(), raw.info), picks="all")
    return model


def _stub_cohort() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "patient_id": "sub-01",
                "eeg_ref_path": "ignored_raw.fif",
                "start_sec": 0.0,
                "end_sec": 1.0,
            }
        ]
    )


def _touch_raw_cache(_raw: mne.io.BaseRaw, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    return path


def test_save_and_load_microstate_model_round_trip(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    model = _fit_model(_make_raw(cfg), cfg)
    path = save_microstate_model(model, tmp_path / "group_template.fif")
    loaded = load_microstate_model(path)
    assert path.exists()
    assert isinstance(loaded, ModKMeans)
    assert tuple(loaded.info["ch_names"]) == tuple(model.info["ch_names"])
    assert np.allclose(loaded.cluster_centers_, model.cluster_centers_)


def test_validate_microstate_model_channels_rejects_incompatible_template(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    model = _fit_model(
        _make_raw(cfg, ("Fp1", "Fp2", "F3", "F4", "Fz", "C3", "C4", "P3", "P4", "O1", "O2")),
        cfg,
    )
    with pytest.raises(ValueError, match="allowed EEG template layouts"):
        validate_microstate_model_channels(
            model,
            cfg.target19_channels,
            alternate_channels=cfg.standard11_channels,
        )


def test_validate_microstate_model_channels_accepts_standard11_template(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    model = _fit_model(_make_raw(cfg, cfg.standard11_channels), cfg)
    validate_microstate_model_channels(
        model,
        cfg.target19_channels,
        alternate_channels=cfg.standard11_channels,
    )


def test_label_microstates_preserves_expected_table_shape(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    raw = _make_raw(cfg)
    model = _fit_model(raw, cfg)
    labels = label_microstates(raw, model, cfg, patient_id="sub-01")
    assert list(labels.columns) == ["patient_id", "time_sec", "sample", "microstate", "corr"]
    assert len(labels) == raw.n_times
    assert (labels["microstate"] >= 0).all()
    assert ((0.0 <= labels["corr"]) & (labels["corr"] <= 1.0)).all()


def test_run_eeg_states_stage_uses_external_template_without_refitting(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    raw = _make_raw(cfg)
    external_model = _fit_model(_make_raw(cfg, cfg.standard11_channels), cfg)
    external_path = save_microstate_model(external_model, tmp_path / "external_template.fif")
    fit_calls = {"count": 0}

    def fail_fit(*args, **kwargs):
        fit_calls["count"] += 1
        raise AssertionError("fit_group_microstate_model should not run when --template-fif is supplied.")

    monkeypatch.setattr(pipelines, "_eligible_rows", lambda _: _stub_cohort())
    monkeypatch.setattr(pipelines, "preprocess_eeg_recording", lambda *args, **kwargs: (raw.copy(), ()))
    monkeypatch.setattr(pipelines, "save_raw_fif", _touch_raw_cache)
    monkeypatch.setattr(pipelines, "fit_group_microstate_model", fail_fit, raising=False)

    outputs = run_eeg_states_stage(cfg, template_fif=str(external_path))
    labels = read_dataframe(outputs["labels"])
    gfp_trace = read_dataframe(outputs["gfp_trace"])
    gfp_peaks = read_dataframe(outputs["gfp_peaks"])
    staged_model = load_microstate_model(outputs["model"])
    assert fit_calls["count"] == 0
    assert outputs["model"].suffix == ".fif"
    assert outputs["model"].exists()
    assert labels["patient_id"].tolist() == ["sub-01"] * raw.n_times
    assert gfp_trace["sample"].tolist() == labels["sample"].tolist()
    assert not gfp_peaks.empty
    assert tuple(staged_model.info["ch_names"]) == cfg.standard11_channels


def test_run_eeg_states_stage_uses_default_template_without_refitting(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    raw = _make_raw(cfg)
    default_model = _fit_model(_make_raw(cfg, cfg.target19_channels), cfg)
    save_microstate_model(default_model, cfg.default_eeg_template_fif)
    fit_calls = {"count": 0}

    def fail_fit(*args, **kwargs):
        fit_calls["count"] += 1
        raise AssertionError("fit_group_microstate_model should not run when the default template is configured.")

    monkeypatch.setattr(pipelines, "_eligible_rows", lambda _: _stub_cohort())
    monkeypatch.setattr(pipelines, "preprocess_eeg_recording", lambda *args, **kwargs: (raw.copy(), ()))
    monkeypatch.setattr(pipelines, "save_raw_fif", _touch_raw_cache)
    monkeypatch.setattr(pipelines, "fit_group_microstate_model", fail_fit, raising=False)

    outputs = run_eeg_states_stage(cfg)
    labels = read_dataframe(outputs["labels"])
    gfp_trace = read_dataframe(outputs["gfp_trace"])
    gfp_peaks = read_dataframe(outputs["gfp_peaks"])
    staged_model = load_microstate_model(outputs["model"])
    assert fit_calls["count"] == 0
    assert outputs["model"].exists()
    assert labels["patient_id"].tolist() == ["sub-01"] * raw.n_times
    assert len(gfp_trace) == len(labels)
    assert {"patient_id", "peak_id", "event_sec", "sample", "gfp"} == set(gfp_peaks.columns)
    assert tuple(staged_model.info["ch_names"]) == cfg.target19_channels


def test_run_eeg_states_stage_requires_default_template_when_no_override(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    with pytest.raises(FileNotFoundError, match="default EEG template"):
        run_eeg_states_stage(cfg)


def test_run_eeg_states_stage_rejects_incompatible_external_template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    raw = _make_raw(cfg)
    incompatible_model = _fit_model(
        _make_raw(cfg, ("Fp1", "Fp2", "F3", "F4", "Fz", "C3", "C4", "P3", "P4", "O1", "O2")),
        cfg,
    )
    external_path = save_microstate_model(incompatible_model, tmp_path / "incompatible_template.fif")

    monkeypatch.setattr(pipelines, "_eligible_rows", lambda _: _stub_cohort())
    monkeypatch.setattr(pipelines, "preprocess_eeg_recording", lambda *args, **kwargs: (raw.copy(), ()))
    monkeypatch.setattr(pipelines, "save_raw_fif", _touch_raw_cache)

    with pytest.raises(ValueError, match="allowed EEG template layouts"):
        run_eeg_states_stage(cfg, template_fif=str(external_path))


def test_render_reports_does_not_export_standalone_eeg_microstate_templates(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    model = _fit_model(_make_raw(cfg), cfg)
    save_microstate_model(model, cfg.cache_path("eeg", "group_microstate_model", ext="fif", branch="band_1_40"))
    outputs = render_reports(cfg)
    assert outputs == {}


def test_run_eeg_states_stage_reuses_cached_gfp_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    cached = {
        "model": cfg.cache_path("eeg", "group_microstate_model", ext="fif", branch="band_1_40"),
        "labels": cfg.cache_path("eeg", "microstate_labels", ext="parquet", branch="band_1_40"),
        "restored_channels": cfg.cache_path("eeg", "restored_channels", ext="parquet", branch="band_1_40"),
        "gfp_trace": cfg.cache_path("eeg", "gfp_trace", ext="parquet", branch="band_1_40"),
        "gfp_peaks": cfg.cache_path("eeg", "gfp_peaks", ext="parquet", branch="band_1_40"),
    }
    model = _fit_model(_make_raw(cfg), cfg)
    save_microstate_model(model, cached["model"])
    readback = pd.DataFrame({"patient_id": ["sub-01"], "sample": [0]})
    readback.to_parquet(cached["labels"], index=False)
    readback.to_parquet(cached["restored_channels"], index=False)
    pd.DataFrame({"patient_id": ["sub-01"], "sample": [0], "time_sec": [0.0], "gfp": [1.0]}).to_parquet(
        cached["gfp_trace"],
        index=False,
    )
    pd.DataFrame({"patient_id": ["sub-01"], "peak_id": [0], "event_sec": [0.0], "sample": [0], "gfp": [1.0]}).to_parquet(
        cached["gfp_peaks"],
        index=False,
    )
    monkeypatch.setattr(pipelines, "_eligible_rows", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should reuse cached EEG artifacts")))
    outputs = run_eeg_states_stage(cfg)
    assert outputs == cached
