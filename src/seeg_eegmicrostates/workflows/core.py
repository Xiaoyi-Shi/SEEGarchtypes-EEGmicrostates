from __future__ import annotations

from .shared import *

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

