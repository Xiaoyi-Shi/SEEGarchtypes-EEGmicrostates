## 1. Archetype-Conditioned EEG Maps

- [x] 1.1 Align staged EEG sensor-space samples to matched SEEG field-state archetype labels on the shared analysis axis
- [x] 1.2 Derive and persist patient-level archetype-conditioned EEG scalp maps with per-archetype sample-support diagnostics
- [x] 1.3 Aggregate patient-level conditioned EEG maps into report-ready group scalp-map summaries

## 2. Template Similarity And EEG Preference

- [x] 2.1 Compute patient-level and group-level spatial similarity between archetype-conditioned EEG scalp maps and staged EEG microstate templates
- [x] 2.2 Export archetype-by-EEG-state conditional probability or equivalent preference summaries at zero lag
- [x] 2.3 Preserve ambiguous or distributed archetype-to-microstate relationships in report outputs without forcing one-to-one assignments

## 3. Fine-Lag And SEEG-Led Follow-Ups

- [x] 3.1 Add native `4 ms` near-zero lag archetype-to-EEG microstate synchrony analysis
- [x] 3.2 Add secondary SEEG archetype-transition to EEG state-entry or switching follow-up analysis
- [x] 3.3 Keep fine-lag and transition inference patient-first with temporal-structure-preserving null procedures

## 4. CLI, Cache, And Reports

- [x] 4.1 Expose archetype-conditioned EEG topography analyses through exploratory CLI/config and runtime hashing
- [x] 4.2 Reuse staged EEG, field-state, and archetype artifacts without recomputing reusable upstream caches
- [x] 4.3 Render conditioned EEG scalp-map panels, similarity matrices, state-preference tables, and SEEG-led transition summaries in reports

## 5. Validation And Documentation

- [x] 5.1 Add or extend tests for conditioned EEG map derivation, template similarity, fine-lag synchrony, and SEEG-led transition follow-ups
- [x] 5.2 Update README and workflow documentation for the new exploratory branch and its interpretation boundaries
- [x] 5.3 Run `uv run pytest -q` and `openspec validate \"add-archetype-conditioned-eeg-topography-alignment\"`
