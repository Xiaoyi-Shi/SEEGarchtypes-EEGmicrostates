## MODIFIED Requirements

### Requirement: Paper-focused analyses SHALL export only result tables and manifest metadata from the Python package
The system SHALL transform retained staged and exploratory caches into manuscript-ready categorized table bundles and manifest metadata for the paper-focused workflow, SHALL keep final figure rendering and other special paper tooling outside the Python package under `scripts/`, and SHALL stop exposing package-level figure/report rendering compatibility paths as part of the maintained workflow.

#### Scenario: Paper tables are exported from retained analysis caches
- **WHEN** retained paper-core or supplementary analysis caches exist for a selected run
- **THEN** the Python package SHALL emit only categorized CSV/XLSX result tables and manifest metadata under the run report directory
- **AND** the export step SHALL NOT require Python package figure rendering

#### Scenario: Users need figures or special paper tooling
- **WHEN** users need manuscript figures or one-off support tooling on top of exported results
- **THEN** the repository SHALL provide those entry points under `scripts/`
- **AND** those scripts SHALL consume exported result tables or cached analysis outputs rather than extending the maintained package CLI

### Requirement: Manuscript-ready tables SHALL use stable scientific schemas
The system SHALL export manuscript-ready tables using stable, analysis-family-specific schemas that preserve effect sizes, significance, and subject-support diagnostics in a consistent column order.

#### Scenario: A lag or coupling table is exported
- **WHEN** the export layer writes a manuscript-ready lag or coupling table
- **THEN** the table SHALL preserve core scientific columns including effect size, significance, subject support, and analysis identity in a stable order suitable for manuscript writing and downstream R Markdown consumption

#### Scenario: A similarity or preference table is exported
- **WHEN** the export layer writes archetype similarity or preference summaries
- **THEN** the table SHALL preserve distributed relationships and support diagnostics rather than collapsing outputs to a forced best label

### Requirement: Manuscript-ready exports SHALL preserve traceability to staged artifacts
The system SHALL preserve enough metadata in manuscript-facing outputs to map each categorized table and downstream figure back to its staged branch identity, parameterization, and subject-support context.

#### Scenario: A manuscript-ready table or manifest row is written
- **WHEN** the export layer writes a paper-facing asset
- **THEN** the output SHALL retain branch identity and analysis metadata either in the asset schema, manifest, or paired metadata table so manuscript claims remain traceable to staged results

## REMOVED Requirements

### Requirement: Manuscript-ready figures SHALL use a coherent visual grammar
**Reason**: Final manuscript figure rendering is moving out of Python and into the maintained R Markdown workflow under `scripts/`.
**Migration**: Use the new `r-markdown-paper-figure-workflow` capability to define figure grammar, panel ordering, and visual conventions for manuscript figures derived from exported tables.

### Requirement: Manuscript-ready exports SHALL classify field-state model-order outputs as supplementary paper tables
The system SHALL export supplementary manuscript-ready field-state model-order tables and manifest metadata that preserve candidate `K`, patient-level support, group-level summaries, and the diagnostics needed to justify retained `K=4` in manuscript text.

#### Scenario: Model-order tables are exported
- **WHEN** supplementary field-state model-order caches exist during paper-table export
- **THEN** the export layer SHALL write categorized supplementary tables for patient-level and group-level model-order summaries
- **AND** those tables SHALL preserve `K`, fit, gain, stability, and interpretability diagnostics in stable scientific schemas

#### Scenario: Model-order manifest metadata is exported
- **WHEN** supplementary field-state model-order tables are written
- **THEN** the manifest SHALL preserve branch identity, evaluated `K` range, and analysis metadata needed to trace the manuscript claim that `K=4` remains the retained main-text default
