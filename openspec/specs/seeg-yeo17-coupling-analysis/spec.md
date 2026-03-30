## ADDED Requirements

### Requirement: Bipolar SEEG channels are mapped to valid Yeo17 networks
The system SHALL assign a bipolar SEEG channel to a Yeo17 network only when both constituent contacts share the same `Schaefer_200_17net` label in the atlas metadata.

#### Scenario: Bipolar channel contacts share a network label
- **WHEN** both contacts that form a bipolar channel have the same `Schaefer_200_17net` label
- **THEN** the system SHALL mark the bipolar channel as valid for that network and include it in network-level aggregation

#### Scenario: Bipolar channel contacts are mixed or unlabeled
- **WHEN** either contact lacks a `Schaefer_200_17net` label or the two contacts belong to different network labels
- **THEN** the system SHALL exclude that bipolar channel from the primary Yeo17 coupling analysis

### Requirement: IDE_A bipolar SEEG is summarized as network-level HFA
The system SHALL compute HFA summaries from `IDE_A` bipolar SEEG recordings and aggregate valid bipolar channels into network-level time series for each patient.

#### Scenario: IDE_A bipolar SEEG is processed
- **WHEN** an eligible `IDE_A` bipolar SEEG recording is loaded
- **THEN** the system SHALL compute the configured HFA summary for each bipolar channel and persist a time-aligned bipolar HFA artifact

#### Scenario: Multiple bipolar channels map to the same network
- **WHEN** more than one valid bipolar channel is assigned to a single Yeo17 network for a patient
- **THEN** the system SHALL aggregate those channels into one network-level HFA time series and SHALL record how many bipolar channels contributed to that network

### Requirement: Microstate-network coupling effects are produced at subject and group level
The system SHALL align EEG microstate labels with network-level SEEG HFA on a shared time axis, compute subject-level `microstate x network` coupling effects, and persist group-level statistical summaries across the cohort.

#### Scenario: Subject-level coupling is computed
- **WHEN** a patient's microstate label table and network-level HFA table are both available
- **THEN** the system SHALL compute subject-level coupling effects that compare each microstate against non-matching time points for every valid network

#### Scenario: Group-level coupling is computed
- **WHEN** subject-level coupling effects are available across the cohort
- **THEN** the system SHALL produce group-level effect summaries and multiple-testing-adjusted significance outputs for each analyzed `microstate x network` combination
