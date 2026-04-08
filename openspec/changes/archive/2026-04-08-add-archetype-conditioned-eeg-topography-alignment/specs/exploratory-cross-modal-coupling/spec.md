## MODIFIED Requirements

### Requirement: Exploratory analyses SHALL expose direct EEG-SEEG state-coupling methods alongside region-signal methods
The exploratory analysis layer SHALL preserve the maintained event-, window-, and transition-based region-signal analyses, SHALL additionally expose direct EEG-SEEG state-coupling methods, SHALL expose GFP-informed global-coupling methods together with GFP-controlled state follow-ups, and SHALL expose subject-level SEEG global-field-state derivation plus SEEG field-state coupling methods, including group archetype summaries, native `4 ms` fine-lag characterization, SEEG-led switching follow-ups, and archetype-conditioned EEG topography alignment, without making those direct, GFP-informed, or field-state methods part of the main workflow.

#### Scenario: User inspects exploratory analysis choices
- **WHEN** a user requests help for the exploratory coupling entry point
- **THEN** the system SHALL expose the maintained region-signal exploratory analyses together with the supported direct EEG-SEEG state-coupling analyses, GFP-informed global-coupling analyses, and SEEG global-field-state analyses, including archetype, fine-lag, SEEG-led switching, and archetype-conditioned EEG topography methods

#### Scenario: Direct state-coupling outputs exist when reports are rendered
- **WHEN** exploratory direct EEG-SEEG state-coupling caches exist for the selected analysis state
- **THEN** the report/export layer SHALL render the corresponding direct-coupling figures and tables in addition to any region-signal exploratory outputs that are also available

#### Scenario: GFP-informed global-coupling outputs exist when reports are rendered
- **WHEN** exploratory GFP-informed global-coupling caches exist for the selected analysis state
- **THEN** the report/export layer SHALL render the corresponding GFP/global figures and tables in addition to any other exploratory outputs that are also available

#### Scenario: SEEG field-state outputs exist when reports are rendered
- **WHEN** exploratory SEEG global-field-state caches exist for the selected analysis state
- **THEN** the report/export layer SHALL render the corresponding SEEG field-template, occupancy/transition, archetype, fine-lag, EEG-SEEG field-state coupling, and archetype-conditioned EEG topography figures and tables in addition to any other exploratory outputs that are also available

### Requirement: Exploratory group-level summaries SHALL require minimum subject support
The system SHALL apply a configurable minimum subject-support threshold before persisting exploratory group-level regional, region-pair, transition, direct state-coupling, global-coupling, SEEG field-state coupling, SEEG field-state archetype, archetype-conditioned EEG topography, or GFP-controlled state-follow-up summaries intended for reporting.

#### Scenario: Exploratory group rows lack sufficient subject support
- **WHEN** a candidate exploratory group summary does not meet the configured minimum subject threshold
- **THEN** the system SHALL exclude that row from the persisted group-level reporting summary
