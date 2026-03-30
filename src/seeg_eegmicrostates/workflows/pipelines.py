from __future__ import annotations

from pathlib import Path

import pandas as pd

from seeg_eegmicrostates._utils import read_dataframe, write_dataframe, write_excel_dataframe
from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.coupling import (
    align_label_table_to_network_timeseries,
    align_network_timeseries_to_labels,
    align_modal_microstates,
    connectivity_analysis_branch,
    compute_cross_modal_state_summaries,
    compute_subject_microstate_connectivity_effects,
    compute_subject_microstate_network_effects,
    normalize_connectivity_method,
)
from seeg_eegmicrostates.eeg import (
    fit_group_microstate_model,
    label_microstates,
    preprocess_eeg_recording,
    save_microstate_model,
)
from seeg_eegmicrostates.io import load_atlas_table, load_workbook_tables, save_raw_fif, scan_repository
from seeg_eegmicrostates.qc import build_main_cohort
from seeg_eegmicrostates.seeg import (
    build_same_network_bipolar_map,
    compute_band_limited_network_signals,
    compute_hfa_envelope,
    fit_network_microstates,
    load_and_crop_bipolar_seeg,
)
from seeg_eegmicrostates.segment import build_ide_a_segments
from seeg_eegmicrostates.stats import run_group_connectivity_statistics, run_group_permutation_statistics
from seeg_eegmicrostates.viz import (
    plot_connectivity_effect_matrices,
    plot_coverage_summary,
    plot_cross_modal_overlap,
    plot_group_effects_heatmap,
    plot_microstate_templates,
)


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


def run_eeg_microstate_branch(cfg: AnalysisConfig, *, branch: str = "main") -> dict[str, Path]:
    cfg.ensure_runtime_directories()
    cached = {
        "model": cfg.cache_path("eeg", "group_microstate_model", ext="npz", branch=branch),
        "labels": cfg.cache_path("eeg", "microstate_labels", ext="parquet", branch=branch),
        "restored_channels": cfg.cache_path("eeg", "restored_channels", ext="parquet", branch=branch),
    }
    if _all_exist(cached):
        return cached
    cohort = _eligible_rows(cfg)
    band = cfg.eeg_microstate_band if branch == "main" else cfg.band_limited_range
    preprocessed_raws: dict[str, object] = {}
    missing_rows: list[dict[str, object]] = []
    for row in cohort.to_dict(orient="records"):
        raw19, missing = preprocess_eeg_recording(
            row["eeg_ref_path"],
            start_sec=float(row["start_sec"]),
            end_sec=float(row["end_sec"]),
            cfg=cfg,
            band=band,
        )
        patient_id = str(row["patient_id"])
        preprocessed_raws[patient_id] = raw19
        save_raw_fif(raw19, cfg.cache_path("eeg", "preprocessed", ext="fif", branch=branch, patient_id=patient_id))
        missing_rows.append({"patient_id": patient_id, "branch": branch, "restored_channels": list(missing)})
    model = fit_group_microstate_model(preprocessed_raws, cfg, branch=branch)
    model_path = save_microstate_model(model, cfg.cache_path("eeg", "group_microstate_model", ext="npz", branch=branch))
    labels = pd.concat(
        [label_microstates(raw, model, cfg, patient_id=patient_id) for patient_id, raw in preprocessed_raws.items()],
        ignore_index=True,
    )
    labels_path = write_dataframe(labels, cfg.cache_path("eeg", "microstate_labels", ext="parquet", branch=branch))
    missing_path = write_dataframe(pd.DataFrame(missing_rows), cfg.cache_path("eeg", "restored_channels", ext="parquet", branch=branch))
    return {"model": model_path, "labels": labels_path, "restored_channels": missing_path}


