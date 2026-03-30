from __future__ import annotations

import numpy as np
import pandas as pd


def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    if p_values.empty:
        return p_values.copy()
    order = np.argsort(p_values.to_numpy(dtype=float))
    ranked = p_values.to_numpy(dtype=float)[order]
    count = ranked.size
    adjusted = np.empty(count, dtype=float)
    running_min = 1.0
    for index in range(count - 1, -1, -1):
        rank = index + 1
        value = ranked[index] * count / rank
        running_min = min(running_min, value)
        adjusted[index] = running_min
    restored = np.empty(count, dtype=float)
    restored[order] = np.clip(adjusted, 0.0, 1.0)
    return pd.Series(restored, index=p_values.index, dtype=float)
