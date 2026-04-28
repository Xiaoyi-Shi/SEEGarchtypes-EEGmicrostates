from __future__ import annotations

import argparse
from itertools import permutations
import os
from pathlib import Path
import re
from typing import Iterable

_LOCAL_HOME = (Path(__file__).resolve().parents[1] / ".mne-home").resolve()
_LOCAL_HOME.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("_MNE_FAKE_HOME_DIR", str(_LOCAL_HOME))
os.environ.setdefault("MNE_DONTWRITE_HOME", "true")
os.environ.setdefault("HOME", str(_LOCAL_HOME))
os.environ.setdefault("USERPROFILE", str(_LOCAL_HOME))
os.environ.setdefault("APPDATA", str(_LOCAL_HOME))
os.environ.setdefault("MNE_HOME", str((_LOCAL_HOME / ".mne").resolve()))

import mne
import numpy as np
import pandas as pd
from scipy.interpolate import RBFInterpolator

from seeg_eegmicrostates.seeg.bipolar_map import build_same_region_bipolar_map


DEFAULT_RUNTIME_HASH = "97411c0ec4"
DEFAULT_CACHE_ROOT = Path("artifacts/cache")
DEFAULT_DATA_ROOT = Path("datas/data_01_seeg")
DEFAULT_REPORT_ROOT = Path("artifacts/runs/20260412_140500/reports")
DEFAULT_OUTPUT_DIR = Path("artifacts/manual/maintext_validation")
DEFAULT_PATIENT_ARCHETYPE_CSV = Path(
    f"artifacts/manual/patient_archetype_tables/patient_archetype_yeo17_summary_{DEFAULT_RUNTIME_HASH}.csv"
)
DEFAULT_REPRESENTATIVE_COUNT = 3

YEO17_ATLAS_COLUMN = "cortex_319663V:Schaefer_200_17net"
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
ARCHETYPE_META_COLUMNS = {
    "patient_id",
    "comparison_space",
    "peak_metric",
    "normalization",
    "n_states",
    "min_duration_ms",
    "assigned_archetype",
    "n_samples",
    "n_unique_eeg_states",
    "field_state",
    "n_channels",
    "n_peak_maps",
    "orientation_sign",
    "n_mapped_channels",
    "n_common_units",
    "n_subjects",
    "total_samples",
}
RUNTIME_HASH_PATTERN = re.compile(r"_([0-9a-f]{10})\.parquet$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export maintained CSV inputs for the manuscript main-text validation figures."
    )
    parser.add_argument("--runtime-hash", default=DEFAULT_RUNTIME_HASH, help="Runtime hash used by the retained IDE-A analysis branch.")
    parser.add_argument("--cache-root", default=str(DEFAULT_CACHE_ROOT), help="Root directory containing cached Parquet outputs.")
    parser.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT), help="Root directory containing patient SEEG data folders.")
    parser.add_argument("--report-root", default=str(DEFAULT_REPORT_ROOT), help="Report root containing exported main/supplementary tables.")
    parser.add_argument(
        "--patient-archetype-csv",
        default=str(DEFAULT_PATIENT_ARCHETYPE_CSV),
        help="Patient-level Yeo17 archetype summary CSV used to define the retained cohort.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where validation CSV inputs will be written.",
    )
    parser.add_argument(
        "--n-representatives",
        type=int,
        default=DEFAULT_REPRESENTATIVE_COUNT,
        help="Number of representative single-subject EEG examples to pre-export for topomap plotting.",
    )
    return parser.parse_args()


def resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.exists():
        return candidate
    parent_candidate = Path("..") / candidate
    if parent_candidate.exists():
        return parent_candidate
    return candidate


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def output_stem(runtime_hash: str) -> str:
    return f"maintext_validation_{runtime_hash}"


def sorted_paths(paths: Iterable[Path]) -> list[Path]:
    return sorted(paths, key=lambda path: (path.stat().st_mtime, path.name), reverse=True)


