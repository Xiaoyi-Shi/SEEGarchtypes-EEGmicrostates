## Why

The current SEEG field-state branch establishes subject-level SEEG global-field states and shows near-zero-lag EEG coupling, but it stops short of the next research questions: whether those field states share common group archetypes, whether EEG-SEEG synchrony remains centered at fine native time resolution, and whether switching analyses should be framed from SEEG transitions toward EEG transitions rather than the reverse. These questions now matter because the existing exploratory results already support subject-level field-state discovery and zero-lag coupling, but not a strong EEG-led switching story.

## What Changes

- Add a group-level SEEG field-state archetype branch that projects subject-level field templates into a shared brain-space representation, orients template signs consistently, and matches subject-level states into reusable group archetypes.
- Add fine-lag EEG microstate versus SEEG field-state coupling analyses that scan a narrow near-zero window at native `4 ms` resolution and report peak lag, lag-curve width, and subject-level peak-lag summaries.
- Reframe SEEG-EEG switching follow-ups so the primary mechanistic question becomes whether SEEG field-state switches precede or accompany EEG microstate switching, while keeping any reverse-direction analyses optional or secondary.
- Extend exploratory report export so archetype summaries, fine-lag curves, and SEEG-to-EEG switching outputs are rendered alongside the existing subject-level field-state artifacts.

## Capabilities

### New Capabilities
- `seeg-global-field-state-archetypes`: Group-level matching, sign orientation, and shared archetype summaries for subject-level SEEG global-field states in a common-space representation.

### Modified Capabilities
- `analysis-cli-orchestration`: Exploratory orchestration and report export must expose and reuse the new archetype, fine-lag, and SEEG-to-EEG switching branches.
- `exploratory-cross-modal-coupling`: Exploratory coupling must include fine native-resolution lag analyses and SEEG-led switching follow-ups alongside the existing field-state methods.
- `seeg-global-field-state-coupling`: The field-state contract must extend from subject-level state discovery to fine `4 ms` synchrony characterization and SEEG-to-EEG switching analyses.

## Impact

- Affected code will center on [field_state.py](F:/uv_env/SEEG-EEGmicrostates/src/seeg_eegmicrostates/coupling/field_state.py), [pipelines.py](F:/uv_env/SEEG-EEGmicrostates/src/seeg_eegmicrostates/workflows/pipelines.py), [cli.py](F:/uv_env/SEEG-EEGmicrostates/src/seeg_eegmicrostates/cli.py), and report rendering in [heatmaps.py](F:/uv_env/SEEG-EEGmicrostates/src/seeg_eegmicrostates/viz/heatmaps.py).
- New exploratory outputs will add archetype-level tables/figures and finer lag-grid summaries under `artifacts/cache/` and `artifacts/runs/<run-id>/reports/`.
- No external dependency shift is expected; the main impact is on exploratory cache identity, report inventory, and interpretation of field-state coupling results.
