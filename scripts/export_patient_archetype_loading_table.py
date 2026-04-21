from __future__ import annotations

import argparse
from pathlib import Path
import re
from typing import Iterable

import pandas as pd


DEFAULT_CACHE_ROOT = Path("artifacts/cache")
DEFAULT_OUTPUT_DIR = Path("artifacts/manual/patient_archetype_tables")
DEFAULT_OUTPUT_STEM = "patient_archetype_yeo17_summary"
DEFAULT_COMPARISON_SPACE = "yeo17"
DEFAULT_N_STATES = 4
RUNTIME_HASH_PATTERN = re.compile(r"_([0-9a-f]{10})\.parquet$", re.IGNORECASE)
YEO17_NETWORK_ORDER: tuple[str, ...] = (
    "VisCent",
    "VisPeri",
    "SomMotA",
    "SomMotB",
    "DorsAttnA",
    "DorsAttnB",
    "SalVentAttnA",
    "SalVentAttnB",
    "LimbicA",
    "LimbicB",
    "ContA",
    "ContB",
    "ContC",
    "DefaultA",
    "DefaultB",
    "DefaultC",
    "TempPar",
)


def _extract_runtime_hash(path: Path) -> str | None:
    match = RUNTIME_HASH_PATTERN.search(path.name)
    if match is None:
        return None
    return str(match.group(1)).lower()


def _sorted_paths(paths: Iterable[Path]) -> list[Path]:
    return sorted(paths, key=lambda path: (path.stat().st_mtime, path.name), reverse=True)


def _discover_assignment_path(cache_root: Path, runtime_hash: str | None) -> Path:
    coupling_root = cache_root / "coupling"
    if runtime_hash is None:
        candidates = _sorted_paths(coupling_root.glob("field_state_archetype_assignments*.parquet"))
    else:
        candidates = _sorted_paths(coupling_root.glob(f"field_state_archetype_assignments*_{runtime_hash}.parquet"))
    if not candidates:
        detail = f" for runtime hash {runtime_hash}" if runtime_hash else ""
        raise FileNotFoundError(f"No field-state archetype assignment cache found{detail}.")
    return candidates[0]


def _load_matching_cache(
    paths: list[Path],
    *,
    label: str,
    n_states: int,
    comparison_space: str,
    required_columns: Iterable[str],
) -> tuple[Path, pd.DataFrame]:
    required = set(required_columns)
    for path in paths:
        frame = pd.read_parquet(path)
        if not required.issubset(frame.columns):
            continue
        if frame.empty:
            continue
        states = sorted(frame["n_states"].dropna().astype(int).unique().tolist()) if "n_states" in frame.columns else []
        if states and states != [int(n_states)]:
            continue
        if "comparison_space" in frame.columns:
            spaces = sorted(frame["comparison_space"].dropna().astype(str).str.lower().unique().tolist())
            if spaces and spaces != [comparison_space.lower()]:
                continue
        return path, frame
    raise FileNotFoundError(
        f"No {label} cache matched n_states={n_states} and comparison_space={comparison_space!r}."
    )


def _discover_cache_path(
    cache_root: Path,
    *,
    runtime_hash: str,
    label: str,
    stem: str,
    n_states: int,
    comparison_space: str,
    required_columns: Iterable[str],
) -> tuple[Path, pd.DataFrame]:
    search_root = cache_root / "coupling"
    candidates = _sorted_paths(search_root.glob(f"{stem}*_{runtime_hash}.parquet"))
    if not candidates:
        raise FileNotFoundError(f"No {label} cache found for runtime hash {runtime_hash}.")
    return _load_matching_cache(
        candidates,
        label=label,
        n_states=n_states,
        comparison_space=comparison_space,
        required_columns=required_columns,
    )


def _load_explicit_cache(
    path: Path,
    *,
    label: str,
    n_states: int,
    comparison_space: str,
    required_columns: Iterable[str],
) -> tuple[Path, pd.DataFrame]:
    if not path.exists():
        raise FileNotFoundError(f"{label} cache not found: {path}")
    return _load_matching_cache(
        [path],
        label=label,
        n_states=n_states,
        comparison_space=comparison_space,
        required_columns=required_columns,
    )


