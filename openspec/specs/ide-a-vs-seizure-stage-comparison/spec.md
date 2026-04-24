## Purpose
Define the IDE-A versus seizure-stage comparison capability, including validated inputs, patient-first baseline deltas, model-ready exports, and manuscript-facing comparison figures.

## Requirements

### Requirement: IDE-A and seizure-stage comparison inputs SHALL be validated
The system SHALL provide a comparison workflow that reads existing IDE-A baseline exports and seizure-stage trajectory exports, validates required identifiers and metric columns, and reports missing or incompatible inputs before computing comparisons.

#### Scenario: Required IDE-A and seizure-stage tables are available
- **WHEN** the comparison workflow is configured with an IDE-A report/export directory and a seizure-stage export directory containing required metric tables
- **THEN** the workflow SHALL load the required tables for the requested metric families
- **AND** it SHALL validate patient identifiers, state/archetype/network identifiers, metric columns, and seizure-stage labels before plotting or exporting results

#### Scenario: A required comparison input is missing
- **WHEN** an IDE-A baseline table or seizure-stage table required for a requested figure family is absent
- **THEN** the workflow SHALL stop for that figure family with a clear error or explicit placeholder that identifies the missing file and affected output
- **AND** it SHALL NOT silently substitute unrelated tables or recompute labels from raw data

### Requirement: Comparisons SHALL use IDE-A as the patient-level baseline
The comparison workflow SHALL summarize IDE-A metrics at the patient level and SHALL compare seizure-stage metrics against the matching patient's IDE-A baseline whenever both baseline and seizure-stage observations exist.

#### Scenario: A patient has both IDE-A and seizure-stage observations
- **WHEN** a patient has an IDE-A baseline value and one or more usable seizure-stage values for the same metric family and state identifier
- **THEN** the workflow SHALL compute patient-level stage summaries
- **AND** it SHALL compute a delta value defined as `stage_value - ide_a_value`

#### Scenario: A patient has multiple seizures in the same stage
- **WHEN** a patient contributes multiple seizure recordings to the same stage and metric family
- **THEN** the workflow SHALL retain seizure-level rows for traceability
- **AND** it SHALL use patient-level stage means for group-facing summaries and primary comparison plots

#### Scenario: A patient lacks a matched IDE-A baseline for a metric
- **WHEN** a patient has seizure-stage observations but no matching IDE-A baseline for the same metric family and state identifier
- **THEN** the workflow SHALL exclude that patient from the paired delta for that specific metric comparison
- **AND** it SHALL include the exclusion in denominator or QC outputs

### Requirement: Comparison outputs SHALL preserve model-ready long format
The comparison workflow SHALL export CSV tables that contain baseline values, seizure-stage values, deltas, denominators, and model-ready long records for EEG microstate, SEEG archetype, Yeo17 loading, and EEG-SEEG relationship comparisons.

#### Scenario: Comparison tables are exported
- **WHEN** the comparison workflow completes a metric family
- **THEN** it SHALL write a CSV table with `patient_id`, `condition`, metric-family identifiers, metric names, metric values, and denominator fields needed to reproduce the plotted summaries
- **AND** it SHALL write delta summary CSV tables with patient-level delta values and group-level estimates

#### Scenario: Seizure type stratification is available
- **WHEN** seizure-stage rows include seizure type labels such as `CPS` and `GTCS`
- **THEN** the exported model-ready tables SHALL preserve `seizure_type`
- **AND** the workflow SHALL allow stratified descriptive summaries without requiring separate reruns

### Requirement: Comparison statistics SHALL respect repeated-patient structure
The comparison workflow SHALL treat patients as the independent statistical unit for primary summaries and SHALL avoid treating repeated seizures from the same patient as independent subjects.

#### Scenario: Group-level delta estimates are computed
- **WHEN** the workflow estimates group-level IDE-A versus stage differences
- **THEN** it SHALL aggregate repeated seizure events within patient before computing group-facing means, intervals, or paired displays
- **AND** output tables SHALL make the patient-level denominator explicit

#### Scenario: Inferential model tables are produced
- **WHEN** inferential statistics are produced from model-ready tables
- **THEN** the model specification SHALL include patient as the repeated-measures unit or grouping factor
- **AND** the output SHALL identify the tested condition contrast, estimate, uncertainty interval, and sample denominator

### Requirement: Comparison figures SHALL show condition and delta structure clearly
The comparison workflow SHALL render SVG figures that communicate IDE-A baseline, seizure-stage order, and signed stage-wise deviations for the main metric families.

#### Scenario: Main comparison figures are rendered
- **WHEN** required comparison tables are available
- **THEN** the workflow SHALL render SVG figures for cohort/QC denominators, EEG microstate deltas, SEEG archetype deltas, Yeo17 network loading deltas, and EEG-SEEG relationship deltas
- **AND** the figures SHALL use stable ordering for `IDE-A`, `pre`, `LVFA`, `SZ`, and `post`

#### Scenario: Heatmap-style comparison figures are rendered
- **WHEN** Yeo17 loading or EEG-SEEG relationship comparison tables are available
- **THEN** the workflow SHALL render signed-delta heatmaps with zero-centered color scales
- **AND** high versus low or positive versus negative deviations SHALL be visually unambiguous

#### Scenario: A combined overview is rendered
- **WHEN** the main comparison panels are available
- **THEN** the workflow SHALL render a combined overview SVG suitable for manuscript assembly
- **AND** each panel SHALL have clear X-axis and Y-axis labels without requiring main titles or subtitles

### Requirement: Comparison documentation SHALL define interpretation boundaries
The system SHALL update project documentation to describe the IDE-A versus seizure-stage comparison purpose, required inputs, statistical unit, main outputs, and interpretation cautions.

#### Scenario: Documentation is updated
- **WHEN** the comparison workflow is added
- **THEN** the docs SHALL explain that IDE-A is used as a baseline state-space reference and within-patient comparison anchor
- **AND** the docs SHALL state that observed deltas are observational seizure-stage deviations rather than causal proof of epilepsy progression
