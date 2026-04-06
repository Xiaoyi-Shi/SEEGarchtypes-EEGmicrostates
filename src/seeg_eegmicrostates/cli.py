from __future__ import annotations

import argparse
from datetime import datetime
import traceback

from seeg_eegmicrostates.config import AnalysisConfig
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
    parser = argparse.ArgumentParser(
        prog="seeg-eegmicrostates",
        description="Staged 1-40 Hz EEG/SEEG microstate analysis for IDE_A.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build-index", help="Scan IDE_A assets and build the eligible cohort index.")
    eeg_parser = subparsers.add_parser("run-eeg-states", help="Generate reusable 1-40 Hz EEG microstate states.")
    eeg_parser.add_argument(
        "--template-fif",
        help="Override the default EEG microstate template file (defaults to artifacts/cache/eeg/ModK.fif).",
    )
    subparsers.add_parser("run-seeg-regions", help="Generate reusable 1-40 Hz SEEG AAL3 region signals.")
    subparsers.add_parser("run-activity-effects", help="Compute supplemental EEG-state-conditioned AAL3 activity effects.")
    connectivity_parser = subparsers.add_parser(
        "run-connectivity-effects",
        help="Compute primary EEG-state-conditioned AAL3 region connectivity effects.",
    )
    connectivity_parser.add_argument("--method", default="all", choices=["corr", "plv", "wpli", "all"])
    exploratory_parser = subparsers.add_parser(
        "run-exploratory-coupling",
        help="Run opt-in exploratory EEG/SEEG coupling analyses from staged EEG labels and AAL3 region signals.",
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
    subparsers.add_parser("render-reports", help="Render figures and Excel tables from staged analysis outputs.")
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
    cfg = AnalysisConfig()
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
