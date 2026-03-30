from __future__ import annotations

import argparse

from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.workflows import (
    build_index_artifacts,
    render_reports,
    run_activity_effects_stage,
    run_connectivity_effects_stage,
    run_eeg_states_stage,
    run_seeg_networks_stage,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seeg-eegmicrostates",
        description="Staged 1-40 Hz EEG/SEEG microstate analysis for IDE_A.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build-index", help="Scan IDE_A assets and build the eligible cohort index.")
    subparsers.add_parser("run-eeg-states", help="Generate reusable 1-40 Hz EEG microstate states.")
    subparsers.add_parser("run-seeg-networks", help="Generate reusable 1-40 Hz SEEG Yeo17 network signals.")
    subparsers.add_parser("run-activity-effects", help="Compute supplemental EEG-state-conditioned Yeo17 activity effects.")
    connectivity_parser = subparsers.add_parser(
        "run-connectivity-effects",
        help="Compute primary EEG-state-conditioned Yeo17 connectivity effects.",
    )
    connectivity_parser.add_argument("--method", default="all", choices=["corr", "plv", "wpli", "all"])
    subparsers.add_parser("render-reports", help="Render figures and Excel tables from staged analysis outputs.")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    cfg = AnalysisConfig()
    if args.command == "build-index":
        outputs = build_index_artifacts(cfg)
    elif args.command == "run-eeg-states":
        outputs = run_eeg_states_stage(cfg)
    elif args.command == "run-seeg-networks":
        outputs = run_seeg_networks_stage(cfg)
    elif args.command == "run-activity-effects":
        outputs = run_activity_effects_stage(cfg)
    elif args.command == "run-connectivity-effects":
        outputs = run_connectivity_effects_stage(cfg, method=args.method)
    elif args.command == "render-reports":
        outputs = render_reports(cfg)
    else:
        raise ValueError(f"Unsupported command: {args.command}")
    for key, value in outputs.items():
        print(f"{key}: {value}")
