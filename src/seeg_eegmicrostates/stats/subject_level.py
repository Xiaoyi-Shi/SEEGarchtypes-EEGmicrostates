from __future__ import annotations

import numpy as np


def cohen_d(group_a: np.ndarray, group_b: np.ndarray) -> float:
    if group_a.size < 2 or group_b.size < 2:
        return 0.0
    var_a = group_a.var(ddof=1)
    var_b = group_b.var(ddof=1)
    pooled = ((group_a.size - 1) * var_a + (group_b.size - 1) * var_b) / (group_a.size + group_b.size - 2)
    if pooled <= 0:
        return 0.0
    return float((group_a.mean() - group_b.mean()) / np.sqrt(pooled))
