## MODIFIED Requirements

### Requirement: The pipeline produces synchronized `1-40 Hz` analysis inputs for both modalities
The system SHALL derive a shared `1-40 Hz` staged representation for EEG and SEEG from the same `IDE_A` cohort and the same per-patient analysis windows, and SHALL use those staged inputs as the common upstream inputs for band-limited activity, connectivity, and optional exploratory cross-modal coupling analyses.

#### Scenario: Patient is eligible for the focused band-limited workflow
- **WHEN** a patient belongs to the main `IDE_A` cohort
- **THEN** the system SHALL produce staged EEG state inputs and staged SEEG signals filtered to `1-40 Hz` for downstream activity, connectivity, and exploratory coupling stages

#### Scenario: Shared band-limited inputs are cached
- **WHEN** the focused `1-40 Hz` workflow or an exploratory coupling analysis is executed
- **THEN** the system SHALL persist reusable `1-40 Hz` EEG and SEEG staged artifacts so downstream activity, connectivity, and exploratory analyses do not overwrite one another or force upstream recomputation

## ADDED Requirements

### Requirement: Exploratory cross-modal analyses SHALL consume the same staged cohort and windows as the focused workflow
Exploratory coupling analyses SHALL operate on the same eligible `IDE_A` cohort membership and the same per-patient staged analysis windows as the focused workflow unless the user explicitly requests a different exploratory subset in a future change.

#### Scenario: User runs an exploratory coupling method after staging the focused workflow
- **WHEN** a user runs any exploratory coupling analysis after the shared `1-40 Hz` staged inputs exist
- **THEN** the analysis SHALL use the same staged cohort and window definitions as the focused workflow inputs rather than deriving a separate implicit cohort
