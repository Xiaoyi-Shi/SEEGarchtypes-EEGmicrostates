from __future__ import annotations

import argparse
from datetime import datetime
import traceback

from seeg_eegmicrostates.config import (
    AnalysisConfig,
    DEFAULT_ANALYSIS_STATE,
    DEFAULT_DIRECT_TRANSITION_WINDOW_SEC,
    SEEG_PARCELLATION_COLUMN,
    SEEG_PARCELLATION_NAME,
    SUPPORTED_ANALYSIS_STATES,
)
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
    SUPPORTED_FIELD_ARCHETYPE_SPACES,
    SUPPORTED_GFP_GLOBAL_METRICS,
    SUPPORTED_GFP_GLOBAL_WEIGHTINGS,
)
from seeg_eegmicrostates.workflows import (
    build_index_artifacts,
    build_seizure_stage_index_artifacts,
    export_seizure_stage_tables,
    export_paper_tables,
    run_eeg_states_stage,
    run_exploratory_coupling_stage,
    run_seizure_stage_analysis,
    run_seeg_regions_stage,
)


_EXPLORATORY_ANALYSIS_CHOICES = (
    "field-state-coupling",
    "field-state-model-order-evaluation",
    "field-state-archetypes",
    "archetype-conditioned-eeg-topography",
    "fine-lag-field-state-coupling",
    "gfp-global-coupling",
    "peak-gfp-global-coupling",
    "gfp-controlled-microstate",
    "gfp-controlled-transition",
    "field-state-to-eeg-switching",
    "gfp-controlled-field-state-to-eeg-switching",
)


