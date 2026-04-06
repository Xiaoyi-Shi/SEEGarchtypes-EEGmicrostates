from __future__ import annotations

from pathlib import Path

import pandas as pd

from seeg_eegmicrostates._utils import write_dataframe
from seeg_eegmicrostates.config import AnalysisConfig, YEO7_PARCELLATION_COLUMN, YEO17_PARCELLATION_COLUMN
from seeg_eegmicrostates.workflows.pipelines import (
    _exploratory_branch,
    render_reports,
    run_activity_effects_stage,
    run_exploratory_coupling_stage,
)


def test_branch_specific_cache_paths(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    main_path = cfg.cache_path("eeg", "microstate_labels", ext="parquet", branch="main")
    band_path = cfg.cache_path("eeg", "microstate_labels", ext="parquet", branch="band_1_40")
    assert main_path != band_path
    assert "main" in main_path.name
    assert "band_1_40" in band_path.name


def test_default_eeg_template_path_tracks_artifact_root(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    assert cfg.default_eeg_template_fif == tmp_path / "artifacts" / "cache" / "eeg" / "ModK.fif"


def test_run_specific_report_and_log_paths_live_under_timestamped_run_directory(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", run_timestamp="20260406_123456")
    report_path = cfg.report_path("activity_effects", ext="png", branch="band_1_40_activity")
    log_path = cfg.log_path("render-reports")
    assert report_path == (
        tmp_path
        / "artifacts"
        / "runs"
        / "20260406_123456"
        / "reports"
        / "figures"
        / f"activity_effects_band_1_40_activity_{cfg.runtime_hash}.png"
    )
    assert log_path == (
        tmp_path
        / "artifacts"
        / "runs"
        / "20260406_123456"
        / "logs"
        / f"render_reports_{cfg.runtime_hash}.log"
    )
    assert not (cfg.reports_root / "qc").exists()


def test_cache_directory_setup_does_not_precreate_run_report_tree(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", run_timestamp="20260406_123456")
    directories = cfg.ensure_cache_directories()
    assert directories["cache_root"].exists()
    assert directories["runs_root"].exists()
    assert not cfg.run_root.exists()
    assert not cfg.reports_root.exists()
    assert not cfg.logs_root.exists()


def test_default_sampling_rates_use_shared_250_hz_grid() -> None:
    cfg = AnalysisConfig()
    assert cfg.eeg_resample_hz == 250.0
    assert cfg.seeg_resample_hz == 250.0
    assert cfg.seeg_signal_scaling == "raw"


def test_seeg_parcellation_changes_runtime_hash_and_cache_identity(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    aal3_cfg = AnalysisConfig(artifact_root=artifact_root)
    custom_cfg = AnalysisConfig(
        artifact_root=artifact_root,
        seeg_parcellation_name="custom",
        seeg_parcellation_column="CustomAtlas",
    )
    aal3_path = aal3_cfg.cache_path("seeg", "region_band_limited", ext="parquet", branch="band_1_40", patient_id="sub-01")
    custom_path = custom_cfg.cache_path("seeg", "region_band_limited", ext="parquet", branch="band_1_40", patient_id="sub-01")
    assert aal3_cfg.runtime_hash != custom_cfg.runtime_hash
    assert aal3_path != custom_path


def test_yeo17_parcellation_uses_default_schaefer_column(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", seeg_parcellation_name="yeo17")
    assert cfg.seeg_parcellation_column == YEO17_PARCELLATION_COLUMN


def test_yeo7_parcellation_uses_default_schaefer_column(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", seeg_parcellation_name="yeo7")
    assert cfg.seeg_parcellation_column == YEO7_PARCELLATION_COLUMN


def test_analysis_state_changes_runtime_hash_and_cache_identity(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    ide_a_cfg = AnalysisConfig(artifact_root=artifact_root, analysis_state="IDE_A")
    ide_s_cfg = AnalysisConfig(artifact_root=artifact_root, analysis_state="IDE_S")
    ide_a_path = ide_a_cfg.cache_path("index", "cohort_ide_a_main", ext="parquet")
    ide_s_path = ide_s_cfg.cache_path("index", "cohort_ide_s_main", ext="parquet")
    assert ide_a_cfg.runtime_hash != ide_s_cfg.runtime_hash
    assert ide_a_path != ide_s_path


def test_run_timestamp_does_not_change_cache_identity(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    first = AnalysisConfig(artifact_root=artifact_root, run_timestamp="20260406_120000")
    second = AnalysisConfig(artifact_root=artifact_root, run_timestamp="20260406_120001")
    assert first.runtime_hash == second.runtime_hash
    assert first.cache_path("eeg", "microstate_labels", ext="parquet", branch="band_1_40") == second.cache_path(
        "eeg",
        "microstate_labels",
        ext="parquet",
        branch="band_1_40",
    )
    assert first.report_path("microstate_templates", ext="png", branch="band_1_40") != second.report_path(
        "microstate_templates",
        ext="png",
        branch="band_1_40",
    )


def test_run_activity_effects_stage_reuses_cached_outputs(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    cached = {
        "aligned": cfg.cache_path("coupling", "aligned_activity", ext="parquet", branch="band_1_40_activity"),
        "subject_profiles": cfg.cache_path(
            "coupling",
            "subject_activity_profiles",
            ext="parquet",
            branch="band_1_40_activity",
        ),
        "group_omnibus": cfg.cache_path(
            "stats",
            "group_activity_omnibus",
            ext="parquet",
            branch="band_1_40_activity",
        ),
        "group_posthoc": cfg.cache_path(
            "stats",
            "group_activity_posthoc",
            ext="parquet",
            branch="band_1_40_activity",
        ),
    }
    for path in cached.values():
        write_dataframe(pd.DataFrame({"value": [1]}), path)
    outputs = run_activity_effects_stage(cfg)
    for key, path in cached.items():
        assert outputs[key] == path
    assert outputs["subject_profiles_excel"].exists()
    assert outputs["group_omnibus_excel"].exists()
    assert outputs["group_posthoc_excel"].exists()
    assert not (cfg.reports_root / "figures").exists()
    assert not (cfg.reports_root / "qc").exists()


def test_render_reports_exports_main_omnibus_and_posthoc_outputs(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", run_timestamp="20260406_123456")
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01", "sub-01", "sub-01", "sub-01"],
                "region": ["Right Hippocampus"] * 4,
                "microstate": [0, 1, 2, 3],
                "state_mean": [0.1, 0.3, 0.2, 0.4],
                "state_std": [0.0, 0.0, 0.0, 0.0],
                "n_state_samples": [10, 10, 10, 10],
            }
        ),
        cfg.cache_path("coupling", "subject_activity_profiles", ext="parquet", branch="band_1_40_activity"),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "region": ["Right Hippocampus"],
                "n_subjects": [7],
                "statistic": [4.2],
                "p_perm": [0.01],
                "mean_state_0": [0.1],
                "mean_state_1": [0.3],
                "mean_state_2": [0.2],
                "mean_state_3": [0.4],
                "q_fdr": [0.01],
            }
        ),
        cfg.cache_path("stats", "group_activity_omnibus", ext="parquet", branch="band_1_40_activity"),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "region": ["Right Hippocampus"],
                "microstate_a": [0],
                "microstate_b": [1],
                "n_subjects": [7],
                "mean_state_a": [0.1],
                "mean_state_b": [0.3],
                "mean_effect": [0.2],
                "median_effect": [0.2],
                "p_perm": [0.02],
                "q_fdr": [0.02],
            }
        ),
        cfg.cache_path("stats", "group_activity_posthoc", ext="parquet", branch="band_1_40_activity"),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01", "sub-01", "sub-01", "sub-01"],
                "method": ["plv"] * 4,
                "region_a": ["Right Hippocampus"] * 4,
                "region_b": ["Right Amygdala"] * 4,
                "microstate": [0, 1, 2, 3],
                "state_connectivity": [0.2, 0.6, 0.3, 0.5],
                "n_state_samples": [20, 20, 20, 20],
            }
        ),
        cfg.cache_path("coupling", "subject_connectivity_profiles", ext="parquet", branch="band_1_40_plv"),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "method": ["plv"],
                "region_a": ["Right Hippocampus"],
                "region_b": ["Right Amygdala"],
                "n_subjects": [7],
                "statistic": [5.1],
                "p_perm": [0.01],
                "mean_state_0": [0.2],
                "mean_state_1": [0.6],
                "mean_state_2": [0.3],
                "mean_state_3": [0.5],
                "q_fdr": [0.01],
            }
        ),
        cfg.cache_path("stats", "group_connectivity_omnibus", ext="parquet", branch="band_1_40_plv"),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "method": ["plv"],
                "region_a": ["Right Hippocampus"],
                "region_b": ["Right Amygdala"],
                "microstate_a": [0],
                "microstate_b": [1],
                "n_subjects": [7],
                "mean_state_a": [0.2],
                "mean_state_b": [0.6],
                "mean_effect": [0.4],
                "median_effect": [0.4],
                "p_perm": [0.01],
                "q_fdr": [0.01],
            }
        ),
        cfg.cache_path("stats", "group_connectivity_posthoc", ext="parquet", branch="band_1_40_plv"),
    )

    outputs = render_reports(cfg)

    assert outputs["activity_omnibus_heatmap"].exists()
    assert outputs["activity_posthoc_heatmap"].exists()
    assert outputs["activity_subject_profiles_excel"].exists()
    assert outputs["activity_group_omnibus_excel"].exists()
    assert outputs["activity_group_posthoc_excel"].exists()
    assert outputs["band_connectivity_plv_omnibus"].exists()
    assert outputs["band_connectivity_plv_posthoc"].exists()
    assert outputs["band_connectivity_plv_subject_profiles_excel"].exists()
    assert outputs["band_connectivity_plv_group_omnibus_excel"].exists()
    assert outputs["band_connectivity_plv_group_posthoc_excel"].exists()


