# SEEG-EEG Microstates

This repository contains a cached, function-oriented analysis pipeline for studying synchronized scalp EEG and intracranial SEEG microstates in the `IDE_A` resting-state segment. The current implementation focuses on two branches:

- EEG microstates from restored 19-channel scalp EEG and SEEG Yeo17-network HFA coupling
- Cross-modal EEG/SEEG microstate comparison in the `1-40 Hz` band

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
uv run seeg-eegmicrostates run-eeg --branch main
uv run seeg-eegmicrostates run-seeg-hfa
uv run seeg-eegmicrostates run-hfa-coupling
uv run seeg-eegmicrostates run-band-1-40
uv run seeg-eegmicrostates run-band-1-40-connectivity --method all
uv run seeg-eegmicrostates render-reports
```

What each command does:

- `build-index`: scans recordings, loads workbook metadata, builds `IDE_A` segments, and filters the main cohort.
- `run-eeg`: preprocesses EEG, restores 19 channels, fits group microstate templates, and writes label tables.
- `run-seeg-hfa`: maps bipolar channels to same-network Yeo17 pairs and computes HFA/network summaries.
- `run-hfa-coupling`: aligns EEG labels with network HFA and computes subject/group effects.
- `run-band-1-40`: runs the parallel `1-40 Hz` EEG and SEEG microstate branch with cross-modal summaries.
- `run-band-1-40-connectivity`: estimates EEG-state-conditioned Yeo17 network connectivity from cached `1-40 Hz` SEEG network time series using `corr`, `PLV`, or `wPLI`.
- `render-reports`: writes QC figures and summary plots from cached results.

## Outputs

Artifacts are written under:

- `artifacts/cache/`: indexed tables, preprocessed FIF files, label tables, network summaries, and statistics
- `artifacts/reports/figures/`: coverage plots, microstate templates, HFA heatmaps, and cross-modal overlap figures
- `artifacts/reports/tables/`: Excel exports of cross-modal summaries and subject/group effect tables

Cache filenames are branch-specific and include a config hash so parameter changes do not silently overwrite earlier runs.

## Source Layout

- `src/seeg_eegmicrostates/io`: workbook, FIF, atlas, and repository scanning helpers
- `src/seeg_eegmicrostates/eeg`: EEG preprocessing, montage restoration, and `pycrostates` model fitting
- `src/seeg_eegmicrostates/seeg`: bipolar mapping, HFA extraction, network aggregation, and SEEG microstates
- `src/seeg_eegmicrostates/coupling` and `stats`: alignment, effect estimation, permutation testing, and FDR correction
- `src/seeg_eegmicrostates/workflows`: cache-aware pipeline entry points used by the CLI

OpenSpec change artifacts for the current implementation live in `openspec/changes/`.
