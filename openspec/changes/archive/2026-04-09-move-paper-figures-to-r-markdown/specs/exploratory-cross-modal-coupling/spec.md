## MODIFIED Requirements

### Requirement: Exploratory analyses SHALL expose direct EEG-SEEG state-coupling methods alongside region-signal methods
The exploratory analysis layer SHALL expose only the maintained paper-focused SEEG global-field-state analyses together with explicitly supplementary GFP-informed global-coupling and SEEG-led switching follow-ups, without requiring region-signal exploratory analyses to remain part of the maintained public workflow, and SHALL prepare maintained outputs for categorized paper-table export and downstream R Markdown figure generation rather than Python-rendered manuscript figures.

#### Scenario: User inspects exploratory analysis choices
- **WHEN** a user requests help for the exploratory coupling entry point
- **THEN** the system SHALL expose the maintained SEEG global-field-state analyses needed by the paper workflow, including field-state derivation, group archetypes, archetype-conditioned EEG topography, and fine-lag synchrony
- **AND** the help surface SHALL expose retained supplementary GFP/global and SEEG-led switching methods as supplementary analyses rather than co-equal headline methods

#### Scenario: Maintained exploratory outputs exist when paper exports are prepared
- **WHEN** retained paper-core or supplementary exploratory caches exist for the selected analysis state
- **THEN** the report/export layer SHALL write only the corresponding manuscript-ready field-state, archetype, conditioned-topography, fine-lag, GFP/global, and SEEG-led switching tables and manifest metadata
- **AND** the maintained Python workflow SHALL not be required to render the corresponding figures

### Requirement: Exploratory group-level summaries SHALL require minimum subject support
The system SHALL apply a configurable minimum subject-support threshold before persisting maintained exploratory group-level SEEG field-state coupling, SEEG field-state archetype, archetype-conditioned EEG topography, GFP-informed global, or SEEG-led switching summaries intended for paper-ready reporting.

#### Scenario: Retained exploratory group rows lack sufficient subject support
- **WHEN** a candidate retained exploratory group summary does not meet the configured minimum subject threshold
- **THEN** the system SHALL exclude that row from the persisted paper-ready group-level reporting summary
