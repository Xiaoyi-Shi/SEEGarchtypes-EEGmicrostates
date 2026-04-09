## ADDED Requirements

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
