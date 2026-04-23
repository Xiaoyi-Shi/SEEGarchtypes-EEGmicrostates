from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from seeg_eegmicrostates._utils import ensure_directory, read_dataframe, write_csv_dataframe, write_dataframe, write_excel_dataframe
from seeg_eegmicrostates.config import AnalysisConfig, DEFAULT_ANALYSIS_STATE, YEO17_PARCELLATION_NAME
from seeg_eegmicrostates.coupling import (
    DEFAULT_FIELD_STATE_NORMALIZATION,
    DEFAULT_FIELD_STATE_PEAK_METRIC,
    align_eeg_and_field_state_labels,
    normalize_field_normalization,
    normalize_field_peak_metric,
)
from seeg_eegmicrostates.coupling.field_state import (
    _absolute_similarity,
    _field_template_channel_columns,
    _map_patterns,
    _normalize_channels,
    _smooth_short_runs,
)
from seeg_eegmicrostates.eeg import (
    build_eeg_gfp_trace,
    label_microstates,
    load_microstate_model,
    preprocess_eeg_recording,
    validate_microstate_model_channels,
)
from seeg_eegmicrostates.io import load_workbook_tables, scan_seizure_repository
from seeg_eegmicrostates.seeg import load_and_crop_bipolar_seeg
from seeg_eegmicrostates.segment import build_seizure_stage_segments, seizure_recording_states
from seeg_eegmicrostates.stats import (
    SEIZURE_IDENTIFIER_COLUMNS,
    patient_level_mean,
    summarize_eeg_gfp_by_microstate,
    summarize_paired_state_relationships,
    summarize_stage_denominators,
    summarize_stage_state_metrics,
    summarize_stage_transition_metrics,
)

from .core import _all_exist
from .shared import (
    _FIELD_ARCHETYPE_ASSIGNMENTS_STEM,
    _FIELD_ARCHETYPE_TEMPLATES_STEM,
    _FIELD_STATE_LABELS_STEM,
    _FIELD_STATE_TEMPLATES_STEM,
    _exploratory_branch,
    _retained_field_state_artifact_branch,
    _resolve_field_min_duration_ms,
    _resolve_field_state_count,
)


_SEIZURE_BRANCH = "seizure_stage"
_SEIZURE_SEGMENT_STEM = "seizure_stage_segments"
_SEIZURE_RECORDING_INDEX_STEM = "seizure_recording_index"
_SEIZURE_SEGMENT_QC_STEM = "seizure_stage_segment_qc"
_SEIZURE_ELIGIBILITY_QC_STEM = "seizure_stage_eligibility_qc"
_SEIZURE_PROCESSING_QC_STEM = "seizure_stage_processing_qc"
_EEG_STAGE_LABELS_STEM = "seizure_stage_eeg_microstate_labels"
_EEG_STAGE_GFP_STEM = "seizure_stage_eeg_gfp_trace"
_SEEG_STAGE_LABELS_STEM = "seizure_stage_seeg_archetype_labels"
_PAIRED_STAGE_LABELS_STEM = "seizure_stage_paired_labels"
_EEG_STAGE_METRICS_STEM = "seizure_stage_eeg_microstate_metrics"
_EEG_STAGE_TRANSITIONS_STEM = "seizure_stage_eeg_microstate_transitions"
_EEG_STAGE_GFP_METRICS_STEM = "seizure_stage_eeg_gfp_metrics"
_SEEG_FIELD_STAGE_METRICS_STEM = "seizure_stage_seeg_field_state_metrics"
_SEEG_ARCHETYPE_STAGE_METRICS_STEM = "seizure_stage_seeg_archetype_metrics"
_SEEG_STAGE_TRANSITIONS_STEM = "seizure_stage_seeg_archetype_transitions"
_SEEG_STAGE_LOADING_STEM = "seizure_stage_yeo_loading_metrics"
_PAIRED_STAGE_RELATIONSHIP_STEM = "seizure_stage_eeg_seeg_relationship_metrics"
_PATIENT_EEG_STAGE_METRICS_STEM = "patient_seizure_stage_eeg_microstate_metrics"
_PATIENT_SEEG_STAGE_METRICS_STEM = "patient_seizure_stage_seeg_archetype_metrics"
_PATIENT_RELATIONSHIP_STAGE_STEM = "patient_seizure_stage_eeg_seeg_relationship_metrics"
_SEIZURE_DENOMINATOR_STEM = "seizure_stage_denominators"
_SEIZURE_MANIFEST_STEM = "seizure_stage_manifest"


