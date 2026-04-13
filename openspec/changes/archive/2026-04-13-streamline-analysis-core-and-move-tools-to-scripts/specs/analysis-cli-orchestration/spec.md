## MODIFIED Requirements

### Requirement: The public CLI SHALL expose only the paper-focused analysis core
The system SHALL expose a public command surface centered only on the paper-focused analysis core described by the retained manuscript workflow, SHALL keep `IDE_A` as the default analysis state while allowing `IDE_S` as an optional override, SHALL retain public commands only for index preparation, EEG state generation, SEEG region data staging, paper-focused exploratory coupling, and result-table export, and SHALL remove region activity/connectivity effect stages from the maintained public CLI.

#### Scenario: User inspects the available public commands
- **WHEN** a user requests CLI help
- **THEN** the command surface SHALL expose `build-index`, `run-eeg-states`, `run-seeg-regions`, `run-exploratory-coupling`, and `export-paper-tables`
- **AND** the shared staged commands SHALL expose `--analysis-state` with `IDE_A` as the default and `IDE_S` as a supported option
- **AND** the public CLI SHALL NOT expose `run-activity-effects` or `run-connectivity-effects`

#### Scenario: User requests paper-focused exploratory help
- **WHEN** a user requests help for `run-exploratory-coupling`
- **THEN** the command surface SHALL expose only the retained paper-focused field-state, archetype, fine-lag synchrony, GFP/global, GFP-controlled, and SEEG-to-EEG switching analyses
- **AND** the command surface SHALL NOT expose retired region-signal, direct-state, or other non-paper exploratory analyses
