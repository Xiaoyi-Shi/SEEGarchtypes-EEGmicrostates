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

### Requirement: Maintained R Markdown scripts SHALL render a supplementary field-state model-order figure family
The maintained R Markdown workflow SHALL render a supplementary field-state model-order figure family from exported supplementary paper tables so the manuscript can visualize the retained support for `K=4`.

#### Scenario: User renders the supplementary model-order figure family
- **WHEN** exported supplementary model-order tables and manifest rows exist for a selected run
- **THEN** the R Markdown workflow SHALL render the corresponding supplementary field-state model-order figure family
- **AND** the figure family SHALL preserve the retained narrative that `K=4` is the main-text default while `K=2..7` appears as supporting evaluation

### Requirement: The supplementary model-order figure family SHALL show fit plateau, gain, and stability
The maintained R Markdown workflow SHALL render the model-order figure family using panels that summarize candidate-`K` fit, incremental gain, and stability across patients, and SHALL keep interpretability-collapse diagnostics available through paired supplementary tables or companion panels.

#### Scenario: Model-order figure panels are rendered
- **WHEN** the supplementary model-order figure family is rendered
- **THEN** the figure family SHALL include panels that allow readers to inspect fit plateau, gain decay, and stability across `K=2..7`
- **AND** the figure family SHALL not present alternative `K` values as replacement main-text defaults without the supporting diagnostics

### Requirement: Maintained R Markdown scripts SHALL render seizure-stage trajectory figures
The maintained R Markdown workflow SHALL include a seizure-stage figure family that reads exported seizure-stage tables and renders manuscript-style SVG figures for EEG microstate, SEEG archetype, Yeo/common-space loading, and EEG-SEEG relationship trajectories across seizure stages.

#### Scenario: User renders seizure-stage figures from exported tables
- **WHEN** seizure-stage metric tables, QC tables, and manifest metadata exist for a selected run or manual export directory
- **THEN** the seizure-stage R Markdown workflow SHALL render the corresponding trajectory figures as SVG outputs
- **AND** the figures SHALL preserve stable stage ordering for `pre`, `LVFA`, `SZ`, and `post`

#### Scenario: User renders figures with incomplete paired EEG-SEEG eligibility
- **WHEN** SEEG-only outputs exist but paired EEG-SEEG relationship outputs are unavailable
- **THEN** the R Markdown workflow SHALL still render SEEG-only seizure-stage figures
- **AND** it SHALL stop only for figure panels whose required paired EEG-SEEG inputs are missing, with a clear missing-input message

### Requirement: Seizure-stage figures SHALL use a stage-aware scientific visual grammar
The seizure-stage R Markdown workflow SHALL use a visual grammar consistent with existing manuscript figures while making seizure-stage structure explicit through stage ordering, cohort denominators, patient-first summaries, and clear axis labels without unnecessary main titles or subtitles.

#### Scenario: A seizure-stage trajectory panel is rendered
- **WHEN** the workflow renders a stage trajectory for occupancy, duration, assignment similarity, loading, or coupling metrics
- **THEN** the figure SHALL show stage on one axis or facet dimension and metric value on the other
- **AND** it SHALL make repeated-patient structure visible through patient-level summaries, paired lines, or model-ready aggregate displays when appropriate

#### Scenario: A seizure-stage heatmap is rendered
- **WHEN** the workflow renders archetype-by-stage, microstate-by-stage, or network-by-stage summaries
- **THEN** the figure SHALL use stable state, archetype, network, and stage ordering
- **AND** the color scale SHALL communicate high versus low values or signed deviations unambiguously

### Requirement: Seizure-stage R Markdown rendering SHALL validate inputs before plotting
The seizure-stage R Markdown workflow SHALL validate that required seizure-stage metric tables contain expected identifiers, stage labels, eligibility labels, and metric columns before rendering any figure family.

#### Scenario: Required seizure-stage table is missing
- **WHEN** a user attempts to render a seizure-stage figure family and a required table is absent
- **THEN** the R Markdown workflow SHALL stop with a clear error identifying the missing table and affected figure panel

#### Scenario: Stage labels are unexpected
- **WHEN** exported seizure-stage tables contain stage labels outside the supported stage set
- **THEN** the R Markdown workflow SHALL stop with a clear validation error unless the user has explicitly configured an extended stage ordering
