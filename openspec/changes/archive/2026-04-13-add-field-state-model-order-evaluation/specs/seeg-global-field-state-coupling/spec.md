## ADDED Requirements

### Requirement: Subject-level SEEG field-state derivation SHALL support supplementary multi-`K` evaluation while preserving retained `K=4`
The system SHALL support supplementary re-derivation of subject-level SEEG field states across candidate `K` values for model-order evaluation, SHALL preserve the same peak-map discovery space and normalization family used by the retained workflow, and SHALL keep `K=4` as the maintained manuscript default for downstream paper-core analyses.

#### Scenario: Supplementary multi-`K` field-state derivation runs
- **WHEN** a user requests field-state model-order evaluation
- **THEN** the workflow SHALL re-derive subject-level field-state artifacts for each maintained candidate `K`
- **AND** those candidate solutions SHALL remain supplementary outputs rather than replacing the retained paper-core `K=4` branch

#### Scenario: Paper-core downstream analyses continue to use retained `K=4`
- **WHEN** archetype, fine-lag, or other retained paper-core field-state analyses are run without an explicit supplementary model-order request
- **THEN** those analyses SHALL continue to consume the retained `K=4` field-state branch
