## ADDED Requirements

### Requirement: Archetype-conditioned EEG exports SHALL include patient-level scalp-map tables for representative panels
The system SHALL export patient-level archetype-conditioned EEG scalp-map tables with stable channel ordering, stable archetype ordering, and per-subject support metadata so R Markdown workflows can render representative single-subject panels without recomputing conditioned maps from raw EEG samples.

#### Scenario: Representative single-subject conditioned EEG maps are exported
- **WHEN** group-level archetype-conditioned EEG maps are derived for manuscript reporting
- **THEN** the export layer SHALL also emit patient-level conditioned-EEG map tables that preserve channel identities, archetype identities, and support counts or equivalent confidence metadata
- **AND** the patient-level tables SHALL remain directly consumable by manuscript-facing R workflows

### Requirement: Archetype-conditioned EEG exports SHALL support deterministic representative-subject selection
The system SHALL emit enough metadata for manuscript workflows to choose representative single-subject conditioned EEG panels reproducibly and anonymize displayed subject labels without losing patient-first traceability in the exported tables.

#### Scenario: Manuscript workflow selects representative subjects
- **WHEN** representative single-subject EEG panels are prepared for plotting
- **THEN** the export layer SHALL provide stable subject identifiers plus ranking or filtering metadata such as support, confidence, or similarity summaries
- **AND** downstream figure workflows SHALL be able to display anonymized labels while keeping the selection reproducible from the exported tables
