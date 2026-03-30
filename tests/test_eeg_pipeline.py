from __future__ import annotations

from pathlib import Path

import mne
import numpy as np

from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.eeg.montage19 import project_to_target19


def _make_raw(ch_names: list[str], n_times: int = 500) -> mne.io.BaseRaw:
    info = mne.create_info(ch_names, sfreq=250.0, ch_types="eeg")
    data = np.random.default_rng(0).standard_normal((len(ch_names), n_times))
    raw = mne.io.RawArray(data, info, verbose="ERROR")
    return raw


def test_project_to_target19_restores_missing_channels(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    raw11 = _make_raw(list(cfg.standard11_channels))
    projected, missing = project_to_target19(raw11, cfg)
    assert tuple(projected.ch_names) == cfg.target19_channels
    assert set(missing) == {"Fp1", "Fp2", "F7", "F8", "T7", "T8", "P7", "P8"}
    assert projected.info["bads"] == []
    assert projected.get_data().shape[0] == len(cfg.target19_channels)
