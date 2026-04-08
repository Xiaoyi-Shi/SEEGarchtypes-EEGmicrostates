## 1. Stage subject-level SEEG field-state artifacts

- [x] 1.1 Add exploratory preprocessing that derives band-limited bipolar SEEG peak maps from cropped SEEG using per-bipolar-channel z-scoring and a predefined peak-metric family with RMS peaks as the primary method.
- [x] 1.2 Implement polarity-invariant peak-map clustering, subject-level template persistence, continuous backfitting, minimum-duration smoothing, and cache identity that separates peak metric, normalization, field-state count, and duration settings.
- [x] 1.3 Add synthetic-bipolar tests for peak extraction, sign-invariant template matching, continuous field-state label generation, and cache reuse/separation.

## 2. Add EEG-SEEG field-state coupling analyses

- [x] 2.1 Implement synchronous EEG microstate versus SEEG field-state coupling summaries with patient-first statistics and structured nulls.
- [x] 2.2 Implement lagged EEG microstate versus SEEG field-state coupling summaries that preserve explicit lag identity and reuse existing staged EEG and field-state artifacts.
- [x] 2.3 Implement transition-conditioned EEG-to-SEEG field-state switching and destination-state summaries with group aggregation and minimum-subject filtering.

## 3. Add GFP-aware field-state follow-ups

- [x] 3.1 Implement EEG GFP-aware follow-ups that model SEEG field-state switching against EEG microstate context while accounting for GFP information.
- [x] 3.2 Implement EEG transition plus GFP-controlled field-state switching follow-ups that preserve EEG `from_state` and `to_state` identity.
- [x] 3.3 Add tests covering patient-first inference, structured-null behavior, and GFP-aware field-state follow-up outputs.

## 4. Extend orchestration, CLI, and report rendering

- [x] 4.1 Extend the exploratory CLI to expose SEEG global-field-state methods and thread their settings through cache and log identity.
- [x] 4.2 Update workflow orchestration to reuse matching staged EEG labels, staged EEG GFP artifacts, and subject-level SEEG field-state artifacts across reruns without recomputing unrelated branches.
- [x] 4.3 Add report discovery and rendering for subject-level SEEG field-template panels, occupancy/transition summaries, and EEG-SEEG field-state coupling tables/figures.

## 5. Validate and document

- [x] 5.1 Update README and workflow documentation with the SEEG global-field-state branch, its primary assumptions, and its limitations around subject-level state identity.
- [x] 5.2 Add or update end-to-end tests for CLI exposure, report export, and synthetic SEEG field-state reruns.
- [x] 5.3 Validate the OpenSpec change and confirm the new exploratory branch is ready for `/opsx:apply`.
