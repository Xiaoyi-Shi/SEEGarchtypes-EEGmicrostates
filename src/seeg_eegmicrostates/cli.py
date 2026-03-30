from __future__ import annotations

import argparse

from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.workflows import (
    build_index_artifacts,
    render_reports,
    run_band_limited_connectivity_branch,
    run_band_limited_cross_modal_branch,
    run_eeg_microstate_branch,
    run_hfa_coupling_branch,
    run_seeg_hfa_branch,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="seeg-eegmicrostates")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build-index")
    eeg_parser = subparsers.add_parser("run-eeg")
    eeg_parser.add_argument("--branch", default="main", choices=["main", "band_1_40"])
    subparsers.add_parser("run-seeg-hfa")
    subparsers.add_parser("run-hfa-coupling")
    subparsers.add_parser("run-band-1-40")
    connectivity_parser = subparsers.add_parser("run-band-1-40-connectivity")
    connectivity_parser.add_argument("--method", default="all", choices=["corr", "plv", "wpli", "all"])
    subparsers.add_parser("render-reports")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    cfg = AnalysisConfig()
    if args.command == "build-index":
        outputs = build_index_artifacts(cfg)
    elif args.command == "run-eeg":
        outputs = run_eeg_microstate_branch(cfg, branch=args.branch)
    elif args.command == "run-seeg-hfa":
        outputs = run_seeg_hfa_branch(cfg)
    elif args.command == "run-hfa-coupling":
        outputs = run_hfa_coupling_branch(cfg)
    elif args.command == "run-band-1-40":
        outputs = run_band_limited_cross_modal_branch(cfg)
    elif args.command == "run-band-1-40-connectivity":
        outputs = run_band_limited_connectivity_branch(cfg, method=args.method)
    elif args.command == "render-reports":
        outputs = render_reports(cfg)
    else:
        raise ValueError(f"Unsupported command: {args.command}")
    for key, value in outputs.items():
        print(f"{key}: {value}")
