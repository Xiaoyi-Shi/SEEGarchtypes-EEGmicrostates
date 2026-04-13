# SEEG-EEG Microstates

This repository is the analysis core for the paper-focused SEEG/EEG microstate workflow described in `docs/科研路线与论文大纲_改进.md`.

The Python package now has a narrow responsibility:

- build the eligible cohort index
- stage EEG microstate labels and GFP artifacts
- stage same-region SEEG `AAL3` result data
- run the retained paper-focused exploratory analyses
- export result tables and manifest metadata

Plotting and other special paper-support tools live under `scripts/`.

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

## CLI Workflow

```bash
uv run seeg-eegmicrostates build-index
uv run seeg-eegmicrostates build-index --analysis-state IDE_S
uv run seeg-eegmicrostates run-eeg-states
uv run seeg-eegmicrostates run-eeg-states --template-fif path/to/group_template.fif
uv run seeg-eegmicrostates run-seeg-regions
uv run seeg-eegmicrostates run-exploratory-coupling --analysis all
uv run seeg-eegmicrostates export-paper-tables
```

If you want multiple staged commands to share one run folder, pass the same `--run-id` to each command:

```bash
uv run seeg-eegmicrostates build-index --run-id 20260406_230000
uv run seeg-eegmicrostates run-eeg-states --run-id 20260406_230000
uv run seeg-eegmicrostates run-seeg-regions --run-id 20260406_230000
uv run seeg-eegmicrostates run-exploratory-coupling --analysis all --run-id 20260406_230000
uv run seeg-eegmicrostates export-paper-tables --run-id 20260406_230000
```

What each command does:

- `build-index`: scans recordings, loads workbook metadata, builds segments for the selected analysis state (`IDE_A` by default, `IDE_S` optionally), and filters the main cohort.
- `run-eeg-states`: preprocesses EEG, restores 19 channels, loads the configured default `pycrostates` `ModKMeans` template at `artifacts/cache/eeg/ModK.fif` unless `--template-fif` overrides it, caches a copy of the active template as `group_microstate_model_*`, and writes reusable state labels together with aligned EEG GFP traces and GFP peak tables.
- `run-seeg-regions`: maps bipolar channels to same-region `AAL3` pairs, rescales them onto the shared `250 Hz` analysis grid, and writes same-region mapping, coverage, and reusable staged SEEG result data.
- `run-exploratory-coupling`: runs the retained paper-focused SEEG field-state workflow on top of staged EEG labels, EEG GFP artifacts, and staged SEEG data.
- `export-paper-tables`: writes categorized manuscript-facing CSV/XLSX tables plus manifests from cached results.

The retained exploratory analyses are:

- `field-state-coupling`
- `field-state-model-order-evaluation`
- `field-state-archetypes`
- `archetype-conditioned-eeg-topography`
- `fine-lag-field-state-coupling`
- `gfp-global-coupling`
- `peak-gfp-global-coupling`
- `gfp-controlled-microstate`
- `gfp-controlled-transition`
- `field-state-to-eeg-switching`
- `gfp-controlled-field-state-to-eeg-switching`
- `all`

Useful examples:

```bash
uv run seeg-eegmicrostates run-exploratory-coupling --analysis field-state-coupling --field-state-count 4
uv run seeg-eegmicrostates run-exploratory-coupling --analysis field-state-model-order-evaluation
uv run seeg-eegmicrostates run-exploratory-coupling --analysis fine-lag-field-state-coupling --fine-lag-window-ms 40
uv run seeg-eegmicrostates run-exploratory-coupling --analysis field-state-archetypes --field-archetype-space yeo17
uv run seeg-eegmicrostates run-exploratory-coupling --analysis archetype-conditioned-eeg-topography --field-archetype-space yeo17 --fine-lag-window-ms 40
uv run seeg-eegmicrostates run-exploratory-coupling --analysis gfp-global-coupling --seeg-parcellation-name yeo17
uv run seeg-eegmicrostates run-exploratory-coupling --analysis peak-gfp-global-coupling --seeg-parcellation-name yeo17 --peak-window-sec 0.5
uv run seeg-eegmicrostates run-exploratory-coupling --analysis gfp-controlled-microstate --seeg-parcellation-name yeo17
uv run seeg-eegmicrostates run-exploratory-coupling --analysis gfp-controlled-transition --seeg-parcellation-name yeo17 --transition-window-sec 0.25
uv run seeg-eegmicrostates run-exploratory-coupling --analysis field-state-to-eeg-switching --transition-window-sec 0.25
uv run seeg-eegmicrostates run-exploratory-coupling --analysis gfp-controlled-field-state-to-eeg-switching --transition-window-sec 0.25
```

