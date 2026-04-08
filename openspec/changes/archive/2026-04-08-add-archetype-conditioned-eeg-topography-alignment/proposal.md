## Why

The current exploratory field-state workflow establishes subject-level SEEG field states, group archetypes, and near-zero EEG-SEEG synchrony, but it still leaves an interpretability gap: the group archetypes live in shared SEEG network space while EEG microstates live in scalp topography space. A direct cross-space correlation is not methodologically defensible, so the next step is to ask what EEG scalp maps look like when each SEEG archetype is active and whether those archetype-conditioned EEG maps preferentially resemble specific EEG microstate templates.

## What Changes

- Add an exploratory branch that derives archetype-conditioned EEG scalp topographies by aligning staged EEG sensor maps to group-matched SEEG field-state archetypes on the shared analysis time axis.
- Add patient-level and group-level summaries of spatial similarity between archetype-conditioned EEG scalp maps and staged EEG microstate templates, rather than attempting direct SEEG-to-EEG cross-space template correlation.
- Add archetype-conditioned EEG state-preference summaries, including conditional probability tables and near-zero fine-lag synchrony on the native `4 ms` grid.
- Add a secondary archetype-transition follow-up that tests whether SEEG archetype transitions are associated with EEG microstate entry or switching, without making transition effects the headline result.
- Extend exploratory CLI, cache identity, and report export so archetype-conditioned topographies, similarity matrices, and archetype-to-EEG follow-ups are reusable and report-ready.

## Capabilities

### New Capabilities
- `seeg-archetype-conditioned-eeg-topography`: derives EEG scalp-map summaries conditioned on SEEG field-state archetypes, compares those scalp maps to EEG microstate templates, and summarizes archetype-conditioned EEG state preference and near-zero synchrony.

### Modified Capabilities
- `analysis-cli-orchestration`: expose and reuse the new archetype-conditioned EEG topography branch and export its figures/tables from staged caches.
- `exploratory-cross-modal-coupling`: include archetype-conditioned EEG topography alignment and archetype-to-EEG follow-ups among the maintained exploratory analyses.
- `seeg-global-field-state-coupling`: extend the field-state exploratory layer so group archetypes can be related back to EEG topography and EEG microstate preference in a patient-first way.

## Impact

- Affected code: `src/seeg_eegmicrostates/coupling/field_state.py`, `src/seeg_eegmicrostates/eeg/`, `src/seeg_eegmicrostates/workflows/pipelines.py`, `src/seeg_eegmicrostates/viz/`, and CLI/report wiring.
- Affected outputs: new exploratory cache branches for archetype-conditioned EEG scalp maps, similarity matrices, conditional state summaries, and archetype-transition follow-ups.
- Dependencies: reuses staged EEG microstate templates, EEG labels, preprocessed EEG sensor data, and existing SEEG field-state archetype artifacts; no new external dependency is required.