def run_seeg_hfa_branch(cfg: AnalysisConfig) -> dict[str, Path]:
    cfg.ensure_runtime_directories()
    cached = {
        "mapping": cfg.cache_path("seeg", "bipolar_network_map", ext="parquet", branch="hfa"),
        "coverage": cfg.cache_path("seeg", "network_coverage", ext="parquet", branch="hfa"),
    }
    if _all_exist(cached):
        return cached
    cohort = _eligible_rows(cfg)
    mapping_frames: list[pd.DataFrame] = []
    coverage_frames: list[pd.DataFrame] = []
    for row in cohort.to_dict(orient="records"):
        patient_id = str(row["patient_id"])
        atlas_df = load_atlas_table(row["atlas_path"])
        raw_bp = load_and_crop_bipolar_seeg(row["seeg_bipolar_path"], float(row["start_sec"]), float(row["end_sec"]))
        mapping_df = build_same_network_bipolar_map(atlas_df, list(raw_bp.ch_names), patient_id=patient_id)
        mapping_frames.append(mapping_df)
        hfa_df = compute_hfa_envelope(raw_bp, cfg)
        write_dataframe(hfa_df, cfg.cache_path("seeg", "bipolar_hfa", ext="parquet", branch="hfa", patient_id=patient_id))
        from seeg_eegmicrostates.seeg.network import aggregate_channel_dataframe_by_network

        network_df, coverage_df = aggregate_channel_dataframe_by_network(hfa_df, mapping_df, patient_id=patient_id)
        coverage_frames.append(coverage_df)
        write_dataframe(network_df, cfg.cache_path("seeg", "network_hfa", ext="parquet", branch="hfa", patient_id=patient_id))
    mapping = pd.concat(mapping_frames, ignore_index=True) if mapping_frames else pd.DataFrame()
    coverage = pd.concat(coverage_frames, ignore_index=True) if coverage_frames else pd.DataFrame()
    return {
        "mapping": write_dataframe(mapping, cached["mapping"]),
        "coverage": write_dataframe(coverage, cached["coverage"]),
    }


