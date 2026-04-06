from __future__ import annotations

from pathlib import Path

import pytest

from seeg_eegmicrostates.cli import build_parser
from seeg_eegmicrostates.config import AnalysisConfig
import seeg_eegmicrostates.cli as cli


def test_cli_exposes_streamlined_staged_commands() -> None:
    parser = build_parser()
    action = next(action for action in parser._actions if getattr(action, "choices", None))
    commands = set(action.choices)
    assert commands == {
        "build-index",
        "run-eeg-states",
        "run-seeg-regions",
        "run-activity-effects",
        "run-connectivity-effects",
        "run-exploratory-coupling",
        "render-reports",
    }


def test_cli_hides_legacy_public_commands() -> None:
    parser = build_parser()
    legacy_commands = ["run-eeg", "run-seeg-hfa", "run-hfa-coupling", "run-band-1-40", "run-band-1-40-connectivity", "run-seeg-networks"]
    for command in legacy_commands:
        try:
            parser.parse_args([command])
        except SystemExit:
            continue
        raise AssertionError(f"Legacy command {command} should not remain in the public CLI.")


def test_cli_describes_aal3_region_outputs() -> None:
    parser = build_parser()
    top_level_help = parser.format_help()
    action = next(action for action in parser._actions if getattr(action, "choices", None))
    eeg_help = action.choices["run-eeg-states"].format_help()
    assert "AAL3" in top_level_help
    assert "ModK.fif" in eeg_help
    assert "run-seeg-regions" in top_level_help
    assert "run-exploratory-coupling" in top_level_help
    assert "state-alignment" not in top_level_help


def test_run_eeg_states_accepts_template_override() -> None:
    parser = build_parser()
    args = parser.parse_args(["run-eeg-states", "--template-fif", "template.fif"])
    assert args.command == "run-eeg-states"
    assert args.template_fif == "template.fif"


def test_run_exploratory_coupling_accepts_analysis_specific_options() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "run-exploratory-coupling",
            "--analysis",
            "event-connectivity",
            "--method",
            "plv",
            "--event-window-sec",
            "1.5",
            "--window-sec",
            "12",
            "--min-subjects",
            "5",
        ]
    )
    assert args.command == "run-exploratory-coupling"
    assert args.analysis == "event-connectivity"
    assert args.method == "plv"
    assert args.event_window_sec == 1.5
    assert args.window_sec == 12.0
    assert args.min_subjects == 5


def test_cli_main_writes_command_log_into_timestamped_run_folder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", run_timestamp="20260406_123456")
    fake_output = tmp_path / "artifact.txt"
    fake_output.write_text("ok", encoding="utf-8")

    monkeypatch.setattr(cli, "AnalysisConfig", lambda: cfg)
    monkeypatch.setattr(cli, "build_index_artifacts", lambda _: {"recording_index": fake_output})

    cli.main(["build-index"])

    captured = capsys.readouterr()
    log_path = cfg.log_path("build-index")
    assert log_path.exists()
    assert "log:" in captured.out
    assert str(log_path) in captured.out
    log_text = log_path.read_text(encoding="utf-8")
    assert "command: build-index" in log_text
    assert "status: completed" in log_text
    assert str(fake_output) in log_text
