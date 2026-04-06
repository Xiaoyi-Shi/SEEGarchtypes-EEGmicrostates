## MODIFIED Requirements

### Requirement: The pipeline produces synchronized `1-40 Hz` analysis inputs for both modalities
The system SHALL derive a shared `1-40 Hz` staged representation for EEG and SEEG from the same `IDE_A` cohort and the same per-patient analysis windows, and SHALL treat staged EEG microstate labels plus staged SEEG region signals as the maintained upstream inputs for downstream activity, connectivity, and supported exploratory analyses.

#### Scenario: Patient is eligible for the focused band-limited workflow
- **WHEN** a patient belongs to the main `IDE_A` cohort
- **THEN** the system SHALL produce staged EEG microstate labels and staged SEEG `AAL3` region inputs filtered to `1-40 Hz` for downstream activity, connectivity, and supported exploratory stages
- **AND** the focused workflow SHALL not require a separate maintained SEEG-microstate overlap branch

#### Scenario: Shared band-limited inputs are cached
- **WHEN** the focused `1-40 Hz` workflow or a supported exploratory coupling analysis is executed
- **THEN** the system SHALL persist reusable `1-40 Hz` EEG label and SEEG region staged artifacts so downstream analyses do not overwrite one another or force upstream recomputation
