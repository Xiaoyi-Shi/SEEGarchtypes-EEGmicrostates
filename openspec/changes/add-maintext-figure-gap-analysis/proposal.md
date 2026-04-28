## Why

The updated manuscript outline in `docs/科研路线与论文大纲_改进3.md` now expects a stronger main-text validation chain than the four manually assembled figures currently provide. The largest gaps are not new headline results, but missing code-backed evidence panels for electrode coverage, field-state reproducibility, lag-structure decomposition, and representative single-subject EEG interpretations.

## What Changes

- Add a maintained manuscript-facing figure workflow for the remaining main-text validation panels that are still missing from the current manual figure set.
- Define a code-backed `Figure 1C` cohort characterization panel that uses `Yeo17` network coverage and retained bipolar-channel counts instead of `AAL3` region coverage.
- Add a validation figure family that reuses existing model-order and archetype outputs to show `K=2..7` support for retained `K=4`, archetype support counts, and observed assignment similarity against a permutation-based null reference.
- Extend the archetype-conditioned EEG figure workflow so it can render manuscript-ready decompositions of near-zero-lag synchrony and representative single-subject conditioned EEG scalp maps.
- Keep the existing `Yeo17` archetype-definition and seizure-stage comparison analyses unchanged as the main analytical reference space; this change only adds missing figure evidence and the supporting export path needed to render it reproducibly.

## Capabilities

### New Capabilities
- `paper-maintext-validation-figures`: Render the missing main-text validation and cohort-characterization figure panels, including `Yeo17` electrode coverage, field-state transition/support summaries, assignment-null comparisons, lag-distribution decompositions, and representative single-subject conditioned EEG maps.

### Modified Capabilities
- `r-markdown-paper-figure-workflow`: Add a maintained R Markdown workflow for the remaining main-text validation panels and require figure outputs that match the updated manuscript outline.
- `seeg-archetype-conditioned-eeg-topography`: Expand manuscript-facing conditioned-EEG exports so representative single-subject scalp-map panels can be rendered with the same patient-first identities and ordering used by group summaries.

## Impact

- Affected docs: `docs/科研路线与论文大纲_改进3.md`
- Affected scripts: new or revised `scripts/` R Markdown figure workflows and shared helpers
- Affected analysis exports: manuscript-facing CSV/SVG outputs under `artifacts/manual/`
- Affected cached inputs: reuse of existing `yeo17` coverage, archetype, lag-coupling, and conditioned-EEG tables, with limited additional export work where current manual outputs are incomplete
