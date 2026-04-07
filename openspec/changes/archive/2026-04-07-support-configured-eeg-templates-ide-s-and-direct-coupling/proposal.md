## Why

The accepted specs still describe an `IDE_A`-only EEG workflow that fits a new cohort template by default, but the intended operating model has shifted toward labeling against a configured or user-supplied `pycrostates` template and supporting `IDE_S` as an optional analysis state. At the same time, the current maintained downstream analyses emphasize region-wise activity and connectivity contrasts, which are not always sensitive to direct EEG-SEEG microstate coupling when the mainline results are weak or null.

This change is needed now to realign the OpenSpec contract with the intended workflow defaults, make `IDE_S` a first-class optional public mode, and add an explicit exploratory path for direct EEG-SEEG state coupling without collapsing the public pipeline back into a second co-equal mainline.

## What Changes

- Treat a configured or user-supplied EEG template `.fif` file as the default source of EEG microstate templates for the staged EEG workflow instead of fitting a new cohort template by default.
- Expand the staged workflow contract from `IDE_A`-only wording to `IDE_A` as the default analysis state with `IDE_S` as an optional supported workflow across indexing, staged caches, downstream analyses, and reports.
- Add an opt-in exploratory direct EEG-SEEG state-coupling branch that derives SEEG state sequences from reduced-space SEEG representations and computes synchronous, lagged, and transition-conditioned coupling summaries.
- Require direct-coupling exploratory analyses to use time-structure-preserving surrogate or permutation procedures so significance estimates do not rely on naive sample shuffling.
- Keep the primary public workflow centered on staged EEG labels plus staged SEEG region signals for activity and connectivity analyses; the new direct state-coupling branch must remain exploratory and opt-in.
- Update CLI help, documentation, cache/report semantics, and tests to reflect the configured-template default, supported `IDE_A`/`IDE_S` modes, and the new direct state-coupling analyses.

## Capabilities

### New Capabilities
- `direct-cross-modal-state-coupling`: Derive exploratory SEEG state sequences from reduced-space SEEG representations and quantify direct EEG-SEEG microstate coupling through synchronous, lagged, and transition-aware summaries.

### Modified Capabilities
- `analysis-cli-orchestration`: The public CLI and staged report surface will treat configured EEG templates as the default EEG input, support `IDE_S` as an optional analysis-state override, and expose the new direct state-coupling exploratory methods.
- `cross-modal-band-limited-microstates`: The shared staged `1-40 Hz` workflow contract will generalize from `IDE_A`-only wording to supported analysis states while clarifying that exploratory direct coupling may derive downstream-specific SEEG state artifacts on top of the staged EEG labels and SEEG signals.
- `eeg-microstate-processing`: The EEG stage requirements will change from fit-by-default behavior to configured-template-by-default behavior with explicit validation and failure semantics for missing or incompatible template files.
- `exploratory-cross-modal-coupling`: The exploratory analysis layer will expand to include direct EEG-SEEG state-coupling methods alongside the existing event-, window-, and transition-based region-signal analyses.
- `ide-a-cohort-indexing`: Cohort indexing and segment materialization will expand from `IDE_A`-only requirements to support the selected analysis state while preserving `IDE_A` as the default.

## Impact

- Affected code: `src/seeg_eegmicrostates/cli.py`, `src/seeg_eegmicrostates/config/schema.py`, `src/seeg_eegmicrostates/workflows/pipelines.py`, `src/seeg_eegmicrostates/eeg/*`, `src/seeg_eegmicrostates/io/*`, `src/seeg_eegmicrostates/segment/*`, `src/seeg_eegmicrostates/coupling/*`, `src/seeg_eegmicrostates/stats/*`, and related visualization/report helpers.
- Affected artifacts: EEG template cache semantics, analysis-state-specific staged caches, exploratory direct-coupling tables/figures, and user-facing logs/help text.
- Affected tests and docs: CLI parsing, config/runtime-hash behavior, indexing/segment extraction, EEG template handling, exploratory coupling outputs, and README/OpenSpec guidance.
