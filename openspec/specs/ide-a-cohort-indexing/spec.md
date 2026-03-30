## ADDED Requirements

### Requirement: IDE_A recordings are indexed from repository data
The system SHALL scan the repository data tree and spreadsheet metadata to produce a structured index of available `IDE_A` EEG, reference SEEG, bipolar SEEG, and atlas resources for each patient.

#### Scenario: Patient has all required IDE_A assets
- **WHEN** a patient directory contains paired `IDE_A` EEG and bipolar SEEG files and an `Atlas.tsv` file
- **THEN** the index SHALL include a row for that patient with resolved paths for each required asset

#### Scenario: Patient is missing a required IDE_A asset
- **WHEN** a patient lacks any required `IDE_A` EEG, bipolar SEEG, or atlas input
- **THEN** the index SHALL record the patient as incomplete and SHALL NOT mark the patient eligible for the main cohort

### Requirement: IDE_A segment windows are materialized from metadata
The system SHALL derive `IDE_A` analysis windows from the metadata workbook and persist explicit segment boundaries for downstream EEG and SEEG loading.

#### Scenario: IDE_A rest metadata is present
- **WHEN** the metadata workbook provides `rest_start` and `rest_end` or equivalent `IDE_A` timing values for a patient
- **THEN** the system SHALL write an `IDE_A` segment row with start time, end time, and duration

#### Scenario: IDE_A timing metadata is invalid
- **WHEN** the metadata workbook contains missing or non-positive `IDE_A` segment boundaries
- **THEN** the system SHALL exclude that segment from the main analysis cohort and SHALL record the exclusion reason

### Requirement: Main IDE_A cohort membership is determined from channel coverage and metadata
The system SHALL derive a main analysis cohort that includes only patients with usable `IDE_A` assets, valid segment metadata, and EEG coverage of the shared 11-channel montage after channel-name normalization.

#### Scenario: Patient covers the shared 11-channel montage
- **WHEN** a patient's `IDE_A` EEG contains the shared frontal, central, parietal, and occipital channels after normalization
- **THEN** the patient SHALL be included in the main `IDE_A` cohort

#### Scenario: Patient lacks required EEG coverage
- **WHEN** a patient's `IDE_A` EEG is missing one or more channels from the shared 11-channel montage
- **THEN** the patient SHALL be excluded from the main cohort and the missing channels SHALL be recorded in cohort metadata
