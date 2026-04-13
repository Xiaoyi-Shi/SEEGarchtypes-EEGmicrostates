## Why

The paper-focused workflow currently fixes subject-level SEEG field-state discovery at `K=4`, but the manuscript still needs explicit model-order support showing why `K=4` is retained as the main-text default. A maintained supplementary model-order evaluation is needed now so the paper can justify `K=4` using fit plateau, stability, and interpretability rather than informal preference.

## What Changes

- Add a maintained supplementary field-state model-order evaluation branch that evaluates subject-level SEEG field-state solutions for `K=2..7`.
- Export manuscript-ready model-order tables that summarize patient-level fit, incremental gain, stability, and occupancy-collapse diagnostics across candidate `K`.
- Add an R Markdown supplementary figure workflow for a model-order figure family built from the exported tables.
- Preserve `K=4` as the main-text default for subject-level SEEG field-state discovery and require the manuscript-facing summary to state that `K=4` is supported by fit plateau, stability, and interpretability.

## Capabilities

### New Capabilities
- `seeg-field-state-model-order-evaluation`: supplementary evaluation of subject-level SEEG field-state model order across `K=2..7`, including fit, gain, and stability summaries

### Modified Capabilities
- `analysis-cli-orchestration`: add maintained orchestration for exporting field-state model-order analyses without changing the default paper-core `K=4` workflow
- `manuscript-ready-report-export`: add categorized supplementary table schemas and manifest entries for field-state model-order outputs
- `r-markdown-paper-figure-workflow`: add a maintained supplementary figure family for field-state model-order evaluation
- `seeg-global-field-state-coupling`: require subject-level field-state derivation to support supplementary multi-`K` evaluation while preserving `K=4` as the default manuscript setting

## Impact

- Affected code: field-state derivation, supplementary orchestration, paper-table export, R Markdown supplementary figure scripts
- Affected outputs: supplementary tables, manifests, and supplementary model-order figures
- Affected manuscript workflow: Methods and supplementary results gain explicit support for `K=4` model-order justification
