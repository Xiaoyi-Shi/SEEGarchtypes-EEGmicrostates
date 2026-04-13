## MODIFIED Requirements

### Requirement: IDE_A bipolar SEEG SHALL be staged as same-region `AAL3` result data for the retained workflow
The system SHALL compute `1-40 Hz` same-region `AAL3` SEEG result data from valid bipolar channels, SHALL persist same-region mapping, coverage summaries, and reusable staged region signals as retained workflow outputs, and SHALL stop treating region-level activity/connectivity effect branches as part of the maintained public workflow.

#### Scenario: User runs the SEEG region generation stage
- **WHEN** an eligible bipolar SEEG recording is processed in the retained workflow
- **THEN** the system SHALL write same-region mapping artifacts, coverage summaries, and staged `AAL3` result data that can be reused by retained analyses or supplementary tooling

#### Scenario: User inspects the maintained workflow scope
- **WHEN** a user inspects the retained public workflow
- **THEN** the maintained workflow SHALL expose SEEG region data staging as a retained result-data step
- **AND** the maintained workflow SHALL NOT expose public region activity or region connectivity effect stages
