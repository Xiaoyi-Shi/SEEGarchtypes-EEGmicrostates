## 1. Input and Output Contract Review

- [x] 1.1 Inspect current `scripts/07_seizure_stage_microstate_archetype_trajectory.Rmd`, `scripts/08_ide_a_vs_seizure_stage_comparison.Rmd`, seizure-stage exports, IDE-A baseline sources, and `docs/科研路线与论文大纲_改进2.md`.
- [x] 1.2 Define the revised output file contract for `07`, including descriptive trajectory SVGs, QC SVGs, stage-duration CSVs, confidence diagnostics, and stage-only summary tables.
- [x] 1.3 Define the revised output file contract for `08`, including Figure 7 SVGs, patient-level deltas, forest/effect-size summaries, model-ready long tables, stratified summaries, and sensitivity CSVs.
- [x] 1.4 Confirm source inputs can regenerate outputs even when prior manual output directories contain only cleanup folders or no previous SVG/CSV files.

## 2. Rewrite `07` as the Seizure-Stage-Only Report

- [x] 2.1 Rewrite R Markdown parameters and input-resolution helpers for seizure-stage-only tables and output directories.
- [x] 2.2 Add strict validation for segment, denominator, processing QC, EEG metric, SEEG metric, Yeo17 loading, and EEG-SEEG relationship tables.
- [x] 2.3 Build stage-duration imbalance and timing/QC summaries from segment and denominator inputs.
- [x] 2.4 Build patient-first EEG microstate trajectory summaries for occupancy, dwell time, occurrence, and confidence.
- [x] 2.5 Build patient-first SEEG archetype trajectory summaries for occupancy, dwell time, occurrence, and assignment-similarity/confidence.
- [x] 2.6 Build descriptive Yeo17 loading and EEG-SEEG relationship heatmap inputs without IDE-A delta language.
- [x] 2.7 Render the revised `07` SVG figure family and export its audit CSV tables.

## 3. Rewrite `08` as the IDE-A Baseline Comparison Report

- [x] 3.1 Rewrite R Markdown parameters and input-resolution helpers for IDE-A baseline artifacts, seizure-stage exports, and output directories.
- [x] 3.2 Derive or load patient-level IDE-A EEG microstate, SEEG archetype, Yeo17 loading, and EEG-SEEG relationship baselines.
- [x] 3.3 Compute patient-level seizure-stage means and matched `stage - IDE-A` deltas for primary metrics.
- [x] 3.4 Compute secondary Yeo17 loading deltas and tertiary EEG-SEEG relationship deltas with zero-centered signed summaries.
- [x] 3.5 Add forest-style paired effect-size summaries for primary EEG/SEEG occupancy and dwell-time deltas.
- [x] 3.6 Add complete-case denominator, stage-duration imbalance, projection-confidence, repeated-seizure, and CPS/GTCS stratification summaries.
- [x] 3.7 Render the revised Figure 7 SVG family and export patient-level, group-level, model-ready, and sensitivity CSV tables.

## 4. Documentation Updates

- [x] 4.1 Update `scripts/README.md` so `07` and `08` have distinct purposes, commands, inputs, and generated output lists.
- [x] 4.2 Update the relevant docs file so the methods/results text, Figure 7 plan, output names, and interpretation boundaries match the rewritten scripts.
- [x] 4.3 Add notes that `08` is a clinical extension using observational patient-first deltas, not a causal seizure-propagation model.

## 5. Verification

- [x] 5.1 Render `scripts/07_seizure_stage_microstate_archetype_trajectory.Rmd` against available local seizure-stage artifacts.
- [x] 5.2 Render `scripts/08_ide_a_vs_seizure_stage_comparison.Rmd` against available local IDE-A and seizure-stage artifacts.
- [x] 5.3 Verify expected SVG and CSV outputs exist and can be regenerated after prior manual outputs are absent.
- [x] 5.4 Validate the OpenSpec change with `openspec validate revise-seizure-stage-baseline-rmds --strict`.
- [x] 5.5 Run relevant automated tests, at minimum `uv run pytest -q` if Python package behavior is touched.
