## Context

The project now has a seizure-stage analysis workflow and an IDE-A versus seizure-stage comparison workflow. The current R Markdown reports render useful outputs, but their figure responsibilities are not fully aligned with the updated manuscript plan in `docs/科研路线与论文大纲_改进2.md`.

The revised plan defines `IDE-A baseline vs seizure-stage comparison` as a clinical extension analysis. That implies a clearer separation:

- `scripts/07_seizure_stage_microstate_archetype_trajectory.Rmd` should describe seizure-stage data on its own terms: stage denominators, timing/QC, stage duration imbalance, trajectories, and projection confidence.
- `scripts/08_ide_a_vs_seizure_stage_comparison.Rmd` should compare seizure stages against IDE-A using matched patient-level deltas, primary metric tiers, signed heatmaps, paired effect-size summaries, and sensitivity outputs.

## Goals / Non-Goals

**Goals:**

- Rewrite `07` so it is a clean seizure-stage descriptive report and avoids IDE-A baseline interpretation.
- Rewrite `08` so it implements the improved 2.9 analysis framework: IDE-A baseline, fixed reference state space, patient-first deltas, metric priority tiers, and interpretation boundaries.
- Make Figure 7 assembly more manuscript-ready by adding flow/QC, core metric delta panels, signed heatmaps, and forest-style paired effect-size summaries.
- Add CSV outputs that preserve patient-level deltas, group estimates, sensitivity summaries, stage-duration diagnostics, complete-case denominators, and CPS/GTCS stratification when inputs exist.
- Keep visual styling consistent with existing `04`, `05`, `06`, and `07` report aesthetics.

**Non-Goals:**

- Do not recompute raw EEG or SEEG labels.
- Do not recluster EEG microstates or SEEG archetypes within seizure stages.
- Do not change CLI commands or Python cache schemas unless a render-blocking issue is discovered during implementation.
- Do not promote the IDE-A comparison to the main mechanistic result; it remains a clinical extension.

## Decisions

### Separate descriptive stage trajectories from baseline deltas

`07` will answer "what happens across seizure stages?" while `08` will answer "how do those stages deviate from IDE-A in the same reference space?" This prevents one figure family from mixing within-seizure trajectory interpretation with IDE-A baseline inference.

Alternative considered: keep all seizure-stage and IDE-A panels in a single report. This would make outputs harder to interpret and would obscure the patient-first baseline requirement.

### Prioritize core metrics in `08`

The primary `08` panels will focus on EEG microstate occupancy/dwell time and SEEG archetype occupancy/dwell time. Yeo17 loading and EEG-SEEG relationship changes will remain secondary/tertiary heatmap outputs.

Alternative considered: display every available metric equally. This increases visual load and encourages overinterpretation of exploratory relationship metrics.

### Add forest-style paired effect-size summaries

Forest-style panels will summarize stage-minus-IDE-A estimates with patient denominators and uncertainty intervals. They make the primary metric hierarchy clearer than raw spaghetti plots alone.

Alternative considered: only use patient trajectory lines. Trajectories show heterogeneity but are weaker for concise manuscript-level comparison.

### Treat sensitivity outputs as supplements

CPS/GTCS stratification, repeated-seizure handling checks, complete-case filtering, and stage-duration imbalance diagnostics will be exported and plotted where feasible, but will not replace the primary patient-first delta panels.

Alternative considered: make stratified outputs the main figure. That would reduce power and make the main result too dependent on seizure type distribution.

### Keep R-first reporting with small Python bridges only when necessary

The R Markdown files should prefer CSV inputs and existing exports. If a baseline must be derived from Parquet caches, use the existing `uv run python` bridge pattern to create compact intermediate CSVs, avoiding a hard R `arrow` dependency.

Alternative considered: add R `arrow` as a required dependency. This increases environment fragility for figure rendering.

## Risks / Trade-offs

- [Risk] Existing `08` outputs may have been moved to `.rubbish` or cleaned. -> Mitigation: implementation should regenerate outputs from source tables and avoid assuming previous SVG/CSV files exist.
- [Risk] Forest-style summaries may overstate inference if they rely only on parametric intervals. -> Mitigation: label them as paired descriptive estimates unless permutation or mixed-model statistics are explicitly computed.
- [Risk] Stage duration imbalance can confound dwell and occurrence metrics. -> Mitigation: include duration QC and keep occupancy as the most robust primary metric.
- [Risk] Relationship metrics are exploratory and can be overread. -> Mitigation: keep them in the tertiary tier and label heatmaps as relationship deltas, not causal transfer.
- [Risk] Rewriting two R Markdown files at once may break render commands. -> Mitigation: validate each script independently and keep strict input checks with explicit missing-input messages.

## Migration Plan

1. Review current `07`, `08`, and `docs/科研路线与论文大纲_改进2.md` for expected inputs and outputs.
2. Rewrite `07` around seizure-stage-only descriptive figures and CSV outputs.
3. Rewrite `08` around the improved 2.9 framework and Figure 7 output plan.
4. Update `scripts/README.md` and relevant docs with the new command/output contract.
5. Render both R Markdown reports and validate generated SVG/CSV outputs.

Rollback is limited to restoring the prior versions of `scripts/07`, `scripts/08`, and docs entries; no raw data or cache migration is required.
