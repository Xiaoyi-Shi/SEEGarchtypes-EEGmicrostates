from __future__ import annotations

import pandas as pd

from seeg_eegmicrostates.config import AnalysisConfig
from seeg_eegmicrostates.seeg.region import aggregate_channel_dataframe_by_region


def compute_band_limited_region_signals(
    raw_bp,
    mapping_df: pd.DataFrame,
    cfg: AnalysisConfig,
    *,
    patient_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    band = raw_bp.copy()
    band.filter(cfg.band_limited_range[0], cfg.band_limited_range[1], verbose="ERROR")
    band.resample(cfg.seeg_resample_hz, verbose="ERROR")
    frame = pd.DataFrame(band.get_data().T, columns=band.ch_names)
    frame.insert(0, "time_sec", band.times.astype(float))
    region_df, coverage_df = aggregate_channel_dataframe_by_region(frame, mapping_df, patient_id=patient_id)
    return region_df, coverage_df
