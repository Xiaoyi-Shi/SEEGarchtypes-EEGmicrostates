## MODIFIED Requirements

### Requirement: The staged EEG command SHALL accept a template-file override
The system SHALL allow the public EEG state generation stage to label against an active `pycrostates` `.fif` template selected from an explicit template-file override or, when none is supplied, from the configured default template path, without creating a separate top-level workflow command.

#### Scenario: User inspects EEG stage help
- **WHEN** a user requests help for the public EEG state generation stage
- **THEN** the command SHALL expose a template-file input for supplying an external `pycrostates` cluster solution
- **AND** the help text SHALL describe that the stage otherwise uses the configured default template file

#### Scenario: User runs the staged EEG command with a template override
- **WHEN** a user supplies an external template file to the public EEG state generation stage
- **THEN** the staged workflow SHALL use that template file for EEG labeling while keeping downstream cache locations compatible with the rest of the public workflow

#### Scenario: User runs the staged EEG command without a template override
- **WHEN** a user runs the public EEG state generation stage without `--template-fif`
- **THEN** the staged workflow SHALL use the configured default template file for EEG labeling
- **AND** the stage SHALL stop before labeling with a clear error if that configured template file is unavailable

### Requirement: The public CLI SHALL expose a focused staged `1-40 Hz` workflow
The system SHALL expose a public command surface centered on the focused staged `1-40 Hz` analysis workflow, SHALL keep `IDE_A` as the default analysis state while allowing `IDE_S` as an optional override, SHALL expose the public SEEG staging step as `run-seeg-regions`, and SHALL allow only the maintained exploratory analyses explicitly supported by the region-based workflow plus the opt-in direct EEG-SEEG state-coupling branch.

#### Scenario: User inspects the available public commands
- **WHEN** a user requests CLI help
- **THEN** the command surface SHALL expose the focused staged workflow for index preparation, EEG state generation, SEEG region generation, activity effects, connectivity effects, exploratory coupling, and report rendering
- **AND** the shared staged commands SHALL expose `--analysis-state` with `IDE_A` as the default and `IDE_S` as a supported option
- **AND** the public SEEG staging command SHALL be named `run-seeg-regions`
- **AND** the exploratory coupling entry point SHALL expose only maintained region-signal analyses plus the supported direct EEG-SEEG state-coupling analyses

#### Scenario: Legacy branch-centric commands are retired from the public workflow
- **WHEN** the streamlined CLI is released with the region-oriented command surface and direct-coupling exploratory extensions
- **THEN** legacy public commands or maintained command aliases for HFA staging, HFA coupling, the old SEEG-microstate cross-modal branch, and `run-seeg-networks` SHALL not define the public workflow

### Requirement: Each public stage SHALL persist reusable intermediate artifacts
The system SHALL persist stage outputs so users can rerun downstream analysis steps without recomputing upstream stages, SHALL keep those reusable artifacts distinct by selected analysis state, and SHALL allow exploratory direct state-coupling reruns to reuse matching upstream staged artifacts.

#### Scenario: Upstream EEG state artifacts already exist
- **WHEN** a downstream activity or connectivity stage runs after EEG state artifacts were already generated for the selected analysis state
- **THEN** the downstream stage SHALL reuse the cached EEG state artifacts rather than recomputing them

#### Scenario: User debugs a downstream method change
- **WHEN** a user reruns connectivity effects after changing only the connectivity method or downstream statistics
- **THEN** the workflow SHALL allow the user to reuse the existing index, EEG state, and staged `AAL3` region caches for the same selected analysis state

#### Scenario: User reruns a direct state-coupling analysis after changing only direct-branch parameters
- **WHEN** a user reruns a direct EEG-SEEG state-coupling analysis after the required index, EEG, and staged SEEG signal artifacts already exist for the selected analysis state
- **THEN** the workflow SHALL reuse the matching upstream staged inputs and recompute only the direct-coupling branch outputs whose cache identity changed

### Requirement: Reports SHALL be exported from staged analysis results
The system SHALL export figures and table outputs from the staged workflow into report directories without requiring users to manually transform cached results, SHALL render EEG microstate figures from the native staged `pycrostates` model artifact when it is available, SHALL export focused-workflow omnibus and post-hoc report artifacts for the main activity and connectivity stages when those caches exist, and SHALL export maintained exploratory region-signal and direct state-coupling reports whenever the corresponding exploratory caches exist for the selected analysis state.

#### Scenario: Reports are rendered after EEG and downstream stages complete
- **WHEN** the report stage runs after staged EEG, main activity, and main connectivity caches exist for the selected analysis state
- **THEN** the system SHALL write an EEG microstate topographic figure derived from the staged `pycrostates` model artifact together with the available `AAL3` activity omnibus, activity post-hoc, connectivity omnibus, and connectivity post-hoc figure and table outputs

#### Scenario: Exploratory caches exist when reports are rendered
- **WHEN** the report stage runs after one or more exploratory region-signal or direct state-coupling analyses have already written their caches for the selected analysis state
- **THEN** the report stage SHALL export the corresponding exploratory figures and tables in addition to the standard main-workflow omnibus and post-hoc reports

#### Scenario: Only a subset of staged outputs exists
- **WHEN** the report stage runs and some staged result caches are absent for the selected analysis state
- **THEN** the report stage SHALL export the EEG microstate topographic figure and any other reports only for the result sets whose required staged artifacts are available
