## Why

The current seizure-stage and IDE-A comparison R Markdown reports were created incrementally, but `docs/科研路线与论文大纲_改进2.md` now defines a clearer analysis boundary: `07` should describe seizure-stage trajectories, while `08` should serve as the patient-first IDE-A baseline versus seizure-stage comparison. Rewriting both reports around that boundary will make the figures more interpretable, statistically safer, and closer to the manuscript storyline.

## What Changes

- Rewrite `scripts/07_seizure_stage_microstate_archetype_trajectory.Rmd` so it focuses on seizure-stage-only descriptive trajectories, denominator/QC, stage duration imbalance, and out-of-reference-space diagnostics without making IDE-A baseline claims.
- Rewrite `scripts/08_ide_a_vs_seizure_stage_comparison.Rmd` around the improved 2.9 framework: IDE-A as patient-level baseline, fixed IDE-A-derived state space, patient-first deltas, primary versus secondary versus tertiary metric tiers, and explicit interpretation boundaries.
- Add or refine figure outputs so Figure 7 can include analysis-flow/QC, core metric trajectories or deltas, signed heatmaps, and paired effect-size/forest-style summaries.
- Add sensitivity and stratification outputs for CPS/GTCS labels, repeated seizures within patient, stage duration imbalance, complete-case denominators, and assignment-similarity/confidence diagnostics when the required inputs exist.
- Update `scripts/README.md` and documentation notes so users know which report answers which question and which outputs are primary versus exploratory.
- Do not change low-level seizure-stage segmentation, EEG/SEEG projection, or cached metric computation.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `r-markdown-paper-figure-workflow`: Refine the maintained seizure-stage and IDE-A comparison R Markdown figure families so `07` and `08` follow the improved manuscript/statistical plan.

## Impact

- Rewrites `scripts/07_seizure_stage_microstate_archetype_trajectory.Rmd`.
- Rewrites `scripts/08_ide_a_vs_seizure_stage_comparison.Rmd`.
- Updates `scripts/README.md`.
- May update `docs/科研路线与论文大纲_改进.md` or `docs/科研路线与论文大纲_改进2.md` to align commands, figure names, and interpretation notes.
- Regenerates SVG and CSV outputs under:
  - `artifacts/manual/seizure_stage_trajectory/`
  - `artifacts/manual/ide_a_vs_seizure_stage_comparison/`
- No breaking CLI changes are expected.
