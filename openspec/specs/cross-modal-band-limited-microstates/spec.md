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

## ADDED Requirements

### Requirement: Exploratory cross-modal analyses SHALL consume the same staged cohort and windows as the focused workflow
Exploratory coupling analyses SHALL operate on the same eligible `IDE_A` cohort membership and the same per-patient staged analysis windows as the focused workflow unless the user explicitly requests a different exploratory subset in a future change.

#### Scenario: User runs an exploratory coupling method after staging the focused workflow
- **WHEN** a user runs any exploratory coupling analysis after the shared `1-40 Hz` staged inputs exist
- **THEN** the analysis SHALL use the same staged cohort and window definitions as the focused workflow inputs rather than deriving a separate implicit cohort

## REMOVED Requirements

### Requirement: The pipeline derives EEG and SEEG microstate sequences in the `1-40 Hz` branch
**Reason**: The maintained public workflow no longer treats SEEG microstate generation as a required branch product. The maintained upstream contract is staged EEG microstate labels plus staged SEEG region signals.
**Migration**: Use staged EEG state generation and staged SEEG region generation instead of band-limited SEEG microstate fitting in the maintained workflow.

### Requirement: Cross-modal branch outputs quantify EEG and SEEG microstate correspondence
**Reason**: EEG/SEEG microstate overlap is no longer a maintained workflow target. The project now centers on region-based activity, connectivity, and the remaining supported exploratory analyses.
**Migration**: Replace the legacy overlap branch with the maintained activity-effects, connectivity-effects, and supported exploratory stages.
