## Why

The repository currently contains synchronized EEG and SEEG recordings, electrode coordinates, and segment metadata, but it does not have a reproducible analysis pipeline for testing how EEG microstates relate to deep and cortical SEEG activity. This change is needed now to turn the dataset into a structured, reusable workflow focused on the agreed primary analysis: `IDE_A` recordings, EEG microstates, SEEG network coupling in Yeo17 space, and an additional synchronized `1-40 Hz` cross-modal EEG/SEEG microstate branch.

## What Changes

- Add a cohort indexing and segmentation workflow that identifies `IDE_A` recordings with usable paired EEG, bipolar SEEG, and atlas metadata.
- Add an EEG preprocessing workflow that standardizes the shared 11-channel montage, expands recordings to a standard 19-channel target layout, and restores missing channels via standard montage attachment plus `interpolate_bads`-style interpolation.
- Add a group microstate workflow built on `pycrostates` that fits templates on `IDE_A` data and labels continuous EEG time points.
- Add a bipolar SEEG workflow that maps same-network bipolar channels into Yeo17/Schaefer 17-network labels and computes network-level HFA summaries aligned to EEG microstate labels.
- Add a parallel `1-40 Hz` branch that derives synchronized EEG and SEEG microstate sequences on a shared `IDE_A` time axis and produces cross-modal comparison summaries.
- Add subject-level and group-level coupling outputs for `microstate x network` effects, plus cached intermediate artifacts for reproducibility and reruns.

## Capabilities

### New Capabilities
- `ide-a-cohort-indexing`: identify eligible `IDE_A` EEG/SEEG recordings, segment metadata, and analysis cohort membership from repository data.
- `eeg-microstate-processing`: preprocess low-density EEG into a standardized 19-channel representation and extract group microstate labels with `pycrostates`.
- `seeg-yeo17-coupling-analysis`: map bipolar SEEG channels to valid Yeo17 networks, compute network-level HFA, and produce aligned microstate-network coupling effects.
- `cross-modal-band-limited-microstates`: derive synchronized `1-40 Hz` EEG and SEEG microstate branches and compute shared-time-axis cross-modal comparison outputs.

### Modified Capabilities
- None.

## Impact

Affected areas include the package structure under `src/seeg_eegmicrostates/`, cached analysis artifacts, and the project dependency set through the addition of `pycrostates`. The change introduces a functional analysis workflow, parquet/npz cache outputs, and analysis-facing modules for EEG preprocessing, SEEG network mapping, coupling, band-limited cross-modal microstate comparison, and statistics.
