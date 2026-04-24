## ADDED Requirements

### Requirement: Seizure-stage R Markdown reporting SHALL separate stage-only and IDE-A baseline questions
The maintained R Markdown workflow SHALL keep seizure-stage descriptive reporting and IDE-A baseline comparison reporting in separate documents with distinct interpretation boundaries.

#### Scenario: User renders the seizure-stage-only report
- **WHEN** `scripts/07_seizure_stage_microstate_archetype_trajectory.Rmd` is rendered from seizure-stage exported tables
- **THEN** the report SHALL describe `pre`, `LVFA`, `SZ`, and `post` stage trajectories, denominators, timing QC, stage-duration diagnostics, and projection confidence without presenting IDE-A baseline deltas
- **AND** the outputs SHALL be labeled as seizure-stage descriptive summaries

#### Scenario: User renders the IDE-A comparison report
- **WHEN** `scripts/08_ide_a_vs_seizure_stage_comparison.Rmd` is rendered from IDE-A baseline artifacts and seizure-stage exported tables
- **THEN** the report SHALL compute and display stage-minus-IDE-A patient-level deltas
- **AND** the outputs SHALL be labeled as IDE-A baseline comparison or clinical extension outputs

### Requirement: The seizure-stage-only report SHALL emphasize QC, trajectories, and reference-space confidence
The seizure-stage-only R Markdown report SHALL render a manuscript-ready figure family that prioritizes data support, stage duration, state trajectories, and projection/backfitting confidence diagnostics.

#### Scenario: Seizure-stage QC panels are rendered
- **WHEN** segment, denominator, processing QC, and timing tables are available
- **THEN** the report SHALL render SVG panels for metric-family denominators, usable versus excluded stage segments, stage duration imbalance, and processing/projection eligibility
- **AND** the report SHALL export matching QC CSV summaries

#### Scenario: Seizure-stage trajectory panels are rendered
- **WHEN** patient-level EEG microstate and SEEG archetype stage metrics are available
- **THEN** the report SHALL render stage-ordered trajectory panels for core parameters such as occupancy, dwell time, occurrence, and confidence
- **AND** repeated-event structure SHALL be summarized at the patient level for group-facing panels

#### Scenario: Seizure-stage heatmaps are rendered
- **WHEN** Yeo17 loading or EEG-SEEG relationship tables are available
- **THEN** the report SHALL render stage-aware heatmaps using stable network, archetype, microstate, and stage ordering
- **AND** color semantics SHALL clearly distinguish high versus low values within the seizure-stage descriptive context

### Requirement: The IDE-A comparison report SHALL implement the improved patient-first baseline framework
The IDE-A comparison R Markdown report SHALL use IDE-A as a patient-level baseline, compute matched patient deltas, preserve repeated-seizure traceability, and respect the primary/secondary/tertiary metric hierarchy.

#### Scenario: Patient-level deltas are computed
- **WHEN** a patient has both IDE-A baseline values and seizure-stage values for the same metric family and state identifier
- **THEN** the report SHALL compute `delta(stage) = patient_mean(stage) - patient_mean(IDE-A)`
- **AND** repeated seizures within the same patient and stage SHALL be averaged before group-level summaries

#### Scenario: Primary metric outputs are rendered
- **WHEN** EEG microstate and SEEG archetype occupancy or dwell-time comparisons are available
- **THEN** the report SHALL render primary core-metric panels before secondary or tertiary metrics
- **AND** the report SHALL include paired effect-size or forest-style summaries with matched patient denominators

#### Scenario: Secondary and tertiary metric outputs are rendered
- **WHEN** Yeo17 loading, archetype composition, or EEG-SEEG relationship comparison tables are available
- **THEN** the report SHALL render them as secondary or tertiary outputs with signed stage-minus-IDE-A heatmaps
- **AND** labels SHALL make clear that relationship metrics are exploratory and not causal transfer estimates

### Requirement: IDE-A comparison reporting SHALL include sensitivity and stratification outputs
The IDE-A comparison R Markdown report SHALL export and, where feasible, plot sensitivity analyses for seizure type, repeated seizures, stage duration imbalance, complete-case support, and projection confidence.

#### Scenario: Seizure type labels are available
- **WHEN** seizure-stage rows contain `seizure_type` values such as `CPS` and `GTCS`
- **THEN** the report SHALL preserve seizure type in model-ready long outputs
- **AND** it SHALL export stratified summaries or plots for seizure type when each stratum has usable matched patients

#### Scenario: Stage durations differ across stages or patients
- **WHEN** segment timing or duration columns are available
- **THEN** the report SHALL export stage-duration QC summaries
- **AND** it SHALL make duration imbalance visible so dwell-time and occurrence results can be interpreted cautiously

#### Scenario: Projection confidence is available
- **WHEN** EEG microstate confidence, SEEG assignment similarity, or related quality columns are available
- **THEN** the report SHALL export confidence diagnostics by condition or stage
- **AND** it SHALL allow users to identify stages that may be out of the IDE-A reference-space distribution

### Requirement: Revised R Markdown outputs SHALL be reproducible and manuscript-ready
The revised `07` and `08` R Markdown reports SHALL render SVG figures and audit-ready CSV tables from source exports, without requiring previously generated SVG or CSV outputs to exist.

#### Scenario: Outputs are regenerated after cleanup
- **WHEN** prior manual outputs are absent or have been moved to a cleanup directory
- **THEN** the reports SHALL regenerate required SVG and CSV outputs from source tables and caches
- **AND** they SHALL fail only when source inputs required for the requested report are missing

#### Scenario: Reports are rendered for manuscript assembly
- **WHEN** the revised reports complete successfully
- **THEN** saved SVG panels SHALL have clear X-axis and Y-axis labels, stable panel ordering, and no unnecessary main titles or subtitles
- **AND** generated CSV files SHALL include enough identifiers to audit plotted values and reproduce group estimates
