## 1. Coverage and validation input exports

- [x] 1.1 Add a script-owned export path that writes patient-level `Yeo17` cohort coverage summaries and retained bipolar-channel counts as audit-ready CSV inputs for `Figure 1C`.
- [x] 1.2 Add or expose field-state transition, archetype-support, and assignment-similarity null-reference summaries in a form consumable by manuscript-facing R workflows.
- [x] 1.3 Verify the new coverage and validation exports can be regenerated from maintained caches or documented fallback inputs without relying on manually edited figures.

## 2. Conditioned EEG export extensions

- [x] 2.1 Extend the archetype-conditioned EEG export layer to write patient-level scalp-map tables with stable channel ordering and archetype ordering.
- [x] 2.2 Add representative-subject selection metadata or equivalent patient-level support/confidence summaries needed for deterministic anonymized plotting.
- [x] 2.3 Validate that group-level and patient-level conditioned-EEG exports stay consistent with the existing patient-first archetype-conditioned EEG workflow.

## 3. Main-text validation figure workflow

- [x] 3.1 Add a dedicated R Markdown script under `scripts/` for the missing main-text validation figure family and wire it to the new coverage, null-reference, lag, and conditioned-EEG inputs.
- [x] 3.2 Render `Yeo17` cohort characterization, field-state reproducibility, and near-zero-lag decomposition panels as manuscript-ready SVG outputs with matching CSV side tables.
- [x] 3.3 Render representative single-subject archetype-conditioned EEG panels with anonymized subject labels and style them consistently with the existing manual figure workflows.

## 4. Documentation and verification

- [x] 4.1 Update `docs/科研路线与论文大纲_改进3.md` so `Figure 1C` is defined as `Yeo17` cohort characterization and the new validation figure outputs match the maintained outline.
- [x] 4.2 Update `scripts/README.md` with the new validation workflow, required inputs, and output inventory.
- [x] 4.3 Run the relevant export and R Markdown render steps, confirm the expected `artifacts/manual/` outputs are written, and summarize any remaining gaps for manual figure assembly in `results/figs`.
