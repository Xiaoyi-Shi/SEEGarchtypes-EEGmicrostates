# SEEG-EEG Microstates

This repository contains a cached, staged analysis pipeline for studying synchronized scalp EEG microstates and intracranial SEEG `AAL3` region dynamics in the `IDE_A` resting-state segment. The public workflow is centered on a single `1-40 Hz` path:

- `1-40 Hz` EEG microstate state generation
- `1-40 Hz` SEEG `AAL3` region signal generation
- EEG-state-conditioned `AAL3` activity profiles plus four-state omnibus/post-hoc outputs
- EEG-state-conditioned `AAL3` connectivity profiles plus four-state omnibus/post-hoc outputs (`corr`, `PLV`, `wPLI`)

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
uv sync --dev
uv run pytest -q
```

The project requires Python `>=3.13` and uses `mne`, `pycrostates`, `pandas`, and `openpyxl`.

## CLI Workflows

```bash
uv run seeg-eegmicrostates build-index
uv run seeg-eegmicrostates run-eeg-states
uv run seeg-eegmicrostates run-eeg-states --template-fif path/to/group_template.fif
uv run seeg-eegmicrostates run-seeg-regions
uv run seeg-eegmicrostates run-activity-effects
uv run seeg-eegmicrostates run-connectivity-effects --method all
uv run seeg-eegmicrostates run-exploratory-coupling --analysis all
uv run seeg-eegmicrostates render-reports
```

What each command does:

- `build-index`: scans recordings, loads workbook metadata, builds `IDE_A` segments, and filters the main cohort.
- `run-eeg-states`: preprocesses EEG, restores 19 channels, loads the default `pycrostates` `ModKMeans` template at `artifacts/cache/eeg/ModK.fif`, caches a copy of the active template as `group_microstate_model_*`, and writes reusable state labels.
- `run-seeg-regions`: maps bipolar channels to same-region `AAL3` pairs, rescales them onto the shared `250 Hz` analysis grid, and computes reusable raw-scale `1-40 Hz` region time series.
- `run-activity-effects`: computes EEG-state-conditioned `AAL3` activity profiles together with four-state omnibus and pairwise post-hoc summaries from the staged caches.
- `run-connectivity-effects`: computes primary EEG-state-conditioned `AAL3` region connectivity profiles together with omnibus and pairwise post-hoc summaries from the staged caches using `corr`, `PLV`, `wPLI`, or all methods.
- `run-exploratory-coupling`: runs opt-in exploratory coupling analyses on top of the staged EEG labels and `AAL3` region signals. Supported analyses are `event-activity`, `event-connectivity`, `windowed-coupling`, `transition-coupling`, or `all`.
- `render-reports`: writes QC figures and Excel exports from cached results.

By default, EEG state staging uses `artifacts/cache/eeg/ModK.fif`. The `--template-fif` option overrides that default with another compatible `pycrostates` `.fif` cluster solution fitted on either the shared 11-channel montage (`F3/Fz/F4/C3/Cz/C4/P3/Pz/P4/O1/O2`) or the restored 19-channel EEG layout used by this workflow.

Exploratory analyses are intentionally opt-in and do not change the default staged pipeline. Useful examples:

```bash
uv run seeg-eegmicrostates run-exploratory-coupling --analysis event-activity --event-window-sec 1.5
uv run seeg-eegmicrostates run-exploratory-coupling --analysis event-connectivity --method plv --event-window-sec 1.0
uv run seeg-eegmicrostates run-exploratory-coupling --analysis windowed-coupling --window-sec 20
uv run seeg-eegmicrostates run-exploratory-coupling --analysis transition-coupling --min-subjects 7
```

The exploratory stages share staged EEG event and transition tables, write branch-hashed cache artifacts, and are picked up automatically by `render-reports` when their caches are present.

To rerun the main workflow from scratch, execute the commands in order:

```bash
uv run seeg-eegmicrostates build-index
uv run seeg-eegmicrostates run-eeg-states
uv run seeg-eegmicrostates run-seeg-regions
uv run seeg-eegmicrostates run-activity-effects
uv run seeg-eegmicrostates run-connectivity-effects --method all
uv run seeg-eegmicrostates render-reports
```

## Outputs

Artifacts are written under:

- `artifacts/cache/`: reusable indexed tables, preprocessed FIF files, label tables, staged region summaries, and statistics
- `artifacts/cache/coupling/` and `artifacts/cache/stats/`: also hold exploratory event-locked, windowed, and transition summaries under hashed `explore_*` branches
- `artifacts/cache/seeg/`: includes staged `AAL3` region mappings, coverage tables, and per-patient `1-40 Hz` region time series used by downstream activity and connectivity stages
- `artifacts/cache/eeg/`: includes the active EEG template copy `group_microstate_model_*.fif`, preprocessed FIF files, restored-channel tables, and downstream microstate label tables
- `artifacts/runs/<YYYYMMDD_HHMMSS>/reports/figures/`: figures produced by a specific CLI command invocation
- `artifacts/runs/<YYYYMMDD_HHMMSS>/reports/tables/`: Excel exports produced by a specific CLI command invocation
- `artifacts/runs/<YYYYMMDD_HHMMSS>/logs/`: per-command logs with command, timing, config hash, and output paths

Each CLI command gets its own timestamped run directory. A full end-to-end pipeline therefore creates multiple sibling folders under `artifacts/runs/`, while cache reuse is still keyed only by the branch-specific config hash.

In practice:

- `build-index`, `run-eeg-states`, `run-seeg-regions`, `run-activity-effects`, and `run-connectivity-effects` primarily update `artifacts/cache/` and write a command log
- `render-reports` reads the existing caches and emits the user-facing figures and Excel tables under its own run directory

Cache filenames are branch-specific and include a config hash so parameter changes do not silently overwrite earlier runs.

## Source Layout

- `src/seeg_eegmicrostates/io`: workbook, FIF, atlas, and repository scanning helpers
- `src/seeg_eegmicrostates/eeg`: EEG preprocessing, montage restoration, and `pycrostates` model fitting
- `src/seeg_eegmicrostates/seeg`: bipolar mapping, region aggregation, and SEEG preprocessing helpers
- `src/seeg_eegmicrostates/coupling` and `stats`: alignment, effect estimation, permutation testing, and FDR correction
- `src/seeg_eegmicrostates/workflows`: cache-aware pipeline entry points used by the CLI

OpenSpec change artifacts for the current implementation live in `openspec/changes/`.
