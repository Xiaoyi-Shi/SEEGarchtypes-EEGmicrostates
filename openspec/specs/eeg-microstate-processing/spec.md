## Requirements

### Requirement: EEG state generation SHALL support whole-template replacement
The system SHALL allow the band-limited EEG state stage to load a user-supplied `pycrostates` `.fif` cluster file as the active template set instead of fitting a new cohort template set.

#### Scenario: User provides a valid external template file
- **WHEN** the user runs the EEG state stage with a valid `pycrostates` template `.fif` file
- **THEN** the system SHALL load that file as the active `ModKMeans` model, skip fitting a new cohort template set, and generate staged EEG microstate labels from the supplied template file

#### Scenario: External template file is incompatible with the staged EEG channel layout
- **WHEN** the user supplies a template file whose fitted channels are incompatible with both the shared 11-channel montage and the restored 19-channel EEG representation supported by the stage
- **THEN** the system SHALL stop before labeling and SHALL report a clear compatibility error

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

### Requirement: Staged EEG artifacts SHALL include reusable GFP traces and GFP peak events
The system SHALL persist reusable EEG global field power artifacts from the staged EEG branch so downstream exploratory analyses can compare continuous EEG global dynamics against SEEG summaries without recomputing the preprocessed EEG inputs.

#### Scenario: User completes the staged EEG branch
- **WHEN** the staged EEG state-generation command completes successfully
- **THEN** the workflow SHALL persist a continuous EEG GFP time series aligned to the staged EEG sample axis
- **AND** the workflow SHALL persist a reusable EEG GFP peak/event artifact derived from the same staged EEG input

#### Scenario: Downstream GFP-informed exploratory analyses require EEG global artifacts
- **WHEN** a downstream GFP-informed exploratory analysis is requested after the staged EEG branch already completed
- **THEN** the exploratory analysis SHALL consume the staged EEG GFP artifacts rather than recomputing GFP from the raw EEG files
