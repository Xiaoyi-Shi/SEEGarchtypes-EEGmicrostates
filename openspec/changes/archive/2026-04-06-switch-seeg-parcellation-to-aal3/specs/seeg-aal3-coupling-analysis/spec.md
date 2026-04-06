## ADDED Requirements

### Requirement: IDE_A bipolar SEEG SHALL be summarized as band-limited AAL3 region signals
The system SHALL compute `1-40 Hz` `AAL3` region-level SEEG time series from valid same-region bipolar channels and persist those staged outputs for downstream activity and connectivity analyses.

#### Scenario: User runs the SEEG region generation stage
- **WHEN** an eligible `IDE_A` bipolar SEEG recording is processed in the focused workflow using the staged public SEEG branch
- **THEN** the system SHALL write `1-40 Hz` `AAL3` region signal artifacts that can be reused by both activity and connectivity stages

#### Scenario: Downstream band-limited analyses are rerun
- **WHEN** activity or connectivity effects are rerun after the SEEG region signal stage already completed
- **THEN** the downstream stages SHALL reuse the cached band-limited `AAL3` region signals rather than recomputing the bipolar-to-region signal stage

### Requirement: State-conditioned AAL3 activity effects SHALL be produced as supplemental outputs
The system SHALL compute subject-level and group-level `AAL3` region activity effects conditioned on EEG microstate labels and persist them as supplemental outputs in the focused workflow.

#### Scenario: Supplemental activity analysis is executed
- **WHEN** EEG state labels and band-limited `AAL3` region signals are both available
- **THEN** the system SHALL compute subject-level activity effects comparing each EEG microstate against non-matching time points for every valid region

#### Scenario: Group-level activity summaries are produced
- **WHEN** subject-level state-conditioned activity effects are available across the cohort
- **THEN** the system SHALL persist group-level activity summary tables for supplemental reporting

### Requirement: State-conditioned AAL3 connectivity effects SHALL be produced as the primary outputs
The system SHALL compute subject-level and group-level `AAL3` region-pair connectivity effects conditioned on EEG microstate labels and persist connectivity results as the primary downstream analysis products.

#### Scenario: Primary connectivity analysis is executed
- **WHEN** EEG state labels and band-limited `AAL3` region signals are both available
- **THEN** the system SHALL compute subject-level region-pair connectivity effects for each EEG microstate against non-matching time points

#### Scenario: Multiple connectivity methods are requested
- **WHEN** the connectivity stage is run with one or more supported connectivity methods
- **THEN** the system SHALL produce method-specific connectivity result artifacts and SHALL keep those outputs distinct from one another
