## ADDED Requirements

### Requirement: Workflow orchestration SHALL be organized into responsibility-specific modules
The `seeg_eegmicrostates.workflows` package SHALL organize workflow orchestration into responsibility-specific internal modules instead of maintaining a single monolithic implementation file, and SHALL separate shared workflow helpers, retained staged workflow execution, retained exploratory workflow execution, and paper-result export responsibilities into distinct module boundaries.

#### Scenario: Developer inspects the workflow package after the refactor
- **WHEN** a developer inspects `src/seeg_eegmicrostates/workflows/`
- **THEN** the package SHALL contain multiple internal modules or subpackages grouped by workflow responsibility
- **AND** the retained staged workflow logic, retained exploratory workflow logic, and paper export logic SHALL not all live in one monolithic `pipelines.py`

### Requirement: Public workflow entry points SHALL remain stable during internal modularization
The package SHALL preserve the public workflow entry points used by the maintained CLI and tests while the internal module layout is refactored, and SHALL continue to make those entry points available from `seeg_eegmicrostates.workflows`.

#### Scenario: Existing package consumers import public workflow entry points
- **WHEN** package code imports `build_index_artifacts`, `run_eeg_states_stage`, `run_seeg_regions_stage`, `run_exploratory_coupling_stage`, or `export_paper_tables` from `seeg_eegmicrostates.workflows`
- **THEN** those imports SHALL continue to resolve successfully after the refactor
- **AND** the imported functions SHALL continue to execute the retained workflow semantics

### Requirement: Workflow modularization SHALL align with the retained analysis surface
The internal workflow module layout SHALL be organized around the retained paper-focused analysis surface, and SHALL not preserve retired activity/connectivity, direct-state, region-event/windowed, or legacy report-rendering branches as first-class module boundaries in the maintained package.

#### Scenario: Developer inspects workflow modules created by the split
- **WHEN** the refactored workflow package is inspected
- **THEN** first-class workflow modules SHALL correspond to retained staged, exploratory, or export responsibilities
- **AND** the maintained module layout SHALL not introduce dedicated top-level modules whose only purpose is to preserve retired workflow branches
