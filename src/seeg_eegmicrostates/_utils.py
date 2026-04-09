from __future__ import annotations

from dataclasses import asdict, is_dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def to_jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value


def config_hash(payload: Any, length: int = 10) -> str:
    encoded = json.dumps(to_jsonable(payload), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def coerce_path(value: str | Path) -> Path:
    return value if isinstance(value, Path) else Path(value)


def dataframe_to_records_frame(df: pd.DataFrame, value_name: str) -> pd.DataFrame:
    melted = df.melt(id_vars=["time_sec"], var_name="name", value_name=value_name)
    return melted.dropna(subset=[value_name]).reset_index(drop=True)


def zscore_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    result = df.copy()
    for column in columns:
        series = result[column]
        std = float(series.std(ddof=0))
        if std == 0 or np.isnan(std):
            result[column] = 0.0
            continue
        result[column] = (series - float(series.mean())) / std
    return result


def contiguous_runs(labels: np.ndarray) -> list[tuple[int, int, int]]:
    if labels.size == 0:
        return []
    runs: list[tuple[int, int, int]] = []
    start = 0
    current = int(labels[0])
    for index in range(1, labels.size):
        label = int(labels[index])
        if label != current:
            runs.append((start, index, current))
            start = index
            current = label
    runs.append((start, labels.size, current))
    return runs


def write_dataframe(df: pd.DataFrame, path: Path) -> Path:
    ensure_directory(path.parent)
    df.to_parquet(path, index=False)
    return path


def write_excel_dataframe(df: pd.DataFrame, path: Path, *, sheet_name: str = "results") -> Path:
    ensure_directory(path.parent)
    df.to_excel(path, index=False, sheet_name=sheet_name)
    return path


def write_csv_dataframe(df: pd.DataFrame, path: Path) -> Path:
    ensure_directory(path.parent)
    df.to_csv(path, index=False)
    return path


def read_dataframe(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)
