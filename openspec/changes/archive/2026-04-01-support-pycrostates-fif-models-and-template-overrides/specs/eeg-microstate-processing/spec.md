## ADDED Requirements

### Requirement: EEG state generation SHALL support whole-template replacement
The system SHALL allow the band-limited EEG state stage to load a user-supplied `pycrostates` `.fif` cluster file as the active template set instead of fitting a new cohort template set.

#### Scenario: User provides a valid external template file
- **WHEN** the user runs the EEG state stage with a valid `pycrostates` template `.fif` file
- **THEN** the system SHALL load that file as the active `ModKMeans` model, skip fitting a new cohort template set, and generate staged EEG microstate labels from the supplied template file

#### Scenario: External template file is incompatible with the staged EEG channel layout
- **WHEN** the user supplies a template file whose fitted channels are incompatible with both the shared 11-channel montage and the restored 19-channel EEG representation supported by the stage
- **THEN** the system SHALL stop before labeling and SHALL report a clear compatibility error

## MODIFIED Requirements

### Requirement: Band-limited EEG state generation SHALL be the public default EEG stage
The system SHALL expose EEG microstate generation for the focused workflow as a standalone staged operation that produces reusable `1-40 Hz` EEG state artifacts, including a standard `pycrostates` `ModKMeans` `.fif` model artifact, for downstream analyses.

#### Scenario: User runs the EEG state stage in the focused workflow
- **WHEN** the user runs the public EEG state generation stage for the streamlined workflow without an external template override
- **THEN** the system SHALL fit a `1-40 Hz` `ModKMeans` model and persist both staged EEG microstate labels and a reusable `.fif` model artifact for downstream activity and connectivity stages

#### Scenario: Downstream stages require EEG state artifacts
- **WHEN** activity or connectivity effects are computed in the focused workflow
- **THEN** those stages SHALL consume the staged `1-40 Hz` EEG microstate outputs produced from the active `pycrostates` model rather than requiring a separate branch-specific EEG command path
