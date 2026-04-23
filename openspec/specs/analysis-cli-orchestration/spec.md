## MODIFIED Requirements

### Requirement: The public CLI SHALL expose only the paper-focused analysis core
The system SHALL expose a public command surface centered on the retained paper-focused IDE analysis core while adding an optional seizure-stage trajectory extension, SHALL keep `IDE_A` as the default IDE analysis state while allowing `IDE_S` as an optional override for shared IDE commands, SHALL retain public commands for index preparation, EEG state generation, SEEG region data staging, paper-focused exploratory coupling, result-table export, seizure-stage index preparation, seizure-stage analysis, and seizure-stage export, and SHALL keep retired region activity/connectivity effect stages outside the maintained public CLI.

#### Scenario: User inspects the available public commands
- **WHEN** a user requests CLI help
- **THEN** the command surface SHALL expose `build-index`, `run-eeg-states`, `run-seeg-regions`, `run-exploratory-coupling`, `export-paper-tables`, `build-seizure-stage-index`, `run-seizure-stage-analysis`, and `export-seizure-stage-tables`
- **AND** the shared IDE staged commands SHALL expose `--analysis-state` with `IDE_A` as the default and `IDE_S` as a supported option
- **AND** the seizure-stage commands SHALL not require users to pass patient-specific `SZ*_<type>` values through `--analysis-state`
- **AND** the public CLI SHALL NOT expose `run-activity-effects` or `run-connectivity-effects`

#### Scenario: User requests paper-focused exploratory help
- **WHEN** a user requests help for `run-exploratory-coupling`
- **THEN** the command surface SHALL expose only the retained paper-focused field-state, archetype, fine-lag synchrony, GFP/global, GFP-controlled, and SEEG-to-EEG switching analyses
- **AND** the command surface SHALL NOT expose retired region-signal, direct-state, or other non-paper exploratory analyses

#### Scenario: User requests seizure-stage workflow help
- **WHEN** a user requests help for seizure-stage commands
- **THEN** the command surface SHALL describe workbook-derived `SZ*_<type>` recording discovery, stage selection, fixed IDE_A reference usage, output locations, and SEEG-only versus paired EEG-SEEG eligibility
- **AND** the help text SHALL make clear that seizure-stage workflow commands do not replace the IDE_A paper-core workflow

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

### Requirement: The public paper-focused workflow SHALL expose supplementary field-state model-order evaluation without changing the default `K=4` core
The system SHALL expose a maintained supplementary field-state model-order evaluation path within the public paper-focused workflow, SHALL keep the retained subject-level field-state core at `K=4`, and SHALL allow users to export paper-facing model-order outputs only when those supplementary caches are present.

#### Scenario: User requests supplementary field-state model-order evaluation
- **WHEN** a user invokes the maintained paper-focused workflow for field-state model-order evaluation
- **THEN** the workflow SHALL run the supplementary `K=2..7` model-order branch
- **AND** the default paper-core field-state branch SHALL remain fixed at `K=4`

#### Scenario: Paper tables are exported after model-order evaluation
- **WHEN** supplementary model-order caches exist for the selected run
- **THEN** the paper export stage SHALL include the corresponding supplementary model-order tables and manifest rows
- **AND** the export stage SHALL not rewrite the retained main-table field-state outputs as alternative `K` results
