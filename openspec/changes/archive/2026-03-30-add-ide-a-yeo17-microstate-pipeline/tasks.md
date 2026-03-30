## 1. Pipeline Scaffold

- [x] 1.1 Add `pycrostates` to project dependencies and create artifact/cache directories for analysis outputs
- [x] 1.2 Create the functional module layout for `io`, `qc`, `segment`, `eeg`, `seeg`, `coupling`, `stats`, `viz`, and `workflows`
- [x] 1.3 Define an immutable analysis configuration object and shared cache naming rules for IDE_A runs

## 2. Cohort Indexing

- [x] 2.1 Implement repository scanning for `IDE_A` EEG, reference SEEG, bipolar SEEG, and atlas assets
- [x] 2.2 Implement workbook loaders for `patient_info` and `annot_info` and materialize IDE_A segment metadata
- [x] 2.3 Implement main cohort filtering based on required assets, valid IDE_A timing, and shared 11-channel EEG coverage

## 3. EEG Microstate Processing

- [x] 3.1 Implement EEG channel-name normalization and shared 11-channel selection for IDE_A recordings
- [x] 3.2 Implement standard montage attachment, target 19-channel expansion, bad-channel interpolation, and cached preprocessed EEG outputs
- [x] 3.3 Implement GFP peak extraction, balanced cohort sampling, and `pycrostates` group template fitting with portable model artifacts
- [x] 3.4 Implement continuous microstate labeling, minimum-duration smoothing, and cached label tables on the analysis time axis

## 4. SEEG Yeo17 Processing

- [x] 4.1 Implement atlas loading and bipolar same-network Yeo17 mapping from `Schaefer_200_17net`
- [x] 4.2 Implement IDE_A bipolar SEEG loading, HFA computation, within-patient normalization, and cached bipolar HFA outputs
- [x] 4.3 Implement network-level HFA aggregation and per-network coverage summaries for valid same-network bipolar channels

## 5. Cross-Modal 1-40 Hz Microstates

- [x] 5.1 Implement a `1-40 Hz` EEG microstate branch with branch-specific caches and model artifacts
- [x] 5.2 Implement a `1-40 Hz` SEEG Yeo17-network microstate branch and cached state sequences on the IDE_A time axis
- [x] 5.3 Implement synchronized EEG/SEEG cross-modal microstate comparison outputs such as contingency, overlap, and lag summaries

## 6. Coupling and Statistics

- [x] 6.1 Implement time-axis alignment between EEG microstate labels and network-level HFA summaries
- [x] 6.2 Implement subject-level `microstate x network` effect calculations and cached subject effect tables
- [x] 6.3 Implement group-level permutation statistics, FDR correction, and result tables for analyzed network combinations

## 7. Validation and Reporting

- [x] 7.1 Add automated tests for cohort eligibility, IDE_A segment extraction, EEG 11-to-19 restoration, bipolar network mapping, and branch-specific cache naming
- [x] 7.2 Add workflow entry points that rerun downstream stages from cached artifacts instead of rescanning raw data every time
- [x] 7.3 Add QC/report outputs for cohort coverage, fitted microstate templates, network coverage, HFA coupling heatmaps, and `1-40 Hz` cross-modal state summaries
