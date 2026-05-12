## ADDED Requirements

### Requirement: Supplementary figure statistics tables SHALL be generated from maintained data exports
The system SHALL provide a maintained table-only R Markdown workflow that reads existing manuscript figure data exports and produces supplement-ready statistical tables for final assembled figure panels without regenerating figures.

#### Scenario: User renders supplement statistics tables for assembled figures
- **WHEN** final figure PDFs exist under `results/figs/` and matching source CSV outputs exist under `artifacts/manual/`
- **THEN** the workflow SHALL read the relevant CSV sources and render supplement-ready tables for the corresponding figure panels
- **AND** the workflow SHALL not require parsing PDF, SVG, AI, or raster figure files to recover statistical values

#### Scenario: User requests table-only output
- **WHEN** the supplementary statistics workflow is rendered
- **THEN** it SHALL generate tables and audit CSV outputs
- **AND** it SHALL not generate or overwrite manuscript figure image outputs

### Requirement: Supplementary tables SHALL preserve figure and panel traceability
The system SHALL map each generated table to the final figure family, panel label, source CSV file, and output table identifier so supplement values can be traced back to the maintained analysis export.

#### Scenario: A table is written for a figure panel
- **WHEN** the workflow writes a supplementary table for a labeled figure panel
- **THEN** the output manifest SHALL include the final figure file, panel label, table title, source CSV path, output CSV path, and any source-availability note

#### Scenario: A panel has no statistical source table
- **WHEN** a figure panel is illustrative or its source table is unavailable
- **THEN** the workflow SHALL add an explicit note in the rendered document or manifest
- **AND** it SHALL not fabricate statistical values from visual figure elements

### Requirement: Supplementary tables SHALL include panel-level descriptive and inferential values
The workflow SHALL produce table rows containing the concrete descriptive statistics, support counts, effect estimates, permutation p values, FDR-adjusted q values, and paired or stage-delta summaries needed to support the assembled figure panels.

#### Scenario: Archetype and Yeo17 panels are summarized
- **WHEN** archetype brain-map or patient-archetype statistic source CSVs are available
- **THEN** the workflow SHALL produce tables for Yeo17 loading summaries, support or coverage summaries, dwell-time contrasts, assignment similarity, and transition probabilities where those panels are present

#### Scenario: EEG-SEEG relationship panels are summarized
- **WHEN** relationship source CSVs are available
- **THEN** the workflow SHALL produce tables for template similarity, state preference, switching effects, fine-lag coupling, and subject peak summaries

#### Scenario: IDE-A versus seizure-stage panels are summarized
- **WHEN** IDE-A comparison source CSVs are available
- **THEN** the workflow SHALL produce tables for primary EEG/SEEG state deltas, complete-case support, projection confidence or duration QC, Yeo17 loading deltas, relationship deltas, and seizure-type or repeated-seizure sensitivity summaries when present

### Requirement: Supplementary table output SHALL be manuscript-ready and audit-ready
The workflow SHALL render publication-style three-line tables in the R Markdown document and write matching CSV files for each generated table.

#### Scenario: Tables are rendered in the R Markdown document
- **WHEN** the workflow renders a supplementary table
- **THEN** the table SHALL use stable row ordering, explicit units, rounded numeric formatting, and concise table captions suitable for supplementary material

#### Scenario: Tables are exported as CSV files
- **WHEN** the workflow renders a supplementary table
- **THEN** the same table data SHALL be written to a CSV file under the configured output directory
- **AND** a manifest SHALL list every exported table

### Requirement: Missing inputs SHALL be reported clearly
The workflow SHALL validate required source CSV files and fail or annotate missing input cases clearly so incomplete supplement tables are not mistaken for complete results.

#### Scenario: A required source CSV is missing
- **WHEN** a required table for a requested figure family is absent
- **THEN** the workflow SHALL stop with an error that identifies the missing file and figure family

#### Scenario: An optional source CSV is missing
- **WHEN** an optional source table is absent
- **THEN** the workflow SHALL continue rendering available tables
- **AND** it SHALL write an explicit unavailable-source note to the rendered document or manifest
