## 1. Add SEEG field-state common-space archetypes

- [x] 1.1 Implement projection of subject-level SEEG field templates into the supported shared comparison space and persist reusable common-space template artifacts with explicit cache identity.
- [x] 1.2 Implement sign-orientation and subject-state matching logic that aligns subject-level field states into group archetypes instead of relying on subject-local discovery order.
- [x] 1.3 Persist archetype-level summaries, subject-to-archetype assignments, and support diagnostics, and add synthetic tests for sign handling, matching stability, and sparse-support filtering.

## 2. Add fine native-resolution lag characterization

- [x] 2.1 Extend lagged SEEG field-state coupling so it can scan a narrow near-zero lag window on the native `4 ms` grid without breaking the existing coarse-lag workflow.
- [x] 2.2 Add patient-level and group-level summaries for fine-lag peak location, lag-curve width, and subject-level peak-lag distributions using patient-first structured-null inference.
- [x] 2.3 Add tests covering native `4 ms` lag identity, cache separation between coarse and fine modes, and report-ready fine-lag outputs.

## 3. Reframe switching analyses around SEEG-to-EEG direction

- [x] 3.1 Implement the primary SEEG-led switching branch that measures whether SEEG field-state transitions predict or accompany EEG microstate switching while preserving SEEG `from_state` and `to_state`.
- [x] 3.2 Implement GFP-aware SEEG-led switching follow-ups that model EEG switching against SEEG transition context while preserving patient-first inference.
- [x] 3.3 Add tests covering SEEG-led transition summaries, GFP-controlled switching outputs, structured null behavior, and minimum-subject filtering.

## 4. Extend orchestration, CLI, and report export

- [x] 4.1 Extend the exploratory CLI to expose group field-state archetype analysis, fine native-resolution lag characterization, and SEEG-led switching methods or parameters.
- [x] 4.2 Update workflow orchestration so archetype, fine-lag, and SEEG-led switching reruns reuse staged EEG labels, staged GFP traces, and subject-level field-state artifacts without recomputing unrelated branches.
- [x] 4.3 Add report discovery and rendering for archetype templates/assignments, fine-lag curves, and SEEG-to-EEG switching tables/figures.

## 5. Validate and document

- [x] 5.1 Update README and workflow documentation with the group-archetype layer, native `4 ms` lag analysis, and the SEEG-led switching interpretation.
- [x] 5.2 Add or update end-to-end tests for CLI exposure, report export, and cache reuse across archetype and fine-lag reruns.
- [x] 5.3 Validate the OpenSpec change and confirm the new exploratory branch is ready for `/opsx:apply`.
