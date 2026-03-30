from __future__ import annotations

import mne
import numpy as np

from seeg_eegmicrostates.config import AnalysisConfig


def attach_standard_montage(raw: mne.io.BaseRaw, cfg: AnalysisConfig) -> mne.io.BaseRaw:
    mounted = raw.copy()
    montage = mne.channels.make_standard_montage(cfg.eeg_montage_name)
    mounted.set_montage(montage, on_missing="ignore")
    return mounted


def expand_to_target19(raw11: mne.io.BaseRaw, cfg: AnalysisConfig) -> tuple[mne.io.BaseRaw, tuple[str, ...]]:
    expanded = raw11.copy()
    missing = tuple(channel for channel in cfg.target19_channels if channel not in expanded.ch_names)
    if missing:
        info = mne.create_info(missing, expanded.info["sfreq"], ch_types="eeg")
        zeros = np.zeros((len(missing), expanded.n_times), dtype=float)
        missing_raw = mne.io.RawArray(zeros, info, verbose="ERROR")
        expanded.add_channels([missing_raw], force_update_info=True)
        expanded.info["bads"] = list(missing)
    montage = mne.channels.make_standard_montage(cfg.eeg_montage_name)
    expanded.set_montage(montage, on_missing="ignore")
    expanded.reorder_channels(list(cfg.target19_channels))
    return expanded, missing


def interpolate_missing_target_channels(raw19_partial: mne.io.BaseRaw) -> mne.io.BaseRaw:
    interpolated = raw19_partial.copy()
    if interpolated.info["bads"]:
        interpolated.interpolate_bads(reset_bads=True, mode="accurate", verbose="ERROR")
    return interpolated


def project_to_target19(raw11: mne.io.BaseRaw, cfg: AnalysisConfig) -> tuple[mne.io.BaseRaw, tuple[str, ...]]:
    mounted = attach_standard_montage(raw11, cfg)
    expanded, missing = expand_to_target19(mounted, cfg)
    restored = interpolate_missing_target_channels(expanded)
    return restored, missing
