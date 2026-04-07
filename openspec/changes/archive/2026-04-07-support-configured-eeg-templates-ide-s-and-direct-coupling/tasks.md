## 1. Align workflow contracts

- [x] 1.1 Update configuration, CLI help, and user-facing documentation to treat configured EEG templates as the default EEG-stage input while preserving `--template-fif` override behavior.
- [x] 1.2 Thread the selected `analysis_state` contract through indexing, segment materialization, cache identity, logs, and reports so `IDE_A` remains the default and `IDE_S` becomes a supported optional workflow.

## 2. Update staged orchestration

- [x] 2.1 Adjust EEG-stage orchestration to resolve template precedence (`--template-fif` override, then configured default template) and fail clearly when no usable template file is available.
- [x] 2.2 Extend exploratory orchestration and report discovery so the maintained region-signal methods and the new direct EEG-SEEG state-coupling methods share the same staged upstream reuse model.
- [x] 2.3 Ensure runtime hashing and branch-specific cache/report stems remain distinct across analysis states, direct-coupling methods, reduced-space backends, and lag settings.

## 3. Add direct EEG-SEEG state-coupling analyses

- [x] 3.1 Implement reduced-space SEEG state derivation and branch-specific staged artifacts for exploratory direct coupling.
- [x] 3.2 Implement synchronous direct EEG-SEEG state-coupling summaries with patient-level metrics and structured null models.
- [x] 3.3 Implement lagged direct EEG-SEEG state-coupling summaries with lag-specific outputs and cache identities.
- [x] 3.4 Implement transition-conditioned direct EEG-SEEG state-coupling summaries and group-level aggregation from patient-first metrics.

## 4. Validate and document the change

- [x] 4.1 Add or update tests for configured-template defaults, missing-template failures, and analysis-state-specific indexing/staging behavior.
- [x] 4.2 Add or update tests for direct-coupling cache reuse, synchronous/lagged/transition summary outputs, and minimum-subject filtering.
- [x] 4.3 Update README and workflow guidance with examples for configured-template defaults, `IDE_S` usage, and direct EEG-SEEG state-coupling exploratory analyses.
