from __future__ import annotations

from pathlib import Path

import pandas as pd

from seeg_eegmicrostates._utils import config_hash, read_dataframe, write_csv_dataframe, write_dataframe, write_excel_dataframe
from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.coupling import (
    DEFAULT_FINE_FIELD_LAG_WINDOW_MS,
    DEFAULT_FIELD_STATE_MODEL_ORDER_RANGE,
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
    summarize_group_field_state_model_order,
    summarize_subject_field_state_model_order,
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
_FIELD_STATE_MODEL_ORDER_SUBJECT_STEM = "subject_field_state_model_order"
_FIELD_STATE_MODEL_ORDER_GROUP_STEM = "group_field_state_model_order"
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
_PAPER_CORE_EXPLORATORY_ANALYSES = (
    "field-state-coupling",
    "field-state-archetypes",
    "archetype-conditioned-eeg-topography",
    "fine-lag-field-state-coupling",
)
_SUPPLEMENTARY_EXPLORATORY_ANALYSES = (
    "field-state-model-order-evaluation",
    "gfp-global-coupling",
    "peak-gfp-global-coupling",
    "gfp-controlled-microstate",
    "gfp-controlled-transition",
    "field-state-to-eeg-switching",
    "gfp-controlled-field-state-to-eeg-switching",
)
_MAINTAINED_EXPLORATORY_ANALYSES = (
    *_PAPER_CORE_EXPLORATORY_ANALYSES,
    *_SUPPLEMENTARY_EXPLORATORY_ANALYSES,
)
_PAPER_REPORT_BRANCH = "paper_workflow"
_MAIN_FIGURE_SUBDIR = "main_figures"
_SUPPLEMENTARY_FIGURE_SUBDIR = "supplementary_figures"
_MAIN_TABLE_SUBDIR = "main_tables"
_SUPPLEMENTARY_TABLE_SUBDIR = "supplementary_tables"
_MANIFEST_SUBDIR = "manifests"


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


def _retained_field_state_artifact_branch(cfg: AnalysisConfig) -> str:
    return _field_state_artifact_branch(
        cfg,
        peak_metric=DEFAULT_FIELD_STATE_PEAK_METRIC,
        normalization=DEFAULT_FIELD_STATE_NORMALIZATION,
        state_count=_resolve_field_state_count(None, cfg),
        min_duration_ms=_resolve_field_min_duration_ms(None, cfg),
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


def _field_state_model_order_branch(
    cfg: AnalysisConfig,
    *,
    peak_metric: str,
    normalization: str,
    min_duration_ms: int,
    candidate_ks: tuple[int, ...],
) -> str:
    return _exploratory_branch(
        cfg,
        "field-state-model-order-evaluation",
        params={
            "peak_metric": normalize_field_peak_metric(peak_metric),
            "normalization": normalize_field_normalization(normalization),
            "min_duration_ms": int(min_duration_ms),
            "candidate_ks": "-".join(str(value) for value in candidate_ks),
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



__all__ = [name for name in globals() if not name.startswith("__")]

