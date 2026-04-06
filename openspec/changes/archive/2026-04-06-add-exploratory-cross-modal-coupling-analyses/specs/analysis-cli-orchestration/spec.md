## MODIFIED Requirements

### Requirement: The public CLI SHALL expose a focused staged `1-40 Hz` workflow
The system SHALL expose a public command surface centered on the focused staged `1-40 Hz` analysis workflow rather than multiple co-equal experimental branches, and SHALL allow users to request exploratory coupling analyses explicitly without redefining the default staged path.

#### Scenario: User inspects the available public commands
- **WHEN** a user requests CLI help
- **THEN** the command surface SHALL continue to expose the focused staged workflow for index preparation, EEG state generation, SEEG signal generation, activity effects, connectivity effects, and report rendering, and SHALL also expose an explicit exploratory coupling entry point or equivalent opt-in mechanism

#### Scenario: Legacy branch-centric commands are retired from the public workflow
- **WHEN** the streamlined CLI is released with exploratory coupling support
- **THEN** legacy public commands for `main` EEG, HFA coupling, and the old branch-centric overlap workflow SHALL still not define the primary public workflow

### Requirement: Reports SHALL be exported from staged analysis results
The system SHALL export figures and table outputs from the staged workflow into report directories without requiring users to manually transform cached results, SHALL render EEG microstate figures from the native staged `pycrostates` model artifact when it is available, and SHALL export exploratory coupling reports whenever the corresponding exploratory caches exist.

#### Scenario: Reports are rendered after EEG and downstream stages complete
- **WHEN** the report stage runs after staged EEG, activity, and connectivity caches exist
- **THEN** the system SHALL write an EEG microstate topographic figure derived from the staged `pycrostates` model artifact together with the available activity and connectivity figure and Excel outputs

#### Scenario: Exploratory caches exist when reports are rendered
- **WHEN** the report stage runs after one or more exploratory coupling analyses have already written their caches
- **THEN** the report stage SHALL export the corresponding exploratory figures and tables in addition to the standard staged workflow reports

## ADDED Requirements

### Requirement: Exploratory coupling analyses SHALL reuse staged upstream artifacts
The orchestration layer SHALL allow exploratory coupling analyses to reuse the existing staged index, EEG microstate labels, and staged SEEG signal caches without recomputing those upstream artifacts.

#### Scenario: User reruns an exploratory method after changing only exploratory parameters
- **WHEN** a user reruns an exploratory coupling analysis after the required index, EEG, and SEEG staged artifacts already exist
- **THEN** the orchestration layer SHALL reuse the upstream staged inputs and recompute only the exploratory method outputs whose cache identity changed
