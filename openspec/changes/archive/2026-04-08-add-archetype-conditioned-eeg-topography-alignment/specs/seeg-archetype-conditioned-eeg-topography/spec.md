## ADDED Requirements

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
