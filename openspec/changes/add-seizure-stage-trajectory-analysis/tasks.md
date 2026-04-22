## 1. Seizure Segment And Index Foundations

- [ ] 1.1 Add `src/seeg_eegmicrostates/segment/seizure.py` to materialize `pre`, `LVFA`, `SZ`, and `post` rows from workbook `annot_info` seizure rows.
- [ ] 1.2 Add timing validation and QC reason fields for missing values, non-positive durations, duration mismatches, stage-order issues, and tolerated floating-point discrepancies.
- [ ] 1.3 Add seizure recording asset discovery for workbook-derived `SZ*_<type>` recording IDs without changing existing IDE_A/IDE_S indexing behavior.
- [ ] 1.4 Add explicit SEEG-only and paired EEG-SEEG eligibility flags to the seizure recording index.
- [ ] 1.5 Add tests for valid seizure rows, invalid timing rows, tolerated boundary differences, missing EEG assets, and missing SEEG/atlas assets.

## 2. Fixed Reference Projection And Metrics

- [ ] 2.1 Add seizure workflow helpers that load fixed IDE_A EEG microstate templates and SEEG archetype/reference artifacts with clear missing-prerequisite errors.
- [ ] 2.2 Implement EEG seizure-stage preprocessing and microstate backfitting for paired EEG-eligible stage windows.
- [ ] 2.3 Implement SEEG seizure-stage preprocessing and field-state/archetype projection for SEEG-eligible stage windows.
- [ ] 2.4 Compute EEG stage metrics including occupancy, duration, occurrence, transitions, GFP summaries, and quality metadata.
- [ ] 2.5 Compute SEEG stage metrics including archetype occupancy, duration, transitions, assignment similarity, and common-space/Yeo loading summaries.
- [ ] 2.6 Compute paired EEG-SEEG stage relationship summaries where aligned labels are available.
- [ ] 2.7 Preserve patient, seizure, seizure type, stage, and eligibility identifiers in every metric table.

## 3. Patient-Level Summaries And Exports

- [ ] 3.1 Add patient-level aggregation tables so repeated seizures are not treated as independent patients in group summaries.
- [ ] 3.2 Add denominator and cohort-support tables for EEG, SEEG, and paired EEG-SEEG metric families.
- [ ] 3.3 Write seizure-stage caches under seizure-specific stems in `artifacts/cache/segments`, `artifacts/cache/eeg`, `artifacts/cache/seeg`, `artifacts/cache/coupling`, and `artifacts/cache/stats`.
- [ ] 3.4 Export R-ready CSV/XLSX tables and manifest metadata under a seizure-stage report or manual output directory.
- [ ] 3.5 Add QC table exports covering segment timing, asset availability, channel coverage, and metric-family eligibility.

## 4. CLI Integration

- [ ] 4.1 Add `build-seizure-stage-index` CLI command for seizure segment/index generation and QC export.
- [ ] 4.2 Add `run-seizure-stage-analysis` CLI command for fixed-reference projection and metric computation.
- [ ] 4.3 Add `export-seizure-stage-tables` CLI command for report-ready table and manifest export.
- [ ] 4.4 Update CLI help text to distinguish seizure-stage commands from IDE_A/IDE_S `--analysis-state` commands.
- [ ] 4.5 Add CLI tests or smoke tests that verify new commands are listed and existing IDE commands remain available.

## 5. R Markdown Figure Workflow

- [ ] 5.1 Add `scripts/07_seizure_stage_microstate_archetype_trajectory.Rmd` for seizure-stage trajectory figure rendering.
- [ ] 5.2 Reuse or extend `scripts/_common.R` helpers for SVG output, input validation, anonymous subject labels, and the established visual style.
- [ ] 5.3 Add stage trajectory panels for EEG microstate parameters and SEEG archetype parameters.
- [ ] 5.4 Add heatmap panels for archetype-by-stage, microstate-by-stage, and Yeo/common-space loading changes.
- [ ] 5.5 Add paired EEG-SEEG relationship panels when paired outputs are available and clear skips/errors when they are not.
- [ ] 5.6 Update `scripts/README.md` with inputs, render command, and expected SVG outputs for the new R Markdown document.

## 6. Validation

- [ ] 6.1 Run unit tests for seizure segment materialization, index discovery, QC, and CLI parsing.
- [ ] 6.2 Run a smoke analysis on the local workbook to confirm 99 seizure rows materialize and SEEG-only versus paired EEG-SEEG denominators are reported.
- [ ] 6.3 Render the seizure-stage R Markdown document against exported tables and confirm SVG outputs are generated.
- [ ] 6.4 Run existing IDE_A/IDE_S smoke tests or commands to verify the retained workflow is unchanged.
- [ ] 6.5 Run `openspec validate add-seizure-stage-trajectory-analysis --strict` and resolve any spec formatting or consistency issues.