By default, EEG state staging uses the configured default template file `artifacts/cache/eeg/ModK.fif`. The `--template-fif` option overrides that default with another compatible `pycrostates` `.fif` cluster solution fitted on either the shared 11-channel montage (`F3/Fz/F4/C3/Cz/C4/P3/Pz/P4/O1/O2`) or the restored 19-channel EEG layout used by this workflow. If neither the override nor the configured default template exists, the EEG stage stops before labeling.

## Scripts Boundary

The Python package does not own plotting.

Use `scripts/` for:

- R Markdown figure rendering
- manuscript-facing panels
- one-off support tools that consume exported tables or cached outputs

Examples:

```bash
Rscript -e "rmarkdown::render('scripts/01_main_figures.Rmd', params=list(report_root='artifacts/runs/<run-id>/reports'))"
Rscript -e "rmarkdown::render('scripts/02_supplementary_figures.Rmd', params=list(report_root='artifacts/runs/<run-id>/reports'))"
```

## Outputs

Artifacts are written under:

- `artifacts/cache/`: reusable indexed tables, preprocessed FIF files, label tables, staged SEEG outputs, and statistics
- `artifacts/cache/eeg/`: active EEG template copy `group_microstate_model_*.fif`, preprocessed FIF files, restored-channel tables, microstate label tables, and reusable `gfp_trace_*` / `gfp_peaks_*` artifacts
- `artifacts/cache/seeg/`: same-region `AAL3` mappings, coverage tables, and staged per-patient `1-40 Hz` SEEG result data
- `artifacts/cache/coupling/` and `artifacts/cache/stats/`: retained field-state, archetype, conditioned-EEG, GFP/global, and switching summaries under hashed `explore_*` branches
- `artifacts/runs/<YYYYMMDD_HHMMSS>/reports/main_tables/`: manuscript-ready main tables
- `artifacts/runs/<YYYYMMDD_HHMMSS>/reports/supplementary_tables/`: manuscript-ready supplementary tables
- `artifacts/runs/<YYYYMMDD_HHMMSS>/reports/manifests/`: manifest files that map manuscript assets back to staged branches and cache artifacts
- `artifacts/runs/<YYYYMMDD_HHMMSS>/reports/main_figures/` and `artifacts/runs/<YYYYMMDD_HHMMSS>/reports/supplementary_figures/`: figures rendered by `scripts/`
- `artifacts/runs/<YYYYMMDD_HHMMSS>/logs/`: per-command logs with command, timing, config hash, and output paths

If you do not pass `--run-id`, each CLI command gets its own timestamped run directory. If you reuse the same `--run-id`, multiple staged commands append logs and report outputs under the same `artifacts/runs/<run-id>/` folder while cache reuse remains keyed only by the branch-specific config hash.

Run directories are created lazily:

- commands that only touch reusable cache outputs typically create `logs/` but no `reports/`
- `export-paper-tables` creates `reports/main_tables/`, `reports/supplementary_tables/`, and `reports/manifests/`
- the R Markdown figure step creates `reports/main_figures/` and `reports/supplementary_figures/`

## Source Layout

- `src/seeg_eegmicrostates/io`: workbook, FIF, atlas, and repository scanning helpers
- `src/seeg_eegmicrostates/eeg`: EEG preprocessing, montage restoration, and `pycrostates` model fitting
- `src/seeg_eegmicrostates/seeg`: bipolar mapping, region aggregation, and SEEG preprocessing helpers
- `src/seeg_eegmicrostates/coupling` and `stats`: retained field-state/GFP-global analysis helpers, permutation testing, and FDR correction
- `src/seeg_eegmicrostates/workflows`: cache-aware pipeline entry points used by the CLI
- `scripts/`: figure rendering and special paper-support tooling

OpenSpec change artifacts for the current implementation live in `openspec/changes/`.

Legacy cache-shaped report names and retired exploratory analyses are mapped in [docs/报告迁移说明.md](docs/报告迁移说明.md).
