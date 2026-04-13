## ADDED Requirements

### Requirement: Plotting and special paper tooling SHALL live under `scripts/`
The repository SHALL keep plotting workflows and other special paper-support tools under `scripts/`, SHALL treat the Python package as the retained analysis-and-result-export core, and SHALL require scripts to consume exported result tables or cached analysis outputs instead of expanding the maintained package command surface.

#### Scenario: User needs a manuscript-facing figure workflow
- **WHEN** a user needs figure rendering or a special paper-support tool
- **THEN** the maintained entry point SHALL live under `scripts/`
- **AND** the tool SHALL operate on exported tables or cached results produced by the Python package
