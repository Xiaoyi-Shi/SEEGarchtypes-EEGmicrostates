## MODIFIED Requirements

### Requirement: Group archetype outputs SHALL preserve assignment and support diagnostics
The system SHALL persist group archetype summaries together with subject-to-archetype assignments, coverage/support diagnostics, and interpretable loading summaries for report export, and SHALL standardize those outputs around manuscript-ready archetype tables rather than cache-shaped dumps.

#### Scenario: Archetype summaries are exported for the paper-focused workflow
- **WHEN** group SEEG field-state archetype analysis completes
- **THEN** the workflow SHALL write group-level archetype templates, subject-level archetype assignments, support diagnostics, and common-space loading summaries suitable for manuscript-ready figures and tables

#### Scenario: Subject support is sparse for an archetype
- **WHEN** a candidate archetype lacks the required group support threshold
- **THEN** the workflow SHALL exclude that archetype from report-ready group summaries

#### Scenario: Main and supplementary archetype outputs are separated
- **WHEN** manuscript-ready reports are rendered
- **THEN** the report layer SHALL place the primary archetype support and loading summaries into the main or supplementary bundle according to the retained paper layout
- **AND** the report layer SHALL avoid exporting raw cache-shaped archetype tables as default paper-facing outputs

