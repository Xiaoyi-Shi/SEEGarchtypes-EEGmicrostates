## ADDED Requirements

### Requirement: Manuscript-ready exports SHALL classify field-state model-order outputs as supplementary paper tables
The system SHALL export supplementary manuscript-ready field-state model-order tables and manifest metadata that preserve candidate `K`, patient-level support, group-level summaries, and the diagnostics needed to justify retained `K=4` in manuscript text.

#### Scenario: Model-order tables are exported
- **WHEN** supplementary field-state model-order caches exist during paper-table export
- **THEN** the export layer SHALL write categorized supplementary tables for patient-level and group-level model-order summaries
- **AND** those tables SHALL preserve `K`, fit, gain, stability, and interpretability diagnostics in stable scientific schemas

#### Scenario: Model-order manifest metadata is exported
- **WHEN** supplementary field-state model-order tables are written
- **THEN** the manifest SHALL preserve branch identity, evaluated `K` range, and analysis metadata needed to trace the manuscript claim that `K=4` remains the retained main-text default
