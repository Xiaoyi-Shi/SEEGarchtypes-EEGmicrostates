## Requirements

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

### Requirement: Group SEEG field-state archetypes SHALL support archetype-conditioned EEG scalp topography summaries
The system SHALL derive patient-level EEG scalp maps conditioned on matched SEEG field-state archetype identity on the shared analysis time axis, SHALL normalize aligned EEG topographies before averaging so map structure is not dominated by global amplitude, and SHALL aggregate those patient-level conditioned maps into report-ready group summaries.

#### Scenario: User runs archetype-conditioned EEG topography analysis
- **WHEN** subject-level SEEG field-state labels, group archetype assignments, and staged EEG sensor-space artifacts are available and a user requests the archetype-conditioned EEG topography branch
- **THEN** the workflow SHALL write patient-level archetype-conditioned EEG scalp maps together with per-archetype sample-support diagnostics

#### Scenario: Group scalp-map summaries are exported
- **WHEN** archetype-conditioned EEG topography analysis completes for a cohort
- **THEN** the workflow SHALL build group scalp-map summaries from patient-level conditioned EEG maps rather than pooled raw EEG samples

### Requirement: Archetype-conditioned EEG scalp maps SHALL support EEG microstate template preference summaries
The system SHALL compare archetype-conditioned EEG scalp maps against staged EEG microstate templates in the shared EEG montage using a polarity-tolerant spatial similarity metric, and SHALL persist similarity matrices together with EEG state-preference summaries rather than forcing a one-to-one archetype-to-microstate assignment.

#### Scenario: User inspects archetype-to-template similarity
- **WHEN** archetype-conditioned EEG scalp maps and staged EEG microstate templates are both available
- **THEN** the workflow SHALL write patient-level and group-level spatial similarity summaries for each SEEG archetype against each EEG microstate template

#### Scenario: Archetype-conditioned EEG state preference is summarized
- **WHEN** a user requests archetype-conditioned EEG preference summaries
- **THEN** the workflow SHALL write conditional probability or equivalent preference tables that preserve SEEG archetype identity and EEG state identity
- **AND** the persisted outputs SHALL preserve ambiguous or distributed preference patterns without collapsing them to a forced best-match label

### Requirement: Archetype-conditioned EEG alignment SHALL support native-grid synchrony and secondary SEEG-led transition follow-ups
The system SHALL characterize SEEG archetype versus EEG microstate synchrony on the native shared `4 ms` grid near zero lag, and SHALL support a secondary exploratory follow-up that tests whether SEEG archetype transitions are associated with EEG microstate entry or switching while preserving SEEG transition identity.

#### Scenario: User runs native-grid near-zero archetype-to-EEG synchrony
- **WHEN** a user requests fine-lag archetype-conditioned EEG synchrony analysis
- **THEN** the workflow SHALL evaluate archetype-to-EEG coupling on the shared `4 ms` grid
- **AND** the persisted outputs SHALL preserve fine-lag peak identity and subject-level near-zero support summaries

#### Scenario: User runs SEEG-led archetype-transition follow-up
- **WHEN** a user requests the secondary archetype-transition to EEG state-entry or switching branch
- **THEN** the workflow SHALL write patient-level and group-level summaries that preserve SEEG archetype `from_state` and `to_state` while quantifying associated EEG state-entry or switching responses