def _seizure_cache_path(cfg: AnalysisConfig, category: str, stem: str, *, ext: str = "parquet") -> Path:
    return cfg.cache_path(category, stem, ext=ext, branch=_SEIZURE_BRANCH)


def _existing_or_latest(path: Path, *, stem: str, branch: str, ext: str = "parquet") -> Path:
    if path.exists():
        return path
    pattern = f"{stem}_{branch}_*.{ext.lstrip('.')}"
    matches = sorted(path.parent.glob(pattern), key=lambda candidate: candidate.stat().st_mtime, reverse=True)
    return matches[0] if matches else path


def _segment_id(row: pd.Series | dict[str, object]) -> str:
    return f"{row['patient_id']}_{row['recording_state']}_{row['stage']}"


def _identifier_payload(row: pd.Series | dict[str, object]) -> dict[str, object]:
    return {
        "patient_id": str(row["patient_id"]),
        "seizure_id": str(row["seizure_id"]),
        "seizure_type": str(row["seizure_type"]),
        "recording_state": str(row["recording_state"]),
        "stage": str(row["stage"]),
        "stage_order": int(row["stage_order"]),
        "segment_id": _segment_id(row),
    }


def _add_identifiers(df: pd.DataFrame, row: pd.Series | dict[str, object]) -> pd.DataFrame:
    identifiers = _identifier_payload(row)
    result = df.copy()
    for key, value in reversed(list(identifiers.items())):
        if key in result.columns:
            result[key] = value
        else:
            result.insert(0, key, value)
    return result


def build_seizure_stage_index_artifacts(cfg: AnalysisConfig) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    _, annotation_info = load_workbook_tables(cfg.workbook_path)
    segments = build_seizure_stage_segments(annotation_info)
    recordings = seizure_recording_states(segments)
    recording_index = scan_seizure_repository(cfg.data_root, recordings)
    segment_qc = segments[~segments["usable_segment"] | (segments["qc_reason"] != "ok")].copy()
    eligibility_qc = recording_index[
        ~recording_index["eligible_seeg_stage"] | ~recording_index["eligible_paired_eeg_seeg"]
    ].copy()
    denominators = summarize_stage_denominators(segments=segments, recording_index=recording_index)
    outputs = {
        "segments": write_dataframe(segments, _seizure_cache_path(cfg, "segments", _SEIZURE_SEGMENT_STEM)),
        "recording_index": write_dataframe(recording_index, _seizure_cache_path(cfg, "index", _SEIZURE_RECORDING_INDEX_STEM)),
        "segment_qc": write_dataframe(segment_qc, _seizure_cache_path(cfg, "segments", _SEIZURE_SEGMENT_QC_STEM)),
        "eligibility_qc": write_dataframe(eligibility_qc, _seizure_cache_path(cfg, "index", _SEIZURE_ELIGIBILITY_QC_STEM)),
        "denominators": write_dataframe(denominators, _seizure_cache_path(cfg, "stats", _SEIZURE_DENOMINATOR_STEM)),
    }
    return outputs


