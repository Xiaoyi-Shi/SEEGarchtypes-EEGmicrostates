from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_patient_info(workbook_path: str | Path) -> pd.DataFrame:
    return pd.read_excel(workbook_path, sheet_name="patient_info")


def load_annotation_info(workbook_path: str | Path) -> pd.DataFrame:
    return pd.read_excel(workbook_path, sheet_name="annot_info")


def load_workbook_tables(workbook_path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_patient_info(workbook_path), load_annotation_info(workbook_path)
