from __future__ import annotations

from .core import (
    _all_exist,
    _eligible_rows,
    _load_patient_eeg_topography_trace,
    _write_table_reports,
    _write_table_reports_from_paths,
    run_eeg_states_stage,
    run_seeg_regions_stage,
)
from .export import _finalize_field_state_model_order_subject_table, _paper_ready_group_rows
from .shared import *

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



def run_exploratory_field_state_model_order_stage(
    cfg: AnalysisConfig,
    *,
    field_peak_metric: str = DEFAULT_FIELD_STATE_PEAK_METRIC,
    field_normalization: str = DEFAULT_FIELD_STATE_NORMALIZATION,
    field_min_duration_ms: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    normalized_metric = normalize_field_peak_metric(field_peak_metric)
    normalized_strategy = normalize_field_normalization(field_normalization)
    min_duration_ms = _resolve_field_min_duration_ms(field_min_duration_ms, cfg)
    threshold = _exploratory_min_subjects(min_subjects, cfg)
    candidate_ks = DEFAULT_FIELD_STATE_MODEL_ORDER_RANGE
    retained_k = _resolve_field_state_count(None, cfg)
    branch = _field_state_model_order_branch(
        cfg,
        peak_metric=normalized_metric,
        normalization=normalized_strategy,
        min_duration_ms=min_duration_ms,
        candidate_ks=candidate_ks,
    )
    cached = {
        "subject_summary": cfg.cache_path("coupling", _FIELD_STATE_MODEL_ORDER_SUBJECT_STEM, ext="parquet", branch=branch),
        "group_summary": cfg.cache_path("stats", _FIELD_STATE_MODEL_ORDER_GROUP_STEM, ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        tables = _write_table_reports_from_paths(
            cfg,
            {
                _FIELD_STATE_MODEL_ORDER_SUBJECT_STEM: cached["subject_summary"],
                _FIELD_STATE_MODEL_ORDER_GROUP_STEM: cached["group_summary"],
            },
            branch=branch,
        )
        return {
            **cached,
            "subject_summary_excel": tables[_FIELD_STATE_MODEL_ORDER_SUBJECT_STEM],
            "group_summary_excel": tables[_FIELD_STATE_MODEL_ORDER_GROUP_STEM],
        }

    subject_frames: list[pd.DataFrame] = []
    for k_index, candidate_k in enumerate(candidate_ks):
        _, state_paths = _ensure_seeg_field_state_artifacts(
            cfg,
            peak_metric=normalized_metric,
            normalization=normalized_strategy,
            state_count=int(candidate_k),
            min_duration_ms=min_duration_ms,
        )
        peak_maps_df = read_dataframe(state_paths["peak_maps"])
        template_df = read_dataframe(state_paths["templates"])
        profile_df = read_dataframe(state_paths["profiles"])
        patient_ids = sorted(
            {
                *peak_maps_df.get("patient_id", pd.Series(dtype=str)).astype(str).tolist(),
                *template_df.get("patient_id", pd.Series(dtype=str)).astype(str).tolist(),
                *profile_df.get("patient_id", pd.Series(dtype=str)).astype(str).tolist(),
            }
        )
        for patient_offset, patient_id in enumerate(patient_ids):
            subject_frames.append(
                summarize_subject_field_state_model_order(
                    peak_maps_df[peak_maps_df["patient_id"].astype(str) == patient_id].copy(),
                    template_df[template_df["patient_id"].astype(str) == patient_id].copy(),
                    profile_df[profile_df["patient_id"].astype(str) == patient_id].copy(),
                    patient_id=patient_id,
                    stability_seed=cfg.random_seed + (k_index * 1000) + patient_offset,
                )
            )

    subject_summary = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()
    subject_summary = _finalize_field_state_model_order_subject_table(
        subject_summary,
        candidate_ks=candidate_ks,
        retained_k=retained_k,
    )
    group_summary = summarize_group_field_state_model_order(subject_summary, retained_k=retained_k)
    if not group_summary.empty:
        group_summary.insert(4, "k_range", f"{candidate_ks[0]}-{candidate_ks[-1]}")
        group_summary = _paper_ready_group_rows(group_summary, min_subjects=threshold)

    subject_path = write_dataframe(subject_summary, cached["subject_summary"])
    group_path = write_dataframe(group_summary, cached["group_summary"])
    tables = _write_table_reports(
        cfg,
        {
            _FIELD_STATE_MODEL_ORDER_SUBJECT_STEM: subject_summary,
            _FIELD_STATE_MODEL_ORDER_GROUP_STEM: group_summary,
        },
        branch=branch,
    )
    return {
        "subject_summary": subject_path,
        "group_summary": group_path,
        "subject_summary_excel": tables[_FIELD_STATE_MODEL_ORDER_SUBJECT_STEM],
        "group_summary_excel": tables[_FIELD_STATE_MODEL_ORDER_GROUP_STEM],
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
    field_peak_metric: str = DEFAULT_FIELD_STATE_PEAK_METRIC,
    field_normalization: str = DEFAULT_FIELD_STATE_NORMALIZATION,
    field_state_count: int | None = None,
    field_min_duration_ms: int | None = None,
    field_archetype_space: str = YEO17_PARCELLATION_NAME,
    global_metric: str = DEFAULT_GFP_GLOBAL_METRIC,
    global_weighting: str = DEFAULT_GFP_GLOBAL_WEIGHTING,
    peak_window_sec: float | None = None,
    transition_window_sec: float | None = None,
    field_surrogates: int | None = None,
    fine_lag_window_ms: int | None = None,
    global_surrogates: int | None = None,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    selected = str(analysis).strip().lower()
    if selected == "all":
        outputs: dict[str, Path] = {}
        for item in _MAINTAINED_EXPLORATORY_ANALYSES:
            kwargs = {
                "peak_window_sec": peak_window_sec,
                "transition_window_sec": transition_window_sec,
                "field_peak_metric": field_peak_metric,
                "field_normalization": field_normalization,
                "field_state_count": field_state_count,
                "field_min_duration_ms": field_min_duration_ms,
                "field_archetype_space": field_archetype_space,
                "field_surrogates": field_surrogates,
                "fine_lag_window_ms": fine_lag_window_ms,
                "global_metric": global_metric,
                "global_weighting": global_weighting,
                "global_surrogates": global_surrogates,
                "min_subjects": min_subjects,
            }
            stage_outputs = run_exploratory_coupling_stage(cfg, analysis=item, **kwargs)
            prefix = cfg.branch_name(item)
            for key, value in stage_outputs.items():
                outputs[f"{prefix}_{key}"] = value
        return outputs
    gfp_analyses = {
        "gfp-global-coupling",
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
                    global_metric=metric_definition,
                    global_weighting=weighting_strategy,
                    peak_window_sec=peak_window_sec,
                    transition_window_sec=transition_window_sec,
                    field_peak_metric=field_peak_metric,
                    field_normalization=field_normalization,
                    field_state_count=field_state_count,
                    field_min_duration_ms=field_min_duration_ms,
                    field_archetype_space=field_archetype_space,
                    field_surrogates=field_surrogates,
                    fine_lag_window_ms=fine_lag_window_ms,
                    global_surrogates=global_surrogates,
                    min_subjects=min_subjects,
                )
                combo_prefix = cfg.branch_name(f"{metric_definition}_{weighting_strategy}")
                for key, value in stage_outputs.items():
                    outputs[f"{combo_prefix}_{key}"] = value
        return outputs
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
    if selected == "field-state-model-order-evaluation":
        return run_exploratory_field_state_model_order_stage(
            cfg,
            field_peak_metric=field_peak_metric,
            field_normalization=field_normalization,
            field_min_duration_ms=field_min_duration_ms,
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
    supported = ", ".join(["all", *_MAINTAINED_EXPLORATORY_ANALYSES])
    raise ValueError(f"Unsupported exploratory analysis '{analysis}'. Expected one of: {supported}.")


