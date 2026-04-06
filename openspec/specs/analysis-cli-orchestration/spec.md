## ADDED Requirements

### Requirement: The staged EEG command SHALL accept a template-file override
The system SHALL allow the public EEG state generation stage to accept an external `pycrostates` `.fif` template file without creating a separate top-level workflow command.

#### Scenario: User inspects EEG stage help
- **WHEN** a user requests help for the public EEG state generation stage
- **THEN** the command SHALL expose a template-file input for supplying an external `pycrostates` cluster solution

#### Scenario: User runs the staged EEG command with a template override
- **WHEN** a user supplies an external template file to the public EEG state generation stage
- **THEN** the staged workflow SHALL use that template file for EEG labeling while keeping downstream cache locations compatible with the rest of the public workflow

### Requirement: Exploratory coupling analyses SHALL reuse staged upstream artifacts
The orchestration layer SHALL allow exploratory coupling analyses to reuse the existing staged index, EEG microstate labels, and staged SEEG region signal caches without recomputing those upstream artifacts.

#### Scenario: User reruns an exploratory method after changing only exploratory parameters
- **WHEN** a user reruns an exploratory coupling analysis after the required index, EEG, and SEEG staged artifacts already exist
- **THEN** the orchestration layer SHALL reuse the upstream staged inputs and recompute only the exploratory method outputs whose cache identity changed

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

### Requirement: Each public stage SHALL persist reusable intermediate artifacts
The system SHALL persist stage outputs so users can rerun downstream analysis steps without recomputing upstream stages.

#### Scenario: Upstream EEG state artifacts already exist
- **WHEN** a downstream activity or connectivity stage runs after EEG state artifacts were already generated
- **THEN** the downstream stage SHALL reuse the cached EEG state artifacts rather than recomputing them

#### Scenario: User debugs a downstream method change
- **WHEN** a user reruns connectivity effects after changing only the connectivity method or downstream statistics
- **THEN** the workflow SHALL allow the user to reuse the existing index, EEG state, and staged `AAL3` region caches

### Requirement: Reports SHALL be exported from staged analysis results
The system SHALL export figures and table outputs from the staged workflow into report directories without requiring users to manually transform cached results, SHALL render EEG microstate figures from the native staged `pycrostates` model artifact when it is available, SHALL export focused-workflow omnibus and post-hoc report artifacts for the main activity and connectivity stages when those caches exist, and SHALL export exploratory coupling reports whenever the corresponding exploratory caches exist.

#### Scenario: Reports are rendered after EEG and downstream stages complete
- **WHEN** the report stage runs after staged EEG, main activity, and main connectivity caches exist
- **THEN** the system SHALL write an EEG microstate topographic figure derived from the staged `pycrostates` model artifact together with the available `AAL3` activity omnibus, activity post-hoc, connectivity omnibus, and connectivity post-hoc figure and table outputs

#### Scenario: Exploratory caches exist when reports are rendered
- **WHEN** the report stage runs after one or more exploratory coupling analyses have already written their caches
- **THEN** the report stage SHALL export the corresponding exploratory figures and tables in addition to the standard main-workflow omnibus and post-hoc reports

#### Scenario: Only a subset of staged outputs exists
- **WHEN** the report stage runs and some staged result caches are absent
- **THEN** the report stage SHALL export the EEG microstate topographic figure and any other reports only for the result sets whose required staged artifacts are available
