## Why

The current seizure-stage workflow summarizes `pre`, `LVFA`, `SZ`, and `post` trajectories, but it does not formally compare these stages against the IDE-A baseline that produced the reference EEG microstates and SEEG archetypes. A patient-first IDE-A versus seizure-stage comparison is needed to quantify how microstate, archetype, Yeo17 loading, and EEG-SEEG relationship metrics deviate from baseline during seizure evolution.

## What Changes

- Add a maintained analysis/reporting workflow that joins IDE-A baseline outputs with seizure-stage outputs using shared patient, EEG microstate, SEEG archetype, and Yeo17 identifiers.
- Compute patient-level IDE-A baselines and seizure-stage summaries, then derive stage-wise deltas such as `stage_mean - ide_a_mean` for EEG microstate, SEEG archetype, Yeo17 loading, and EEG-SEEG relationship metrics.
- Add R Markdown statistical reporting under `scripts/` to render publication-ready SVG figures and export model-ready/statistics-ready CSV tables.
- Update `docs/` to describe the IDE-A baseline versus seizure-stage comparison rationale, required inputs, statistical unit, main outputs, and interpretation cautions.
- Preserve the existing seizure-stage workflow; this change does not redefine stage annotation, reference projection, or low-level EEG/SEEG labeling.

## Capabilities

### New Capabilities
- `ide-a-vs-seizure-stage-comparison`: Defines patient-first comparison of IDE-A baseline metrics against seizure-stage metrics, including baseline construction, delta summaries, statistics-ready exports, figure outputs, and documentation expectations.

### Modified Capabilities
- `r-markdown-paper-figure-workflow`: Extends maintained R Markdown rendering to include the IDE-A versus seizure-stage comparison figure family and clear input validation.

## Impact

- Adds a new R Markdown document under `scripts/`, expected as `scripts/08_ide_a_vs_seizure_stage_comparison.Rmd`.
- Adds SVG and CSV outputs under a manual/report output directory, expected as `artifacts/manual/ide_a_vs_seizure_stage_comparison/`.
- Updates the research route/manuscript outline in `docs/科研路线与论文大纲_改进.md`.
- Uses existing IDE-A paper export tables and seizure-stage trajectory tables; no breaking CLI changes are expected.
