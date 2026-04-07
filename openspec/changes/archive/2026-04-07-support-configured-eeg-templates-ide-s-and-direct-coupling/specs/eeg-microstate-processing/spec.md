## MODIFIED Requirements

### Requirement: Band-limited EEG state generation SHALL be the public default EEG stage
The system SHALL expose EEG microstate generation for the focused workflow as a standalone staged operation that produces reusable `1-40 Hz` EEG state artifacts by labeling against an active `pycrostates` `ModKMeans` `.fif` template selected from `--template-fif` or the configured default template path, and SHALL persist a reusable `.fif` copy of that active template for downstream activity, connectivity, and reporting stages.

#### Scenario: User runs the EEG state stage in the focused workflow without an external template override
- **WHEN** the user runs the public EEG state generation stage for the streamlined workflow without `--template-fif`
- **THEN** the system SHALL load the configured default `pycrostates` template `.fif` file as the active model
- **AND** the system SHALL persist both staged EEG microstate labels and a reusable staged `.fif` model artifact derived from that active template

#### Scenario: Configured default template file is unavailable
- **WHEN** the user runs the public EEG state generation stage without an external template override and the configured default template file does not exist
- **THEN** the system SHALL stop before labeling and SHALL report a clear missing-template error

#### Scenario: Downstream stages require EEG state artifacts
- **WHEN** activity or connectivity effects are computed in the focused workflow
- **THEN** those stages SHALL consume the staged `1-40 Hz` EEG microstate outputs produced from the active `pycrostates` model rather than requiring a separate branch-specific EEG command path
