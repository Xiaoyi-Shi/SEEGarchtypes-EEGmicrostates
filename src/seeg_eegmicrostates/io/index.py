from __future__ import annotations

from pathlib import Path
import re

import pandas as pd


def _preferred_match(paths: list[Path], exact_name: str) -> Path | None:
    if not paths:
        return None
    for path in paths:
        if path.name == exact_name:
            return path
    return sorted(paths)[0]


def scan_repository(data_root: str | Path) -> pd.DataFrame:
    root = Path(data_root)
    rows: list[dict[str, object]] = []
    for patient_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        patient_id = patient_dir.name
        ref_dir = patient_dir / "ref"
        bipolar_dir = patient_dir / "bipolar"
        atlas_path = patient_dir / "MNI" / "Atlas.tsv"
        eeg_path = _preferred_match(list(ref_dir.glob("IDE_A_eeg.fif")), "IDE_A_eeg.fif") if ref_dir.exists() else None
        ref_seeg_path = _preferred_match(list(ref_dir.glob("IDE_A_seeg*.fif")), "IDE_A_seeg.fif") if ref_dir.exists() else None
        bipolar_seeg_path = (
            _preferred_match(list(bipolar_dir.glob("IDE_A_seeg*.fif")), "IDE_A_seeg.fif")
            if bipolar_dir.exists()
            else None
        )
        rows.append(
            {
                "patient_id": patient_id,
                "state": "IDE_A",
                "eeg_ref_path": str(eeg_path) if eeg_path else pd.NA,
                "seeg_ref_path": str(ref_seeg_path) if ref_seeg_path else pd.NA,
                "seeg_bipolar_path": str(bipolar_seeg_path) if bipolar_seeg_path else pd.NA,
                "atlas_path": str(atlas_path) if atlas_path.exists() else pd.NA,
                "has_eeg": eeg_path is not None,
                "has_ref_seeg": ref_seeg_path is not None,
                "has_bipolar": bipolar_seeg_path is not None,
                "has_atlas": atlas_path.exists(),
            }
        )
    return pd.DataFrame(rows)
