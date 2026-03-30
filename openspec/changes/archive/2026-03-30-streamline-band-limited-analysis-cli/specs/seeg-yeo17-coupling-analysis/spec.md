## REMOVED Requirements

### Requirement: IDE_A bipolar SEEG is summarized as network-level HFA
**Reason**: The focused public workflow no longer centers Yeo17 analysis on HFA summaries. The mainline now operates on `1-40 Hz` Yeo17 network signals shared by both activity and connectivity stages.
**Migration**: Replace HFA-first downstream use with the staged `1-40 Hz` SEEG network generation step.

### Requirement: Microstate-network coupling effects are produced at subject and group level
**Reason**: The original requirement described a single HFA-centered coupling product. The focused workflow now separates Yeo17 activity effects and Yeo17 connectivity effects, with connectivity treated as the primary downstream product.
**Migration**: Use the new activity-effects stage for supplemental network-strength outputs and the new connectivity-effects stage for primary network-pair results.

## ADDED Requirements

### Requirement: IDE_A bipolar SEEG SHALL be summarized as band-limited Yeo17 network signals
The system SHALL compute `1-40 Hz` Yeo17 network-level SEEG time series from valid same-network bipolar channels and persist those staged outputs for downstream activity and connectivity analyses.

#### Scenario: User runs the SEEG network generation stage
- **WHEN** an eligible `IDE_A` bipolar SEEG recording is processed in the focused workflow
- **THEN** the system SHALL write `1-40 Hz` Yeo17 network signal artifacts that can be reused by both activity and connectivity stages

#### Scenario: Downstream band-limited analyses are rerun
- **WHEN** activity or connectivity effects are rerun after the SEEG network signal stage already completed
- **THEN** the downstream stages SHALL reuse the cached band-limited Yeo17 network signals rather than recomputing the bipolar-to-network signal stage

### Requirement: State-conditioned Yeo17 activity effects SHALL be produced as supplemental outputs
The system SHALL compute subject-level and group-level Yeo17 activity effects conditioned on EEG microstate labels and persist them as supplemental outputs in the focused workflow.

#### Scenario: Supplemental activity analysis is executed
- **WHEN** EEG state labels and band-limited Yeo17 network signals are both available
- **THEN** the system SHALL compute subject-level activity effects comparing each EEG microstate against non-matching time points for every valid network

#### Scenario: Group-level activity summaries are produced
- **WHEN** subject-level state-conditioned activity effects are available across the cohort
- **THEN** the system SHALL persist group-level activity summary tables for supplemental reporting

### Requirement: State-conditioned Yeo17 connectivity effects SHALL be produced as the primary outputs
The system SHALL compute subject-level and group-level Yeo17 network-pair connectivity effects conditioned on EEG microstate labels and persist connectivity results as the primary downstream analysis products.

#### Scenario: Primary connectivity analysis is executed
- **WHEN** EEG state labels and band-limited Yeo17 network signals are both available
- **THEN** the system SHALL compute subject-level network-pair connectivity effects for each EEG microstate against non-matching time points

#### Scenario: Multiple connectivity methods are requested
- **WHEN** the connectivity stage is run with one or more supported connectivity methods
- **THEN** the system SHALL produce method-specific connectivity result artifacts and SHALL keep those outputs distinct from one another
