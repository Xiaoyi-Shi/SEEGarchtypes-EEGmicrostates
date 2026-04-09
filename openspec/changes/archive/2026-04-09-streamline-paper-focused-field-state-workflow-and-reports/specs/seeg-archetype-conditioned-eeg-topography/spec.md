## MODIFIED Requirements

### Requirement: SEEG field-state archetypes SHALL support EEG-space conditioned map summaries
The system SHALL allow group-matched SEEG field-state archetypes to be related back to EEG sensor space through archetype-conditioned EEG scalp maps derived on the shared analysis axis, and SHALL standardize those maps as manuscript-facing conditioned-topography outputs rather than as raw cache mirrors.

#### Scenario: User requests EEG-space interpretation of SEEG field-state archetypes
- **WHEN** group SEEG field-state archetypes and staged EEG sensor-space artifacts are available
- **THEN** the workflow SHALL derive EEG-space summaries conditioned on archetype activity instead of directly correlating SEEG common-space loadings with EEG scalp maps
- **AND** the report layer SHALL emit ordered conditioned-topography panels suitable for manuscript figures

### Requirement: Archetype-conditioned EEG summaries SHALL preserve patient-first template and state-preference inference
The system SHALL compute archetype-conditioned EEG template similarity and EEG state-preference summaries within each patient before group aggregation, SHALL persist patient-level support diagnostics together with group-level outputs, and SHALL preserve distributed archetype-to-microstate relationships in manuscript-facing tables.

#### Scenario: Archetype-conditioned EEG similarity is estimated
- **WHEN** the workflow compares archetype-conditioned EEG scalp maps to staged EEG microstate templates
- **THEN** it SHALL estimate those similarities from patient-level conditioned summaries rather than pooled EEG samples
- **AND** the report layer SHALL emit a standardized similarity matrix with effect size and support columns

#### Scenario: Archetype-conditioned EEG preference is exported
- **WHEN** group-level archetype-conditioned EEG preference tables are written
- **THEN** the outputs SHALL retain patient-support diagnostics and preserve SEEG archetype identity across all reported rows
- **AND** the report layer SHALL avoid collapsing distributed preference patterns into a forced best-match label

### Requirement: Archetype-conditioned EEG synchrony and SEEG-led transition follow-ups SHALL remain native-grid and structured-null
The system SHALL estimate near-zero SEEG archetype versus EEG microstate synchrony on the native shared `4 ms` grid and SHALL estimate secondary SEEG-led archetype-transition follow-ups using temporal-structure-preserving surrogate or permutation procedures, with synchrony treated as the retained main result and transition follow-ups treated as supplementary context.

#### Scenario: Fine-lag archetype-conditioned synchrony is estimated
- **WHEN** the workflow computes near-zero lag SEEG archetype versus EEG microstate coupling
- **THEN** the lag curve SHALL be evaluated on the native `4 ms` grid
- **AND** the persisted summaries SHALL preserve subject-level peak-lag or near-zero support diagnostics
- **AND** the report layer SHALL route this family to the retained main paper bundle

#### Scenario: SEEG-led archetype-transition significance is estimated
- **WHEN** the workflow computes significance for archetype-transition to EEG entry or switching follow-ups
- **THEN** the null procedure SHALL preserve the temporal structure of the SEEG archetype and EEG state sequences through constrained surrogate generation or equivalent structured permutation
- **AND** the report layer SHALL route these outputs to supplementary figure/table bundles

