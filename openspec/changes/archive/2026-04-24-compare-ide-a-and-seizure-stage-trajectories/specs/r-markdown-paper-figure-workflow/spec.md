## ADDED Requirements

### Requirement: Maintained R Markdown scripts SHALL render IDE-A versus seizure-stage comparison figures
The maintained R Markdown workflow SHALL include an IDE-A versus seizure-stage comparison document that reads exported IDE-A baseline tables and seizure-stage tables, computes patient-first comparison summaries, and renders manuscript-style SVG figures.

#### Scenario: User renders IDE-A versus seizure-stage figures
- **WHEN** required IDE-A baseline exports and seizure-stage trajectory exports exist
- **THEN** the R Markdown workflow SHALL render IDE-A versus seizure-stage comparison figures as SVG outputs
- **AND** it SHALL preserve stable condition ordering for `IDE-A`, `pre`, `LVFA`, `SZ`, and `post`

#### Scenario: User renders comparison tables for later statistics
- **WHEN** the R Markdown workflow computes comparison summaries
- **THEN** it SHALL export CSV tables containing the patient-level values, deltas, denominators, and model-ready long records used by the figures
- **AND** the exported tables SHALL preserve metric-family identifiers needed to audit each panel

### Requirement: IDE-A versus seizure-stage figures SHALL follow the existing scientific visual grammar
The IDE-A versus seizure-stage R Markdown workflow SHALL use the established visual style from existing manuscript support figures while making baseline, stage, and signed-delta structure explicit.

#### Scenario: A trajectory or delta panel is rendered
- **WHEN** the workflow renders EEG microstate or SEEG archetype occupancy, duration, occurrence, GFP, or assignment-similarity comparisons
- **THEN** the panel SHALL use clear X-axis and Y-axis labels, stable state or archetype ordering, and patient-first summaries
- **AND** it SHALL avoid unnecessary main titles and subtitles in saved figure panels

#### Scenario: A signed heatmap is rendered
- **WHEN** the workflow renders Yeo17 loading or EEG-SEEG relationship deltas
- **THEN** the heatmap SHALL use stable network, state, archetype, microstate, and condition ordering
- **AND** its color scale SHALL be centered on zero so increases and decreases relative to IDE-A are visually distinct

### Requirement: IDE-A versus seizure-stage R Markdown rendering SHALL validate inputs before plotting
The IDE-A versus seizure-stage R Markdown workflow SHALL validate required comparison inputs and SHALL make missing metric-family support explicit rather than producing misleading partial figures.

#### Scenario: A required comparison table is missing
- **WHEN** a user attempts to render a comparison panel and a required IDE-A or seizure-stage table is absent
- **THEN** the R Markdown workflow SHALL stop with a clear message or render an explicit placeholder for only the affected panel
- **AND** the message SHALL identify the missing table and expected input directory

#### Scenario: Required identifiers do not overlap
- **WHEN** IDE-A and seizure-stage tables have no overlapping patients for a requested paired comparison
- **THEN** the R Markdown workflow SHALL report the empty overlap in a denominator or QC output
- **AND** it SHALL NOT render a paired delta panel that implies matched observations exist
