## MODIFIED Requirements

### Requirement: EEG microstates SHALL support synchronous and lagged coupling summaries against SEEG field states
The system SHALL compute patient-level and group-level relationships between staged EEG microstates and subject-level SEEG field-state sequences on the shared analysis time axis, SHALL support both zero-lag and explicit lagged summaries, and SHALL support a fine-lag characterization mode that measures near-zero synchronization at native `4 ms` resolution.

#### Scenario: User runs synchronous SEEG field-state coupling
- **WHEN** a user requests `field-state-coupling`
- **THEN** the workflow SHALL write patient-level and group-level summaries for synchronous EEG microstate versus SEEG field-state coupling

#### Scenario: User runs coarse SEEG field-state lag characterization
- **WHEN** a user requests `lagged-field-state-coupling` across a broad lag window
- **THEN** the workflow SHALL write lag-specific patient-level and group-level summaries
- **AND** the persisted outputs SHALL preserve lag identity rather than collapsing lag results into a single aggregate score

#### Scenario: User runs fine-lag SEEG field-state characterization near zero lag
- **WHEN** a user requests native-resolution near-zero lag characterization for EEG microstate versus SEEG field-state coupling
- **THEN** the workflow SHALL evaluate the lag curve on the shared `4 ms` grid
- **AND** the persisted outputs SHALL preserve fine-lag peak identity and support summary of subject-level peak-lag distributions

### Requirement: SEEG field-state transitions and EEG GFP context SHALL support EEG switching follow-ups
The system SHALL support exploratory summaries that test whether SEEG field-state transitions are associated with subsequent or near-synchronous EEG microstate switching, and SHALL support GFP-aware follow-ups that account for EEG GFP context while preserving SEEG transition identity.

#### Scenario: User runs SEEG-led transition-conditioned switching analysis
- **WHEN** a user requests the primary field-state transition follow-up
- **THEN** the workflow SHALL write patient-level and group-level summaries that preserve SEEG `from_state` and `to_state` while quantifying associated EEG microstate switching or destination-state responses

#### Scenario: User runs GFP-controlled SEEG-led switching follow-up
- **WHEN** a user requests GFP-aware SEEG field-state switching follow-up analysis
- **THEN** the workflow SHALL write patient-level and group-level summaries that model EEG microstate switching against SEEG field-state transition context while accounting for EEG GFP information

### Requirement: SEEG field-state coupling inference SHALL remain patient-first and time-structure preserving
The system SHALL estimate SEEG field-state coupling significance from patient-level summaries rather than pooled raw samples, and SHALL use temporal-structure-preserving surrogate or permutation procedures for synchronous, coarse-lag, fine-lag, transition-conditioned, or GFP-aware analyses.

#### Scenario: SEEG field-state coupling significance is estimated
- **WHEN** the system computes significance for synchronous, coarse-lag, fine-lag, transition-conditioned, or GFP-aware SEEG field-state coupling
- **THEN** the null procedure SHALL preserve the temporal structure of the SEEG field-state and EEG label sequences through constrained surrogate generation or equivalent structured permutation
- **AND** the persisted group-level summaries SHALL aggregate patient-level effects rather than pooled sample-level values
