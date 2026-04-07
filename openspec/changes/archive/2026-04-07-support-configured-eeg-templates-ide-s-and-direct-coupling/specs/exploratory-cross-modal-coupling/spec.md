## ADDED Requirements

### Requirement: Exploratory analyses SHALL expose direct EEG-SEEG state-coupling methods alongside region-signal methods
The exploratory analysis layer SHALL preserve the maintained event-, window-, and transition-based region-signal analyses and SHALL additionally expose direct EEG-SEEG state-coupling methods without making those direct methods part of the main workflow.

#### Scenario: User inspects exploratory analysis choices
- **WHEN** a user requests help for the exploratory coupling entry point
- **THEN** the system SHALL expose the maintained region-signal exploratory analyses together with the supported direct EEG-SEEG state-coupling analyses

#### Scenario: Direct state-coupling outputs exist when reports are rendered
- **WHEN** exploratory direct EEG-SEEG state-coupling caches exist for the selected analysis state
- **THEN** the report/export layer SHALL render the corresponding direct-coupling figures and tables in addition to any region-signal exploratory outputs that are also available

## MODIFIED Requirements

### Requirement: Exploratory group-level summaries SHALL require minimum subject support
The system SHALL apply a configurable minimum subject-support threshold before persisting exploratory group-level regional, region-pair, transition, or direct state-coupling summaries intended for reporting.

#### Scenario: Exploratory group rows lack sufficient subject support
- **WHEN** a candidate exploratory group summary does not meet the configured minimum subject threshold
- **THEN** the system SHALL exclude that row from the persisted group-level reporting summary
