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
    build_index_help = action.choices["build-index"].format_help()
    eeg_help = action.choices["run-eeg-states"].format_help()
    exploratory_help = action.choices["run-exploratory-coupling"].format_help()
    assert "AAL3" in top_level_help
    assert "ModK.fif" in eeg_help
    assert "configured default" in eeg_help
    assert "template at artifacts/cache/eeg/ModK.fif" in eeg_help
    assert "run-seeg-regions" in top_level_help
    assert "run-exploratory-coupling" in top_level_help
    assert "IDE_S" in build_index_help
    assert "field-state-coupling" in exploratory_help
    assert "field-state-archetypes" in exploratory_help
    assert "archetype-conditioned-eeg-topography" in exploratory_help
    assert "fine-lag-field-state-coupling" in exploratory_help
    assert "gfp-global-coupling" in exploratory_help
    assert "lagged-gfp-global-coupling" in exploratory_help
    assert "peak-gfp-global-coupling" in exploratory_help
    assert "gfp-controlled-microstate" in exploratory_help
    assert "gfp-controlled-transition" in exploratory_help
    assert "field-state-to-eeg-switching" in exploratory_help
    assert "gfp-controlled-field-state-to-eeg-switching" in exploratory_help
    assert "direct-state-coupling" not in exploratory_help
    assert "event-connectivity" not in exploratory_help
    assert "--event-window-sec" not in exploratory_help
    assert "--direct-backend" not in exploratory_help
    assert "state-alignment" not in top_level_help


def test_cli_accepts_analysis_state_override() -> None:
    parser = build_parser()
    args = parser.parse_args(["build-index", "--analysis-state", "IDE_S"])
    assert args.command == "build-index"
    assert args.analysis_state == "IDE_S"


def test_cli_accepts_shared_run_id_override() -> None:
    parser = build_parser()
    args = parser.parse_args(["build-index", "--run-id", "20260406_230000"])
    assert args.command == "build-index"
    assert args.run_id == "20260406_230000"


def test_cli_accepts_yeo17_parcellation_override() -> None:
    parser = build_parser()
    args = parser.parse_args(["run-seeg-regions", "--seeg-parcellation-name", "yeo17"])
    assert args.command == "run-seeg-regions"
    assert args.seeg_parcellation_name == "yeo17"


def test_cli_accepts_yeo7_parcellation_override() -> None:
    parser = build_parser()
    args = parser.parse_args(["run-seeg-regions", "--seeg-parcellation-name", "yeo7"])
    assert args.command == "run-seeg-regions"
    assert args.seeg_parcellation_name == "yeo7"


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
            "gfp-controlled-transition",
            "--global-metric",
            "envelope-rms",
            "--global-weighting",
            "sqrt-channel-count",
            "--transition-window-sec",
            "0.5",
            "--min-subjects",
            "5",
        ]
    )
    assert args.command == "run-exploratory-coupling"
    assert args.analysis == "gfp-controlled-transition"
    assert args.global_metric == "envelope-rms"
    assert args.global_weighting == "sqrt-channel-count"
    assert args.transition_window_sec == 0.5
    assert args.min_subjects == 5


def test_run_exploratory_coupling_rejects_retired_public_options() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["run-exploratory-coupling", "--analysis", "lagged-state-coupling"])
    with pytest.raises(SystemExit):
        parser.parse_args(["run-exploratory-coupling", "--analysis", "field-state-coupling", "--direct-backend", "pca-kmeans"])


def test_run_exploratory_coupling_accepts_field_state_options() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "run-exploratory-coupling",
            "--analysis",
            "fine-lag-field-state-coupling",
            "--field-peak-metric",
            "spatial-std",
            "--field-normalization",
            "robust-zscore",
            "--field-state-count",
            "5",
            "--field-min-duration-ms",
            "20",
            "--field-archetype-space",
            "yeo17",
            "--field-surrogates",
            "64",
            "--fine-lag-window-ms",
            "24",
        ]
    )
    assert args.analysis == "fine-lag-field-state-coupling"
    assert args.field_peak_metric == "spatial-std"
    assert args.field_normalization == "robust-zscore"
    assert args.field_state_count == 5
    assert args.field_min_duration_ms == 20
    assert args.field_archetype_space == "yeo17"
    assert args.field_surrogates == 64
    assert args.fine_lag_window_ms == 24


def test_run_exploratory_coupling_accepts_archetype_conditioned_topography_analysis() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "run-exploratory-coupling",
            "--analysis",
            "archetype-conditioned-eeg-topography",
            "--field-archetype-space",
            "yeo17",
            "--fine-lag-window-ms",
            "32",
            "--transition-window-sec",
            "0.2",
            "--field-surrogates",
            "48",
        ]
    )
    assert args.analysis == "archetype-conditioned-eeg-topography"
    assert args.field_archetype_space == "yeo17"
    assert args.fine_lag_window_ms == 32
    assert args.transition_window_sec == 0.2
    assert args.field_surrogates == 48


def test_run_exploratory_coupling_accepts_gfp_global_options() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "run-exploratory-coupling",
            "--analysis",
            "peak-gfp-global-coupling",
            "--global-metric",
            "envelope-rms",
            "--global-weighting",
            "sqrt-channel-count",
            "--peak-window-sec",
            "0.75",
            "--global-surrogates",
            "96",
        ]
    )
    assert args.analysis == "peak-gfp-global-coupling"
    assert args.global_metric == "envelope-rms"
    assert args.global_weighting == "sqrt-channel-count"
    assert args.peak_window_sec == 0.75
    assert args.global_surrogates == 96


def test_cli_main_writes_command_log_into_timestamped_run_folder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cfg = AnalysisConfig(artifact_root=tmp_path / "artifacts", run_timestamp="20260406_123456")
    fake_output = tmp_path / "artifact.txt"
    fake_output.write_text("ok", encoding="utf-8")

    monkeypatch.setattr(cli, "AnalysisConfig", lambda **_kwargs: cfg)
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
    assert "analysis_state: IDE_A" in log_text
    assert str(fake_output) in log_text
    assert not cfg.reports_root.exists()
