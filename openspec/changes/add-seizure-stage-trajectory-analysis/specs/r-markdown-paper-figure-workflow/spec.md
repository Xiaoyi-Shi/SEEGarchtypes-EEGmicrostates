## ADDED Requirements

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
