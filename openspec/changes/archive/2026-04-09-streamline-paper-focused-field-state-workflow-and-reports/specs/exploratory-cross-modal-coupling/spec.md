## MODIFIED Requirements

### Requirement: Exploratory analyses SHALL expose direct EEG-SEEG state-coupling methods alongside region-signal methods
The exploratory analysis layer SHALL expose only the maintained paper-focused SEEG global-field-state analyses together with explicitly supplementary GFP-informed global-coupling and SEEG-led switching follow-ups, without requiring region-signal exploratory analyses to remain part of the maintained public workflow.

#### Scenario: User inspects exploratory analysis choices
- **WHEN** a user requests help for the exploratory coupling entry point
- **THEN** the system SHALL expose the maintained SEEG global-field-state analyses needed by the paper workflow, including field-state derivation, group archetypes, archetype-conditioned EEG topography, and fine-lag synchrony
- **AND** the help surface SHALL expose retained supplementary GFP/global and SEEG-led switching methods as supplementary analyses rather than co-equal headline methods

#### Scenario: Maintained exploratory outputs exist when reports are rendered
- **WHEN** retained paper-core or supplementary exploratory caches exist for the selected analysis state
- **THEN** the report/export layer SHALL render only the corresponding manuscript-ready field-state, archetype, conditioned-topography, fine-lag, GFP/global, and SEEG-led switching figures and tables

### Requirement: Exploratory group-level summaries SHALL require minimum subject support
The system SHALL apply a configurable minimum subject-support threshold before persisting maintained exploratory group-level SEEG field-state coupling, SEEG field-state archetype, archetype-conditioned EEG topography, GFP-informed global, or SEEG-led switching summaries intended for paper-ready reporting.

#### Scenario: Retained exploratory group rows lack sufficient subject support
- **WHEN** a candidate retained exploratory group summary does not meet the configured minimum subject threshold
- **THEN** the system SHALL exclude that row from the persisted paper-ready group-level reporting summary

## REMOVED Requirements

### Requirement: EEG microstate events SHALL support event-locked SEEG activity summaries
**Reason**: Event-locked region-signal analyses are outside the retained paper-focused workflow and add CLI/report complexity without supporting the main field-state manuscript narrative.
**Migration**: Historical event-activity runs remain traceable in archived changes and old caches, but new maintained workflows SHALL use the field-state paper-core analyses instead.

### Requirement: EEG microstate events SHALL support event-locked SEEG connectivity summaries
**Reason**: Event-locked region-pair connectivity is being retired from the maintained public exploratory surface in favor of the paper-focused field-state pipeline.
**Migration**: Historical event-connectivity outputs remain usable for legacy interpretation, but they are not part of the maintained paper workflow.

### Requirement: Windowed EEG state metrics SHALL support slow-timescale SEEG coupling summaries
**Reason**: Windowed region-signal coupling does not support the retained manuscript storyline and materially increases maintenance cost.
**Migration**: Use the retained fine-lag field-state synchrony and supplementary GFP/global branches for maintained cross-modal timing analyses.

### Requirement: EEG state transitions SHALL support transition-locked SEEG coupling summaries
**Reason**: Region-signal transition coupling is being retired from the maintained exploratory surface because the paper-focused workflow centers on SEEG field states and archetypes.
**Migration**: Use the retained SEEG field-state and archetype transition follow-ups when transition-oriented interpretation is required.

