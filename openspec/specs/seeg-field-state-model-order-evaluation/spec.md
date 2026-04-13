## ADDED Requirements

### Requirement: Subject-level SEEG field-state model order SHALL be evaluated across `K=2..7`
The system SHALL provide a maintained supplementary evaluation that derives subject-level SEEG field-state solutions across candidate state counts from `K=2` through `K=7` using the same bipolar peak-map discovery space and polarity-invariant matching family used by the retained `K=4` workflow.

#### Scenario: User runs supplementary field-state model-order evaluation
- **WHEN** cropped bipolar SEEG and the maintained field-state discovery inputs are available and a user requests field-state model-order evaluation
- **THEN** the workflow SHALL evaluate subject-level field-state solutions for each `K` in `2..7`
- **AND** each candidate solution SHALL preserve separate cache identity from the retained paper-core `K=4` branch

### Requirement: Model-order evaluation SHALL summarize fit, gain, stability, and interpretability
The system SHALL summarize candidate subject-level field-state counts using maintained diagnostics that quantify discovery fit, incremental improvement versus lower `K`, stability across repeated derivations or resampled subsets, and interpretability signals that detect occupancy collapse or near-empty states.

#### Scenario: Patient-level model-order diagnostics are computed
- **WHEN** a candidate `K` is evaluated for a patient
- **THEN** the workflow SHALL write patient-level diagnostics for template fit, gain, stability, and occupancy or support collapse

#### Scenario: Group-level support for retained `K=4` is summarized
- **WHEN** patient-level model-order diagnostics are aggregated across the maintained cohort
- **THEN** the workflow SHALL write group-level summaries that allow the manuscript to state that retained `K=4` is supported by fit plateau, stability, and interpretability rather than by a single metric alone
