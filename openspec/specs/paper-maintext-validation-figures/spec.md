# paper-maintext-validation-figures Specification

## Purpose
TBD - created by archiving change add-maintext-figure-gap-analysis. Update Purpose after archive.
## Requirements
### Requirement: Main-text validation figures SHALL render cohort characterization from `Yeo17` coverage
The system SHALL provide a maintained manuscript-facing workflow that renders the cohort-characterization panel for the updated manuscript outline from retained bipolar-channel counts and `Yeo17` network coverage, while leaving the downstream archetype analyses unchanged.

#### Scenario: User renders the `Figure 1C` cohort panel
- **WHEN** retained bipolar-channel counts and `Yeo17` network coverage inputs are available for the cohort
- **THEN** the workflow SHALL export an audit-ready patient-level coverage summary table and manuscript-ready SVG panel outputs
- **AND** the outputs SHALL show both retained bipolar-channel support and `Yeo17` network coverage in a form suitable for cohort characterization rather than archetype interpretation

### Requirement: Main-text validation figures SHALL render field-state reproducibility evidence
The system SHALL render a reproducibility figure family that combines field-state transition summaries, `K=2..7` model-order support, archetype support counts, and observed assignment similarity versus a permutation-based null reference.

#### Scenario: User renders the field-state reproducibility panels
- **WHEN** model-order diagnostics, field-state transition summaries, archetype-support summaries, and assignment-similarity null-reference tables are available
- **THEN** the workflow SHALL render manuscript-ready SVG panels for those evidence families with stable ordering across `K`, archetypes, and subjects
- **AND** the assignment-similarity panel SHALL distinguish observed similarities from the null reference rather than plotting observed ranks alone

### Requirement: Main-text validation figures SHALL decompose near-zero-lag synchrony into complementary panels
The system SHALL render the near-zero-lag synchrony result as a coordinated panel family that separates the group lag curve, subject peak-lag distribution, subject peak-width distribution, and observed-versus-null coupling reference.

#### Scenario: User renders the near-zero-lag validation panels
- **WHEN** group lag-curve summaries and subject-level peak summaries are available for the archetype-conditioned EEG coupling analysis
- **THEN** the workflow SHALL render a coordinated panel family that exposes the group curve, subject peak-lag distribution, subject peak-width distribution, and null-reference comparison
- **AND** the group lag summary SHALL preserve the native shared lag grid used by the retained analysis

### Requirement: Main-text validation figures SHALL render representative conditioned EEG interpretation panels
The system SHALL render group and representative single-subject archetype-conditioned EEG interpretation panels from standardized patient-first exports so the manuscript can compare the group background pattern with individual examples.

#### Scenario: User renders representative conditioned EEG maps
- **WHEN** group-level and patient-level archetype-conditioned EEG map tables are available
- **THEN** the workflow SHALL render group archetype-conditioned scalp maps together with a representative single-subject panel
- **AND** displayed subject labels SHALL be anonymized while preserving deterministic selection and archetype ordering