def test_render_reports_reads_region_coverage_cache(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", run_timestamp="20260406_123456")
    coverage_path = cfg.cache_path("seeg", "region_coverage", ext="parquet", branch="band_1_40")
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "region": ["Right Hippocampus"],
                "n_bipolar_channels": [3],
            }
        ),
        coverage_path,
    )
    outputs = render_reports(cfg)
    assert outputs["coverage"].exists()
    assert "region_coverage" in outputs["coverage"].name
    assert "runs" in str(outputs["coverage"])


def test_run_exploratory_coupling_stage_reuses_cached_event_activity_outputs(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts")
    branch = _exploratory_branch(
        cfg,
        "event-activity",
        params={"event_window_sec": 1.0, "min_subjects": cfg.min_group_subjects},
    )
    cached = {
        "event_details": cfg.cache_path("coupling", "event_locked_activity", ext="parquet", branch=branch),
        "subject_effects": cfg.cache_path("coupling", "subject_event_locked_activity", ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", "group_event_locked_activity", ext="parquet", branch=branch),
    }
    write_dataframe(pd.DataFrame({"patient_id": ["sub-01"], "microstate": [0], "region": ["Right Hippocampus"]}), cached["event_details"])
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "microstate": [0],
                "region": ["Right Hippocampus"],
                "n_events": [4],
                "pre_value": [0.1],
                "post_value": [0.3],
                "effect_mean_diff": [0.2],
            }
        ),
        cached["subject_effects"],
    )
    write_dataframe(
        pd.DataFrame(
            {
                "microstate": [0],
                "region": ["Right Hippocampus"],
                "n_subjects": [7],
                "mean_effect": [0.2],
                "median_effect": [0.2],
                "p_perm": [0.01],
                "q_fdr": [0.01],
            }
        ),
        cached["group_effects"],
    )
    outputs = run_exploratory_coupling_stage(cfg, analysis="event-activity")
    for key, path in cached.items():
        assert outputs[key] == path
    assert outputs["subject_effects_excel"].exists()
    assert outputs["group_effects_excel"].exists()


