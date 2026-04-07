## Why

The current Yeo17 results suggest that cross-modal signal may be easier to detect in shared global dynamics and state-transition timing than in static region/network omnibus effects. Right now the workflow jumps directly from EEG microstate labels to SEEG coupling analyses without first testing whether EEG global field power (GFP) and SEEG global amplitude/energy share a common drive, so positive microstate findings remain hard to interpret.

## What Changes

- Add an exploratory GFP-informed cross-modal analysis branch that quantifies the relationship between continuous EEG GFP and SEEG global metrics derived from staged Yeo17 network signals.
- Support multiple SEEG global-metric definitions for the same staged inputs, including equal-weight RMS, envelope-based RMS, and spatial-dispersion style summaries, so the analysis can compare robustness across reasonable formulations.
- Add lagged and peak-centered EEG GFP versus SEEG global analyses that use symmetric windows rather than assuming EEG leads or lags SEEG a priori.
- Add exploratory follow-up analyses that test whether EEG microstate or transition effects on SEEG remain after accounting for EEG GFP, so amplitude-driven coupling can be separated from state-specific coupling.
- Export reusable tables and figures for global coupling curves, peak-centered trajectories, and GFP-controlled state/transition summaries.

## Capabilities

### New Capabilities
- `gfp-informed-global-cross-modal-coupling`: exploratory EEG GFP versus SEEG global-metric analyses, including multiple SEEG global definitions, lag scans, symmetric peak-centered summaries, and GFP-controlled follow-up models.

### Modified Capabilities
- `analysis-cli-orchestration`: extend the exploratory command surface and staged report discovery to include GFP/global-coupling analyses and GFP-controlled state follow-ups.
- `eeg-microstate-processing`: persist reusable EEG GFP time series and GFP peak artifacts from the staged EEG branch for downstream exploratory reuse.
- `exploratory-cross-modal-coupling`: expose GFP/global exploratory analyses alongside existing region-signal and direct-state methods, including GFP-controlled microstate and transition follow-ups.

## Impact

- Affected code will center on the staged EEG outputs, exploratory coupling orchestration, reporting, and group-level statistics over patient-first global metrics.
- New cached artifacts will likely include EEG GFP traces, GFP peak/event tables, SEEG global-metric traces, lagged global-coupling summaries, and GFP-controlled state/transition summary tables.
- The exploratory CLI and reports will gain new method names and outputs, but the main staged activity/connectivity workflow remains unchanged.
