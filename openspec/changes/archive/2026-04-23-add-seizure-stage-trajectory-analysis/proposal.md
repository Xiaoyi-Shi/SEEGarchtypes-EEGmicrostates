## Why

The current workflow characterizes EEG microstates, SEEG field-state archetypes, and their relationship in IDE baseline segments, but it does not use the manually annotated seizure-stage windows already present in `datas/info_patient.xlsx`. A dedicated seizure-stage trajectory workflow is needed to test how microstate composition, SEEG archetype engagement, and EEG-SEEG coupling change across `pre`, `LVFA`, `SZ`, and `post` phases without contaminating the retained IDE_A paper-core analysis.

## What Changes

- Add a seizure-stage segment builder that materializes `pre`, `LVFA`, `SZ`, and `post` windows from the workbook `annot_info` sheet for each `SZ*_<type>` recording.
- Add seizure recording indexing for `SZ1_CPS`, `SZ2_GTCS`, and related FIF assets, including explicit support for SEEG-only and paired EEG-SEEG eligibility.
- Add a staged seizure trajectory analysis workflow that projects seizure-stage data into the fixed IDE_A-derived EEG microstate and SEEG archetype state space.
- Export seizure-stage metrics for EEG microstate parameters, SEEG archetype parameters, Yeo17/common-space loadings, and EEG-SEEG relationship summaries.
- Add QC outputs for missing EEG assets, invalid or inconsistent stage timings, insufficient channel coverage, and floating-point boundary tolerance handling.
- Add maintained R Markdown rendering for seizure-stage trajectory figures using the existing manuscript visual style and SVG output convention.
- No breaking changes to existing IDE_A/IDE_S commands, caches, or paper-core outputs.

## Capabilities

### New Capabilities

- `seizure-stage-trajectory-analysis`: Defines seizure-stage segment materialization, SZ asset indexing, fixed-template stage projection, stage-level metric export, QC reporting, and seizure-stage figure inputs.

### Modified Capabilities

- `analysis-cli-orchestration`: Add optional seizure-stage analysis/export commands while preserving the existing IDE_A/IDE_S paper-core command behavior.
- `r-markdown-paper-figure-workflow`: Add a maintained seizure-stage trajectory R Markdown figure family with the same validation and visual grammar expectations as existing manuscript scripts.

## Impact

- Affected package areas: `src/seeg_eegmicrostates/segment/`, `src/seeg_eegmicrostates/io/`, `src/seeg_eegmicrostates/workflows/`, `src/seeg_eegmicrostates/stats/`, and `src/seeg_eegmicrostates/cli.py`.
- Affected scripts: a new `scripts/07_seizure_stage_microstate_archetype_trajectory.Rmd` and likely shared helpers in `scripts/_common.R`.
- New cache/report outputs under seizure-specific branches such as `artifacts/cache/segments/`, `artifacts/cache/eeg/`, `artifacts/cache/seeg/`, `artifacts/cache/coupling/`, `artifacts/cache/stats/`, and `artifacts/manual/seizure_stage_trajectory/`.
- Tests should use synthetic workbook rows and minimal synthetic FIF-like fixtures or mocked loaders; raw patient data remains outside git.