def test_render_reports_discovers_exploratory_outputs(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", run_timestamp="20260406_123456")
    event_branch = _exploratory_branch(
        cfg,
        "event-activity",
        params={"event_window_sec": 1.0, "min_subjects": cfg.min_group_subjects},
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "microstate": [0],
                "region": ["Right Hippocampus"],
                "n_events": [3],
                "pre_value": [0.0],
                "post_value": [0.5],
                "effect_mean_diff": [0.5],
            }
        ),
        cfg.cache_path("coupling", "subject_event_locked_activity", ext="parquet", branch=event_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "microstate": [0],
                "region": ["Right Hippocampus"],
                "n_subjects": [7],
                "mean_effect": [0.5],
                "median_effect": [0.5],
                "p_perm": [0.01],
                "q_fdr": [0.01],
            }
        ),
        cfg.cache_path("stats", "group_event_locked_activity", ext="parquet", branch=event_branch),
    )

    connectivity_branch = _exploratory_branch(
        cfg,
        "event-connectivity",
        method="plv",
        params={"event_window_sec": 1.0, "min_subjects": cfg.min_group_subjects},
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "method": ["plv"],
                "microstate": [0],
                "region_a": ["Right Hippocampus"],
                "region_b": ["Right Amygdala"],
                "n_events": [3],
                "state_connectivity": [0.7],
                "off_connectivity": [0.2],
                "effect_mean_diff": [0.5],
            }
        ),
        cfg.cache_path("coupling", "subject_event_locked_connectivity", ext="parquet", branch=connectivity_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "method": ["plv"],
                "microstate": [0],
                "region_a": ["Right Hippocampus"],
                "region_b": ["Right Amygdala"],
                "n_subjects": [7],
                "mean_effect": [0.5],
                "median_effect": [0.5],
                "mean_state_connectivity": [0.7],
                "mean_off_connectivity": [0.2],
                "p_perm": [0.01],
                "q_fdr": [0.01],
            }
        ),
        cfg.cache_path("stats", "group_event_locked_connectivity", ext="parquet", branch=connectivity_branch),
    )

    windowed_branch = _exploratory_branch(
        cfg,
        "windowed-coupling",
        params={"window_sec": 10.0, "min_subjects": cfg.min_group_subjects},
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "microstate": [0],
                "region": ["Right Hippocampus"],
                "n_windows": [4],
                "slope": [1.2],
                "effect_mean_diff": [0.6],
            }
        ),
        cfg.cache_path("coupling", "subject_windowed_coupling", ext="parquet", branch=windowed_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "microstate": [0],
                "region": ["Right Hippocampus"],
                "n_subjects": [7],
                "mean_effect": [0.6],
                "median_effect": [0.6],
                "p_perm": [0.01],
                "q_fdr": [0.01],
            }
        ),
        cfg.cache_path("stats", "group_windowed_coupling", ext="parquet", branch=windowed_branch),
    )

    transition_branch = _exploratory_branch(
        cfg,
        "transition-coupling",
        params={"event_window_sec": 1.0, "min_subjects": cfg.min_group_subjects},
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "from_state": [0],
                "to_state": [1],
                "region": ["Right Hippocampus"],
                "n_events": [2],
                "pre_value": [0.1],
                "post_value": [0.4],
                "effect_mean_diff": [0.3],
            }
        ),
        cfg.cache_path("coupling", "subject_transition_coupling", ext="parquet", branch=transition_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "from_state": [0],
                "to_state": [1],
                "region": ["Right Hippocampus"],
                "n_subjects": [7],
                "mean_effect": [0.3],
                "median_effect": [0.3],
                "p_perm": [0.03],
                "q_fdr": [0.03],
            }
        ),
        cfg.cache_path("stats", "group_transition_coupling", ext="parquet", branch=transition_branch),
    )

    outputs = render_reports(cfg)
    assert outputs[f"{event_branch}_event_activity_heatmap"].exists()
    assert outputs[f"{connectivity_branch}_event_connectivity_heatmap"].exists()
    assert outputs[f"{windowed_branch}_windowed_coupling_heatmap"].exists()
    assert outputs[f"{transition_branch}_transition_coupling_heatmap"].exists()
