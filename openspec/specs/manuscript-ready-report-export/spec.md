## ADDED Requirements

### Requirement: Paper-focused analyses SHALL export manuscript-ready figure and table bundles
The system SHALL transform retained staged and exploratory caches into manuscript-ready report bundles that separate main figures, supplementary figures, main tables, and supplementary tables rather than exposing cache-shaped exports as the default paper-facing output.

#### Scenario: Main paper-core outputs are exported
- **WHEN** retained field-state, archetype, archetype-conditioned EEG topography, and fine-lag synchrony caches exist
- **THEN** the report layer SHALL emit the corresponding main figure and main table bundle for the paper-focused workflow

#### Scenario: Supplementary follow-ups are exported
- **WHEN** retained supplementary GFP/global or SEEG-led switching caches exist
- **THEN** the report layer SHALL emit those outputs into supplementary figure and supplementary table bundles rather than mixing them into the main bundle

### Requirement: Manuscript-ready tables SHALL use stable scientific schemas
The system SHALL export manuscript-ready tables using stable, analysis-family-specific schemas that preserve effect sizes, significance, and subject-support diagnostics in a consistent column order.

#### Scenario: A lag or coupling table is exported
- **WHEN** the report layer exports a manuscript-ready lag or coupling table
- **THEN** the table SHALL preserve core scientific columns including effect size, significance, subject support, and analysis identity in a stable order suitable for manuscript writing

#### Scenario: A similarity or preference table is exported
- **WHEN** the report layer exports archetype similarity or preference summaries
- **THEN** the table SHALL preserve distributed relationships and support diagnostics rather than collapsing outputs to a forced best label

### Requirement: Manuscript-ready figures SHALL use a coherent visual grammar
The system SHALL render manuscript-ready figures with a consistent visual grammar across topography panels, heatmaps, and lag curves so related results are easier to compare and present in an SCI manuscript.

#### Scenario: A conditioned EEG topography panel is rendered
- **WHEN** the report layer renders archetype-conditioned EEG maps
- **THEN** it SHALL use a stable panel ordering, consistent channel layout, and shared color semantics across the panel set

#### Scenario: A heatmap or lag curve is rendered
- **WHEN** the report layer renders similarity, preference, support, or lag summaries
- **THEN** it SHALL use stable titles, axis labeling, and color or line conventions shared across the retained paper-focused analyses

### Requirement: Manuscript-ready exports SHALL preserve traceability to staged artifacts
The system SHALL preserve enough metadata in manuscript-facing outputs to map each figure and table back to its staged branch identity, parameterization, and subject-support context.

#### Scenario: A manuscript-ready figure or table is written
- **WHEN** the report layer exports a paper-facing asset
- **THEN** the output SHALL retain branch identity and analysis metadata either in the asset schema, manifest, or paired metadata table so manuscript claims remain traceable to staged results

