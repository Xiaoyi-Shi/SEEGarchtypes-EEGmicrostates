from __future__ import annotations

from pathlib import Path

import pandas as pd

from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.io.fif import read_raw_fif
from seeg_eegmicrostates.qc.eeg_channels import channel_coverage_report


def inspect_eeg_channel_inventory(eeg_path: str | Path, cfg: AnalysisConfig) -> dict[str, object]:
    raw = read_raw_fif(eeg_path, preload=False)
    report = channel_coverage_report(raw.ch_names, cfg.standard11_channels)
    return {
        "n_eeg_channels": len(raw.ch_names),
        "original_channels": list(raw.ch_names),
        "present_channels": list(report["present_channels"]),
        "missing_channels": list(report["missing_channels"]),
        "extra_channels": list(report["extra_channels"]),
        "covers_standard11": bool(report["covers_required"]),
    }


def build_main_cohort(
    recording_index: pd.DataFrame,
    segments: pd.DataFrame,
    cfg: AnalysisConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    eligible_segments = segments[segments["usable_segment"]].copy()
    merged = recording_index.merge(eligible_segments, on=["patient_id", "state"], how="left")
    rows: list[dict[str, object]] = []
    inventories: list[dict[str, object]] = []
    for row in merged.to_dict(orient="records"):
        include = bool(row.get("has_eeg")) and bool(row.get("has_bipolar")) and bool(row.get("has_atlas"))
        reason = ""
        coverage = {
            "n_eeg_channels": pd.NA,
            "original_channels": [],
            "present_channels": [],
            "missing_channels": [],
            "extra_channels": [],
            "covers_standard11": False,
        }
        if not row.get("usable_segment", False):
            include = False
            reason = f"invalid_{cfg.analysis_state_token}_segment"
        elif not include:
            include = False
            reason = "missing_required_assets"
        else:
            coverage = inspect_eeg_channel_inventory(row["eeg_ref_path"], cfg)
            inventories.append({"patient_id": row["patient_id"], **coverage})
            if not coverage["covers_standard11"]:
                include = False
                reason = "missing_standard11_channels"
        rows.append(
            {
                "patient_id": row["patient_id"],
                "state": row["state"],
                "include_main": include,
                "reason_excluded": "" if include else reason,
                "eeg_ref_path": row["eeg_ref_path"],
                "seeg_ref_path": row["seeg_ref_path"],
                "seeg_bipolar_path": row["seeg_bipolar_path"],
                "atlas_path": row["atlas_path"],
                "start_sec": row.get("start_sec"),
                "end_sec": row.get("end_sec"),
                "duration_sec": row.get("duration_sec"),
                "covers_standard11": coverage["covers_standard11"],
                "missing_channels": coverage["missing_channels"],
            }
        )
    inventory_df = pd.DataFrame(inventories)
    return pd.DataFrame(rows), inventory_df
