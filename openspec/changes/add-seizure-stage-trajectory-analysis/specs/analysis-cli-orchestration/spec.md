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
