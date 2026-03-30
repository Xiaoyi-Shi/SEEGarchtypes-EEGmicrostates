## MODIFIED Requirements

### Requirement: The pipeline produces synchronized `1-40 Hz` analysis inputs for both modalities
The system SHALL derive a shared `1-40 Hz` staged representation for EEG and SEEG from the same `IDE_A` cohort and the same per-patient analysis windows, and SHALL use those staged inputs as the common upstream inputs for band-limited activity and connectivity analyses.

#### Scenario: Patient is eligible for the focused band-limited workflow
- **WHEN** a patient belongs to the main `IDE_A` cohort
- **THEN** the system SHALL produce staged EEG state inputs and staged SEEG Yeo17 network inputs filtered to `1-40 Hz` for downstream activity and connectivity stages

#### Scenario: Shared band-limited inputs are cached
- **WHEN** the focused `1-40 Hz` workflow is executed
- **THEN** the system SHALL persist reusable `1-40 Hz` EEG and SEEG staged artifacts so downstream activity and connectivity stages do not overwrite one another or force upstream recomputation

## REMOVED Requirements

### Requirement: The pipeline derives EEG and SEEG microstate sequences in the `1-40 Hz` branch
**Reason**: The focused public workflow no longer treats SEEG microstate generation as a required branch product. The mainline now uses EEG states plus Yeo17 network signals as shared upstream artifacts for activity and connectivity analyses.
**Migration**: Use staged EEG state generation and staged SEEG network generation instead of band-limited SEEG microstate fitting in the main workflow.

### Requirement: Cross-modal branch outputs quantify EEG and SEEG microstate correspondence
**Reason**: EEG/SEEG microstate overlap is no longer a primary public workflow target. The project is being narrowed to state-conditioned Yeo17 activity and connectivity outputs.
**Migration**: Replace cross-modal overlap reporting with the activity-effects and connectivity-effects stages in the focused workflow.
