## ADDED Requirements

### Requirement: Band-limited EEG state generation SHALL be the public default EEG stage
The system SHALL expose EEG microstate generation for the focused workflow as a standalone staged operation that produces reusable `1-40 Hz` EEG state artifacts for downstream analyses.

#### Scenario: User runs the EEG state stage in the focused workflow
- **WHEN** the user runs the public EEG state generation stage for the streamlined workflow
- **THEN** the system SHALL generate and persist `1-40 Hz` EEG microstate labels and supporting model artifacts for downstream activity and connectivity stages

#### Scenario: Downstream stages require EEG state artifacts
- **WHEN** activity or connectivity effects are computed in the focused workflow
- **THEN** those stages SHALL consume the staged `1-40 Hz` EEG microstate outputs rather than requiring a separate branch-specific EEG command path
