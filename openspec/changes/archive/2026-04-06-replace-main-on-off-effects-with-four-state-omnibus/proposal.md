## Why

The main activity and connectivity stages currently reduce each EEG microstate to a `state k` versus `not state k` contrast. That design is easy to compute, but it collapses the remaining three states into a pooled background, obscures full four-state response profiles, and prevents a true omnibus test of whether a region or region pair differs across all EEG states.

The focused public workflow now needs a four-state repeated-measures analysis that can answer both questions users actually ask: whether any EEG-state effect exists at all, and which state pairs drive that effect.

## What Changes

- Replace the main activity-stage subject summaries from `on/off` mean-difference effects with per-subject four-state activity summaries for each `AAL3` region.
- Replace the main connectivity-stage subject summaries from `state/off-state` connectivity differences with per-subject four-state connectivity summaries for each `AAL3` region pair and method.
- Add group-level omnibus outputs for the main activity and connectivity stages.
- Add pairwise post-hoc outputs for the main activity and connectivity stages, scoped to the four EEG microstates.
- Update report rendering, exported table sets, and public documentation so the focused workflow reports omnibus and post-hoc results instead of `state-vs-rest` effects.
- **BREAKING**: Main activity and connectivity result tables, column semantics, and report filenames will change from `effect_mean_diff`-based `on/off` outputs to omnibus and post-hoc outputs.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `seeg-aal3-coupling-analysis`: change the focused `AAL3` activity and connectivity requirements from `state-vs-rest` effects to four-state omnibus plus post-hoc outputs.
- `analysis-cli-orchestration`: change the focused workflow reporting requirements so the existing public commands export omnibus and post-hoc result artifacts for the main activity and connectivity stages.

## Impact

- Affected code: `src/seeg_eegmicrostates/coupling/effects.py`, `src/seeg_eegmicrostates/coupling/connectivity.py`, `src/seeg_eegmicrostates/stats/group_level.py`, `src/seeg_eegmicrostates/workflows/pipelines.py`, and plotting/report helpers.
- Affected outputs: cached subject/group activity tables, cached subject/group connectivity tables, Excel exports, and heatmap/report filenames for the main workflow.
- Affected tests/docs: staged workflow tests, report-discovery tests, README workflow documentation, and the processing-flow document.
