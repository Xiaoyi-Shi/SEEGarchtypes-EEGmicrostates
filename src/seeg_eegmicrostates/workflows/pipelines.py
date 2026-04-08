from __future__ import annotations

from pathlib import Path

import pandas as pd

from seeg_eegmicrostates._utils import config_hash, read_dataframe, write_dataframe, write_excel_dataframe
from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.coupling import (
    DEFAULT_FINE_FIELD_LAG_WINDOW_MS,
    DEFAULT_FIELD_STATE_NORMALIZATION,
    DEFAULT_FIELD_STATE_PEAK_METRIC,
    DEFAULT_FIELD_STATE_SURROGATES,
    DEFAULT_GFP_GLOBAL_METRIC,
    DEFAULT_GFP_GLOBAL_SURROGATES,
    DEFAULT_GFP_GLOBAL_WEIGHTING,
    DEFAULT_GFP_PEAK_WINDOW_SEC,
    SUPPORTED_FIELD_STATE_NORMALIZATIONS,
    SUPPORTED_FIELD_STATE_PEAK_METRICS,
    SUPPORTED_GFP_GLOBAL_METRICS,
    SUPPORTED_GFP_GLOBAL_WEIGHTINGS,
    align_eeg_and_field_state_labels,
    align_eeg_gfp_and_field_state_labels,
    align_eeg_topography_to_archetypes,
    align_eeg_and_seeg_state_labels,
    align_gfp_and_global_traces,
    align_label_table_to_region_timeseries,
    align_microstate_to_gfp_and_global,
    align_region_timeseries_to_labels,
    build_eeg_microstate_template_table,
    build_eeg_topography_trace,
    build_microstate_event_table,
    build_state_transition_table,
    compute_subject_archetype_conditioned_eeg_maps,
    compute_subject_archetype_state_preference,
    compute_subject_archetype_template_similarity,
    compute_subject_field_state_coupling,
    compute_subject_field_state_to_eeg_switching,
    connectivity_analysis_branch,
    compute_subject_gfp_controlled_field_state_profiles,
    compute_subject_gfp_controlled_field_state_to_eeg_switching,
    compute_subject_gfp_controlled_field_state_transition_effects,
    compute_subject_direct_state_coupling,
    compute_subject_event_locked_connectivity_effects,
    compute_subject_event_locked_region_effects,
    compute_subject_gfp_controlled_microstate_profiles,
    compute_subject_gfp_controlled_transition_effects,
    compute_subject_gfp_global_coupling,
    compute_subject_microstate_connectivity_profiles,
    compute_subject_microstate_region_profiles,
    compute_subject_peak_centered_global_trajectory,
    derive_group_field_state_archetypes,
    normalize_field_archetype_space,
    compute_subject_transition_field_state_coupling,
    compute_subject_transition_state_coupling,
    compute_subject_windowed_region_coupling,
    compute_windowed_region_metrics,
    compute_windowed_state_metrics,
    derive_seeg_field_state_artifacts,
    derive_seeg_global_metric_trace,
    derive_direct_seeg_state_artifacts,
    global_metric_label,
    normalize_connectivity_method,
    normalize_direct_state_backend,
    normalize_field_normalization,
    normalize_field_peak_metric,
    normalize_global_metric_definition,
    normalize_global_weighting_strategy,
    project_field_state_templates_to_common_space,
    sample_period_from_times,
    summarize_group_archetype_conditioned_eeg_maps,
    summarize_group_archetype_template_similarity,
    summarize_subject_fine_lag_profile,
)
from seeg_eegmicrostates.eeg import (
    build_eeg_gfp_peak_table,
    build_eeg_gfp_trace,
    label_microstates,
    load_microstate_model,
    preprocess_eeg_recording,
    save_microstate_model,
    validate_microstate_model_channels,
)
from seeg_eegmicrostates.io import load_atlas_table, load_workbook_tables, read_raw_fif, save_raw_fif, scan_repository
from seeg_eegmicrostates.qc import build_main_cohort
from seeg_eegmicrostates.seeg import (
    build_same_region_bipolar_map,
    compute_band_limited_region_signals,
    load_and_crop_bipolar_seeg,
)
from seeg_eegmicrostates.segment import build_state_segments
from seeg_eegmicrostates.stats import (
    run_group_connectivity_statistics,
    run_group_permutation_statistics,
    run_group_profile_omnibus_statistics,
    run_group_profile_posthoc_statistics,
    run_group_scalar_statistics,
)
from seeg_eegmicrostates.viz import (
    plot_connectivity_effect_matrices,
    plot_connectivity_omnibus_matrix,
    plot_connectivity_posthoc_matrices,
    plot_coverage_summary,
    plot_effect_curve,
    plot_direct_coupling_lag_curve,
    plot_eeg_topography_panels,
    plot_group_effects_heatmap,
    plot_group_metric_heatmap,
    plot_microstate_templates,
    plot_subject_state_profile_heatmap,
    plot_subject_template_panels,
    plot_state_transition_matrix,
    plot_transition_effect_heatmap,
)
from seeg_eegmicrostates.config import (
    SEEG_PARCELLATION_COLUMN,
    SEEG_PARCELLATION_NAME,
    YEO17_PARCELLATION_COLUMN,
    YEO17_PARCELLATION_NAME,
)


_BAND_BRANCH = "band_1_40"
_ACTIVITY_BRANCH = "band_1_40_activity"
_ACTIVITY_SUBJECT_PROFILE_STEM = "subject_activity_profiles"
_ACTIVITY_GROUP_OMNIBUS_STEM = "group_activity_omnibus"
_ACTIVITY_GROUP_POSTHOC_STEM = "group_activity_posthoc"
_CONNECTIVITY_SUBJECT_PROFILE_STEM = "subject_connectivity_profiles"
_CONNECTIVITY_GROUP_OMNIBUS_STEM = "group_connectivity_omnibus"
_CONNECTIVITY_GROUP_POSTHOC_STEM = "group_connectivity_posthoc"
_SEEG_REGION_MAP_STEM = "bipolar_region_map"
_SEEG_REGION_COVERAGE_STEM = "region_coverage"
_SEEG_REGION_BAND_STEM = "region_band_limited"
_EXPLORATORY_SHARED_BRANCH = "exploratory_shared"
_DIRECT_STATE_FEATURES_STEM = "direct_state_features"
_DIRECT_STATE_LABELS_STEM = "direct_state_labels"
_DIRECT_STATE_SUBJECT_STEM = "subject_direct_state_coupling"
_DIRECT_STATE_GROUP_STEM = "group_direct_state_coupling"
_LAGGED_STATE_SUBJECT_STEM = "subject_lagged_state_coupling"
_LAGGED_STATE_GROUP_STEM = "group_lagged_state_coupling"
_TRANSITION_STATE_SUBJECT_STEM = "subject_transition_state_coupling"
_TRANSITION_STATE_GROUP_STEM = "group_transition_state_coupling"
_FIELD_STATE_TRACE_STEM = "field_state_trace"
_FIELD_STATE_PEAK_STEM = "field_state_peaks"
_FIELD_STATE_MAPS_STEM = "field_state_peak_maps"
_FIELD_STATE_TEMPLATES_STEM = "field_state_templates"
_FIELD_STATE_LABELS_STEM = "field_state_labels"
_FIELD_STATE_PROFILES_STEM = "field_state_profiles"
_FIELD_STATE_TRANSITION_PROFILES_STEM = "field_state_transition_profiles"
_FIELD_ARCHETYPE_PROJECTIONS_STEM = "field_state_archetype_projections"
_FIELD_ARCHETYPE_ASSIGNMENTS_STEM = "field_state_archetype_assignments"
_FIELD_ARCHETYPE_TEMPLATES_STEM = "field_state_archetypes"
_FIELD_ARCHETYPE_SUPPORT_STEM = "field_state_archetype_support"
_FIELD_STATE_SUBJECT_STEM = "subject_field_state_coupling"
_FIELD_STATE_GROUP_STEM = "group_field_state_coupling"
_LAGGED_FIELD_STATE_SUBJECT_STEM = "subject_lagged_field_state_coupling"
_LAGGED_FIELD_STATE_GROUP_STEM = "group_lagged_field_state_coupling"
_FINE_LAG_FIELD_STATE_SUBJECT_STEM = "subject_fine_lag_field_state_coupling"
_FINE_LAG_FIELD_STATE_GROUP_STEM = "group_fine_lag_field_state_coupling"
_FINE_LAG_FIELD_STATE_PEAK_SUBJECT_STEM = "subject_fine_lag_field_state_peaks"
_FINE_LAG_FIELD_STATE_PEAK_GROUP_STEM = "group_fine_lag_field_state_peak_summary"
_TRANSITION_FIELD_STATE_SUBJECT_STEM = "subject_transition_field_state_coupling"
_TRANSITION_FIELD_STATE_GROUP_STEM = "group_transition_field_state_coupling"
_GFP_CONTROLLED_FIELD_STATE_SUBJECT_STEM = "subject_gfp_controlled_field_state_switching"
_GFP_CONTROLLED_FIELD_STATE_GROUP_OMNIBUS_STEM = "group_gfp_controlled_field_state_switching_omnibus"
_GFP_CONTROLLED_FIELD_STATE_GROUP_POSTHOC_STEM = "group_gfp_controlled_field_state_switching_posthoc"
_GFP_CONTROLLED_FIELD_STATE_TRANSITION_SUBJECT_STEM = "subject_gfp_controlled_field_state_transition_switching"
_GFP_CONTROLLED_FIELD_STATE_TRANSITION_GROUP_STEM = "group_gfp_controlled_field_state_transition_switching"
_FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM = "subject_field_state_to_eeg_switching"
_FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM = "group_field_state_to_eeg_switching"
_GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM = "subject_gfp_controlled_field_state_to_eeg_switching"
_GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM = "group_gfp_controlled_field_state_to_eeg_switching"
_ARCHETYPE_EEG_MAP_SUBJECT_STEM = "subject_archetype_conditioned_eeg_maps"
_ARCHETYPE_EEG_MAP_GROUP_STEM = "group_archetype_conditioned_eeg_maps"
_ARCHETYPE_EEG_SIMILARITY_SUBJECT_STEM = "subject_archetype_eeg_template_similarity"
_ARCHETYPE_EEG_SIMILARITY_GROUP_STEM = "group_archetype_eeg_template_similarity"
_ARCHETYPE_EEG_PREFERENCE_SUBJECT_STEM = "subject_archetype_eeg_state_preference"
_ARCHETYPE_EEG_PREFERENCE_GROUP_STEM = "group_archetype_eeg_state_preference"
_ARCHETYPE_EEG_FINE_LAG_SUBJECT_STEM = "subject_archetype_eeg_fine_lag_coupling"
_ARCHETYPE_EEG_FINE_LAG_GROUP_STEM = "group_archetype_eeg_fine_lag_coupling"
_ARCHETYPE_EEG_FINE_LAG_PEAK_SUBJECT_STEM = "subject_archetype_eeg_fine_lag_peaks"
_ARCHETYPE_EEG_FINE_LAG_PEAK_GROUP_STEM = "group_archetype_eeg_fine_lag_peak_summary"
_ARCHETYPE_EEG_TRANSITION_SUBJECT_STEM = "subject_archetype_to_eeg_switching"
_ARCHETYPE_EEG_TRANSITION_GROUP_STEM = "group_archetype_to_eeg_switching"
_EEG_GFP_TRACE_STEM = "gfp_trace"
_EEG_GFP_PEAK_STEM = "gfp_peaks"
_SEEG_GLOBAL_TRACE_STEM = "seeg_global_trace"
_SEEG_GLOBAL_SUPPORT_STEM = "seeg_global_network_support"
_GFP_GLOBAL_SUBJECT_STEM = "subject_gfp_global_coupling"
_GFP_GLOBAL_GROUP_STEM = "group_gfp_global_coupling"
_LAGGED_GFP_GLOBAL_SUBJECT_STEM = "subject_lagged_gfp_global_coupling"
_LAGGED_GFP_GLOBAL_GROUP_STEM = "group_lagged_gfp_global_coupling"
_PEAK_GFP_GLOBAL_SUBJECT_STEM = "subject_peak_gfp_global_coupling"
_PEAK_GFP_GLOBAL_GROUP_STEM = "group_peak_gfp_global_coupling"
_GFP_CONTROLLED_MICROSTATE_SUBJECT_STEM = "subject_gfp_controlled_microstate"
_GFP_CONTROLLED_MICROSTATE_GROUP_OMNIBUS_STEM = "group_gfp_controlled_microstate_omnibus"
_GFP_CONTROLLED_MICROSTATE_GROUP_POSTHOC_STEM = "group_gfp_controlled_microstate_posthoc"
_GFP_CONTROLLED_TRANSITION_SUBJECT_STEM = "subject_gfp_controlled_transition"
_GFP_CONTROLLED_TRANSITION_GROUP_STEM = "group_gfp_controlled_transition"
_EXPLORATORY_ANALYSES = (
    "event-activity",
    "event-connectivity",
    "windowed-coupling",
    "transition-coupling",
    "direct-state-coupling",
    "lagged-state-coupling",
    "transition-state-coupling",
    "field-state-coupling",
    "lagged-field-state-coupling",
    "fine-lag-field-state-coupling",
    "transition-field-state-coupling",
    "field-state-to-eeg-switching",
    "gfp-controlled-field-state-switching",
    "field-state-archetypes",
    "archetype-conditioned-eeg-topography",
    "gfp-controlled-field-state-to-eeg-switching",
    "gfp-global-coupling",
    "lagged-gfp-global-coupling",
    "peak-gfp-global-coupling",
    "gfp-controlled-microstate",
    "gfp-controlled-transition",
)


def _exploratory_branch(cfg: AnalysisConfig, analysis: str, *, method: str | None = None, params: dict[str, object] | None = None) -> str:
    payload = {"analysis": analysis, **(params or {})}
    if method and method != "all":
        payload["method"] = normalize_connectivity_method(method) if analysis == "event-connectivity" else method
    token = config_hash(payload, length=8)
    parts = ["explore", cfg.branch_name(analysis)]
    if method and method != "all":
        parts.append(cfg.branch_name(str(payload["method"])))
    parts.append(token)
    return "_".join(parts)


def _shared_event_paths(cfg: AnalysisConfig) -> dict[str, Path]:
    return {
        "events": cfg.cache_path("coupling", "exploratory_event_table", ext="parquet", branch=_EXPLORATORY_SHARED_BRANCH),
        "transitions": cfg.cache_path("coupling", "exploratory_transition_table", ext="parquet", branch=_EXPLORATORY_SHARED_BRANCH),
    }


def _direct_state_artifact_branch(
    cfg: AnalysisConfig,
    *,
    backend: str,
    state_count: int,
    components: int,
) -> str:
    return _exploratory_branch(
        cfg,
        "direct-state-shared",
        params={
            "backend": normalize_direct_state_backend(backend),
            "state_count": int(state_count),
            "components": int(components),
        },
    )


def _field_state_artifact_branch(
    cfg: AnalysisConfig,
    *,
    peak_metric: str,
    normalization: str,
    state_count: int,
    min_duration_ms: int,
) -> str:
    return _exploratory_branch(
        cfg,
        "field-state-shared",
        params={
            "peak_metric": normalize_field_peak_metric(peak_metric),
            "normalization": normalize_field_normalization(normalization),
            "state_count": int(state_count),
            "min_duration_ms": int(min_duration_ms),
        },
    )


def _field_state_archetype_artifact_branch(
    cfg: AnalysisConfig,
    *,
    peak_metric: str,
    normalization: str,
    state_count: int,
    min_duration_ms: int,
    comparison_space: str,
) -> str:
    return _exploratory_branch(
        cfg,
        "field-state-archetype-shared",
        params={
            "peak_metric": normalize_field_peak_metric(peak_metric),
            "normalization": normalize_field_normalization(normalization),
            "state_count": int(state_count),
            "min_duration_ms": int(min_duration_ms),
            "comparison_space": normalize_field_archetype_space(comparison_space),
        },
    )


def _ensure_exploratory_event_tables(cfg: AnalysisConfig) -> dict[str, Path]:
    paths = _shared_event_paths(cfg)
    if _all_exist(paths):
        return paths
    eeg_outputs = run_eeg_states_stage(cfg)
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    event_frames: list[pd.DataFrame] = []
    transition_frames: list[pd.DataFrame] = []
    for patient_id, group in eeg_labels.groupby("patient_id"):
        event_frames.append(build_microstate_event_table(group, patient_id=str(patient_id)))
        transition_frames.append(build_state_transition_table(group, patient_id=str(patient_id)))
    events = pd.concat(event_frames, ignore_index=True) if event_frames else pd.DataFrame()
    transitions = pd.concat(transition_frames, ignore_index=True) if transition_frames else pd.DataFrame()
    return {
        "events": write_dataframe(events, paths["events"]),
        "transitions": write_dataframe(transitions, paths["transitions"]),
    }


def _branch_from_path(path: Path, stem: str, *, runtime_hash: str, ext: str) -> str | None:
    prefix = f"{stem}_"
    suffix = f"_{runtime_hash}.{ext.lstrip('.')}"
    if not path.name.startswith(prefix) or not path.name.endswith(suffix):
        return None
    return path.name[len(prefix) : -len(suffix)]


def _discover_branch_paths(cfg: AnalysisConfig, category: str, stem: str, *, ext: str) -> list[tuple[str, Path]]:
    category_dir = cfg.cache_root / category
    if not category_dir.exists():
        return []
    matches = sorted(category_dir.glob(f"{stem}_*_{cfg.runtime_hash}.{ext.lstrip('.')}"))
    discovered: list[tuple[str, Path]] = []
    for path in matches:
        branch = _branch_from_path(path, stem, runtime_hash=cfg.runtime_hash, ext=ext)
        if branch is not None:
            discovered.append((branch, path))
    return discovered


def _exploratory_min_subjects(min_subjects: int | None, cfg: AnalysisConfig) -> int:
    return int(min_subjects if min_subjects is not None else cfg.min_group_subjects)


def _resolve_direct_state_count(state_count: int | None, cfg: AnalysisConfig) -> int:
    return max(1, int(state_count if state_count is not None else cfg.microstate_k))


def _resolve_direct_components(components: int | None, cfg: AnalysisConfig) -> int:
    return max(1, int(components if components is not None else cfg.direct_state_components))


def _resolve_direct_surrogates(surrogates: int | None, cfg: AnalysisConfig) -> int:
    return max(1, int(surrogates if surrogates is not None else cfg.direct_state_surrogates))


def _resolve_field_state_count(state_count: int | None, cfg: AnalysisConfig) -> int:
    return max(1, int(state_count if state_count is not None else cfg.microstate_k))


def _resolve_field_min_duration_ms(min_duration_ms: int | None, cfg: AnalysisConfig) -> int:
    return max(1, int(min_duration_ms if min_duration_ms is not None else cfg.min_microstate_duration_ms))


def _resolve_field_surrogates(surrogates: int | None) -> int:
    return max(1, int(surrogates if surrogates is not None else DEFAULT_FIELD_STATE_SURROGATES))


def _resolve_field_archetype_space(comparison_space: str | None) -> str:
    return normalize_field_archetype_space(comparison_space or YEO17_PARCELLATION_NAME)


def _resolve_fine_field_lag_window_ms(window_ms: int | None) -> int:
    return max(4, int(window_ms if window_ms is not None else DEFAULT_FINE_FIELD_LAG_WINDOW_MS))


def _resolve_transition_window_sec(window_sec: float | None, cfg: AnalysisConfig) -> float:
    return float(window_sec if window_sec is not None else cfg.direct_transition_window_sec)


def _resolve_global_surrogates(surrogates: int | None) -> int:
    return max(1, int(surrogates if surrogates is not None else DEFAULT_GFP_GLOBAL_SURROGATES))


def _resolve_peak_window_sec(window_sec: float | None) -> float:
    return float(window_sec if window_sec is not None else DEFAULT_GFP_PEAK_WINDOW_SEC)


def _resolve_direct_lag_grid(
    cfg: AnalysisConfig,
    *,
    sample_period_sec: float,
    max_lag_ms: int | None,
    lag_step_ms: int | None,
) -> list[int]:
    if sample_period_sec <= 0.0:
        return [0]
    max_lag = max(0, int(max_lag_ms if max_lag_ms is not None else cfg.direct_max_lag_ms))
    lag_step = max(1, int(lag_step_ms if lag_step_ms is not None else cfg.direct_lag_step_ms))
    max_lag_samples = int(round(max_lag / 1000.0 / sample_period_sec))
    step_samples = max(1, int(round(lag_step / 1000.0 / sample_period_sec)))
    values = list(range(-max_lag_samples, max_lag_samples + 1, step_samples))
    if 0 not in values:
        values.append(0)
    return sorted(set(values))


def _global_metric_artifact_branch(
    cfg: AnalysisConfig,
    *,
    metric_definition: str,
    weighting_strategy: str,
) -> str:
    return _exploratory_branch(
        cfg,
        "gfp-global-shared",
        params={
            "metric_definition": normalize_global_metric_definition(metric_definition),
            "weighting_strategy": normalize_global_weighting_strategy(weighting_strategy),
        },
    )


def _segment_stem(cfg: AnalysisConfig) -> str:
    return f"{cfg.analysis_state_token}_segments"


def _cohort_stem(cfg: AnalysisConfig) -> str:
    return f"cohort_{cfg.analysis_state_token}_main"


def build_index_artifacts(cfg: AnalysisConfig) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    patient_info, annotation_info = load_workbook_tables(cfg.workbook_path)
    _ = patient_info
    recording_index = scan_repository(cfg.data_root, analysis_state=cfg.analysis_state)
    segments = build_state_segments(annotation_info, cfg.analysis_state)
    cohort, inventory = build_main_cohort(recording_index, segments, cfg)
    outputs = {
        "recording_index": write_dataframe(recording_index, cfg.cache_path("index", "recording_index", ext="parquet")),
        "segments": write_dataframe(segments, cfg.cache_path("segments", _segment_stem(cfg), ext="parquet")),
        "cohort": write_dataframe(cohort, cfg.cache_path("index", _cohort_stem(cfg), ext="parquet")),
        "eeg_inventory": write_dataframe(inventory, cfg.cache_path("eeg", "eeg_channel_inventory", ext="parquet")),
    }
    return outputs


