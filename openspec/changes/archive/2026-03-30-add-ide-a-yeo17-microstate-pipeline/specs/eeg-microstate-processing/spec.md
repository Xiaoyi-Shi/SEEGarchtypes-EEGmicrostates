## ADDED Requirements

### Requirement: IDE_A EEG is standardized to a 19-channel target layout
The system SHALL normalize eligible `IDE_A` EEG recordings to the shared 11-channel montage, attach a standard EEG montage, expand the recording to the agreed 19-channel target layout, and restore missing target channels through bad-channel interpolation.

#### Scenario: Eligible EEG recording enters preprocessing
- **WHEN** an eligible `IDE_A` EEG recording is loaded for preprocessing
- **THEN** the system SHALL output a preprocessed EEG artifact with the agreed 19-channel target layout in a fixed channel order

#### Scenario: Target channels are absent in the source recording
- **WHEN** one or more channels required by the 19-channel layout are not present in the normalized 11-channel input
- **THEN** the system SHALL add those channels as missing EEG channels, mark them as bad, and restore them using the configured interpolation workflow before applying average reference

### Requirement: Group microstate templates are fitted with pycrostates
The system SHALL fit group microstate templates on the `IDE_A` cohort by using `pycrostates` and deterministic configuration values, including a fixed cluster count and random seed.

#### Scenario: Group microstate fitting is executed
- **WHEN** the pipeline fits group microstates for the main cohort
- **THEN** it SHALL use `pycrostates` to fit the configured number of templates and SHALL persist the resulting template maps and fit metadata as a reusable model artifact

#### Scenario: Cohort recordings have unequal durations
- **WHEN** the cohort contains recordings with different lengths
- **THEN** the group fitting stage SHALL sample GFP peak maps in a way that prevents longer recordings from dominating the fitted template set

### Requirement: Continuous IDE_A samples are labeled with group microstates
The system SHALL assign each usable time point in preprocessed `IDE_A` EEG to a group microstate label and persist the resulting label sequence on the analysis time axis.

#### Scenario: Continuous labels are generated from a fitted model
- **WHEN** a preprocessed `IDE_A` EEG recording and a fitted group microstate model are available
- **THEN** the system SHALL produce a time-aligned label table containing microstate identity and label confidence metadata for that recording

#### Scenario: Transient label fragments violate the configured duration rule
- **WHEN** a labeled microstate segment is shorter than the configured minimum duration
- **THEN** the system SHALL smooth or merge the fragment according to the configured duration rule before persisting final labels
