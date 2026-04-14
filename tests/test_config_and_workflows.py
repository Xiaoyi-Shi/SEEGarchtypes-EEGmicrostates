from __future__ import annotations

from pathlib import Path

import pandas as pd

from seeg_eegmicrostates._utils import write_dataframe
from seeg_eegmicrostates.config import AnalysisConfig, YEO7_PARCELLATION_COLUMN, YEO17_PARCELLATION_COLUMN
from seeg_eegmicrostates.workflows import export_paper_tables, run_exploratory_coupling_stage
from seeg_eegmicrostates.workflows.shared import _exploratory_branch


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
    report_path = cfg.report_path("field_state_coupling", ext="csv", branch="paper_workflow")
    log_path = cfg.log_path("export-paper-tables")
    assert report_path == (
        tmp_path
        / "artifacts"
        / "runs"
        / "20260406_123456"
        / "reports"
        / "figures"
        / f"field_state_coupling_paper_workflow_{cfg.runtime_hash}.csv"
    )
    assert log_path == (
        tmp_path
        / "artifacts"
        / "runs"
        / "20260406_123456"
        / "logs"
        / f"export_paper_tables_{cfg.runtime_hash}.log"
    )


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


def test_analysis_config_no_longer_exposes_direct_state_settings() -> None:
    cfg = AnalysisConfig()
    assert not hasattr(cfg, "direct_state_backend")
    assert not hasattr(cfg, "direct_state_components")
    assert not hasattr(cfg, "direct_state_surrogates")
    assert not hasattr(cfg, "direct_max_lag_ms")
    assert not hasattr(cfg, "direct_lag_step_ms")


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
    assert first.report_path("paper_results", ext="csv", branch="paper_workflow") != second.report_path(
        "paper_results",
        ext="csv",
        branch="paper_workflow",
    )


def test_render_reports_does_not_promote_region_coverage_to_paper_bundle(tmp_path: Path) -> None:
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
    outputs = export_paper_tables(cfg)
    assert outputs == {}


