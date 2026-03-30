# SEEG-EEG Microstates

This repository contains a cached, staged analysis pipeline for studying synchronized scalp EEG microstates and intracranial SEEG Yeo17 network dynamics in the `IDE_A` resting-state segment. The public workflow is centered on a single `1-40 Hz` path:

- `1-40 Hz` EEG microstate state generation
- `1-40 Hz` SEEG Yeo17 network signal generation
- supplemental EEG-state-conditioned activity effects
- primary EEG-state-conditioned connectivity effects (`corr`, `PLV`, `wPLI`)

The code is organized for recomputation from intermediate artifacts rather than notebook-only analysis.

## Data Assumptions

The default configuration expects:

- `datas/data_01_seeg/<patient>/ref/*.fif`
- `datas/data_01_seeg/<patient>/bipolar/*.fif`
- `datas/data_01_seeg/<patient>/MNI/Atlas.tsv`
- `datas/info_patient.xlsx`

`IDE_A` timing is read from the workbook. EEG channels are normalized to the shared 11-channel set (`F3/Fz/F4/C3/Cz/C4/P3/Pz/P4/O1/O2`), then expanded to a standard 19-channel montage by adding missing channels as bads and restoring them with interpolation.

## Setup

```bash
uv sync
uv run pytest -q
```

The project requires Python `>=3.13` and uses `mne`, `pycrostates`, `pandas`, and `openpyxl`.

## CLI Workflows

```bash
uv run seeg-eegmicrostates build-index
uv run seeg-eegmicrostates run-eeg-states
uv run seeg-eegmicrostates run-seeg-networks
uv run seeg-eegmicrostates run-activity-effects
uv run seeg-eegmicrostates run-connectivity-effects --method all
uv run seeg-eegmicrostates render-reports
```

What each command does:

- `build-index`: scans recordings, loads workbook metadata, builds `IDE_A` segments, and filters the main cohort.
- `run-eeg-states`: preprocesses EEG, restores 19 channels, fits `1-40 Hz` EEG microstate templates, and writes reusable state labels.
- `run-seeg-networks`: maps bipolar channels to same-network Yeo17 pairs and computes reusable `1-40 Hz` network time series.
- `run-activity-effects`: computes supplemental EEG-state-conditioned Yeo17 activity effects from the staged caches.
- `run-connectivity-effects`: computes primary EEG-state-conditioned Yeo17 network connectivity effects from the staged caches using `corr`, `PLV`, `wPLI`, or all methods.
- `render-reports`: writes QC figures and summary plots from cached results.

## Outputs

Artifacts are written under:

- `artifacts/cache/`: indexed tables, preprocessed FIF files, label tables, staged network summaries, and statistics
- `artifacts/reports/figures/`: coverage plots, `1-40 Hz` microstate templates, supplemental activity heatmaps, and primary connectivity figures
- `artifacts/reports/tables/`: Excel exports of supplemental activity and primary connectivity result tables

Cache filenames are branch-specific and include a config hash so parameter changes do not silently overwrite earlier runs.

## Source Layout

- `src/seeg_eegmicrostates/io`: workbook, FIF, atlas, and repository scanning helpers
- `src/seeg_eegmicrostates/eeg`: EEG preprocessing, montage restoration, and `pycrostates` model fitting
- `src/seeg_eegmicrostates/seeg`: bipolar mapping, HFA extraction, network aggregation, and SEEG microstates
- `src/seeg_eegmicrostates/coupling` and `stats`: alignment, effect estimation, permutation testing, and FDR correction
- `src/seeg_eegmicrostates/workflows`: cache-aware pipeline entry points used by the CLI

OpenSpec change artifacts for the current implementation live in `openspec/changes/`.
