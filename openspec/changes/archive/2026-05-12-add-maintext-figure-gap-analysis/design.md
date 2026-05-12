## Context

The repository already has maintained manual-figure workflows under `scripts/03` through `scripts/08`, plus staged manuscript exports under `artifacts/runs/.../reports/` and manual outputs under `artifacts/manual/`. The updated outline in `docs/科研路线与论文大纲_改进3.md` raises the bar for the main-text evidence chain: the current four manually assembled figures do not yet provide a reproducible `Figure 1C` cohort-coverage panel, an observed-versus-null archetype-assignment panel, a decomposed near-zero-lag panel set, or representative single-subject archetype-conditioned EEG maps.

Current data availability is uneven. Many underlying statistics already exist in caches or supplementary exports, including model-order diagnostics, fine-lag summaries, GFP-global coupling, and archetype-conditioned EEG tables. The main gaps are (1) a maintained figure workflow that reassembles those inputs into the updated main-text story, (2) a `Yeo17`-based cohort-coverage path for `Figure 1C`, and (3) patient-level conditioned-EEG exports that are explicit enough for representative single-subject plotting.

## Goals / Non-Goals

**Goals:**
- Add a maintained manuscript-facing workflow for the missing main-text validation figures.
- Define `Figure 1C` as `Yeo17` cohort characterization while keeping it as a descriptive coverage panel rather than a new archetype-derivation branch.
- Reuse existing statistics and caches wherever possible instead of recomputing the full analysis pipeline.
- Extend conditioned-EEG exports so representative single-subject scalp-map panels can be plotted reproducibly in R.
- Keep new outputs audit-friendly by writing stable CSV inputs and SVG outputs under `artifacts/manual/`.

**Non-Goals:**
- Re-derive SEEG archetypes in a new `Yeo17` validation branch.
- Change the current `Yeo17` baseline or seizure-stage analytical reference space.
- Replace the hand-drawn acquisition or high-level workflow schematics in `Figure 1A/B`.
- Introduce a broad new CLI surface when a script-owned export or R Markdown step is sufficient.

## Decisions

### 1. Add a dedicated main-text validation R Markdown workflow

Create a dedicated script, expected to live alongside the current manual workflows, that owns the missing validation panels for the updated main-text outline. This keeps the paper-facing responsibilities explicit and avoids overloading `04`, `05`, or `08` with unrelated panel families.

Alternative considered:
- Extend `04` and `05` further: rejected because those documents already own distinct figure stories and would become harder to audit and maintain.

### 2. Use `Yeo17` coverage for cohort characterization without changing archetype derivation

`Figure 1C` will summarize retained bipolar-channel counts and `Yeo17` network coverage. This keeps the cohort-coverage panel in the same network naming system as the main analyses while still serving a descriptive sampling role rather than a new archetype-derivation step.

Alternative considered:
- Use `AAL3` coverage as originally drafted: rejected because it is too granular for a main-text cohort summary.
- Recompute the main archetype pipeline solely for the coverage panel: rejected because the figure only needs descriptive retained-channel support, not a new derivation branch.

### 3. Reuse existing analysis outputs and add only the missing export contracts

The new workflow will preferentially consume existing caches, supplementary tables, and manual CSVs for model-order support, field-state transitions, lag coupling, and stage metrics. New computation will be limited to gaps where current manual outputs are incomplete, especially `Yeo17` coverage summaries, assignment-similarity null references, and patient-level conditioned-EEG plotting tables.

Alternative considered:
- Rebuild all figure statistics from raw FIF inputs inside the new R Markdown workflow: rejected because it duplicates core analysis code and weakens reproducibility boundaries.

### 4. Keep plotting in R and make conditioned-EEG exports more explicit

Representative single-subject archetype-conditioned EEG maps will be rendered in R so they share the same style as the existing manuscript figures. The Python-side analysis/export layer should therefore emit patient-level conditioned-EEG tables with stable channel ordering, archetype ordering, and support metadata rather than trying to pre-render those panels.

Alternative considered:
- Render representative subject topographies directly in Python: rejected because it would split the figure style across toolchains and make manuscript edits harder.

### 5. Keep outputs manuscript-ready and audit-friendly

Each new panel family should write both figure outputs and the CSV tables that drove them. This preserves the current repository pattern where manual figure outputs can be inspected without reopening cached Parquet files.

## Risks / Trade-offs

- [Risk] `Yeo17` coverage caches may not align with the retained bipolar-channel subset used in the manuscript cohort panel. → Mitigation: build the coverage summary directly from each patient's retained bipolar channels and `Atlas.tsv` `Schaefer_200_17net` annotations.
- [Risk] Assignment-similarity null data may not yet be persisted in the manual-output path. → Mitigation: add a narrow export step that writes null-reference summaries without changing the retained archetype-assignment logic.
- [Risk] Representative single-subject EEG maps can be sensitive to subject-selection rules. → Mitigation: export deterministic ranking or selection metadata and keep plotted subject labels anonymized.
- [Risk] Pulling too many supplementary analyses into the main-text workflow could blur the narrative. → Mitigation: keep the new script focused on the exact figure gaps identified in the updated outline and reuse existing figure families where they already fit.

## Migration Plan

1. Add or extend export helpers so `Yeo17` coverage summaries, assignment-null summaries, and patient-level conditioned-EEG map tables are available as CSV inputs.
2. Add the new validation-focused R Markdown workflow and any shared helper updates needed for consistent styling.
3. Update `docs/科研路线与论文大纲_改进3.md` and `scripts/README.md` so the new workflow and `Figure 1C` `Yeo17` decision are reflected in the maintained documentation.
4. Render the new panels into `artifacts/manual/` and confirm they can be used to refresh the manually assembled figures under `results/figs/`.

## Open Questions

- Whether `Figure 4D` should show the lag-curve null as an overlaid mean curve, a ribbon, or a separate density-style summary.
- Whether representative single-subject EEG maps should be selected by support, confidence, or a predeclared patient list from the manuscript notes.
