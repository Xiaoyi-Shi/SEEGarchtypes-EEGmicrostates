## ADDED Requirements

### Requirement: GFP-informed exploratory analyses SHALL derive predefined SEEG global metrics from staged Yeo17 signals
The system SHALL derive exploratory SEEG global metrics from staged Yeo17 network signals using a predefined family of metric definitions rather than an ad hoc single summary, SHALL define one primary metric for interpretation, and SHALL preserve branch identity across metric definitions and weighting strategies.

#### Scenario: User runs GFP-informed global coupling with the primary metric
- **WHEN** staged EEG artifacts and staged Yeo17 network signals are available and a user requests GFP-informed global coupling
- **THEN** the workflow SHALL derive the primary SEEG global metric from within-patient standardized Yeo17 core-network signals using an equal-weight RMS-style summary

#### Scenario: User compares predefined SEEG global metric definitions
- **WHEN** the exploratory branch evaluates one or more supported SEEG global metric definitions
- **THEN** the workflow SHALL keep outputs distinct by metric definition and weighting strategy
- **AND** the branch SHALL support at least RMS-style magnitude, envelope-based magnitude, and spatial-dispersion style summaries

### Requirement: Continuous EEG GFP versus SEEG global coupling SHALL support synchronous and lagged summaries
The system SHALL quantify patient-level and group-level relationships between continuous EEG GFP and SEEG global metrics on the shared staged time axis, and SHALL support both zero-lag and explicit lagged summaries.

#### Scenario: User runs continuous GFP/global coupling
- **WHEN** a user requests continuous GFP-informed global coupling
- **THEN** the workflow SHALL write patient-level and group-level summaries for the requested SEEG global metric without recomputing the upstream staged EEG or SEEG inputs

#### Scenario: User evaluates lagged GFP/global coupling
- **WHEN** a user requests lagged GFP-informed global coupling across explicit lags
- **THEN** the workflow SHALL write lag-specific patient-level and group-level summaries
- **AND** the persisted outputs SHALL preserve lag identity rather than collapsing lag results into a single aggregate score

### Requirement: EEG GFP peaks SHALL support symmetric peak-centered SEEG global summaries
The system SHALL support exploratory summaries centered on EEG GFP peaks using symmetric windows around the EEG event time rather than assuming SEEG changes occur only after the EEG peak.

#### Scenario: User runs peak-centered GFP/global analysis
- **WHEN** a user requests GFP peak-centered SEEG global summaries
- **THEN** the workflow SHALL derive peak-centered patient-level and group-level trajectories using windows that extend both before and after the EEG GFP peak

### Requirement: GFP-controlled state follow-ups SHALL separate shared amplitude effects from state-specific effects
The system SHALL support exploratory follow-up analyses that test whether EEG microstate and transition effects on SEEG global metrics remain after accounting for EEG GFP.

#### Scenario: User runs GFP-controlled microstate follow-up
- **WHEN** a user requests a GFP-controlled microstate-to-SEEG global analysis
- **THEN** the workflow SHALL write patient-level and group-level summaries that model SEEG global metrics as a function of both EEG GFP and EEG microstate state identity

#### Scenario: User runs GFP-controlled transition follow-up
- **WHEN** a user requests a GFP-controlled transition-conditioned SEEG global analysis
- **THEN** the workflow SHALL write patient-level and group-level summaries that preserve EEG transition identity while accounting for EEG GFP

### Requirement: GFP-informed global-coupling inference SHALL remain patient-first and time-structure preserving
The system SHALL estimate GFP/global exploratory significance from patient-level summaries rather than pooled raw samples, and SHALL use time-structure-preserving surrogate or permutation procedures for continuous and peak-centered analyses.

#### Scenario: Continuous or peak-centered GFP/global significance is estimated
- **WHEN** the system computes significance for continuous, lagged, or peak-centered GFP-informed global coupling
- **THEN** the null procedure SHALL preserve temporal structure through circular shifts or an equivalent constrained surrogate method
- **AND** the persisted group-level summaries SHALL aggregate patient-level effects rather than pooled sample-level values
