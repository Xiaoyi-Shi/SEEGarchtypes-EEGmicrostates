# SEEG-EEG Microstates

This repository contains a cached, staged analysis pipeline for studying synchronized scalp EEG microstates and intracranial SEEG dynamics in resting-state IDE segments. The public workflow defaults to `IDE_A`, supports `IDE_S` as an optional override, and is centered on a single `1-40 Hz` path:

- `1-40 Hz` EEG microstate state generation
- `1-40 Hz` SEEG `AAL3` region signal generation
- EEG-state-conditioned `AAL3` activity profiles plus four-state omnibus/post-hoc outputs
- EEG-state-conditioned `AAL3` connectivity profiles plus four-state omnibus/post-hoc outputs (`corr`, `PLV`, `wPLI`)
- opt-in exploratory branches for direct EEG-SEEG state coupling and Yeo17 GFP-informed global coupling

The code is organized for recomputation from intermediate artifacts rather than notebook-only analysis.

## Data Assumptions

The default configuration expects:

- `datas/data_01_seeg/<patient>/ref/*.fif`
- `datas/data_01_seeg/<patient>/bipolar/*.fif`
- `datas/data_01_seeg/<patient>/MNI/Atlas.tsv`
- `datas/info_patient.xlsx`

Timing for the selected analysis state is read from the workbook. EEG channels are normalized to the shared 11-channel set (`F3/Fz/F4/C3/Cz/C4/P3/Pz/P4/O1/O2`), then expanded to a standard 19-channel montage by adding missing channels as bads and restoring them with interpolation.

## Setup

```bash
uv sync --dev
uv run pytest -q
```

The project requires Python `>=3.13` and uses `mne`, `pycrostates`, `pandas`, and `openpyxl`.

## CLI Workflows

```bash
uv run seeg-eegmicrostates build-index
uv run seeg-eegmicrostates build-index --analysis-state IDE_S
uv run seeg-eegmicrostates run-eeg-states
uv run seeg-eegmicrostates run-eeg-states --template-fif path/to/group_template.fif
uv run seeg-eegmicrostates run-seeg-regions
uv run seeg-eegmicrostates run-activity-effects
uv run seeg-eegmicrostates run-connectivity-effects --method all
uv run seeg-eegmicrostates run-exploratory-coupling --analysis all
uv run seeg-eegmicrostates render-reports
```

If you want multiple staged commands to share one run folder, pass the same `--run-id` to each command:

```bash
uv run seeg-eegmicrostates build-index --run-id 20260406_230000
uv run seeg-eegmicrostates run-eeg-states --run-id 20260406_230000
uv run seeg-eegmicrostates run-seeg-regions --run-id 20260406_230000
uv run seeg-eegmicrostates run-activity-effects --run-id 20260406_230000
uv run seeg-eegmicrostates run-connectivity-effects --method all --run-id 20260406_230000
uv run seeg-eegmicrostates render-reports --run-id 20260406_230000
```

What each command does:

- `build-index`: scans recordings, loads workbook metadata, builds segments for the selected analysis state (`IDE_A` by default, `IDE_S` optionally), and filters the main cohort.
- `run-eeg-states`: preprocesses EEG, restores 19 channels, loads the configured default `pycrostates` `ModKMeans` template at `artifacts/cache/eeg/ModK.fif` unless `--template-fif` overrides it, caches a copy of the active template as `group_microstate_model_*`, and writes reusable state labels together with aligned EEG GFP traces and GFP peak tables.
- `run-seeg-regions`: maps bipolar channels to same-region `AAL3` pairs, rescales them onto the shared `250 Hz` analysis grid, and computes reusable raw-scale `1-40 Hz` region time series.
- `run-activity-effects`: computes EEG-state-conditioned `AAL3` activity profiles together with four-state omnibus and pairwise post-hoc summaries from the staged caches.
- `run-connectivity-effects`: computes primary EEG-state-conditioned `AAL3` region connectivity profiles together with omnibus and pairwise post-hoc summaries from the staged caches using `corr`, `PLV`, `wPLI`, or all methods.
- `run-exploratory-coupling`: runs opt-in exploratory coupling analyses on top of the staged EEG labels, staged EEG GFP artifacts, and staged SEEG signals. Supported analyses are `event-activity`, `event-connectivity`, `windowed-coupling`, `transition-coupling`, `direct-state-coupling`, `lagged-state-coupling`, `transition-state-coupling`, `gfp-global-coupling`, `lagged-gfp-global-coupling`, `peak-gfp-global-coupling`, `gfp-controlled-microstate`, `gfp-controlled-transition`, or `all`.
- `render-reports`: writes figures and Excel exports from cached results.

