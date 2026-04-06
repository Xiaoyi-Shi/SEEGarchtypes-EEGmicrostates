## Why

The current public pipeline can stage EEG microstate labels and SEEG regional signals, but its downstream coupling outputs are limited to state-conditioned activity and connectivity contrasts. The next useful step is to add exploratory cross-modal coupling analyses that test event-locked, state-alignment, and transition-based relationships between EEG microstates and SEEG dynamics without replacing the focused default workflow.

## What Changes

- Add a new exploratory coupling capability that supports five optional analysis families on top of staged EEG labels and staged SEEG regional signals: EEG event-triggered SEEG activity, EEG-SEEG microstate alignment, EEG event-triggered SEEG connectivity, windowed occupancy/dwell coupling, and EEG state-transition coupling.
- Add reusable staged artifacts for exploratory subject-level summaries, group-level summary tables, and figures so each method can be rerun independently without recomputing upstream EEG or SEEG stages.
- Extend the orchestration layer so these exploratory analyses can be run explicitly without displacing the existing focused `build-index -> EEG -> SEEG -> activity/connectivity -> reports` workflow.
- Update the cross-modal capability so exploratory outputs once again include EEG/SEEG state correspondence, but now as optional analyses rather than the primary public workflow target.

## Capabilities

### New Capabilities
- `exploratory-cross-modal-coupling`: Optional cross-modal coupling analyses built on staged EEG microstate labels and staged SEEG regional signals, including event-locked, alignment-based, windowed, and transition-based summaries.

### Modified Capabilities
- `analysis-cli-orchestration`: The orchestration layer will expose explicit entry points for exploratory coupling analyses while preserving the current focused default workflow.
- `cross-modal-band-limited-microstates`: Cross-modal outputs will once again include EEG/SEEG state correspondence, lagged overlap, and related exploratory summaries as optional analyses rather than required branch products.

## Impact

- Affected code: `src/seeg_eegmicrostates/workflows/`, `src/seeg_eegmicrostates/coupling/`, `src/seeg_eegmicrostates/seeg/`, `src/seeg_eegmicrostates/stats/`, `src/seeg_eegmicrostates/viz/`, and CLI/report tests.
- Affected artifacts: new exploratory caches under `artifacts/cache/`, additional report figures/tables, and method-specific summary outputs.
- Workflow dependency: this proposal assumes the staged SEEG baseline provides regional signals rather than the older Yeo17-only framing, so it should be implemented on top of the current AAL3-directed pipeline work.
