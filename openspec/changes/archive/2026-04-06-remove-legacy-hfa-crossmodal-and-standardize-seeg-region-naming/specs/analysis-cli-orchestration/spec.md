## MODIFIED Requirements

### Requirement: The public CLI SHALL expose a focused staged `1-40 Hz` workflow
The system SHALL expose a public command surface centered on the focused staged `1-40 Hz` analysis workflow rather than multiple co-equal experimental branches, SHALL expose the public SEEG staging step as `run-seeg-regions`, and SHALL allow only the maintained exploratory coupling analyses explicitly supported by the region-based workflow.

#### Scenario: User inspects the available public commands
- **WHEN** a user requests CLI help
- **THEN** the command surface SHALL expose the focused staged workflow for index preparation, EEG state generation, SEEG region generation, activity effects, connectivity effects, and report rendering
- **AND** the public SEEG staging command SHALL be named `run-seeg-regions`
- **AND** the exploratory coupling entry point SHALL expose only maintained exploratory analyses that reuse staged EEG labels plus staged SEEG region signals

#### Scenario: Legacy branch-centric commands are retired from the public workflow
- **WHEN** the streamlined CLI is released with the region-oriented command surface
- **THEN** legacy public commands or maintained command aliases for HFA staging, HFA coupling, the old SEEG-microstate cross-modal branch, and `run-seeg-networks` SHALL not define the public workflow
