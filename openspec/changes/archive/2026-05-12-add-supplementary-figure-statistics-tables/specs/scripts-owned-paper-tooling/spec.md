## ADDED Requirements

### Requirement: Scripts-owned paper tooling SHALL include supplement table assembly
The repository SHALL keep supplement-facing statistical table assembly under `scripts/` and SHALL require it to consume exported result tables or cached manual outputs rather than expanding the Python package command surface.

#### Scenario: User needs supplementary statistical tables for manuscript figures
- **WHEN** a user needs concrete statistics behind final manuscript figure panels
- **THEN** the maintained entry point SHALL live under `scripts/`
- **AND** the tool SHALL operate on `artifacts/manual/` CSV outputs or exported report tables produced by the retained analysis workflows

#### Scenario: Supplement table workflow needs additional summaries
- **WHEN** a table requires simple formatting or aggregation of existing exported values
- **THEN** the script MAY compute those summaries in R from source CSV files
- **AND** it SHALL not rerun core EEG/SEEG state extraction or coupling analyses
