## MODIFIED Requirements

### Requirement: Exploratory coupling analyses SHALL reuse staged upstream artifacts
The orchestration layer SHALL allow the maintained paper-focused exploratory analyses to reuse the existing staged index, EEG microstate labels, staged EEG GFP artifacts, staged EEG sensor-space artifacts, and the branch-specific SEEG exploratory inputs required by each retained method, including subject-level SEEG field-state artifacts for electrode-space field-state methods, common-space field-state projection artifacts for group archetype methods, and group archetype assignments for archetype-conditioned EEG topography methods, without recomputing those reusable upstream artifacts.

#### Scenario: User reruns a paper-core SEEG field-state method after changing only exploratory parameters
- **WHEN** a user reruns a maintained SEEG global-field-state exploratory analysis after the required index, EEG, GFP, and subject-level SEEG field-state artifacts already exist
- **THEN** the orchestration layer SHALL reuse those upstream inputs and recompute only the retained field-state branch outputs whose cache identity changed

#### Scenario: User reruns a field-state archetype method after changing only common-space or matching parameters
- **WHEN** a user reruns a group SEEG field-state archetype analysis after the required index, EEG, and subject-level SEEG field-state artifacts already exist
- **THEN** the orchestration layer SHALL reuse the upstream staged inputs and recompute only the archetype branch outputs whose cache identity changed

#### Scenario: User reruns archetype-conditioned EEG topography after changing only EEG-alignment parameters
- **WHEN** a user reruns an archetype-conditioned EEG topography analysis after the required index, staged EEG artifacts, subject-level SEEG field-state artifacts, and group archetype assignments already exist
- **THEN** the orchestration layer SHALL reuse those upstream staged inputs and recompute only the archetype-conditioned EEG outputs whose cache identity changed

#### Scenario: User reruns a supplementary GFP or SEEG-led switching follow-up
- **WHEN** a user reruns a retained supplementary GFP/global or SEEG-led switching analysis after the required staged inputs already exist
- **THEN** the orchestration layer SHALL reuse those upstream staged inputs and recompute only the supplementary branch outputs whose cache identity changed

### Requirement: The public CLI SHALL expose a focused staged `1-40 Hz` workflow
The system SHALL expose a public command surface centered on the focused staged `1-40 Hz` analysis workflow, SHALL keep `IDE_A` as the default analysis state while allowing `IDE_S` as an optional override, SHALL expose the public SEEG staging step as `run-seeg-regions`, and SHALL limit the maintained exploratory command surface to the paper-focused SEEG field-state pipeline plus explicitly supplementary GFP-informed global and SEEG-led switching follow-ups.

#### Scenario: User inspects the available public commands
- **WHEN** a user requests CLI help
- **THEN** the command surface SHALL expose the focused staged workflow for index preparation, EEG state generation, SEEG region generation, exploratory coupling, and report rendering
- **AND** the shared staged commands SHALL expose `--analysis-state` with `IDE_A` as the default and `IDE_S` as a supported option
- **AND** the public SEEG staging command SHALL be named `run-seeg-regions`
- **AND** the exploratory coupling entry point SHALL expose the maintained field-state analyses needed for the paper workflow, including field-state derivation, group archetypes, archetype-conditioned EEG topography, and native `4 ms` fine-lag synchrony, together with explicitly supplementary GFP/global and SEEG-led switching follow-ups

#### Scenario: Retired region-signal exploratory methods are no longer part of the maintained public surface
- **WHEN** the streamlined paper-focused CLI is released
- **THEN** region-signal event, windowed, and transition exploratory analyses SHALL not appear in the maintained public exploratory help surface
- **AND** their historical implementation, if still present internally, SHALL not define the maintained paper workflow

### Requirement: Reports SHALL be exported from staged analysis results
The system SHALL export figures and table outputs from the staged workflow into report directories without requiring users to manually transform cached results, SHALL render manuscript-ready main and supplementary bundles for the retained paper-focused analyses instead of cache-shaped report dumps, and SHALL export only the report bundles whose required staged artifacts are available for the selected analysis state.

#### Scenario: Main paper-core caches exist when reports are rendered
- **WHEN** the report stage runs after field-state, archetype, archetype-conditioned EEG topography, and fine-lag caches exist for the selected analysis state
- **THEN** the report stage SHALL write the corresponding manuscript-ready main figures and main tables for the paper-focused workflow

#### Scenario: Supplementary follow-up caches exist when reports are rendered
- **WHEN** the report stage runs after retained supplementary GFP/global or SEEG-led switching caches exist for the selected analysis state
- **THEN** the report stage SHALL write the corresponding supplementary figures and supplementary tables without promoting them into the main figure/table bundle

#### Scenario: Only a subset of paper-focused outputs exists
- **WHEN** the report stage runs and only some retained paper-focused result caches are present
- **THEN** the report stage SHALL export only the manuscript-ready bundles whose required staged artifacts are available

