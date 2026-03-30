## ADDED Requirements

### Requirement: The pipeline produces synchronized `1-40 Hz` analysis inputs for both modalities
The system SHALL derive a branch-specific `1-40 Hz` representation for EEG and SEEG from the same `IDE_A` cohort and the same per-patient analysis windows used by the primary pipeline.

#### Scenario: Patient is eligible for the band-limited branch
- **WHEN** a patient belongs to the main `IDE_A` cohort
- **THEN** the system SHALL produce branch-specific EEG and SEEG inputs filtered to `1-40 Hz` on a shared analysis time axis

#### Scenario: Branch-specific inputs are cached
- **WHEN** the `1-40 Hz` branch is executed
- **THEN** the system SHALL persist outputs with branch-specific cache identifiers so they do not overwrite HFA or primary microstate artifacts

### Requirement: The pipeline derives EEG and SEEG microstate sequences in the `1-40 Hz` branch
The system SHALL derive EEG microstates from the branch-specific `1-40 Hz` EEG representation and SHALL derive SEEG microstates from branch-specific `1-40 Hz` Yeo17 network representations.

#### Scenario: EEG branch-specific microstates are fitted
- **WHEN** the `1-40 Hz` EEG branch runs for the eligible cohort
- **THEN** the system SHALL fit or apply branch-specific EEG microstate templates and persist branch-specific EEG microstate labels

#### Scenario: SEEG branch-specific microstates are fitted
- **WHEN** the `1-40 Hz` SEEG branch runs for an eligible patient
- **THEN** the system SHALL derive SEEG microstate labels from Yeo17 network-level `1-40 Hz` representations rather than raw contact-space signals

### Requirement: Cross-modal branch outputs quantify EEG and SEEG microstate correspondence
The system SHALL compare synchronized EEG and SEEG microstate sequences from the `1-40 Hz` branch and persist cross-modal summary outputs for each patient and the cohort.

#### Scenario: Cross-modal microstate summaries are computed
- **WHEN** branch-specific EEG and SEEG microstate labels are both available for a patient
- **THEN** the system SHALL compute synchronized comparison outputs such as contingency, overlap, or lag summaries on the shared time axis

#### Scenario: Group-level branch summaries are produced
- **WHEN** patient-level cross-modal summaries are available across the cohort
- **THEN** the system SHALL produce cohort-level summary tables or reports for the `1-40 Hz` cross-modal branch
