from __future__ import annotations

from pathlib import Path

import pandas as pd

from seeg_eegmicrostates._utils import config_hash, read_dataframe, write_dataframe, write_excel_dataframe
from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.coupling import (
    DEFAULT_GFP_GLOBAL_METRIC,
    DEFAULT_GFP_GLOBAL_SURROGATES,
    DEFAULT_GFP_GLOBAL_WEIGHTING,
    DEFAULT_GFP_PEAK_WINDOW_SEC,
    SUPPORTED_GFP_GLOBAL_METRICS,
    SUPPORTED_GFP_GLOBAL_WEIGHTINGS,
    align_eeg_and_seeg_state_labels,
    align_gfp_and_global_traces,
    align_label_table_to_region_timeseries,
    align_microstate_to_gfp_and_global,
    align_region_timeseries_to_labels,
    build_microstate_event_table,
    build_state_transition_table,
    connectivity_analysis_branch,
    compute_subject_direct_state_coupling,
    compute_subject_event_locked_connectivity_effects,
    compute_subject_event_locked_region_effects,
    compute_subject_gfp_controlled_microstate_profiles,
    compute_subject_gfp_controlled_transition_effects,
    compute_subject_gfp_global_coupling,
    compute_subject_microstate_connectivity_profiles,
    compute_subject_microstate_region_profiles,
    compute_subject_peak_centered_global_trajectory,
    compute_subject_transition_state_coupling,
    compute_subject_windowed_region_coupling,
    compute_windowed_region_metrics,
    compute_windowed_state_metrics,
    derive_seeg_global_metric_trace,
    derive_direct_seeg_state_artifacts,
    global_metric_label,
    normalize_connectivity_method,
    normalize_direct_state_backend,
    normalize_global_metric_definition,
    normalize_global_weighting_strategy,
    sample_period_from_times,
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
from seeg_eegmicrostates.io import load_atlas_table, load_workbook_tables, save_raw_fif, scan_repository
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
    plot_group_effects_heatmap,
    plot_group_metric_heatmap,
    plot_microstate_templates,
    plot_state_transition_matrix,
    plot_transition_effect_heatmap,
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
    global_metric: str = DEFAULT_GFP_GLOBAL_METRIC,
    global_weighting: str = DEFAULT_GFP_GLOBAL_WEIGHTING,
    event_window_sec: float = 1.0,
    window_sec: float = 10.0,
    peak_window_sec: float | None = None,
    transition_window_sec: float | None = None,
    direct_backend: str = "pca-kmeans",
    direct_state_count: int | None = None,
    direct_components: int | None = None,
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
    return outputs
