## 1. Stage EEG GFP artifacts

- [x] 1.1 Persist a reusable continuous EEG GFP trace from the staged EEG branch on the same sample axis as the staged labels.
- [x] 1.2 Persist a reusable EEG GFP peak/event table derived from the staged EEG branch and thread those artifacts through cache identity and logs.
- [x] 1.3 Extend staged EEG tests to cover GFP artifact generation, cache reuse, and downstream artifact discovery.

## 2. Derive SEEG global metrics

- [x] 2.1 Implement branch-specific SEEG global-metric derivation from staged Yeo17 signals using the primary equal-weight RMS definition over a predeclared core-network subset.
- [x] 2.2 Add supported sensitivity metric definitions for envelope-based RMS and spatial-dispersion summaries, with distinct cache/report identity for metric and weighting strategy.
- [x] 2.3 Add tests for metric derivation, core-network handling, and weighting/definition-specific cache separation.

## 3. Add GFP-informed exploratory analyses

- [x] 3.1 Implement continuous synchronous and lagged EEG GFP versus SEEG global-coupling summaries with patient-first statistics and structured nulls.
- [x] 3.2 Implement symmetric EEG GFP peak-centered SEEG global trajectory summaries and corresponding group-level outputs.
- [x] 3.3 Extend the exploratory CLI and report/export discovery to expose GFP-informed global-coupling analyses and render their tables/figures.

## 4. Add GFP-controlled state follow-ups

- [x] 4.1 Implement GFP-controlled microstate-to-SEEG global follow-up summaries using patient-level adjustment models and group aggregation.
- [x] 4.2 Implement GFP-controlled transition-conditioned SEEG global follow-up summaries that preserve transition identity while accounting for GFP.
- [x] 4.3 Add minimum-subject filtering and report outputs for GFP-controlled state and transition follow-up summaries.

## 5. Validate and document

- [x] 5.1 Add or update tests for continuous global coupling, lag scans, peak-centered trajectories, and GFP-controlled state/transition summaries.
- [x] 5.2 Update README and workflow documentation with the GFP-informed analysis ladder, the primary versus sensitivity SEEG global metrics, and interpretation guidance for GFP-controlled follow-ups.
- [x] 5.3 Validate the OpenSpec change and confirm the new exploratory branch is ready for `/opsx:apply`.
