from __future__ import annotations

from pathlib import Path

import pandas as pd

from seeg_eegmicrostates._utils import write_dataframe
from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.workflows.pipelines import run_activity_effects_stage


def test_branch_specific_cache_paths(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    main_path = cfg.cache_path("eeg", "microstate_labels", ext="parquet", branch="main")
    band_path = cfg.cache_path("eeg", "microstate_labels", ext="parquet", branch="band_1_40")
    assert main_path != band_path
    assert "main" in main_path.name
    assert "band_1_40" in band_path.name


def test_run_activity_effects_stage_reuses_cached_outputs(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    cached = {
        "aligned": cfg.cache_path("coupling", "aligned_activity", ext="parquet", branch="band_1_40_activity"),
        "subject_effects": cfg.cache_path(
            "coupling",
            "subject_activity_effects",
            ext="parquet",
            branch="band_1_40_activity",
        ),
        "group_effects": cfg.cache_path(
            "stats",
            "group_activity_effects",
            ext="parquet",
            branch="band_1_40_activity",
        ),
    }
    for path in cached.values():
        write_dataframe(pd.DataFrame({"value": [1]}), path)
    outputs = run_activity_effects_stage(cfg)
    for key, path in cached.items():
        assert outputs[key] == path
    assert outputs["subject_effects_excel"].exists()
    assert outputs["group_effects_excel"].exists()
