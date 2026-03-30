from __future__ import annotations

from pathlib import Path

import mne

from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.eeg.montage19 import project_to_target19
from seeg_eegmicrostates.io.fif import read_raw_fif
from seeg_eegmicrostates.qc.eeg_channels import canonicalize_channel_name


def load_and_crop_eeg(eeg_path: str | Path, start_sec: float, end_sec: float) -> mne.io.BaseRaw:
    raw = read_raw_fif(eeg_path, preload=False)
    max_time = raw.times[-1]
    tmin = max(0.0, float(start_sec))
    tmax = min(float(end_sec), float(max_time))
    raw.crop(tmin=tmin, tmax=tmax, include_tmax=False)
    raw.load_data()
    return raw


def normalize_eeg_channel_names(raw: mne.io.BaseRaw) -> mne.io.BaseRaw:
    renamed = raw.copy()
    renamed.rename_channels({name: canonicalize_channel_name(name) for name in renamed.ch_names})
    return renamed


def select_standard11(raw: mne.io.BaseRaw, cfg: AnalysisConfig) -> mne.io.BaseRaw:
    selected = raw.copy().pick(list(cfg.standard11_channels))
    selected.reorder_channels(list(cfg.standard11_channels))
    return selected


def preprocess_eeg_recording(
    eeg_path: str | Path,
    *,
    start_sec: float,
    end_sec: float,
    cfg: AnalysisConfig,
    band: tuple[float, float],
) -> tuple[mne.io.BaseRaw, tuple[str, ...]]:
    raw = load_and_crop_eeg(eeg_path, start_sec, end_sec)
    raw = normalize_eeg_channel_names(raw)
    raw = select_standard11(raw, cfg)
    raw.filter(band[0], band[1], verbose="ERROR")
    raw.resample(cfg.eeg_resample_hz, verbose="ERROR")
    raw19, missing = project_to_target19(raw, cfg)
    raw19.set_eeg_reference("average", projection=False, verbose="ERROR")
    return raw19, missing
