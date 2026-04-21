from __future__ import annotations

import importlib.util
from pathlib import Path

import mne
import numpy as np
import pandas as pd


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "export_seeg_peak_segment.py"
    spec = importlib.util.spec_from_file_location("export_seeg_peak_segment", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_synthetic_seeg(path: Path) -> None:
    sfreq = 250.0
    times = np.arange(0.0, 1.0, 1.0 / sfreq)
    data = np.vstack(
        [
            np.sin(2.0 * np.pi * 4.0 * times),
            0.8 * np.sin(2.0 * np.pi * 4.0 * times + 0.35),
            0.6 * np.sin(2.0 * np.pi * 4.0 * times + 0.7),
        ]
    )
    for sample in (40, 120, 210):
        data[0, sample] += 4.0
        data[1, sample] -= 3.0
        data[2, sample] += 2.5
    info = mne.create_info(["A1-A2", "A2-A3", "B1-B2"], sfreq=sfreq, ch_types="seeg")
    raw = mne.io.RawArray(data, info, verbose="ERROR")
    raw.save(path, overwrite=True, verbose="ERROR")


def _write_synthetic_atlas(path: Path) -> None:
    atlas_df = pd.DataFrame(
        {
            "Channel": ["A1", "A2", "A3", "B1", "B2"],
            "cortex_319663V:Schaefer_200_17net": [
                "DefaultA_PFC_1 L",
                "DefaultA_PFC_2 L",
                "DefaultA_PFC_3 L",
                "LimbicB_OFC_1 R",
                "LimbicB_OFC_2 R",
            ],
        }
    )
    atlas_df.to_csv(path, sep="\t", index=False)


def test_export_seeg_peak_segment_writes_expected_outputs(tmp_path: Path) -> None:
    module = _load_script_module()
    seeg_path = tmp_path / "synthetic_raw.fif"
    output_dir = tmp_path / "outputs"
    _write_synthetic_seeg(seeg_path)

    output_paths = module.export_seeg_peak_segment(
        seeg_path=seeg_path,
        start_sec=0.0,
        end_sec=1.0,
        output_dir=output_dir,
        patient_id="sub-01",
    )

    for path in output_paths.values():
        assert path.exists()

    segment_matrix = pd.read_csv(output_paths["segment_matrix"])
    peak_summary = pd.read_csv(output_paths["peak_summary"])
    peak_trace = pd.read_csv(output_paths["peak_trace"])
    segment_info = pd.read_csv(output_paths["segment_info"])
    standardized_segment_matrix = pd.read_csv(output_paths["standardized_segment_matrix"])

    assert segment_matrix.columns[0] == "row_name"
    assert segment_matrix["row_name"].tolist()[:3] == ["A1-A2", "A2-A3", "B1-B2"]
    assert "peak_metric_value" in segment_matrix["row_name"].tolist()
    assert "spatial_std_raw" in segment_matrix["row_name"].tolist()
    assert "rms_raw" in segment_matrix["row_name"].tolist()
    assert "is_peak_sample" in segment_matrix["row_name"].tolist()
    assert not peak_summary.empty
    assert peak_trace.shape[0] == segment_matrix.shape[1] - 1
    assert int(float(segment_info.loc[segment_info["key"] == "n_samples", "value"].iloc[0])) == peak_trace.shape[0]
    assert segment_info.loc[segment_info["key"] == "mapping_filter_applied", "value"].iloc[0] == "False"
    assert segment_info.loc[segment_info["key"] == "n_input_channels", "value"].iloc[0] == "3"
    assert segment_info.loc[segment_info["key"] == "n_channels", "value"].iloc[0] == "3"
    assert segment_info.loc[segment_info["key"] == "channel_normalization", "value"].iloc[0] == "zscore"
    assert "spatial_std_zscore" in standardized_segment_matrix["row_name"].tolist()
    assert "rms_zscore" in standardized_segment_matrix["row_name"].tolist()

    peak_mask_row = segment_matrix.loc[segment_matrix["row_name"] == "is_peak_sample"].iloc[0, 1:].astype(float)
    assert int(peak_mask_row.sum()) == peak_summary.shape[0]
    channel_layout = pd.read_csv(output_paths["channel_layout"])
    assert channel_layout["region"].tolist() == ["Unmapped", "Unmapped", "Unmapped"]
    for channel in ["A1-A2", "A2-A3", "B1-B2"]:
        row = standardized_segment_matrix.loc[standardized_segment_matrix["row_name"] == channel].iloc[0, 1:].astype(float)
        assert abs(float(row.mean())) < 1e-9
        assert abs(float(row.std(ddof=0)) - 1.0) < 1e-6


def test_export_seeg_peak_segment_main_cli(tmp_path: Path) -> None:
    module = _load_script_module()
    seeg_path = tmp_path / "synthetic_raw.fif"
    output_dir = tmp_path / "outputs"
    _write_synthetic_seeg(seeg_path)

    exit_code = module.main(
        [
            "--seeg-path",
            str(seeg_path),
            "--start-sec",
            "0.1",
            "--end-sec",
            "0.9",
            "--output-dir",
            str(output_dir),
            "--patient-id",
            "sub-02",
            "--min-peak-distance-ms",
            "20",
        ]
    )

    assert exit_code == 0
    assert list(output_dir.glob("*_segment_bundle.xlsx"))
    assert list(output_dir.glob("*_segment_waveform.png"))
    assert list(output_dir.glob("*_segment_waveform.svg"))
    assert list(output_dir.glob("*_standardized_waveform.png"))
    assert list(output_dir.glob("*_standardized_waveform.svg"))
    svg_text = next(output_dir.glob("*_segment_waveform.svg")).read_text(encoding="utf-8")
    assert "<text" in svg_text
    standardized_svg_text = next(output_dir.glob("*_standardized_waveform.svg")).read_text(encoding="utf-8")
    assert "<text" in standardized_svg_text


def test_export_seeg_peak_segment_orders_channels_by_yeo17(tmp_path: Path) -> None:
    module = _load_script_module()
    seeg_path = tmp_path / "synthetic_raw.fif"
    atlas_path = tmp_path / "Atlas.tsv"
    output_dir = tmp_path / "outputs"
    _write_synthetic_seeg(seeg_path)
    _write_synthetic_atlas(atlas_path)

    output_paths = module.export_seeg_peak_segment(
        seeg_path=seeg_path,
        start_sec=0.0,
        end_sec=1.0,
        output_dir=output_dir,
        patient_id="sub-03",
        atlas_path=atlas_path,
    )

    channel_layout = pd.read_csv(output_paths["channel_layout"])
    assert channel_layout["region"].tolist() == ["LimbicB", "DefaultA", "DefaultA"]
    assert channel_layout.loc[channel_layout["region"] == "LimbicB", "bipolar_channel"].tolist() == ["B1-B2"]
    assert channel_layout.loc[channel_layout["region"] == "DefaultA", "bipolar_channel"].tolist() == ["A1-A2", "A2-A3"]
    segment_info = pd.read_csv(output_paths["segment_info"])
    assert (
        segment_info.loc[segment_info["key"] == "n_mapped_channels", "value"].iloc[0]
        == "3"
    )
    assert segment_info.loc[segment_info["key"] == "mapping_filter_applied", "value"].iloc[0] == "True"
    assert segment_info.loc[segment_info["key"] == "n_input_channels", "value"].iloc[0] == "3"
    assert segment_info.loc[segment_info["key"] == "n_channels", "value"].iloc[0] == "3"
