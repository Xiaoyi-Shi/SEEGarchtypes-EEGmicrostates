## ADDED Requirements

### Requirement: R Markdown workflows SHALL support table-only supplementary statistics output
The maintained R Markdown workflow family SHALL include a table-only document that assembles supplementary statistical tables for final manuscript figures using the same source-output traceability principles as the figure-rendering documents.

#### Scenario: User renders the supplementary statistics R Markdown
- **WHEN** source CSV outputs exist under `artifacts/manual/` for the final figure families
- **THEN** the table-only R Markdown workflow SHALL render supplement-ready statistical tables
- **AND** it SHALL write CSV side tables and a manifest without rendering new figure panels

#### Scenario: Supplement tables are tied to final assembled figures
- **WHEN** the workflow detects or is configured with final figure files under `results/figs/`
- **THEN** it SHALL preserve stable figure-family and panel-label mappings in the rendered tables and manifest
- **AND** the output SHALL make clear which table supports which final figure panel
