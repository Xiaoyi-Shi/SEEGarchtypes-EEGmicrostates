## Why

The repository still carries legacy HFA, SEEG-microstate overlap, and `network`-named code paths that no longer match the public `AAL3` region workflow. Those remnants are now creating ambiguity in the CLI, the internal APIs, and the specs, while the active downstream analyses already rely on staged EEG microstate labels plus staged SEEG region signals.

## What Changes

- Remove the internal HFA staging and HFA coupling branches from the maintained workflow.
- Remove the old band-limited SEEG-microstate cross-modal branch as a maintained analysis path.
- **BREAKING** Rename the public SEEG staging command from `run-seeg-networks` to `run-seeg-regions`.
- Replace leftover `network`-oriented command, workflow, cache, helper, and plotting names with `region`-oriented naming where the public workflow is explicitly `AAL3`.
- Remove exploratory state-alignment support if it still depends on fitting a separate SEEG microstate branch rather than reusing the staged EEG microstate labels used by the maintained downstream analyses.
- Keep the atlas/parcellation configuration abstraction in place so a future change can switch the staging backend back to `Yeo17` or another parcellation without reintroducing misleading `network` compatibility layers into the current public workflow.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `analysis-cli-orchestration`: rename the public SEEG staging command, retire legacy HFA/cross-modal branch expectations, and keep the public CLI centered on EEG labels plus SEEG region staging.
- `cross-modal-band-limited-microstates`: remove the maintained SEEG-microstate overlap branch and clarify that downstream analyses consume staged EEG labels and staged SEEG region signals.
- `exploratory-cross-modal-coupling`: remove exploratory methods that depend on the retired SEEG-microstate cross-modal branch and keep only exploratory analyses that reuse staged EEG labels plus staged SEEG region signals.
- `seeg-aal3-coupling-analysis`: standardize public AAL3 staging and downstream outputs on region-oriented naming rather than legacy network compatibility names.

## Impact

- Affected code: `src/seeg_eegmicrostates/cli.py`, `src/seeg_eegmicrostates/workflows/pipelines.py`, `src/seeg_eegmicrostates/seeg/*`, `src/seeg_eegmicrostates/coupling/*`, `src/seeg_eegmicrostates/qc/*`, `src/seeg_eegmicrostates/viz/*`, and related tests.
- Affected artifacts: public command names, cache/report stems, helper names, exploratory method availability, and documentation.
- Compatibility: existing users of `run-seeg-networks`, HFA internals, or SEEG-microstate overlap internals will need to migrate to the region-oriented workflow.
