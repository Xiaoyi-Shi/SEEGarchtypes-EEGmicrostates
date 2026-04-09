## 1. Paper Export Contract

- [x] 1.1 Define stable categorized schemas for all retained main-table analysis families, including field-state profiles, synchronous coupling, fine-lag synchrony, archetype loadings, and archetype-template similarity.
- [x] 1.2 Define stable categorized schemas for all retained supplementary-table analysis families, including GFP/global, SEEG-led switching, GFP-controlled follow-ups, and archetype-conditioned EEG preference outputs.
- [x] 1.3 Update manifest generation so every exported table is traceable to run identity, branch identity, parameters, and subject-support diagnostics.

## 2. Python Workflow Refactor

- [x] 2.1 Replace the maintained Python report stage with a table-first export stage that writes categorized tables and manifests without rendering final figures.
- [x] 2.2 Update the public CLI to expose paper-table export semantics instead of Python manuscript rendering semantics.
- [x] 2.3 Refactor retained field-state, archetype, conditioned-topography, fine-lag, and supplementary branches so they feed the new categorized export layer cleanly.

## 3. R Markdown Figure Workflow

- [x] 3.1 Create the maintained `scripts/` R Markdown structure for main figures, supplementary figures, shared helpers, and usage documentation.
- [x] 3.2 Implement R Markdown inputs and validation logic so the figure scripts consume only standardized categorized tables and manifests.
- [x] 3.3 Define a consistent figure grammar in the R workflow for topography panels, lag curves, heatmaps, and support summaries, aligned to the paper storyline.

## 4. Plotting Surface Retirement

- [x] 4.1 Remove Python `viz` modules and any maintained pipeline code that exists only to generate manuscript figures from Python.
- [x] 4.2 Remove or migrate legacy `render-reports` paths, figure-oriented helpers, and Python-only plotting tests that no longer belong to the maintained workflow.
- [x] 4.3 Ensure historical caches remain analyzable through categorized table export even though Python figure rendering is retired.

## 5. Verification and Documentation

- [x] 5.1 Update README and `docs/` so the documented paper workflow is `Python export -> R Markdown render`.
- [x] 5.2 Add or rewrite tests around categorized table schemas, manifests, CLI export behavior, and R workflow input validation.
- [x] 5.3 Verify the full retained paper workflow end-to-end: staged analysis, categorized table export, and successful rendering of manuscript figures from `scripts/`.
