from __future__ import annotations

from pathlib import Path

import mne

from seeg_eegmicrostates.io.fif import read_raw_fif


def load_and_crop_bipolar_seeg(seeg_path: str | Path, start_sec: float, end_sec: float) -> mne.io.BaseRaw:
    raw = read_raw_fif(seeg_path, preload=False)
    max_time = raw.times[-1]
    tmin = max(0.0, float(start_sec))
    tmax = min(float(end_sec), float(max_time))
    raw.crop(tmin=tmin, tmax=tmax, include_tmax=False)
    raw.load_data()
    return raw
