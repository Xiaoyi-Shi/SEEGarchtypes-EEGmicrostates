## MODIFIED Requirements

### Requirement: The public CLI SHALL expose a focused staged `1-40 Hz` workflow
The system SHALL expose a public command surface centered on the staged `1-40 Hz` analysis workflow rather than multiple co-equal experimental branches.

#### Scenario: User inspects the available public commands
- **WHEN** a user requests CLI help
- **THEN** the public commands SHALL map to staged workflow steps for index preparation, EEG state generation, SEEG region generation, activity effects, connectivity effects, and report rendering, and the SEEG stage SHALL be described as producing `AAL3` region outputs for the public workflow

#### Scenario: Legacy branch-centric commands are retired from the public workflow
- **WHEN** the streamlined CLI is released
- **THEN** legacy public commands for `main` EEG, HFA coupling, and cross-modal overlap SHALL no longer define the primary public workflow

### Requirement: Each public stage SHALL persist reusable intermediate artifacts
The system SHALL persist stage outputs so users can rerun downstream analysis steps without recomputing upstream stages.

#### Scenario: Upstream EEG state artifacts already exist
- **WHEN** a downstream activity or connectivity stage runs after EEG state artifacts were already generated
- **THEN** the downstream stage SHALL reuse the cached EEG state artifacts rather than recomputing them

#### Scenario: User debugs a downstream method change
- **WHEN** a user reruns connectivity effects after changing only the connectivity method or downstream statistics
- **THEN** the workflow SHALL allow the user to reuse the existing index, EEG state, and staged `AAL3` region caches

### Requirement: Reports SHALL be exported from staged analysis results
The system SHALL export figures and table outputs from the staged workflow into report directories without requiring users to manually transform cached results, and SHALL render EEG microstate figures from the native staged `pycrostates` model artifact when it is available.

#### Scenario: Reports are rendered after EEG and downstream stages complete
- **WHEN** the report stage runs after staged EEG, activity, and connectivity caches exist
- **THEN** the system SHALL write an EEG microstate topographic figure derived from the staged `pycrostates` model artifact together with the available `AAL3` activity and connectivity figure and Excel outputs

#### Scenario: Only a subset of staged outputs exists
- **WHEN** the report stage runs and some staged result caches are absent
- **THEN** the report stage SHALL export the EEG microstate topographic figure and any other reports only for the result sets whose required staged artifacts are available
