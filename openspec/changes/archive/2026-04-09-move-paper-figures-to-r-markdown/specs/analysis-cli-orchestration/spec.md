## MODIFIED Requirements

### Requirement: The public CLI SHALL expose a focused staged `1-40 Hz` workflow
The system SHALL expose a public command surface centered on the focused staged `1-40 Hz` analysis workflow, SHALL keep `IDE_A` as the default analysis state while allowing `IDE_S` as an optional override, SHALL expose the public SEEG staging step as `run-seeg-regions`, and SHALL limit the maintained exploratory command surface to the paper-focused SEEG field-state pipeline plus explicitly supplementary GFP-informed global and SEEG-led switching follow-ups, with paper-facing export represented as a table-first handoff rather than Python figure rendering.

#### Scenario: User inspects the available public commands
- **WHEN** a user requests CLI help
- **THEN** the command surface SHALL expose the focused staged workflow for index preparation, EEG state generation, SEEG region generation, exploratory coupling, and paper-table export
- **AND** the shared staged commands SHALL expose `--analysis-state` with `IDE_A` as the default and `IDE_S` as a supported option
- **AND** the public SEEG staging command SHALL be named `run-seeg-regions`
- **AND** the exploratory coupling entry point SHALL expose the maintained field-state analyses needed for the paper workflow, including field-state derivation, group archetypes, archetype-conditioned EEG topography, and native `4 ms` fine-lag synchrony, together with explicitly supplementary GFP/global and SEEG-led switching follow-ups

#### Scenario: Retired region-signal exploratory methods are no longer part of the maintained public surface
- **WHEN** the streamlined paper-focused CLI is released
- **THEN** region-signal event, windowed, and transition exploratory analyses SHALL not appear in the maintained public exploratory help surface
- **AND** their historical implementation, if still present internally, SHALL not define the maintained paper workflow

### Requirement: Reports SHALL be exported from staged analysis results
The system SHALL export paper-facing categorized tables and manifest metadata from the staged workflow into report directories without requiring users to manually transform cached results, SHALL stop treating Python as the maintained manuscript figure renderer, and SHALL export only the paper-table bundles whose required staged artifacts are available for the selected analysis state.

#### Scenario: Main paper-core caches exist when paper tables are exported
- **WHEN** the paper export stage runs after field-state, archetype, archetype-conditioned EEG topography, and fine-lag caches exist for the selected analysis state
- **THEN** the export stage SHALL write the corresponding manuscript-ready main tables and manifest entries for the paper-focused workflow
- **AND** the Python export stage SHALL not be required to emit final figure files

#### Scenario: Supplementary follow-up caches exist when paper tables are exported
- **WHEN** the paper export stage runs after retained supplementary GFP/global or SEEG-led switching caches exist for the selected analysis state
- **THEN** the export stage SHALL write the corresponding supplementary tables and manifest entries without promoting them into the main table bundle

#### Scenario: Only a subset of paper-focused outputs exists
- **WHEN** the paper export stage runs and only some retained paper-focused result caches are present
- **THEN** the export stage SHALL write only the categorized table bundles and manifest rows whose required staged artifacts are available
