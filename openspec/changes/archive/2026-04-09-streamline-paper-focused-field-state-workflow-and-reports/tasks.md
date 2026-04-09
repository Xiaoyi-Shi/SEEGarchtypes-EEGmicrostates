## 1. Workflow Surface Cleanup

- [x] 1.1 Remove or hide retired region-signal exploratory analyses from the maintained public CLI/help surface
- [x] 1.2 Update exploratory orchestration and report discovery so only the retained field-state core plus supplementary GFP/switching branches participate in the maintained paper workflow
- [x] 1.3 Isolate or delete redundant legacy field-state diagnostics that are no longer part of the maintained public surface without breaking staged cache reuse for the retained pipeline

## 2. Field-State Paper Core

- [x] 2.1 Simplify the maintained SEEG field-state branch so its default persisted outputs are limited to subject-level states, group archetypes, conditioned EEG topography, and native `4 ms` synchrony
- [x] 2.2 Keep GFP-informed global and SEEG-led switching analyses available only as explicitly supplementary follow-ups with stable branch identities
- [x] 2.3 Standardize archetype, similarity, preference, and synchrony summaries around the retained paper-facing schemas

## 3. Manuscript-Ready Reports

- [x] 3.1 Add manuscript-ready main and supplementary figure/table bundle generation on top of the staged cache layer
- [x] 3.2 Standardize table schemas, column ordering, and statistical/support fields for fine-lag, archetype, similarity, preference, GFP/global, and switching outputs
- [x] 3.3 Redesign plotting helpers so retained paper-facing figures share a coherent visual grammar, panel ordering, and scientific labeling
- [x] 3.4 Stop exporting cache-mirroring tables and figures as the default paper-facing report surface when manuscript-ready equivalents exist

## 4. Documentation And Migration

- [x] 4.1 Update README and workflow documentation to describe the retained paper-focused field-state workflow and the supplementary status of GFP/switching follow-ups
- [x] 4.2 Document breaking CLI/report changes, including which exploratory analyses are retired from the maintained public surface
- [x] 4.3 Add a migration note that maps old report names or cache-shaped outputs to the new manuscript-ready bundles

## 5. Validation

- [x] 5.1 Extend tests for the streamlined exploratory CLI surface and the retirement of region-signal exploratory branches from maintained help/report discovery
- [x] 5.2 Add or update tests for manuscript-ready figure/table bundle generation, stable schemas, and retained supplementary outputs
- [x] 5.3 Run `uv run pytest -q` and `openspec validate "streamline-paper-focused-field-state-workflow-and-reports"`