def _load_cohort_and_segments(cfg: AnalysisConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    cohort_path = cfg.cache_path("index", _cohort_stem(cfg), ext="parquet")
    segments_path = cfg.cache_path("segments", _segment_stem(cfg), ext="parquet")
    if not cohort_path.exists() or not segments_path.exists():
        build_index_artifacts(cfg)
    cohort = read_dataframe(cohort_path)
    segments = read_dataframe(segments_path)
    return cohort, segments


def _eligible_rows(cfg: AnalysisConfig) -> pd.DataFrame:
    cohort, _ = _load_cohort_and_segments(cfg)
    return cohort[cohort["include_main"]].copy().sort_values("patient_id")


def _all_exist(paths: dict[str, Path]) -> bool:
    return all(path.exists() for path in paths.values())


def _write_table_reports(cfg: AnalysisConfig, tables: dict[str, pd.DataFrame], *, branch: str) -> dict[str, Path]:
    outputs: dict[str, Path] = {}
    for stem, table in tables.items():
        outputs[stem] = write_excel_dataframe(table, cfg.report_path(stem, ext="xlsx", subdir="tables", branch=branch))
    return outputs


def _write_table_reports_from_paths(cfg: AnalysisConfig, paths: dict[str, Path], *, branch: str) -> dict[str, Path]:
    tables = {stem: read_dataframe(path) for stem, path in paths.items() if path.exists()}
    return _write_table_reports(cfg, tables, branch=branch)


def _ensure_direct_state_artifacts(
    cfg: AnalysisConfig,
    *,
    backend: str,
    state_count: int,
    components: int,
) -> tuple[str, dict[str, Path]]:
    normalized_backend = normalize_direct_state_backend(backend)
    state_branch = _direct_state_artifact_branch(
        cfg,
        backend=normalized_backend,
        state_count=state_count,
        components=components,
    )
    cached = {
        "features": cfg.cache_path("coupling", _DIRECT_STATE_FEATURES_STEM, ext="parquet", branch=state_branch),
        "labels": cfg.cache_path("coupling", _DIRECT_STATE_LABELS_STEM, ext="parquet", branch=state_branch),
    }
    if _all_exist(cached):
        return state_branch, cached
    _ = run_seeg_regions_stage(cfg)
    cohort = _eligible_rows(cfg)
    feature_frames: list[pd.DataFrame] = []
    label_frames: list[pd.DataFrame] = []
    for offset, patient_id in enumerate(cohort["patient_id"].astype(str)):
        region_df = read_dataframe(
            cfg.cache_path("seeg", _SEEG_REGION_BAND_STEM, ext="parquet", branch=_BAND_BRANCH, patient_id=patient_id)
        )
        feature_df, label_df = derive_direct_seeg_state_artifacts(
            region_df,
            patient_id=patient_id,
            backend=normalized_backend,
            n_states=state_count,
            n_components=components,
            seed=cfg.random_seed + offset,
        )
        feature_frames.append(feature_df)
        label_frames.append(label_df)
    features = pd.concat(feature_frames, ignore_index=True) if feature_frames else pd.DataFrame()
    labels = pd.concat(label_frames, ignore_index=True) if label_frames else pd.DataFrame()
    return state_branch, {
        "features": write_dataframe(features, cached["features"]),
        "labels": write_dataframe(labels, cached["labels"]),
    }


def _ensure_seeg_field_state_artifacts(
    cfg: AnalysisConfig,
    *,
    peak_metric: str,
    normalization: str,
    state_count: int,
    min_duration_ms: int,
) -> tuple[str, dict[str, Path]]:
    normalized_metric = normalize_field_peak_metric(peak_metric)
    normalized_strategy = normalize_field_normalization(normalization)
    field_branch = _field_state_artifact_branch(
        cfg,
        peak_metric=normalized_metric,
        normalization=normalized_strategy,
        state_count=state_count,
        min_duration_ms=min_duration_ms,
    )
    cached = {
        "trace": cfg.cache_path("coupling", _FIELD_STATE_TRACE_STEM, ext="parquet", branch=field_branch),
        "peaks": cfg.cache_path("coupling", _FIELD_STATE_PEAK_STEM, ext="parquet", branch=field_branch),
        "peak_maps": cfg.cache_path("coupling", _FIELD_STATE_MAPS_STEM, ext="parquet", branch=field_branch),
        "templates": cfg.cache_path("coupling", _FIELD_STATE_TEMPLATES_STEM, ext="parquet", branch=field_branch),
        "labels": cfg.cache_path("coupling", _FIELD_STATE_LABELS_STEM, ext="parquet", branch=field_branch),
        "profiles": cfg.cache_path("coupling", _FIELD_STATE_PROFILES_STEM, ext="parquet", branch=field_branch),
        "transition_profiles": cfg.cache_path("coupling", _FIELD_STATE_TRANSITION_PROFILES_STEM, ext="parquet", branch=field_branch),
    }
    if _all_exist(cached):
        return field_branch, cached
    cohort = _eligible_rows(cfg)
    trace_frames: list[pd.DataFrame] = []
    peak_frames: list[pd.DataFrame] = []
    peak_map_frames: list[pd.DataFrame] = []
    template_frames: list[pd.DataFrame] = []
    label_frames: list[pd.DataFrame] = []
    profile_frames: list[pd.DataFrame] = []
    transition_profile_frames: list[pd.DataFrame] = []
    for offset, row in enumerate(cohort.to_dict(orient="records")):
        patient_id = str(row["patient_id"])
        raw_bp = load_and_crop_bipolar_seeg(row["seeg_bipolar_path"], float(row["start_sec"]), float(row["end_sec"]))
        band = raw_bp.copy()
        band.filter(cfg.band_limited_range[0], cfg.band_limited_range[1], verbose="ERROR")
        band.resample(cfg.seeg_resample_hz, verbose="ERROR")
        channel_df = pd.DataFrame(band.get_data().T, columns=band.ch_names)
        channel_df.insert(0, "time_sec", band.times.astype(float))
        artifacts = derive_seeg_field_state_artifacts(
            channel_df,
            patient_id=patient_id,
            peak_metric=normalized_metric,
            normalization=normalized_strategy,
            n_states=state_count,
            min_duration_ms=min_duration_ms,
            min_peak_distance_ms=cfg.gfp_min_peak_distance_ms,
            seed=cfg.random_seed + offset,
        )
        trace_frames.append(artifacts["trace"])
        peak_frames.append(artifacts["peaks"])
        peak_map_frames.append(artifacts["peak_maps"])
        template_frames.append(artifacts["templates"])
        label_frames.append(artifacts["labels"])
        profile_frames.append(artifacts["profiles"])
        transition_profile_frames.append(artifacts["transition_profiles"])
    trace_df = pd.concat(trace_frames, ignore_index=True) if trace_frames else pd.DataFrame()
    peak_df = pd.concat(peak_frames, ignore_index=True) if peak_frames else pd.DataFrame()
    peak_maps_df = pd.concat(peak_map_frames, ignore_index=True) if peak_map_frames else pd.DataFrame()
    template_df = pd.concat(template_frames, ignore_index=True) if template_frames else pd.DataFrame()
    label_df = pd.concat(label_frames, ignore_index=True) if label_frames else pd.DataFrame()
    profile_df = pd.concat(profile_frames, ignore_index=True) if profile_frames else pd.DataFrame()
    transition_profile_df = (
        pd.concat(transition_profile_frames, ignore_index=True) if transition_profile_frames else pd.DataFrame()
    )
    return field_branch, {
        "trace": write_dataframe(trace_df, cached["trace"]),
        "peaks": write_dataframe(peak_df, cached["peaks"]),
        "peak_maps": write_dataframe(peak_maps_df, cached["peak_maps"]),
        "templates": write_dataframe(template_df, cached["templates"]),
        "labels": write_dataframe(label_df, cached["labels"]),
        "profiles": write_dataframe(profile_df, cached["profiles"]),
        "transition_profiles": write_dataframe(transition_profile_df, cached["transition_profiles"]),
    }


def _field_archetype_space_config(comparison_space: str) -> tuple[str, str]:
    normalized_space = normalize_field_archetype_space(comparison_space)
    if normalized_space == YEO17_PARCELLATION_NAME:
        return YEO17_PARCELLATION_NAME, YEO17_PARCELLATION_COLUMN
    return SEEG_PARCELLATION_NAME, SEEG_PARCELLATION_COLUMN


def _ensure_seeg_field_state_archetype_artifacts(
    cfg: AnalysisConfig,
    *,
    peak_metric: str,
    normalization: str,
    state_count: int,
    min_duration_ms: int,
    comparison_space: str,
) -> tuple[str, dict[str, Path]]:
    normalized_space = _resolve_field_archetype_space(comparison_space)
    artifact_branch = _field_state_archetype_artifact_branch(
        cfg,
        peak_metric=peak_metric,
        normalization=normalization,
        state_count=state_count,
        min_duration_ms=min_duration_ms,
        comparison_space=normalized_space,
    )
    cached = {
        "projections": cfg.cache_path("coupling", _FIELD_ARCHETYPE_PROJECTIONS_STEM, ext="parquet", branch=artifact_branch),
    }
    if _all_exist(cached):
        return artifact_branch, cached
    _, state_paths = _ensure_seeg_field_state_artifacts(
        cfg,
        peak_metric=peak_metric,
        normalization=normalization,
        state_count=state_count,
        min_duration_ms=min_duration_ms,
    )
    template_df = read_dataframe(state_paths["templates"])
    if template_df.empty:
        return artifact_branch, {"projections": write_dataframe(pd.DataFrame(), cached["projections"])}
    cohort = _eligible_rows(cfg)
    parcellation_name, atlas_column = _field_archetype_space_config(normalized_space)
    projection_frames: list[pd.DataFrame] = []
    for row in cohort.to_dict(orient="records"):
        patient_id = str(row["patient_id"])
        patient_templates = template_df[template_df["patient_id"] == patient_id]
        if patient_templates.empty:
            continue
        template_columns = [
            column
            for column in patient_templates.columns
            if column
            not in {
                "patient_id",
                "field_state",
                "peak_metric",
                "normalization",
                "n_states",
                "min_duration_ms",
                "n_channels",
                "n_peak_maps",
            }
        ]
        atlas_df = load_atlas_table(row["atlas_path"])
        mapping_df = build_same_region_bipolar_map(
            atlas_df,
            template_columns,
            patient_id=patient_id,
            atlas_column=atlas_column,
            parcellation_name=parcellation_name,
        )
        projection_frames.append(
            project_field_state_templates_to_common_space(
                patient_templates,
                mapping_df,
                patient_id=patient_id,
                comparison_space=normalized_space,
            )
        )
    projection_df = pd.concat(projection_frames, ignore_index=True) if projection_frames else pd.DataFrame()
    return artifact_branch, {"projections": write_dataframe(projection_df, cached["projections"])}


def _require_yeo17_global_branch(cfg: AnalysisConfig) -> None:
    if cfg.seeg_parcellation_name != "yeo17":
        raise ValueError(
            "GFP-informed global coupling currently requires --seeg-parcellation-name yeo17 "
            f"(received {cfg.seeg_parcellation_name!r})."
        )


def _ensure_seeg_global_metric_artifacts(
    cfg: AnalysisConfig,
    *,
    metric_definition: str,
    weighting_strategy: str,
) -> tuple[str, dict[str, Path]]:
    _require_yeo17_global_branch(cfg)
    normalized_metric = normalize_global_metric_definition(metric_definition)
    normalized_weighting = normalize_global_weighting_strategy(weighting_strategy)
    metric_branch = _global_metric_artifact_branch(
        cfg,
        metric_definition=normalized_metric,
        weighting_strategy=normalized_weighting,
    )
    cached = {
        "global_trace": cfg.cache_path("coupling", _SEEG_GLOBAL_TRACE_STEM, ext="parquet", branch=metric_branch),
        "network_support": cfg.cache_path("coupling", _SEEG_GLOBAL_SUPPORT_STEM, ext="parquet", branch=metric_branch),
    }
    if _all_exist(cached):
        return metric_branch, cached
    region_outputs = run_seeg_regions_stage(cfg)
    coverage_df = read_dataframe(region_outputs["coverage"])
    cohort = _eligible_rows(cfg)
    trace_frames: list[pd.DataFrame] = []
    support_frames: list[pd.DataFrame] = []
    for patient_id in cohort["patient_id"].astype(str):
        region_df = read_dataframe(
            cfg.cache_path("seeg", _SEEG_REGION_BAND_STEM, ext="parquet", branch=_BAND_BRANCH, patient_id=patient_id)
        )
        trace_df, support_df = derive_seeg_global_metric_trace(
            region_df,
            coverage_df[coverage_df["patient_id"] == patient_id].copy(),
            patient_id=patient_id,
            metric_definition=normalized_metric,
            weighting_strategy=normalized_weighting,
        )
        trace_frames.append(trace_df)
        support_frames.append(support_df)
    traces = pd.concat(trace_frames, ignore_index=True) if trace_frames else pd.DataFrame()
    supports = pd.concat(support_frames, ignore_index=True) if support_frames else pd.DataFrame()
    return metric_branch, {
        "global_trace": write_dataframe(traces, cached["global_trace"]),
        "network_support": write_dataframe(supports, cached["network_support"]),
    }


def _long_activity_frame(aligned_wide_df: pd.DataFrame, *, patient_id: str) -> pd.DataFrame:
    long = aligned_wide_df.melt(
        id_vars=["patient_id", "time_sec", "microstate", "corr"],
        var_name="region",
        value_name="value",
    )
    if "patient_id" not in long.columns:
        long.insert(0, "patient_id", patient_id)
    return long.dropna(subset=["value"]).reset_index(drop=True)


def run_eeg_microstate_branch(
    cfg: AnalysisConfig,
    *,
    branch: str = _BAND_BRANCH,
    template_fif: str | Path | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    cached = {
        "model": cfg.cache_path("eeg", "group_microstate_model", ext="fif", branch=branch),
        "labels": cfg.cache_path("eeg", "microstate_labels", ext="parquet", branch=branch),
        "restored_channels": cfg.cache_path("eeg", "restored_channels", ext="parquet", branch=branch),
        "gfp_trace": cfg.cache_path("eeg", _EEG_GFP_TRACE_STEM, ext="parquet", branch=branch),
        "gfp_peaks": cfg.cache_path("eeg", _EEG_GFP_PEAK_STEM, ext="parquet", branch=branch),
    }
    if template_fif is None and _all_exist(cached):
        return cached
    selected_template = Path(template_fif) if template_fif is not None else cfg.default_eeg_template_fif
    if not selected_template.exists():
        source = "--template-fif override" if template_fif is not None else "default EEG template"
        raise FileNotFoundError(f"{source} not found: {selected_template}")
    cohort = _eligible_rows(cfg)
    preprocessed_raws: dict[str, object] = {}
    missing_rows: list[dict[str, object]] = []
    for row in cohort.to_dict(orient="records"):
        raw19, missing = preprocess_eeg_recording(
            row["eeg_ref_path"],
            start_sec=float(row["start_sec"]),
            end_sec=float(row["end_sec"]),
            cfg=cfg,
            band=cfg.band_limited_range,
        )
        patient_id = str(row["patient_id"])
        preprocessed_raws[patient_id] = raw19
        save_raw_fif(raw19, cfg.cache_path("eeg", "preprocessed", ext="fif", branch=branch, patient_id=patient_id))
        missing_rows.append({"patient_id": patient_id, "branch": branch, "restored_channels": list(missing)})
    model = load_microstate_model(selected_template)
    validate_microstate_model_channels(
        model,
        cfg.target19_channels,
        alternate_channels=cfg.standard11_channels,
    )
    model_path = save_microstate_model(model, cached["model"])
    label_frames: list[pd.DataFrame] = []
    gfp_frames: list[pd.DataFrame] = []
    peak_frames: list[pd.DataFrame] = []
    for patient_id, raw in preprocessed_raws.items():
        label_frames.append(label_microstates(raw, model, cfg, patient_id=patient_id))
        gfp_trace = build_eeg_gfp_trace(raw, patient_id=patient_id)
        gfp_frames.append(gfp_trace)
        peak_frames.append(build_eeg_gfp_peak_table(gfp_trace, cfg, patient_id=patient_id, sfreq=float(raw.info["sfreq"])))
    labels = pd.concat(label_frames, ignore_index=True) if label_frames else pd.DataFrame()
    gfp_trace = pd.concat(gfp_frames, ignore_index=True) if gfp_frames else pd.DataFrame()
    gfp_peaks = pd.concat(peak_frames, ignore_index=True) if peak_frames else pd.DataFrame()
    labels_path = write_dataframe(labels, cfg.cache_path("eeg", "microstate_labels", ext="parquet", branch=branch))
    missing_path = write_dataframe(pd.DataFrame(missing_rows), cfg.cache_path("eeg", "restored_channels", ext="parquet", branch=branch))
    gfp_trace_path = write_dataframe(gfp_trace, cached["gfp_trace"])
    gfp_peaks_path = write_dataframe(gfp_peaks, cached["gfp_peaks"])
    return {
        "model": model_path,
        "labels": labels_path,
        "restored_channels": missing_path,
        "gfp_trace": gfp_trace_path,
        "gfp_peaks": gfp_peaks_path,
    }


def run_eeg_states_stage(cfg: AnalysisConfig, *, template_fif: str | Path | None = None) -> dict[str, Path]:
    return run_eeg_microstate_branch(cfg, template_fif=template_fif)


def _patient_preprocessed_eeg_path(cfg: AnalysisConfig, *, patient_id: str, branch: str = _BAND_BRANCH) -> Path:
    return cfg.cache_path("eeg", "preprocessed", ext="fif", branch=branch, patient_id=patient_id)


def _load_patient_eeg_topography_trace(cfg: AnalysisConfig, cohort_row: dict[str, object], *, patient_id: str) -> pd.DataFrame:
    path = _patient_preprocessed_eeg_path(cfg, patient_id=patient_id)
    if path.exists():
        raw19 = read_raw_fif(path, preload=True)
    else:
        raw19, _ = preprocess_eeg_recording(
            cohort_row["eeg_ref_path"],
            start_sec=float(cohort_row["start_sec"]),
            end_sec=float(cohort_row["end_sec"]),
            cfg=cfg,
            band=cfg.band_limited_range,
        )
        save_raw_fif(raw19, path)
    return build_eeg_topography_trace(raw19, patient_id=patient_id)


def run_seeg_band_limited_region_branch(cfg: AnalysisConfig) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    cohort = _eligible_rows(cfg)
    cached = {
        "mapping": cfg.cache_path("seeg", _SEEG_REGION_MAP_STEM, ext="parquet", branch="band_1_40"),
        "coverage": cfg.cache_path("seeg", _SEEG_REGION_COVERAGE_STEM, ext="parquet", branch="band_1_40"),
    }
    patient_paths = [
        cfg.cache_path("seeg", _SEEG_REGION_BAND_STEM, ext="parquet", branch="band_1_40", patient_id=str(patient_id))
        for patient_id in cohort["patient_id"].tolist()
    ]
    if _all_exist(cached) and all(path.exists() for path in patient_paths):
        return cached
    mapping_frames: list[pd.DataFrame] = []
    coverage_frames: list[pd.DataFrame] = []
    for row in cohort.to_dict(orient="records"):
        patient_id = str(row["patient_id"])
        atlas_df = load_atlas_table(row["atlas_path"])
        raw_bp = load_and_crop_bipolar_seeg(row["seeg_bipolar_path"], float(row["start_sec"]), float(row["end_sec"]))
        mapping_df = build_same_region_bipolar_map(
            atlas_df,
            list(raw_bp.ch_names),
            patient_id=patient_id,
            atlas_column=cfg.seeg_parcellation_column,
            parcellation_name=cfg.seeg_parcellation_name,
        )
        mapping_frames.append(mapping_df)
        region_df, coverage_df = compute_band_limited_region_signals(raw_bp, mapping_df, cfg, patient_id=patient_id)
        coverage_frames.append(coverage_df)
        write_dataframe(
            region_df,
            cfg.cache_path("seeg", _SEEG_REGION_BAND_STEM, ext="parquet", branch="band_1_40", patient_id=patient_id),
        )
    mapping = pd.concat(mapping_frames, ignore_index=True) if mapping_frames else pd.DataFrame()
    coverage = pd.concat(coverage_frames, ignore_index=True) if coverage_frames else pd.DataFrame()
    return {
        "mapping": write_dataframe(mapping, cached["mapping"]),
        "coverage": write_dataframe(coverage, cached["coverage"]),
    }


def run_seeg_regions_stage(cfg: AnalysisConfig) -> dict[str, Path]:
    return run_seeg_band_limited_region_branch(cfg)


def run_activity_effects_stage(cfg: AnalysisConfig) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    cached = {
        "aligned": cfg.cache_path("coupling", "aligned_activity", ext="parquet", branch=_ACTIVITY_BRANCH),
        "subject_profiles": cfg.cache_path("coupling", _ACTIVITY_SUBJECT_PROFILE_STEM, ext="parquet", branch=_ACTIVITY_BRANCH),
        "group_omnibus": cfg.cache_path("stats", _ACTIVITY_GROUP_OMNIBUS_STEM, ext="parquet", branch=_ACTIVITY_BRANCH),
        "group_posthoc": cfg.cache_path("stats", _ACTIVITY_GROUP_POSTHOC_STEM, ext="parquet", branch=_ACTIVITY_BRANCH),
    }
    if _all_exist(cached):
        table_reports = _write_table_reports_from_paths(
            cfg,
            {
                _ACTIVITY_SUBJECT_PROFILE_STEM: cached["subject_profiles"],
                _ACTIVITY_GROUP_OMNIBUS_STEM: cached["group_omnibus"],
                _ACTIVITY_GROUP_POSTHOC_STEM: cached["group_posthoc"],
            },
            branch=_ACTIVITY_BRANCH,
        )
        return {
            **cached,
            "subject_profiles_excel": table_reports[_ACTIVITY_SUBJECT_PROFILE_STEM],
            "group_omnibus_excel": table_reports[_ACTIVITY_GROUP_OMNIBUS_STEM],
            "group_posthoc_excel": table_reports[_ACTIVITY_GROUP_POSTHOC_STEM],
        }
    eeg_outputs = run_eeg_states_stage(cfg)
    _ = run_seeg_regions_stage(cfg)
    cohort = _eligible_rows(cfg)
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    aligned_frames: list[pd.DataFrame] = []
    for row in cohort.to_dict(orient="records"):
        patient_id = str(row["patient_id"])
        label_df = eeg_labels[eeg_labels["patient_id"] == patient_id]
        region_df = read_dataframe(
            cfg.cache_path("seeg", _SEEG_REGION_BAND_STEM, ext="parquet", branch=_BAND_BRANCH, patient_id=patient_id)
        )
        aligned_wide = align_region_timeseries_to_labels(label_df, region_df, patient_id=patient_id)
        aligned_frames.append(_long_activity_frame(aligned_wide, patient_id=patient_id))
    aligned_df = pd.concat(aligned_frames, ignore_index=True) if aligned_frames else pd.DataFrame()
    aligned_path = write_dataframe(aligned_df, cached["aligned"])
    subject_profiles = compute_subject_microstate_region_profiles(aligned_df)
    subject_path = write_dataframe(subject_profiles, cached["subject_profiles"])
    group_omnibus = run_group_profile_omnibus_statistics(
        subject_profiles,
        group_keys=["region"],
        value_column="state_mean",
        seed=cfg.random_seed,
        min_subjects=cfg.min_group_subjects,
    )
    group_omnibus_path = write_dataframe(group_omnibus, cached["group_omnibus"])
    group_posthoc = run_group_profile_posthoc_statistics(
        subject_profiles,
        group_keys=["region"],
        value_column="state_mean",
        seed=cfg.random_seed,
        min_subjects=cfg.min_group_subjects,
    )
    group_posthoc_path = write_dataframe(group_posthoc, cached["group_posthoc"])
    table_reports = _write_table_reports(
        cfg,
        {
            _ACTIVITY_SUBJECT_PROFILE_STEM: subject_profiles,
            _ACTIVITY_GROUP_OMNIBUS_STEM: group_omnibus,
            _ACTIVITY_GROUP_POSTHOC_STEM: group_posthoc,
        },
        branch=_ACTIVITY_BRANCH,
    )
    return {
        "aligned": aligned_path,
        "subject_profiles": subject_path,
        "group_omnibus": group_omnibus_path,
        "group_posthoc": group_posthoc_path,
        "subject_profiles_excel": table_reports[_ACTIVITY_SUBJECT_PROFILE_STEM],
        "group_omnibus_excel": table_reports[_ACTIVITY_GROUP_OMNIBUS_STEM],
        "group_posthoc_excel": table_reports[_ACTIVITY_GROUP_POSTHOC_STEM],
    }


def run_exploratory_event_activity_stage(
    cfg: AnalysisConfig,
    *,
    event_window_sec: float = 1.0,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    branch = _exploratory_branch(
        cfg,
        "event-activity",
        params={"event_window_sec": event_window_sec, "min_subjects": threshold},
    )
    cached = {
        "event_details": cfg.cache_path("coupling", "event_locked_activity", ext="parquet", branch=branch),
        "subject_effects": cfg.cache_path("coupling", "subject_event_locked_activity", ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", "group_event_locked_activity", ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                "subject_event_locked_activity": cached["subject_effects"],
                "group_event_locked_activity": cached["group_effects"],
            },
            branch=branch,
        )
        return {**cached, "subject_effects_excel": tables["subject_event_locked_activity"], "group_effects_excel": tables["group_event_locked_activity"]}
    event_paths = _ensure_exploratory_event_tables(cfg)
    _ = run_seeg_regions_stage(cfg)
    events = read_dataframe(event_paths["events"])
    cohort = _eligible_rows(cfg)
    event_frames: list[pd.DataFrame] = []
    subject_frames: list[pd.DataFrame] = []
    for patient_id in cohort["patient_id"].astype(str):
        patient_events = events[(events["patient_id"] == patient_id) & (events["event_type"] == "onset")]
        region_df = read_dataframe(cfg.cache_path("seeg", _SEEG_REGION_BAND_STEM, ext="parquet", branch=_BAND_BRANCH, patient_id=patient_id))
        event_detail, subject_summary = compute_subject_event_locked_region_effects(
            patient_events,
            region_df,
            patient_id=patient_id,
            window_sec=event_window_sec,
            event_keys=("microstate",),
        )
        event_frames.append(event_detail)
        subject_frames.append(subject_summary)
    event_details = pd.concat(event_frames, ignore_index=True) if event_frames else pd.DataFrame()
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    event_detail_path = write_dataframe(event_details, cached["event_details"])
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_permutation_statistics(subject_effects, seed=cfg.random_seed, min_subjects=threshold)
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            "subject_event_locked_activity": subject_effects,
            "group_event_locked_activity": group_effects,
        },
        branch=branch,
    )
    return {
        "events": event_paths["events"],
        "event_details": event_detail_path,
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables["subject_event_locked_activity"],
        "group_effects_excel": tables["group_event_locked_activity"],
    }


def run_exploratory_event_connectivity_stage(
    cfg: AnalysisConfig,
    *,
    method: str = "corr",
    event_window_sec: float = 1.0,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    if method == "all":
        outputs: dict[str, Path] = {}
        for item in ("corr", "plv", "wpli"):
            for key, value in run_exploratory_event_connectivity_stage(
                cfg,
                method=item,
                event_window_sec=event_window_sec,
                min_subjects=min_subjects,
            ).items():
                outputs[f"{item}_{key}"] = value
        return outputs
    normalized_method = normalize_connectivity_method(method)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    branch = _exploratory_branch(
        cfg,
        "event-connectivity",
        method=normalized_method,
        params={"event_window_sec": event_window_sec, "min_subjects": threshold},
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", "subject_event_locked_connectivity", ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", "group_event_locked_connectivity", ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                "subject_event_locked_connectivity": cached["subject_effects"],
                "group_event_locked_connectivity": cached["group_effects"],
            },
            branch=branch,
        )
        return {**cached, "subject_effects_excel": tables["subject_event_locked_connectivity"], "group_effects_excel": tables["group_event_locked_connectivity"]}
    event_paths = _ensure_exploratory_event_tables(cfg)
    _ = run_seeg_regions_stage(cfg)
    events = read_dataframe(event_paths["events"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    min_samples = max(4, int(round(cfg.seeg_resample_hz * min(event_window_sec, 0.5))))
    for patient_id in cohort["patient_id"].astype(str):
        patient_events = events[(events["patient_id"] == patient_id) & (events["event_type"] == "onset")]
        region_df = read_dataframe(cfg.cache_path("seeg", _SEEG_REGION_BAND_STEM, ext="parquet", branch=_BAND_BRANCH, patient_id=patient_id))
        subject_frames.append(
            compute_subject_event_locked_connectivity_effects(
                patient_events,
                region_df,
                patient_id=patient_id,
                window_sec=event_window_sec,
                min_samples=min_samples,
                method=normalized_method,
                event_keys=("microstate",),
            )
        )
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_connectivity_statistics(
        subject_effects,
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            "subject_event_locked_connectivity": subject_effects,
            "group_event_locked_connectivity": group_effects,
        },
        branch=branch,
    )
    return {
        "events": event_paths["events"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables["subject_event_locked_connectivity"],
        "group_effects_excel": tables["group_event_locked_connectivity"],
    }


def run_exploratory_windowed_coupling_stage(
    cfg: AnalysisConfig,
    *,
    window_sec: float = 10.0,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    branch = _exploratory_branch(
        cfg,
        "windowed-coupling",
        params={"window_sec": window_sec, "min_subjects": threshold},
    )
    cached = {
        "state_windows": cfg.cache_path("coupling", "windowed_state_metrics", ext="parquet", branch=branch),
        "region_windows": cfg.cache_path("coupling", "windowed_region_metrics", ext="parquet", branch=branch),
        "subject_effects": cfg.cache_path("coupling", "subject_windowed_coupling", ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", "group_windowed_coupling", ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                "subject_windowed_coupling": cached["subject_effects"],
                "group_windowed_coupling": cached["group_effects"],
            },
            branch=branch,
        )
        return {**cached, "subject_effects_excel": tables["subject_windowed_coupling"], "group_effects_excel": tables["group_windowed_coupling"]}
    eeg_outputs = run_eeg_states_stage(cfg)
    _ = run_seeg_regions_stage(cfg)
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    cohort = _eligible_rows(cfg)
    state_frames: list[pd.DataFrame] = []
    region_frames: list[pd.DataFrame] = []
    subject_frames: list[pd.DataFrame] = []
    for patient_id in cohort["patient_id"].astype(str):
        label_df = eeg_labels[eeg_labels["patient_id"] == patient_id]
        region_df = read_dataframe(cfg.cache_path("seeg", _SEEG_REGION_BAND_STEM, ext="parquet", branch=_BAND_BRANCH, patient_id=patient_id))
        state_windows = compute_windowed_state_metrics(label_df, patient_id=patient_id, window_sec=window_sec)
        region_windows = compute_windowed_region_metrics(region_df, patient_id=patient_id, window_sec=window_sec)
        state_frames.append(state_windows)
        region_frames.append(region_windows)
        subject_frames.append(compute_subject_windowed_region_coupling(state_windows, region_windows))
    state_window_df = pd.concat(state_frames, ignore_index=True) if state_frames else pd.DataFrame()
    region_window_df = pd.concat(region_frames, ignore_index=True) if region_frames else pd.DataFrame()
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    state_path = write_dataframe(state_window_df, cached["state_windows"])
    region_path = write_dataframe(region_window_df, cached["region_windows"])
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_permutation_statistics(subject_effects, seed=cfg.random_seed, min_subjects=threshold)
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            "subject_windowed_coupling": subject_effects,
            "group_windowed_coupling": group_effects,
        },
        branch=branch,
    )
    return {
        "state_windows": state_path,
        "region_windows": region_path,
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables["subject_windowed_coupling"],
        "group_effects_excel": tables["group_windowed_coupling"],
    }


def run_exploratory_transition_coupling_stage(
    cfg: AnalysisConfig,
    *,
    event_window_sec: float = 1.0,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    branch = _exploratory_branch(
        cfg,
        "transition-coupling",
        params={"event_window_sec": event_window_sec, "min_subjects": threshold},
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", "subject_transition_coupling", ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", "group_transition_coupling", ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                "subject_transition_coupling": cached["subject_effects"],
                "group_transition_coupling": cached["group_effects"],
            },
            branch=branch,
        )
        return {**cached, "subject_effects_excel": tables["subject_transition_coupling"], "group_effects_excel": tables["group_transition_coupling"]}
    event_paths = _ensure_exploratory_event_tables(cfg)
    _ = run_seeg_regions_stage(cfg)
    transitions = read_dataframe(event_paths["transitions"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    for patient_id in cohort["patient_id"].astype(str):
        patient_transitions = transitions[transitions["patient_id"] == patient_id]
        region_df = read_dataframe(cfg.cache_path("seeg", _SEEG_REGION_BAND_STEM, ext="parquet", branch=_BAND_BRANCH, patient_id=patient_id))
        _, subject_summary = compute_subject_event_locked_region_effects(
            patient_transitions,
            region_df,
            patient_id=patient_id,
            window_sec=event_window_sec,
            event_keys=("from_state", "to_state"),
        )
        subject_frames.append(subject_summary)
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_scalar_statistics(
        subject_effects,
        group_keys=["from_state", "to_state", "region"],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            "subject_transition_coupling": subject_effects,
            "group_transition_coupling": group_effects,
        },
        branch=branch,
    )
    return {
        "transitions": event_paths["transitions"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables["subject_transition_coupling"],
        "group_effects_excel": tables["group_transition_coupling"],
    }


def run_exploratory_direct_state_coupling_stage(
    cfg: AnalysisConfig,
    *,
    direct_backend: str = "pca-kmeans",
    direct_state_count: int | None = None,
    direct_components: int | None = None,
    direct_surrogates: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_backend = normalize_direct_state_backend(direct_backend)
    state_count = _resolve_direct_state_count(direct_state_count, cfg)
    components = _resolve_direct_components(direct_components, cfg)
    surrogates = _resolve_direct_surrogates(direct_surrogates, cfg)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    _state_branch, state_paths = _ensure_direct_state_artifacts(
        cfg,
        backend=normalized_backend,
        state_count=state_count,
        components=components,
    )
    branch = _exploratory_branch(
        cfg,
        "direct-state-coupling",
        params={
            "backend": normalized_backend,
            "state_count": state_count,
            "components": components,
            "surrogates": surrogates,
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", _DIRECT_STATE_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", _DIRECT_STATE_GROUP_STEM, ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _DIRECT_STATE_SUBJECT_STEM: cached["subject_effects"],
                _DIRECT_STATE_GROUP_STEM: cached["group_effects"],
            },
            branch=branch,
        )
        return {
            "state_features": state_paths["features"],
            "state_labels": state_paths["labels"],
            **cached,
            "subject_effects_excel": tables[_DIRECT_STATE_SUBJECT_STEM],
            "group_effects_excel": tables[_DIRECT_STATE_GROUP_STEM],
        }
    eeg_outputs = run_eeg_states_stage(cfg)
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    seeg_state_labels = read_dataframe(state_paths["labels"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    for offset, patient_id in enumerate(cohort["patient_id"].astype(str)):
        aligned = align_eeg_and_seeg_state_labels(
            eeg_labels[eeg_labels["patient_id"] == patient_id],
            seeg_state_labels[seeg_state_labels["patient_id"] == patient_id],
            patient_id=patient_id,
        )
        sample_period = sample_period_from_times(aligned["time_sec"].to_numpy(dtype=float)) if not aligned.empty else 0.0
        subject_frames.append(
            compute_subject_direct_state_coupling(
                aligned,
                patient_id=patient_id,
                backend=normalized_backend,
                n_states=state_count,
                lag_samples=[0],
                sample_period_sec=sample_period,
                n_surrogates=surrogates,
                seed=cfg.random_seed + offset,
            )
        )
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_scalar_statistics(
        subject_effects,
        group_keys=["backend", "n_states", "lag_ms"],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            _DIRECT_STATE_SUBJECT_STEM: subject_effects,
            _DIRECT_STATE_GROUP_STEM: group_effects,
        },
        branch=branch,
    )
    return {
        "state_features": state_paths["features"],
        "state_labels": state_paths["labels"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables[_DIRECT_STATE_SUBJECT_STEM],
        "group_effects_excel": tables[_DIRECT_STATE_GROUP_STEM],
    }


def run_exploratory_lagged_state_coupling_stage(
    cfg: AnalysisConfig,
    *,
    direct_backend: str = "pca-kmeans",
    direct_state_count: int | None = None,
    direct_components: int | None = None,
    max_lag_ms: int | None = None,
    lag_step_ms: int | None = None,
    direct_surrogates: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_backend = normalize_direct_state_backend(direct_backend)
    state_count = _resolve_direct_state_count(direct_state_count, cfg)
    components = _resolve_direct_components(direct_components, cfg)
    surrogates = _resolve_direct_surrogates(direct_surrogates, cfg)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    _state_branch, state_paths = _ensure_direct_state_artifacts(
        cfg,
        backend=normalized_backend,
        state_count=state_count,
        components=components,
    )
    branch = _exploratory_branch(
        cfg,
        "lagged-state-coupling",
        params={
            "backend": normalized_backend,
            "state_count": state_count,
            "components": components,
            "max_lag_ms": int(max_lag_ms if max_lag_ms is not None else cfg.direct_max_lag_ms),
            "lag_step_ms": int(lag_step_ms if lag_step_ms is not None else cfg.direct_lag_step_ms),
            "surrogates": surrogates,
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", _LAGGED_STATE_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", _LAGGED_STATE_GROUP_STEM, ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _LAGGED_STATE_SUBJECT_STEM: cached["subject_effects"],
                _LAGGED_STATE_GROUP_STEM: cached["group_effects"],
            },
            branch=branch,
        )
        return {
            "state_features": state_paths["features"],
            "state_labels": state_paths["labels"],
            **cached,
            "subject_effects_excel": tables[_LAGGED_STATE_SUBJECT_STEM],
            "group_effects_excel": tables[_LAGGED_STATE_GROUP_STEM],
        }
    eeg_outputs = run_eeg_states_stage(cfg)
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    seeg_state_labels = read_dataframe(state_paths["labels"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    for offset, patient_id in enumerate(cohort["patient_id"].astype(str)):
        aligned = align_eeg_and_seeg_state_labels(
            eeg_labels[eeg_labels["patient_id"] == patient_id],
            seeg_state_labels[seeg_state_labels["patient_id"] == patient_id],
            patient_id=patient_id,
        )
        sample_period = sample_period_from_times(aligned["time_sec"].to_numpy(dtype=float)) if not aligned.empty else 0.0
        lag_grid = _resolve_direct_lag_grid(
            cfg,
            sample_period_sec=sample_period,
            max_lag_ms=max_lag_ms,
            lag_step_ms=lag_step_ms,
        )
        subject_frames.append(
            compute_subject_direct_state_coupling(
                aligned,
                patient_id=patient_id,
                backend=normalized_backend,
                n_states=state_count,
                lag_samples=lag_grid,
                sample_period_sec=sample_period,
                n_surrogates=surrogates,
                seed=cfg.random_seed + offset,
            )
        )
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_scalar_statistics(
        subject_effects,
        group_keys=["backend", "n_states", "lag_ms"],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            _LAGGED_STATE_SUBJECT_STEM: subject_effects,
            _LAGGED_STATE_GROUP_STEM: group_effects,
        },
        branch=branch,
    )
    return {
        "state_features": state_paths["features"],
        "state_labels": state_paths["labels"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables[_LAGGED_STATE_SUBJECT_STEM],
        "group_effects_excel": tables[_LAGGED_STATE_GROUP_STEM],
    }


def run_exploratory_transition_state_coupling_stage(
    cfg: AnalysisConfig,
    *,
    direct_backend: str = "pca-kmeans",
    direct_state_count: int | None = None,
    direct_components: int | None = None,
    transition_window_sec: float | None = None,
    direct_surrogates: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_backend = normalize_direct_state_backend(direct_backend)
    state_count = _resolve_direct_state_count(direct_state_count, cfg)
    components = _resolve_direct_components(direct_components, cfg)
    surrogates = _resolve_direct_surrogates(direct_surrogates, cfg)
    window_sec = _resolve_transition_window_sec(transition_window_sec, cfg)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    event_paths = _ensure_exploratory_event_tables(cfg)
    _state_branch, state_paths = _ensure_direct_state_artifacts(
        cfg,
        backend=normalized_backend,
        state_count=state_count,
        components=components,
    )
    branch = _exploratory_branch(
        cfg,
        "transition-state-coupling",
        params={
            "backend": normalized_backend,
            "state_count": state_count,
            "components": components,
            "transition_window_sec": float(window_sec),
            "surrogates": surrogates,
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", _TRANSITION_STATE_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", _TRANSITION_STATE_GROUP_STEM, ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _TRANSITION_STATE_SUBJECT_STEM: cached["subject_effects"],
                _TRANSITION_STATE_GROUP_STEM: cached["group_effects"],
            },
            branch=branch,
        )
        return {
            "transitions": event_paths["transitions"],
            "state_features": state_paths["features"],
            "state_labels": state_paths["labels"],
            **cached,
            "subject_effects_excel": tables[_TRANSITION_STATE_SUBJECT_STEM],
            "group_effects_excel": tables[_TRANSITION_STATE_GROUP_STEM],
        }
    eeg_transitions = read_dataframe(event_paths["transitions"])
    seeg_state_labels = read_dataframe(state_paths["labels"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    for offset, patient_id in enumerate(cohort["patient_id"].astype(str)):
        subject_frames.append(
            compute_subject_transition_state_coupling(
                eeg_transitions[eeg_transitions["patient_id"] == patient_id],
                seeg_state_labels[seeg_state_labels["patient_id"] == patient_id],
                patient_id=patient_id,
                backend=normalized_backend,
                n_states=state_count,
                window_sec=window_sec,
                n_surrogates=surrogates,
                seed=cfg.random_seed + offset,
            )
        )
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_scalar_statistics(
        subject_effects,
        group_keys=["backend", "n_states", "from_state", "to_state"],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            _TRANSITION_STATE_SUBJECT_STEM: subject_effects,
            _TRANSITION_STATE_GROUP_STEM: group_effects,
        },
        branch=branch,
    )
    return {
        "transitions": event_paths["transitions"],
        "state_features": state_paths["features"],
        "state_labels": state_paths["labels"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables[_TRANSITION_STATE_SUBJECT_STEM],
        "group_effects_excel": tables[_TRANSITION_STATE_GROUP_STEM],
    }


def run_exploratory_field_state_coupling_stage(
    cfg: AnalysisConfig,
    *,
    field_peak_metric: str = DEFAULT_FIELD_STATE_PEAK_METRIC,
    field_normalization: str = DEFAULT_FIELD_STATE_NORMALIZATION,
    field_state_count: int | None = None,
    field_min_duration_ms: int | None = None,
    field_surrogates: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_field_peak_metric(field_peak_metric)
    normalized_strategy = normalize_field_normalization(field_normalization)
    state_count = _resolve_field_state_count(field_state_count, cfg)
    min_duration_ms = _resolve_field_min_duration_ms(field_min_duration_ms, cfg)
    surrogates = _resolve_field_surrogates(field_surrogates)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    _field_branch, state_paths = _ensure_seeg_field_state_artifacts(
        cfg,
        peak_metric=normalized_metric,
        normalization=normalized_strategy,
        state_count=state_count,
        min_duration_ms=min_duration_ms,
    )
    branch = _exploratory_branch(
        cfg,
        "field-state-coupling",
        params={
            "peak_metric": normalized_metric,
            "normalization": normalized_strategy,
            "state_count": state_count,
            "min_duration_ms": min_duration_ms,
            "surrogates": surrogates,
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", _FIELD_STATE_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", _FIELD_STATE_GROUP_STEM, ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _FIELD_STATE_SUBJECT_STEM: cached["subject_effects"],
                _FIELD_STATE_GROUP_STEM: cached["group_effects"],
            },
            branch=branch,
        )
        return {
            "field_trace": state_paths["trace"],
            "field_peaks": state_paths["peaks"],
            "field_peak_maps": state_paths["peak_maps"],
            "field_templates": state_paths["templates"],
            "field_labels": state_paths["labels"],
            "field_profiles": state_paths["profiles"],
            "field_transition_profiles": state_paths["transition_profiles"],
            **cached,
            "subject_effects_excel": tables[_FIELD_STATE_SUBJECT_STEM],
            "group_effects_excel": tables[_FIELD_STATE_GROUP_STEM],
        }
    eeg_outputs = run_eeg_states_stage(cfg)
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    field_labels = read_dataframe(state_paths["labels"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    for offset, patient_id in enumerate(cohort["patient_id"].astype(str)):
        aligned = align_eeg_and_field_state_labels(
            eeg_labels[eeg_labels["patient_id"] == patient_id],
            field_labels[field_labels["patient_id"] == patient_id],
            patient_id=patient_id,
        )
        sample_period = sample_period_from_times(aligned["time_sec"].to_numpy(dtype=float)) if not aligned.empty else 0.0
        subject_frames.append(
            compute_subject_field_state_coupling(
                aligned,
                patient_id=patient_id,
                lag_samples=[0],
                sample_period_sec=sample_period,
                n_surrogates=surrogates,
                seed=cfg.random_seed + offset,
            )
        )
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_scalar_statistics(
        subject_effects,
        group_keys=["peak_metric", "normalization", "n_states", "min_duration_ms", "lag_ms"],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            _FIELD_STATE_SUBJECT_STEM: subject_effects,
            _FIELD_STATE_GROUP_STEM: group_effects,
        },
        branch=branch,
    )
    return {
        "field_trace": state_paths["trace"],
        "field_peaks": state_paths["peaks"],
        "field_peak_maps": state_paths["peak_maps"],
        "field_templates": state_paths["templates"],
        "field_labels": state_paths["labels"],
        "field_profiles": state_paths["profiles"],
        "field_transition_profiles": state_paths["transition_profiles"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables[_FIELD_STATE_SUBJECT_STEM],
        "group_effects_excel": tables[_FIELD_STATE_GROUP_STEM],
    }


def run_exploratory_lagged_field_state_coupling_stage(
    cfg: AnalysisConfig,
    *,
    field_peak_metric: str = DEFAULT_FIELD_STATE_PEAK_METRIC,
    field_normalization: str = DEFAULT_FIELD_STATE_NORMALIZATION,
    field_state_count: int | None = None,
    field_min_duration_ms: int | None = None,
    max_lag_ms: int | None = None,
    lag_step_ms: int | None = None,
    field_surrogates: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_field_peak_metric(field_peak_metric)
    normalized_strategy = normalize_field_normalization(field_normalization)
    state_count = _resolve_field_state_count(field_state_count, cfg)
    min_duration_ms = _resolve_field_min_duration_ms(field_min_duration_ms, cfg)
    surrogates = _resolve_field_surrogates(field_surrogates)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    _field_branch, state_paths = _ensure_seeg_field_state_artifacts(
        cfg,
        peak_metric=normalized_metric,
        normalization=normalized_strategy,
        state_count=state_count,
        min_duration_ms=min_duration_ms,
    )
    branch = _exploratory_branch(
        cfg,
        "lagged-field-state-coupling",
        params={
            "peak_metric": normalized_metric,
            "normalization": normalized_strategy,
            "state_count": state_count,
            "min_duration_ms": min_duration_ms,
            "max_lag_ms": int(max_lag_ms if max_lag_ms is not None else cfg.direct_max_lag_ms),
            "lag_step_ms": int(lag_step_ms if lag_step_ms is not None else cfg.direct_lag_step_ms),
            "surrogates": surrogates,
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", _LAGGED_FIELD_STATE_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", _LAGGED_FIELD_STATE_GROUP_STEM, ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _LAGGED_FIELD_STATE_SUBJECT_STEM: cached["subject_effects"],
                _LAGGED_FIELD_STATE_GROUP_STEM: cached["group_effects"],
            },
            branch=branch,
        )
        return {
            "field_trace": state_paths["trace"],
            "field_peaks": state_paths["peaks"],
            "field_peak_maps": state_paths["peak_maps"],
            "field_templates": state_paths["templates"],
            "field_labels": state_paths["labels"],
            "field_profiles": state_paths["profiles"],
            "field_transition_profiles": state_paths["transition_profiles"],
            **cached,
            "subject_effects_excel": tables[_LAGGED_FIELD_STATE_SUBJECT_STEM],
            "group_effects_excel": tables[_LAGGED_FIELD_STATE_GROUP_STEM],
        }
    eeg_outputs = run_eeg_states_stage(cfg)
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    field_labels = read_dataframe(state_paths["labels"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    for offset, patient_id in enumerate(cohort["patient_id"].astype(str)):
        aligned = align_eeg_and_field_state_labels(
            eeg_labels[eeg_labels["patient_id"] == patient_id],
            field_labels[field_labels["patient_id"] == patient_id],
            patient_id=patient_id,
        )
        sample_period = sample_period_from_times(aligned["time_sec"].to_numpy(dtype=float)) if not aligned.empty else 0.0
        subject_frames.append(
            compute_subject_field_state_coupling(
                aligned,
                patient_id=patient_id,
                lag_samples=_resolve_direct_lag_grid(
                    cfg,
                    sample_period_sec=sample_period,
                    max_lag_ms=max_lag_ms,
                    lag_step_ms=lag_step_ms,
                ),
                sample_period_sec=sample_period,
                n_surrogates=surrogates,
                seed=cfg.random_seed + offset,
            )
        )
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_scalar_statistics(
        subject_effects,
        group_keys=["peak_metric", "normalization", "n_states", "min_duration_ms", "lag_ms"],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            _LAGGED_FIELD_STATE_SUBJECT_STEM: subject_effects,
            _LAGGED_FIELD_STATE_GROUP_STEM: group_effects,
        },
        branch=branch,
    )
    return {
        "field_trace": state_paths["trace"],
        "field_peaks": state_paths["peaks"],
        "field_peak_maps": state_paths["peak_maps"],
        "field_templates": state_paths["templates"],
        "field_labels": state_paths["labels"],
        "field_profiles": state_paths["profiles"],
        "field_transition_profiles": state_paths["transition_profiles"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables[_LAGGED_FIELD_STATE_SUBJECT_STEM],
        "group_effects_excel": tables[_LAGGED_FIELD_STATE_GROUP_STEM],
    }


def run_exploratory_field_state_archetypes_stage(
    cfg: AnalysisConfig,
    *,
    field_peak_metric: str = DEFAULT_FIELD_STATE_PEAK_METRIC,
    field_normalization: str = DEFAULT_FIELD_STATE_NORMALIZATION,
    field_state_count: int | None = None,
    field_min_duration_ms: int | None = None,
    field_archetype_space: str = YEO17_PARCELLATION_NAME,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_field_peak_metric(field_peak_metric)
    normalized_strategy = normalize_field_normalization(field_normalization)
    comparison_space = _resolve_field_archetype_space(field_archetype_space)
    state_count = _resolve_field_state_count(field_state_count, cfg)
    min_duration_ms = _resolve_field_min_duration_ms(field_min_duration_ms, cfg)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    artifact_branch, artifact_paths = _ensure_seeg_field_state_archetype_artifacts(
        cfg,
        peak_metric=normalized_metric,
        normalization=normalized_strategy,
        state_count=state_count,
        min_duration_ms=min_duration_ms,
        comparison_space=comparison_space,
    )
    branch = _exploratory_branch(
        cfg,
        "field-state-archetypes",
        params={
            "peak_metric": normalized_metric,
            "normalization": normalized_strategy,
            "state_count": state_count,
            "min_duration_ms": min_duration_ms,
            "comparison_space": comparison_space,
            "min_subjects": threshold,
        },
    )
    cached = {
        "assignments": cfg.cache_path("coupling", _FIELD_ARCHETYPE_ASSIGNMENTS_STEM, ext="parquet", branch=branch),
        "archetypes": cfg.cache_path("coupling", _FIELD_ARCHETYPE_TEMPLATES_STEM, ext="parquet", branch=branch),
        "support": cfg.cache_path("stats", _FIELD_ARCHETYPE_SUPPORT_STEM, ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _FIELD_ARCHETYPE_PROJECTIONS_STEM: artifact_paths["projections"],
                _FIELD_ARCHETYPE_ASSIGNMENTS_STEM: cached["assignments"],
                _FIELD_ARCHETYPE_TEMPLATES_STEM: cached["archetypes"],
                _FIELD_ARCHETYPE_SUPPORT_STEM: cached["support"],
            },
            branch=branch,
        )
        return {
            "subject_projections": artifact_paths["projections"],
            **cached,
            "subject_projections_excel": tables[_FIELD_ARCHETYPE_PROJECTIONS_STEM],
            "assignments_excel": tables[_FIELD_ARCHETYPE_ASSIGNMENTS_STEM],
            "archetypes_excel": tables[_FIELD_ARCHETYPE_TEMPLATES_STEM],
            "support_excel": tables[_FIELD_ARCHETYPE_SUPPORT_STEM],
        }
    projection_df = read_dataframe(artifact_paths["projections"])
    summaries = derive_group_field_state_archetypes(
        projection_df,
        comparison_space=comparison_space,
        n_states=state_count,
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    assignment_path = write_dataframe(summaries["assignments"], cached["assignments"])
    archetype_path = write_dataframe(summaries["archetypes"], cached["archetypes"])
    support_path = write_dataframe(summaries["support"], cached["support"])
    tables = _write_table_reports(
        cfg,
        {
            _FIELD_ARCHETYPE_PROJECTIONS_STEM: projection_df,
            _FIELD_ARCHETYPE_ASSIGNMENTS_STEM: summaries["assignments"],
            _FIELD_ARCHETYPE_TEMPLATES_STEM: summaries["archetypes"],
            _FIELD_ARCHETYPE_SUPPORT_STEM: summaries["support"],
        },
        branch=branch,
    )
    return {
        "subject_projections": artifact_paths["projections"],
        "assignments": assignment_path,
        "archetypes": archetype_path,
        "support": support_path,
        "subject_projections_excel": tables[_FIELD_ARCHETYPE_PROJECTIONS_STEM],
        "assignments_excel": tables[_FIELD_ARCHETYPE_ASSIGNMENTS_STEM],
        "archetypes_excel": tables[_FIELD_ARCHETYPE_TEMPLATES_STEM],
        "support_excel": tables[_FIELD_ARCHETYPE_SUPPORT_STEM],
    }


def run_exploratory_archetype_conditioned_eeg_topography_stage(
    cfg: AnalysisConfig,
    *,
    field_peak_metric: str = DEFAULT_FIELD_STATE_PEAK_METRIC,
    field_normalization: str = DEFAULT_FIELD_STATE_NORMALIZATION,
    field_state_count: int | None = None,
    field_min_duration_ms: int | None = None,
    field_archetype_space: str = YEO17_PARCELLATION_NAME,
    fine_lag_window_ms: int | None = None,
    transition_window_sec: float | None = None,
    field_surrogates: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_field_peak_metric(field_peak_metric)
    normalized_strategy = normalize_field_normalization(field_normalization)
    comparison_space = _resolve_field_archetype_space(field_archetype_space)
    state_count = _resolve_field_state_count(field_state_count, cfg)
    min_duration_ms = _resolve_field_min_duration_ms(field_min_duration_ms, cfg)
    window_ms = _resolve_fine_field_lag_window_ms(fine_lag_window_ms)
    window_sec = _resolve_transition_window_sec(transition_window_sec, cfg)
    surrogates = _resolve_field_surrogates(field_surrogates)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    _field_branch, state_paths = _ensure_seeg_field_state_artifacts(
        cfg,
        peak_metric=normalized_metric,
        normalization=normalized_strategy,
        state_count=state_count,
        min_duration_ms=min_duration_ms,
    )
    archetype_outputs = run_exploratory_field_state_archetypes_stage(
        cfg,
        field_peak_metric=normalized_metric,
        field_normalization=normalized_strategy,
        field_state_count=state_count,
        field_min_duration_ms=min_duration_ms,
        field_archetype_space=comparison_space,
        min_subjects=threshold,
    )
    branch = _exploratory_branch(
        cfg,
        "archetype-conditioned-eeg-topography",
        params={
            "peak_metric": normalized_metric,
            "normalization": normalized_strategy,
            "state_count": state_count,
            "min_duration_ms": min_duration_ms,
            "comparison_space": comparison_space,
            "fine_lag_window_ms": window_ms,
            "transition_window_sec": float(window_sec),
            "surrogates": surrogates,
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_maps": cfg.cache_path("coupling", _ARCHETYPE_EEG_MAP_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_maps": cfg.cache_path("coupling", _ARCHETYPE_EEG_MAP_GROUP_STEM, ext="parquet", branch=branch),
        "subject_similarity": cfg.cache_path("coupling", _ARCHETYPE_EEG_SIMILARITY_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_similarity": cfg.cache_path("stats", _ARCHETYPE_EEG_SIMILARITY_GROUP_STEM, ext="parquet", branch=branch),
        "subject_preference": cfg.cache_path("coupling", _ARCHETYPE_EEG_PREFERENCE_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_preference": cfg.cache_path("stats", _ARCHETYPE_EEG_PREFERENCE_GROUP_STEM, ext="parquet", branch=branch),
        "subject_fine_lag": cfg.cache_path("coupling", _ARCHETYPE_EEG_FINE_LAG_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_fine_lag": cfg.cache_path("stats", _ARCHETYPE_EEG_FINE_LAG_GROUP_STEM, ext="parquet", branch=branch),
        "subject_fine_lag_peaks": cfg.cache_path(
            "coupling", _ARCHETYPE_EEG_FINE_LAG_PEAK_SUBJECT_STEM, ext="parquet", branch=branch
        ),
        "group_fine_lag_peak_summary": cfg.cache_path(
            "stats", _ARCHETYPE_EEG_FINE_LAG_PEAK_GROUP_STEM, ext="parquet", branch=branch
        ),
        "subject_transition_effects": cfg.cache_path(
            "coupling", _ARCHETYPE_EEG_TRANSITION_SUBJECT_STEM, ext="parquet", branch=branch
        ),
        "group_transition_effects": cfg.cache_path(
            "stats", _ARCHETYPE_EEG_TRANSITION_GROUP_STEM, ext="parquet", branch=branch
        ),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _ARCHETYPE_EEG_MAP_SUBJECT_STEM: cached["subject_maps"],
                _ARCHETYPE_EEG_MAP_GROUP_STEM: cached["group_maps"],
                _ARCHETYPE_EEG_SIMILARITY_SUBJECT_STEM: cached["subject_similarity"],
                _ARCHETYPE_EEG_SIMILARITY_GROUP_STEM: cached["group_similarity"],
                _ARCHETYPE_EEG_PREFERENCE_SUBJECT_STEM: cached["subject_preference"],
                _ARCHETYPE_EEG_PREFERENCE_GROUP_STEM: cached["group_preference"],
                _ARCHETYPE_EEG_FINE_LAG_SUBJECT_STEM: cached["subject_fine_lag"],
                _ARCHETYPE_EEG_FINE_LAG_GROUP_STEM: cached["group_fine_lag"],
                _ARCHETYPE_EEG_FINE_LAG_PEAK_SUBJECT_STEM: cached["subject_fine_lag_peaks"],
                _ARCHETYPE_EEG_FINE_LAG_PEAK_GROUP_STEM: cached["group_fine_lag_peak_summary"],
                _ARCHETYPE_EEG_TRANSITION_SUBJECT_STEM: cached["subject_transition_effects"],
                _ARCHETYPE_EEG_TRANSITION_GROUP_STEM: cached["group_transition_effects"],
            },
            branch=branch,
        )
        return {
            "field_trace": state_paths["trace"],
            "field_peaks": state_paths["peaks"],
            "field_peak_maps": state_paths["peak_maps"],
            "field_templates": state_paths["templates"],
            "field_labels": state_paths["labels"],
            "field_profiles": state_paths["profiles"],
            "field_transition_profiles": state_paths["transition_profiles"],
            "archetype_assignments": archetype_outputs["assignments"],
            "archetypes": archetype_outputs["archetypes"],
            "archetype_support": archetype_outputs["support"],
            **cached,
            "subject_maps_excel": tables[_ARCHETYPE_EEG_MAP_SUBJECT_STEM],
            "group_maps_excel": tables[_ARCHETYPE_EEG_MAP_GROUP_STEM],
            "subject_similarity_excel": tables[_ARCHETYPE_EEG_SIMILARITY_SUBJECT_STEM],
            "group_similarity_excel": tables[_ARCHETYPE_EEG_SIMILARITY_GROUP_STEM],
            "subject_preference_excel": tables[_ARCHETYPE_EEG_PREFERENCE_SUBJECT_STEM],
            "group_preference_excel": tables[_ARCHETYPE_EEG_PREFERENCE_GROUP_STEM],
            "subject_fine_lag_excel": tables[_ARCHETYPE_EEG_FINE_LAG_SUBJECT_STEM],
            "group_fine_lag_excel": tables[_ARCHETYPE_EEG_FINE_LAG_GROUP_STEM],
            "subject_fine_lag_peaks_excel": tables[_ARCHETYPE_EEG_FINE_LAG_PEAK_SUBJECT_STEM],
            "group_fine_lag_peak_summary_excel": tables[_ARCHETYPE_EEG_FINE_LAG_PEAK_GROUP_STEM],
            "subject_transition_effects_excel": tables[_ARCHETYPE_EEG_TRANSITION_SUBJECT_STEM],
            "group_transition_effects_excel": tables[_ARCHETYPE_EEG_TRANSITION_GROUP_STEM],
        }
    eeg_outputs = run_eeg_states_stage(cfg)
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    eeg_templates = build_eeg_microstate_template_table(load_microstate_model(eeg_outputs["model"]))
    field_labels = read_dataframe(state_paths["labels"])
    assignment_df = read_dataframe(archetype_outputs["assignments"])
    archetype_df = read_dataframe(archetype_outputs["archetypes"])
    valid_archetypes = (
        set(archetype_df["field_state"].astype(int).tolist())
        if not archetype_df.empty and "field_state" in archetype_df.columns
        else set()
    )
    if valid_archetypes:
        assignment_df = assignment_df[assignment_df["assigned_archetype"].astype(int).isin(valid_archetypes)].copy()
    else:
        assignment_df = assignment_df.iloc[0:0].copy()
    subject_map_frames: list[pd.DataFrame] = []
    subject_similarity_frames: list[pd.DataFrame] = []
    subject_preference_frames: list[pd.DataFrame] = []
    subject_fine_lag_frames: list[pd.DataFrame] = []
    subject_fine_lag_peak_frames: list[pd.DataFrame] = []
    subject_transition_frames: list[pd.DataFrame] = []
    for offset, row in enumerate(_eligible_rows(cfg).to_dict(orient="records")):
        patient_id = str(row["patient_id"])
        patient_eeg_labels = eeg_labels[eeg_labels["patient_id"] == patient_id].copy()
        patient_field_labels = field_labels[field_labels["patient_id"] == patient_id].copy()
        patient_assignments = assignment_df[assignment_df["patient_id"].astype(str) == patient_id].copy()
        if patient_eeg_labels.empty or patient_field_labels.empty or patient_assignments.empty:
            continue
        eeg_topography = _load_patient_eeg_topography_trace(cfg, row, patient_id=patient_id)
        aligned = align_eeg_topography_to_archetypes(
            eeg_topography,
            patient_eeg_labels,
            patient_field_labels,
            patient_assignments,
            patient_id=patient_id,
        )
        if aligned.empty:
            continue
        subject_maps = compute_subject_archetype_conditioned_eeg_maps(aligned, patient_id=patient_id)
        if not subject_maps.empty:
            subject_map_frames.append(subject_maps)
            subject_similarity_frames.append(
                compute_subject_archetype_template_similarity(subject_maps, eeg_templates, patient_id=patient_id)
            )
        subject_preference_frames.append(compute_subject_archetype_state_preference(aligned, patient_id=patient_id))
        sample_period = sample_period_from_times(aligned["time_sec"].to_numpy(dtype=float))
        if sample_period > 0.0:
            lag_window_samples = max(1, int(round(window_ms / (sample_period * 1000.0))))
            lag_samples = list(range(-lag_window_samples, lag_window_samples + 1))
            coupling_input = aligned.drop(columns=["field_state"]).rename(columns={"assigned_archetype": "field_state"})
            subject_curve = compute_subject_field_state_coupling(
                coupling_input,
                patient_id=patient_id,
                lag_samples=lag_samples,
                sample_period_sec=sample_period,
                n_surrogates=surrogates,
                seed=cfg.random_seed + offset,
            )
            if not subject_curve.empty:
                subject_curve["comparison_space"] = comparison_space
                subject_fine_lag_frames.append(subject_curve)
                subject_peak = summarize_subject_fine_lag_profile(subject_curve, patient_id=patient_id)
                subject_peak["comparison_space"] = comparison_space
                subject_fine_lag_peak_frames.append(subject_peak)
        archetype_label_df = patient_field_labels.merge(
            patient_assignments[
                ["patient_id", "field_state", "assigned_archetype", "comparison_space"]
            ].copy(),
            on=["patient_id", "field_state"],
            how="inner",
        )
        if not archetype_label_df.empty:
            transition_input = archetype_label_df.copy()
            transition_input["field_state"] = transition_input["assigned_archetype"].astype(int)
            transition_effects = compute_subject_field_state_to_eeg_switching(
                transition_input[
                    [
                        "time_sec",
                        "field_state",
                        "peak_metric",
                        "normalization",
                        "n_states",
                        "min_duration_ms",
                    ]
                ],
                patient_eeg_labels,
                patient_id=patient_id,
                window_sec=window_sec,
                n_surrogates=surrogates,
                seed=cfg.random_seed + offset,
            )
            if not transition_effects.empty:
                transition_effects["comparison_space"] = comparison_space
                subject_transition_frames.append(transition_effects)
    subject_maps_df = pd.concat(subject_map_frames, ignore_index=True) if subject_map_frames else pd.DataFrame()
    group_maps_df = summarize_group_archetype_conditioned_eeg_maps(subject_maps_df, min_subjects=threshold)
    subject_similarity_df = (
        pd.concat(subject_similarity_frames, ignore_index=True) if subject_similarity_frames else pd.DataFrame()
    )
    group_similarity_df = summarize_group_archetype_template_similarity(subject_similarity_df, min_subjects=threshold)
    subject_preference_df = (
        pd.concat(subject_preference_frames, ignore_index=True) if subject_preference_frames else pd.DataFrame()
    )
    group_preference_df = run_group_scalar_statistics(
        subject_preference_df,
        group_keys=[
            "comparison_space",
            "peak_metric",
            "normalization",
            "n_states",
            "min_duration_ms",
            "assigned_archetype",
            "microstate",
        ],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    if not group_preference_df.empty and not subject_preference_df.empty:
        probability_summary = (
            subject_preference_df.groupby(
                [
                    "comparison_space",
                    "peak_metric",
                    "normalization",
                    "n_states",
                    "min_duration_ms",
                    "assigned_archetype",
                    "microstate",
                ],
                as_index=False,
            )
            .agg(
                mean_conditional_probability=("conditional_probability", "mean"),
                mean_baseline_probability=("baseline_probability", "mean"),
                mean_joint_samples=("joint_samples", "mean"),
                mean_state_samples=("n_samples", "mean"),
            )
        )
        group_preference_df = group_preference_df.merge(
            probability_summary,
            on=[
                "comparison_space",
                "peak_metric",
                "normalization",
                "n_states",
                "min_duration_ms",
                "assigned_archetype",
                "microstate",
            ],
            how="left",
        )
    subject_fine_lag_df = pd.concat(subject_fine_lag_frames, ignore_index=True) if subject_fine_lag_frames else pd.DataFrame()
    group_fine_lag_df = run_group_scalar_statistics(
        subject_fine_lag_df,
        group_keys=["comparison_space", "peak_metric", "normalization", "n_states", "min_duration_ms", "lag_ms"],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    if not group_fine_lag_df.empty and not subject_fine_lag_df.empty:
        lag_summary = (
            subject_fine_lag_df.groupby(
                ["comparison_space", "peak_metric", "normalization", "n_states", "min_duration_ms", "lag_ms"],
                as_index=False,
            )
            .agg(
                mean_observed_coupling=("observed_coupling", "mean"),
                mean_null_mean_coupling=("null_mean_coupling", "mean"),
            )
        )
        group_fine_lag_df = group_fine_lag_df.merge(
            lag_summary,
            on=["comparison_space", "peak_metric", "normalization", "n_states", "min_duration_ms", "lag_ms"],
            how="left",
        )
    subject_fine_lag_peak_df = (
        pd.concat(subject_fine_lag_peak_frames, ignore_index=True) if subject_fine_lag_peak_frames else pd.DataFrame()
    )
    peak_long = (
        subject_fine_lag_peak_df.melt(
            id_vars=["patient_id", "comparison_space", "peak_metric", "normalization", "n_states", "min_duration_ms"],
            value_vars=["peak_lag_ms", "peak_effect_mean_diff", "peak_width_ms"],
            var_name="summary_kind",
            value_name="summary_value",
        )
        if not subject_fine_lag_peak_df.empty
        else pd.DataFrame(
            columns=[
                "patient_id",
                "comparison_space",
                "peak_metric",
                "normalization",
                "n_states",
                "min_duration_ms",
                "summary_kind",
                "summary_value",
            ]
        )
    )
    group_fine_lag_peak_df = run_group_scalar_statistics(
        peak_long,
        group_keys=["comparison_space", "peak_metric", "normalization", "n_states", "min_duration_ms", "summary_kind"],
        value_column="summary_value",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    subject_transition_df = (
        pd.concat(subject_transition_frames, ignore_index=True) if subject_transition_frames else pd.DataFrame()
    )
    group_transition_df = run_group_scalar_statistics(
        subject_transition_df,
        group_keys=[
            "comparison_space",
            "peak_metric",
            "normalization",
            "n_states",
            "min_duration_ms",
            "from_state",
            "to_state",
            "response_kind",
            "response_state",
        ],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    subject_map_path = write_dataframe(subject_maps_df, cached["subject_maps"])
    group_map_path = write_dataframe(group_maps_df, cached["group_maps"])
    subject_similarity_path = write_dataframe(subject_similarity_df, cached["subject_similarity"])
    group_similarity_path = write_dataframe(group_similarity_df, cached["group_similarity"])
    subject_preference_path = write_dataframe(subject_preference_df, cached["subject_preference"])
    group_preference_path = write_dataframe(group_preference_df, cached["group_preference"])
    subject_fine_lag_path = write_dataframe(subject_fine_lag_df, cached["subject_fine_lag"])
    group_fine_lag_path = write_dataframe(group_fine_lag_df, cached["group_fine_lag"])
    subject_fine_lag_peak_path = write_dataframe(subject_fine_lag_peak_df, cached["subject_fine_lag_peaks"])
    group_fine_lag_peak_path = write_dataframe(group_fine_lag_peak_df, cached["group_fine_lag_peak_summary"])
    subject_transition_path = write_dataframe(subject_transition_df, cached["subject_transition_effects"])
    group_transition_path = write_dataframe(group_transition_df, cached["group_transition_effects"])
    tables = _write_table_reports(
        cfg,
        {
            _ARCHETYPE_EEG_MAP_SUBJECT_STEM: subject_maps_df,
            _ARCHETYPE_EEG_MAP_GROUP_STEM: group_maps_df,
            _ARCHETYPE_EEG_SIMILARITY_SUBJECT_STEM: subject_similarity_df,
            _ARCHETYPE_EEG_SIMILARITY_GROUP_STEM: group_similarity_df,
            _ARCHETYPE_EEG_PREFERENCE_SUBJECT_STEM: subject_preference_df,
            _ARCHETYPE_EEG_PREFERENCE_GROUP_STEM: group_preference_df,
            _ARCHETYPE_EEG_FINE_LAG_SUBJECT_STEM: subject_fine_lag_df,
            _ARCHETYPE_EEG_FINE_LAG_GROUP_STEM: group_fine_lag_df,
            _ARCHETYPE_EEG_FINE_LAG_PEAK_SUBJECT_STEM: subject_fine_lag_peak_df,
            _ARCHETYPE_EEG_FINE_LAG_PEAK_GROUP_STEM: group_fine_lag_peak_df,
            _ARCHETYPE_EEG_TRANSITION_SUBJECT_STEM: subject_transition_df,
            _ARCHETYPE_EEG_TRANSITION_GROUP_STEM: group_transition_df,
        },
        branch=branch,
    )
    return {
        "field_trace": state_paths["trace"],
        "field_peaks": state_paths["peaks"],
        "field_peak_maps": state_paths["peak_maps"],
        "field_templates": state_paths["templates"],
        "field_labels": state_paths["labels"],
        "field_profiles": state_paths["profiles"],
        "field_transition_profiles": state_paths["transition_profiles"],
        "archetype_assignments": archetype_outputs["assignments"],
        "archetypes": archetype_outputs["archetypes"],
        "archetype_support": archetype_outputs["support"],
        "subject_maps": subject_map_path,
        "group_maps": group_map_path,
        "subject_similarity": subject_similarity_path,
        "group_similarity": group_similarity_path,
        "subject_preference": subject_preference_path,
        "group_preference": group_preference_path,
        "subject_fine_lag": subject_fine_lag_path,
        "group_fine_lag": group_fine_lag_path,
        "subject_fine_lag_peaks": subject_fine_lag_peak_path,
        "group_fine_lag_peak_summary": group_fine_lag_peak_path,
        "subject_transition_effects": subject_transition_path,
        "group_transition_effects": group_transition_path,
        "subject_maps_excel": tables[_ARCHETYPE_EEG_MAP_SUBJECT_STEM],
        "group_maps_excel": tables[_ARCHETYPE_EEG_MAP_GROUP_STEM],
        "subject_similarity_excel": tables[_ARCHETYPE_EEG_SIMILARITY_SUBJECT_STEM],
        "group_similarity_excel": tables[_ARCHETYPE_EEG_SIMILARITY_GROUP_STEM],
        "subject_preference_excel": tables[_ARCHETYPE_EEG_PREFERENCE_SUBJECT_STEM],
        "group_preference_excel": tables[_ARCHETYPE_EEG_PREFERENCE_GROUP_STEM],
        "subject_fine_lag_excel": tables[_ARCHETYPE_EEG_FINE_LAG_SUBJECT_STEM],
        "group_fine_lag_excel": tables[_ARCHETYPE_EEG_FINE_LAG_GROUP_STEM],
        "subject_fine_lag_peaks_excel": tables[_ARCHETYPE_EEG_FINE_LAG_PEAK_SUBJECT_STEM],
        "group_fine_lag_peak_summary_excel": tables[_ARCHETYPE_EEG_FINE_LAG_PEAK_GROUP_STEM],
        "subject_transition_effects_excel": tables[_ARCHETYPE_EEG_TRANSITION_SUBJECT_STEM],
        "group_transition_effects_excel": tables[_ARCHETYPE_EEG_TRANSITION_GROUP_STEM],
    }


def run_exploratory_fine_lag_field_state_coupling_stage(
    cfg: AnalysisConfig,
    *,
    field_peak_metric: str = DEFAULT_FIELD_STATE_PEAK_METRIC,
    field_normalization: str = DEFAULT_FIELD_STATE_NORMALIZATION,
    field_state_count: int | None = None,
    field_min_duration_ms: int | None = None,
    fine_lag_window_ms: int | None = None,
    field_surrogates: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_field_peak_metric(field_peak_metric)
    normalized_strategy = normalize_field_normalization(field_normalization)
    state_count = _resolve_field_state_count(field_state_count, cfg)
    min_duration_ms = _resolve_field_min_duration_ms(field_min_duration_ms, cfg)
    window_ms = _resolve_fine_field_lag_window_ms(fine_lag_window_ms)
    surrogates = _resolve_field_surrogates(field_surrogates)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    _field_branch, state_paths = _ensure_seeg_field_state_artifacts(
        cfg,
        peak_metric=normalized_metric,
        normalization=normalized_strategy,
        state_count=state_count,
        min_duration_ms=min_duration_ms,
    )
    branch = _exploratory_branch(
        cfg,
        "fine-lag-field-state-coupling",
        params={
            "peak_metric": normalized_metric,
            "normalization": normalized_strategy,
            "state_count": state_count,
            "min_duration_ms": min_duration_ms,
            "fine_lag_window_ms": window_ms,
            "surrogates": surrogates,
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", _FINE_LAG_FIELD_STATE_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", _FINE_LAG_FIELD_STATE_GROUP_STEM, ext="parquet", branch=branch),
        "subject_peaks": cfg.cache_path("coupling", _FINE_LAG_FIELD_STATE_PEAK_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_peak_summary": cfg.cache_path("stats", _FINE_LAG_FIELD_STATE_PEAK_GROUP_STEM, ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _FINE_LAG_FIELD_STATE_SUBJECT_STEM: cached["subject_effects"],
                _FINE_LAG_FIELD_STATE_GROUP_STEM: cached["group_effects"],
                _FINE_LAG_FIELD_STATE_PEAK_SUBJECT_STEM: cached["subject_peaks"],
                _FINE_LAG_FIELD_STATE_PEAK_GROUP_STEM: cached["group_peak_summary"],
            },
            branch=branch,
        )
        return {
            "field_trace": state_paths["trace"],
            "field_peaks": state_paths["peaks"],
            "field_peak_maps": state_paths["peak_maps"],
            "field_templates": state_paths["templates"],
            "field_labels": state_paths["labels"],
            "field_profiles": state_paths["profiles"],
            "field_transition_profiles": state_paths["transition_profiles"],
            **cached,
            "subject_effects_excel": tables[_FINE_LAG_FIELD_STATE_SUBJECT_STEM],
            "group_effects_excel": tables[_FINE_LAG_FIELD_STATE_GROUP_STEM],
            "subject_peaks_excel": tables[_FINE_LAG_FIELD_STATE_PEAK_SUBJECT_STEM],
            "group_peak_summary_excel": tables[_FINE_LAG_FIELD_STATE_PEAK_GROUP_STEM],
        }
    eeg_outputs = run_eeg_states_stage(cfg)
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    field_labels = read_dataframe(state_paths["labels"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    subject_peak_frames: list[pd.DataFrame] = []
    for offset, patient_id in enumerate(cohort["patient_id"].astype(str)):
        aligned = align_eeg_and_field_state_labels(
            eeg_labels[eeg_labels["patient_id"] == patient_id],
            field_labels[field_labels["patient_id"] == patient_id],
            patient_id=patient_id,
        )
        sample_period = sample_period_from_times(aligned["time_sec"].to_numpy(dtype=float)) if not aligned.empty else 0.0
        if sample_period <= 0.0:
            continue
        lag_window_samples = max(1, int(round(window_ms / (sample_period * 1000.0))))
        lag_samples = list(range(-lag_window_samples, lag_window_samples + 1))
        subject_curve = compute_subject_field_state_coupling(
            aligned,
            patient_id=patient_id,
            lag_samples=lag_samples,
            sample_period_sec=sample_period,
            n_surrogates=surrogates,
            seed=cfg.random_seed + offset,
        )
        subject_frames.append(subject_curve)
        subject_peak_frames.append(summarize_subject_fine_lag_profile(subject_curve, patient_id=patient_id))
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    subject_peaks = pd.concat(subject_peak_frames, ignore_index=True) if subject_peak_frames else pd.DataFrame()
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_scalar_statistics(
        subject_effects,
        group_keys=["peak_metric", "normalization", "n_states", "min_duration_ms", "lag_ms"],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    subject_peak_path = write_dataframe(subject_peaks, cached["subject_peaks"])
    peak_long = (
        subject_peaks.melt(
            id_vars=["patient_id", "peak_metric", "normalization", "n_states", "min_duration_ms"],
            value_vars=["peak_lag_ms", "peak_effect_mean_diff", "peak_width_ms"],
            var_name="summary_kind",
            value_name="summary_value",
        )
        if not subject_peaks.empty
        else pd.DataFrame(
            columns=[
                "patient_id",
                "peak_metric",
                "normalization",
                "n_states",
                "min_duration_ms",
                "summary_kind",
                "summary_value",
            ]
        )
    )
    group_peak_summary = run_group_scalar_statistics(
        peak_long,
        group_keys=["peak_metric", "normalization", "n_states", "min_duration_ms", "summary_kind"],
        value_column="summary_value",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_peak_path = write_dataframe(group_peak_summary, cached["group_peak_summary"])
    tables = _write_table_reports(
        cfg,
        {
            _FINE_LAG_FIELD_STATE_SUBJECT_STEM: subject_effects,
            _FINE_LAG_FIELD_STATE_GROUP_STEM: group_effects,
            _FINE_LAG_FIELD_STATE_PEAK_SUBJECT_STEM: subject_peaks,
            _FINE_LAG_FIELD_STATE_PEAK_GROUP_STEM: group_peak_summary,
        },
        branch=branch,
    )
    return {
        "field_trace": state_paths["trace"],
        "field_peaks": state_paths["peaks"],
        "field_peak_maps": state_paths["peak_maps"],
        "field_templates": state_paths["templates"],
        "field_labels": state_paths["labels"],
        "field_profiles": state_paths["profiles"],
        "field_transition_profiles": state_paths["transition_profiles"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_peaks": subject_peak_path,
        "group_peak_summary": group_peak_path,
        "subject_effects_excel": tables[_FINE_LAG_FIELD_STATE_SUBJECT_STEM],
        "group_effects_excel": tables[_FINE_LAG_FIELD_STATE_GROUP_STEM],
        "subject_peaks_excel": tables[_FINE_LAG_FIELD_STATE_PEAK_SUBJECT_STEM],
        "group_peak_summary_excel": tables[_FINE_LAG_FIELD_STATE_PEAK_GROUP_STEM],
    }


def run_exploratory_transition_field_state_coupling_stage(
    cfg: AnalysisConfig,
    *,
    field_peak_metric: str = DEFAULT_FIELD_STATE_PEAK_METRIC,
    field_normalization: str = DEFAULT_FIELD_STATE_NORMALIZATION,
    field_state_count: int | None = None,
    field_min_duration_ms: int | None = None,
    transition_window_sec: float | None = None,
    field_surrogates: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_field_peak_metric(field_peak_metric)
    normalized_strategy = normalize_field_normalization(field_normalization)
    state_count = _resolve_field_state_count(field_state_count, cfg)
    min_duration_ms = _resolve_field_min_duration_ms(field_min_duration_ms, cfg)
    window_sec = _resolve_transition_window_sec(transition_window_sec, cfg)
    surrogates = _resolve_field_surrogates(field_surrogates)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    event_paths = _ensure_exploratory_event_tables(cfg)
    _field_branch, state_paths = _ensure_seeg_field_state_artifacts(
        cfg,
        peak_metric=normalized_metric,
        normalization=normalized_strategy,
        state_count=state_count,
        min_duration_ms=min_duration_ms,
    )
    branch = _exploratory_branch(
        cfg,
        "transition-field-state-coupling",
        params={
            "peak_metric": normalized_metric,
            "normalization": normalized_strategy,
            "state_count": state_count,
            "min_duration_ms": min_duration_ms,
            "transition_window_sec": float(window_sec),
            "surrogates": surrogates,
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", _TRANSITION_FIELD_STATE_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", _TRANSITION_FIELD_STATE_GROUP_STEM, ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _TRANSITION_FIELD_STATE_SUBJECT_STEM: cached["subject_effects"],
                _TRANSITION_FIELD_STATE_GROUP_STEM: cached["group_effects"],
            },
            branch=branch,
        )
        return {
            "transitions": event_paths["transitions"],
            "field_trace": state_paths["trace"],
            "field_peaks": state_paths["peaks"],
            "field_peak_maps": state_paths["peak_maps"],
            "field_templates": state_paths["templates"],
            "field_labels": state_paths["labels"],
            "field_profiles": state_paths["profiles"],
            "field_transition_profiles": state_paths["transition_profiles"],
            **cached,
            "subject_effects_excel": tables[_TRANSITION_FIELD_STATE_SUBJECT_STEM],
            "group_effects_excel": tables[_TRANSITION_FIELD_STATE_GROUP_STEM],
        }
    eeg_transitions = read_dataframe(event_paths["transitions"])
    field_labels = read_dataframe(state_paths["labels"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    for offset, patient_id in enumerate(cohort["patient_id"].astype(str)):
        subject_frames.append(
            compute_subject_transition_field_state_coupling(
                eeg_transitions[eeg_transitions["patient_id"] == patient_id],
                field_labels[field_labels["patient_id"] == patient_id],
                patient_id=patient_id,
                window_sec=window_sec,
                n_surrogates=surrogates,
                seed=cfg.random_seed + offset,
            )
        )
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_scalar_statistics(
        subject_effects,
        group_keys=[
            "peak_metric",
            "normalization",
            "n_states",
            "min_duration_ms",
            "from_state",
            "to_state",
            "response_kind",
            "response_state",
        ],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            _TRANSITION_FIELD_STATE_SUBJECT_STEM: subject_effects,
            _TRANSITION_FIELD_STATE_GROUP_STEM: group_effects,
        },
        branch=branch,
    )
    return {
        "transitions": event_paths["transitions"],
        "field_trace": state_paths["trace"],
        "field_peaks": state_paths["peaks"],
        "field_peak_maps": state_paths["peak_maps"],
        "field_templates": state_paths["templates"],
        "field_labels": state_paths["labels"],
        "field_profiles": state_paths["profiles"],
        "field_transition_profiles": state_paths["transition_profiles"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables[_TRANSITION_FIELD_STATE_SUBJECT_STEM],
        "group_effects_excel": tables[_TRANSITION_FIELD_STATE_GROUP_STEM],
    }


def run_exploratory_gfp_controlled_field_state_switching_stage(
    cfg: AnalysisConfig,
    *,
    field_peak_metric: str = DEFAULT_FIELD_STATE_PEAK_METRIC,
    field_normalization: str = DEFAULT_FIELD_STATE_NORMALIZATION,
    field_state_count: int | None = None,
    field_min_duration_ms: int | None = None,
    transition_window_sec: float | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_field_peak_metric(field_peak_metric)
    normalized_strategy = normalize_field_normalization(field_normalization)
    state_count = _resolve_field_state_count(field_state_count, cfg)
    min_duration_ms = _resolve_field_min_duration_ms(field_min_duration_ms, cfg)
    window_sec = _resolve_transition_window_sec(transition_window_sec, cfg)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    event_paths = _ensure_exploratory_event_tables(cfg)
    _field_branch, state_paths = _ensure_seeg_field_state_artifacts(
        cfg,
        peak_metric=normalized_metric,
        normalization=normalized_strategy,
        state_count=state_count,
        min_duration_ms=min_duration_ms,
    )
    branch = _exploratory_branch(
        cfg,
        "gfp-controlled-field-state-switching",
        params={
            "peak_metric": normalized_metric,
            "normalization": normalized_strategy,
            "state_count": state_count,
            "min_duration_ms": min_duration_ms,
            "transition_window_sec": float(window_sec),
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_profiles": cfg.cache_path("coupling", _GFP_CONTROLLED_FIELD_STATE_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_omnibus": cfg.cache_path("stats", _GFP_CONTROLLED_FIELD_STATE_GROUP_OMNIBUS_STEM, ext="parquet", branch=branch),
        "group_posthoc": cfg.cache_path("stats", _GFP_CONTROLLED_FIELD_STATE_GROUP_POSTHOC_STEM, ext="parquet", branch=branch),
        "subject_transition_effects": cfg.cache_path(
            "coupling", _GFP_CONTROLLED_FIELD_STATE_TRANSITION_SUBJECT_STEM, ext="parquet", branch=branch
        ),
        "group_transition_effects": cfg.cache_path(
            "stats", _GFP_CONTROLLED_FIELD_STATE_TRANSITION_GROUP_STEM, ext="parquet", branch=branch
        ),
    }
    eeg_outputs = run_eeg_states_stage(cfg)
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _GFP_CONTROLLED_FIELD_STATE_SUBJECT_STEM: cached["subject_profiles"],
                _GFP_CONTROLLED_FIELD_STATE_GROUP_OMNIBUS_STEM: cached["group_omnibus"],
                _GFP_CONTROLLED_FIELD_STATE_GROUP_POSTHOC_STEM: cached["group_posthoc"],
                _GFP_CONTROLLED_FIELD_STATE_TRANSITION_SUBJECT_STEM: cached["subject_transition_effects"],
                _GFP_CONTROLLED_FIELD_STATE_TRANSITION_GROUP_STEM: cached["group_transition_effects"],
            },
            branch=branch,
        )
        return {
            "transitions": event_paths["transitions"],
            "gfp_trace": eeg_outputs["gfp_trace"],
            "field_trace": state_paths["trace"],
            "field_peaks": state_paths["peaks"],
            "field_peak_maps": state_paths["peak_maps"],
            "field_templates": state_paths["templates"],
            "field_labels": state_paths["labels"],
            "field_profiles": state_paths["profiles"],
            "field_transition_profiles": state_paths["transition_profiles"],
            **cached,
            "subject_profiles_excel": tables[_GFP_CONTROLLED_FIELD_STATE_SUBJECT_STEM],
            "group_omnibus_excel": tables[_GFP_CONTROLLED_FIELD_STATE_GROUP_OMNIBUS_STEM],
            "group_posthoc_excel": tables[_GFP_CONTROLLED_FIELD_STATE_GROUP_POSTHOC_STEM],
            "subject_transition_effects_excel": tables[_GFP_CONTROLLED_FIELD_STATE_TRANSITION_SUBJECT_STEM],
            "group_transition_effects_excel": tables[_GFP_CONTROLLED_FIELD_STATE_TRANSITION_GROUP_STEM],
        }
    label_df = read_dataframe(eeg_outputs["labels"])
    gfp_trace_df = read_dataframe(eeg_outputs["gfp_trace"])
    transition_df = read_dataframe(event_paths["transitions"])
    field_label_df = read_dataframe(state_paths["labels"])
    cohort = _eligible_rows(cfg)
    subject_profile_frames: list[pd.DataFrame] = []
    subject_transition_frames: list[pd.DataFrame] = []
    for patient_id in cohort["patient_id"].astype(str):
        aligned = align_eeg_gfp_and_field_state_labels(
            label_df[label_df["patient_id"] == patient_id],
            gfp_trace_df[gfp_trace_df["patient_id"] == patient_id],
            field_label_df[field_label_df["patient_id"] == patient_id],
            patient_id=patient_id,
        )
        subject_profile_frames.append(
            compute_subject_gfp_controlled_field_state_profiles(
                aligned,
                patient_id=patient_id,
            )
        )
        sample_period = sample_period_from_times(aligned["time_sec"].to_numpy(dtype=float)) if not aligned.empty else 0.0
        subject_transition_frames.append(
            compute_subject_gfp_controlled_field_state_transition_effects(
                transition_df[transition_df["patient_id"] == patient_id],
                aligned,
                patient_id=patient_id,
                window_sec=window_sec,
                sample_period_sec=sample_period,
            )
        )
    subject_profiles = pd.concat(subject_profile_frames, ignore_index=True) if subject_profile_frames else pd.DataFrame()
    subject_profiles_path = write_dataframe(subject_profiles, cached["subject_profiles"])
    group_omnibus = run_group_profile_omnibus_statistics(
        subject_profiles,
        group_keys=["peak_metric", "normalization", "n_states", "min_duration_ms"],
        value_column="adjusted_switch_rate",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_omnibus_path = write_dataframe(group_omnibus, cached["group_omnibus"])
    group_posthoc = run_group_profile_posthoc_statistics(
        subject_profiles,
        group_keys=["peak_metric", "normalization", "n_states", "min_duration_ms"],
        value_column="adjusted_switch_rate",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_posthoc_path = write_dataframe(group_posthoc, cached["group_posthoc"])
    subject_transition_effects = (
        pd.concat(subject_transition_frames, ignore_index=True) if subject_transition_frames else pd.DataFrame()
    )
    subject_transition_effects_path = write_dataframe(subject_transition_effects, cached["subject_transition_effects"])
    group_transition_effects = run_group_scalar_statistics(
        subject_transition_effects,
        group_keys=["peak_metric", "normalization", "n_states", "min_duration_ms", "from_state", "to_state"],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_transition_effects_path = write_dataframe(group_transition_effects, cached["group_transition_effects"])
    tables = _write_table_reports(
        cfg,
        {
            _GFP_CONTROLLED_FIELD_STATE_SUBJECT_STEM: subject_profiles,
            _GFP_CONTROLLED_FIELD_STATE_GROUP_OMNIBUS_STEM: group_omnibus,
            _GFP_CONTROLLED_FIELD_STATE_GROUP_POSTHOC_STEM: group_posthoc,
            _GFP_CONTROLLED_FIELD_STATE_TRANSITION_SUBJECT_STEM: subject_transition_effects,
            _GFP_CONTROLLED_FIELD_STATE_TRANSITION_GROUP_STEM: group_transition_effects,
        },
        branch=branch,
    )
    return {
        "transitions": event_paths["transitions"],
        "gfp_trace": eeg_outputs["gfp_trace"],
        "field_trace": state_paths["trace"],
        "field_peaks": state_paths["peaks"],
        "field_peak_maps": state_paths["peak_maps"],
        "field_templates": state_paths["templates"],
        "field_labels": state_paths["labels"],
        "field_profiles": state_paths["profiles"],
        "field_transition_profiles": state_paths["transition_profiles"],
        "subject_profiles": subject_profiles_path,
        "group_omnibus": group_omnibus_path,
        "group_posthoc": group_posthoc_path,
        "subject_transition_effects": subject_transition_effects_path,
        "group_transition_effects": group_transition_effects_path,
        "subject_profiles_excel": tables[_GFP_CONTROLLED_FIELD_STATE_SUBJECT_STEM],
        "group_omnibus_excel": tables[_GFP_CONTROLLED_FIELD_STATE_GROUP_OMNIBUS_STEM],
        "group_posthoc_excel": tables[_GFP_CONTROLLED_FIELD_STATE_GROUP_POSTHOC_STEM],
        "subject_transition_effects_excel": tables[_GFP_CONTROLLED_FIELD_STATE_TRANSITION_SUBJECT_STEM],
        "group_transition_effects_excel": tables[_GFP_CONTROLLED_FIELD_STATE_TRANSITION_GROUP_STEM],
    }


def run_exploratory_field_state_to_eeg_switching_stage(
    cfg: AnalysisConfig,
    *,
    field_peak_metric: str = DEFAULT_FIELD_STATE_PEAK_METRIC,
    field_normalization: str = DEFAULT_FIELD_STATE_NORMALIZATION,
    field_state_count: int | None = None,
    field_min_duration_ms: int | None = None,
    transition_window_sec: float | None = None,
    field_surrogates: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_field_peak_metric(field_peak_metric)
    normalized_strategy = normalize_field_normalization(field_normalization)
    state_count = _resolve_field_state_count(field_state_count, cfg)
    min_duration_ms = _resolve_field_min_duration_ms(field_min_duration_ms, cfg)
    window_sec = _resolve_transition_window_sec(transition_window_sec, cfg)
    surrogates = _resolve_field_surrogates(field_surrogates)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    _field_branch, state_paths = _ensure_seeg_field_state_artifacts(
        cfg,
        peak_metric=normalized_metric,
        normalization=normalized_strategy,
        state_count=state_count,
        min_duration_ms=min_duration_ms,
    )
    branch = _exploratory_branch(
        cfg,
        "field-state-to-eeg-switching",
        params={
            "peak_metric": normalized_metric,
            "normalization": normalized_strategy,
            "state_count": state_count,
            "min_duration_ms": min_duration_ms,
            "transition_window_sec": float(window_sec),
            "surrogates": surrogates,
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", _FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", _FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM, ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM: cached["subject_effects"],
                _FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM: cached["group_effects"],
            },
            branch=branch,
        )
        return {
            "field_trace": state_paths["trace"],
            "field_peaks": state_paths["peaks"],
            "field_peak_maps": state_paths["peak_maps"],
            "field_templates": state_paths["templates"],
            "field_labels": state_paths["labels"],
            "field_profiles": state_paths["profiles"],
            "field_transition_profiles": state_paths["transition_profiles"],
            **cached,
            "subject_effects_excel": tables[_FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM],
            "group_effects_excel": tables[_FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM],
        }
    eeg_outputs = run_eeg_states_stage(cfg)
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    field_labels = read_dataframe(state_paths["labels"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    for offset, patient_id in enumerate(cohort["patient_id"].astype(str)):
        subject_frames.append(
            compute_subject_field_state_to_eeg_switching(
                field_labels[field_labels["patient_id"] == patient_id],
                eeg_labels[eeg_labels["patient_id"] == patient_id],
                patient_id=patient_id,
                window_sec=window_sec,
                n_surrogates=surrogates,
                seed=cfg.random_seed + offset,
            )
        )
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_scalar_statistics(
        subject_effects,
        group_keys=[
            "peak_metric",
            "normalization",
            "n_states",
            "min_duration_ms",
            "from_state",
            "to_state",
            "response_kind",
            "response_state",
        ],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            _FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM: subject_effects,
            _FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM: group_effects,
        },
        branch=branch,
    )
    return {
        "field_trace": state_paths["trace"],
        "field_peaks": state_paths["peaks"],
        "field_peak_maps": state_paths["peak_maps"],
        "field_templates": state_paths["templates"],
        "field_labels": state_paths["labels"],
        "field_profiles": state_paths["profiles"],
        "field_transition_profiles": state_paths["transition_profiles"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables[_FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM],
        "group_effects_excel": tables[_FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM],
    }


def run_exploratory_gfp_controlled_field_state_to_eeg_switching_stage(
    cfg: AnalysisConfig,
    *,
    field_peak_metric: str = DEFAULT_FIELD_STATE_PEAK_METRIC,
    field_normalization: str = DEFAULT_FIELD_STATE_NORMALIZATION,
    field_state_count: int | None = None,
    field_min_duration_ms: int | None = None,
    transition_window_sec: float | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_field_peak_metric(field_peak_metric)
    normalized_strategy = normalize_field_normalization(field_normalization)
    state_count = _resolve_field_state_count(field_state_count, cfg)
    min_duration_ms = _resolve_field_min_duration_ms(field_min_duration_ms, cfg)
    window_sec = _resolve_transition_window_sec(transition_window_sec, cfg)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    _field_branch, state_paths = _ensure_seeg_field_state_artifacts(
        cfg,
        peak_metric=normalized_metric,
        normalization=normalized_strategy,
        state_count=state_count,
        min_duration_ms=min_duration_ms,
    )
    branch = _exploratory_branch(
        cfg,
        "gfp-controlled-field-state-to-eeg-switching",
        params={
            "peak_metric": normalized_metric,
            "normalization": normalized_strategy,
            "state_count": state_count,
            "min_duration_ms": min_duration_ms,
            "transition_window_sec": float(window_sec),
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_effects": cfg.cache_path(
            "coupling",
            _GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM,
            ext="parquet",
            branch=branch,
        ),
        "group_effects": cfg.cache_path(
            "stats",
            _GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM,
            ext="parquet",
            branch=branch,
        ),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM: cached["subject_effects"],
                _GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM: cached["group_effects"],
            },
            branch=branch,
        )
        return {
            "gfp_trace": run_eeg_states_stage(cfg)["gfp_trace"],
            "field_trace": state_paths["trace"],
            "field_peaks": state_paths["peaks"],
            "field_peak_maps": state_paths["peak_maps"],
            "field_templates": state_paths["templates"],
            "field_labels": state_paths["labels"],
            "field_profiles": state_paths["profiles"],
            "field_transition_profiles": state_paths["transition_profiles"],
            **cached,
            "subject_effects_excel": tables[_GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM],
            "group_effects_excel": tables[_GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM],
        }
    eeg_outputs = run_eeg_states_stage(cfg)
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    gfp_trace = read_dataframe(eeg_outputs["gfp_trace"])
    field_labels = read_dataframe(state_paths["labels"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    for patient_id in cohort["patient_id"].astype(str):
        patient_field_labels = field_labels[field_labels["patient_id"] == patient_id]
        field_transitions = build_state_transition_table(
            patient_field_labels.rename(columns={"field_state": "microstate"})[["time_sec", "microstate"]],
            patient_id=patient_id,
        )
        aligned = align_eeg_gfp_and_field_state_labels(
            eeg_labels[eeg_labels["patient_id"] == patient_id],
            gfp_trace[gfp_trace["patient_id"] == patient_id],
            patient_field_labels,
            patient_id=patient_id,
        )
        sample_period = sample_period_from_times(aligned["time_sec"].to_numpy(dtype=float)) if not aligned.empty else 0.0
        subject_frames.append(
            compute_subject_gfp_controlled_field_state_to_eeg_switching(
                field_transitions,
                aligned,
                patient_id=patient_id,
                window_sec=window_sec,
                sample_period_sec=sample_period,
            )
        )
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_scalar_statistics(
        subject_effects,
        group_keys=["peak_metric", "normalization", "n_states", "min_duration_ms", "from_state", "to_state"],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            _GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM: subject_effects,
            _GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM: group_effects,
        },
        branch=branch,
    )
    return {
        "gfp_trace": eeg_outputs["gfp_trace"],
        "field_trace": state_paths["trace"],
        "field_peaks": state_paths["peaks"],
        "field_peak_maps": state_paths["peak_maps"],
        "field_templates": state_paths["templates"],
        "field_labels": state_paths["labels"],
        "field_profiles": state_paths["profiles"],
        "field_transition_profiles": state_paths["transition_profiles"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables[_GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM],
        "group_effects_excel": tables[_GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM],
    }


def run_exploratory_gfp_global_coupling_stage(
    cfg: AnalysisConfig,
    *,
    global_metric: str = DEFAULT_GFP_GLOBAL_METRIC,
    global_weighting: str = DEFAULT_GFP_GLOBAL_WEIGHTING,
    global_surrogates: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_global_metric_definition(global_metric)
    normalized_weighting = normalize_global_weighting_strategy(global_weighting)
    surrogates = _resolve_global_surrogates(global_surrogates)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    _metric_branch, metric_paths = _ensure_seeg_global_metric_artifacts(
        cfg,
        metric_definition=normalized_metric,
        weighting_strategy=normalized_weighting,
    )
    branch = _exploratory_branch(
        cfg,
        "gfp-global-coupling",
        params={
            "metric_definition": normalized_metric,
            "weighting_strategy": normalized_weighting,
            "surrogates": surrogates,
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", _GFP_GLOBAL_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", _GFP_GLOBAL_GROUP_STEM, ext="parquet", branch=branch),
    }
    eeg_outputs = run_eeg_states_stage(cfg)
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _GFP_GLOBAL_SUBJECT_STEM: cached["subject_effects"],
                _GFP_GLOBAL_GROUP_STEM: cached["group_effects"],
            },
            branch=branch,
        )
        return {
            "gfp_trace": eeg_outputs["gfp_trace"],
            "gfp_peaks": eeg_outputs["gfp_peaks"],
            "global_trace": metric_paths["global_trace"],
            "network_support": metric_paths["network_support"],
            **cached,
            "subject_effects_excel": tables[_GFP_GLOBAL_SUBJECT_STEM],
            "group_effects_excel": tables[_GFP_GLOBAL_GROUP_STEM],
        }
    gfp_trace_df = read_dataframe(eeg_outputs["gfp_trace"])
    global_trace_df = read_dataframe(metric_paths["global_trace"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    for offset, patient_id in enumerate(cohort["patient_id"].astype(str)):
        aligned = align_gfp_and_global_traces(
            gfp_trace_df[gfp_trace_df["patient_id"] == patient_id],
            global_trace_df[global_trace_df["patient_id"] == patient_id],
            patient_id=patient_id,
        )
        sample_period = sample_period_from_times(aligned["time_sec"].to_numpy(dtype=float)) if not aligned.empty else 0.0
        subject_frames.append(
            compute_subject_gfp_global_coupling(
                aligned,
                patient_id=patient_id,
                lag_samples=[0],
                sample_period_sec=sample_period,
                n_surrogates=surrogates,
                seed=cfg.random_seed + offset,
            )
        )
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    if not subject_effects.empty:
        subject_effects["global_metric_label"] = subject_effects.apply(
            lambda row: global_metric_label(str(row.metric_definition), str(row.weighting_strategy)),
            axis=1,
        )
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_scalar_statistics(
        subject_effects,
        group_keys=["metric_definition", "weighting_strategy", "network_scope", "lag_ms"],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    if not group_effects.empty:
        group_effects["global_metric_label"] = group_effects.apply(
            lambda row: global_metric_label(str(row.metric_definition), str(row.weighting_strategy)),
            axis=1,
        )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            _GFP_GLOBAL_SUBJECT_STEM: subject_effects,
            _GFP_GLOBAL_GROUP_STEM: group_effects,
        },
        branch=branch,
    )
    return {
        "gfp_trace": eeg_outputs["gfp_trace"],
        "gfp_peaks": eeg_outputs["gfp_peaks"],
        "global_trace": metric_paths["global_trace"],
        "network_support": metric_paths["network_support"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables[_GFP_GLOBAL_SUBJECT_STEM],
        "group_effects_excel": tables[_GFP_GLOBAL_GROUP_STEM],
    }


def run_exploratory_lagged_gfp_global_coupling_stage(
    cfg: AnalysisConfig,
    *,
    global_metric: str = DEFAULT_GFP_GLOBAL_METRIC,
    global_weighting: str = DEFAULT_GFP_GLOBAL_WEIGHTING,
    max_lag_ms: int | None = None,
    lag_step_ms: int | None = None,
    global_surrogates: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_global_metric_definition(global_metric)
    normalized_weighting = normalize_global_weighting_strategy(global_weighting)
    surrogates = _resolve_global_surrogates(global_surrogates)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    _metric_branch, metric_paths = _ensure_seeg_global_metric_artifacts(
        cfg,
        metric_definition=normalized_metric,
        weighting_strategy=normalized_weighting,
    )
    branch = _exploratory_branch(
        cfg,
        "lagged-gfp-global-coupling",
        params={
            "metric_definition": normalized_metric,
            "weighting_strategy": normalized_weighting,
            "max_lag_ms": int(max_lag_ms if max_lag_ms is not None else cfg.direct_max_lag_ms),
            "lag_step_ms": int(lag_step_ms if lag_step_ms is not None else cfg.direct_lag_step_ms),
            "surrogates": surrogates,
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", _LAGGED_GFP_GLOBAL_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", _LAGGED_GFP_GLOBAL_GROUP_STEM, ext="parquet", branch=branch),
    }
    eeg_outputs = run_eeg_states_stage(cfg)
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _LAGGED_GFP_GLOBAL_SUBJECT_STEM: cached["subject_effects"],
                _LAGGED_GFP_GLOBAL_GROUP_STEM: cached["group_effects"],
            },
            branch=branch,
        )
        return {
            "gfp_trace": eeg_outputs["gfp_trace"],
            "gfp_peaks": eeg_outputs["gfp_peaks"],
            "global_trace": metric_paths["global_trace"],
            "network_support": metric_paths["network_support"],
            **cached,
            "subject_effects_excel": tables[_LAGGED_GFP_GLOBAL_SUBJECT_STEM],
            "group_effects_excel": tables[_LAGGED_GFP_GLOBAL_GROUP_STEM],
        }
    gfp_trace_df = read_dataframe(eeg_outputs["gfp_trace"])
    global_trace_df = read_dataframe(metric_paths["global_trace"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    for offset, patient_id in enumerate(cohort["patient_id"].astype(str)):
        aligned = align_gfp_and_global_traces(
            gfp_trace_df[gfp_trace_df["patient_id"] == patient_id],
            global_trace_df[global_trace_df["patient_id"] == patient_id],
            patient_id=patient_id,
        )
        sample_period = sample_period_from_times(aligned["time_sec"].to_numpy(dtype=float)) if not aligned.empty else 0.0
        subject_frames.append(
            compute_subject_gfp_global_coupling(
                aligned,
                patient_id=patient_id,
                lag_samples=_resolve_direct_lag_grid(
                    cfg,
                    sample_period_sec=sample_period,
                    max_lag_ms=max_lag_ms,
                    lag_step_ms=lag_step_ms,
                ),
                sample_period_sec=sample_period,
                n_surrogates=surrogates,
                seed=cfg.random_seed + offset,
            )
        )
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    if not subject_effects.empty:
        subject_effects["global_metric_label"] = subject_effects.apply(
            lambda row: global_metric_label(str(row.metric_definition), str(row.weighting_strategy)),
            axis=1,
        )
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_scalar_statistics(
        subject_effects,
        group_keys=["metric_definition", "weighting_strategy", "network_scope", "lag_ms"],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    if not group_effects.empty:
        group_effects["global_metric_label"] = group_effects.apply(
            lambda row: global_metric_label(str(row.metric_definition), str(row.weighting_strategy)),
            axis=1,
        )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            _LAGGED_GFP_GLOBAL_SUBJECT_STEM: subject_effects,
            _LAGGED_GFP_GLOBAL_GROUP_STEM: group_effects,
        },
        branch=branch,
    )
    return {
        "gfp_trace": eeg_outputs["gfp_trace"],
        "gfp_peaks": eeg_outputs["gfp_peaks"],
        "global_trace": metric_paths["global_trace"],
        "network_support": metric_paths["network_support"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables[_LAGGED_GFP_GLOBAL_SUBJECT_STEM],
        "group_effects_excel": tables[_LAGGED_GFP_GLOBAL_GROUP_STEM],
    }


def run_exploratory_peak_gfp_global_coupling_stage(
    cfg: AnalysisConfig,
    *,
    global_metric: str = DEFAULT_GFP_GLOBAL_METRIC,
    global_weighting: str = DEFAULT_GFP_GLOBAL_WEIGHTING,
    peak_window_sec: float | None = None,
    global_surrogates: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_global_metric_definition(global_metric)
    normalized_weighting = normalize_global_weighting_strategy(global_weighting)
    window_sec = _resolve_peak_window_sec(peak_window_sec)
    surrogates = _resolve_global_surrogates(global_surrogates)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    _metric_branch, metric_paths = _ensure_seeg_global_metric_artifacts(
        cfg,
        metric_definition=normalized_metric,
        weighting_strategy=normalized_weighting,
    )
    branch = _exploratory_branch(
        cfg,
        "peak-gfp-global-coupling",
        params={
            "metric_definition": normalized_metric,
            "weighting_strategy": normalized_weighting,
            "peak_window_sec": float(window_sec),
            "surrogates": surrogates,
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", _PEAK_GFP_GLOBAL_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", _PEAK_GFP_GLOBAL_GROUP_STEM, ext="parquet", branch=branch),
    }
    eeg_outputs = run_eeg_states_stage(cfg)
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _PEAK_GFP_GLOBAL_SUBJECT_STEM: cached["subject_effects"],
                _PEAK_GFP_GLOBAL_GROUP_STEM: cached["group_effects"],
            },
            branch=branch,
        )
        return {
            "gfp_trace": eeg_outputs["gfp_trace"],
            "gfp_peaks": eeg_outputs["gfp_peaks"],
            "global_trace": metric_paths["global_trace"],
            "network_support": metric_paths["network_support"],
            **cached,
            "subject_effects_excel": tables[_PEAK_GFP_GLOBAL_SUBJECT_STEM],
            "group_effects_excel": tables[_PEAK_GFP_GLOBAL_GROUP_STEM],
        }
    gfp_peaks_df = read_dataframe(eeg_outputs["gfp_peaks"])
    gfp_trace_df = read_dataframe(eeg_outputs["gfp_trace"])
    global_trace_df = read_dataframe(metric_paths["global_trace"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    for offset, patient_id in enumerate(cohort["patient_id"].astype(str)):
        aligned = align_gfp_and_global_traces(
            gfp_trace_df[gfp_trace_df["patient_id"] == patient_id],
            global_trace_df[global_trace_df["patient_id"] == patient_id],
            patient_id=patient_id,
        )
        sample_period = sample_period_from_times(aligned["time_sec"].to_numpy(dtype=float)) if not aligned.empty else 0.0
        subject_frames.append(
            compute_subject_peak_centered_global_trajectory(
                gfp_peaks_df[gfp_peaks_df["patient_id"] == patient_id],
                aligned,
                patient_id=patient_id,
                window_sec=window_sec,
                sample_period_sec=sample_period,
                n_surrogates=surrogates,
                seed=cfg.random_seed + offset,
            )
        )
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    if not subject_effects.empty:
        subject_effects["global_metric_label"] = subject_effects.apply(
            lambda row: global_metric_label(str(row.metric_definition), str(row.weighting_strategy)),
            axis=1,
        )
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_scalar_statistics(
        subject_effects,
        group_keys=["metric_definition", "weighting_strategy", "network_scope", "offset_ms"],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    if not group_effects.empty:
        group_effects["global_metric_label"] = group_effects.apply(
            lambda row: global_metric_label(str(row.metric_definition), str(row.weighting_strategy)),
            axis=1,
        )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            _PEAK_GFP_GLOBAL_SUBJECT_STEM: subject_effects,
            _PEAK_GFP_GLOBAL_GROUP_STEM: group_effects,
        },
        branch=branch,
    )
    return {
        "gfp_trace": eeg_outputs["gfp_trace"],
        "gfp_peaks": eeg_outputs["gfp_peaks"],
        "global_trace": metric_paths["global_trace"],
        "network_support": metric_paths["network_support"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables[_PEAK_GFP_GLOBAL_SUBJECT_STEM],
        "group_effects_excel": tables[_PEAK_GFP_GLOBAL_GROUP_STEM],
    }


def run_exploratory_gfp_controlled_microstate_stage(
    cfg: AnalysisConfig,
    *,
    global_metric: str = DEFAULT_GFP_GLOBAL_METRIC,
    global_weighting: str = DEFAULT_GFP_GLOBAL_WEIGHTING,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_global_metric_definition(global_metric)
    normalized_weighting = normalize_global_weighting_strategy(global_weighting)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    _metric_branch, metric_paths = _ensure_seeg_global_metric_artifacts(
        cfg,
        metric_definition=normalized_metric,
        weighting_strategy=normalized_weighting,
    )
    branch = _exploratory_branch(
        cfg,
        "gfp-controlled-microstate",
        params={
            "metric_definition": normalized_metric,
            "weighting_strategy": normalized_weighting,
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_profiles": cfg.cache_path("coupling", _GFP_CONTROLLED_MICROSTATE_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_omnibus": cfg.cache_path("stats", _GFP_CONTROLLED_MICROSTATE_GROUP_OMNIBUS_STEM, ext="parquet", branch=branch),
        "group_posthoc": cfg.cache_path("stats", _GFP_CONTROLLED_MICROSTATE_GROUP_POSTHOC_STEM, ext="parquet", branch=branch),
    }
    eeg_outputs = run_eeg_states_stage(cfg)
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _GFP_CONTROLLED_MICROSTATE_SUBJECT_STEM: cached["subject_profiles"],
                _GFP_CONTROLLED_MICROSTATE_GROUP_OMNIBUS_STEM: cached["group_omnibus"],
                _GFP_CONTROLLED_MICROSTATE_GROUP_POSTHOC_STEM: cached["group_posthoc"],
            },
            branch=branch,
        )
        return {
            "gfp_trace": eeg_outputs["gfp_trace"],
            "global_trace": metric_paths["global_trace"],
            "network_support": metric_paths["network_support"],
            **cached,
            "subject_profiles_excel": tables[_GFP_CONTROLLED_MICROSTATE_SUBJECT_STEM],
            "group_omnibus_excel": tables[_GFP_CONTROLLED_MICROSTATE_GROUP_OMNIBUS_STEM],
            "group_posthoc_excel": tables[_GFP_CONTROLLED_MICROSTATE_GROUP_POSTHOC_STEM],
        }
    label_df = read_dataframe(eeg_outputs["labels"])
    gfp_trace_df = read_dataframe(eeg_outputs["gfp_trace"])
    global_trace_df = read_dataframe(metric_paths["global_trace"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    for patient_id in cohort["patient_id"].astype(str):
        aligned = align_microstate_to_gfp_and_global(
            label_df[label_df["patient_id"] == patient_id],
            gfp_trace_df[gfp_trace_df["patient_id"] == patient_id],
            global_trace_df[global_trace_df["patient_id"] == patient_id],
            patient_id=patient_id,
        )
        subject_frames.append(
            compute_subject_gfp_controlled_microstate_profiles(
                aligned,
                patient_id=patient_id,
            )
        )
    subject_profiles = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    subject_path = write_dataframe(subject_profiles, cached["subject_profiles"])
    group_omnibus = run_group_profile_omnibus_statistics(
        subject_profiles,
        group_keys=["global_metric_label", "metric_definition", "weighting_strategy", "network_scope"],
        value_column="adjusted_global_metric",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_omnibus_path = write_dataframe(group_omnibus, cached["group_omnibus"])
    group_posthoc = run_group_profile_posthoc_statistics(
        subject_profiles,
        group_keys=["global_metric_label", "metric_definition", "weighting_strategy", "network_scope"],
        value_column="adjusted_global_metric",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_posthoc_path = write_dataframe(group_posthoc, cached["group_posthoc"])
    tables = _write_table_reports(
        cfg,
        {
            _GFP_CONTROLLED_MICROSTATE_SUBJECT_STEM: subject_profiles,
            _GFP_CONTROLLED_MICROSTATE_GROUP_OMNIBUS_STEM: group_omnibus,
            _GFP_CONTROLLED_MICROSTATE_GROUP_POSTHOC_STEM: group_posthoc,
        },
        branch=branch,
    )
    return {
        "gfp_trace": eeg_outputs["gfp_trace"],
        "global_trace": metric_paths["global_trace"],
        "network_support": metric_paths["network_support"],
        "subject_profiles": subject_path,
        "group_omnibus": group_omnibus_path,
        "group_posthoc": group_posthoc_path,
        "subject_profiles_excel": tables[_GFP_CONTROLLED_MICROSTATE_SUBJECT_STEM],
        "group_omnibus_excel": tables[_GFP_CONTROLLED_MICROSTATE_GROUP_OMNIBUS_STEM],
        "group_posthoc_excel": tables[_GFP_CONTROLLED_MICROSTATE_GROUP_POSTHOC_STEM],
    }


def run_exploratory_gfp_controlled_transition_stage(
    cfg: AnalysisConfig,
    *,
    global_metric: str = DEFAULT_GFP_GLOBAL_METRIC,
    global_weighting: str = DEFAULT_GFP_GLOBAL_WEIGHTING,
    transition_window_sec: float | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_global_metric_definition(global_metric)
    normalized_weighting = normalize_global_weighting_strategy(global_weighting)
    window_sec = _resolve_transition_window_sec(transition_window_sec, cfg)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    event_paths = _ensure_exploratory_event_tables(cfg)
    _metric_branch, metric_paths = _ensure_seeg_global_metric_artifacts(
        cfg,
        metric_definition=normalized_metric,
        weighting_strategy=normalized_weighting,
    )
    branch = _exploratory_branch(
        cfg,
        "gfp-controlled-transition",
        params={
            "metric_definition": normalized_metric,
            "weighting_strategy": normalized_weighting,
            "transition_window_sec": float(window_sec),
            "min_subjects": threshold,
        },
    )
    cached = {
        "subject_effects": cfg.cache_path("coupling", _GFP_CONTROLLED_TRANSITION_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_effects": cfg.cache_path("stats", _GFP_CONTROLLED_TRANSITION_GROUP_STEM, ext="parquet", branch=branch),
    }
    eeg_outputs = run_eeg_states_stage(cfg)
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _GFP_CONTROLLED_TRANSITION_SUBJECT_STEM: cached["subject_effects"],
                _GFP_CONTROLLED_TRANSITION_GROUP_STEM: cached["group_effects"],
            },
            branch=branch,
        )
        return {
            "transitions": event_paths["transitions"],
            "gfp_trace": eeg_outputs["gfp_trace"],
            "global_trace": metric_paths["global_trace"],
            "network_support": metric_paths["network_support"],
            **cached,
            "subject_effects_excel": tables[_GFP_CONTROLLED_TRANSITION_SUBJECT_STEM],
            "group_effects_excel": tables[_GFP_CONTROLLED_TRANSITION_GROUP_STEM],
        }
    transition_df = read_dataframe(event_paths["transitions"])
    gfp_trace_df = read_dataframe(eeg_outputs["gfp_trace"])
    global_trace_df = read_dataframe(metric_paths["global_trace"])
    cohort = _eligible_rows(cfg)
    subject_frames: list[pd.DataFrame] = []
    for patient_id in cohort["patient_id"].astype(str):
        aligned = align_gfp_and_global_traces(
            gfp_trace_df[gfp_trace_df["patient_id"] == patient_id],
            global_trace_df[global_trace_df["patient_id"] == patient_id],
            patient_id=patient_id,
        )
        sample_period = sample_period_from_times(aligned["time_sec"].to_numpy(dtype=float)) if not aligned.empty else 0.0
        subject_frames.append(
            compute_subject_gfp_controlled_transition_effects(
                transition_df[transition_df["patient_id"] == patient_id],
                aligned,
                patient_id=patient_id,
                window_sec=window_sec,
                sample_period_sec=sample_period,
            )
        )
    subject_effects = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_scalar_statistics(
        subject_effects,
        group_keys=["global_metric_label", "metric_definition", "weighting_strategy", "network_scope", "from_state", "to_state"],
        value_column="effect_mean_diff",
        seed=cfg.random_seed,
        min_subjects=threshold,
    )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    tables = _write_table_reports(
        cfg,
        {
            _GFP_CONTROLLED_TRANSITION_SUBJECT_STEM: subject_effects,
            _GFP_CONTROLLED_TRANSITION_GROUP_STEM: group_effects,
        },
        branch=branch,
    )
    return {
        "transitions": event_paths["transitions"],
        "gfp_trace": eeg_outputs["gfp_trace"],
        "global_trace": metric_paths["global_trace"],
        "network_support": metric_paths["network_support"],
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": tables[_GFP_CONTROLLED_TRANSITION_SUBJECT_STEM],
        "group_effects_excel": tables[_GFP_CONTROLLED_TRANSITION_GROUP_STEM],
    }


def run_exploratory_coupling_stage(
    cfg: AnalysisConfig,
    *,
    analysis: str = "all",
    method: str = "all",
    field_peak_metric: str = DEFAULT_FIELD_STATE_PEAK_METRIC,
    field_normalization: str = DEFAULT_FIELD_STATE_NORMALIZATION,
    field_state_count: int | None = None,
    field_min_duration_ms: int | None = None,
    field_archetype_space: str = YEO17_PARCELLATION_NAME,
    global_metric: str = DEFAULT_GFP_GLOBAL_METRIC,
    global_weighting: str = DEFAULT_GFP_GLOBAL_WEIGHTING,
    event_window_sec: float = 1.0,
    window_sec: float = 10.0,
    peak_window_sec: float | None = None,
    transition_window_sec: float | None = None,
    direct_backend: str = "pca-kmeans",
    direct_state_count: int | None = None,
    direct_components: int | None = None,
    field_surrogates: int | None = None,
    fine_lag_window_ms: int | None = None,
    max_lag_ms: int | None = None,
    lag_step_ms: int | None = None,
    direct_surrogates: int | None = None,
    global_surrogates: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    selected = str(analysis).strip().lower()
    if selected == "all":
        outputs: dict[str, Path] = {}
        for item in _EXPLORATORY_ANALYSES:
            kwargs = {
                "event_window_sec": event_window_sec,
                "window_sec": window_sec,
                "peak_window_sec": peak_window_sec,
                "transition_window_sec": transition_window_sec,
                "direct_backend": direct_backend,
                "direct_state_count": direct_state_count,
                "direct_components": direct_components,
                "field_peak_metric": field_peak_metric,
                "field_normalization": field_normalization,
                "field_state_count": field_state_count,
                "field_min_duration_ms": field_min_duration_ms,
                "field_archetype_space": field_archetype_space,
                "field_surrogates": field_surrogates,
                "fine_lag_window_ms": fine_lag_window_ms,
                "max_lag_ms": max_lag_ms,
                "lag_step_ms": lag_step_ms,
                "direct_surrogates": direct_surrogates,
                "global_metric": global_metric,
                "global_weighting": global_weighting,
                "global_surrogates": global_surrogates,
                "min_subjects": min_subjects,
                "method": method,
            }
            stage_outputs = run_exploratory_coupling_stage(cfg, analysis=item, **kwargs)
            prefix = cfg.branch_name(item)
            for key, value in stage_outputs.items():
                outputs[f"{prefix}_{key}"] = value
        return outputs
    gfp_analyses = {
        "gfp-global-coupling",
        "lagged-gfp-global-coupling",
        "peak-gfp-global-coupling",
        "gfp-controlled-microstate",
        "gfp-controlled-transition",
    }
    if selected in gfp_analyses and (global_metric == "all" or global_weighting == "all"):
        outputs: dict[str, Path] = {}
        metrics = SUPPORTED_GFP_GLOBAL_METRICS if global_metric == "all" else (normalize_global_metric_definition(global_metric),)
        weightings = (
            SUPPORTED_GFP_GLOBAL_WEIGHTINGS
            if global_weighting == "all"
            else (normalize_global_weighting_strategy(global_weighting),)
        )
        for metric_definition in metrics:
            for weighting_strategy in weightings:
                stage_outputs = run_exploratory_coupling_stage(
                    cfg,
                    analysis=selected,
                    method=method,
                    global_metric=metric_definition,
                    global_weighting=weighting_strategy,
                    event_window_sec=event_window_sec,
                    window_sec=window_sec,
                    peak_window_sec=peak_window_sec,
                    transition_window_sec=transition_window_sec,
                    direct_backend=direct_backend,
                    direct_state_count=direct_state_count,
                    direct_components=direct_components,
                    field_peak_metric=field_peak_metric,
                    field_normalization=field_normalization,
                    field_state_count=field_state_count,
                    field_min_duration_ms=field_min_duration_ms,
                    field_archetype_space=field_archetype_space,
                    field_surrogates=field_surrogates,
                    fine_lag_window_ms=fine_lag_window_ms,
                    max_lag_ms=max_lag_ms,
                    lag_step_ms=lag_step_ms,
                    direct_surrogates=direct_surrogates,
                    global_surrogates=global_surrogates,
                    min_subjects=min_subjects,
                )
                combo_prefix = cfg.branch_name(f"{metric_definition}_{weighting_strategy}")
                for key, value in stage_outputs.items():
                    outputs[f"{combo_prefix}_{key}"] = value
        return outputs
    if selected == "event-activity":
        return run_exploratory_event_activity_stage(cfg, event_window_sec=event_window_sec, min_subjects=min_subjects)
    if selected == "event-connectivity":
        return run_exploratory_event_connectivity_stage(
            cfg,
            method=method,
            event_window_sec=event_window_sec,
            min_subjects=min_subjects,
        )
    if selected == "windowed-coupling":
        return run_exploratory_windowed_coupling_stage(cfg, window_sec=window_sec, min_subjects=min_subjects)
    if selected == "transition-coupling":
        return run_exploratory_transition_coupling_stage(cfg, event_window_sec=event_window_sec, min_subjects=min_subjects)
    if selected == "direct-state-coupling":
        return run_exploratory_direct_state_coupling_stage(
            cfg,
            direct_backend=direct_backend,
            direct_state_count=direct_state_count,
            direct_components=direct_components,
            direct_surrogates=direct_surrogates,
            min_subjects=min_subjects,
        )
    if selected == "lagged-state-coupling":
        return run_exploratory_lagged_state_coupling_stage(
            cfg,
            direct_backend=direct_backend,
            direct_state_count=direct_state_count,
            direct_components=direct_components,
            max_lag_ms=max_lag_ms,
            lag_step_ms=lag_step_ms,
            direct_surrogates=direct_surrogates,
            min_subjects=min_subjects,
        )
    if selected == "transition-state-coupling":
        return run_exploratory_transition_state_coupling_stage(
            cfg,
            direct_backend=direct_backend,
            direct_state_count=direct_state_count,
            direct_components=direct_components,
            transition_window_sec=transition_window_sec,
            direct_surrogates=direct_surrogates,
            min_subjects=min_subjects,
        )
    if selected == "field-state-coupling":
        return run_exploratory_field_state_coupling_stage(
            cfg,
            field_peak_metric=field_peak_metric,
            field_normalization=field_normalization,
            field_state_count=field_state_count,
            field_min_duration_ms=field_min_duration_ms,
            field_surrogates=field_surrogates,
            min_subjects=min_subjects,
        )
    if selected == "lagged-field-state-coupling":
        return run_exploratory_lagged_field_state_coupling_stage(
            cfg,
            field_peak_metric=field_peak_metric,
            field_normalization=field_normalization,
            field_state_count=field_state_count,
            field_min_duration_ms=field_min_duration_ms,
            max_lag_ms=max_lag_ms,
            lag_step_ms=lag_step_ms,
            field_surrogates=field_surrogates,
            min_subjects=min_subjects,
        )
    if selected == "fine-lag-field-state-coupling":
        return run_exploratory_fine_lag_field_state_coupling_stage(
            cfg,
            field_peak_metric=field_peak_metric,
            field_normalization=field_normalization,
            field_state_count=field_state_count,
            field_min_duration_ms=field_min_duration_ms,
            fine_lag_window_ms=fine_lag_window_ms,
            field_surrogates=field_surrogates,
            min_subjects=min_subjects,
        )
    if selected == "transition-field-state-coupling":
        return run_exploratory_transition_field_state_coupling_stage(
            cfg,
            field_peak_metric=field_peak_metric,
            field_normalization=field_normalization,
            field_state_count=field_state_count,
            field_min_duration_ms=field_min_duration_ms,
            transition_window_sec=transition_window_sec,
            field_surrogates=field_surrogates,
            min_subjects=min_subjects,
        )
    if selected == "field-state-to-eeg-switching":
        return run_exploratory_field_state_to_eeg_switching_stage(
            cfg,
            field_peak_metric=field_peak_metric,
            field_normalization=field_normalization,
            field_state_count=field_state_count,
            field_min_duration_ms=field_min_duration_ms,
            transition_window_sec=transition_window_sec,
            field_surrogates=field_surrogates,
            min_subjects=min_subjects,
        )
    if selected == "gfp-controlled-field-state-switching":
        return run_exploratory_gfp_controlled_field_state_switching_stage(
            cfg,
            field_peak_metric=field_peak_metric,
            field_normalization=field_normalization,
            field_state_count=field_state_count,
            field_min_duration_ms=field_min_duration_ms,
            transition_window_sec=transition_window_sec,
            min_subjects=min_subjects,
        )
    if selected == "field-state-archetypes":
        return run_exploratory_field_state_archetypes_stage(
            cfg,
            field_peak_metric=field_peak_metric,
            field_normalization=field_normalization,
            field_state_count=field_state_count,
            field_min_duration_ms=field_min_duration_ms,
            field_archetype_space=field_archetype_space,
            min_subjects=min_subjects,
        )
    if selected == "archetype-conditioned-eeg-topography":
        return run_exploratory_archetype_conditioned_eeg_topography_stage(
            cfg,
            field_peak_metric=field_peak_metric,
            field_normalization=field_normalization,
            field_state_count=field_state_count,
            field_min_duration_ms=field_min_duration_ms,
            field_archetype_space=field_archetype_space,
            fine_lag_window_ms=fine_lag_window_ms,
            transition_window_sec=transition_window_sec,
            field_surrogates=field_surrogates,
            min_subjects=min_subjects,
        )
    if selected == "gfp-controlled-field-state-to-eeg-switching":
        return run_exploratory_gfp_controlled_field_state_to_eeg_switching_stage(
            cfg,
            field_peak_metric=field_peak_metric,
            field_normalization=field_normalization,
            field_state_count=field_state_count,
            field_min_duration_ms=field_min_duration_ms,
            transition_window_sec=transition_window_sec,
            min_subjects=min_subjects,
        )
    if selected == "gfp-global-coupling":
        return run_exploratory_gfp_global_coupling_stage(
            cfg,
            global_metric=global_metric,
            global_weighting=global_weighting,
            global_surrogates=global_surrogates,
            min_subjects=min_subjects,
        )
    if selected == "lagged-gfp-global-coupling":
        return run_exploratory_lagged_gfp_global_coupling_stage(
            cfg,
            global_metric=global_metric,
            global_weighting=global_weighting,
            max_lag_ms=max_lag_ms,
            lag_step_ms=lag_step_ms,
            global_surrogates=global_surrogates,
            min_subjects=min_subjects,
        )
    if selected == "peak-gfp-global-coupling":
        return run_exploratory_peak_gfp_global_coupling_stage(
            cfg,
            global_metric=global_metric,
            global_weighting=global_weighting,
            peak_window_sec=peak_window_sec,
            global_surrogates=global_surrogates,
            min_subjects=min_subjects,
        )
    if selected == "gfp-controlled-microstate":
        return run_exploratory_gfp_controlled_microstate_stage(
            cfg,
            global_metric=global_metric,
            global_weighting=global_weighting,
            min_subjects=min_subjects,
        )
    if selected == "gfp-controlled-transition":
        return run_exploratory_gfp_controlled_transition_stage(
            cfg,
            global_metric=global_metric,
            global_weighting=global_weighting,
            transition_window_sec=transition_window_sec,
            min_subjects=min_subjects,
        )
    supported = ", ".join(["all", *_EXPLORATORY_ANALYSES])
    raise ValueError(f"Unsupported exploratory analysis '{analysis}'. Expected one of: {supported}.")


def run_band_limited_connectivity_branch(cfg: AnalysisConfig, *, method: str = "corr") -> dict[str, Path]:
    cfg.ensure_cache_directories()
    if method == "all":
        outputs: dict[str, Path] = {}
        for item in ("corr", "plv", "wpli"):
            for key, value in run_band_limited_connectivity_branch(cfg, method=item).items():
                outputs[f"{item}_{key}"] = value
        return outputs
    normalized_method = normalize_connectivity_method(method)
    analysis_branch = connectivity_analysis_branch(normalized_method)
    cached = {
        "aligned": cfg.cache_path("coupling", "aligned_connectivity", ext="parquet", branch=analysis_branch),
        "subject_profiles": cfg.cache_path("coupling", _CONNECTIVITY_SUBJECT_PROFILE_STEM, ext="parquet", branch=analysis_branch),
        "group_omnibus": cfg.cache_path("stats", _CONNECTIVITY_GROUP_OMNIBUS_STEM, ext="parquet", branch=analysis_branch),
        "group_posthoc": cfg.cache_path("stats", _CONNECTIVITY_GROUP_POSTHOC_STEM, ext="parquet", branch=analysis_branch),
    }
    if _all_exist(cached):
        table_reports = _write_table_reports_from_paths(
            cfg,
            {
                _CONNECTIVITY_SUBJECT_PROFILE_STEM: cached["subject_profiles"],
                _CONNECTIVITY_GROUP_OMNIBUS_STEM: cached["group_omnibus"],
                _CONNECTIVITY_GROUP_POSTHOC_STEM: cached["group_posthoc"],
            },
            branch=analysis_branch,
        )
        return {
            **cached,
            "subject_profiles_excel": table_reports[_CONNECTIVITY_SUBJECT_PROFILE_STEM],
            "group_omnibus_excel": table_reports[_CONNECTIVITY_GROUP_OMNIBUS_STEM],
            "group_posthoc_excel": table_reports[_CONNECTIVITY_GROUP_POSTHOC_STEM],
        }
    eeg_outputs = run_eeg_states_stage(cfg)
    _ = run_seeg_regions_stage(cfg)
    cohort = _eligible_rows(cfg)
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    aligned_frames: list[pd.DataFrame] = []
    for row in cohort.to_dict(orient="records"):
        patient_id = str(row["patient_id"])
        label_df = eeg_labels[eeg_labels["patient_id"] == patient_id]
        region_path = cfg.cache_path("seeg", _SEEG_REGION_BAND_STEM, ext="parquet", branch=_BAND_BRANCH, patient_id=patient_id)
        region_df = read_dataframe(region_path)
        aligned_frames.append(align_region_timeseries_to_labels(label_df, region_df, patient_id=patient_id))
    aligned_df = pd.concat(aligned_frames, ignore_index=True) if aligned_frames else pd.DataFrame()
    aligned_path = write_dataframe(aligned_df, cached["aligned"])
    min_samples = max(8, int(round(cfg.seeg_resample_hz * 0.25)))
    subject_profiles = compute_subject_microstate_connectivity_profiles(
        aligned_df,
        min_samples=min_samples,
        method=normalized_method,
    )
    subject_path = write_dataframe(subject_profiles, cached["subject_profiles"])
    group_omnibus = run_group_profile_omnibus_statistics(
        subject_profiles,
        group_keys=["method", "region_a", "region_b"],
        value_column="state_connectivity",
        seed=cfg.random_seed,
        min_subjects=cfg.min_group_subjects,
    )
    group_omnibus_path = write_dataframe(group_omnibus, cached["group_omnibus"])
    group_posthoc = run_group_profile_posthoc_statistics(
        subject_profiles,
        group_keys=["method", "region_a", "region_b"],
        value_column="state_connectivity",
        seed=cfg.random_seed,
        min_subjects=cfg.min_group_subjects,
    )
    group_posthoc_path = write_dataframe(group_posthoc, cached["group_posthoc"])
    table_reports = _write_table_reports(
        cfg,
        {
            _CONNECTIVITY_SUBJECT_PROFILE_STEM: subject_profiles,
            _CONNECTIVITY_GROUP_OMNIBUS_STEM: group_omnibus,
            _CONNECTIVITY_GROUP_POSTHOC_STEM: group_posthoc,
        },
        branch=analysis_branch,
    )
    return {
        "aligned": aligned_path,
        "subject_profiles": subject_path,
        "group_omnibus": group_omnibus_path,
        "group_posthoc": group_posthoc_path,
        "subject_profiles_excel": table_reports[_CONNECTIVITY_SUBJECT_PROFILE_STEM],
        "group_omnibus_excel": table_reports[_CONNECTIVITY_GROUP_OMNIBUS_STEM],
        "group_posthoc_excel": table_reports[_CONNECTIVITY_GROUP_POSTHOC_STEM],
    }


def run_connectivity_effects_stage(cfg: AnalysisConfig, *, method: str = "all") -> dict[str, Path]:
    return run_band_limited_connectivity_branch(cfg, method=method)


def render_reports(cfg: AnalysisConfig) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    outputs: dict[str, Path] = {}
    state_label = cfg.analysis_state.replace("_", " ")
    parcel_label = f"{cfg.parcellation_display_name} {cfg.parcellation_unit_label}"
    coverage_path = cfg.cache_path("seeg", _SEEG_REGION_COVERAGE_STEM, ext="parquet", branch=_BAND_BRANCH)
    if coverage_path.exists():
        coverage_df = read_dataframe(coverage_path)
        outputs["coverage"] = plot_coverage_summary(
            coverage_df,
            cfg.report_path("region_coverage", ext="png", branch=_BAND_BRANCH),
            title=f"{state_label} {parcel_label} coverage",
        )
    model_path = cfg.cache_path("eeg", "group_microstate_model", ext="fif", branch=_BAND_BRANCH)
    if model_path.exists():
        outputs["microstates"] = plot_microstate_templates(
            load_microstate_model(model_path),
            cfg.report_path("microstate_templates", ext="png", branch=_BAND_BRANCH),
        )
    activity_omnibus_path = cfg.cache_path("stats", _ACTIVITY_GROUP_OMNIBUS_STEM, ext="parquet", branch=_ACTIVITY_BRANCH)
    if activity_omnibus_path.exists():
        outputs["activity_omnibus_heatmap"] = plot_group_metric_heatmap(
            read_dataframe(activity_omnibus_path),
            cfg.report_path("activity_omnibus", ext="png", branch=_ACTIVITY_BRANCH),
            title=f"{state_label} band-limited {parcel_label} activity omnibus statistics",
            value_column="statistic",
            unit_column="region",
        )
    activity_posthoc_path = cfg.cache_path("stats", _ACTIVITY_GROUP_POSTHOC_STEM, ext="parquet", branch=_ACTIVITY_BRANCH)
    if activity_posthoc_path.exists():
        outputs["activity_posthoc_heatmap"] = plot_group_metric_heatmap(
            read_dataframe(activity_posthoc_path),
            cfg.report_path("activity_posthoc", ext="png", branch=_ACTIVITY_BRANCH),
            title=f"{state_label} band-limited {parcel_label} activity post-hoc effects",
            value_column="mean_effect",
            unit_column="region",
            row_column="contrast",
        )
    activity_subject_path = cfg.cache_path("coupling", _ACTIVITY_SUBJECT_PROFILE_STEM, ext="parquet", branch=_ACTIVITY_BRANCH)
    if activity_subject_path.exists() and activity_omnibus_path.exists() and activity_posthoc_path.exists():
        table_reports = _write_table_reports_from_paths(
            cfg,
            {
                _ACTIVITY_SUBJECT_PROFILE_STEM: activity_subject_path,
                _ACTIVITY_GROUP_OMNIBUS_STEM: activity_omnibus_path,
                _ACTIVITY_GROUP_POSTHOC_STEM: activity_posthoc_path,
            },
            branch=_ACTIVITY_BRANCH,
        )
        outputs["activity_subject_profiles_excel"] = table_reports[_ACTIVITY_SUBJECT_PROFILE_STEM]
        outputs["activity_group_omnibus_excel"] = table_reports[_ACTIVITY_GROUP_OMNIBUS_STEM]
        outputs["activity_group_posthoc_excel"] = table_reports[_ACTIVITY_GROUP_POSTHOC_STEM]
    for method in ("corr", "plv", "wpli"):
        branch = connectivity_analysis_branch(method)
        connectivity_omnibus_path = cfg.cache_path("stats", _CONNECTIVITY_GROUP_OMNIBUS_STEM, ext="parquet", branch=branch)
        if connectivity_omnibus_path.exists():
            outputs[f"band_connectivity_{method}_omnibus"] = plot_connectivity_omnibus_matrix(
                read_dataframe(connectivity_omnibus_path),
                cfg.report_path(f"band_connectivity_omnibus_{method}", ext="png", branch=branch),
                title=f"{state_label} {parcel_label} band-limited connectivity omnibus statistics ({method.upper()})",
            )
        connectivity_posthoc_path = cfg.cache_path("stats", _CONNECTIVITY_GROUP_POSTHOC_STEM, ext="parquet", branch=branch)
        if connectivity_posthoc_path.exists():
            outputs[f"band_connectivity_{method}_posthoc"] = plot_connectivity_posthoc_matrices(
                read_dataframe(connectivity_posthoc_path),
                cfg.report_path(f"band_connectivity_posthoc_{method}", ext="png", branch=branch),
                title=f"{state_label} {parcel_label} band-limited connectivity post-hoc effects ({method.upper()})",
            )
        subject_path = cfg.cache_path("coupling", _CONNECTIVITY_SUBJECT_PROFILE_STEM, ext="parquet", branch=branch)
        if subject_path.exists() and connectivity_omnibus_path.exists() and connectivity_posthoc_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    _CONNECTIVITY_SUBJECT_PROFILE_STEM: subject_path,
                    _CONNECTIVITY_GROUP_OMNIBUS_STEM: connectivity_omnibus_path,
                    _CONNECTIVITY_GROUP_POSTHOC_STEM: connectivity_posthoc_path,
                },
                branch=branch,
            )
            outputs[f"band_connectivity_{method}_subject_profiles_excel"] = table_reports[_CONNECTIVITY_SUBJECT_PROFILE_STEM]
            outputs[f"band_connectivity_{method}_group_omnibus_excel"] = table_reports[_CONNECTIVITY_GROUP_OMNIBUS_STEM]
            outputs[f"band_connectivity_{method}_group_posthoc_excel"] = table_reports[_CONNECTIVITY_GROUP_POSTHOC_STEM]
    for branch, group_path in _discover_branch_paths(cfg, "stats", "group_event_locked_activity", ext="parquet"):
        outputs[f"{branch}_event_activity_heatmap"] = plot_group_effects_heatmap(
            read_dataframe(group_path),
            cfg.report_path("exploratory_event_activity", ext="png", branch=branch),
            title=f"Exploratory {state_label} EEG event-locked {parcel_label} activity effects",
        )
        subject_path = cfg.cache_path("coupling", "subject_event_locked_activity", ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    "subject_event_locked_activity": subject_path,
                    "group_event_locked_activity": group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_event_activity_subject_excel"] = table_reports["subject_event_locked_activity"]
            outputs[f"{branch}_event_activity_group_excel"] = table_reports["group_event_locked_activity"]
    for branch, group_path in _discover_branch_paths(cfg, "stats", "group_event_locked_connectivity", ext="parquet"):
        group_df = read_dataframe(group_path)
        method = str(group_df["method"].iloc[0]) if not group_df.empty and "method" in group_df.columns else "corr"
        outputs[f"{branch}_event_connectivity_heatmap"] = plot_connectivity_effect_matrices(
            group_df,
            cfg.report_path("exploratory_event_connectivity", ext="png", branch=branch),
            title=f"Exploratory {state_label} EEG event-locked {parcel_label} connectivity effects ({method.upper()})",
        )
        subject_path = cfg.cache_path("coupling", "subject_event_locked_connectivity", ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    "subject_event_locked_connectivity": subject_path,
                    "group_event_locked_connectivity": group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_event_connectivity_subject_excel"] = table_reports["subject_event_locked_connectivity"]
            outputs[f"{branch}_event_connectivity_group_excel"] = table_reports["group_event_locked_connectivity"]
    for branch, group_path in _discover_branch_paths(cfg, "stats", "group_windowed_coupling", ext="parquet"):
        outputs[f"{branch}_windowed_coupling_heatmap"] = plot_group_effects_heatmap(
            read_dataframe(group_path),
            cfg.report_path("exploratory_windowed_coupling", ext="png", branch=branch),
            title=f"Exploratory {state_label} windowed EEG occupancy and {parcel_label} coupling effects",
        )
        subject_path = cfg.cache_path("coupling", "subject_windowed_coupling", ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    "subject_windowed_coupling": subject_path,
                    "group_windowed_coupling": group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_windowed_coupling_subject_excel"] = table_reports["subject_windowed_coupling"]
            outputs[f"{branch}_windowed_coupling_group_excel"] = table_reports["group_windowed_coupling"]
    for branch, group_path in _discover_branch_paths(cfg, "stats", "group_transition_coupling", ext="parquet"):
        outputs[f"{branch}_transition_coupling_heatmap"] = plot_transition_effect_heatmap(
            read_dataframe(group_path),
            cfg.report_path("exploratory_transition_coupling", ext="png", branch=branch),
            title=f"Exploratory {state_label} EEG transition-locked {parcel_label} coupling effects",
        )
        subject_path = cfg.cache_path("coupling", "subject_transition_coupling", ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    "subject_transition_coupling": subject_path,
                    "group_transition_coupling": group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_transition_coupling_subject_excel"] = table_reports["subject_transition_coupling"]
            outputs[f"{branch}_transition_coupling_group_excel"] = table_reports["group_transition_coupling"]
    for branch, template_path in _discover_branch_paths(cfg, "coupling", _FIELD_STATE_TEMPLATES_STEM, ext="parquet"):
        template_df = read_dataframe(template_path)
        outputs[f"{branch}_field_template_panels"] = plot_subject_template_panels(
            template_df,
            cfg.report_path("exploratory_field_state_templates", ext="png", branch=branch),
            title=f"Exploratory {state_label} subject-level SEEG field templates",
        )
        profile_path = cfg.cache_path("coupling", _FIELD_STATE_PROFILES_STEM, ext="parquet", branch=branch)
        transition_profile_path = cfg.cache_path("coupling", _FIELD_STATE_TRANSITION_PROFILES_STEM, ext="parquet", branch=branch)
        if profile_path.exists():
            profile_df = read_dataframe(profile_path)
            outputs[f"{branch}_field_profile_heatmap"] = plot_subject_state_profile_heatmap(
                profile_df,
                cfg.report_path("exploratory_field_state_profiles", ext="png", branch=branch),
                title=f"Exploratory {state_label} SEEG field-state occupancy",
                state_column="field_state",
                value_column="occupancy",
            )
        if transition_profile_path.exists():
            transition_profile_df = read_dataframe(transition_profile_path)
            transition_group = (
                transition_profile_df.groupby(["from_state", "to_state"], as_index=False)
                .agg(mean_effect=("transition_probability", "mean"))
                .reset_index(drop=True)
            )
            outputs[f"{branch}_field_transition_matrix"] = plot_state_transition_matrix(
                transition_group,
                cfg.report_path("exploratory_field_state_transitions", ext="png", branch=branch),
                title=f"Exploratory {state_label} mean SEEG field-state transitions",
            )
        report_sources = {_FIELD_STATE_TEMPLATES_STEM: template_path}
        if profile_path.exists():
            report_sources[_FIELD_STATE_PROFILES_STEM] = profile_path
        if transition_profile_path.exists():
            report_sources[_FIELD_STATE_TRANSITION_PROFILES_STEM] = transition_profile_path
        table_reports = _write_table_reports_from_paths(cfg, report_sources, branch=branch)
        outputs[f"{branch}_field_templates_excel"] = table_reports[_FIELD_STATE_TEMPLATES_STEM]
        if _FIELD_STATE_PROFILES_STEM in table_reports:
            outputs[f"{branch}_field_profiles_excel"] = table_reports[_FIELD_STATE_PROFILES_STEM]
        if _FIELD_STATE_TRANSITION_PROFILES_STEM in table_reports:
            outputs[f"{branch}_field_transition_profiles_excel"] = table_reports[_FIELD_STATE_TRANSITION_PROFILES_STEM]
    for branch, archetype_path in _discover_branch_paths(cfg, "coupling", _FIELD_ARCHETYPE_TEMPLATES_STEM, ext="parquet"):
        archetype_df = read_dataframe(archetype_path)
        outputs[f"{branch}_field_archetype_panels"] = plot_subject_template_panels(
            archetype_df,
            cfg.report_path("exploratory_field_state_archetypes", ext="png", branch=branch),
            title=f"Exploratory {state_label} SEEG field-state archetypes",
            subject_column="patient_id",
            x_label="Common-space unit",
        )
        assignment_path = cfg.cache_path("coupling", _FIELD_ARCHETYPE_ASSIGNMENTS_STEM, ext="parquet", branch=branch)
        support_path = cfg.cache_path("stats", _FIELD_ARCHETYPE_SUPPORT_STEM, ext="parquet", branch=branch)
        projection_path = cfg.cache_path("coupling", _FIELD_ARCHETYPE_PROJECTIONS_STEM, ext="parquet", branch=branch)
        if assignment_path.exists():
            assignment_df = read_dataframe(assignment_path)
            outputs[f"{branch}_field_archetype_assignments"] = plot_subject_state_profile_heatmap(
                assignment_df,
                cfg.report_path("exploratory_field_state_archetype_assignments", ext="png", branch=branch),
                title=f"Exploratory {state_label} SEEG field-state archetype assignments",
                state_column="assigned_archetype",
                value_column="assignment_similarity",
            )
        report_sources = {_FIELD_ARCHETYPE_TEMPLATES_STEM: archetype_path}
        if projection_path.exists():
            report_sources[_FIELD_ARCHETYPE_PROJECTIONS_STEM] = projection_path
        if assignment_path.exists():
            report_sources[_FIELD_ARCHETYPE_ASSIGNMENTS_STEM] = assignment_path
        if support_path.exists():
            report_sources[_FIELD_ARCHETYPE_SUPPORT_STEM] = support_path
        table_reports = _write_table_reports_from_paths(cfg, report_sources, branch=branch)
        outputs[f"{branch}_field_archetype_templates_excel"] = table_reports[_FIELD_ARCHETYPE_TEMPLATES_STEM]
        if _FIELD_ARCHETYPE_PROJECTIONS_STEM in table_reports:
            outputs[f"{branch}_field_archetype_projections_excel"] = table_reports[_FIELD_ARCHETYPE_PROJECTIONS_STEM]
        if _FIELD_ARCHETYPE_ASSIGNMENTS_STEM in table_reports:
            outputs[f"{branch}_field_archetype_assignments_excel"] = table_reports[_FIELD_ARCHETYPE_ASSIGNMENTS_STEM]
        if _FIELD_ARCHETYPE_SUPPORT_STEM in table_reports:
            outputs[f"{branch}_field_archetype_support_excel"] = table_reports[_FIELD_ARCHETYPE_SUPPORT_STEM]
    for branch, group_map_path in _discover_branch_paths(cfg, "coupling", _ARCHETYPE_EEG_MAP_GROUP_STEM, ext="parquet"):
        outputs[f"{branch}_archetype_conditioned_eeg_topographies"] = plot_eeg_topography_panels(
            read_dataframe(group_map_path),
            cfg.report_path("exploratory_archetype_conditioned_eeg_topographies", ext="png", branch=branch),
            title=f"Exploratory {state_label} archetype-conditioned EEG topographies",
            state_column="assigned_archetype",
        )
        report_sources = {
            _ARCHETYPE_EEG_MAP_GROUP_STEM: group_map_path,
        }
        subject_map_path = cfg.cache_path("coupling", _ARCHETYPE_EEG_MAP_SUBJECT_STEM, ext="parquet", branch=branch)
        similarity_path = cfg.cache_path("stats", _ARCHETYPE_EEG_SIMILARITY_GROUP_STEM, ext="parquet", branch=branch)
        subject_similarity_path = cfg.cache_path(
            "coupling", _ARCHETYPE_EEG_SIMILARITY_SUBJECT_STEM, ext="parquet", branch=branch
        )
        preference_path = cfg.cache_path("stats", _ARCHETYPE_EEG_PREFERENCE_GROUP_STEM, ext="parquet", branch=branch)
        subject_preference_path = cfg.cache_path(
            "coupling", _ARCHETYPE_EEG_PREFERENCE_SUBJECT_STEM, ext="parquet", branch=branch
        )
        fine_lag_group_path = cfg.cache_path("stats", _ARCHETYPE_EEG_FINE_LAG_GROUP_STEM, ext="parquet", branch=branch)
        fine_lag_subject_path = cfg.cache_path(
            "coupling", _ARCHETYPE_EEG_FINE_LAG_SUBJECT_STEM, ext="parquet", branch=branch
        )
        fine_lag_peak_subject_path = cfg.cache_path(
            "coupling", _ARCHETYPE_EEG_FINE_LAG_PEAK_SUBJECT_STEM, ext="parquet", branch=branch
        )
        fine_lag_peak_group_path = cfg.cache_path(
            "stats", _ARCHETYPE_EEG_FINE_LAG_PEAK_GROUP_STEM, ext="parquet", branch=branch
        )
        transition_group_path = cfg.cache_path("stats", _ARCHETYPE_EEG_TRANSITION_GROUP_STEM, ext="parquet", branch=branch)
        transition_subject_path = cfg.cache_path(
            "coupling", _ARCHETYPE_EEG_TRANSITION_SUBJECT_STEM, ext="parquet", branch=branch
        )
        if similarity_path.exists():
            outputs[f"{branch}_archetype_template_similarity_heatmap"] = plot_group_metric_heatmap(
                read_dataframe(similarity_path),
                cfg.report_path("exploratory_archetype_eeg_template_similarity", ext="png", branch=branch),
                title=f"Exploratory {state_label} archetype-conditioned EEG template similarity",
                value_column="mean_similarity",
                unit_column="microstate",
                row_column="assigned_archetype",
            )
            report_sources[_ARCHETYPE_EEG_SIMILARITY_GROUP_STEM] = similarity_path
        if preference_path.exists():
            outputs[f"{branch}_archetype_state_preference_heatmap"] = plot_group_metric_heatmap(
                read_dataframe(preference_path),
                cfg.report_path("exploratory_archetype_eeg_state_preference", ext="png", branch=branch),
                title=f"Exploratory {state_label} archetype-conditioned EEG state preference",
                value_column="mean_effect",
                unit_column="microstate",
                row_column="assigned_archetype",
            )
            report_sources[_ARCHETYPE_EEG_PREFERENCE_GROUP_STEM] = preference_path
        if fine_lag_group_path.exists():
            outputs[f"{branch}_archetype_fine_lag_curve"] = plot_effect_curve(
                read_dataframe(fine_lag_group_path),
                cfg.report_path("exploratory_archetype_eeg_fine_lag_coupling", ext="png", branch=branch),
                title=f"Exploratory {state_label} archetype-to-EEG fine-lag coupling",
                x_column="lag_ms",
                x_label="Lag (ms)",
            )
            report_sources[_ARCHETYPE_EEG_FINE_LAG_GROUP_STEM] = fine_lag_group_path
        if fine_lag_peak_subject_path.exists():
            subject_peak_df = read_dataframe(fine_lag_peak_subject_path)
            if not subject_peak_df.empty:
                outputs[f"{branch}_archetype_fine_lag_peak_heatmap"] = plot_subject_state_profile_heatmap(
                    subject_peak_df.melt(
                        id_vars=["patient_id"],
                        value_vars=["peak_lag_ms", "peak_effect_mean_diff", "peak_width_ms"],
                        var_name="summary_kind",
                        value_name="summary_value",
                    ),
                    cfg.report_path("exploratory_archetype_eeg_fine_lag_peak_summary", ext="png", branch=branch),
                    title=f"Exploratory {state_label} archetype-conditioned EEG fine-lag peak summaries",
                    state_column="summary_kind",
                    value_column="summary_value",
                )
            report_sources[_ARCHETYPE_EEG_FINE_LAG_PEAK_SUBJECT_STEM] = fine_lag_peak_subject_path
        if fine_lag_peak_group_path.exists():
            report_sources[_ARCHETYPE_EEG_FINE_LAG_PEAK_GROUP_STEM] = fine_lag_peak_group_path
        if transition_group_path.exists():
            transition_group_df = read_dataframe(transition_group_path)
            plotted_transition_df = (
                transition_group_df[transition_group_df["response_kind"] == "any-switch"].copy()
                if "response_kind" in transition_group_df.columns
                else transition_group_df
            )
            outputs[f"{branch}_archetype_to_eeg_switching_matrix"] = plot_state_transition_matrix(
                plotted_transition_df,
                cfg.report_path("exploratory_archetype_to_eeg_switching", ext="png", branch=branch),
                title=f"Exploratory {state_label} archetype-led EEG switching",
                x_label="SEEG archetype to_state",
                y_label="SEEG archetype from_state",
            )
            report_sources[_ARCHETYPE_EEG_TRANSITION_GROUP_STEM] = transition_group_path
        if subject_map_path.exists():
            report_sources[_ARCHETYPE_EEG_MAP_SUBJECT_STEM] = subject_map_path
        if subject_similarity_path.exists():
            report_sources[_ARCHETYPE_EEG_SIMILARITY_SUBJECT_STEM] = subject_similarity_path
        if subject_preference_path.exists():
            report_sources[_ARCHETYPE_EEG_PREFERENCE_SUBJECT_STEM] = subject_preference_path
        if fine_lag_subject_path.exists():
            report_sources[_ARCHETYPE_EEG_FINE_LAG_SUBJECT_STEM] = fine_lag_subject_path
        if transition_subject_path.exists():
            report_sources[_ARCHETYPE_EEG_TRANSITION_SUBJECT_STEM] = transition_subject_path
        table_reports = _write_table_reports_from_paths(cfg, report_sources, branch=branch)
        if _ARCHETYPE_EEG_MAP_SUBJECT_STEM in table_reports:
            outputs[f"{branch}_archetype_conditioned_eeg_maps_subject_excel"] = table_reports[_ARCHETYPE_EEG_MAP_SUBJECT_STEM]
        outputs[f"{branch}_archetype_conditioned_eeg_maps_group_excel"] = table_reports[_ARCHETYPE_EEG_MAP_GROUP_STEM]
        if _ARCHETYPE_EEG_SIMILARITY_SUBJECT_STEM in table_reports:
            outputs[f"{branch}_archetype_template_similarity_subject_excel"] = table_reports[
                _ARCHETYPE_EEG_SIMILARITY_SUBJECT_STEM
            ]
        if _ARCHETYPE_EEG_SIMILARITY_GROUP_STEM in table_reports:
            outputs[f"{branch}_archetype_template_similarity_group_excel"] = table_reports[
                _ARCHETYPE_EEG_SIMILARITY_GROUP_STEM
            ]
        if _ARCHETYPE_EEG_PREFERENCE_SUBJECT_STEM in table_reports:
            outputs[f"{branch}_archetype_state_preference_subject_excel"] = table_reports[
                _ARCHETYPE_EEG_PREFERENCE_SUBJECT_STEM
            ]
        if _ARCHETYPE_EEG_PREFERENCE_GROUP_STEM in table_reports:
            outputs[f"{branch}_archetype_state_preference_group_excel"] = table_reports[
                _ARCHETYPE_EEG_PREFERENCE_GROUP_STEM
            ]
        if _ARCHETYPE_EEG_FINE_LAG_SUBJECT_STEM in table_reports:
            outputs[f"{branch}_archetype_fine_lag_subject_excel"] = table_reports[_ARCHETYPE_EEG_FINE_LAG_SUBJECT_STEM]
        if _ARCHETYPE_EEG_FINE_LAG_GROUP_STEM in table_reports:
            outputs[f"{branch}_archetype_fine_lag_group_excel"] = table_reports[_ARCHETYPE_EEG_FINE_LAG_GROUP_STEM]
        if _ARCHETYPE_EEG_FINE_LAG_PEAK_SUBJECT_STEM in table_reports:
            outputs[f"{branch}_archetype_fine_lag_peak_subject_excel"] = table_reports[
                _ARCHETYPE_EEG_FINE_LAG_PEAK_SUBJECT_STEM
            ]
        if _ARCHETYPE_EEG_FINE_LAG_PEAK_GROUP_STEM in table_reports:
            outputs[f"{branch}_archetype_fine_lag_peak_group_excel"] = table_reports[
                _ARCHETYPE_EEG_FINE_LAG_PEAK_GROUP_STEM
            ]
        if _ARCHETYPE_EEG_TRANSITION_SUBJECT_STEM in table_reports:
            outputs[f"{branch}_archetype_to_eeg_switching_subject_excel"] = table_reports[
                _ARCHETYPE_EEG_TRANSITION_SUBJECT_STEM
            ]
        if _ARCHETYPE_EEG_TRANSITION_GROUP_STEM in table_reports:
            outputs[f"{branch}_archetype_to_eeg_switching_group_excel"] = table_reports[
                _ARCHETYPE_EEG_TRANSITION_GROUP_STEM
            ]
    for branch, group_path in _discover_branch_paths(cfg, "stats", _DIRECT_STATE_GROUP_STEM, ext="parquet"):
        outputs[f"{branch}_direct_state_coupling_curve"] = plot_direct_coupling_lag_curve(
            read_dataframe(group_path),
            cfg.report_path("exploratory_direct_state_coupling", ext="png", branch=branch),
            title=f"Exploratory {state_label} direct EEG-SEEG state coupling",
        )
        subject_path = cfg.cache_path("coupling", _DIRECT_STATE_SUBJECT_STEM, ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    _DIRECT_STATE_SUBJECT_STEM: subject_path,
                    _DIRECT_STATE_GROUP_STEM: group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_direct_state_coupling_subject_excel"] = table_reports[_DIRECT_STATE_SUBJECT_STEM]
            outputs[f"{branch}_direct_state_coupling_group_excel"] = table_reports[_DIRECT_STATE_GROUP_STEM]
    for branch, group_path in _discover_branch_paths(cfg, "stats", _LAGGED_STATE_GROUP_STEM, ext="parquet"):
        outputs[f"{branch}_lagged_state_coupling_curve"] = plot_direct_coupling_lag_curve(
            read_dataframe(group_path),
            cfg.report_path("exploratory_lagged_state_coupling", ext="png", branch=branch),
            title=f"Exploratory {state_label} lagged EEG-SEEG state coupling",
        )
        subject_path = cfg.cache_path("coupling", _LAGGED_STATE_SUBJECT_STEM, ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    _LAGGED_STATE_SUBJECT_STEM: subject_path,
                    _LAGGED_STATE_GROUP_STEM: group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_lagged_state_coupling_subject_excel"] = table_reports[_LAGGED_STATE_SUBJECT_STEM]
            outputs[f"{branch}_lagged_state_coupling_group_excel"] = table_reports[_LAGGED_STATE_GROUP_STEM]
    for branch, group_path in _discover_branch_paths(cfg, "stats", _TRANSITION_STATE_GROUP_STEM, ext="parquet"):
        outputs[f"{branch}_transition_state_coupling_matrix"] = plot_state_transition_matrix(
            read_dataframe(group_path),
            cfg.report_path("exploratory_transition_state_coupling", ext="png", branch=branch),
            title=f"Exploratory {state_label} EEG transition-conditioned SEEG state coupling",
        )
        subject_path = cfg.cache_path("coupling", _TRANSITION_STATE_SUBJECT_STEM, ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    _TRANSITION_STATE_SUBJECT_STEM: subject_path,
                    _TRANSITION_STATE_GROUP_STEM: group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_transition_state_coupling_subject_excel"] = table_reports[_TRANSITION_STATE_SUBJECT_STEM]
            outputs[f"{branch}_transition_state_coupling_group_excel"] = table_reports[_TRANSITION_STATE_GROUP_STEM]
    for branch, group_path in _discover_branch_paths(cfg, "stats", _FIELD_STATE_GROUP_STEM, ext="parquet"):
        outputs[f"{branch}_field_state_coupling_curve"] = plot_direct_coupling_lag_curve(
            read_dataframe(group_path),
            cfg.report_path("exploratory_field_state_coupling", ext="png", branch=branch),
            title=f"Exploratory {state_label} EEG and SEEG field-state coupling",
        )
        subject_path = cfg.cache_path("coupling", _FIELD_STATE_SUBJECT_STEM, ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    _FIELD_STATE_SUBJECT_STEM: subject_path,
                    _FIELD_STATE_GROUP_STEM: group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_field_state_coupling_subject_excel"] = table_reports[_FIELD_STATE_SUBJECT_STEM]
            outputs[f"{branch}_field_state_coupling_group_excel"] = table_reports[_FIELD_STATE_GROUP_STEM]
    for branch, group_path in _discover_branch_paths(cfg, "stats", _LAGGED_FIELD_STATE_GROUP_STEM, ext="parquet"):
        outputs[f"{branch}_lagged_field_state_coupling_curve"] = plot_direct_coupling_lag_curve(
            read_dataframe(group_path),
            cfg.report_path("exploratory_lagged_field_state_coupling", ext="png", branch=branch),
            title=f"Exploratory {state_label} lagged EEG and SEEG field-state coupling",
        )
        subject_path = cfg.cache_path("coupling", _LAGGED_FIELD_STATE_SUBJECT_STEM, ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    _LAGGED_FIELD_STATE_SUBJECT_STEM: subject_path,
                    _LAGGED_FIELD_STATE_GROUP_STEM: group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_lagged_field_state_coupling_subject_excel"] = table_reports[_LAGGED_FIELD_STATE_SUBJECT_STEM]
            outputs[f"{branch}_lagged_field_state_coupling_group_excel"] = table_reports[_LAGGED_FIELD_STATE_GROUP_STEM]
    for branch, group_path in _discover_branch_paths(cfg, "stats", _FINE_LAG_FIELD_STATE_GROUP_STEM, ext="parquet"):
        outputs[f"{branch}_fine_lag_field_state_coupling_curve"] = plot_direct_coupling_lag_curve(
            read_dataframe(group_path),
            cfg.report_path("exploratory_fine_lag_field_state_coupling", ext="png", branch=branch),
            title=f"Exploratory {state_label} fine-lag EEG and SEEG field-state coupling",
        )
        subject_peaks_path = cfg.cache_path("coupling", _FINE_LAG_FIELD_STATE_PEAK_SUBJECT_STEM, ext="parquet", branch=branch)
        group_peak_path = cfg.cache_path("stats", _FINE_LAG_FIELD_STATE_PEAK_GROUP_STEM, ext="parquet", branch=branch)
        if subject_peaks_path.exists():
            subject_peaks_df = read_dataframe(subject_peaks_path)
            if not subject_peaks_df.empty:
                subject_peak_long = subject_peaks_df.melt(
                    id_vars=["patient_id"],
                    value_vars=["peak_lag_ms", "peak_effect_mean_diff", "peak_width_ms"],
                    var_name="summary_kind",
                    value_name="summary_value",
                )
                outputs[f"{branch}_fine_lag_field_state_peak_heatmap"] = plot_subject_state_profile_heatmap(
                    subject_peak_long,
                    cfg.report_path("exploratory_fine_lag_field_state_peak_summary", ext="png", branch=branch),
                    title=f"Exploratory {state_label} fine-lag field-state peak summaries",
                    state_column="summary_kind",
                    value_column="summary_value",
                )
        report_sources = {
            _FINE_LAG_FIELD_STATE_GROUP_STEM: group_path,
        }
        subject_curve_path = cfg.cache_path("coupling", _FINE_LAG_FIELD_STATE_SUBJECT_STEM, ext="parquet", branch=branch)
        if subject_curve_path.exists():
            report_sources[_FINE_LAG_FIELD_STATE_SUBJECT_STEM] = subject_curve_path
        if subject_peaks_path.exists():
            report_sources[_FINE_LAG_FIELD_STATE_PEAK_SUBJECT_STEM] = subject_peaks_path
        if group_peak_path.exists():
            report_sources[_FINE_LAG_FIELD_STATE_PEAK_GROUP_STEM] = group_peak_path
        table_reports = _write_table_reports_from_paths(cfg, report_sources, branch=branch)
        if _FINE_LAG_FIELD_STATE_SUBJECT_STEM in table_reports:
            outputs[f"{branch}_fine_lag_field_state_coupling_subject_excel"] = table_reports[_FINE_LAG_FIELD_STATE_SUBJECT_STEM]
        outputs[f"{branch}_fine_lag_field_state_coupling_group_excel"] = table_reports[_FINE_LAG_FIELD_STATE_GROUP_STEM]
        if _FINE_LAG_FIELD_STATE_PEAK_SUBJECT_STEM in table_reports:
            outputs[f"{branch}_fine_lag_field_state_peak_subject_excel"] = table_reports[_FINE_LAG_FIELD_STATE_PEAK_SUBJECT_STEM]
        if _FINE_LAG_FIELD_STATE_PEAK_GROUP_STEM in table_reports:
            outputs[f"{branch}_fine_lag_field_state_peak_group_excel"] = table_reports[_FINE_LAG_FIELD_STATE_PEAK_GROUP_STEM]
    for branch, group_path in _discover_branch_paths(cfg, "stats", _TRANSITION_FIELD_STATE_GROUP_STEM, ext="parquet"):
        group_df = read_dataframe(group_path)
        plotted_df = group_df[group_df["response_kind"] == "any-switch"].copy() if "response_kind" in group_df.columns else group_df
        outputs[f"{branch}_transition_field_state_coupling_matrix"] = plot_state_transition_matrix(
            plotted_df,
            cfg.report_path("exploratory_transition_field_state_coupling", ext="png", branch=branch),
            title=f"Exploratory {state_label} transition-conditioned SEEG field-state switching",
        )
        subject_path = cfg.cache_path("coupling", _TRANSITION_FIELD_STATE_SUBJECT_STEM, ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    _TRANSITION_FIELD_STATE_SUBJECT_STEM: subject_path,
                    _TRANSITION_FIELD_STATE_GROUP_STEM: group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_transition_field_state_coupling_subject_excel"] = table_reports[
                _TRANSITION_FIELD_STATE_SUBJECT_STEM
            ]
            outputs[f"{branch}_transition_field_state_coupling_group_excel"] = table_reports[
                _TRANSITION_FIELD_STATE_GROUP_STEM
            ]
    for branch, group_path in _discover_branch_paths(cfg, "stats", _FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM, ext="parquet"):
        group_df = read_dataframe(group_path)
        plotted_df = group_df[group_df["response_kind"] == "any-switch"].copy() if "response_kind" in group_df.columns else group_df
        outputs[f"{branch}_field_state_to_eeg_switching_matrix"] = plot_state_transition_matrix(
            plotted_df,
            cfg.report_path("exploratory_field_state_to_eeg_switching", ext="png", branch=branch),
            title=f"Exploratory {state_label} SEEG-led EEG switching",
            x_label="SEEG to_state",
            y_label="SEEG from_state",
        )
        subject_path = cfg.cache_path("coupling", _FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM, ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    _FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM: subject_path,
                    _FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM: group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_field_state_to_eeg_switching_subject_excel"] = table_reports[
                _FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM
            ]
            outputs[f"{branch}_field_state_to_eeg_switching_group_excel"] = table_reports[
                _FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM
            ]
    for branch, group_path in _discover_branch_paths(cfg, "stats", _GFP_GLOBAL_GROUP_STEM, ext="parquet"):
        outputs[f"{branch}_gfp_global_coupling_curve"] = plot_effect_curve(
            read_dataframe(group_path),
            cfg.report_path("exploratory_gfp_global_coupling", ext="png", branch=branch),
            title=f"Exploratory {state_label} EEG GFP versus SEEG global coupling",
            x_column="lag_ms",
            x_label="Lag (ms)",
        )
        subject_path = cfg.cache_path("coupling", _GFP_GLOBAL_SUBJECT_STEM, ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    _GFP_GLOBAL_SUBJECT_STEM: subject_path,
                    _GFP_GLOBAL_GROUP_STEM: group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_gfp_global_coupling_subject_excel"] = table_reports[_GFP_GLOBAL_SUBJECT_STEM]
            outputs[f"{branch}_gfp_global_coupling_group_excel"] = table_reports[_GFP_GLOBAL_GROUP_STEM]
    for branch, group_path in _discover_branch_paths(cfg, "stats", _LAGGED_GFP_GLOBAL_GROUP_STEM, ext="parquet"):
        outputs[f"{branch}_lagged_gfp_global_coupling_curve"] = plot_effect_curve(
            read_dataframe(group_path),
            cfg.report_path("exploratory_lagged_gfp_global_coupling", ext="png", branch=branch),
            title=f"Exploratory {state_label} lagged EEG GFP versus SEEG global coupling",
            x_column="lag_ms",
            x_label="Lag (ms)",
        )
        subject_path = cfg.cache_path("coupling", _LAGGED_GFP_GLOBAL_SUBJECT_STEM, ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    _LAGGED_GFP_GLOBAL_SUBJECT_STEM: subject_path,
                    _LAGGED_GFP_GLOBAL_GROUP_STEM: group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_lagged_gfp_global_coupling_subject_excel"] = table_reports[_LAGGED_GFP_GLOBAL_SUBJECT_STEM]
            outputs[f"{branch}_lagged_gfp_global_coupling_group_excel"] = table_reports[_LAGGED_GFP_GLOBAL_GROUP_STEM]
    for branch, group_path in _discover_branch_paths(cfg, "stats", _PEAK_GFP_GLOBAL_GROUP_STEM, ext="parquet"):
        outputs[f"{branch}_peak_gfp_global_coupling_curve"] = plot_effect_curve(
            read_dataframe(group_path),
            cfg.report_path("exploratory_peak_gfp_global_coupling", ext="png", branch=branch),
            title=f"Exploratory {state_label} EEG GFP peak-centered SEEG global trajectory",
            x_column="offset_ms",
            x_label="Offset (ms)",
        )
        subject_path = cfg.cache_path("coupling", _PEAK_GFP_GLOBAL_SUBJECT_STEM, ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    _PEAK_GFP_GLOBAL_SUBJECT_STEM: subject_path,
                    _PEAK_GFP_GLOBAL_GROUP_STEM: group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_peak_gfp_global_coupling_subject_excel"] = table_reports[_PEAK_GFP_GLOBAL_SUBJECT_STEM]
            outputs[f"{branch}_peak_gfp_global_coupling_group_excel"] = table_reports[_PEAK_GFP_GLOBAL_GROUP_STEM]
    for branch, omnibus_path in _discover_branch_paths(cfg, "stats", _GFP_CONTROLLED_MICROSTATE_GROUP_OMNIBUS_STEM, ext="parquet"):
        omnibus_df = read_dataframe(omnibus_path)
        if not omnibus_df.empty and "global_metric_label" not in omnibus_df.columns:
            omnibus_df["global_metric_label"] = omnibus_df.apply(
                lambda row: global_metric_label(str(row.metric_definition), str(row.weighting_strategy)),
                axis=1,
            )
        outputs[f"{branch}_gfp_controlled_microstate_omnibus_heatmap"] = plot_group_metric_heatmap(
            omnibus_df,
            cfg.report_path("exploratory_gfp_controlled_microstate_omnibus", ext="png", branch=branch),
            title=f"Exploratory {state_label} GFP-controlled microstate omnibus statistics",
            value_column="statistic",
            unit_column="global_metric_label",
        )
        posthoc_path = cfg.cache_path("stats", _GFP_CONTROLLED_MICROSTATE_GROUP_POSTHOC_STEM, ext="parquet", branch=branch)
        if posthoc_path.exists():
            posthoc_df = read_dataframe(posthoc_path)
            if not posthoc_df.empty and "global_metric_label" not in posthoc_df.columns:
                posthoc_df["global_metric_label"] = posthoc_df.apply(
                    lambda row: global_metric_label(str(row.metric_definition), str(row.weighting_strategy)),
                    axis=1,
                )
            outputs[f"{branch}_gfp_controlled_microstate_posthoc_heatmap"] = plot_group_metric_heatmap(
                posthoc_df,
                cfg.report_path("exploratory_gfp_controlled_microstate_posthoc", ext="png", branch=branch),
                title=f"Exploratory {state_label} GFP-controlled microstate post-hoc effects",
                value_column="mean_effect",
                unit_column="global_metric_label",
                row_column="contrast",
            )
        subject_path = cfg.cache_path("coupling", _GFP_CONTROLLED_MICROSTATE_SUBJECT_STEM, ext="parquet", branch=branch)
        if subject_path.exists() and posthoc_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    _GFP_CONTROLLED_MICROSTATE_SUBJECT_STEM: subject_path,
                    _GFP_CONTROLLED_MICROSTATE_GROUP_OMNIBUS_STEM: omnibus_path,
                    _GFP_CONTROLLED_MICROSTATE_GROUP_POSTHOC_STEM: posthoc_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_gfp_controlled_microstate_subject_excel"] = table_reports[_GFP_CONTROLLED_MICROSTATE_SUBJECT_STEM]
            outputs[f"{branch}_gfp_controlled_microstate_group_omnibus_excel"] = table_reports[
                _GFP_CONTROLLED_MICROSTATE_GROUP_OMNIBUS_STEM
            ]
            outputs[f"{branch}_gfp_controlled_microstate_group_posthoc_excel"] = table_reports[
                _GFP_CONTROLLED_MICROSTATE_GROUP_POSTHOC_STEM
            ]
    for branch, group_path in _discover_branch_paths(cfg, "stats", _GFP_CONTROLLED_TRANSITION_GROUP_STEM, ext="parquet"):
        outputs[f"{branch}_gfp_controlled_transition_matrix"] = plot_state_transition_matrix(
            read_dataframe(group_path),
            cfg.report_path("exploratory_gfp_controlled_transition", ext="png", branch=branch),
            title=f"Exploratory {state_label} GFP-controlled transition-conditioned SEEG global effects",
        )
        subject_path = cfg.cache_path("coupling", _GFP_CONTROLLED_TRANSITION_SUBJECT_STEM, ext="parquet", branch=branch)
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    _GFP_CONTROLLED_TRANSITION_SUBJECT_STEM: subject_path,
                    _GFP_CONTROLLED_TRANSITION_GROUP_STEM: group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_gfp_controlled_transition_subject_excel"] = table_reports[_GFP_CONTROLLED_TRANSITION_SUBJECT_STEM]
            outputs[f"{branch}_gfp_controlled_transition_group_excel"] = table_reports[_GFP_CONTROLLED_TRANSITION_GROUP_STEM]
    for branch, omnibus_path in _discover_branch_paths(cfg, "stats", _GFP_CONTROLLED_FIELD_STATE_GROUP_OMNIBUS_STEM, ext="parquet"):
        outputs[f"{branch}_gfp_controlled_field_state_omnibus_heatmap"] = plot_group_metric_heatmap(
            read_dataframe(omnibus_path),
            cfg.report_path("exploratory_gfp_controlled_field_state_omnibus", ext="png", branch=branch),
            title=f"Exploratory {state_label} GFP-controlled field-state switching omnibus statistics",
            value_column="statistic",
            unit_column="peak_metric",
        )
        posthoc_path = cfg.cache_path("stats", _GFP_CONTROLLED_FIELD_STATE_GROUP_POSTHOC_STEM, ext="parquet", branch=branch)
        if posthoc_path.exists():
            outputs[f"{branch}_gfp_controlled_field_state_posthoc_heatmap"] = plot_group_metric_heatmap(
                read_dataframe(posthoc_path),
                cfg.report_path("exploratory_gfp_controlled_field_state_posthoc", ext="png", branch=branch),
                title=f"Exploratory {state_label} GFP-controlled field-state switching post-hoc effects",
                value_column="mean_effect",
                unit_column="peak_metric",
                row_column="contrast",
            )
        transition_group_path = cfg.cache_path("stats", _GFP_CONTROLLED_FIELD_STATE_TRANSITION_GROUP_STEM, ext="parquet", branch=branch)
        if transition_group_path.exists():
            outputs[f"{branch}_gfp_controlled_field_state_transition_matrix"] = plot_state_transition_matrix(
                read_dataframe(transition_group_path),
                cfg.report_path("exploratory_gfp_controlled_field_state_transition", ext="png", branch=branch),
                title=f"Exploratory {state_label} GFP-controlled field-state transition switching",
            )
        subject_profile_path = cfg.cache_path("coupling", _GFP_CONTROLLED_FIELD_STATE_SUBJECT_STEM, ext="parquet", branch=branch)
        subject_transition_path = cfg.cache_path(
            "coupling", _GFP_CONTROLLED_FIELD_STATE_TRANSITION_SUBJECT_STEM, ext="parquet", branch=branch
        )
        report_sources = {
            _GFP_CONTROLLED_FIELD_STATE_GROUP_OMNIBUS_STEM: omnibus_path,
        }
        if subject_profile_path.exists():
            report_sources[_GFP_CONTROLLED_FIELD_STATE_SUBJECT_STEM] = subject_profile_path
        if posthoc_path.exists():
            report_sources[_GFP_CONTROLLED_FIELD_STATE_GROUP_POSTHOC_STEM] = posthoc_path
        if subject_transition_path.exists():
            report_sources[_GFP_CONTROLLED_FIELD_STATE_TRANSITION_SUBJECT_STEM] = subject_transition_path
        if transition_group_path.exists():
            report_sources[_GFP_CONTROLLED_FIELD_STATE_TRANSITION_GROUP_STEM] = transition_group_path
        table_reports = _write_table_reports_from_paths(cfg, report_sources, branch=branch)
        if _GFP_CONTROLLED_FIELD_STATE_SUBJECT_STEM in table_reports:
            outputs[f"{branch}_gfp_controlled_field_state_subject_excel"] = table_reports[
                _GFP_CONTROLLED_FIELD_STATE_SUBJECT_STEM
            ]
        outputs[f"{branch}_gfp_controlled_field_state_group_omnibus_excel"] = table_reports[
            _GFP_CONTROLLED_FIELD_STATE_GROUP_OMNIBUS_STEM
        ]
        if _GFP_CONTROLLED_FIELD_STATE_GROUP_POSTHOC_STEM in table_reports:
            outputs[f"{branch}_gfp_controlled_field_state_group_posthoc_excel"] = table_reports[
                _GFP_CONTROLLED_FIELD_STATE_GROUP_POSTHOC_STEM
            ]
        if _GFP_CONTROLLED_FIELD_STATE_TRANSITION_SUBJECT_STEM in table_reports:
            outputs[f"{branch}_gfp_controlled_field_state_transition_subject_excel"] = table_reports[
                _GFP_CONTROLLED_FIELD_STATE_TRANSITION_SUBJECT_STEM
            ]
        if _GFP_CONTROLLED_FIELD_STATE_TRANSITION_GROUP_STEM in table_reports:
            outputs[f"{branch}_gfp_controlled_field_state_transition_group_excel"] = table_reports[
                _GFP_CONTROLLED_FIELD_STATE_TRANSITION_GROUP_STEM
            ]
    for branch, group_path in _discover_branch_paths(cfg, "stats", _GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM, ext="parquet"):
        outputs[f"{branch}_gfp_controlled_field_state_to_eeg_switching_matrix"] = plot_state_transition_matrix(
            read_dataframe(group_path),
            cfg.report_path("exploratory_gfp_controlled_field_state_to_eeg_switching", ext="png", branch=branch),
            title=f"Exploratory {state_label} GFP-controlled SEEG-led EEG switching",
            x_label="SEEG to_state",
            y_label="SEEG from_state",
        )
        subject_path = cfg.cache_path(
            "coupling", _GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM, ext="parquet", branch=branch
        )
        if subject_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    _GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM: subject_path,
                    _GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM: group_path,
                },
                branch=branch,
            )
            outputs[f"{branch}_gfp_controlled_field_state_to_eeg_switching_subject_excel"] = table_reports[
                _GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_SUBJECT_STEM
            ]
            outputs[f"{branch}_gfp_controlled_field_state_to_eeg_switching_group_excel"] = table_reports[
                _GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM
            ]
    return outputs
