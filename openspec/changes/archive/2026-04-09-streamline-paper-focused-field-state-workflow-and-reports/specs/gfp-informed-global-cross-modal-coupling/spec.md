## MODIFIED Requirements

### Requirement: GFP-informed exploratory analyses SHALL derive predefined SEEG global metrics from staged Yeo17 signals
The system SHALL preserve GFP-informed global metrics as a retained supplementary branch derived from staged Yeo17 network signals using a predefined family of metric definitions rather than an ad hoc single summary, SHALL define one primary supplementary metric for interpretation, and SHALL keep manuscript-facing supplementary outputs distinct by metric definition and weighting strategy.

#### Scenario: User runs GFP-informed global coupling with the primary supplementary metric
- **WHEN** staged EEG artifacts and staged Yeo17 network signals are available and a user requests GFP-informed global coupling
- **THEN** the workflow SHALL derive the primary supplementary SEEG global metric from within-patient standardized Yeo17 core-network signals using an equal-weight RMS-style summary

#### Scenario: User compares predefined supplementary SEEG global metric definitions
- **WHEN** the supplementary GFP/global branch evaluates one or more supported SEEG global metric definitions
- **THEN** the workflow SHALL keep supplementary outputs distinct by metric definition and weighting strategy
- **AND** the branch SHALL support at least RMS-style magnitude, envelope-based magnitude, and spatial-dispersion style summaries

### Requirement: GFP-controlled state follow-ups SHALL separate shared amplitude effects from state-specific effects
The system SHALL support exploratory follow-up analyses that test whether EEG microstate and transition effects on SEEG global metrics remain after accounting for EEG GFP, and SHALL present those outputs as supplementary mechanistic context rather than as part of the main field-state result bundle.

#### Scenario: User runs GFP-controlled microstate follow-up
- **WHEN** a user requests a GFP-controlled microstate-to-SEEG global analysis
- **THEN** the workflow SHALL write patient-level and group-level summaries that model SEEG global metrics as a function of both EEG GFP and EEG microstate state identity
- **AND** the resulting exports SHALL be routed to supplementary figure/table bundles

#### Scenario: User runs GFP-controlled transition follow-up
- **WHEN** a user requests a GFP-controlled transition-conditioned SEEG global analysis
- **THEN** the workflow SHALL write patient-level and group-level summaries that preserve EEG transition identity while accounting for EEG GFP
- **AND** the resulting exports SHALL be routed to supplementary figure/table bundles

