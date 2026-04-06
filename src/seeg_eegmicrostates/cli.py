from __future__ import annotations

import argparse
from datetime import datetime
import traceback

from seeg_eegmicrostates.config import (
    AnalysisConfig,
    DEFAULT_ANALYSIS_STATE,
    SEEG_PARCELLATION_COLUMN,
    SEEG_PARCELLATION_NAME,
    SUPPORTED_ANALYSIS_STATES,
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
        help="Override the default EEG microstate template file (defaults to artifacts/cache/eeg/ModK.fif).",
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
        help="Run opt-in exploratory EEG/SEEG coupling analyses from staged EEG labels and staged SEEG parcellation signals.",
    )
    exploratory_parser.add_argument("--analysis", default="all", choices=["all", *_EXPLORATORY_ANALYSIS_CHOICES])
    exploratory_parser.add_argument("--method", default="all", choices=["corr", "plv", "wpli", "all"])
    exploratory_parser.add_argument("--event-window-sec", type=float, default=1.0)
    exploratory_parser.add_argument("--window-sec", type=float, default=10.0)
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
                event_window_sec=args.event_window_sec,
                window_sec=args.window_sec,
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
