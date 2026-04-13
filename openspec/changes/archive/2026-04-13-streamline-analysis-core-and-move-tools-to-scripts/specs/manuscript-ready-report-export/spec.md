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
