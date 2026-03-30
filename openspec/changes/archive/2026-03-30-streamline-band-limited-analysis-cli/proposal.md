## Why

The repository currently exposes several parallel analysis branches, including `main` EEG microstates, HFA-based SEEG coupling, band-limited cross-modal microstate overlap, and band-limited connectivity. That breadth made sense during exploration, but it no longer matches the intended scientific workflow: the project now centers on `1-40 Hz` EEG microstates with Yeo17 SEEG activity as a supplemental analysis and Yeo17 connectivity as the primary analysis.

The next change should make the public workflow reflect that focus while keeping stable intermediate caches for debugging and preserving room for future frequency bands or connectivity methods.

## What Changes

- **BREAKING** Remove public CLI exposure of the legacy `main` EEG, HFA, and cross-modal overlap branches.
- Introduce a streamlined 4-6 step CLI centered on:
  - cohort/index preparation
  - `1-40 Hz` EEG microstate state generation
  - `1-40 Hz` SEEG Yeo17 network signal generation
  - state-conditioned activity effects
  - state-conditioned connectivity effects
  - report rendering/export
- Reposition state-conditioned Yeo17 connectivity as the primary statistical output.
- Reposition state-conditioned Yeo17 activity as a supplemental output built on the same cached `1-40 Hz` intermediates.
- Keep internal cache boundaries explicit so each stage can be rerun independently for debugging.
- Preserve future extensibility by keeping frequency band and connectivity method variation in parameters/configuration rather than command proliferation.

## Capabilities

### New Capabilities
- `analysis-cli-orchestration`: Defines the public staged CLI for the focused `1-40 Hz` workflow and the cache/report boundaries between stages.

### Modified Capabilities
- `eeg-microstate-processing`: EEG microstate processing becomes a band-limited first-class stage in the streamlined public workflow rather than one branch among several public alternatives.
- `seeg-yeo17-coupling-analysis`: Yeo17 analysis shifts from HFA-first coupling toward a `1-40 Hz` state-conditioned pipeline where activity is supplemental and connectivity is primary.
- `cross-modal-band-limited-microstates`: The band-limited branch no longer centers the public workflow on EEG/SEEG microstate overlap outputs; band-limited downstream analysis is refocused on activity and connectivity products.

## Impact

- Affected code: CLI entry points, workflow orchestration, cache naming/selection, reports/tables, and tests.
- Affected user interface: command names and the supported public workflow will change.
- Affected documentation: README and synced specs must reflect the new primary/supplemental analysis hierarchy.
