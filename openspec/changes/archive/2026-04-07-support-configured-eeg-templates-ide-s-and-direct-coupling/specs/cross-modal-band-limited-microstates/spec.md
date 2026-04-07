## MODIFIED Requirements

### Requirement: The pipeline produces synchronized `1-40 Hz` analysis inputs for both modalities
The system SHALL derive a shared `1-40 Hz` staged representation for EEG and SEEG from the same selected supported analysis-state cohort and the same per-patient analysis windows, SHALL keep `IDE_A` as the default analysis state while supporting `IDE_S` as an optional override, and SHALL treat staged EEG microstate labels plus staged SEEG region signals as the maintained upstream inputs for downstream activity, connectivity, and supported exploratory analyses.

#### Scenario: Patient is eligible for the focused band-limited workflow
- **WHEN** a patient belongs to the main cohort for the selected analysis state
- **THEN** the system SHALL produce staged EEG microstate labels and staged SEEG `AAL3` region inputs filtered to `1-40 Hz` for downstream activity, connectivity, and supported exploratory stages
- **AND** the focused workflow SHALL not require a separate maintained SEEG-microstate overlap branch

#### Scenario: Shared band-limited inputs are cached
- **WHEN** the focused `1-40 Hz` workflow or a supported exploratory coupling analysis is executed for a selected analysis state
- **THEN** the system SHALL persist reusable `1-40 Hz` EEG label and SEEG region staged artifacts so downstream analyses do not overwrite one another or force upstream recomputation

### Requirement: Exploratory cross-modal analyses SHALL consume the same staged cohort and windows as the focused workflow
Exploratory coupling analyses SHALL operate on the same eligible selected-analysis-state cohort membership and the same per-patient staged analysis windows as the focused workflow unless the user explicitly requests a different exploratory subset in a future change.

#### Scenario: User runs an exploratory coupling method after staging the focused workflow
- **WHEN** a user runs any exploratory coupling analysis after the shared `1-40 Hz` staged inputs exist for the selected analysis state
- **THEN** the analysis SHALL use the same staged cohort and window definitions as the focused workflow inputs rather than deriving a separate implicit cohort

## ADDED Requirements

### Requirement: Direct state-coupling analyses SHALL derive downstream-specific SEEG state artifacts from the shared staged inputs
The system SHALL allow the exploratory direct EEG-SEEG state-coupling branch to derive reduced-space SEEG state artifacts from the shared staged EEG labels and staged SEEG signals, and SHALL keep those downstream-specific state artifacts distinct from the maintained upstream contract of EEG labels plus SEEG region signals.

#### Scenario: User runs a direct state-coupling analysis after staging the focused workflow
- **WHEN** a user requests a direct EEG-SEEG state-coupling analysis after the shared staged EEG labels and SEEG signals already exist for the selected analysis state
- **THEN** the workflow SHALL derive and cache any required reduced-space SEEG state artifacts as exploratory branch outputs
- **AND** the workflow SHALL NOT replace the maintained staged EEG-label or staged SEEG-region artifacts

#### Scenario: User reruns direct state coupling with different exploratory state-space parameters
- **WHEN** a user reruns a direct EEG-SEEG state-coupling analysis after changing only reduced-space state-derivation or lag parameters
- **THEN** the workflow SHALL reuse the matching staged EEG labels and staged SEEG signals and recompute only the affected exploratory direct-state artifacts
