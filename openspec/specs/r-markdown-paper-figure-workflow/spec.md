## Purpose
Define the maintained R Markdown figure-rendering workflow used to turn exported analysis tables into manuscript-ready figures, including the revised seizure-stage and IDE-A comparison reporting split.

## Requirements

### Requirement: Maintained R Markdown scripts SHALL render manuscript figures from categorized paper exports
The system SHALL provide a maintained R Markdown workflow under `scripts/` that reads categorized manuscript tables and manifest metadata from a selected staged run and renders the corresponding paper-core and supplementary figures without relying on Python plotting code.

#### Scenario: User renders main manuscript figures from exported paper tables
- **WHEN** main paper-core tables and manifests exist for a selected run
- **THEN** the maintained R Markdown workflow SHALL read those inputs and render the corresponding main manuscript figures
- **AND** the workflow SHALL preserve figure ordering consistent with the retained paper storyline

#### Scenario: User renders supplementary manuscript figures from exported paper tables
- **WHEN** supplementary tables and manifests exist for a selected run
- **THEN** the maintained R Markdown workflow SHALL read those inputs and render the corresponding supplementary manuscript figures

### Requirement: R Markdown figure rendering SHALL use a coherent scientific visual grammar
The maintained R Markdown workflow SHALL render manuscript figures with a consistent visual grammar across topography panels, heatmaps, support summaries, and lag curves so related results can be compared directly in the manuscript.

#### Scenario: A conditioned EEG topography panel is rendered from exported tables
- **WHEN** the R Markdown workflow renders archetype-conditioned EEG topography figures
- **THEN** it SHALL use stable panel ordering, consistent channel layout, and shared color semantics across the panel set

#### Scenario: A heatmap or lag curve is rendered from exported tables
- **WHEN** the R Markdown workflow renders similarity, preference, support, or lag summaries
- **THEN** it SHALL use stable titles, axis labeling, and color or line conventions shared across the retained paper-focused analyses

### Requirement: R Markdown scripts SHALL fail clearly when required inputs are missing or stale
The maintained R Markdown workflow SHALL validate that required categorized tables and manifests exist before rendering and SHALL report missing or incompatible inputs clearly instead of silently producing partial or misleading figures.

#### Scenario: Required table input is missing
- **WHEN** a user attempts to render a figure family whose required categorized tables or manifests are not present for the selected run
- **THEN** the R Markdown workflow SHALL stop with a clear error that identifies the missing input

#### Scenario: Manifest metadata does not match the expected figure family
- **WHEN** a manifest row or table schema does not match the requested figure family
- **THEN** the R Markdown workflow SHALL stop with a clear validation error rather than guessing how to reshape the data

### Requirement: Maintained R Markdown scripts SHALL render a supplementary field-state model-order figure family
The maintained R Markdown workflow SHALL render a supplementary field-state model-order figure family from exported supplementary paper tables so the manuscript can visualize the retained support for `K=4`.

#### Scenario: User renders the supplementary model-order figure family
- **WHEN** exported supplementary model-order tables and manifest rows exist for a selected run
- **THEN** the R Markdown workflow SHALL render the corresponding supplementary field-state model-order figure family
- **AND** the figure family SHALL preserve the retained narrative that `K=4` is the main-text default while `K=2..7` appears as supporting evaluation

### Requirement: The supplementary model-order figure family SHALL show fit plateau, gain, and stability
The maintained R Markdown workflow SHALL render the model-order figure family using panels that summarize candidate-`K` fit, incremental gain, and stability across patients, and SHALL keep interpretability-collapse diagnostics available through paired supplementary tables or companion panels.

#### Scenario: Model-order figure panels are rendered
- **WHEN** the supplementary model-order figure family is rendered
- **THEN** the figure family SHALL include panels that allow readers to inspect fit plateau, gain decay, and stability across `K=2..7`
- **AND** the figure family SHALL not present alternative `K` values as replacement main-text defaults without the supporting diagnostics

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

#### Scenario: User renders stage-only figures with incomplete paired EEG-SEEG eligibility
- **WHEN** SEEG-only outputs exist but paired EEG-SEEG relationship outputs are unavailable
- **THEN** the seizure-stage-only report SHALL still render SEEG-only seizure-stage figures
- **AND** it SHALL stop only for figure panels whose required paired EEG-SEEG inputs are missing, with a clear missing-input message

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

### Requirement: Maintained R Markdown scripts SHALL render the remaining main-text validation figure family
The maintained R Markdown workflow SHALL include a dedicated manuscript-facing document under `scripts/` that renders the remaining validation and cohort-characterization panels required by the updated manuscript outline from exported tables, cached summaries, or manual CSV inputs.

#### Scenario: User renders the validation figure family from maintained scripts
- **WHEN** required coverage, model-order, archetype-support, lag-coupling, and conditioned-EEG inputs are available
- **THEN** the maintained R Markdown workflow SHALL render reproducible SVG outputs for the missing main-text validation panels
- **AND** the panels SHALL use the same visual grammar and audit-friendly CSV side outputs as the existing maintained manual figure workflows

### Requirement: Validation-family R Markdown outputs SHALL label cohort characterization as `Yeo17` coverage while preserving the retained analytical summaries
The maintained R Markdown workflow SHALL present the cohort-coverage panel in `Yeo17` network labels and SHALL not relabel the retained archetype, lag-coupling, or seizure-stage analytical outputs as a different parcellation result.

#### Scenario: User renders `Yeo17` coverage alongside archetype validation panels
- **WHEN** the validation-family workflow combines cohort coverage, archetype reproducibility, and conditioned-EEG follow-up panels in one document
- **THEN** the saved outputs SHALL label the coverage panel as `Yeo17` cohort characterization
- **AND** any archetype-loading, lag-coupling, or seizure-stage panels reused in the same workflow SHALL remain labeled according to their retained `Yeo17` or EEG analysis spaces

### Requirement: R Markdown workflows SHALL support table-only supplementary statistics output
The maintained R Markdown workflow family SHALL include a table-only document that assembles supplementary statistical tables for final manuscript figures using the same source-output traceability principles as the figure-rendering documents.

#### Scenario: User renders the supplementary statistics R Markdown
- **WHEN** source CSV outputs exist under `artifacts/manual/` for the final figure families
- **THEN** the table-only R Markdown workflow SHALL render supplement-ready statistical tables
- **AND** it SHALL write CSV side tables and a manifest without rendering new figure panels

#### Scenario: Supplement tables are tied to final assembled figures
- **WHEN** the workflow detects or is configured with final figure files under `results/figs/`
- **THEN** it SHALL preserve stable figure-family and panel-label mappings in the rendered tables and manifest
- **AND** the output SHALL make clear which table supports which final figure panel
