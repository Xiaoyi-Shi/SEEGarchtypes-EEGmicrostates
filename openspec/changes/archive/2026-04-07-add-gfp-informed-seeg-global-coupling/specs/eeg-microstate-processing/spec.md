## ADDED Requirements

### Requirement: Staged EEG artifacts SHALL include reusable GFP traces and GFP peak events
The system SHALL persist reusable EEG global field power artifacts from the staged EEG branch so downstream exploratory analyses can compare continuous EEG global dynamics against SEEG summaries without recomputing the preprocessed EEG inputs.

#### Scenario: User completes the staged EEG branch
- **WHEN** the staged EEG state-generation command completes successfully
- **THEN** the workflow SHALL persist a continuous EEG GFP time series aligned to the staged EEG sample axis
- **AND** the workflow SHALL persist a reusable EEG GFP peak/event artifact derived from the same staged EEG input

#### Scenario: Downstream GFP-informed exploratory analyses require EEG global artifacts
- **WHEN** a downstream GFP-informed exploratory analysis is requested after the staged EEG branch already completed
- **THEN** the exploratory analysis SHALL consume the staged EEG GFP artifacts rather than recomputing GFP from the raw EEG files
