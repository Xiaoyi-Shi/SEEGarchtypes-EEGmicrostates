from __future__ import annotations

import argparse
from datetime import datetime
import traceback

from seeg_eegmicrostates.config import (
    AnalysisConfig,
    DEFAULT_ANALYSIS_STATE,
    DEFAULT_DIRECT_LAG_STEP_MS,
    DEFAULT_DIRECT_MAX_LAG_MS,
    DEFAULT_DIRECT_STATE_BACKEND,
    DEFAULT_DIRECT_STATE_COMPONENTS,
    DEFAULT_DIRECT_STATE_SURROGATES,
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
    SUPPORTED_DIRECT_STATE_BACKENDS,
    SUPPORTED_GFP_GLOBAL_METRICS,
    SUPPORTED_GFP_GLOBAL_WEIGHTINGS,
)
from seeg_eegmicrostates.workflows import (
    build_index_artifacts,
    render_reports,
    run_activity_effects_stage,
    run_connectivity_effects_stage,
    run_eeg_states_stage,
    run_exploratory_coupling_stage,
    run_seeg_regions_stage,
)


_EXPLORATORY_ANALYSIS_CHOICES = (
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
    subparsers.add_parser("run-activity-effects", parents=common_parents, help="Compute supplemental EEG-state-conditioned SEEG activity effects.")
    connectivity_parser = subparsers.add_parser(
        "run-connectivity-effects",
        parents=common_parents,
        help="Compute primary EEG-state-conditioned SEEG connectivity effects.",
    )
    connectivity_parser.add_argument("--method", default="all", choices=["corr", "plv", "wpli", "all"])
    exploratory_parser = subparsers.add_parser(
        "run-exploratory-coupling",
        parents=common_parents,
        help="Run opt-in exploratory EEG/SEEG region-signal and direct state-coupling analyses from staged EEG labels and staged SEEG parcellation signals.",
    )
    exploratory_parser.add_argument("--analysis", default="all", choices=["all", *_EXPLORATORY_ANALYSIS_CHOICES])
    exploratory_parser.add_argument("--method", default="all", choices=["corr", "plv", "wpli", "all"])
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
        help="Weighting strategy used when aggregating Yeo17 core-network signals into a SEEG global metric.",
    )
    exploratory_parser.add_argument("--event-window-sec", type=float, default=1.0)
    exploratory_parser.add_argument("--window-sec", type=float, default=10.0)
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
        help="Window size in seconds used by transition-conditioned exploratory analyses.",
    )
    exploratory_parser.add_argument(
        "--direct-backend",
        default=DEFAULT_DIRECT_STATE_BACKEND,
        choices=list(SUPPORTED_DIRECT_STATE_BACKENDS),
        help="Reduced-space backend used for direct EEG-SEEG state-coupling analyses.",
    )
    exploratory_parser.add_argument(
        "--direct-state-count",
        type=int,
        default=None,
        help="Optional SEEG state count for direct EEG-SEEG state coupling. Defaults to the EEG microstate count.",
    )
    exploratory_parser.add_argument(
        "--direct-components",
        type=int,
        default=DEFAULT_DIRECT_STATE_COMPONENTS,
        help="Number of reduced SEEG components used by direct EEG-SEEG state coupling.",
    )
    exploratory_parser.add_argument(
        "--max-lag-ms",
        type=int,
        default=DEFAULT_DIRECT_MAX_LAG_MS,
        help="Maximum absolute lag in milliseconds used by lagged direct EEG-SEEG state coupling.",
    )
    exploratory_parser.add_argument(
        "--lag-step-ms",
        type=int,
        default=DEFAULT_DIRECT_LAG_STEP_MS,
        help="Lag step size in milliseconds used by lagged direct EEG-SEEG state coupling.",
    )
    exploratory_parser.add_argument(
        "--direct-surrogates",
        type=int,
        default=DEFAULT_DIRECT_STATE_SURROGATES,
        help="Number of circular-shift surrogates used by direct EEG-SEEG state coupling statistics.",
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
    subparsers.add_parser("render-reports", parents=common_parents, help="Render figures and Excel tables from staged analysis outputs.")
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
        "analysis_state": args.analysis_state,
        "seeg_parcellation_name": args.seeg_parcellation_name,
        "seeg_parcellation_column": args.seeg_parcellation_column,
    }
    if args.run_id is not None:
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
        elif args.command == "run-activity-effects":
            outputs = run_activity_effects_stage(cfg)
        elif args.command == "run-connectivity-effects":
            outputs = run_connectivity_effects_stage(cfg, method=args.method)
        elif args.command == "run-exploratory-coupling":
            outputs = run_exploratory_coupling_stage(
                cfg,
                analysis=args.analysis,
                method=args.method,
                global_metric=args.global_metric,
                global_weighting=args.global_weighting,
                event_window_sec=args.event_window_sec,
                window_sec=args.window_sec,
                peak_window_sec=args.peak_window_sec,
                transition_window_sec=args.transition_window_sec,
                direct_backend=args.direct_backend,
                direct_state_count=args.direct_state_count,
                direct_components=args.direct_components,
                field_peak_metric=args.field_peak_metric,
                field_normalization=args.field_normalization,
                field_state_count=args.field_state_count,
                field_min_duration_ms=args.field_min_duration_ms,
                field_archetype_space=args.field_archetype_space,
                field_surrogates=args.field_surrogates,
                fine_lag_window_ms=args.fine_lag_window_ms,
                max_lag_ms=args.max_lag_ms,
                lag_step_ms=args.lag_step_ms,
                direct_surrogates=args.direct_surrogates,
                global_surrogates=args.global_surrogates,
                min_subjects=args.min_subjects,
            )
        elif args.command == "render-reports":
            outputs = render_reports(cfg)
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
