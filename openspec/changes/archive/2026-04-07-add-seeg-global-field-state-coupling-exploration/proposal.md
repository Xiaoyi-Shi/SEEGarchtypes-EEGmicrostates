## Why

Current exploratory results suggest two partially separated phenomena: a strong shared EEG GFP versus SEEG global-amplitude drive, and a weaker but potentially meaningful EEG-state transition timing effect. The workflow still lacks a middle layer that can test whether SEEG also expresses a small set of recurrent peak-centered spatial configurations in electrode space, and whether those subject-level SEEG field states relate to EEG microstates beyond global amplitude alone.

## What Changes

- Add a new exploratory branch that derives subject-level SEEG global-field states from band-limited bipolar SEEG peak maps rather than only from region/network averages.
- Define a polarity-invariant, patient-level SEEG peak-topography workflow using per-bipolar-channel normalization, SEEG global-metric peak detection, peak-map clustering, and continuous backfitting to produce SEEG field-state sequences.
- Add EEG-SEEG coupling summaries that relate subject-level SEEG field states to EEG microstates through synchronous, lagged, and transition-conditioned analyses.
- Add follow-up summaries that test whether SEEG field-state switching remains associated with EEG microstates or EEG transitions after accounting for EEG GFP context.
- Export exploratory figures/tables that summarize SEEG field templates, SEEG field-state occupancy/transition summaries, and EEG-SEEG field-state coupling outputs.

## Capabilities

### New Capabilities
- `seeg-global-field-state-coupling`: Subject-level SEEG peak-topography state derivation and coupling analyses against EEG microstates.

### Modified Capabilities
- `analysis-cli-orchestration`: Extend the exploratory CLI, staged artifact reuse, and report/export contract to include SEEG global-field-state analyses.
- `exploratory-cross-modal-coupling`: Extend exploratory behavior to expose SEEG electrode-space field-state derivation and EEG coupling summaries.

## Impact

- Affected code: SEEG exploratory preprocessing, coupling/statistics modules, workflow orchestration, CLI parsing, and report rendering.
- Affected data flow: new exploratory artifacts will be derived from cropped bipolar SEEG before region/network averaging, then related back to staged EEG labels and GFP artifacts.
- Affected interpretation: the branch will explicitly distinguish shared global amplitude effects from subject-level SEEG spatial state structure rather than treating all EEG-SEEG coupling as region-average or reduced-space effects.
