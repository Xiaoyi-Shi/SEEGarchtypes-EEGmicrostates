## Why

The current staged SEEG workflow is built around Schaefer/Yeo17 functional-network labels, but the available atlas tables already include `AAL3` anatomical labels that better match the intended analysis framing. Switching the public SEEG staging path to `AAL3` now avoids further investment in Yeo17-specific assumptions across mapping, caching, reporting, and downstream interpretation.

## What Changes

- Add a new SEEG coupling capability centered on staged `AAL3` region signals derived from valid same-region bipolar channels.
- Replace the public staged SEEG outputs used by activity and connectivity analyses so downstream effects are computed on `AAL3` regions and region pairs instead of Yeo17 networks and network pairs.
- Update the staged workflow language, cached artifact semantics, and reports to describe atlas regions/parcels rather than Yeo17 networks where the public behavior changes.
- **BREAKING**: Existing staged SEEG caches, reports, and spec language tied to Yeo17 network outputs will no longer describe the primary public workflow.

## Capabilities

### New Capabilities
- `seeg-aal3-coupling-analysis`: Stage `1-40 Hz` SEEG signals as `AAL3` region-level time series and use them for downstream EEG-state-conditioned activity and connectivity analyses.

### Modified Capabilities
- `analysis-cli-orchestration`: The public staged CLI and reports will describe atlas-region outputs rather than Yeo17-network outputs for the SEEG stages.
- `cross-modal-band-limited-microstates`: The shared staged `1-40 Hz` SEEG inputs for the focused workflow will switch from Yeo17 network signals to `AAL3` region signals.
- `seeg-yeo17-coupling-analysis`: The accepted Yeo17-centered downstream requirements will be retired from the primary public workflow and replaced by the new `AAL3`-centered staging path.

## Impact

- Affected code: `src/seeg_eegmicrostates/seeg/`, `src/seeg_eegmicrostates/workflows/`, `src/seeg_eegmicrostates/cli.py`, `src/seeg_eegmicrostates/viz/`, and tests covering SEEG mapping, connectivity, and CLI behavior.
- Affected artifacts: staged SEEG mapping/coverage/time-series caches, downstream activity/connectivity tables, and generated report labels.
- Data assumptions: the public workflow will depend on the existing `AAL3` column in each patient `Atlas.tsv`.
