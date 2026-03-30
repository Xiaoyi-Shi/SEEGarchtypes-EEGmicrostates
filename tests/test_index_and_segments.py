from __future__ import annotations

from pathlib import Path

import mne
import numpy as np
import pandas as pd

from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.qc.cohort import build_main_cohort
from seeg_eegmicrostates.segment.ide_a import build_ide_a_segments


def _write_eeg(path: Path, ch_names: list[str]) -> Path:
    info = mne.create_info(ch_names, sfreq=250.0, ch_types="eeg")
    data = np.random.default_rng(1).standard_normal((len(ch_names), 500))
    raw = mne.io.RawArray(data, info, verbose="ERROR")
    raw.save(path, overwrite=True, verbose="ERROR")
    return path


def test_build_ide_a_segments_materializes_valid_windows() -> None:
    annotation_info = pd.DataFrame(
        [
            {"ID": "sub-01", "status1": "IDE", "status2": "A", "rest_start": 20.0, "rest_end": 200.0, "rest_during": 180.0},
            {"ID": "sub-02", "status1": "IDE", "status2": "A", "rest_start": None, "rest_end": 200.0, "rest_during": 180.0},
        ]
    )
    segments = build_ide_a_segments(annotation_info)
    assert len(segments) == 2
    assert bool(segments.loc[0, "usable_segment"]) is True
    assert bool(segments.loc[1, "usable_segment"]) is False


def test_build_main_cohort_filters_missing_channels(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    good_path = _write_eeg(tmp_path / "good_raw.fif", list(cfg.standard11_channels))
    bad_path = _write_eeg(tmp_path / "bad_raw.fif", list(cfg.standard11_channels[:-1]))
    recording_index = pd.DataFrame(
        [
            {
                "patient_id": "good",
                "state": "IDE_A",
                "eeg_ref_path": str(good_path),
                "seeg_ref_path": "good_seeg.fif",
                "seeg_bipolar_path": "good_bipolar.fif",
                "atlas_path": "good_atlas.tsv",
                "has_eeg": True,
                "has_ref_seeg": True,
                "has_bipolar": True,
                "has_atlas": True,
            },
            {
                "patient_id": "bad",
                "state": "IDE_A",
                "eeg_ref_path": str(bad_path),
                "seeg_ref_path": "bad_seeg.fif",
                "seeg_bipolar_path": "bad_bipolar.fif",
                "atlas_path": "bad_atlas.tsv",
                "has_eeg": True,
                "has_ref_seeg": True,
                "has_bipolar": True,
                "has_atlas": True,
            },
        ]
    )
    segments = pd.DataFrame(
        [
            {"patient_id": "good", "state": "IDE_A", "start_sec": 0.0, "end_sec": 1.0, "duration_sec": 1.0, "usable_segment": True},
            {"patient_id": "bad", "state": "IDE_A", "start_sec": 0.0, "end_sec": 1.0, "duration_sec": 1.0, "usable_segment": True},
        ]
    )
    cohort, inventory = build_main_cohort(recording_index, segments, cfg)
    assert cohort.loc[cohort["patient_id"] == "good", "include_main"].item() is True
    assert cohort.loc[cohort["patient_id"] == "bad", "include_main"].item() is False
    assert "O2" in cohort.loc[cohort["patient_id"] == "bad", "missing_channels"].item()
    assert len(inventory) == 2
