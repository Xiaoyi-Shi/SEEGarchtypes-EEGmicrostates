## MODIFIED Requirements

### Requirement: IDE_A bipolar SEEG SHALL be summarized as band-limited AAL3 region signals
The system SHALL compute `1-40 Hz` `AAL3` region-level SEEG time series from valid same-region bipolar channels, SHALL persist those staged outputs for downstream activity and connectivity analyses, and SHALL expose the public staged artifacts and reports for this workflow with region-oriented naming rather than legacy network-oriented names.

#### Scenario: User runs the SEEG region generation stage
- **WHEN** an eligible `IDE_A` bipolar SEEG recording is processed in the focused workflow using the staged public SEEG branch
- **THEN** the system SHALL write `1-40 Hz` `AAL3` region signal artifacts together with same-region mapping and coverage artifacts that can be reused by both activity and connectivity stages

#### Scenario: Downstream band-limited analyses are rerun
- **WHEN** activity or connectivity effects are rerun after the SEEG region signal stage already completed
- **THEN** the downstream stages SHALL reuse the cached band-limited `AAL3` region signals rather than recomputing the bipolar-to-region signal stage
