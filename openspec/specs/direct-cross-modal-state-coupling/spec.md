## Requirements

### Requirement: Exploratory SEEG state sequences SHALL be derived from a reduced-space SEEG representation
The system SHALL derive exploratory SEEG state sequences for direct EEG-SEEG coupling from a reduced-space SEEG representation that is explicit in branch identity, SHALL use the same selected analysis-state cohort and analysis windows as the staged workflow, and SHALL keep those state artifacts separate from the maintained AAL3 activity/connectivity outputs.

#### Scenario: User runs a direct coupling analysis with reduced-space SEEG state derivation
- **WHEN** staged EEG labels and staged SEEG signals are available for a selected analysis state and a user requests direct EEG-SEEG state coupling
- **THEN** the system SHALL derive or load branch-specific SEEG state artifacts from the configured reduced-space SEEG representation
- **AND** the system SHALL preserve separate cache identity for the reduced-space state backend and other direct-branch parameters

### Requirement: Direct EEG-SEEG state coupling SHALL be summarized synchronously and across lags
The system SHALL compute patient-level direct EEG-SEEG state-coupling summaries on the shared analysis time axis and SHALL support both zero-lag and explicit lagged summaries while keeping lag-specific outputs distinct from one another.

#### Scenario: User runs synchronous direct state coupling
- **WHEN** a user requests direct EEG-SEEG state coupling at zero lag
- **THEN** the system SHALL write patient-level synchronous coupling summaries and the corresponding group-level summaries for the selected analysis state

#### Scenario: User runs lagged direct state coupling
- **WHEN** a user requests direct EEG-SEEG state coupling across one or more explicit lags
- **THEN** the system SHALL write lag-specific patient-level and group-level summaries
- **AND** the persisted outputs SHALL preserve the evaluated lag identity

### Requirement: Direct EEG-state transitions SHALL support transition-conditioned SEEG state coupling summaries
The system SHALL support transition-conditioned direct EEG-SEEG state coupling summaries that preserve EEG source and destination states while quantifying associated SEEG state responses.

#### Scenario: User runs transition-conditioned direct state coupling
- **WHEN** a user requests direct coupling summaries conditioned on EEG state transitions
- **THEN** the system SHALL write patient-level and group-level direct coupling summaries stratified by EEG `from_state` and `to_state`

### Requirement: Direct state-coupling inference SHALL preserve temporal structure
The system SHALL estimate direct EEG-SEEG state-coupling significance using time-structure-preserving surrogate or permutation procedures rather than naive sample shuffling, and SHALL aggregate evidence from patient-level summaries rather than pooled raw samples.

#### Scenario: Direct coupling significance is estimated
- **WHEN** the system computes statistical significance for synchronous, lagged, or transition-conditioned direct EEG-SEEG state coupling
- **THEN** the null procedure SHALL preserve the temporal structure of the state sequences through constrained surrogate generation or equivalent structured permutation
- **AND** the persisted group-level summaries SHALL be derived from patient-level coupling metrics
