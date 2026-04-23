from __future__ import annotations

from pathlib import Path

import pandas as pd

from seeg_eegmicrostates.io.index import scan_seizure_repository
from seeg_eegmicrostates.segment.seizure import build_seizure_stage_segments, seizure_recording_states


def _seizure_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "ID": 523619,
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
    row.update(overrides)
    return row


def test_build_seizure_stage_segments_materializes_four_stage_rows() -> None:
    segments = build_seizure_stage_segments(pd.DataFrame([_seizure_row()]))

    assert list(segments["stage"]) == ["pre", "LVFA", "SZ", "post"]
    assert segments["recording_state"].unique().tolist() == ["SZ1_CPS"]
    assert segments["seizure_type"].unique().tolist() == ["CPS"]
    assert segments["usable_segment"].tolist() == [True, True, True, True]
    assert segments.loc[segments["stage"] == "LVFA", "duration_sec"].item() == 2.0


def test_build_seizure_stage_segments_reports_invalid_timing() -> None:
    segments = build_seizure_stage_segments(
        pd.DataFrame(
            [
                _seizure_row(pre_during=None),
                _seizure_row(status1="SZ2", SZ_end=11.0, SZ_during=20.0),
            ]
        )
    )

    pre = segments[(segments["recording_state"] == "SZ1_CPS") & (segments["stage"] == "pre")].iloc[0]
    sz = segments[(segments["recording_state"] == "SZ2_CPS") & (segments["stage"] == "SZ")].iloc[0]
    assert bool(pre["usable_segment"]) is False
    assert "missing_stage_timing" in pre["qc_reason"]
    assert bool(sz["usable_segment"]) is False
    assert "non_positive_duration" in sz["qc_reason"]


def test_build_seizure_stage_segments_tolerates_small_boundary_differences() -> None:
    segments = build_seizure_stage_segments(
        pd.DataFrame([_seizure_row(LVFA_start=10.0005, LVFA_during=1.9995)]),
        timing_tolerance_sec=0.001,
    )

    lvfa = segments[segments["stage"] == "LVFA"].iloc[0]
    assert bool(lvfa["usable_segment"]) is True
    assert bool(lvfa["timing_tolerance_applied"]) is True
    assert "tolerated" in lvfa["qc_reason"]


def test_scan_seizure_repository_marks_seeg_only_and_paired_eligibility(tmp_path: Path) -> None:
    segments = build_seizure_stage_segments(
        pd.DataFrame(
            [
                _seizure_row(ID="sub-01", status1="SZ1", status2="CPS"),
                _seizure_row(ID="sub-02", status1="SZ1", status2="GTCS"),
            ]
        )
    )
    recordings = seizure_recording_states(segments)
    for patient_id, state, include_eeg in [("sub-01", "SZ1_CPS", True), ("sub-02", "SZ1_GTCS", False)]:
        ref = tmp_path / patient_id / "ref"
        bipolar = tmp_path / patient_id / "bipolar"
        atlas = tmp_path / patient_id / "MNI"
        ref.mkdir(parents=True)
        bipolar.mkdir(parents=True)
        atlas.mkdir(parents=True)
        if include_eeg:
            (ref / f"{state}_eeg.fif").write_text("", encoding="utf-8")
        (ref / f"{state}_seeg.fif").write_text("", encoding="utf-8")
        (bipolar / f"{state}_seeg.fif").write_text("", encoding="utf-8")
        (atlas / "Atlas.tsv").write_text("name\n", encoding="utf-8")

    indexed = scan_seizure_repository(tmp_path, recordings)

    paired = indexed[indexed["patient_id"] == "sub-01"].iloc[0]
    seeg_only = indexed[indexed["patient_id"] == "sub-02"].iloc[0]
    assert bool(paired["eligible_seeg_stage"]) is True
    assert bool(paired["eligible_paired_eeg_seeg"]) is True
    assert bool(seeg_only["eligible_seeg_stage"]) is True
    assert bool(seeg_only["eligible_paired_eeg_seeg"]) is False
    assert seeg_only["missing_assets"] == "eeg"


def test_scan_seizure_repository_reports_missing_seeg_or_atlas_assets(tmp_path: Path) -> None:
    segments = build_seizure_stage_segments(pd.DataFrame([_seizure_row(ID="sub-01")]))
    recordings = seizure_recording_states(segments)
    ref = tmp_path / "sub-01" / "ref"
    ref.mkdir(parents=True)
    (ref / "SZ1_CPS_eeg.fif").write_text("", encoding="utf-8")

    indexed = scan_seizure_repository(tmp_path, recordings)

    row = indexed.iloc[0]
    assert bool(row["eligible_seeg_stage"]) is False
    assert bool(row["eligible_paired_eeg_seeg"]) is False
    assert "bipolar_seeg" in row["missing_assets"]
    assert "atlas" in row["missing_assets"]
