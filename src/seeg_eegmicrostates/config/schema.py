from __future__ import annotations

from dataclasses import dataclass, field
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

YEO17_NETWORKS: tuple[str, ...] = (
    "ContA",
    "ContB",
    "ContC",
    "DefaultA",
    "DefaultB",
    "DefaultC",
    "DorsAttnA",
    "DorsAttnB",
    "LimbicA",
    "LimbicB",
    "SalVentAttnA",
    "SalVentAttnB",
    "SomMotA",
    "SomMotB",
    "TempPar",
    "VisCent",
    "VisPeri",
)


def _sanitize_branch(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    data_root: Path = Path("datas/data_01_seeg")
    workbook_path: Path = Path("datas/info_patient.xlsx")
    artifact_root: Path = Path("artifacts")
    eeg_montage_name: str = "standard_1020"
    eeg_microstate_band: tuple[float, float] = (2.0, 20.0)
    band_limited_range: tuple[float, float] = (1.0, 40.0)
    seeg_hfa_band: tuple[float, float] = (70.0, 150.0)
    eeg_resample_hz: float = 250.0
    seeg_resample_hz: float = 100.0
    microstate_k: int = 4
    microstate_n_init: int = 20
    microstate_max_iter: int = 300
    gfp_peak_sample_size: int = 500
    gfp_min_peak_distance_ms: int = 10
    min_microstate_duration_ms: int = 30
    random_seed: int = 42
    min_network_subjects: int = 7
    min_network_pairs_per_subject: int = 2
    cross_modal_lag_window_sec: float = 2.0
    standard11_channels: tuple[str, ...] = field(default=STANDARD11_CHANNELS)
    target19_channels: tuple[str, ...] = field(default=TARGET19_CHANNELS)
    yeo17_networks: tuple[str, ...] = field(default=YEO17_NETWORKS)

    @property
    def cache_root(self) -> Path:
        return self.artifact_root / "cache"

    @property
    def reports_root(self) -> Path:
        return self.artifact_root / "reports"

    @property
    def logs_root(self) -> Path:
        return self.artifact_root / "logs"

    @property
    def runtime_hash(self) -> str:
        return config_hash(self)

    def ensure_runtime_directories(self) -> dict[str, Path]:
        directories = {
            "artifact_root": ensure_directory(self.artifact_root),
            "cache_root": ensure_directory(self.cache_root),
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
