# SEEG-EEG Microstates

This repository contains a cached, staged analysis pipeline for studying synchronized scalp EEG microstates and intracranial SEEG dynamics in resting-state IDE segments. The public workflow defaults to `IDE_A`, supports `IDE_S` as an optional override, and is centered on a single `1-40 Hz` path:

- `1-40 Hz` EEG microstate state generation
- `1-40 Hz` SEEG `AAL3` region signal generation
- supplemental EEG-state-conditioned `AAL3` activity and connectivity staging
- a paper-focused SEEG field-state lineage:
  subject-level field states -> group archetypes -> archetype-conditioned EEG topography -> native `4 ms` synchrony
- explicitly supplementary GFP/global and SEEG-led switching follow-ups

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
- `run-exploratory-coupling`: runs the maintained paper-focused SEEG field-state workflow on top of the staged EEG labels, EEG GFP artifacts, and staged SEEG signals. Maintained analyses are `field-state-coupling`, `fine-lag-field-state-coupling`, `field-state-archetypes`, `archetype-conditioned-eeg-topography`, plus supplementary `gfp-global-coupling`, `lagged-gfp-global-coupling`, `peak-gfp-global-coupling`, `gfp-controlled-microstate`, `gfp-controlled-transition`, `field-state-to-eeg-switching`, `gfp-controlled-field-state-to-eeg-switching`, or `all`.
- `render-reports`: writes manuscript-ready main and supplementary figure/table bundles from cached results.

By default, EEG state staging uses the configured default template file `artifacts/cache/eeg/ModK.fif`. The `--template-fif` option overrides that default with another compatible `pycrostates` `.fif` cluster solution fitted on either the shared 11-channel montage (`F3/Fz/F4/C3/Cz/C4/P3/Pz/P4/O1/O2`) or the restored 19-channel EEG layout used by this workflow. If neither the override nor the configured default template exists, the EEG stage stops before labeling.

Exploratory analyses are intentionally opt-in and do not change the default staged pipeline. Useful examples:

```bash
uv run seeg-eegmicrostates run-exploratory-coupling --analysis field-state-coupling --field-state-count 4
uv run seeg-eegmicrostates run-exploratory-coupling --analysis fine-lag-field-state-coupling --fine-lag-window-ms 40
uv run seeg-eegmicrostates run-exploratory-coupling --analysis field-state-archetypes --field-archetype-space yeo17
uv run seeg-eegmicrostates run-exploratory-coupling --analysis archetype-conditioned-eeg-topography --field-archetype-space yeo17 --fine-lag-window-ms 40
uv run seeg-eegmicrostates run-exploratory-coupling --analysis gfp-global-coupling --seeg-parcellation-name yeo17
uv run seeg-eegmicrostates run-exploratory-coupling --analysis lagged-gfp-global-coupling --seeg-parcellation-name yeo17 --global-metric all
uv run seeg-eegmicrostates run-exploratory-coupling --analysis peak-gfp-global-coupling --seeg-parcellation-name yeo17 --peak-window-sec 0.5
uv run seeg-eegmicrostates run-exploratory-coupling --analysis gfp-controlled-microstate --seeg-parcellation-name yeo17
uv run seeg-eegmicrostates run-exploratory-coupling --analysis gfp-controlled-transition --seeg-parcellation-name yeo17 --transition-window-sec 0.25
uv run seeg-eegmicrostates run-exploratory-coupling --analysis field-state-to-eeg-switching --transition-window-sec 0.25
uv run seeg-eegmicrostates run-exploratory-coupling --analysis gfp-controlled-field-state-to-eeg-switching --transition-window-sec 0.25
```

The maintained exploratory surface is intentionally narrower than the historical one. Subject-level SEEG global-field-state analyses derive bipolar peak maps before region averaging, cluster them with polarity-invariant matching, and backfit continuous subject-level field-state labels. Those field-state labels are intentionally subject-local and should not be interpreted as a universal cross-subject template atlas. The `field-state-archetypes` branch projects those subject-level templates into a shared `Yeo17` comparison space, resolves sign orientation before matching, and writes group-level archetype summaries plus subject-to-archetype assignments. The `archetype-conditioned-eeg-topography` branch then aligns staged EEG sensor-space samples to those matched archetype labels, writes group scalp-map panels, compares them against staged EEG microstate templates, and summarizes native `4 ms` fine-lag synchrony without forcing one-to-one archetype-to-microstate assignments. Supplementary GFP/global analyses currently target `Yeo17` staged SEEG signals and compare continuous EEG GFP against a predefined family of SEEG global metrics:

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
- `artifacts/cache/coupling/` and `artifacts/cache/stats/`: hold maintained exploratory field-state, archetype, archetype-conditioned EEG, GFP/global, and switching summaries under hashed `explore_*` branches
- `artifacts/cache/seeg/`: includes staged `AAL3` region mappings, coverage tables, and per-patient `1-40 Hz` region time series used by downstream activity and connectivity stages
- `artifacts/cache/eeg/`: includes the active EEG template copy `group_microstate_model_*.fif`, preprocessed FIF files, restored-channel tables, downstream microstate label tables, and reusable `gfp_trace_*` / `gfp_peaks_*` artifacts
- `artifacts/cache/coupling/`: SEEG global-field-state runs write subject-level field traces, peak tables, peak maps, templates, continuous labels, occupancy/transition summaries, common-space archetype projections, archetype assignments, archetype-conditioned EEG scalp maps, archetype-to-template similarity tables, preference summaries, native `4 ms` synchrony summaries, and SEEG-led switching summaries, while GFP-informed runs write branch-specific Yeo17 SEEG global traces, network-support tables, continuous coupling summaries, peak-centered trajectories, and GFP-controlled follow-up summaries
- `artifacts/runs/<YYYYMMDD_HHMMSS>/reports/main_figures/`: manuscript-ready main figures
- `artifacts/runs/<YYYYMMDD_HHMMSS>/reports/main_tables/`: manuscript-ready main tables
- `artifacts/runs/<YYYYMMDD_HHMMSS>/reports/supplementary_figures/`: manuscript-ready supplementary figures
- `artifacts/runs/<YYYYMMDD_HHMMSS>/reports/supplementary_tables/`: manuscript-ready supplementary tables
- `artifacts/runs/<YYYYMMDD_HHMMSS>/reports/manifests/`: manifest files that map manuscript assets back to staged branches and cache artifacts
- `artifacts/runs/<YYYYMMDD_HHMMSS>/logs/`: per-command logs with command, timing, config hash, and output paths

If you do not pass `--run-id`, each CLI command gets its own timestamped run directory. If you reuse the same `--run-id`, multiple staged commands append logs and report outputs under the same `artifacts/runs/<run-id>/` folder while cache reuse remains keyed only by the branch-specific config hash.

Run directories are created lazily:

- commands that only touch reusable cache outputs typically create `logs/` but no `reports/`
- `reports/main_figures/`, `reports/main_tables/`, `reports/supplementary_figures/`, and `reports/supplementary_tables/` only appear when a command actually writes manuscript-facing outputs
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

Legacy cache-shaped report names and retired exploratory analyses are mapped in [docs/报告迁移说明.md](docs/报告迁移说明.md).
