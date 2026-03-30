from __future__ import annotations

from pathlib import Path

import mne


def read_raw_fif(path: str | Path, *, preload: bool = False) -> mne.io.BaseRaw:
    return mne.io.read_raw_fif(path, preload=preload, verbose="ERROR")


def save_raw_fif(raw: mne.io.BaseRaw, path: str | Path, *, overwrite: bool = True) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    raw.save(output_path, overwrite=overwrite, verbose="ERROR")
    return output_path
