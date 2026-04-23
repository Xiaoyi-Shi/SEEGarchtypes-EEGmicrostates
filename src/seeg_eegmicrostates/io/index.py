from __future__ import annotations

from pathlib import Path

import pandas as pd


def _preferred_match(paths: list[Path], exact_name: str) -> Path | None:
    if not paths:
        return None
    for path in paths:
        if path.name == exact_name:
            return path
    return sorted(paths)[0]


def scan_repository(data_root: str | Path, *, analysis_state: str = "IDE_A") -> pd.DataFrame:
    root = Path(data_root)
    state = str(analysis_state).strip().upper()
    eeg_name = f"{state}_eeg.fif"
    seeg_name = f"{state}_seeg.fif"
    seeg_glob = f"{state}_seeg*.fif"
    rows: list[dict[str, object]] = []
    for patient_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        patient_id = patient_dir.name
        ref_dir = patient_dir / "ref"
        bipolar_dir = patient_dir / "bipolar"
        atlas_path = patient_dir / "MNI" / "Atlas.tsv"
        eeg_path = _preferred_match(list(ref_dir.glob(eeg_name)), eeg_name) if ref_dir.exists() else None
        ref_seeg_path = _preferred_match(list(ref_dir.glob(seeg_glob)), seeg_name) if ref_dir.exists() else None
        bipolar_seeg_path = (
            _preferred_match(list(bipolar_dir.glob(seeg_glob)), seeg_name)
            if bipolar_dir.exists()
            else None
        )
        rows.append(
            {
                "patient_id": patient_id,
                "state": state,
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


def scan_seizure_repository(data_root: str | Path, seizure_recordings: pd.DataFrame) -> pd.DataFrame:
    root = Path(data_root)
    columns = [
        "patient_id",
        "seizure_id",
        "seizure_type",
        "recording_state",
        "eeg_ref_path",
        "seeg_ref_path",
        "seeg_bipolar_path",
        "atlas_path",
        "has_eeg",
        "has_ref_seeg",
        "has_bipolar",
        "has_atlas",
        "eligible_seeg_stage",
        "eligible_paired_eeg_seeg",
        "missing_assets",
    ]
    if seizure_recordings.empty:
        return pd.DataFrame(columns=columns)
    rows: list[dict[str, object]] = []
    for recording in seizure_recordings.drop_duplicates(["patient_id", "recording_state"]).to_dict(orient="records"):
        patient_id = str(recording["patient_id"])
        state = str(recording["recording_state"]).strip().upper()
        patient_dir = root / patient_id
        ref_dir = patient_dir / "ref"
        bipolar_dir = patient_dir / "bipolar"
        atlas_path = patient_dir / "MNI" / "Atlas.tsv"
        eeg_path = ref_dir / f"{state}_eeg.fif"
        ref_seeg_path = ref_dir / f"{state}_seeg.fif"
        bipolar_seeg_path = bipolar_dir / f"{state}_seeg.fif"
        has_eeg = eeg_path.exists()
        has_ref_seeg = ref_seeg_path.exists()
        has_bipolar = bipolar_seeg_path.exists()
        has_atlas = atlas_path.exists()
        missing_assets = [
            name
            for name, present in (
                ("eeg", has_eeg),
                ("ref_seeg", has_ref_seeg),
                ("bipolar_seeg", has_bipolar),
                ("atlas", has_atlas),
            )
            if not present
        ]
        eligible_seeg = bool(has_ref_seeg and has_bipolar and has_atlas)
        rows.append(
            {
                "patient_id": patient_id,
                "seizure_id": str(recording["seizure_id"]),
                "seizure_type": str(recording["seizure_type"]),
                "recording_state": state,
                "eeg_ref_path": str(eeg_path) if has_eeg else pd.NA,
                "seeg_ref_path": str(ref_seeg_path) if has_ref_seeg else pd.NA,
                "seeg_bipolar_path": str(bipolar_seeg_path) if has_bipolar else pd.NA,
                "atlas_path": str(atlas_path) if has_atlas else pd.NA,
                "has_eeg": has_eeg,
                "has_ref_seeg": has_ref_seeg,
                "has_bipolar": has_bipolar,
                "has_atlas": has_atlas,
                "eligible_seeg_stage": eligible_seeg,
                "eligible_paired_eeg_seeg": bool(eligible_seeg and has_eeg),
                "missing_assets": ";".join(missing_assets) if missing_assets else "none",
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values(["patient_id", "recording_state"]).reset_index(drop=True)
