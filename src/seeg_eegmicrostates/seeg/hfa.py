from __future__ import annotations

import numpy as np
import pandas as pd

from seeg_eegmicrostates._utils import zscore_columns
from seeg_eegmicrostates.config import AnalysisConfig


def compute_hfa_envelope(raw_bp, cfg: AnalysisConfig) -> pd.DataFrame:
    hfa = raw_bp.copy()
    hfa.filter(cfg.seeg_hfa_band[0], cfg.seeg_hfa_band[1], verbose="ERROR")
    hfa.apply_hilbert(envelope=True)
    hfa.resample(cfg.seeg_resample_hz, verbose="ERROR")
    data = hfa.get_data()
    frame = pd.DataFrame(data.T, columns=hfa.ch_names)
    frame.insert(0, "time_sec", hfa.times.astype(float))
    channel_columns = [column for column in frame.columns if column != "time_sec"]
    frame[channel_columns] = np.log10(frame[channel_columns].abs().clip(lower=1e-12))
    return zscore_columns(frame, channel_columns)
