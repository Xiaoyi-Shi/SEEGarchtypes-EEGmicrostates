## Why

The current paper-focused workflow still mixes two concerns inside Python: scientific result derivation and manuscript figure rendering. That coupling makes the pipeline harder to simplify around the approved paper storyline in [科研路线与论文大纲_改进.md](F:/uv_env/SEEG-EEGmicrostates/docs/科研路线与论文大纲_改进.md), and it leaves the report layer responsible for plot code that the project no longer wants to maintain in Python.

## What Changes

- Refocus the maintained Python workflow on staged analysis, grouped manuscript tables, and manifest metadata rather than Python-side figure rendering.
- Introduce a maintained `scripts/`-based R Markdown figure workflow that reads standardized paper-facing table exports and produces the manuscript figures outside the Python package.
- Replace manuscript-ready figure bundles with categorized table bundles and R-ready figure inputs that preserve branch identity, parameterization, and subject-support diagnostics.
- **BREAKING** retire the maintained Python plotting surface and remove Python `viz` modules from the paper workflow contract.
- **BREAKING** replace the current `render-reports` responsibility with a paper export stage that prepares grouped tables, manifests, and R Markdown inputs instead of emitting final figures from Python.

## Capabilities

### New Capabilities
- `r-markdown-paper-figure-workflow`: Defines the maintained `scripts/` R Markdown workflow, its expected inputs, and the figure-oriented outputs generated from standardized manuscript tables.

### Modified Capabilities
- `analysis-cli-orchestration`: The public CLI and report/export stage will shift from Python figure rendering to table-first paper export plus R Markdown handoff.
- `exploratory-cross-modal-coupling`: Maintained exploratory outputs will be exported as grouped analysis tables and R-ready inputs rather than Python-rendered figure bundles.
- `gfp-informed-global-cross-modal-coupling`: Supplementary GFP/global outputs will move to categorized table exports intended for downstream R Markdown figures.
- `manuscript-ready-report-export`: The manuscript-facing export contract will change from Python figure-and-table bundles to standardized table bundles, manifests, and R Markdown figure inputs.
- `seeg-global-field-state-coupling`: Field-state outputs will persist the paper-core diagnostics needed for grouped tables and external figure generation, without requiring Python plotting.
- `seeg-global-field-state-archetypes`: Archetype exports will be standardized around grouped tables, support diagnostics, and common-space loadings consumed by the R Markdown workflow.
- `seeg-archetype-conditioned-eeg-topography`: Conditioned-topography outputs will be exported as stable table schemas and R-ready sensor-space inputs instead of Python-rendered panels.

## Impact

- Affected code: [cli.py](F:/uv_env/SEEG-EEGmicrostates/src/seeg_eegmicrostates/cli.py), [pipelines.py](F:/uv_env/SEEG-EEGmicrostates/src/seeg_eegmicrostates/workflows/pipelines.py), [src/seeg_eegmicrostates/viz](F:/uv_env/SEEG-EEGmicrostates/src/seeg_eegmicrostates/viz), report/export tests, and manuscript-facing docs.
- New assets: `scripts/*.Rmd` and supporting R helpers for figure generation.
- Breaking surface changes: Python no longer owns manuscript plot generation, and downstream users will consume categorized table exports plus the maintained R Markdown workflow.
