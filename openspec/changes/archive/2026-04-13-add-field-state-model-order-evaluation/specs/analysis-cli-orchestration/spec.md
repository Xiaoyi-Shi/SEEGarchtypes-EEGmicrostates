## ADDED Requirements

### Requirement: The public paper-focused workflow SHALL expose supplementary field-state model-order evaluation without changing the default `K=4` core
The system SHALL expose a maintained supplementary field-state model-order evaluation path within the public paper-focused workflow, SHALL keep the retained subject-level field-state core at `K=4`, and SHALL allow users to export paper-facing model-order outputs only when those supplementary caches are present.

#### Scenario: User requests supplementary field-state model-order evaluation
- **WHEN** a user invokes the maintained paper-focused workflow for field-state model-order evaluation
- **THEN** the workflow SHALL run the supplementary `K=2..7` model-order branch
- **AND** the default paper-core field-state branch SHALL remain fixed at `K=4`

#### Scenario: Paper tables are exported after model-order evaluation
- **WHEN** supplementary model-order caches exist for the selected run
- **THEN** the paper export stage SHALL include the corresponding supplementary model-order tables and manifest rows
- **AND** the export stage SHALL not rewrite the retained main-table field-state outputs as alternative `K` results
