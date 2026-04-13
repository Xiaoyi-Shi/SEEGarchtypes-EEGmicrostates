## 1. Multi-K Field-State Derivation

- [x] 1.1 Add a supplementary field-state model-order branch that evaluates subject-level field-state solutions for `K=2..7` with distinct cache identity
- [x] 1.2 Compute patient-level model-order diagnostics for each candidate `K`, including template fit, incremental gain, stability, and occupancy or support-collapse summaries
- [x] 1.3 Preserve the retained paper-core `K=4` branch as the unchanged default for downstream field-state, archetype, and fine-lag analyses

## 2. Group Summaries

- [x] 2.1 Aggregate patient-level model-order diagnostics into group-level summaries that support the manuscript claim that retained `K=4` is justified by fit plateau, stability, and interpretability
- [x] 2.2 Define stable scientific schemas for patient-level and group-level model-order outputs, including explicit candidate-`K` identity and support diagnostics

## 3. Paper Export

- [x] 3.1 Extend paper-table export and manifest generation to classify field-state model-order outputs as supplementary tables
- [x] 3.2 Ensure exported supplementary model-order tables retain branch metadata, evaluated `K` range, and the diagnostics required for manuscript traceability

## 4. R Markdown Figure Workflow

- [x] 4.1 Add a supplementary R Markdown figure family that renders field-state model-order support from exported tables
- [x] 4.2 Render model-order panels that summarize fit plateau, incremental gain, and stability across `K=2..7`, with interpretability-collapse diagnostics available through paired tables or companion panels
- [x] 4.3 Validate that the R Markdown workflow fails clearly when required model-order tables or manifest metadata are missing

## 5. Documentation and Validation

- [x] 5.1 Update manuscript-facing docs to state that `K=4` remains the main-text default and is supported by fit plateau, stability, and interpretability
- [x] 5.2 Add or update automated tests for multi-`K` derivation, model-order exports, manifest metadata, and R Markdown figure input validation
- [x] 5.3 Run the relevant validation commands, including OpenSpec validation, and confirm the change is apply-ready