By default, EEG state staging uses the configured default template file `artifacts/cache/eeg/ModK.fif`. The `--template-fif` option overrides that default with another compatible `pycrostates` `.fif` cluster solution fitted on either the shared 11-channel montage (`F3/Fz/F4/C3/Cz/C4/P3/Pz/P4/O1/O2`) or the restored 19-channel EEG layout used by this workflow. If neither the override nor the configured default template exists, the EEG stage stops before labeling.

Exploratory analyses are intentionally opt-in and do not change the default staged pipeline. Useful examples:

```bash
uv run seeg-eegmicrostates run-exploratory-coupling --analysis event-activity --event-window-sec 1.5
uv run seeg-eegmicrostates run-exploratory-coupling --analysis event-connectivity --method plv --event-window-sec 1.0
uv run seeg-eegmicrostates run-exploratory-coupling --analysis windowed-coupling --window-sec 20
uv run seeg-eegmicrostates run-exploratory-coupling --analysis transition-coupling --min-subjects 7
uv run seeg-eegmicrostates run-exploratory-coupling --analysis direct-state-coupling --direct-backend pca-kmeans
uv run seeg-eegmicrostates run-exploratory-coupling --analysis lagged-state-coupling --max-lag-ms 200 --lag-step-ms 40
uv run seeg-eegmicrostates run-exploratory-coupling --analysis transition-state-coupling --transition-window-sec 0.5
uv run seeg-eegmicrostates run-exploratory-coupling --analysis gfp-global-coupling --seeg-parcellation-name yeo17
uv run seeg-eegmicrostates run-exploratory-coupling --analysis lagged-gfp-global-coupling --seeg-parcellation-name yeo17 --global-metric all
uv run seeg-eegmicrostates run-exploratory-coupling --analysis peak-gfp-global-coupling --seeg-parcellation-name yeo17 --peak-window-sec 0.5
uv run seeg-eegmicrostates run-exploratory-coupling --analysis gfp-controlled-microstate --seeg-parcellation-name yeo17
uv run seeg-eegmicrostates run-exploratory-coupling --analysis gfp-controlled-transition --seeg-parcellation-name yeo17 --transition-window-sec 0.25
```

The exploratory stages share staged EEG event and transition tables. Direct state-coupling analyses additionally derive reduced-space SEEG state artifacts from the staged SEEG signals. GFP-informed global analyses currently target `Yeo17` staged SEEG signals and compare continuous EEG GFP against a predefined family of SEEG global metrics:

- primary: equal-weight `rms` over within-patient standardized Yeo17 core-network signals
- sensitivity: `envelope-rms`
- sensitivity: `spatial-std`
- optional weighting sensitivity: `sqrt-channel-count`

The intended interpretation ladder is:

1. quantify shared EEG GFP versus SEEG global coupling
2. inspect symmetric GFP peak-centered SEEG trajectories without assuming lead or lag
3. test whether microstate or transition effects remain after controlling for EEG GFP

If a GFP-controlled follow-up remains positive, it suggests state identity adds information beyond shared global amplitude dynamics. If it disappears after GFP control, the cleaner interpretation is that the observed coupling is mainly a shared global-drive effect.

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
- `artifacts/cache/coupling/` and `artifacts/cache/stats/`: also hold exploratory event-locked, windowed, transition, and direct state-coupling summaries under hashed `explore_*` branches
- `artifacts/cache/seeg/`: includes staged `AAL3` region mappings, coverage tables, and per-patient `1-40 Hz` region time series used by downstream activity and connectivity stages
- `artifacts/cache/eeg/`: includes the active EEG template copy `group_microstate_model_*.fif`, preprocessed FIF files, restored-channel tables, downstream microstate label tables, and reusable `gfp_trace_*` / `gfp_peaks_*` artifacts
- `artifacts/cache/coupling/`: direct state-coupling runs also write reduced-space SEEG state features and state-label tables, while GFP-informed runs write branch-specific Yeo17 SEEG global traces, network-support tables, continuous coupling summaries, peak-centered trajectories, and GFP-controlled follow-up summaries
- `artifacts/runs/<YYYYMMDD_HHMMSS>/reports/figures/`: figures produced by a specific CLI command invocation
- `artifacts/runs/<YYYYMMDD_HHMMSS>/reports/tables/`: Excel exports produced by a specific CLI command invocation
- `artifacts/runs/<YYYYMMDD_HHMMSS>/logs/`: per-command logs with command, timing, config hash, and output paths

If you do not pass `--run-id`, each CLI command gets its own timestamped run directory. If you reuse the same `--run-id`, multiple staged commands append logs and report outputs under the same `artifacts/runs/<run-id>/` folder while cache reuse remains keyed only by the branch-specific config hash.

Run directories are created lazily:

- commands that only touch reusable cache outputs typically create `logs/` but no `reports/`
- `reports/figures/` and `reports/tables/` only appear when a command actually writes figure or Excel outputs
- there is no precreated `reports/qc/` placeholder anymore

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
