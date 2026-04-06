## ADDED Requirements

### Requirement: EEG microstate events SHALL support event-locked SEEG activity summaries
The system SHALL derive EEG microstate event tables from staged EEG labels, SHALL align staged SEEG regional signals to those events, and SHALL persist subject-level and group-level event-locked activity summaries for exploratory analysis.

#### Scenario: User runs event-locked activity analysis
- **WHEN** staged EEG microstate labels and staged SEEG regional signals are available and the exploratory event-locked activity analysis is requested
- **THEN** the system SHALL write subject-level event-locked SEEG activity summaries and SHALL produce corresponding group-level activity summaries without recomputing the upstream EEG or SEEG stages

#### Scenario: Event-locked activity is rerun after upstream staging already exists
- **WHEN** the user reruns event-locked activity analysis after the relevant EEG and SEEG staged inputs already exist
- **THEN** the analysis SHALL reuse the cached staged inputs rather than rebuilding the upstream EEG labels or SEEG regional signals

### Requirement: EEG and SEEG microstate sequences SHALL support exploratory alignment summaries
The system SHALL allow exploratory alignment analyses that fit SEEG microstate sequences from staged SEEG regional signals and compare them against staged EEG microstate labels using correspondence and lagged-overlap summaries.

#### Scenario: User runs exploratory EEG-SEEG alignment
- **WHEN** staged EEG microstate labels and staged SEEG regional signals are available and the exploratory alignment analysis is requested
- **THEN** the system SHALL fit exploratory SEEG microstates, align EEG and SEEG state sequences, and SHALL persist correspondence summary artifacts

#### Scenario: Lagged alignment summaries are requested
- **WHEN** exploratory alignment is executed
- **THEN** the system SHALL persist lagged-overlap or equivalent time-shifted state correspondence summaries in addition to direct state-alignment outputs

### Requirement: EEG microstate events SHALL support event-locked SEEG connectivity summaries
The system SHALL compute exploratory event-locked SEEG region-pair connectivity summaries conditioned on EEG microstate events and SHALL keep method-specific connectivity outputs distinct from one another.

#### Scenario: User runs event-locked connectivity analysis
- **WHEN** staged EEG microstate labels and staged SEEG regional signals are available and the exploratory event-locked connectivity analysis is requested
- **THEN** the system SHALL write subject-level and group-level event-locked connectivity summaries for the requested connectivity method or methods

#### Scenario: Multiple exploratory connectivity methods are requested
- **WHEN** the exploratory event-locked connectivity analysis is run with more than one supported connectivity method
- **THEN** the system SHALL persist method-specific outputs separately so reruns and report exports remain traceable by connectivity metric

### Requirement: Windowed EEG state metrics SHALL support slow-timescale SEEG coupling summaries
The system SHALL derive windowed EEG microstate occupancy or dwell summaries, SHALL align those summaries with windowed SEEG regional metrics, and SHALL persist subject-level and group-level slow-timescale coupling outputs.

#### Scenario: User runs windowed coupling analysis
- **WHEN** staged EEG microstate labels and staged SEEG regional signals are available and the exploratory windowed coupling analysis is requested
- **THEN** the system SHALL write reusable windowed EEG and SEEG summary artifacts together with the resulting subject-level and group-level coupling summaries

### Requirement: EEG state transitions SHALL support transition-locked SEEG coupling summaries
The system SHALL derive EEG state-transition event tables and SHALL persist transition-locked SEEG regional or region-pair coupling summaries stratified by the source and destination EEG states.

#### Scenario: User runs transition coupling analysis
- **WHEN** staged EEG microstate labels and staged SEEG regional signals are available and the exploratory transition coupling analysis is requested
- **THEN** the system SHALL write transition-locked subject-level summaries and SHALL preserve the associated transition identifiers in downstream group summaries

### Requirement: Exploratory group-level summaries SHALL require minimum subject support
The system SHALL apply a configurable minimum subject-support threshold before persisting exploratory group-level regional, region-pair, alignment, or transition summaries intended for reporting.

#### Scenario: Exploratory group rows lack sufficient subject support
- **WHEN** a candidate exploratory group summary does not meet the configured minimum subject threshold
- **THEN** the system SHALL exclude that row from the persisted group-level reporting summary