def _normalize_string_columns(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    normalized = frame.copy()
    for column in columns:
        if column in normalized.columns:
            normalized[column] = normalized[column].astype(str)
    return normalized


def build_patient_archetype_table(
    assignment_df: pd.DataFrame,
    projection_df: pd.DataFrame,
    profile_df: pd.DataFrame,
) -> pd.DataFrame:
    assignment_keys = [
        "patient_id",
        "field_state",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "comparison_space",
    ]
    profile_keys = [
        "patient_id",
        "field_state",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
    ]
    assignment_df = _normalize_string_columns(
        assignment_df,
        columns=["patient_id", "peak_metric", "normalization", "comparison_space"],
    )
    projection_df = _normalize_string_columns(
        projection_df,
        columns=["patient_id", "peak_metric", "normalization", "comparison_space"],
    )
    profile_df = _normalize_string_columns(
        profile_df,
        columns=["patient_id", "peak_metric", "normalization"],
    )
    merged = assignment_df.merge(
        projection_df,
        on=assignment_keys,
        how="left",
        validate="one_to_one",
        suffixes=("", "_projection"),
    )
    if merged["n_channels"].isna().any():
        missing = merged.loc[merged["n_channels"].isna(), ["patient_id", "field_state"]]
        raise ValueError(
            "Some assignment rows did not find matching patient-level projection rows:\n"
            f"{missing.to_string(index=False)}"
        )
    merged = merged.merge(
        profile_df,
        on=profile_keys,
        how="left",
        validate="one_to_one",
        suffixes=("", "_profile"),
    )
    if merged["occupancy"].isna().any():
        missing = merged.loc[merged["occupancy"].isna(), ["patient_id", "field_state"]]
        raise ValueError(
            "Some assignment rows did not find matching patient-level field-state profiles:\n"
            f"{missing.to_string(index=False)}"
        )
    for network in YEO17_NETWORK_ORDER:
        if network not in merged.columns:
            merged[network] = pd.NA
    merged["archetype"] = merged["assigned_archetype"].astype(int)
    merged["source_field_state"] = merged["field_state"].astype(int)
    merged["effective_bipolar_channels"] = merged["n_channels"].astype("Int64")
    merged["mapped_yeo17_bipolar_channels"] = merged["n_mapped_channels"].astype("Int64")
    merged["covered_yeo17_networks"] = merged["n_common_units"].astype("Int64")
    merged["mean_dwell_ms"] = merged["mean_dwell_sec"].astype(float) * 1000.0
    ordered_columns = [
        "patient_id",
        "archetype",
        *YEO17_NETWORK_ORDER,
        "effective_bipolar_channels",
        "mapped_yeo17_bipolar_channels",
        "covered_yeo17_networks",
        "occupancy",
        "mean_dwell_ms",
        "n_samples",
        "n_runs",
        "n_peak_maps",
        "assignment_similarity",
        "source_field_state",
        "orientation_sign",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
    ]
    table = merged.loc[:, ordered_columns].copy()
    table = table.sort_values(["patient_id", "archetype"], kind="stable").reset_index(drop=True)
    return table


def export_patient_archetype_table(
    *,
    cache_root: Path,
    output_dir: Path,
    output_stem: str,
    runtime_hash: str | None,
    n_states: int,
    comparison_space: str,
    assignment_path: Path | None,
    projection_path: Path | None,
    profile_path: Path | None,
) -> tuple[pd.DataFrame, Path, Path, str]:
    if assignment_path is None:
        resolved_assignment_path = _discover_assignment_path(cache_root, runtime_hash)
    else:
        resolved_assignment_path = assignment_path
    resolved_runtime_hash = runtime_hash or _extract_runtime_hash(resolved_assignment_path)
    if resolved_runtime_hash is None:
        raise ValueError(
            "Could not infer runtime hash from the selected assignment cache name. Pass --runtime-hash explicitly."
        )
    assignment_required = [
        "patient_id",
        "field_state",
        "assigned_archetype",
        "assignment_similarity",
        "orientation_sign",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "comparison_space",
    ]
    projection_required = [
        "patient_id",
        "field_state",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "comparison_space",
        "orientation_sign",
        "n_channels",
        "n_peak_maps",
        "n_mapped_channels",
        "n_common_units",
    ]
    profile_required = [
        "patient_id",
        "field_state",
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "occupancy",
        "mean_dwell_sec",
        "n_samples",
        "n_runs",
    ]
    assignment_path, assignment_df = _load_explicit_cache(
        resolved_assignment_path,
        label="assignment",
        n_states=n_states,
        comparison_space=comparison_space,
        required_columns=assignment_required,
    )
    if projection_path is None:
        projection_path, projection_df = _discover_cache_path(
            cache_root,
            runtime_hash=resolved_runtime_hash,
            label="projection",
            stem="field_state_archetype_projections",
            n_states=n_states,
            comparison_space=comparison_space,
            required_columns=projection_required,
        )
    else:
        projection_path, projection_df = _load_explicit_cache(
            projection_path,
            label="projection",
            n_states=n_states,
            comparison_space=comparison_space,
            required_columns=projection_required,
        )
    if profile_path is None:
        profile_path, profile_df = _discover_cache_path(
            cache_root,
            runtime_hash=resolved_runtime_hash,
            label="field-state profile",
            stem="field_state_profiles",
            n_states=n_states,
            comparison_space=comparison_space,
            required_columns=profile_required,
        )
    else:
        profile_path, profile_df = _load_explicit_cache(
            profile_path,
            label="field-state profile",
            n_states=n_states,
            comparison_space=comparison_space,
            required_columns=profile_required,
        )
    table = build_patient_archetype_table(assignment_df, projection_df, profile_df)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{output_stem}_{resolved_runtime_hash}"
    csv_path = output_dir / f"{stem}.csv"
    xlsx_path = output_dir / f"{stem}.xlsx"
    table.to_csv(csv_path, index=False, encoding="utf-8-sig")
    table.to_excel(xlsx_path, index=False)
    print(f"runtime_hash: {resolved_runtime_hash}")
    print(f"assignment_cache: {assignment_path}")
    print(f"projection_cache: {projection_path}")
    print(f"profile_cache: {profile_path}")
    print(f"rows: {len(table)}")
    print(f"patients: {table['patient_id'].nunique()}")
    print(f"csv: {csv_path}")
    print(f"xlsx: {xlsx_path}")
    return table, csv_path, xlsx_path, resolved_runtime_hash


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export a patient-by-archetype Yeo17 loading table from existing field-state archetype caches. "
            "The primary output is one row per patient x assigned archetype."
        )
    )
    parser.add_argument(
        "--cache-root",
        type=Path,
        default=DEFAULT_CACHE_ROOT,
        help="Cache root that contains coupling/*.parquet files. Defaults to artifacts/cache.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for CSV/XLSX exports. Defaults to artifacts/manual/patient_archetype_tables.",
    )
    parser.add_argument(
        "--output-stem",
        default=DEFAULT_OUTPUT_STEM,
        help="Base filename stem for output tables. The runtime hash is appended automatically.",
    )
    parser.add_argument(
        "--runtime-hash",
        default=None,
        help=(
            "Optional runtime hash suffix used to pick matching caches. "
            "If omitted, the script uses the newest archetype assignment cache."
        ),
    )
    parser.add_argument(
        "--n-states",
        type=int,
        default=DEFAULT_N_STATES,
        help="Expected field-state count. Defaults to 4.",
    )
    parser.add_argument(
        "--comparison-space",
        default=DEFAULT_COMPARISON_SPACE,
        help="Expected common-space label in the archetype caches. Defaults to yeo17.",
    )
    parser.add_argument(
        "--assignment-path",
        type=Path,
        default=None,
        help="Optional explicit assignment cache path.",
    )
    parser.add_argument(
        "--projection-path",
        type=Path,
        default=None,
        help="Optional explicit patient-level projection cache path.",
    )
    parser.add_argument(
        "--profile-path",
        type=Path,
        default=None,
        help="Optional explicit field-state profile cache path.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    export_patient_archetype_table(
        cache_root=args.cache_root,
        output_dir=args.output_dir,
        output_stem=args.output_stem,
        runtime_hash=str(args.runtime_hash).lower() if args.runtime_hash else None,
        n_states=int(args.n_states),
        comparison_space=str(args.comparison_space).strip().lower(),
        assignment_path=args.assignment_path,
        projection_path=args.projection_path,
        profile_path=args.profile_path,
    )


if __name__ == "__main__":
    main()
