from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.workflows.seizure import (
    _fixed_reference_paths,
    _require_fixed_references,
    build_seizure_stage_index_artifacts,
    export_seizure_stage_tables,
)


def _write_workbook(path: Path) -> None:
    patient_info = pd.DataFrame({"ID": ["sub-01"]})
    annot_info = pd.DataFrame(
        [
            {
                "ID": "sub-01",
                "status1": "SZ1",
                "status2": "CPS",
                "pre_start": 0.0,
                "pre_during": 10.0,
                "pre_end": 10.0,
                "LVFA_start": 10.0,
                "LVFA_during": 2.0,
                "LVFA_end": 12.0,
                "SZ_start": 12.0,
                "SZ_during": 20.0,
                "SZ_end": 32.0,
                "post_start": 32.0,
                "post_during": 15.0,
                "post_end": 47.0,
            }
        ]
    )
    with pd.ExcelWriter(path) as writer:
        patient_info.to_excel(writer, sheet_name="patient_info", index=False)
        annot_info.to_excel(writer, sheet_name="annot_info", index=False)


def _write_assets(root: Path) -> None:
    patient = root / "sub-01"
    ref = patient / "ref"
    bipolar = patient / "bipolar"
    atlas = patient / "MNI"
    ref.mkdir(parents=True)
    bipolar.mkdir(parents=True)
    atlas.mkdir(parents=True)
    (ref / "SZ1_CPS_eeg.fif").write_text("", encoding="utf-8")
    (ref / "SZ1_CPS_seeg.fif").write_text("", encoding="utf-8")
    (bipolar / "SZ1_CPS_seeg.fif").write_text("", encoding="utf-8")
    (atlas / "Atlas.tsv").write_text("name\n", encoding="utf-8")


def test_build_seizure_stage_index_artifacts_writes_cache_outputs(tmp_path: Path) -> None:
    workbook = tmp_path / "info_patient.xlsx"
    data_root = tmp_path / "data"
    _write_workbook(workbook)
    _write_assets(data_root)
    cfg = AnalysisConfig(workbook_path=workbook, data_root=data_root, artifact_root=tmp_path / "artifacts")

    outputs = build_seizure_stage_index_artifacts(cfg)

    segments = pd.read_parquet(outputs["segments"])
    recording_index = pd.read_parquet(outputs["recording_index"])
    denominators = pd.read_parquet(outputs["denominators"])
    assert segments.shape[0] == 4
    assert bool(recording_index.loc[0, "eligible_paired_eeg_seeg"]) is True
    assert denominators["n_usable_segments"].sum() == 12


def test_export_seizure_stage_tables_exports_available_index_tables(tmp_path: Path) -> None:
    workbook = tmp_path / "info_patient.xlsx"
    data_root = tmp_path / "data"
    _write_workbook(workbook)
    _write_assets(data_root)
    cfg = AnalysisConfig(
        workbook_path=workbook,
        data_root=data_root,
        artifact_root=tmp_path / "artifacts",
        run_timestamp="test_run",
    )
    build_seizure_stage_index_artifacts(cfg)

    outputs = export_seizure_stage_tables(cfg)

    assert outputs["segments_csv"].exists()
    assert outputs["manifest_csv"].exists()
    manifest = pd.read_csv(outputs["manifest_csv"])
    assert {"segments", "recording_index", "denominators"}.issubset(set(manifest["table"]))


def test_fixed_reference_check_reports_missing_ide_a_artifacts(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    paths = _fixed_reference_paths(cfg)

    with pytest.raises(FileNotFoundError, match="Missing fixed IDE_A reference artifacts"):
        _require_fixed_references(paths)
