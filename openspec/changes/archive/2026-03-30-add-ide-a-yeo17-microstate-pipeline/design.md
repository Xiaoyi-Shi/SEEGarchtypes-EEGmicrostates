## Context

The repository already contains synchronized EEG and SEEG recordings in `datas/data_01_seeg`, atlas tables with Schaefer/Yeo labels, and spreadsheet metadata describing patient eligibility and analysis windows. The codebase does not yet provide a reproducible pipeline that turns those inputs into a cohort definition, standardized EEG microstate labels, SEEG network summaries, and group-level coupling statistics.

The agreed primary analysis is narrow by design: use `IDE_A` recordings only, retain patients whose EEG covers the shared 11-channel montage, expand EEG into a standard 19-channel representation, fit group microstates with `pycrostates`, and analyze SEEG HFA at the Yeo17 network level. The change now also includes a parallel `1-40 Hz` cross-modal branch that derives synchronized EEG and SEEG microstate sequences on the same `IDE_A` time axis. The dataset is large, low-density on the EEG side, and only partially covered by cortical atlas labels on the SEEG side, so the implementation must make those constraints explicit rather than hide them.

## Goals / Non-Goals

**Goals:**
- Build a reproducible cohort and segment indexing workflow for `IDE_A` recordings.
- Standardize low-density EEG into a consistent 19-channel representation using a documented interpolation strategy.
- Fit and cache group microstate templates with `pycrostates`, then label continuous EEG time points.
- Map bipolar SEEG channels to valid Yeo17 networks, compute network-level HFA, and align it to microstate labels.
- Add a synchronized `1-40 Hz` EEG/SEEG microstate branch that produces cross-modal state sequences and summary comparison metrics.
- Keep the pipeline functional and cache-driven so individual steps can be rerun without recomputing the entire workflow.

**Non-Goals:**
- Implement `IDE_S`, pre-ictal, ictal, or post-ictal analyses in this change.
- Introduce deep-ROI coupling analyses for hippocampus, amygdala, or parahippocampal structures in the primary pipeline.
- Build a notebook-first workflow that mixes I/O, stateful processing, and analysis logic in the same code path.
- Produce publication-ready statistical conclusions beyond the cached outputs and report scaffolding needed to support them.

## Decisions

### 1. Limit the main cohort to `IDE_A` recordings with standardized 11-channel EEG coverage
The primary cohort SHALL include only recordings with paired `IDE_A` EEG, paired bipolar SEEG, atlas metadata, and shared 11-channel EEG coverage after name normalization. This keeps the first implementation consistent with the agreed scientific question and avoids conflating awake resting-state analysis with sleep or seizure-state heterogeneity.

Alternatives considered:
- Include all paired EEG patients and down-project to the minimal shared channel set. Rejected because it weakens scalp topology further.
- Mix `IDE_A` and `IDE_S` in a single first-pass workflow. Rejected because it changes the biological question and complicates validation.

### 2. Restore a standard 19-channel EEG layout by attaching a standard montage and interpolating simulated missing channels
The EEG pipeline SHALL normalize recordings to the shared 11-channel set, attach a standard `10-20` montage, add the missing channels required by the target 19-channel layout as missing EEG channels, mark them bad, and restore them with `interpolate_bads`-style interpolation. Average reference SHALL be applied after the 19-channel layout has been restored.

Alternatives considered:
- Keep the analysis entirely in 11 channels. Rejected as the primary path because the target workflow explicitly standardizes to 19 channels for group microstate fitting.
- Use a different interpolation route such as direct montage-to-montage projection. Deferred behind an abstraction boundary; the initial implementation will use the agreed `set_montage` plus bad-channel interpolation strategy.

### 3. Use `pycrostates` as the microstate engine, but persist only portable model artifacts
Microstate fitting SHALL use `pycrostates` and its modified k-means workflow rather than a custom implementation. The code SHALL wrap `pycrostates` in boundary functions and persist model artifacts as portable arrays and metadata instead of passing live estimator objects throughout the pipeline.

Alternatives considered:
- Implement clustering from scratch. Rejected because it increases validation burden without adding scientific value.
- Persist raw estimator objects directly. Rejected because it couples cache compatibility to internal library state.