def _load_seizure_stage_index(cfg: AnalysisConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    segment_path = _seizure_cache_path(cfg, "segments", _SEIZURE_SEGMENT_STEM)
    index_path = _seizure_cache_path(cfg, "index", _SEIZURE_RECORDING_INDEX_STEM)
    if not segment_path.exists() or not index_path.exists():
        build_seizure_stage_index_artifacts(cfg)
    return read_dataframe(segment_path), read_dataframe(index_path)


def _reference_cfg(cfg: AnalysisConfig) -> AnalysisConfig:
    return replace(cfg, analysis_state=DEFAULT_ANALYSIS_STATE)


def _field_archetype_branch(cfg: AnalysisConfig) -> str:
    state_count = _resolve_field_state_count(None, cfg)
    min_duration_ms = _resolve_field_min_duration_ms(None, cfg)
    return _exploratory_branch(
        cfg,
        "field-state-archetypes",
        params={
            "peak_metric": DEFAULT_FIELD_STATE_PEAK_METRIC,
            "normalization": DEFAULT_FIELD_STATE_NORMALIZATION,
            "state_count": state_count,
            "min_duration_ms": min_duration_ms,
            "comparison_space": YEO17_PARCELLATION_NAME,
            "min_subjects": cfg.min_group_subjects,
        },
    )


def _fixed_reference_paths(cfg: AnalysisConfig, *, eeg_template_fif: str | Path | None = None) -> dict[str, Path]:
    ref_cfg = _reference_cfg(cfg)
    field_branch = _retained_field_state_artifact_branch(ref_cfg)
    archetype_branch = _field_archetype_branch(ref_cfg)
    field_templates = ref_cfg.cache_path("coupling", _FIELD_STATE_TEMPLATES_STEM, ext="parquet", branch=field_branch)
    field_labels = ref_cfg.cache_path("coupling", _FIELD_STATE_LABELS_STEM, ext="parquet", branch=field_branch)
    archetype_assignments = ref_cfg.cache_path("coupling", _FIELD_ARCHETYPE_ASSIGNMENTS_STEM, ext="parquet", branch=archetype_branch)
    archetypes = ref_cfg.cache_path("coupling", _FIELD_ARCHETYPE_TEMPLATES_STEM, ext="parquet", branch=archetype_branch)
    return {
        "eeg_template": Path(eeg_template_fif) if eeg_template_fif is not None else ref_cfg.default_eeg_template_fif,
        "field_templates": _existing_or_latest(field_templates, stem=_FIELD_STATE_TEMPLATES_STEM, branch=field_branch),
        "field_labels_reference": _existing_or_latest(field_labels, stem=_FIELD_STATE_LABELS_STEM, branch=field_branch),
        "archetype_assignments": _existing_or_latest(
            archetype_assignments,
            stem=_FIELD_ARCHETYPE_ASSIGNMENTS_STEM,
            branch=archetype_branch,
        ),
        "archetypes": _existing_or_latest(archetypes, stem=_FIELD_ARCHETYPE_TEMPLATES_STEM, branch=archetype_branch),
    }


def _require_fixed_references(paths: dict[str, Path]) -> None:
    missing = {name: path for name, path in paths.items() if name != "field_labels_reference" and not path.exists()}
    if missing:
        details = "\n".join(f"- {name}: {path}" for name, path in missing.items())
        raise FileNotFoundError(
            "Missing fixed IDE_A reference artifacts required for seizure-stage projection.\n"
            "Run the retained IDE_A EEG state and SEEG field-state/archetype workflow first, or pass --template-fif for EEG.\n"
            f"{details}"
        )


def _seeg_label_columns() -> list[str]:
    return [
        *SEIZURE_IDENTIFIER_COLUMNS,
        "time_sec",
        "sample",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "field_state",
        "corr",
        "assigned_archetype",
        "assignment_similarity",
    ]


def _sample_period_sec(times: np.ndarray) -> float:
    if times.size < 2:
        return 0.0
    return float(np.median(np.diff(times.astype(float))))


def _label_seeg_with_fixed_templates(
    channel_df: pd.DataFrame,
    patient_templates: pd.DataFrame,
    *,
    patient_id: str,
    cfg: AnalysisConfig,
) -> pd.DataFrame:
    columns = [
        "patient_id",
        "time_sec",
        "sample",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "field_state",
        "corr",
    ]
    if channel_df.empty or patient_templates.empty:
        return pd.DataFrame(columns=columns)
    template_columns = [column for column in _field_template_channel_columns(patient_templates) if column in channel_df.columns]
    if len(template_columns) < 2:
        return pd.DataFrame(columns=columns)
    values = channel_df[template_columns].to_numpy(dtype=float)
    valid = np.isfinite(values).any(axis=0) & (np.nanstd(values, axis=0, ddof=0) > 0.0)
    selected_columns = [column for column, is_valid in zip(template_columns, valid, strict=False) if is_valid]
    if len(selected_columns) < 2:
        return pd.DataFrame(columns=columns)
    ordered_templates = patient_templates.sort_values("field_state").reset_index(drop=True)
    normalized_metric = normalize_field_peak_metric(str(ordered_templates["peak_metric"].iloc[0]))
    normalized_strategy = normalize_field_normalization(str(ordered_templates["normalization"].iloc[0]))
    min_duration_ms = int(ordered_templates["min_duration_ms"].iloc[0])
    state_count = int(ordered_templates["n_states"].iloc[0])
    normalized_values = _normalize_channels(channel_df[selected_columns].to_numpy(dtype=float), normalized_strategy)
    patterns = _map_patterns(normalized_values)
    template_patterns = _map_patterns(ordered_templates[selected_columns].fillna(0.0).to_numpy(dtype=float))
    similarity = _absolute_similarity(patterns, template_patterns)
    if similarity.size == 0:
        return pd.DataFrame(columns=columns)
    labels = np.argmax(similarity, axis=1).astype(int)
    sample_period = _sample_period_sec(channel_df["time_sec"].to_numpy(dtype=float))
    min_samples = max(1, int(round(min_duration_ms / 1000.0 / sample_period))) if sample_period > 0.0 else 1
    labels = _smooth_short_runs(labels, similarity, min_samples)
    scores = similarity[np.arange(similarity.shape[0]), labels]
    return pd.DataFrame(
        {
            "patient_id": patient_id,
            "time_sec": channel_df["time_sec"].to_numpy(dtype=float),
            "sample": np.arange(channel_df.shape[0], dtype=int),
            "peak_metric": normalized_metric,
            "normalization": normalized_strategy,
            "n_states": state_count,
            "min_duration_ms": min_duration_ms,
            "field_state": labels.astype(int),
            "corr": scores.astype(float),
        },
        columns=columns,
    )


def _attach_archetype_assignments(label_df: pd.DataFrame, assignment_df: pd.DataFrame, *, patient_id: str) -> pd.DataFrame:
    if label_df.empty:
        return label_df.assign(assigned_archetype=pd.Series(dtype="Int64"), assignment_similarity=pd.Series(dtype=float))
    patient_assignments = assignment_df[assignment_df["patient_id"].astype(str) == str(patient_id)]
    if patient_assignments.empty:
        result = label_df.copy()
        result["assigned_archetype"] = result["field_state"].astype(int)
        result["assignment_similarity"] = np.nan
        return result
    mapping = patient_assignments[["field_state", "assigned_archetype", "assignment_similarity"]].drop_duplicates("field_state")
    result = label_df.merge(mapping, on="field_state", how="left")
    result["assigned_archetype"] = result["assigned_archetype"].fillna(result["field_state"]).astype(int)
    return result


def _prepare_segment_table(segments: pd.DataFrame, recording_index: pd.DataFrame) -> pd.DataFrame:
    merged = segments.merge(
        recording_index,
        on=["patient_id", "seizure_id", "seizure_type", "recording_state"],
        how="left",
        suffixes=("", "_asset"),
    )
    return merged[merged["usable_segment"]].copy().sort_values(["patient_id", "recording_state", "stage_order"])


def _process_eeg_stage_segments(
    stage_table: pd.DataFrame,
    *,
    cfg: AnalysisConfig,
    model,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    label_frames: list[pd.DataFrame] = []
    gfp_frames: list[pd.DataFrame] = []
    qc_rows: list[dict[str, object]] = []
    paired = stage_table[stage_table["eligible_paired_eeg_seeg"].fillna(False)].copy()
    for row in paired.to_dict(orient="records"):
        identifiers = _identifier_payload(row)
        try:
            raw19, restored = preprocess_eeg_recording(
                row["eeg_ref_path"],
                start_sec=float(row["start_sec"]),
                end_sec=float(row["end_sec"]),
                cfg=cfg,
                band=cfg.band_limited_range,
            )
            labels = label_microstates(raw19, model, cfg, patient_id=str(row["patient_id"]))
            gfp_trace = build_eeg_gfp_trace(raw19, patient_id=str(row["patient_id"]))
            label_frames.append(_add_identifiers(labels, row))
            gfp_frames.append(_add_identifiers(gfp_trace, row))
            qc_rows.append({**identifiers, "metric_family": "eeg_microstate", "qc_status": "ok", "qc_reason": "ok", "restored_channels": ";".join(restored)})
        except Exception as exc:  # pragma: no cover - exercised in integration with real data
            qc_rows.append(
                {
                    **identifiers,
                    "metric_family": "eeg_microstate",
                    "qc_status": "failed",
                    "qc_reason": f"{type(exc).__name__}: {exc}",
                    "restored_channels": "",
                }
            )
    labels = pd.concat(label_frames, ignore_index=True) if label_frames else pd.DataFrame(columns=[*SEIZURE_IDENTIFIER_COLUMNS, "time_sec", "sample", "microstate", "corr"])
    gfp = pd.concat(gfp_frames, ignore_index=True) if gfp_frames else pd.DataFrame(columns=[*SEIZURE_IDENTIFIER_COLUMNS, "time_sec", "sample", "gfp"])
    qc = pd.DataFrame(qc_rows)
    return labels, gfp, qc


def _process_seeg_stage_segments(
    stage_table: pd.DataFrame,
    *,
    cfg: AnalysisConfig,
    field_templates: pd.DataFrame,
    archetype_assignments: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    label_frames: list[pd.DataFrame] = []
    qc_rows: list[dict[str, object]] = []
    seeg_rows = stage_table[stage_table["eligible_seeg_stage"].fillna(False)].copy()
    for row in seeg_rows.to_dict(orient="records"):
        identifiers = _identifier_payload(row)
        patient_id = str(row["patient_id"])
        patient_templates = field_templates[field_templates["patient_id"].astype(str) == patient_id]
        if patient_templates.empty:
            qc_rows.append({**identifiers, "metric_family": "seeg_archetype", "qc_status": "failed", "qc_reason": "missing_patient_field_templates"})
            continue
        try:
            raw_bp = load_and_crop_bipolar_seeg(row["seeg_bipolar_path"], float(row["start_sec"]), float(row["end_sec"]))
            band = raw_bp.copy()
            band.filter(cfg.band_limited_range[0], cfg.band_limited_range[1], verbose="ERROR")
            band.resample(cfg.seeg_resample_hz, verbose="ERROR")
            channel_df = pd.DataFrame(band.get_data().T, columns=band.ch_names)
            channel_df.insert(0, "time_sec", band.times.astype(float))
            labels = _label_seeg_with_fixed_templates(channel_df, patient_templates, patient_id=patient_id, cfg=cfg)
            labels = _attach_archetype_assignments(labels, archetype_assignments, patient_id=patient_id)
            label_frames.append(_add_identifiers(labels, row))
            qc_rows.append({**identifiers, "metric_family": "seeg_archetype", "qc_status": "ok", "qc_reason": "ok"})
        except Exception as exc:  # pragma: no cover - exercised in integration with real data
            qc_rows.append({**identifiers, "metric_family": "seeg_archetype", "qc_status": "failed", "qc_reason": f"{type(exc).__name__}: {exc}"})
    labels = pd.concat(label_frames, ignore_index=True) if label_frames else pd.DataFrame(columns=_seeg_label_columns())
    qc = pd.DataFrame(qc_rows)
    return labels, qc


def _align_stage_labels(eeg_labels: pd.DataFrame, seeg_labels: pd.DataFrame) -> pd.DataFrame:
    columns = [
        *SEIZURE_IDENTIFIER_COLUMNS,
        "time_sec",
        "microstate",
        "corr",
        "field_state",
        "field_corr",
        "sample",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "assigned_archetype",
        "assignment_similarity",
    ]
    if eeg_labels.empty or seeg_labels.empty:
        return pd.DataFrame(columns=columns)
    frames: list[pd.DataFrame] = []
    for segment_id, eeg_group in eeg_labels.groupby("segment_id", sort=True):
        seeg_group = seeg_labels[seeg_labels["segment_id"] == segment_id]
        if seeg_group.empty:
            continue
        identifiers = {column: eeg_group[column].iloc[0] for column in SEIZURE_IDENTIFIER_COLUMNS}
        aligned = align_eeg_and_field_state_labels(
            eeg_group[["time_sec", "microstate", "corr"]].copy(),
            seeg_group[["time_sec", "field_state", "corr", "sample", "peak_metric", "normalization", "n_states", "min_duration_ms"]].copy(),
            patient_id=str(identifiers["patient_id"]),
        )
        if aligned.empty:
            continue
        archetype_lookup = seeg_group[["field_state", "assigned_archetype", "assignment_similarity"]].drop_duplicates(
            "field_state"
        )
        aligned = aligned.merge(archetype_lookup, on="field_state", how="left")
        for key, value in reversed(list(identifiers.items())):
            if key in aligned.columns:
                aligned[key] = value
            else:
                aligned.insert(0, key, value)
        frames.append(aligned)
    return pd.concat(frames, ignore_index=True)[columns] if frames else pd.DataFrame(columns=columns)


def _build_loading_metrics(archetype_metrics: pd.DataFrame, archetypes: pd.DataFrame) -> pd.DataFrame:
    columns = [
        *SEIZURE_IDENTIFIER_COLUMNS,
        "assigned_archetype",
        "network",
        "occupancy",
        "loading_value",
        "weighted_loading",
    ]
    if archetype_metrics.empty or archetypes.empty:
        return pd.DataFrame(columns=columns)
    network_columns = _field_template_channel_columns(archetypes)
    if not network_columns:
        return pd.DataFrame(columns=columns)
    template_rows = archetypes.rename(columns={"field_state": "assigned_archetype"}).copy()
    rows: list[dict[str, object]] = []
    for metric in archetype_metrics.to_dict(orient="records"):
        archetype = int(metric["assigned_archetype"])
        template = template_rows[template_rows["assigned_archetype"].astype(int) == archetype]
        if template.empty:
            continue
        template_row = template.iloc[0]
        for network in network_columns:
            loading = float(template_row[network])
            rows.append(
                {
                    **{column: metric[column] for column in SEIZURE_IDENTIFIER_COLUMNS},
                    "assigned_archetype": archetype,
                    "network": str(network),
                    "occupancy": float(metric["occupancy"]),
                    "loading_value": loading,
                    "weighted_loading": float(metric["occupancy"]) * loading,
                }
            )
    return pd.DataFrame(rows, columns=columns)


def _analysis_cache_paths(cfg: AnalysisConfig) -> dict[str, Path]:
    return {
        "eeg_labels": _seizure_cache_path(cfg, "eeg", _EEG_STAGE_LABELS_STEM),
        "eeg_gfp_trace": _seizure_cache_path(cfg, "eeg", _EEG_STAGE_GFP_STEM),
        "seeg_labels": _seizure_cache_path(cfg, "seeg", _SEEG_STAGE_LABELS_STEM),
        "paired_labels": _seizure_cache_path(cfg, "coupling", _PAIRED_STAGE_LABELS_STEM),
        "eeg_microstate_metrics": _seizure_cache_path(cfg, "eeg", _EEG_STAGE_METRICS_STEM),
        "eeg_microstate_transitions": _seizure_cache_path(cfg, "eeg", _EEG_STAGE_TRANSITIONS_STEM),
        "eeg_gfp_metrics": _seizure_cache_path(cfg, "eeg", _EEG_STAGE_GFP_METRICS_STEM),
        "seeg_field_state_metrics": _seizure_cache_path(cfg, "seeg", _SEEG_FIELD_STAGE_METRICS_STEM),
        "seeg_archetype_metrics": _seizure_cache_path(cfg, "seeg", _SEEG_ARCHETYPE_STAGE_METRICS_STEM),
        "seeg_archetype_transitions": _seizure_cache_path(cfg, "seeg", _SEEG_STAGE_TRANSITIONS_STEM),
        "seeg_yeo_loading_metrics": _seizure_cache_path(cfg, "seeg", _SEEG_STAGE_LOADING_STEM),
        "relationship_metrics": _seizure_cache_path(cfg, "coupling", _PAIRED_STAGE_RELATIONSHIP_STEM),
        "patient_eeg_metrics": _seizure_cache_path(cfg, "stats", _PATIENT_EEG_STAGE_METRICS_STEM),
        "patient_seeg_metrics": _seizure_cache_path(cfg, "stats", _PATIENT_SEEG_STAGE_METRICS_STEM),
        "patient_relationship_metrics": _seizure_cache_path(cfg, "stats", _PATIENT_RELATIONSHIP_STAGE_STEM),
        "processing_qc": _seizure_cache_path(cfg, "stats", _SEIZURE_PROCESSING_QC_STEM),
    }


def run_seizure_stage_analysis(
    cfg: AnalysisConfig,
    *,
    template_fif: str | Path | None = None,
) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    index_outputs = build_seizure_stage_index_artifacts(cfg)
    paths = _analysis_cache_paths(cfg)
    if _all_exist(paths):
        return {**index_outputs, **paths}
    reference_paths = _fixed_reference_paths(cfg, eeg_template_fif=template_fif)
    _require_fixed_references(reference_paths)
    model = load_microstate_model(reference_paths["eeg_template"])
    validate_microstate_model_channels(model, cfg.target19_channels, alternate_channels=cfg.standard11_channels)
    field_templates = read_dataframe(reference_paths["field_templates"])
    archetype_assignments = read_dataframe(reference_paths["archetype_assignments"])
    archetypes = read_dataframe(reference_paths["archetypes"])
    segments, recording_index = _load_seizure_stage_index(cfg)
    stage_table = _prepare_segment_table(segments, recording_index)

    reusable_label_paths = {
        "eeg_labels": paths["eeg_labels"],
        "eeg_gfp_trace": paths["eeg_gfp_trace"],
        "seeg_labels": paths["seeg_labels"],
        "processing_qc": paths["processing_qc"],
    }
    if _all_exist(reusable_label_paths):
        eeg_labels = read_dataframe(paths["eeg_labels"])
        eeg_gfp_trace = read_dataframe(paths["eeg_gfp_trace"])
        seeg_labels = read_dataframe(paths["seeg_labels"])
        processing_qc = read_dataframe(paths["processing_qc"])
    else:
        eeg_labels, eeg_gfp_trace, eeg_qc = _process_eeg_stage_segments(stage_table, cfg=cfg, model=model)
        seeg_labels, seeg_qc = _process_seeg_stage_segments(
            stage_table,
            cfg=cfg,
            field_templates=field_templates,
            archetype_assignments=archetype_assignments,
        )
        processing_qc = pd.concat([eeg_qc, seeg_qc], ignore_index=True) if not eeg_qc.empty or not seeg_qc.empty else pd.DataFrame()
        write_dataframe(eeg_labels, paths["eeg_labels"])
        write_dataframe(eeg_gfp_trace, paths["eeg_gfp_trace"])
        write_dataframe(seeg_labels, paths["seeg_labels"])
        write_dataframe(processing_qc, paths["processing_qc"])
    paired_labels = _align_stage_labels(eeg_labels, seeg_labels)

    eeg_metrics = summarize_stage_state_metrics(
        eeg_labels,
        state_column="microstate",
        metric_family="eeg_microstate",
        state_output_column="microstate",
    )
    eeg_transitions = summarize_stage_transition_metrics(eeg_labels, state_column="microstate", metric_family="eeg_microstate")
    eeg_gfp_metrics = summarize_eeg_gfp_by_microstate(eeg_labels, eeg_gfp_trace)
    seeg_field_metrics = summarize_stage_state_metrics(
        seeg_labels,
        state_column="field_state",
        metric_family="seeg_field_state",
        state_output_column="field_state",
    )
    seeg_archetype_metrics = summarize_stage_state_metrics(
        seeg_labels,
        state_column="assigned_archetype",
        metric_family="seeg_archetype",
        state_output_column="assigned_archetype",
    )
    seeg_transitions = summarize_stage_transition_metrics(
        seeg_labels,
        state_column="assigned_archetype",
        metric_family="seeg_archetype",
    )
    loading_metrics = _build_loading_metrics(seeg_archetype_metrics, archetypes)
    relationship_metrics = summarize_paired_state_relationships(paired_labels, field_column="assigned_archetype")
    patient_eeg_metrics = patient_level_mean(
        eeg_metrics,
        value_columns=["occupancy", "mean_dwell_sec", "occurrence_per_min", "mean_confidence"],
        extra_keys=["stage", "stage_order", "microstate"],
    )
    patient_seeg_metrics = patient_level_mean(
        seeg_archetype_metrics,
        value_columns=["occupancy", "mean_dwell_sec", "occurrence_per_min", "mean_confidence"],
        extra_keys=["stage", "stage_order", "assigned_archetype"],
    )
    patient_relationship_metrics = patient_level_mean(
        relationship_metrics,
        value_columns=["joint_probability", "p_microstate_given_field", "p_field_given_microstate"],
        extra_keys=["stage", "stage_order", "field_state", "microstate"],
    )

    outputs = {
        "eeg_labels": write_dataframe(eeg_labels, paths["eeg_labels"]),
        "eeg_gfp_trace": write_dataframe(eeg_gfp_trace, paths["eeg_gfp_trace"]),
        "seeg_labels": write_dataframe(seeg_labels, paths["seeg_labels"]),
        "paired_labels": write_dataframe(paired_labels, paths["paired_labels"]),
        "eeg_microstate_metrics": write_dataframe(eeg_metrics, paths["eeg_microstate_metrics"]),
        "eeg_microstate_transitions": write_dataframe(eeg_transitions, paths["eeg_microstate_transitions"]),
        "eeg_gfp_metrics": write_dataframe(eeg_gfp_metrics, paths["eeg_gfp_metrics"]),
        "seeg_field_state_metrics": write_dataframe(seeg_field_metrics, paths["seeg_field_state_metrics"]),
        "seeg_archetype_metrics": write_dataframe(seeg_archetype_metrics, paths["seeg_archetype_metrics"]),
        "seeg_archetype_transitions": write_dataframe(seeg_transitions, paths["seeg_archetype_transitions"]),
        "seeg_yeo_loading_metrics": write_dataframe(loading_metrics, paths["seeg_yeo_loading_metrics"]),
        "relationship_metrics": write_dataframe(relationship_metrics, paths["relationship_metrics"]),
        "patient_eeg_metrics": write_dataframe(patient_eeg_metrics, paths["patient_eeg_metrics"]),
        "patient_seeg_metrics": write_dataframe(patient_seeg_metrics, paths["patient_seeg_metrics"]),
        "patient_relationship_metrics": write_dataframe(patient_relationship_metrics, paths["patient_relationship_metrics"]),
        "processing_qc": write_dataframe(processing_qc, paths["processing_qc"]),
    }
    return {**index_outputs, **outputs}


def _exportable_seizure_tables(cfg: AnalysisConfig) -> dict[str, Path]:
    index_paths = {
        "segments": _seizure_cache_path(cfg, "segments", _SEIZURE_SEGMENT_STEM),
        "recording_index": _seizure_cache_path(cfg, "index", _SEIZURE_RECORDING_INDEX_STEM),
        "segment_qc": _seizure_cache_path(cfg, "segments", _SEIZURE_SEGMENT_QC_STEM),
        "eligibility_qc": _seizure_cache_path(cfg, "index", _SEIZURE_ELIGIBILITY_QC_STEM),
        "denominators": _seizure_cache_path(cfg, "stats", _SEIZURE_DENOMINATOR_STEM),
    }
    return {**index_paths, **_analysis_cache_paths(cfg)}


def export_seizure_stage_tables(cfg: AnalysisConfig) -> dict[str, Path]:
    cfg.ensure_runtime_directories()
    if not _seizure_cache_path(cfg, "segments", _SEIZURE_SEGMENT_STEM).exists():
        build_seizure_stage_index_artifacts(cfg)
    manual_dir = ensure_directory(cfg.artifact_root / "manual" / "seizure_stage_trajectory")
    outputs: dict[str, Path] = {}
    manifest_rows: list[dict[str, object]] = []
    excel_row_limit = 1_048_576
    for stem, source_path in _exportable_seizure_tables(cfg).items():
        if not source_path.exists():
            continue
        table = read_dataframe(source_path)
        csv_path = manual_dir / f"{stem}.csv"
        xlsx_path = cfg.report_path(stem, ext="xlsx", subdir="seizure_stage_tables", branch=_SEIZURE_BRANCH)
        outputs[f"{stem}_csv"] = write_csv_dataframe(table, csv_path)
        xlsx_status = "written"
        xlsx_output = str(xlsx_path)
        if table.shape[0] > excel_row_limit:
            xlsx_status = "skipped_too_many_rows"
            xlsx_output = ""
        else:
            outputs[f"{stem}_xlsx"] = write_excel_dataframe(table, xlsx_path)
        manifest_rows.append(
            {
                "table": stem,
                "rows": int(table.shape[0]),
                "columns": int(table.shape[1]),
                "csv_path": str(csv_path),
                "xlsx_path": xlsx_output,
                "xlsx_status": xlsx_status,
                "source_path": str(source_path),
            }
        )
    manifest = pd.DataFrame(manifest_rows)
    manifest_csv = manual_dir / f"{_SEIZURE_MANIFEST_STEM}.csv"
    manifest_xlsx = cfg.report_path(_SEIZURE_MANIFEST_STEM, ext="xlsx", subdir="seizure_stage_tables", branch=_SEIZURE_BRANCH)
    outputs["manifest_csv"] = write_csv_dataframe(manifest, manifest_csv)
    outputs["manifest_xlsx"] = write_excel_dataframe(manifest, manifest_xlsx)
    return outputs
