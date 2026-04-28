## ADDED Requirements

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
