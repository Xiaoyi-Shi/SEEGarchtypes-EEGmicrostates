from __future__ import annotations

from seeg_eegmicrostates.cli import build_parser


def test_cli_exposes_streamlined_staged_commands() -> None:
    parser = build_parser()
    action = next(action for action in parser._actions if getattr(action, "choices", None))
    commands = set(action.choices)
    assert commands == {
        "build-index",
        "run-eeg-states",
        "run-seeg-networks",
        "run-activity-effects",
        "run-connectivity-effects",
        "render-reports",
    }


def test_cli_hides_legacy_public_commands() -> None:
    parser = build_parser()
    legacy_commands = ["run-eeg", "run-seeg-hfa", "run-hfa-coupling", "run-band-1-40", "run-band-1-40-connectivity"]
    for command in legacy_commands:
        try:
            parser.parse_args([command])
        except SystemExit:
            continue
        raise AssertionError(f"Legacy command {command} should not remain in the public CLI.")
