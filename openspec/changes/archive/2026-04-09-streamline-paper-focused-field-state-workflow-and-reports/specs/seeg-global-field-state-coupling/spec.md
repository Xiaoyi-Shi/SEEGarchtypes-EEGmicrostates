## MODIFIED Requirements

### Requirement: Subject-level SEEG field states SHALL be derived from bipolar peak maps before region/network averaging
The system SHALL support a maintained exploratory SEEG field-state branch that derives subject-level SEEG field templates and continuous SEEG field-state labels from band-limited bipolar SEEG peak maps before same-region or same-network averaging, SHALL use per-bipolar-channel normalization as the primary discovery space, and SHALL preserve the patient-level summaries needed for the paper-focused workflow.

#### Scenario: User runs maintained SEEG field-state derivation
- **WHEN** cropped bipolar SEEG and staged EEG artifacts are available for the selected analysis state and a user requests SEEG field-state coupling
- **THEN** the workflow SHALL derive subject-level SEEG field templates from peak-centered bipolar maps
- **AND** the workflow SHALL backfit those templates to the continuous bipolar time series to produce a continuous subject-level SEEG field-state label sequence
- **AND** the persisted outputs SHALL include the occupancy, dwell, and transition diagnostics required by the paper-focused report layer

#### Scenario: Branch identity for maintained SEEG field-state derivation changes
- **WHEN** a user changes the peak metric, normalization strategy, field-state count, or minimum-duration setting for SEEG field-state derivation
- **THEN** the workflow SHALL preserve separate cache identity for the resulting subject-level SEEG field-state artifacts

### Requirement: EEG microstates SHALL support synchronous and lagged coupling summaries against SEEG field states
The system SHALL compute patient-level and group-level relationships between staged EEG microstates and subject-level SEEG field-state sequences on the shared analysis time axis, SHALL preserve synchronous summaries as part of the maintained paper core, and SHALL preserve native `4 ms` near-zero-lag characterization as the maintained lag summary for manuscript interpretation.

#### Scenario: User runs synchronous SEEG field-state coupling
- **WHEN** a user requests `field-state-coupling`
- **THEN** the workflow SHALL write patient-level and group-level summaries for synchronous EEG microstate versus SEEG field-state coupling
- **AND** the persisted outputs SHALL feed the manuscript-ready field-state summary tables

#### Scenario: User runs native-resolution near-zero lag characterization
- **WHEN** a user requests fine-lag characterization for EEG microstate versus SEEG field-state coupling
- **THEN** the workflow SHALL evaluate the lag curve on the shared `4 ms` grid
- **AND** the persisted outputs SHALL preserve fine-lag peak identity and support summary of subject-level peak-lag distributions

### Requirement: SEEG field-state transitions and EEG GFP context SHALL support EEG switching follow-ups
The system SHALL support supplementary exploratory summaries that test whether SEEG field-state transitions are associated with subsequent or near-synchronous EEG microstate switching, and SHALL support GFP-aware follow-ups that account for EEG GFP context while preserving SEEG transition identity.

#### Scenario: User runs SEEG-led transition-conditioned switching analysis
- **WHEN** a user requests the supplementary field-state transition follow-up
- **THEN** the workflow SHALL write patient-level and group-level summaries that preserve SEEG `from_state` and `to_state` while quantifying associated EEG microstate switching or destination-state responses
- **AND** the resulting exports SHALL be routed to supplementary figure/table bundles

#### Scenario: User runs GFP-controlled SEEG-led switching follow-up
- **WHEN** a user requests GFP-aware SEEG field-state switching follow-up analysis
- **THEN** the workflow SHALL write patient-level and group-level summaries that model EEG microstate switching against SEEG field-state transition context while accounting for EEG GFP information
- **AND** the resulting exports SHALL be routed to supplementary figure/table bundles

## REMOVED Requirements

### Requirement: SEEG field-state coupling inference SHALL remain patient-first and time-structure preserving
**Reason**: This requirement is being relocated into analysis-family-specific contracts and manuscript-ready export contracts so the maintained workflow can distinguish paper-core synchrony from supplementary switching follow-ups more cleanly.
**Migration**: The maintained implementation SHALL continue to use patient-first, structured-null inference, but future accepted requirements will reference that behavior through the updated retained field-state and report capabilities.