def discover_cache(cache_root: Path, stem: str, runtime_hash: str) -> Path:
    search_root = cache_root / "coupling"
    candidates = sorted_paths(search_root.glob(f"{stem}*_{runtime_hash}.parquet"))
    if candidates:
        return candidates[0]
    fallback = sorted_paths(search_root.glob(f"{stem}*.parquet"))
    if not fallback:
        raise FileNotFoundError(f"Could not find cache matching stem '{stem}'.")
    return fallback[0]


def discover_report_csv(report_root: Path, subdir: str, label_pattern: str, runtime_hash: str | None = None) -> Path:
    search_root = report_root / subdir
    if runtime_hash:
        matches = sorted_paths(search_root.glob(f"*{label_pattern}*{runtime_hash}.csv"))
        if matches:
            return matches[0]
    matches = sorted_paths(search_root.glob(f"*{label_pattern}*.csv"))
    if not matches:
        raise FileNotFoundError(f"Could not find report CSV containing '{label_pattern}' under {search_root}.")
    return matches[0]


def archetype_label(archetype: int) -> str:
    labels = {
        0: "A0 SM-SV",
        1: "A1 LB-SV",
        2: "A2 LB-DA",
        3: "A3 CT-DA",
    }
    return labels.get(int(archetype), f"A{int(archetype)}")


def extract_runtime_hash(path: Path) -> str | None:
    match = RUNTIME_HASH_PATTERN.search(path.name)
    return None if match is None else str(match.group(1)).lower()


def stable_alias_table(patient_ids: Iterable[str]) -> pd.DataFrame:
    ids = sorted({str(patient_id) for patient_id in patient_ids})
    return pd.DataFrame(
        {
            "patient_id": ids,
            "patient_alias": [f"sub-{index:02d}" for index in range(1, len(ids) + 1)],
        }
    )


def non_metadata_columns(frame: pd.DataFrame) -> list[str]:
    return [column for column in frame.columns if column not in ARCHETYPE_META_COLUMNS]


def field_state_channel_columns(frame: pd.DataFrame) -> list[str]:
    montage = mne.channels.make_standard_montage("standard_1020")
    valid_names = {name.lower() for name in montage.get_positions()["ch_pos"].keys()}
    return [
        column
        for column in frame.columns
        if column not in ARCHETYPE_META_COLUMNS and str(column).lower() in valid_names
    ]