def build_parser() -> argparse.ArgumentParser:
    state_parent = argparse.ArgumentParser(add_help=False)
    state_parent.add_argument(
        "--analysis-state",
        default=DEFAULT_ANALYSIS_STATE,
        choices=list(SUPPORTED_ANALYSIS_STATES),
        help="Select which IDE segment to analyze. Defaults to IDE_A.",
    )
    state_parent.add_argument(
        "--run-id",
        default=None,
        help="Optional shared run directory name. Reuse the same value across staged commands to collect logs and reports under one artifacts/runs/<run-id>/ folder.",
    )
    parcellation_parent = argparse.ArgumentParser(add_help=False)
    parcellation_parent.add_argument(
        "--seeg-parcellation-name",
        default=SEEG_PARCELLATION_NAME,
        help="SEEG parcellation backend name. Use 'aal3', 'yeo7', 'yeo17', or provide a custom label.",
    )
    parcellation_parent.add_argument(
        "--seeg-parcellation-column",
        default=SEEG_PARCELLATION_COLUMN,
        help="Atlas.tsv column used for SEEG parcellation labels.",
    )
    parser = argparse.ArgumentParser(
        prog="seeg-eegmicrostates",
        description="Staged 1-40 Hz EEG/SEEG microstate analysis for configurable IDE segments with default AAL3 SEEG parcellation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    common_parents = [state_parent, parcellation_parent]
    subparsers.add_parser("build-index", parents=common_parents, help="Scan IDE assets and build the eligible cohort index.")
    eeg_parser = subparsers.add_parser("run-eeg-states", parents=common_parents, help="Generate reusable 1-40 Hz EEG microstate states.")
    eeg_parser.add_argument(
        "--template-fif",
        help="Use an external EEG microstate template file. Without this override, the stage uses the configured default template at artifacts/cache/eeg/ModK.fif.",
    )
    subparsers.add_parser("run-seeg-regions", parents=common_parents, help="Generate reusable 1-40 Hz SEEG parcellation signals.")
    exploratory_parser = subparsers.add_parser(
        "run-exploratory-coupling",
        parents=common_parents,
        help="Run the paper-focused SEEG field-state exploratory workflow plus supplementary GFP/global and SEEG-led switching follow-ups.",
    )
    exploratory_parser.add_argument("--analysis", default="all", choices=["all", *_EXPLORATORY_ANALYSIS_CHOICES])
    exploratory_parser.add_argument(
        "--field-peak-metric",
        default=DEFAULT_FIELD_STATE_PEAK_METRIC,
        choices=list(SUPPORTED_FIELD_STATE_PEAK_METRICS),
        help="Peak metric used to define subject-level SEEG global-field-state peak maps.",
    )
    exploratory_parser.add_argument(
        "--field-normalization",
        default=DEFAULT_FIELD_STATE_NORMALIZATION,
        choices=list(SUPPORTED_FIELD_STATE_NORMALIZATIONS),
        help="Channel-wise normalization used before SEEG field-state peak-map clustering.",
    )
    exploratory_parser.add_argument(
        "--field-state-count",
        type=int,
        default=None,
        help="Optional subject-level SEEG field-state count. Defaults to the EEG microstate count.",
    )
    exploratory_parser.add_argument(
        "--field-min-duration-ms",
        type=int,
        default=None,
        help="Minimum duration in milliseconds applied when backfitting continuous SEEG field-state labels.",
    )
    exploratory_parser.add_argument(
        "--field-surrogates",
        type=int,
        default=DEFAULT_FIELD_STATE_SURROGATES,
        help="Number of circular-shift surrogates used by SEEG field-state coupling statistics.",
    )
    exploratory_parser.add_argument(
        "--field-archetype-space",
        default="yeo17",
        choices=list(SUPPORTED_FIELD_ARCHETYPE_SPACES),
        help="Common-space representation used for cross-subject SEEG field-state archetype matching.",
    )
    exploratory_parser.add_argument(
        "--fine-lag-window-ms",
        type=int,
        default=DEFAULT_FINE_FIELD_LAG_WINDOW_MS,
        help="Half-window in milliseconds for native 4 ms fine-lag SEEG field-state coupling around zero lag.",
    )
    exploratory_parser.add_argument(
        "--global-metric",
        default=DEFAULT_GFP_GLOBAL_METRIC,
        choices=[*SUPPORTED_GFP_GLOBAL_METRICS, "all"],
        help="SEEG global metric definition used by GFP-informed exploratory analyses.",
    )
    exploratory_parser.add_argument(
        "--global-weighting",
        default=DEFAULT_GFP_GLOBAL_WEIGHTING,
        choices=[*SUPPORTED_GFP_GLOBAL_WEIGHTINGS, "all"],
        help="Weighting strategy used when aggregating Yeo17 core-network signals into a SEEG global metric for supplementary GFP-informed analyses.",
    )
    exploratory_parser.add_argument(
        "--peak-window-sec",
        type=float,
        default=DEFAULT_GFP_PEAK_WINDOW_SEC,
        help="Half-window size in seconds used by EEG GFP peak-centered SEEG global trajectory analyses.",
    )
    exploratory_parser.add_argument(
        "--transition-window-sec",
        type=float,
        default=DEFAULT_DIRECT_TRANSITION_WINDOW_SEC,
        help="Window size in seconds used by supplementary SEEG-led switching and GFP-controlled transition follow-ups.",
    )
    exploratory_parser.add_argument(
        "--global-surrogates",
        type=int,
        default=DEFAULT_GFP_GLOBAL_SURROGATES,
        help="Number of circular-shift surrogates used by GFP-informed global coupling statistics.",
    )
    exploratory_parser.add_argument(
        "--min-subjects",
        type=int,
        default=None,
        help="Minimum subject support for exploratory group summaries; defaults to the config threshold.",
    )
    subparsers.add_parser(
        "export-paper-tables",
        parents=common_parents,
        help="Export categorized manuscript tables and manifests from staged analysis outputs.",
        description="Export categorized manuscript tables and manifests from staged analysis outputs without rendering figures in Python.",
    )
    seizure_index_parser = subparsers.add_parser(
        "build-seizure-stage-index",
        parents=[parcellation_parent],
        help="Build SZ recording and pre/LVFA/SZ/post stage indexes from workbook annotations.",
        description=(
            "Build a seizure-stage index from workbook-derived SZ*_<type> recordings without using --analysis-state. "
            "Outputs include stage timing QC plus SEEG-only and paired EEG-SEEG eligibility."
        ),
    )
    seizure_index_parser.add_argument(
        "--run-id",
        default=None,
        help="Optional shared run directory name for seizure-stage logs and reports.",
    )
    seizure_analysis_parser = subparsers.add_parser(
        "run-seizure-stage-analysis",
        parents=[parcellation_parent],
        help="Project seizure-stage data into fixed IDE_A EEG microstate and SEEG archetype references.",
        description=(
            "Run the optional seizure-stage trajectory workflow for workbook-derived SZ*_<type> recordings. "
            "This does not replace the IDE_A paper-core workflow and requires fixed IDE_A reference artifacts."
        ),
    )
    seizure_analysis_parser.add_argument(
        "--template-fif",
        help="Use an external EEG microstate template file for seizure-stage EEG projection.",
    )
    seizure_analysis_parser.add_argument(
        "--run-id",
        default=None,
        help="Optional shared run directory name for seizure-stage logs and reports.",
    )
    seizure_export_parser = subparsers.add_parser(
        "export-seizure-stage-tables",
        parents=[parcellation_parent],
        help="Export seizure-stage trajectory tables and manifests for R Markdown rendering.",
        description=(
            "Export seizure-stage R-ready tables from generated caches for R Markdown rendering. "
            "SEEG-only tables can be exported even when paired EEG-SEEG outputs are unavailable."
        ),
    )
    seizure_export_parser.add_argument(
        "--run-id",
        default=None,
        help="Optional shared run directory name for seizure-stage logs and reports.",
    )
    return parser


def _write_command_log(
    cfg: AnalysisConfig,
    *,
    command: str,
    argv: list[str],
    started_at: datetime,
    finished_at: datetime,
    outputs: dict[str, object] | None = None,
    error_text: str | None = None,
) -> None:
    cfg.ensure_runtime_directories()
    status = "failed" if error_text else "completed"
    log_path = cfg.log_path(command)
    lines = [
        f"command: {command}",
        f"argv: {' '.join(argv)}",
        f"status: {status}",
        f"run_timestamp: {cfg.run_timestamp}",
        f"analysis_state: {cfg.analysis_state}",
        f"seeg_parcellation_name: {cfg.seeg_parcellation_name}",
        f"seeg_parcellation_column: {cfg.seeg_parcellation_column}",
        f"run_root: {cfg.run_root}",
        f"cache_root: {cfg.cache_root}",
        f"runtime_hash: {cfg.runtime_hash}",
        f"started_at: {started_at.isoformat(timespec='seconds')}",
        f"finished_at: {finished_at.isoformat(timespec='seconds')}",
        f"duration_sec: {(finished_at - started_at).total_seconds():.3f}",
    ]
    if outputs:
        lines.append("outputs:")
        for key, value in outputs.items():
            lines.append(f"{key}: {value}")
    if error_text:
        lines.append("traceback:")
        lines.append(error_text.rstrip())
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    cfg_kwargs = {
        "analysis_state": getattr(args, "analysis_state", DEFAULT_ANALYSIS_STATE),
        "seeg_parcellation_name": args.seeg_parcellation_name,
        "seeg_parcellation_column": args.seeg_parcellation_column,
    }
    if getattr(args, "run_id", None) is not None:
        cfg_kwargs["run_timestamp"] = args.run_id
    cfg = AnalysisConfig(**cfg_kwargs)
    started_at = datetime.now()
    try:
        if args.command == "build-index":
            outputs = build_index_artifacts(cfg)
        elif args.command == "run-eeg-states":
            outputs = run_eeg_states_stage(cfg, template_fif=args.template_fif)
        elif args.command == "run-seeg-regions":
            outputs = run_seeg_regions_stage(cfg)
        elif args.command == "run-exploratory-coupling":
            outputs = run_exploratory_coupling_stage(
                cfg,
                analysis=args.analysis,
                global_metric=args.global_metric,
                global_weighting=args.global_weighting,
                peak_window_sec=args.peak_window_sec,
                transition_window_sec=args.transition_window_sec,
                field_peak_metric=args.field_peak_metric,
                field_normalization=args.field_normalization,
                field_state_count=args.field_state_count,
                field_min_duration_ms=args.field_min_duration_ms,
                field_archetype_space=args.field_archetype_space,
                field_surrogates=args.field_surrogates,
                fine_lag_window_ms=args.fine_lag_window_ms,
                global_surrogates=args.global_surrogates,
                min_subjects=args.min_subjects,
            )
        elif args.command == "export-paper-tables":
            outputs = export_paper_tables(cfg)
        elif args.command == "build-seizure-stage-index":
            outputs = build_seizure_stage_index_artifacts(cfg)
        elif args.command == "run-seizure-stage-analysis":
            outputs = run_seizure_stage_analysis(cfg, template_fif=args.template_fif)
        elif args.command == "export-seizure-stage-tables":
            outputs = export_seizure_stage_tables(cfg)
        else:
            raise ValueError(f"Unsupported command: {args.command}")
    except Exception:
        _write_command_log(
            cfg,
            command=args.command,
            argv=argv if argv is not None else [],
            started_at=started_at,
            finished_at=datetime.now(),
            error_text=traceback.format_exc(),
        )
        raise
    _write_command_log(
        cfg,
        command=args.command,
        argv=argv if argv is not None else [],
        started_at=started_at,
        finished_at=datetime.now(),
        outputs=outputs,
    )
    for key, value in outputs.items():
        print(f"{key}: {value}")
    print(f"log: {cfg.log_path(args.command)}")
