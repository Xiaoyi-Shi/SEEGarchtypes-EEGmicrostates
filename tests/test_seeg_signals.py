from __future__ import annotations

import numpy as np
import pandas as pd

from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.seeg.microstates import compute_band_limited_region_signals


class _FakeRaw:
    def __init__(self, data: np.ndarray, ch_names: list[str], times: np.ndarray) -> None:
        self._data = np.asarray(data, dtype=float)
        self.ch_names = list(ch_names)
        self.times = np.asarray(times, dtype=float)

    def copy(self) -> "_FakeRaw":
        return _FakeRaw(self._data.copy(), list(self.ch_names), self.times.copy())

    def filter(self, *_args, **_kwargs) -> "_FakeRaw":
        return self

    def apply_hilbert(self, *, envelope: bool) -> "_FakeRaw":
        assert envelope is True
        return self

    def resample(self, _sfreq: float, **_kwargs) -> "_FakeRaw":
        return self

    def get_data(self) -> np.ndarray:
        return self._data


def test_band_limited_region_signals_preserve_channel_scale() -> None:
    raw = _FakeRaw(
        data=np.array(
            [
                [1.0, 2.0, 3.0],
                [2.0, 4.0, 6.0],
            ]
        ),
        ch_names=["A1-A2", "A2-A3"],
        times=np.array([0.0, 0.004, 0.008]),
    )
    mapping_df = pd.DataFrame(
        {
            "bipolar_channel": ["A1-A2", "A2-A3"],
            "region": ["Right Hippocampus", "Right Hippocampus"],
            "valid_same_region": [True, True],
        }
    )

    region_df, coverage_df = compute_band_limited_region_signals(
        raw,
        mapping_df,
        AnalysisConfig(),
        patient_id="sub-01",
    )

    assert region_df["Right Hippocampus"].tolist() == [1.5, 3.0, 4.5]
    assert coverage_df.iloc[0]["n_bipolar_channels"] == 2
