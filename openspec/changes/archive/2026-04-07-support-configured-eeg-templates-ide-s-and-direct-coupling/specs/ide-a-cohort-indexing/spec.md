## MODIFIED Requirements

### Requirement: IDE_A recordings are indexed from repository data
The system SHALL scan the repository data tree and spreadsheet metadata to produce a structured index of available EEG, reference SEEG, bipolar SEEG, and atlas resources for the selected supported analysis state, SHALL keep `IDE_A` as the default analysis state, and SHALL support `IDE_S` as an optional override.

#### Scenario: Patient has all required assets for the selected analysis state
- **WHEN** a patient directory contains paired EEG and bipolar SEEG files plus an `Atlas.tsv` file for the selected analysis state
- **THEN** the index SHALL include a row for that patient with resolved paths for each required asset

#### Scenario: Patient is missing a required asset for the selected analysis state
- **WHEN** a patient lacks any required EEG, bipolar SEEG, or atlas input for the selected analysis state
- **THEN** the index SHALL record the patient as incomplete and SHALL NOT mark the patient eligible for the main cohort

### Requirement: IDE_A segment windows are materialized from metadata
The system SHALL derive analysis windows for the selected supported analysis state from the metadata workbook, SHALL keep `IDE_A` as the default state selection, and SHALL persist explicit segment boundaries for downstream EEG and SEEG loading.

#### Scenario: Metadata is present for the selected analysis state
- **WHEN** the metadata workbook provides valid timing values for the selected analysis state for a patient
- **THEN** the system SHALL write a segment row for that state with start time, end time, and duration

#### Scenario: Timing metadata is invalid for the selected analysis state
- **WHEN** the metadata workbook contains missing or non-positive segment boundaries for the selected analysis state
- **THEN** the system SHALL exclude that segment from the main analysis cohort and SHALL record the exclusion reason

### Requirement: Main IDE_A cohort membership is determined from channel coverage and metadata
The system SHALL derive a main analysis cohort that includes only patients with usable assets for the selected analysis state, valid segment metadata, and EEG coverage of the shared 11-channel montage after channel-name normalization.

#### Scenario: Patient covers the shared 11-channel montage in the selected analysis-state EEG
- **WHEN** a patient's EEG for the selected analysis state contains the shared frontal, central, parietal, and occipital channels after normalization
- **THEN** the patient SHALL be included in the main cohort for that selected analysis state

#### Scenario: Patient lacks required EEG coverage in the selected analysis-state EEG
- **WHEN** a patient's EEG for the selected analysis state is missing one or more channels from the shared 11-channel montage
- **THEN** the patient SHALL be excluded from the main cohort and the missing channels SHALL be recorded in cohort metadata
