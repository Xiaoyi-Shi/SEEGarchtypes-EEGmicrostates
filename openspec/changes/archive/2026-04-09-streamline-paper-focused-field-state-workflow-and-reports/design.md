## Context

The current repository contains a broad staged workflow plus multiple exploratory branches that were useful during method discovery but now compete with the paper-focused field-state storyline. The strongest current scientific signal is concentrated in one path:

```text
EEG staging
   -> SEEG subject-level field states
   -> group archetypes in Yeo17
   -> archetype-conditioned EEG topography
   -> native 4 ms fine-lag synchrony
   -> supplementary GFP/global and SEEG-led switching follow-ups
```

By contrast, the public exploratory surface still exposes region-signal event/window/transition analyses and multiple legacy field-state diagnostics. Report exports largely mirror cache schemas, which produces too many loosely related tables and figures and makes manuscript writing cumbersome.

This change is intentionally narrower than a full platform deprecation. It targets the maintained paper-facing workflow and report layer, while leaving non-paper legacy capabilities outside this cleanup scope unless they directly interfere with the maintained field-state path.

## Goals / Non-Goals

**Goals:**
- Make the maintained exploratory workflow align with the paper-focused field-state narrative.
- Reduce the public exploratory surface to the analyses needed for the paper core plus clearly supplementary follow-ups.
- Reorganize report generation into manuscript-ready main and supplementary bundles rather than cache-shaped exports.
- Standardize figure styles, panel naming, table schemas, and statistical summary columns so outputs can be used directly in an SCI manuscript.
- Simplify workflow orchestration, report discovery, and documentation around the retained field-state pipeline.

**Non-Goals:**
- Replacing the accepted staged EEG and SEEG preprocessing contracts.
- Deleting every historical capability in a single change.
- Reworking scientific estimators that are already aligned with the target paper storyline.
- Converting the cache layer itself into a publication-facing schema.
- Changing cohort selection, EEG template semantics, or the accepted Yeo17 comparison-space choice.

## Decisions

### 1. The maintained paper workflow will center on the field-state lineage

The retained primary analyses will be:

- subject-level `SEEG global-field-state` derivation
- group `field-state archetypes`
- `archetype-conditioned EEG topography`
- `field-state` synchronous coupling
- native `4 ms` fine-lag synchrony

Supplementary analyses will remain but be clearly subordinate:

- GFP-informed global coupling
- SEEG-led switching follow-ups
- GFP-controlled SEEG-led switching follow-ups

Region-signal exploratory analyses will be retired from the maintained public surface because they do not support the main manuscript narrative and substantially increase CLI/report complexity.

Alternatives considered:
- Keep every exploratory analysis and only relabel reports.
  Rejected because report sprawl and pipeline complexity would remain.
- Remove all legacy capabilities immediately.
  Rejected because it is too disruptive and broader than the paper-focused cleanup.

### 2. Cache-facing artifacts and manuscript-facing exports will be separated

The cache layer will remain optimized for staged reuse and branch identity. A new manuscript-ready report layer will transform those caches into:

- ordered main figures
- ordered supplementary figures
- ordered main tables
- ordered supplementary tables

The report layer will no longer expose every cache-like table by default. Instead, each paper-facing analysis family will declare which summaries belong in:

- `main`
- `supplementary`
- `internal-only`

Alternatives considered:
- Rename existing cache-mirroring tables to look more paper-like.
  Rejected because cache schemas and manuscript schemas solve different problems.

### 3. Figures and tables will follow fixed scientific schemas

Each retained analysis family will emit a stable, narrow schema.

Examples:

- Fine-lag tables must include `lag_ms`, `n_subjects`, `mean_effect`, `median_effect`, `p_perm`, `q_fdr`, and support diagnostics.
- Archetype support tables must include support counts, similarity summaries, and common-space loadings.
- Preference/similarity tables must preserve distributed relationships and avoid forced best-match labels.
- Transition summaries must be supplementary by default and preserve `from_state`, `to_state`, response identity, and support.

Figure families will use consistent visual rules:

- topography panels for EEG maps
- shared heatmap grammar for similarity/support/preference matrices
- line + uncertainty grammar for lag curves
- explicit separation of main and supplementary panel families

Alternatives considered:
- Allow each plotting helper to define its own columns and aesthetics.
  Rejected because the current inconsistency is part of the problem.

### 4. CLI and report discovery will reflect the maintained paper surface

`run-exploratory-coupling` help and report discovery will expose only the retained field-state core and explicitly supplementary follow-ups. Retired region-signal exploratory branches will no longer appear in the maintained public help or default report rendering flow.

This change does not require deleting every legacy module immediately. The contract change is at the maintained public surface first; implementation can then remove or isolate dead code safely.

Alternatives considered:
- Keep retired analyses in help but mark them as deprecated.
  Rejected because the user asked for a real cleanup, not an ever-growing menu.

### 5. Main workflow staging remains intact for now

The accepted staged EEG and SEEG preprocessing workflow remains unchanged in this change. Main activity/connectivity staging may remain implemented as legacy or supplementary infrastructure, but it is not part of the maintained paper-facing workflow contract.

This limits risk and keeps the change focused on the scientific line that is already supported by results.

## Risks / Trade-offs

- [Removing exploratory branches could block future side analyses] -> Keep legacy capabilities out of scope unless they directly interfere, and preserve archived specs/history for reintroduction if needed.
- [Manuscript-ready exports may drift from cache truth] -> Derive report bundles from staged caches with explicit, testable transformations rather than duplicating analysis logic.
- [Users may still rely on old report/table names] -> Treat renamed exports as breaking and document the migration clearly in README and workflow docs.
- [Over-simplifying the workflow may hide useful diagnostics] -> Keep GFP/global and SEEG-led switching as supplementary outputs rather than deleting every non-headline result.
- [Aesthetic standardization could mask analysis-specific nuances] -> Use a shared visual grammar but keep family-specific annotations where scientifically necessary.

## Migration Plan

1. Define the retained and retired analysis families at the spec level.
2. Introduce manuscript-ready figure/table capabilities and output naming.
3. Update orchestration so report discovery emits only retained main/supplementary bundles.
4. Remove or isolate retired region-signal exploratory branches from the maintained public CLI/help surface.
5. Update documentation to describe the paper-focused workflow and the role of supplementary analyses.
6. Keep archived change history and existing caches available during transition so old results remain traceable.

## Open Questions

- Should coarse `lagged-field-state-coupling` remain as a supplementary diagnostic, or should fine-lag fully replace it in the maintained workflow?
- Should GFP-informed global coupling remain CLI-addressable as a standalone supplementary branch, or only appear in report bundles once caches exist?
- How much of the old main activity/connectivity report export should remain visible versus becoming internal-only?
- Should manuscript-ready exports use figure/table numbering in filenames, or only in manifest metadata plus captions?
