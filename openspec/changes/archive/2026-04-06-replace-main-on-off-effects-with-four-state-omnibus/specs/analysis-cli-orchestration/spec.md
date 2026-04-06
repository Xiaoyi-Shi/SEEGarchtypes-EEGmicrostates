## MODIFIED Requirements

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