def absolute_similarity(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    left_array = np.asarray(left, dtype=float)
    right_array = np.asarray(right, dtype=float)
    left_norm = np.linalg.norm(left_array, axis=1, keepdims=True)
    right_norm = np.linalg.norm(right_array, axis=1, keepdims=True)
    left_norm[~np.isfinite(left_norm) | (left_norm == 0.0)] = 1.0
    right_norm[~np.isfinite(right_norm) | (right_norm == 0.0)] = 1.0
    similarity = np.abs((left_array / left_norm) @ (right_array / right_norm).T)
    similarity[~np.isfinite(similarity)] = 0.0
    return similarity


def orient_pattern(pattern: np.ndarray) -> np.ndarray:
    values = np.asarray(pattern, dtype=float)
    if values.size == 0:
        return values
    working = values.copy()
    working[~np.isfinite(working)] = 0.0
    dominant_index = int(np.argmax(np.abs(working)))
    if working[dominant_index] < 0.0:
        working = -working
    return working


def channel_xy(channels: list[str]) -> pd.DataFrame:
    montage = mne.channels.make_standard_montage("standard_1020")
    positions = montage.get_positions()["ch_pos"]
    rows: list[dict[str, float | str]] = []
    for channel in channels:
        key = channel if channel in positions else channel.upper()
        if key not in positions:
            raise KeyError(f"Could not find standard_1020 position for EEG channel: {channel}")
        xyz = np.asarray(positions[key], dtype=float)
        rows.append({"channel": channel, "x_raw": float(xyz[0]), "y_raw": float(xyz[1])})
    frame = pd.DataFrame(rows)
    xy = frame[["x_raw", "y_raw"]].to_numpy(dtype=float)
    xy = xy - xy.mean(axis=0, keepdims=True)
    radius = np.max(np.linalg.norm(xy, axis=1))
    if not np.isfinite(radius) or radius <= 0:
        radius = 1.0
    xy = xy / radius * 0.82
    frame["x"] = xy[:, 0]
    frame["y"] = xy[:, 1]
    return frame[["channel", "x", "y"]]


def build_topomap_tables(
    frame: pd.DataFrame,
    *,
    channel_columns: list[str],
    group_columns: list[str],
    grid_size: int = 96,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    coords = channel_xy(channel_columns)
    sensor_xy = coords[["x", "y"]].to_numpy(dtype=float)
    grid_axis = np.linspace(-1.0, 1.0, grid_size)
    xx, yy = np.meshgrid(grid_axis, grid_axis)
    points = np.column_stack([xx.ravel(), yy.ravel()])
    mask = np.sqrt(points[:, 0] ** 2 + points[:, 1] ** 2) <= 0.98

    value_rows: list[pd.DataFrame] = []
    grid_rows: list[pd.DataFrame] = []
    for _, row in frame.iterrows():
        metadata = {column: row[column] for column in group_columns}
        channel_values = orient_pattern(row[channel_columns].to_numpy(dtype=float))
        value_frame = coords.copy()
        value_frame["value"] = channel_values
        for column, value in metadata.items():
            value_frame[column] = value
        value_rows.append(value_frame)

        interpolator = RBFInterpolator(sensor_xy, channel_values, kernel="thin_plate_spline", smoothing=0.01)
        grid_values = np.full(points.shape[0], np.nan, dtype=float)
        grid_values[mask] = interpolator(points[mask])
        grid_frame = pd.DataFrame(
            {
                "x": points[:, 0],
                "y": points[:, 1],
                "value": grid_values,
                "inside_head": mask,
            }
        )
        for column, value in metadata.items():
            grid_frame[column] = value
        grid_rows.append(grid_frame)

    return pd.concat(value_rows, ignore_index=True), pd.concat(grid_rows, ignore_index=True)


def build_yeo17_coverage_tables(
    patient_ids: list[str],
    patient_reference: pd.DataFrame,
    data_root: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    dynamic_networks: set[str] = set(YEO17_NETWORK_ORDER)
    patient_count_lookup: dict[str, dict[str, int]] = {}
    retained_lookup: dict[str, int] = {}

    for patient_id in patient_ids:
        patient_dir = data_root / patient_id
        fif_path = patient_dir / "bipolar" / "IDE_A_seeg.fif"
        atlas_path = patient_dir / "MNI" / "Atlas.tsv"
        if not fif_path.exists():
            raise FileNotFoundError(f"Missing bipolar IDE_A FIF for patient {patient_id}: {fif_path}")
        if not atlas_path.exists():
            raise FileNotFoundError(f"Missing Atlas.tsv for patient {patient_id}: {atlas_path}")

        annotations = pd.read_csv(atlas_path, sep="\t")
        required_columns = {"Channel", YEO17_ATLAS_COLUMN}
        if not required_columns.issubset(annotations.columns):
            missing = ", ".join(sorted(required_columns - set(annotations.columns)))
            raise ValueError(f"{atlas_path} is missing required columns: {missing}")

        raw = mne.io.read_raw_fif(fif_path, preload=False, verbose="ERROR")
        mapping = build_same_region_bipolar_map(
            annotations[["Channel", YEO17_ATLAS_COLUMN]],
            raw.ch_names,
            patient_id=patient_id,
            atlas_column=YEO17_ATLAS_COLUMN,
            parcellation_name="yeo17",
        )
        valid = mapping.loc[mapping["valid_same_region"]].copy()
        non_background = valid.loc[valid["region"].notna()].copy()
        counts = (
            non_background.groupby("region", as_index=False)
            .agg(n_bipolar_channels=("bipolar_channel", "nunique"))
            .sort_values(["region"])
        )
        dynamic_networks.update(counts["region"].astype(str).tolist())
        patient_count_lookup[patient_id] = {
            str(row["region"]): int(row["n_bipolar_channels"]) for _, row in counts.iterrows()
        }

        reference_row = patient_reference.loc[patient_reference["patient_id"] == patient_id].head(1)
        retained_reference = (
            int(reference_row["effective_bipolar_channels"].iloc[0])
            if not reference_row.empty and pd.notna(reference_row["effective_bipolar_channels"].iloc[0])
            else len(raw.ch_names)
        )
        retained_bipolar_channels = int(len(raw.ch_names))
        retained_lookup[patient_id] = retained_bipolar_channels
        summary_rows.append(
            {
                "patient_id": patient_id,
                "retained_bipolar_channels": retained_bipolar_channels,
                "reference_effective_bipolar_channels": retained_reference,
                "retained_matches_reference": bool(retained_bipolar_channels == retained_reference),
                "mapped_yeo17_bipolar_channels": int(counts["n_bipolar_channels"].sum()) if not counts.empty else 0,
                "covered_yeo17_networks": int(counts.shape[0]),
                "background_same_network_bipolar_channels": int(valid["region"].isna().sum()),
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    ordered_networks = [network for network in YEO17_NETWORK_ORDER if network in dynamic_networks] + [
        network for network in sorted(dynamic_networks) if network not in YEO17_NETWORK_ORDER
    ]
    long_rows: list[dict[str, object]] = []
    for patient_id in patient_ids:
        count_lookup = patient_count_lookup.get(patient_id, {})
        retained_bipolar_channels = retained_lookup.get(patient_id, 0)
        for network in ordered_networks:
            value = int(count_lookup.get(network, 0))
            long_rows.append(
                {
                    "patient_id": patient_id,
                    "network": network,
                    "n_bipolar_channels": value,
                    "coverage_pct": value / retained_bipolar_channels * 100.0 if retained_bipolar_channels > 0 else np.nan,
                }
            )
    long_df = pd.DataFrame(long_rows)
    alias_df = stable_alias_table(summary_df["patient_id"].tolist())
    summary_df = summary_df.merge(alias_df, on="patient_id", how="left")
    long_df = long_df.merge(alias_df, on="patient_id", how="left")
    return summary_df, long_df


def build_transition_tables(report_root: Path, runtime_hash: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    transition_path = discover_report_csv(report_root, "supplementary_tables", "subject_field_state_transition_profiles", runtime_hash)
    transition_df = pd.read_csv(transition_path)
    transition_df["patient_id"] = transition_df["patient_id"].astype(str)
    group_df = (
        transition_df.groupby(["from_state", "to_state"], as_index=False)
        .agg(
            n_subjects=("patient_id", "nunique"),
            mean_transition_probability=("transition_probability", "mean"),
            median_transition_probability=("transition_probability", "median"),
            total_transitions=("n_transitions", "sum"),
        )
        .sort_values(["from_state", "to_state"])
        .reset_index(drop=True)
    )
    transition_df["source_report_csv"] = str(transition_path).replace("\\", "/")
    group_df["source_report_csv"] = str(transition_path).replace("\\", "/")
    return transition_df, group_df


def build_model_order_tables(report_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    subject_path = discover_report_csv(report_root, "supplementary_tables", "field_state_model_order_subject", None)
    group_path = discover_report_csv(report_root, "supplementary_tables", "field_state_model_order_group", None)
    subject_df = pd.read_csv(subject_path)
    group_df = pd.read_csv(group_path)
    subject_df["source_report_csv"] = str(subject_path).replace("\\", "/")
    group_df["source_report_csv"] = str(group_path).replace("\\", "/")
    return subject_df, group_df


def build_archetype_support_tables(cache_root: Path, runtime_hash: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    assignment_path = discover_cache(cache_root, "field_state_archetype_assignments", runtime_hash)
    projection_path = discover_cache(cache_root, "field_state_archetype_projections", runtime_hash)
    archetype_path = discover_cache(cache_root, "field_state_archetypes", runtime_hash)

    assignments = pd.read_parquet(assignment_path)
    projections = pd.read_parquet(projection_path)
    archetypes = pd.read_parquet(archetype_path)
    assignments["patient_id"] = assignments["patient_id"].astype(str)
    projections["patient_id"] = projections["patient_id"].astype(str)

    support_df = (
        assignments.groupby("assigned_archetype", as_index=False)
        .agg(
            n_subjects=("patient_id", "nunique"),
            n_state_assignments=("field_state", "size"),
            mean_similarity=("assignment_similarity", "mean"),
            median_similarity=("assignment_similarity", "median"),
            min_similarity=("assignment_similarity", "min"),
        )
        .sort_values("assigned_archetype")
        .reset_index(drop=True)
    )
    support_df["archetype_label"] = support_df["assigned_archetype"].map(archetype_label)

    channel_columns = [column for column in non_metadata_columns(archetypes) if column in projections.columns]
    archetype_templates = (
        archetypes.sort_values("field_state")[channel_columns]
        .fillna(0.0)
        .to_numpy(dtype=float)
    )

    observed_rows: list[dict[str, object]] = []
    null_rows: list[dict[str, object]] = []
    for patient_id, group in projections.groupby("patient_id", sort=True):
        patient_group = group.sort_values("field_state").reset_index(drop=True)
        similarity = absolute_similarity(
            patient_group[channel_columns].fillna(0.0).to_numpy(dtype=float),
            archetype_templates,
        )
        observed_assignment = (
            assignments.loc[assignments["patient_id"].astype(str) == str(patient_id)]
            .sort_values("field_state")["assigned_archetype"]
            .astype(int)
            .tolist()
        )
        observed_permutation = tuple(observed_assignment)
        field_states = patient_group["field_state"].astype(int).tolist()

        observed_frame = (
            assignments.loc[assignments["patient_id"].astype(str) == str(patient_id)]
            .copy()
            .sort_values("field_state")
        )
        for _, row in observed_frame.iterrows():
            observed_rows.append(
                {
                    "patient_id": str(patient_id),
                    "field_state": int(row["field_state"]),
                    "assigned_archetype": int(row["assigned_archetype"]),
                    "assignment_similarity": float(row["assignment_similarity"]),
                    "source": "observed",
                    "permutation_id": -1,
                }
            )

        perm_counter = 0
        for perm in permutations(range(archetype_templates.shape[0]), len(field_states)):
            if tuple(perm) == observed_permutation:
                continue
            for row_index, archetype_index in enumerate(perm):
                null_rows.append(
                    {
                        "patient_id": str(patient_id),
                        "field_state": int(field_states[row_index]),
                        "assigned_archetype": int(archetype_index),
                        "assignment_similarity": float(similarity[row_index, archetype_index]),
                        "source": "null",
                        "permutation_id": perm_counter,
                    }
                )
            perm_counter += 1

    long_df = pd.DataFrame([*observed_rows, *null_rows])
    long_df["archetype_label"] = long_df["assigned_archetype"].map(archetype_label)
    summary_df = (
        long_df.groupby(["assigned_archetype", "archetype_label", "source"], as_index=False)
        .agg(
            n_rows=("assignment_similarity", "size"),
            mean_similarity=("assignment_similarity", "mean"),
            median_similarity=("assignment_similarity", "median"),
            q05_similarity=("assignment_similarity", lambda values: float(np.quantile(values, 0.05))),
            q95_similarity=("assignment_similarity", lambda values: float(np.quantile(values, 0.95))),
        )
        .sort_values(["assigned_archetype", "source"])
        .reset_index(drop=True)
    )
    return support_df, long_df, summary_df


def build_lag_tables(report_root: Path, runtime_hash: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    lag_path = discover_report_csv(report_root, "main_tables", "archetype_eeg_fine_lag_synchrony", runtime_hash)
    subject_peak_path = discover_report_csv(report_root, "supplementary_tables", "archetype_eeg_fine_lag_subject_peaks", runtime_hash)
    lag_df = pd.read_csv(lag_path)
    subject_df = pd.read_csv(subject_peak_path)
    subject_df["patient_id"] = subject_df["patient_id"].astype(str)
    lag_df["source_report_csv"] = str(lag_path).replace("\\", "/")
    subject_df["source_report_csv"] = str(subject_peak_path).replace("\\", "/")
    alias_df = stable_alias_table(subject_df["patient_id"].astype(str).tolist())
    subject_df = subject_df.merge(alias_df, on="patient_id", how="left")
    return lag_df, subject_df


def build_conditioned_eeg_tables(
    cache_root: Path,
    runtime_hash: str,
    patient_archetype: pd.DataFrame,
    *,
    n_representatives: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    subject_path = discover_cache(cache_root, "subject_archetype_conditioned_eeg_maps", runtime_hash)
    group_path = discover_cache(cache_root, "group_archetype_conditioned_eeg_maps", runtime_hash)
    subject_maps = pd.read_parquet(subject_path)
    group_maps = pd.read_parquet(group_path)
    subject_maps["patient_id"] = subject_maps["patient_id"].astype(str)
    patient_archetype = patient_archetype.copy()
    patient_archetype["patient_id"] = patient_archetype["patient_id"].astype(str)

    metrics = (
        patient_archetype[["patient_id", "archetype", "assignment_similarity", "occupancy", "mean_dwell_ms", "n_peak_maps"]]
        .drop_duplicates(["patient_id", "archetype"])
        .rename(columns={"archetype": "assigned_archetype"})
    )
    alias_df = stable_alias_table(subject_maps["patient_id"].astype(str).tolist())

    subject_maps = (
        subject_maps.merge(metrics, on=["patient_id", "assigned_archetype"], how="left")
        .merge(alias_df, on="patient_id", how="left")
        .sort_values(["patient_id", "assigned_archetype"])
        .reset_index(drop=True)
    )
    subject_maps["archetype_label"] = subject_maps["assigned_archetype"].map(archetype_label)

    subject_summary = (
        subject_maps.groupby(["patient_id", "patient_alias"], as_index=False)
        .agg(
            n_archetypes_present=("assigned_archetype", "nunique"),
            total_conditioned_samples=("n_samples", "sum"),
            min_conditioned_samples=("n_samples", "min"),
            mean_assignment_similarity=("assignment_similarity", "mean"),
            mean_occupancy=("occupancy", "mean"),
            mean_dwell_ms=("mean_dwell_ms", "mean"),
        )
    )
    expected_states = int(subject_maps["assigned_archetype"].nunique())
    subject_summary["complete_archetype_panel"] = subject_summary["n_archetypes_present"] == expected_states
    subject_summary = subject_summary.sort_values(
        ["complete_archetype_panel", "min_conditioned_samples", "mean_assignment_similarity", "total_conditioned_samples", "patient_id"],
        ascending=[False, False, False, False, True],
    ).reset_index(drop=True)
    subject_summary["representative_rank"] = np.arange(1, len(subject_summary) + 1)

    representative_subjects = subject_summary.loc[subject_summary["complete_archetype_panel"]].head(int(n_representatives)).copy()
    if representative_subjects.empty:
        representative_subjects = subject_summary.head(int(n_representatives)).copy()

    representative_ids = representative_subjects["patient_id"].astype(str).tolist()
    representative_maps = subject_maps.loc[subject_maps["patient_id"].astype(str).isin(representative_ids)].copy()
    representative_maps = representative_maps.merge(
        representative_subjects[["patient_id", "representative_rank"]],
        on="patient_id",
        how="left",
    )
    representative_maps["patient_display"] = representative_maps["patient_alias"]
    representative_maps = representative_maps.sort_values(["representative_rank", "assigned_archetype"]).reset_index(drop=True)

    group_maps = group_maps.copy()
    group_maps["patient_alias"] = "group"
    group_maps["patient_display"] = "Group"
    group_maps["archetype_label"] = group_maps["assigned_archetype"].map(archetype_label)

    channel_columns = field_state_channel_columns(subject_maps)
    topomap_panels = pd.concat(
        [
            group_maps.assign(representative_rank=0),
            representative_maps,
        ],
        ignore_index=True,
        sort=False,
    )
    group_columns = ["patient_id", "patient_alias", "patient_display", "representative_rank", "assigned_archetype", "archetype_label", "n_samples"]
    topomap_values, topomap_grid = build_topomap_tables(
        topomap_panels[group_columns + channel_columns],
        channel_columns=channel_columns,
        group_columns=group_columns,
    )
    return group_maps, subject_maps, subject_summary, representative_subjects, topomap_values, topomap_grid


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False)


def main() -> None:
    args = parse_args()
    runtime_hash = str(args.runtime_hash).lower()
    cache_root = resolve_path(args.cache_root)
    data_root = resolve_path(args.data_root)
    report_root = resolve_path(args.report_root)
    patient_archetype_path = resolve_path(args.patient_archetype_csv)
    output_dir = ensure_dir(resolve_path(args.output_dir))
    stem = output_stem(runtime_hash)

    patient_archetype = pd.read_csv(patient_archetype_path)
    patient_archetype["patient_id"] = patient_archetype["patient_id"].astype(str)
    patient_reference = (
        patient_archetype[["patient_id", "effective_bipolar_channels", "mapped_yeo17_bipolar_channels", "covered_yeo17_networks"]]
        .drop_duplicates("patient_id")
        .reset_index(drop=True)
    )
    patient_ids = sorted(patient_reference["patient_id"].astype(str).tolist())

    yeo17_summary, yeo17_long = build_yeo17_coverage_tables(patient_ids, patient_reference, data_root)
    transition_subject, transition_group = build_transition_tables(report_root, runtime_hash)
    model_order_subject, model_order_group = build_model_order_tables(report_root)
    support_summary, assignment_null_long, assignment_null_summary = build_archetype_support_tables(cache_root, runtime_hash)
    lag_curve, lag_subject = build_lag_tables(report_root, runtime_hash)
    group_maps, subject_maps, subject_summary, representative_subjects, topomap_values, topomap_grid = build_conditioned_eeg_tables(
        cache_root,
        runtime_hash,
        patient_archetype,
        n_representatives=int(args.n_representatives),
    )

    manifest_rows = [
        ("yeo17_coverage_summary", f"{stem}_yeo17_coverage_summary.csv", "Patient-level retained bipolar counts and Yeo17 coverage summary."),
        ("yeo17_coverage_long", f"{stem}_yeo17_coverage_long.csv", "Patient x Yeo17 network bipolar-channel coverage counts."),
        ("field_state_transition_subject", f"{stem}_field_state_transition_subject.csv", "Subject-level SEEG field-state transition profiles."),
        ("field_state_transition_group", f"{stem}_field_state_transition_group.csv", "Group-averaged SEEG field-state transition matrix."),
        ("field_state_model_order_subject", f"{stem}_field_state_model_order_subject.csv", "Subject-level K=2..7 field-state model-order diagnostics."),
        ("field_state_model_order_group", f"{stem}_field_state_model_order_group.csv", "Group-level K=2..7 field-state model-order diagnostics."),
        ("archetype_support_summary", f"{stem}_archetype_support_summary.csv", "Archetype support counts and observed assignment similarity summary."),
        ("assignment_similarity_null_long", f"{stem}_assignment_similarity_null_long.csv", "Observed and permuted assignment-similarity distributions."),
        ("assignment_similarity_null_summary", f"{stem}_assignment_similarity_null_summary.csv", "Observed and permuted assignment-similarity summary statistics."),
        ("archetype_eeg_fine_lag_curve", f"{stem}_archetype_eeg_fine_lag_curve.csv", "Group fine-lag coupling summary with null mean reference."),
        ("archetype_eeg_subject_peaks", f"{stem}_archetype_eeg_subject_peaks.csv", "Subject-level peak lag, width, observed, and null coupling summaries."),
        ("conditioned_eeg_group_maps_wide", f"{stem}_conditioned_eeg_group_maps_wide.csv", "Group-level archetype-conditioned EEG scalp maps in wide channel format."),
        ("conditioned_eeg_subject_maps_wide", f"{stem}_conditioned_eeg_subject_maps_wide.csv", "Patient-level archetype-conditioned EEG scalp maps in wide channel format."),
        ("conditioned_eeg_subject_summary", f"{stem}_conditioned_eeg_subject_summary.csv", "Patient-level support and ranking metrics for representative subject selection."),
        ("conditioned_eeg_representative_subjects", f"{stem}_conditioned_eeg_representative_subjects.csv", "Selected representative subjects for manuscript plotting."),
        ("conditioned_eeg_topomap_values", f"{stem}_conditioned_eeg_topomap_values.csv", "Channel-position/value tables for group and representative conditioned EEG topomaps."),
        ("conditioned_eeg_topomap_grid", f"{stem}_conditioned_eeg_topomap_grid.csv", "Interpolated topomap grid for group and representative conditioned EEG panels."),
    ]

    outputs = {
        f"{stem}_yeo17_coverage_summary.csv": yeo17_summary,
        f"{stem}_yeo17_coverage_long.csv": yeo17_long,
        f"{stem}_field_state_transition_subject.csv": transition_subject,
        f"{stem}_field_state_transition_group.csv": transition_group,
        f"{stem}_field_state_model_order_subject.csv": model_order_subject,
        f"{stem}_field_state_model_order_group.csv": model_order_group,
        f"{stem}_archetype_support_summary.csv": support_summary,
        f"{stem}_assignment_similarity_null_long.csv": assignment_null_long,
        f"{stem}_assignment_similarity_null_summary.csv": assignment_null_summary,
        f"{stem}_archetype_eeg_fine_lag_curve.csv": lag_curve,
        f"{stem}_archetype_eeg_subject_peaks.csv": lag_subject,
        f"{stem}_conditioned_eeg_group_maps_wide.csv": group_maps,
        f"{stem}_conditioned_eeg_subject_maps_wide.csv": subject_maps,
        f"{stem}_conditioned_eeg_subject_summary.csv": subject_summary,
        f"{stem}_conditioned_eeg_representative_subjects.csv": representative_subjects,
        f"{stem}_conditioned_eeg_topomap_values.csv": topomap_values,
        f"{stem}_conditioned_eeg_topomap_grid.csv": topomap_grid,
    }

    for file_name, frame in outputs.items():
        write_csv(frame, output_dir / file_name)

    manifest = pd.DataFrame(
        [
            {
                "item": item,
                "file_name": file_name,
                "path": str((output_dir / file_name).resolve()).replace("\\", "/"),
                "description": description,
            }
            for item, file_name, description in manifest_rows
        ]
    )
    manifest.to_csv(output_dir / f"{stem}_manifest.csv", index=False)


if __name__ == "__main__":
    main()
