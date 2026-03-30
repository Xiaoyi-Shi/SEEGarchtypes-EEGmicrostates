from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_atlas_table(atlas_path: str | Path) -> pd.DataFrame:
    return pd.read_csv(atlas_path, sep="\t")
