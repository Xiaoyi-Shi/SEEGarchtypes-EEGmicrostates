## Context

The repository already has two relevant output families. The IDE-A paper workflow exports baseline EEG microstate, SEEG archetype, Yeo17 loading, and cross-modal relationship summaries from the retained reference state space. The seizure-stage workflow exports the same state-space projections across `pre`, `LVFA`, `SZ`, and `post`, while preserving patient, seizure, seizure type, and eligibility identifiers.

This change adds a reporting-layer comparison between those two families. It is intentionally R Markdown-first because the requested deliverable is statistical reporting, figure rendering, and documentation rather than a new low-level signal-processing stage.

## Goals / Non-Goals

**Goals:**

- Create a maintained R Markdown comparison report under `scripts/` that reads existing IDE-A and seizure-stage tables.
- Treat patient as the primary statistical unit and repeated seizure events as within-patient observations.
- Compute IDE-A baseline summaries and seizure-stage deltas for EEG microstate, SEEG archetype, Yeo17 network loading, and EEG-SEEG relationship metrics.
- Render manuscript-style SVG figures with visual grammar consistent with the existing `04`, `05`, `06`, and `07` R Markdown documents.
- Export CSV tables that preserve model-ready long format and support later statistical reanalysis.
- Update the Chinese research-route document in `docs/` so the new comparison has a clear manuscript role and interpretation boundary.

**Non-Goals:**

- Recluster EEG microstates or SEEG archetypes within seizure stages.
- Modify seizure-stage annotation parsing, asset indexing, or projection/backfitting code.
- Replace the existing seizure-stage trajectory R Markdown document.
- Claim seizure progression effects from seizure-level rows without patient-first aggregation or repeated-measures handling.

## Decisions

### Use IDE-A as a within-patient baseline

The R Markdown report will compute patient-level IDE-A means and compare each seizure stage against the same patient's IDE-A baseline whenever that patient has both data families available. This preserves comparability because the seizure-stage workflow already projects into IDE-A-derived reference spaces.

Alternative considered: compare group means from IDE-A and seizure stages independently. This is simpler but weaker because missingness and repeated seizures can make group composition differ by condition.

### Export deltas plus model-ready long tables

The report will export both descriptive deltas and long tables containing identifiers such as `patient_id`, `condition`, `stage`, `seizure_type`, `state`, `archetype`, `network`, `metric_name`, and `metric_value`. The R Markdown can render descriptive estimates immediately while preserving enough structure for mixed-effects models.

Alternative considered: only render figures. This would make the output less auditable and would force future statistical checks to reverse-engineer plotted data.

### Keep statistical summaries conservative

The report will prioritize patient-level mean differences, bootstrap confidence intervals, paired/spaghetti displays, and clearly labeled model-ready exports. If inferential models are included, they will use patient as the repeated-measures unit and condition as the main fixed effect.

Alternative considered: treat all seizure segments as independent observations. This inflates sample size and is inappropriate because 99 seizure recordings come from fewer patients.

### Render a small set of main figures

The maintained figure family will focus on cohort/QC, EEG microstate deltas, SEEG archetype deltas, Yeo17 loading deltas, and EEG-SEEG relationship deltas. Supplementary outputs can include CPS versus GTCS stratification, individual trajectories, transitions, and GFP-controlled panels when the required tables exist.

Alternative considered: combine every metric into a single large figure. That would obscure the main biological interpretation and make missing-input behavior harder to validate.

### Do not add new package dependencies unless needed by existing style

The R Markdown should reuse current plotting dependencies such as `ggplot2`, `dplyr`, `tidyr`, `patchwork`, `ggdist`, `ggtext`, `paletteer`, and `svglite` when available. New R dependencies require explicit justification in the implementation.

Alternative considered: adopt a new statistical plotting framework. This could improve aesthetics but adds install burden and inconsistency with prior figures.

## Risks / Trade-offs

- [Risk] IDE-A and seizure-stage exports may not share identical schemas or metric names. -> Mitigation: implement strict input validation with clear missing-column errors and small normalization helpers.
- [Risk] Some patients have seizure-stage data but no eligible IDE-A baseline for a metric family. -> Mitigation: report denominators per metric family and condition, and exclude only the affected comparison instead of silently dropping all outputs.
- [Risk] Repeated seizures can bias stage summaries toward patients with more seizures. -> Mitigation: compute seizure-level summaries for traceability but use patient-level means for group-facing plots and primary statistics.
- [Risk] Large label-level seizure-stage tables exceed memory needs for the R report. -> Mitigation: read patient-level and metric-level exported summaries by default, not per-sample label traces.
- [Risk] A visual delta can be misread as seizure causality. -> Mitigation: document that this is an observational within-patient baseline comparison, not a causal disease-progression model.

## Migration Plan

1. Add the new R Markdown document and output directory conventions without changing existing scripts.
2. Update `scripts/README.md` with render commands and expected inputs.
3. Update `docs/科研路线与论文大纲_改进.md` with the IDE-A versus seizure-stage result section.
4. Validate the OpenSpec change and render the R Markdown on existing exported artifacts when available.

Rollback is straightforward: remove the new R Markdown document and documentation section without touching Python analysis outputs.
