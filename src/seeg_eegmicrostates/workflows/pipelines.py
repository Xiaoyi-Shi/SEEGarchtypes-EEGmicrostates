from __future__ import annotations

from pathlib import Path

import pandas as pd

from seeg_eegmicrostates._utils import config_hash, read_dataframe, write_dataframe, write_excel_dataframe
from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.coupling import (
    align_label_table_to_region_timeseries,
    align_region_timeseries_to_labels,
    build_microstate_event_table,
    build_state_transition_table,
    connectivity_analysis_branch,
    compute_subject_event_locked_connectivity_effects,
    compute_subject_event_locked_region_effects,
    compute_subject_microstate_connectivity_profiles,
    compute_subject_microstate_region_profiles,
    compute_subject_windowed_region_coupling,
    compute_windowed_region_metrics,
    compute_windowed_state_metrics,
    normalize_connectivity_method,
)
from seeg_eegmicrostates.eeg import (
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
from seeg_eegmicrostates.segment import build_ide_a_segments
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
    plot_group_effects_heatmap,
    plot_group_metric_heatmap,
    plot_microstate_templates,
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
_EXPLORATORY_ANALYSES = (
    "event-activity",
    "event-connectivity",
    "windowed-coupling",
    "transition-coupling",
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


def build_index_artifacts(cfg: AnalysisConfig) -> dict[str, Path]:
    cfg.ensure_runtime_directories()
    patient_info, annotation_info = load_workbook_tables(cfg.workbook_path)
    _ = patient_info
    recording_index = scan_repository(cfg.data_root)
    segments = build_ide_a_segments(annotation_info)
    cohort, inventory = build_main_cohort(recording_index, segments, cfg)
    outputs = {
        "recording_index": write_dataframe(recording_index, cfg.cache_path("index", "recording_index", ext="parquet")),
        "ide_a_segments": write_dataframe(segments, cfg.cache_path("segments", "ide_a_segments", ext="parquet")),
        "cohort": write_dataframe(cohort, cfg.cache_path("index", "cohort_ide_a_main", ext="parquet")),
        "eeg_inventory": write_dataframe(inventory, cfg.cache_path("eeg", "eeg_channel_inventory", ext="parquet")),
    }
    return outputs


def _load_cohort_and_segments(cfg: AnalysisConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    cohort_path = cfg.cache_path("index", "cohort_ide_a_main", ext="parquet")
    segments_path = cfg.cache_path("segments", "ide_a_segments", ext="parquet")
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
    cfg.ensure_runtime_directories()
    cached = {
        "model": cfg.cache_path("eeg", "group_microstate_model", ext="fif", branch=branch),
        "labels": cfg.cache_path("eeg", "microstate_labels", ext="parquet", branch=branch),
        "restored_channels": cfg.cache_path("eeg", "restored_channels", ext="parquet", branch=branch),
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
    labels = pd.concat(
        [label_microstates(raw, model, cfg, patient_id=patient_id) for patient_id, raw in preprocessed_raws.items()],
        ignore_index=True,
    )
    labels_path = write_dataframe(labels, cfg.cache_path("eeg", "microstate_labels", ext="parquet", branch=branch))
    missing_path = write_dataframe(pd.DataFrame(missing_rows), cfg.cache_path("eeg", "restored_channels", ext="parquet", branch=branch))
    return {"model": model_path, "labels": labels_path, "restored_channels": missing_path}


def run_eeg_states_stage(cfg: AnalysisConfig, *, template_fif: str | Path | None = None) -> dict[str, Path]:
    return run_eeg_microstate_branch(cfg, template_fif=template_fif)


def run_seeg_band_limited_region_branch(cfg: AnalysisConfig) -> dict[str, Path]:
    cfg.ensure_runtime_directories()
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
    cfg.ensure_runtime_directories()
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
    cfg.ensure_runtime_directories()
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
    cfg.ensure_runtime_directories()
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
    cfg.ensure_runtime_directories()
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
    cfg.ensure_runtime_directories()
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


def run_exploratory_coupling_stage(
    cfg: AnalysisConfig,
    *,
    analysis: str = "all",
    method: str = "all",
    event_window_sec: float = 1.0,
    window_sec: float = 10.0,
    min_subjects: int | None = None,
) -> dict[str, Path]:
    selected = str(analysis).strip().lower()
    if selected == "all":
        outputs: dict[str, Path] = {}
        for item in _EXPLORATORY_ANALYSES:
            kwargs = {
                "event_window_sec": event_window_sec,
                "window_sec": window_sec,
                "min_subjects": min_subjects,
                "method": method,
            }
            stage_outputs = run_exploratory_coupling_stage(cfg, analysis=item, **kwargs)
            prefix = cfg.branch_name(item)
            for key, value in stage_outputs.items():
                outputs[f"{prefix}_{key}"] = value
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
    supported = ", ".join(["all", *_EXPLORATORY_ANALYSES])
    raise ValueError(f"Unsupported exploratory analysis '{analysis}'. Expected one of: {supported}.")


def run_band_limited_connectivity_branch(cfg: AnalysisConfig, *, method: str = "corr") -> dict[str, Path]:
    cfg.ensure_runtime_directories()
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
    cfg.ensure_runtime_directories()
    outputs: dict[str, Path] = {}
    coverage_path = cfg.cache_path("seeg", _SEEG_REGION_COVERAGE_STEM, ext="parquet", branch=_BAND_BRANCH)
    if coverage_path.exists():
        coverage_df = read_dataframe(coverage_path)
        outputs["coverage"] = plot_coverage_summary(
            coverage_df,
            cfg.report_path("region_coverage", ext="png", branch=_BAND_BRANCH),
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
            title="Supplemental band-limited AAL3 activity omnibus statistics",
            value_column="statistic",
            unit_column="region",
        )
    activity_posthoc_path = cfg.cache_path("stats", _ACTIVITY_GROUP_POSTHOC_STEM, ext="parquet", branch=_ACTIVITY_BRANCH)
    if activity_posthoc_path.exists():
        outputs["activity_posthoc_heatmap"] = plot_group_metric_heatmap(
            read_dataframe(activity_posthoc_path),
            cfg.report_path("activity_posthoc", ext="png", branch=_ACTIVITY_BRANCH),
            title="Supplemental band-limited AAL3 activity post-hoc effects",
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
                title=f"AAL3 band-limited connectivity omnibus statistics ({method.upper()})",
            )
        connectivity_posthoc_path = cfg.cache_path("stats", _CONNECTIVITY_GROUP_POSTHOC_STEM, ext="parquet", branch=branch)
        if connectivity_posthoc_path.exists():
            outputs[f"band_connectivity_{method}_posthoc"] = plot_connectivity_posthoc_matrices(
                read_dataframe(connectivity_posthoc_path),
                cfg.report_path(f"band_connectivity_posthoc_{method}", ext="png", branch=branch),
                title=f"AAL3 band-limited connectivity post-hoc effects ({method.upper()})",
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
            title="Exploratory EEG event-locked AAL3 activity effects",
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
            title=f"Exploratory EEG event-locked AAL3 connectivity effects ({method.upper()})",
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
            title="Exploratory windowed EEG occupancy and AAL3 coupling effects",
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
            title="Exploratory EEG transition-locked AAL3 coupling effects",
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
    return outputs
