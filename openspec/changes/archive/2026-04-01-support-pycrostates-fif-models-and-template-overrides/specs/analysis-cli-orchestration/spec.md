## ADDED Requirements

### Requirement: The staged EEG command SHALL accept a template-file override
The system SHALL allow the public EEG state generation stage to accept an external `pycrostates` `.fif` template file without creating a separate top-level workflow command.

#### Scenario: User inspects EEG stage help
- **WHEN** a user requests help for the public EEG state generation stage
- **THEN** the command SHALL expose a template-file input for supplying an external `pycrostates` cluster solution

#### Scenario: User runs the staged EEG command with a template override
- **WHEN** a user supplies an external template file to the public EEG state generation stage
- **THEN** the staged workflow SHALL use that template file for EEG labeling while keeping downstream cache locations compatible with the rest of the public workflow

## MODIFIED Requirements

### Requirement: Reports SHALL be exported from staged analysis results
The system SHALL export figures and table outputs from the staged workflow into report directories without requiring users to manually transform cached results, and SHALL render EEG microstate figures from the native staged `pycrostates` model artifact when it is available.

#### Scenario: Reports are rendered after EEG and downstream stages complete
- **WHEN** the report stage runs after staged EEG, activity, and connectivity caches exist
- **THEN** the system SHALL write an EEG microstate topographic figure derived from the staged `pycrostates` model artifact together with the available activity and connectivity figure and Excel outputs

#### Scenario: Only a subset of staged outputs exists
- **WHEN** the report stage runs and some staged result caches are absent
- **THEN** the report stage SHALL export the EEG microstate topographic figure and any other reports only for the result sets whose required staged artifacts are available
