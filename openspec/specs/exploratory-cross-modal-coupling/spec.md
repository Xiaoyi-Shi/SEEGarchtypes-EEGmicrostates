## Requirements

### Requirement: EEG microstate events SHALL support event-locked SEEG activity summaries
The system SHALL derive EEG microstate event tables from staged EEG labels, SHALL align staged SEEG regional signals to those events, and SHALL persist subject-level and group-level event-locked activity summaries for exploratory analysis.

#### Scenario: User runs event-locked activity analysis
- **WHEN** staged EEG microstate labels and staged SEEG regional signals are available and the exploratory event-locked activity analysis is requested
- **THEN** the system SHALL write subject-level event-locked SEEG activity summaries and SHALL produce corresponding group-level activity summaries without recomputing the upstream EEG or SEEG stages

#### Scenario: Event-locked activity is rerun after upstream staging already exists
- **WHEN** the user reruns event-locked activity analysis after the relevant EEG and SEEG staged inputs already exist
- **THEN** the analysis SHALL reuse the cached staged inputs rather than rebuilding the upstream EEG labels or SEEG regional signals

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

### Requirement: Exploratory analyses SHALL expose direct EEG-SEEG state-coupling methods alongside region-signal methods
The exploratory analysis layer SHALL preserve the maintained event-, window-, and transition-based region-signal analyses, SHALL additionally expose direct EEG-SEEG state-coupling methods, and SHALL expose GFP-informed global-coupling methods together with GFP-controlled state follow-ups without making those direct or GFP-informed methods part of the main workflow.

#### Scenario: User inspects exploratory analysis choices
- **WHEN** a user requests help for the exploratory coupling entry point
- **THEN** the system SHALL expose the maintained region-signal exploratory analyses together with the supported direct EEG-SEEG state-coupling analyses and GFP-informed global-coupling analyses

#### Scenario: Direct state-coupling outputs exist when reports are rendered
- **WHEN** exploratory direct EEG-SEEG state-coupling caches exist for the selected analysis state
- **THEN** the report/export layer SHALL render the corresponding direct-coupling figures and tables in addition to any region-signal exploratory outputs that are also available

#### Scenario: GFP-informed global-coupling outputs exist when reports are rendered
- **WHEN** exploratory GFP-informed global-coupling caches exist for the selected analysis state
- **THEN** the report/export layer SHALL render the corresponding GFP/global figures and tables in addition to any other exploratory outputs that are also available

### Requirement: Exploratory group-level summaries SHALL require minimum subject support
The system SHALL apply a configurable minimum subject-support threshold before persisting exploratory group-level regional, region-pair, transition, direct state-coupling, global-coupling, or GFP-controlled state-follow-up summaries intended for reporting.

#### Scenario: Exploratory group rows lack sufficient subject support
- **WHEN** a candidate exploratory group summary does not meet the configured minimum subject threshold
- **THEN** the system SHALL exclude that row from the persisted group-level reporting summary