def run_seeg_band_limited_network_branch(cfg: AnalysisConfig) -> dict[str, Path]:
    cfg.ensure_runtime_directories()
    cohort = _eligible_rows(cfg)
    cached = {
        "mapping": cfg.cache_path("seeg", "bipolar_network_map", ext="parquet", branch="band_1_40"),
        "coverage": cfg.cache_path("seeg", "network_coverage", ext="parquet", branch="band_1_40"),
    }
    patient_paths = [
        cfg.cache_path("seeg", "network_band_limited", ext="parquet", branch="band_1_40", patient_id=str(patient_id))
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
        mapping_df = build_same_network_bipolar_map(atlas_df, list(raw_bp.ch_names), patient_id=patient_id)
        mapping_frames.append(mapping_df)
        network_df, coverage_df = compute_band_limited_network_signals(raw_bp, mapping_df, cfg, patient_id=patient_id)
        coverage_frames.append(coverage_df)
        write_dataframe(
            network_df,
            cfg.cache_path("seeg", "network_band_limited", ext="parquet", branch="band_1_40", patient_id=patient_id),
        )
    mapping = pd.concat(mapping_frames, ignore_index=True) if mapping_frames else pd.DataFrame()
    coverage = pd.concat(coverage_frames, ignore_index=True) if coverage_frames else pd.DataFrame()
    return {
        "mapping": write_dataframe(mapping, cached["mapping"]),
        "coverage": write_dataframe(coverage, cached["coverage"]),
    }


def run_band_limited_cross_modal_branch(cfg: AnalysisConfig) -> dict[str, Path]:
    cfg.ensure_runtime_directories()
    cached = {
        "eeg_labels": cfg.cache_path("eeg", "microstate_labels", ext="parquet", branch="band_1_40"),
        "seeg_labels": cfg.cache_path("seeg", "network_microstate_labels", ext="parquet", branch="band_1_40"),
        "contingency": cfg.cache_path("coupling", "cross_modal_contingency", ext="parquet", branch="band_1_40"),
        "summary": cfg.cache_path("coupling", "cross_modal_summary", ext="parquet", branch="band_1_40"),
        "mapping": cfg.cache_path("seeg", "bipolar_network_map", ext="parquet", branch="band_1_40"),
    }
    if _all_exist(cached):
        table_reports = _write_table_reports_from_paths(
            cfg,
            {
                "cross_modal_contingency": cached["contingency"],
                "cross_modal_summary": cached["summary"],
            },
            branch="band_1_40",
        )
        return {
            **cached,
            "contingency_excel": table_reports["cross_modal_contingency"],
            "summary_excel": table_reports["cross_modal_summary"],
        }
    eeg_outputs = run_eeg_microstate_branch(cfg, branch="band_1_40")
    band_outputs = run_seeg_band_limited_network_branch(cfg)
    cohort = _eligible_rows(cfg)
    contingency_frames: list[pd.DataFrame] = []
    summary_frames: list[pd.DataFrame] = []
    label_frames: list[pd.DataFrame] = []
    for row in cohort.to_dict(orient="records"):
        patient_id = str(row["patient_id"])
        network_df = read_dataframe(
            cfg.cache_path("seeg", "network_band_limited", ext="parquet", branch="band_1_40", patient_id=patient_id)
        )
        model, seeg_labels = fit_network_microstates(network_df, cfg, patient_id=patient_id)
        label_frames.append(seeg_labels)
        save_microstate_model(model, cfg.cache_path("seeg", "network_microstate_model", ext="npz", branch="band_1_40", patient_id=patient_id))
    seeg_labels_df = pd.concat(label_frames, ignore_index=True) if label_frames else pd.DataFrame()
    seeg_labels_path = write_dataframe(seeg_labels_df, cfg.cache_path("seeg", "network_microstate_labels", ext="parquet", branch="band_1_40"))
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    lag_window_samples = int(round(cfg.cross_modal_lag_window_sec * cfg.seeg_resample_hz))
    for patient_id, eeg_group in eeg_labels.groupby("patient_id"):
        seeg_group = seeg_labels_df[seeg_labels_df["patient_id"] == patient_id]
        aligned = align_modal_microstates(eeg_group, seeg_group, patient_id=str(patient_id))
        contingency, summary = compute_cross_modal_state_summaries(aligned, lag_window_samples=lag_window_samples)
        contingency_frames.append(contingency)
        summary_frames.append(summary)
    contingency_path = write_dataframe(
        pd.concat(contingency_frames, ignore_index=True) if contingency_frames else pd.DataFrame(),
        cfg.cache_path("coupling", "cross_modal_contingency", ext="parquet", branch="band_1_40"),
    )
    summary_path = write_dataframe(
        pd.concat(summary_frames, ignore_index=True) if summary_frames else pd.DataFrame(),
        cfg.cache_path("coupling", "cross_modal_summary", ext="parquet", branch="band_1_40"),
    )
    table_reports = _write_table_reports(
        cfg,
        {
            "cross_modal_contingency": read_dataframe(contingency_path),
            "cross_modal_summary": read_dataframe(summary_path),
        },
        branch="band_1_40",
    )
    return {
        "eeg_labels": eeg_outputs["labels"],
        "seeg_labels": seeg_labels_path,
        "contingency": contingency_path,
        "summary": summary_path,
        "mapping": band_outputs["mapping"],
        "contingency_excel": table_reports["cross_modal_contingency"],
        "summary_excel": table_reports["cross_modal_summary"],
    }
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
        "subject_effects": cfg.cache_path("coupling", "subject_connectivity_effects", ext="parquet", branch=analysis_branch),
        "group_effects": cfg.cache_path("stats", "group_connectivity_effects", ext="parquet", branch=analysis_branch),
    }
    if _all_exist(cached):
        table_reports = _write_table_reports_from_paths(
            cfg,
            {
                "subject_connectivity_effects": cached["subject_effects"],
                "group_connectivity_effects": cached["group_effects"],
            },
            branch=analysis_branch,
        )
        return {
            **cached,
            "subject_effects_excel": table_reports["subject_connectivity_effects"],
            "group_effects_excel": table_reports["group_connectivity_effects"],
        }
    eeg_outputs = run_eeg_microstate_branch(cfg, branch="band_1_40")
    _ = run_seeg_band_limited_network_branch(cfg)
    cohort = _eligible_rows(cfg)
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    aligned_frames: list[pd.DataFrame] = []
    for row in cohort.to_dict(orient="records"):
        patient_id = str(row["patient_id"])
        label_df = eeg_labels[eeg_labels["patient_id"] == patient_id]
        network_path = cfg.cache_path("seeg", "network_band_limited", ext="parquet", branch="band_1_40", patient_id=patient_id)
        network_df = read_dataframe(network_path)
        aligned_frames.append(align_network_timeseries_to_labels(label_df, network_df, patient_id=patient_id))
    aligned_df = pd.concat(aligned_frames, ignore_index=True) if aligned_frames else pd.DataFrame()
    aligned_path = write_dataframe(aligned_df, cached["aligned"])
    min_samples = max(8, int(round(cfg.seeg_resample_hz * 0.25)))
    subject_effects = compute_subject_microstate_connectivity_effects(
        aligned_df,
        min_samples=min_samples,
        method=normalized_method,
    )
    subject_path = write_dataframe(subject_effects, cached["subject_effects"])
    group_effects = run_group_connectivity_statistics(
        subject_effects,
        seed=cfg.random_seed,
        min_subjects=cfg.min_network_subjects,
    )
    group_path = write_dataframe(group_effects, cached["group_effects"])
    table_reports = _write_table_reports(
        cfg,
        {
            "subject_connectivity_effects": subject_effects,
            "group_connectivity_effects": group_effects,
        },
        branch=analysis_branch,
    )
    return {
        "aligned": aligned_path,
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": table_reports["subject_connectivity_effects"],
        "group_effects_excel": table_reports["group_connectivity_effects"],
    }