def test_gfp_global_branch_identity_changes_with_metric_and_weighting(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", seeg_parcellation_name="yeo17")
    rms_branch = _exploratory_branch(
        cfg,
        "gfp-global-coupling",
        params={
            "metric_definition": "rms",
            "weighting_strategy": "equal",
            "surrogates": 128,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    env_branch = _exploratory_branch(
        cfg,
        "gfp-global-coupling",
        params={
            "metric_definition": "envelope-rms",
            "weighting_strategy": "equal",
            "surrogates": 128,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    weighted_branch = _exploratory_branch(
        cfg,
        "gfp-global-coupling",
        params={
            "metric_definition": "rms",
            "weighting_strategy": "sqrt-channel-count",
            "surrogates": 128,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    assert rms_branch != env_branch
    assert rms_branch != weighted_branch


def test_run_exploratory_coupling_stage_reuses_cached_gfp_global_outputs(tmp_path: Path, monkeypatch) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", seeg_parcellation_name="yeo17")
    branch = _exploratory_branch(
        cfg,
        "gfp-global-coupling",
        params={
            "metric_definition": "rms",
            "weighting_strategy": "equal",
            "surrogates": 128,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    shared_paths = {
        "global_trace": tmp_path / "global_trace.parquet",
        "network_support": tmp_path / "network_support.parquet",
    }
    eeg_paths = {
        "labels": tmp_path / "labels.parquet",
        "gfp_trace": tmp_path / "gfp_trace.parquet",
        "gfp_peaks": tmp_path / "gfp_peaks.parquet",
    }
    for path in (*shared_paths.values(), *eeg_paths.values()):
        write_dataframe(pd.DataFrame({"patient_id": ["sub-01"]}), path)
    monkeypatch.setattr(
        "seeg_eegmicrostates.workflows.pipelines._ensure_seeg_global_metric_artifacts",
        lambda *args, **kwargs: ("gfp-shared", shared_paths),
    )
    monkeypatch.setattr(
        "seeg_eegmicrostates.workflows.pipelines.run_eeg_states_stage",
        lambda *args, **kwargs: eeg_paths,
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", "subject_gfp_global_coupling", ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", "group_gfp_global_coupling", ext="parquet", branch=branch),
    }
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "metric_definition": ["rms"],
                "weighting_strategy": ["equal"],
                "network_scope": ["yeo17-core"],
                "lag_ms": [0],
                "n_samples": [10],
                "n_networks_used": [3],
                "observed_coupling": [0.4],
                "null_mean_coupling": [0.1],
                "effect_mean_diff": [0.3],
                "p_perm": [0.05],
                "global_metric_label": ["rms__equal"],
            }
        ),
        cached["subject_effects"],
    )
    write_dataframe(
        pd.DataFrame(
            {
                "metric_definition": ["rms"],
                "weighting_strategy": ["equal"],
                "network_scope": ["yeo17-core"],
                "lag_ms": [0],
                "n_subjects": [7],
                "mean_effect": [0.3],
                "median_effect": [0.3],
                "p_perm": [0.05],
                "q_fdr": [0.05],
                "global_metric_label": ["rms__equal"],
            }
        ),
        cached["group_effects"],
    )
    outputs = run_exploratory_coupling_stage(cfg, analysis="gfp-global-coupling")
    assert outputs["global_trace"] == shared_paths["global_trace"]
    assert outputs["network_support"] == shared_paths["network_support"]
    assert outputs["subject_effects"] == cached["subject_effects"]
    assert outputs["group_effects"] == cached["group_effects"]
    assert outputs["subject_effects_excel"].exists()
    assert outputs["group_effects_excel"].exists()


def test_render_reports_discovers_gfp_global_outputs(tmp_path: Path) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", run_timestamp="20260406_123456", seeg_parcellation_name="yeo17")
    gfp_branch = _exploratory_branch(
        cfg,
        "gfp-global-coupling",
        params={
            "metric_definition": "rms",
            "weighting_strategy": "equal",
            "surrogates": 128,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "metric_definition": ["rms"],
                "weighting_strategy": ["equal"],
                "network_scope": ["yeo17-core"],
                "lag_ms": [0],
                "n_samples": [12],
                "n_networks_used": [3],
                "observed_coupling": [0.6],
                "null_mean_coupling": [0.2],
                "effect_mean_diff": [0.4],
                "p_perm": [0.02],
                "global_metric_label": ["rms__equal"],
            }
        ),
        cfg.cache_path("coupling", "subject_gfp_global_coupling", ext="parquet", branch=gfp_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "metric_definition": ["rms"],
                "weighting_strategy": ["equal"],
                "network_scope": ["yeo17-core"],
                "lag_ms": [0],
                "n_subjects": [7],
                "mean_effect": [0.4],
                "median_effect": [0.4],
                "p_perm": [0.02],
                "q_fdr": [0.02],
                "global_metric_label": ["rms__equal"],
            }
        ),
        cfg.cache_path("stats", "group_gfp_global_coupling", ext="parquet", branch=gfp_branch),
    )

    peak_branch = _exploratory_branch(
        cfg,
        "peak-gfp-global-coupling",
        params={
            "metric_definition": "rms",
            "weighting_strategy": "equal",
            "peak_window_sec": 0.5,
            "surrogates": 128,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01", "sub-01", "sub-01"],
                "metric_definition": ["rms"] * 3,
                "weighting_strategy": ["equal"] * 3,
                "network_scope": ["yeo17-core"] * 3,
                "offset_ms": [-4, 0, 4],
                "n_events": [3, 3, 3],
                "n_networks_used": [3, 3, 3],
                "observed_coupling": [0.1, 0.3, 0.2],
                "null_mean_coupling": [0.0, 0.1, 0.05],
                "effect_mean_diff": [0.1, 0.2, 0.15],
                "p_perm": [0.3, 0.02, 0.2],
                "global_metric_label": ["rms__equal"] * 3,
            }
        ),
        cfg.cache_path("coupling", "subject_peak_gfp_global_coupling", ext="parquet", branch=peak_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "metric_definition": ["rms"] * 3,
                "weighting_strategy": ["equal"] * 3,
                "network_scope": ["yeo17-core"] * 3,
                "offset_ms": [-4, 0, 4],
                "n_subjects": [7, 7, 7],
                "mean_effect": [0.1, 0.2, 0.15],
                "median_effect": [0.1, 0.2, 0.15],
                "p_perm": [0.3, 0.02, 0.2],
                "q_fdr": [0.3, 0.06, 0.3],
                "global_metric_label": ["rms__equal"] * 3,
            }
        ),
        cfg.cache_path("stats", "group_peak_gfp_global_coupling", ext="parquet", branch=peak_branch),
    )

    microstate_branch = _exploratory_branch(
        cfg,
        "gfp-controlled-microstate",
        params={
            "metric_definition": "rms",
            "weighting_strategy": "equal",
            "min_subjects": cfg.min_group_subjects,
        },
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"] * 4,
                "global_metric_label": ["rms__equal"] * 4,
                "metric_definition": ["rms"] * 4,
                "weighting_strategy": ["equal"] * 4,
                "network_scope": ["yeo17-core"] * 4,
                "microstate": [0, 1, 2, 3],
                "adjusted_global_metric": [0.1, 0.3, 0.2, 0.4],
                "raw_global_metric": [0.1, 0.3, 0.2, 0.4],
                "n_state_samples": [10, 10, 10, 10],
                "mean_state_gfp": [0.2, 0.4, 0.3, 0.5],
                "gfp_beta": [0.5, 0.5, 0.5, 0.5],
                "n_networks_used": [3, 3, 3, 3],
            }
        ),
        cfg.cache_path("coupling", "subject_gfp_controlled_microstate", ext="parquet", branch=microstate_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "global_metric_label": ["rms__equal"],
                "metric_definition": ["rms"],
                "weighting_strategy": ["equal"],
                "network_scope": ["yeo17-core"],
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
        cfg.cache_path("stats", "group_gfp_controlled_microstate_omnibus", ext="parquet", branch=microstate_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "global_metric_label": ["rms__equal"],
                "metric_definition": ["rms"],
                "weighting_strategy": ["equal"],
                "network_scope": ["yeo17-core"],
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
        cfg.cache_path("stats", "group_gfp_controlled_microstate_posthoc", ext="parquet", branch=microstate_branch),
    )

    transition_branch = _exploratory_branch(
        cfg,
        "gfp-controlled-transition",
        params={
            "metric_definition": "rms",
            "weighting_strategy": "equal",
            "transition_window_sec": cfg.direct_transition_window_sec,
            "min_subjects": cfg.min_group_subjects,
        },
    )
    write_dataframe(
        pd.DataFrame(
            {
                "patient_id": ["sub-01"],
                "global_metric_label": ["rms__equal"],
                "metric_definition": ["rms"],
                "weighting_strategy": ["equal"],
                "network_scope": ["yeo17-core"],
                "from_state": [0],
                "to_state": [1],
                "n_events": [4],
                "n_samples": [40],
                "pre_value": [0.2],
                "post_value": [0.5],
                "effect_mean_diff": [0.3],
                "gfp_beta": [0.4],
                "n_networks_used": [3],
            }
        ),
        cfg.cache_path("coupling", "subject_gfp_controlled_transition", ext="parquet", branch=transition_branch),
    )
    write_dataframe(
        pd.DataFrame(
            {
                "global_metric_label": ["rms__equal"],
                "metric_definition": ["rms"],
                "weighting_strategy": ["equal"],
                "network_scope": ["yeo17-core"],
                "from_state": [0],
                "to_state": [1],
                "n_subjects": [7],
                "mean_effect": [0.3],
                "median_effect": [0.3],
                "p_perm": [0.02],
                "q_fdr": [0.02],
            }
        ),
        cfg.cache_path("stats", "group_gfp_controlled_transition", ext="parquet", branch=transition_branch),
    )

    outputs = export_paper_tables(cfg)
    output_paths = list(outputs.values())
    assert outputs["paper_manifest_csv"].exists()
    assert outputs["paper_manifest_excel"].exists()
    assert not any(path.parent.name == "supplementary_figures" for path in output_paths)
    assert any(path.parent.name == "supplementary_tables" and "gfp_global_coupling" in path.name for path in output_paths)
    assert any(path.parent.name == "supplementary_tables" and "peak_gfp_global_coupling" in path.name for path in output_paths)
    assert any(path.parent.name == "supplementary_tables" and "gfp_controlled_transition" in path.name for path in output_paths)
    assert not any("lagged_gfp_global_coupling" in path.name for path in output_paths)
