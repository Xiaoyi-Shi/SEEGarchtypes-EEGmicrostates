## 1. Input Discovery and Validation

- [x] 1.1 Inspect existing IDE-A paper export tables and seizure-stage trajectory tables to identify stable filenames, columns, and metric mappings for EEG microstate, SEEG archetype, Yeo17 loading, and EEG-SEEG relationship comparisons.
- [x] 1.2 Define R Markdown parameters for IDE-A input, seizure-stage input, and output directories with repository-relative path resolution.
- [x] 1.3 Implement strict table-loading helpers in the new R Markdown document that validate required files, required columns, stage labels, condition labels, and patient overlap.
- [x] 1.4 Add denominator/QC table construction that reports available patients, seizure recordings, stages, and paired-baseline eligibility per metric family.

## 2. Comparison Table Construction

- [x] 2.1 Build patient-level IDE-A baseline summaries for EEG microstate metrics from exported IDE-A tables.
- [x] 2.2 Build patient-level seizure-stage EEG microstate summaries and deltas relative to matched IDE-A baselines.
- [x] 2.3 Build patient-level IDE-A baseline summaries for SEEG archetype metrics and assignment-similarity-style metrics.
- [x] 2.4 Build patient-level seizure-stage SEEG archetype summaries and deltas relative to matched IDE-A baselines.
- [x] 2.5 Build Yeo17 network loading comparison tables with signed stage-minus-IDE-A deltas.
- [x] 2.6 Build EEG-SEEG relationship comparison tables with archetype or field-state by microstate stage-minus-IDE-A deltas.
- [x] 2.7 Preserve seizure-level traceability and `seizure_type` labels in model-ready long CSV exports while using patient-level summaries for primary plots.

## 3. Figure Rendering

- [x] 3.1 Create `scripts/08_ide_a_vs_seizure_stage_comparison.Rmd` using the established visual style from existing R Markdown documents.
- [x] 3.2 Render a cohort/QC denominator SVG showing IDE-A, seizure-stage, and paired comparison availability by metric family.
- [x] 3.3 Render an EEG microstate comparison SVG showing baseline-to-stage trajectories or deltas for occupancy and other available core parameters.
- [x] 3.4 Render a SEEG archetype comparison SVG showing baseline-to-stage trajectories or deltas for occupancy, dwell time, occurrence, and assignment similarity when available.
- [x] 3.5 Render a Yeo17 signed-delta heatmap SVG showing which networks increase or decrease relative to IDE-A across seizure stages and archetypes.
- [x] 3.6 Render an EEG-SEEG relationship signed-delta heatmap SVG showing seizure-stage deviations from IDE-A coupling/preference patterns.
- [x] 3.7 Render a combined overview SVG composed from the main panels, using clear axis labels and no unnecessary main titles or subtitles.

## 4. Output Exports and Documentation

- [x] 4.1 Export CSV files for denominator/QC summaries, patient-level values, patient-level deltas, group-level estimates, and model-ready long tables.
- [x] 4.2 Update `scripts/README.md` with the render command, expected inputs, output directory, and generated files.
- [x] 4.3 Update `docs/科研路线与论文大纲_改进.md` with the IDE-A versus seizure-stage comparison rationale, main result types, figure plan, and interpretation cautions.

## 5. Verification

- [x] 5.1 Validate the OpenSpec change with `openspec validate compare-ide-a-and-seizure-stage-trajectories --strict`.
- [x] 5.2 Render the new R Markdown document against available local artifacts or document which required inputs are missing.
- [x] 5.3 Run relevant automated tests, at minimum `uv run pytest -q` if Python package behavior is touched.