def run_hfa_coupling_branch(cfg: AnalysisConfig) -> dict[str, Path]:
    cfg.ensure_runtime_directories()
    cached = {
        "aligned": cfg.cache_path("coupling", "aligned_hfa", ext="parquet", branch="hfa"),
        "subject_effects": cfg.cache_path("coupling", "subject_effects", ext="parquet", branch="hfa"),
        "group_effects": cfg.cache_path("stats", "group_effects", ext="parquet", branch="hfa"),
    }
    if _all_exist(cached):
        table_reports = _write_table_reports_from_paths(
            cfg,
            {
                "hfa_subject_effects": cached["subject_effects"],
                "hfa_group_effects": cached["group_effects"],
            },
            branch="hfa",
        )
        return {
            **cached,
            "subject_effects_excel": table_reports["hfa_subject_effects"],
            "group_effects_excel": table_reports["hfa_group_effects"],
        }
    eeg_outputs = run_eeg_microstate_branch(cfg, branch="main")
    _ = run_seeg_hfa_branch(cfg)
    cohort = _eligible_rows(cfg)
    eeg_labels = read_dataframe(eeg_outputs["labels"])
    aligned_frames: list[pd.DataFrame] = []
    for row in cohort.to_dict(orient="records"):
        patient_id = str(row["patient_id"])
        label_df = eeg_labels[eeg_labels["patient_id"] == patient_id]
        network_path = cfg.cache_path("seeg", "network_hfa", ext="parquet", branch="hfa", patient_id=patient_id)
        network_df = read_dataframe(network_path)
        aligned_frames.append(align_label_table_to_network_timeseries(label_df, network_df, patient_id=patient_id))
    aligned_df = pd.concat(aligned_frames, ignore_index=True) if aligned_frames else pd.DataFrame()
    aligned_path = write_dataframe(aligned_df, cfg.cache_path("coupling", "aligned_hfa", ext="parquet", branch="hfa"))
    subject_effects = compute_subject_microstate_network_effects(aligned_df)
    subject_path = write_dataframe(subject_effects, cfg.cache_path("coupling", "subject_effects", ext="parquet", branch="hfa"))
    group_effects = run_group_permutation_statistics(subject_effects, seed=cfg.random_seed)
    group_path = write_dataframe(group_effects, cfg.cache_path("stats", "group_effects", ext="parquet", branch="hfa"))
    table_reports = _write_table_reports(
        cfg,
        {
            "hfa_subject_effects": subject_effects,
            "hfa_group_effects": group_effects,
        },
        branch="hfa",
    )
    return {
        "aligned": aligned_path,
        "subject_effects": subject_path,
        "group_effects": group_path,
        "subject_effects_excel": table_reports["hfa_subject_effects"],
        "group_effects_excel": table_reports["hfa_group_effects"],
    }


