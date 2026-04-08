## ADDED Requirements

### Requirement: Subject-level SEEG field states SHALL be derived from bipolar peak maps before region/network averaging
The system SHALL support an exploratory SEEG field-state branch that derives subject-level SEEG field templates and continuous SEEG field-state labels from band-limited bipolar SEEG peak maps before same-region or same-network averaging, SHALL use per-bipolar-channel normalization as the primary discovery space, and SHALL keep those field-state artifacts distinct from the maintained region/network workflows.

#### Scenario: User runs SEEG field-state derivation
- **WHEN** cropped bipolar SEEG and staged EEG artifacts are available for the selected analysis state and a user requests SEEG field-state coupling
- **THEN** the workflow SHALL derive subject-level SEEG field templates from peak-centered bipolar maps
- **AND** the workflow SHALL backfit those templates to the continuous bipolar time series to produce a continuous subject-level SEEG field-state label sequence

#### Scenario: Branch identity for SEEG field-state derivation changes
- **WHEN** a user changes the peak metric, normalization strategy, field-state count, or minimum-duration setting for SEEG field-state derivation
- **THEN** the workflow SHALL preserve separate cache identity for the resulting subject-level SEEG field-state artifacts

### Requirement: SEEG field-state template matching SHALL be polarity-invariant
The system SHALL compare bipolar peak maps and continuous bipolar samples against SEEG field templates using a polarity-invariant spatial similarity measure rather than treating sign-flipped maps as distinct states by default.

#### Scenario: A bipolar map is sign-flipped relative to a learned template
- **WHEN** an instantaneous bipolar map matches a SEEG field template up to global sign reversal
- **THEN** the matching step SHALL treat that map as the same SEEG field configuration rather than a different state solely due to polarity

### Requirement: EEG microstates SHALL support synchronous and lagged coupling summaries against SEEG field states
The system SHALL compute patient-level and group-level relationships between staged EEG microstates and subject-level SEEG field-state sequences on the shared analysis time axis, and SHALL support both zero-lag and explicit lagged summaries.

#### Scenario: User runs synchronous SEEG field-state coupling
- **WHEN** a user requests `field-state-coupling`
- **THEN** the workflow SHALL write patient-level and group-level summaries for synchronous EEG microstate versus SEEG field-state coupling

#### Scenario: User runs lagged SEEG field-state coupling
- **WHEN** a user requests `lagged-field-state-coupling` across one or more explicit lags
- **THEN** the workflow SHALL write lag-specific patient-level and group-level summaries
- **AND** the persisted outputs SHALL preserve lag identity rather than collapsing lag results into a single aggregate score

### Requirement: EEG transitions and EEG GFP context SHALL support SEEG field-state switching follow-ups
The system SHALL support exploratory summaries that test whether EEG transitions are associated with SEEG field-state switching, and SHALL support GFP-aware follow-ups that account for EEG GFP context while preserving EEG transition identity.

#### Scenario: User runs transition-conditioned SEEG field-state coupling
- **WHEN** a user requests `transition-field-state-coupling`
- **THEN** the workflow SHALL write patient-level and group-level summaries that preserve EEG `from_state` and `to_state` while quantifying associated SEEG field-state switching or destination-state responses

#### Scenario: User runs GFP-controlled SEEG field-state switching follow-up
- **WHEN** a user requests `gfp-controlled-field-state-switching`
- **THEN** the workflow SHALL write patient-level and group-level summaries that model SEEG field-state switching against EEG microstate or transition context while accounting for EEG GFP information

### Requirement: SEEG field-state coupling inference SHALL remain patient-first and time-structure preserving
The system SHALL estimate SEEG field-state coupling significance from patient-level summaries rather than pooled raw samples, and SHALL use temporal-structure-preserving surrogate or permutation procedures for synchronous, lagged, and transition-conditioned analyses.

#### Scenario: SEEG field-state coupling significance is estimated
- **WHEN** the system computes significance for synchronous, lagged, transition-conditioned, or GFP-aware SEEG field-state coupling
- **THEN** the null procedure SHALL preserve the temporal structure of the SEEG field-state and EEG label sequences through constrained surrogate generation or equivalent structured permutation
- **AND** the persisted group-level summaries SHALL aggregate patient-level effects rather than pooled sample-level values
