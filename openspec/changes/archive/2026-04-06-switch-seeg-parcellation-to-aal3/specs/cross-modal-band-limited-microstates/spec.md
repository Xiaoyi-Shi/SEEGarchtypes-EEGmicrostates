## MODIFIED Requirements

### Requirement: The pipeline produces synchronized `1-40 Hz` analysis inputs for both modalities
The system SHALL derive a shared `1-40 Hz` staged representation for EEG and SEEG from the same `IDE_A` cohort and the same per-patient analysis windows, and SHALL use those staged inputs as the common upstream inputs for band-limited activity and connectivity analyses.

#### Scenario: Patient is eligible for the focused band-limited workflow
- **WHEN** a patient belongs to the main `IDE_A` cohort
- **THEN** the system SHALL produce staged EEG state inputs and staged SEEG `AAL3` region inputs filtered to `1-40 Hz` for downstream activity and connectivity stages

#### Scenario: Shared band-limited inputs are cached
- **WHEN** the focused `1-40 Hz` workflow is executed
- **THEN** the system SHALL persist reusable `1-40 Hz` EEG and SEEG staged artifacts so downstream activity and connectivity stages do not overwrite one another or force upstream recomputation
