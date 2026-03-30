from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from seeg_eegmicrostates._utils import write_dataframe
from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.coupling.connectivity import (
    compute_subject_microstate_connectivity_effects,
    connectivity_analysis_branch,
    normalize_connectivity_method,
)
from seeg_eegmicrostates.workflows.pipelines import run_band_limited_connectivity_branch


def test_compute_subject_microstate_connectivity_effects_detects_state_specific_pairing() -> None:
    rng = np.random.default_rng(7)
    strong = np.sin(np.linspace(0.0, 12.0 * np.pi, 80, endpoint=False))
    strong_shifted = np.sin(np.linspace(0.3, 12.0 * np.pi + 0.3, 80, endpoint=False))
    weak_a = rng.standard_normal(80)
    weak_b = rng.standard_normal(80)
    aligned = pd.DataFrame(
        {
            "patient_id": ["sub-01"] * 160,
            "time_sec": np.arange(160, dtype=float) / 100.0,
            "microstate": np.concatenate([np.zeros(80, dtype=int), np.ones(80, dtype=int)]),
            "corr": np.ones(160, dtype=float),
            "DefaultA": np.concatenate([strong, weak_a]),
            "DefaultB": np.concatenate([strong_shifted, weak_b]),
            "LimbicB": rng.standard_normal(160),
        }
    )
    for method in ("corr", "plv", "wpli"):
        effects = compute_subject_microstate_connectivity_effects(aligned, min_samples=20, method=method)
        pair = effects[
            (effects["microstate"] == 0)
            & (effects["network_a"] == "DefaultA")
            & (effects["network_b"] == "DefaultB")
        ].iloc[0]
        assert pair["method"] == method
        assert pair["state_connectivity"] > pair["off_connectivity"]
        assert pair["effect_mean_diff"] > 0.1


def test_connectivity_method_helpers_normalize_and_name_branches() -> None:
    assert normalize_connectivity_method("correlation") == "corr"
    assert normalize_connectivity_method("PLV") == "plv"
    assert normalize_connectivity_method("weighted_phase_lag_index") == "wpli"
    assert connectivity_analysis_branch("plv") == "band_1_40_plv"


def test_run_band_limited_connectivity_branch_reuses_cached_outputs(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    cached = {
        "aligned": cfg.cache_path("coupling", "aligned_connectivity", ext="parquet", branch="band_1_40_plv"),
        "subject_effects": cfg.cache_path("coupling", "subject_connectivity_effects", ext="parquet", branch="band_1_40_plv"),
        "group_effects": cfg.cache_path("stats", "group_connectivity_effects", ext="parquet", branch="band_1_40_plv"),
    }
    for path in cached.values():
        write_dataframe(pd.DataFrame({"value": [1]}), path)
    outputs = run_band_limited_connectivity_branch(cfg, method="plv")
    for key, path in cached.items():
        assert outputs[key] == path
    assert outputs["subject_effects_excel"].exists()
    assert outputs["group_effects_excel"].exists()
