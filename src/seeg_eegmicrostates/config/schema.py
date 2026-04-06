from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re

from seeg_eegmicrostates._utils import config_hash, ensure_directory


STANDARD11_CHANNELS: tuple[str, ...] = (
    "F3",
    "Fz",
    "F4",
    "C3",
    "Cz",
    "C4",
    "P3",
    "Pz",
    "P4",
    "O1",
    "O2",
)

TARGET19_CHANNELS: tuple[str, ...] = (
    "Fp1",
    "Fp2",
    "F7",
    "F3",
    "Fz",
    "F4",
    "F8",
    "T7",
    "C3",
    "Cz",
    "C4",
    "T8",
    "P7",
    "P3",
    "Pz",
    "P4",
    "P8",
    "O1",
    "O2",
)

SEEG_PARCELLATION_NAME = "aal3"
SEEG_PARCELLATION_COLUMN = "AAL3"
DEFAULT_EEG_TEMPLATE_RELPATH = Path("cache/eeg/ModK.fif")


def _sanitize_branch(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()


def _default_run_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    data_root: Path = Path("datas/data_01_seeg")
    workbook_path: Path = Path("datas/info_patient.xlsx")
    artifact_root: Path = Path("artifacts")
    run_timestamp: str = field(default_factory=_default_run_timestamp)
    default_eeg_template_relpath: Path = DEFAULT_EEG_TEMPLATE_RELPATH
    eeg_montage_name: str = "standard_1020"
    band_limited_range: tuple[float, float] = (1.0, 40.0)
    eeg_resample_hz: float = 250.0
    seeg_resample_hz: float = 250.0
    seeg_signal_scaling: str = "raw"
    microstate_k: int = 4
    microstate_n_init: int = 20
    microstate_max_iter: int = 300
    gfp_peak_sample_size: int = 500
    gfp_min_peak_distance_ms: int = 10
    min_microstate_duration_ms: int = 30
    random_seed: int = 42
    min_group_subjects: int = 7
    seeg_parcellation_name: str = SEEG_PARCELLATION_NAME
    seeg_parcellation_column: str = SEEG_PARCELLATION_COLUMN
    standard11_channels: tuple[str, ...] = field(default=STANDARD11_CHANNELS)
    target19_channels: tuple[str, ...] = field(default=TARGET19_CHANNELS)

    @property
    def cache_root(self) -> Path:
        return self.artifact_root / "cache"

    @property
    def runs_root(self) -> Path:
        return self.artifact_root / "runs"

    @property
    def run_root(self) -> Path:
        return self.runs_root / self.run_timestamp

    @property
    def reports_root(self) -> Path:
        return self.run_root / "reports"

    @property
    def logs_root(self) -> Path:
        return self.run_root / "logs"

    @property
    def default_eeg_template_fif(self) -> Path:
        return self.artifact_root / self.default_eeg_template_relpath

    @property
    def runtime_hash(self) -> str:
        return config_hash(
            {
                "data_root": self.data_root,
                "workbook_path": self.workbook_path,
                "artifact_root": self.artifact_root,
                "default_eeg_template_relpath": self.default_eeg_template_relpath,
                "eeg_montage_name": self.eeg_montage_name,
                "band_limited_range": self.band_limited_range,
                "eeg_resample_hz": self.eeg_resample_hz,
                "seeg_resample_hz": self.seeg_resample_hz,
                "seeg_signal_scaling": self.seeg_signal_scaling,
                "microstate_k": self.microstate_k,
                "microstate_n_init": self.microstate_n_init,
                "microstate_max_iter": self.microstate_max_iter,
                "gfp_peak_sample_size": self.gfp_peak_sample_size,
                "gfp_min_peak_distance_ms": self.gfp_min_peak_distance_ms,
                "min_microstate_duration_ms": self.min_microstate_duration_ms,
                "random_seed": self.random_seed,
                "min_group_subjects": self.min_group_subjects,
                "seeg_parcellation_name": self.seeg_parcellation_name,
                "seeg_parcellation_column": self.seeg_parcellation_column,
                "standard11_channels": self.standard11_channels,
                "target19_channels": self.target19_channels,
            }
        )

    def ensure_runtime_directories(self) -> dict[str, Path]:
        directories = {
            "artifact_root": ensure_directory(self.artifact_root),
            "cache_root": ensure_directory(self.cache_root),
            "runs_root": ensure_directory(self.runs_root),
            "run_root": ensure_directory(self.run_root),
            "reports_root": ensure_directory(self.reports_root),
            "logs_root": ensure_directory(self.logs_root),
        }
        for subdir in (
            "index",
            "segments",
            "eeg",
            "seeg",
            "coupling",
            "stats",
            "reports",
        ):
            directories[subdir] = ensure_directory(self.cache_root / subdir)
        for subdir in ("qc", "tables", "figures"):
            directories[f"reports_{subdir}"] = ensure_directory(self.reports_root / subdir)
        return directories

    def branch_name(self, branch: str) -> str:
        return _sanitize_branch(branch)

    def cache_path(
        self,
        category: str,
        stem: str,
        *,
        ext: str,
        branch: str = "main",
        patient_id: str | None = None,
    ) -> Path:
        category_dir = ensure_directory(self.cache_root / category)
        branch_token = self.branch_name(branch)
        patient_token = f"{patient_id}_" if patient_id else ""
        filename = f"{patient_token}{stem}_{branch_token}_{self.runtime_hash}.{ext.lstrip('.')}"
        return category_dir / filename

    def report_path(self, stem: str, *, ext: str, subdir: str = "figures", branch: str = "main") -> Path:
        directory = ensure_directory(self.reports_root / subdir)
        filename = f"{stem}_{self.branch_name(branch)}_{self.runtime_hash}.{ext.lstrip('.')}"
        return directory / filename

    def log_path(self, stem: str, *, ext: str = "log") -> Path:
        directory = ensure_directory(self.logs_root)
        filename = f"{self.branch_name(stem)}_{self.runtime_hash}.{ext.lstrip('.')}"
        return directory / filename
