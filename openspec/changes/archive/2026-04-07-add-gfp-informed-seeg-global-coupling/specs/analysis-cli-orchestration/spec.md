## MODIFIED Requirements

### Requirement: The public CLI SHALL expose a focused staged `1-40 Hz` workflow
The system SHALL expose a public command surface centered on the focused staged `1-40 Hz` analysis workflow, SHALL keep `IDE_A` as the default analysis state while allowing `IDE_S` as an optional override, SHALL expose the public SEEG staging step as `run-seeg-regions`, and SHALL allow only the maintained exploratory analyses explicitly supported by the region-based workflow plus the opt-in direct EEG-SEEG state-coupling branch and GFP-informed global-coupling branch.

#### Scenario: User inspects the available public commands
- **WHEN** a user requests CLI help
- **THEN** the command surface SHALL expose the focused staged workflow for index preparation, EEG state generation, SEEG region generation, activity effects, connectivity effects, exploratory coupling, and report rendering
- **AND** the shared staged commands SHALL expose `--analysis-state` with `IDE_A` as the default and `IDE_S` as a supported option
- **AND** the public SEEG staging command SHALL be named `run-seeg-regions`
- **AND** the exploratory coupling entry point SHALL expose only maintained region-signal analyses plus the supported direct EEG-SEEG state-coupling analyses and the supported GFP-informed global-coupling analyses

#### Scenario: Legacy branch-centric commands are retired from the public workflow
- **WHEN** the streamlined CLI is released with the region-oriented command surface, direct-coupling exploratory extensions, and GFP-informed global exploratory extensions
- **THEN** legacy public commands or maintained command aliases for HFA staging, HFA coupling, the old SEEG-microstate cross-modal branch, and `run-seeg-networks` SHALL not define the public workflow

### Requirement: Exploratory coupling analyses SHALL reuse staged upstream artifacts
The orchestration layer SHALL allow exploratory coupling analyses to reuse the existing staged index, EEG microstate labels, staged EEG GFP artifacts, and staged SEEG region signal caches without recomputing those upstream artifacts.

#### Scenario: User reruns an exploratory method after changing only exploratory parameters
- **WHEN** a user reruns an exploratory coupling analysis after the required index, EEG, GFP, and SEEG staged artifacts already exist
- **THEN** the orchestration layer SHALL reuse the upstream staged inputs and recompute only the exploratory method outputs whose cache identity changed

### Requirement: Reports SHALL be exported from staged analysis results
The system SHALL export figures and table outputs from the staged workflow into report directories without requiring users to manually transform cached results, SHALL render EEG microstate figures from the native staged `pycrostates` model artifact when it is available, SHALL export focused-workflow omnibus and post-hoc report artifacts for the main activity and connectivity stages when those caches exist, and SHALL export maintained exploratory region-signal, direct state-coupling, and GFP-informed global-coupling reports whenever the corresponding exploratory caches exist for the selected analysis state.

#### Scenario: Reports are rendered after EEG and downstream stages complete
- **WHEN** the report stage runs after staged EEG, main activity, and main connectivity caches exist for the selected analysis state
- **THEN** the system SHALL write an EEG microstate topographic figure derived from the staged `pycrostates` model artifact together with the available `AAL3` activity omnibus, activity post-hoc, connectivity omnibus, and connectivity post-hoc figure and table outputs

#### Scenario: Exploratory caches exist when reports are rendered
- **WHEN** the report stage runs after one or more exploratory region-signal, direct state-coupling, or GFP-informed global-coupling analyses have already written their caches for the selected analysis state
- **THEN** the report stage SHALL export the corresponding exploratory figures and tables in addition to the standard main-workflow omnibus and post-hoc reports

#### Scenario: Only a subset of staged outputs exists
- **WHEN** the report stage runs and some staged result caches are absent for the selected analysis state
- **THEN** the report stage SHALL export the EEG microstate topographic figure and any other reports only for the result sets whose required staged artifacts are available
