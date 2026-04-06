## MODIFIED Requirements

### Requirement: IDE_A bipolar SEEG SHALL be summarized as band-limited AAL3 region signals
The system SHALL compute `1-40 Hz` `AAL3` region-level SEEG time series from valid same-region bipolar channels, SHALL persist those staged outputs for downstream activity and connectivity analyses, and SHALL expose the public staged artifacts and reports for this workflow with region-oriented naming rather than legacy network-oriented names.

#### Scenario: User runs the SEEG region generation stage
- **WHEN** an eligible `IDE_A` bipolar SEEG recording is processed in the focused workflow using the staged public SEEG branch
- **THEN** the system SHALL write `1-40 Hz` `AAL3` region signal artifacts together with same-region mapping and coverage artifacts that can be reused by both activity and connectivity stages

#### Scenario: Downstream band-limited analyses are rerun
- **WHEN** activity or connectivity effects are rerun after the SEEG region signal stage already completed
- **THEN** the downstream stages SHALL reuse the cached band-limited `AAL3` region signals rather than recomputing the bipolar-to-region signal stage

### Requirement: State-conditioned AAL3 activity effects SHALL be produced as supplemental outputs
The system SHALL compute subject-level and group-level `AAL3` region activity summaries conditioned on EEG microstate labels and persist focused-workflow supplemental outputs that include four-state subject profiles, group-level omnibus results, and pairwise post-hoc results.

#### Scenario: Supplemental activity analysis is executed
- **WHEN** EEG state labels and band-limited `AAL3` region signals are both available
- **THEN** the system SHALL compute subject-level activity summaries for every valid `patient x region x microstate` combination using the four EEG microstates as distinct within-subject levels rather than comparing each state against pooled non-matching time points

#### Scenario: Group-level activity omnibus summaries are produced
- **WHEN** subject-level four-state activity summaries are available across the cohort
- **THEN** the system SHALL persist group-level omnibus activity summary tables that test whether each valid region differs across the four EEG microstates

#### Scenario: Group-level activity post-hoc summaries are produced
- **WHEN** subject-level four-state activity summaries are available across the cohort
- **THEN** the system SHALL persist pairwise activity post-hoc summary tables covering the EEG microstate pairs for each eligible region

### Requirement: State-conditioned AAL3 connectivity effects SHALL be produced as the primary outputs
The system SHALL compute subject-level and group-level `AAL3` region-pair connectivity summaries conditioned on EEG microstate labels and persist focused-workflow primary outputs that include four-state subject profiles, group-level omnibus results, and pairwise post-hoc results.

#### Scenario: Primary connectivity analysis is executed
- **WHEN** EEG state labels and band-limited `AAL3` region signals are both available
- **THEN** the system SHALL compute subject-level region-pair connectivity summaries for every valid `patient x method x region_a x region_b x microstate` combination using the four EEG microstates as distinct within-subject levels rather than comparing each state against pooled non-matching time points

#### Scenario: Group-level connectivity omnibus summaries are produced
- **WHEN** subject-level four-state connectivity summaries are available across the cohort
- **THEN** the system SHALL persist group-level omnibus connectivity summary tables that test whether each eligible region pair differs across the four EEG microstates

#### Scenario: Multiple connectivity methods are requested
- **WHEN** the connectivity stage is run with one or more supported connectivity methods
- **THEN** the system SHALL produce method-specific subject profiles, omnibus outputs, and pairwise post-hoc outputs and SHALL keep those outputs distinct from one another
