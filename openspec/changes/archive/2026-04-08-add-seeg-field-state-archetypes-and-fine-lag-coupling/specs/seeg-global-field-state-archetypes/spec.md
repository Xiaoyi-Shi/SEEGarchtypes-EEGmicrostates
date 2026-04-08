## ADDED Requirements

### Requirement: Subject-level SEEG field states SHALL support projection into a shared comparison space
The system SHALL derive common-space representations for subject-level SEEG field templates so cross-subject field-state comparison does not rely on raw bipolar channel identity, and SHALL use a stable shared representation suitable for group archetype discovery.

#### Scenario: User runs field-state archetype projection
- **WHEN** subject-level SEEG field-state templates are available and a user requests group archetype analysis
- **THEN** the workflow SHALL project each subject-level field-state template into a shared comparison space before cross-subject matching

#### Scenario: Group archetype matching uses the primary comparison space
- **WHEN** group archetype summaries are computed
- **THEN** the workflow SHALL use the supported primary common-space representation for archetype matching
- **AND** any finer-grained regional representation SHALL be treated as descriptive follow-up rather than the primary matching space

### Requirement: Group archetype matching SHALL align subject-level states before summarization
The system SHALL orient subject-level field-state templates consistently and SHALL match subject-level states into group archetypes using similarity-based assignment rather than discovery-order labels.

#### Scenario: A subject-level template is sign-flipped relative to a shared archetype
- **WHEN** a subject-level field-state template matches a group archetype up to global sign reversal
- **THEN** the matching step SHALL orient the template consistently before archetype assignment and summary export

#### Scenario: Subject-level field-state labels differ across patients
- **WHEN** field-state archetypes are summarized across patients
- **THEN** the workflow SHALL align subject-level states by matched archetype identity rather than by subject-local state index alone

### Requirement: Group archetype outputs SHALL preserve assignment and support diagnostics
The system SHALL persist group archetype summaries together with subject-to-archetype assignments, coverage/support diagnostics, and interpretable loading summaries for report export.

#### Scenario: Archetype summaries are exported
- **WHEN** group SEEG field-state archetype analysis completes
- **THEN** the workflow SHALL write group-level archetype templates, subject-level archetype assignments, and support diagnostics suitable for figures and tables

#### Scenario: Subject support is sparse for an archetype
- **WHEN** a candidate archetype lacks the required group support threshold
- **THEN** the workflow SHALL exclude that archetype from report-ready group summaries
