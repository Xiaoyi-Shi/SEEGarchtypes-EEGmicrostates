## ADDED Requirements

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