def render_reports(cfg: AnalysisConfig) -> dict[str, Path]:
    cfg.ensure_runtime_directories()
    outputs: dict[str, Path] = {}
    coverage_path = cfg.cache_path("seeg", "network_coverage", ext="parquet", branch="hfa")
    if coverage_path.exists():
        coverage_df = read_dataframe(coverage_path)
        outputs["coverage"] = plot_coverage_summary(coverage_df, cfg.report_path("network_coverage", ext="png", branch="hfa"))
    model_path = cfg.cache_path("eeg", "group_microstate_model", ext="npz", branch="main")
    if model_path.exists():
        from seeg_eegmicrostates.eeg.microstates import load_microstate_model

        outputs["microstates"] = plot_microstate_templates(
            load_microstate_model(model_path),
            cfg.report_path("microstate_templates", ext="png", branch="main"),
        )
    group_path = cfg.cache_path("stats", "group_effects", ext="parquet", branch="hfa")
    if group_path.exists():
        outputs["group_heatmap"] = plot_group_effects_heatmap(
            read_dataframe(group_path),
            cfg.report_path("group_effects", ext="png", branch="hfa"),
        )
    subject_path = cfg.cache_path("coupling", "subject_effects", ext="parquet", branch="hfa")
    if subject_path.exists() and group_path.exists():
        table_reports = _write_table_reports_from_paths(
            cfg,
            {
                "hfa_subject_effects": subject_path,
                "hfa_group_effects": group_path,
            },
            branch="hfa",
        )
        outputs["hfa_subject_effects_excel"] = table_reports["hfa_subject_effects"]
        outputs["hfa_group_effects_excel"] = table_reports["hfa_group_effects"]
    cross_modal_path = cfg.cache_path("coupling", "cross_modal_summary", ext="parquet", branch="band_1_40")
    if cross_modal_path.exists():
        outputs["cross_modal"] = plot_cross_modal_overlap(
            read_dataframe(cross_modal_path),
            cfg.report_path("cross_modal_overlap", ext="png", branch="band_1_40"),
        )
    contingency_path = cfg.cache_path("coupling", "cross_modal_contingency", ext="parquet", branch="band_1_40")
    if contingency_path.exists() and cross_modal_path.exists():
        table_reports = _write_table_reports_from_paths(
            cfg,
            {
                "cross_modal_contingency": contingency_path,
                "cross_modal_summary": cross_modal_path,
            },
            branch="band_1_40",
        )
        outputs["cross_modal_contingency_excel"] = table_reports["cross_modal_contingency"]
        outputs["cross_modal_summary_excel"] = table_reports["cross_modal_summary"]
    for method in ("corr", "plv", "wpli"):
        branch = connectivity_analysis_branch(method)
        connectivity_path = cfg.cache_path("stats", "group_connectivity_effects", ext="parquet", branch=branch)
        if connectivity_path.exists():
            outputs[f"band_connectivity_{method}"] = plot_connectivity_effect_matrices(
                read_dataframe(connectivity_path),
                cfg.report_path(f"band_connectivity_effects_{method}", ext="png", branch=branch),
                title=f"Band-limited connectivity effects ({method.upper()})",
            )
        subject_path = cfg.cache_path("coupling", "subject_connectivity_effects", ext="parquet", branch=branch)
        if subject_path.exists() and connectivity_path.exists():
            table_reports = _write_table_reports_from_paths(
                cfg,
                {
                    "subject_connectivity_effects": subject_path,
                    "group_connectivity_effects": connectivity_path,
                },
                branch=branch,
            )
            outputs[f"band_connectivity_{method}_subject_excel"] = table_reports["subject_connectivity_effects"]
            outputs[f"band_connectivity_{method}_group_excel"] = table_reports["group_connectivity_effects"]
    return outputs