### 4. Use only same-network bipolar SEEG channels for Yeo17 coupling
Bipolar channels SHALL be assigned to a Yeo17 network only when both constituent contacts share the same `Schaefer_200_17net` label. Mixed-network or unlabeled bipolar channels SHALL be excluded from the primary network-level coupling analysis.

Alternatives considered:
- Assign bipolar channels by a single contact. Rejected because it weakens interpretability for bipolar derivations.
- Use Yeo7 as the primary network space. Rejected because the agreed analysis target is Yeo17 and the atlas already exposes Schaefer 17-network labels.

### 5. Add a parallel `1-40 Hz` cross-modal microstate branch on the same IDE_A time axis
The pipeline SHALL preserve the original HFA coupling branch and add a second branch that filters EEG and SEEG-derived network signals in `1-40 Hz`, derives EEG microstates and SEEG microstates from those band-limited representations, and persists cross-modal comparison outputs on a shared `IDE_A` time axis. SEEG microstates SHALL be defined in Yeo17 network space rather than raw contact space so the state dimension remains comparable across patients.

Alternatives considered:
- Reuse the HFA branch as a proxy for low-frequency cross-modal states. Rejected because it tests a different signal regime.
- Derive SEEG microstates directly from raw contact-space data. Rejected because contact coverage is inconsistent across patients and does not yield a stable group state space.

### 6. Keep the codebase function-oriented with explicit caches and immutable configuration
Analysis logic SHALL be expressed as small functions with explicit inputs and outputs. Stateful `MNE` and `pycrostates` objects SHALL remain localized to I/O and wrapper boundaries. Each major step SHALL materialize stable parquet, fif, or npz artifacts so parameter changes only require rerunning downstream steps.

Alternatives considered:
- A single notebook or script pipeline. Rejected because it is hard to test, rerun, and migrate.
- Object-heavy orchestration classes. Rejected because the requested design emphasizes portability and local reasoning over mutable runtime state.

### 7. Compute statistics at the subject level before group aggregation
The coupling workflow SHALL compute subject-level `microstate x network` effect summaries first and only then run group-level inference. This avoids treating densely sampled time points as independent observations and provides a cleaner path for permutation-based group statistics.

Alternatives considered:
- Fit statistics directly on all aligned time points. Rejected because it inflates effective sample size and obscures subject-level heterogeneity.

## Risks / Trade-offs

- [Interpolated 19-channel EEG may overstate spatial detail] -> Preserve the original 11-channel inputs, record which channels were restored, and plan a sensitivity analysis outside this change.
- [Yeo17 labels cover only part of the SEEG contact set] -> Exclude unlabeled and mixed-network bipolar channels explicitly and report per-network coverage tables.
- [Large FIF files can make reruns slow and memory-heavy] -> Cache cohort tables, preprocessed EEG, HFA summaries, and aligned outputs at each major boundary.
- [Library wrappers can leak stateful behavior back into the pipeline] -> Keep `Raw` and `ModKMeans` objects inside boundary functions and serialize only stable data artifacts.
- [The additional `1-40 Hz` branch can multiply cache volume and parameter complexity] -> Use explicit branch identifiers in file names and configs so the HFA and band-limited outputs remain separable.
- [Primary pipeline may be misapplied to seizure or sleep data later] -> Encode `IDE_A` scope in cohort filters, file naming, and cache metadata.

## Migration Plan

1. Add `pycrostates` to project dependencies and create the functional module layout under `src/seeg_eegmicrostates/`.
2. Introduce artifact directories for caches, logs, and reports without altering raw data locations.
3. Implement indexing and cohort selection first so downstream steps run only on a validated `IDE_A` cohort.
4. Implement EEG, SEEG, HFA coupling, and `1-40 Hz` cross-modal stages behind stable file artifacts to support incremental reruns.
5. Roll back by removing the new dependency and pipeline modules; no raw data migration is required because the workflow is additive.

## Open Questions

- The exact HFA band edges need to be frozen at implementation time, although `70-150 Hz` is the current default.
- The minimum per-network coverage threshold for group inference should be finalized when coverage reports are available from the implemented mapper.
- The exact comparison metrics for cross-modal state alignment should be frozen at implementation time, although contingency, overlap, and lag summaries are the current default.
