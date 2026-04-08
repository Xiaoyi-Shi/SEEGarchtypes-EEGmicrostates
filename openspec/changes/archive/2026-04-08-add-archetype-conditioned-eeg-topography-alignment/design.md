## Context

The exploratory SEEG field-state workflow now reaches three layers that matter for interpretation: subject-level field states in bipolar space, group archetypes in a shared `Yeo17` representation, and near-zero EEG-SEEG synchrony on the shared `250 Hz` time axis. What it does not yet provide is a defensible bridge back to EEG scalp topography. Group archetypes are expressed as SEEG network loadings, while EEG microstates are expressed as scalp maps, so a direct archetype-to-microstate spatial correlation is not methodologically valid. The design therefore needs an intermediate object: EEG scalp maps conditioned on archetype activity.

The codebase already has the staged ingredients for this branch: reusable EEG labels, staged EEG `pycrostates` templates, per-patient preprocessed EEG FIF files on the restored `19`-channel montage, subject-level SEEG field-state labels, and group archetype assignments. The main constraints are the shared `250 Hz` grid, the need to stay patient-first, and the need to keep archetype-conditioned EEG maps interpretable as scalp patterns rather than raw amplitude averages.

## Goals / Non-Goals

**Goals:**
- Derive patient-level and group-level EEG scalp maps conditioned on SEEG field-state archetype identity.
- Compare those archetype-conditioned EEG maps against staged EEG microstate templates using a polarity-tolerant spatial similarity metric.
- Summarize archetype-conditioned EEG state preference and near-zero archetype-to-microstate synchrony on the native `4 ms` grid.
- Add a secondary SEEG archetype-transition to EEG state-entry/switching follow-up without making transition effects the headline interpretation.
- Preserve staged cache reuse, patient-first inference, and exploratory report export.

**Non-Goals:**
- Do not perform direct SEEG-network-to-EEG-scalp spatial correlation as if the two lived in the same feature space.
- Do not introduce source reconstruction, inverse modeling, or new anatomical forward models.
- Do not move this branch into the main activity/connectivity workflow.
- Do not require a universal electrode-space SEEG template shared across subjects.

## Decisions

### Decision: The primary object will be archetype-conditioned EEG scalp maps, not direct cross-space archetype-template correlation
For each patient and each matched SEEG archetype, the workflow will average aligned EEG sensor topographies in EEG space after per-sample topographic normalization. Group summaries will be built from those patient-level maps.

Why:
- SEEG archetypes and EEG microstate templates are not defined in the same coordinate system.
- Conditioning EEG scalp maps on archetype activity creates a valid common comparison space for downstream similarity analysis.
- Per-sample topographic normalization reduces the risk that global amplitude dominates the resulting maps.

Alternatives considered:
- Directly correlating `Yeo17` archetype loadings with scalp topographies: rejected because the spaces are not commensurate.
- Averaging raw EEG voltages without per-sample normalization: rejected because shared amplitude drive would dominate pattern structure.

### Decision: Spatial similarity to EEG microstate templates will be sign-tolerant and template-based
The branch will compare archetype-conditioned EEG maps against the staged EEG microstate templates using polarity-tolerant spatial correlation in the restored shared EEG montage.

Why:
- EEG microstate comparison is fundamentally a scalp-pattern comparison problem.
- Polarity-tolerant matching is more consistent with microstate-style topographic similarity than strict signed correlation.
- Reusing the staged microstate templates avoids introducing a second competing EEG state representation.

Alternatives considered:
- Comparing only to discrete EEG labels and ignoring scalp-map similarity: rejected because it leaves the topographic interpretation gap unresolved.
- Using strict signed correlation: rejected because it is more brittle for scalp-map comparison and less aligned with microstate-style matching.

### Decision: Patient-level maps and statistics will be computed before group summaries
Archetype-conditioned EEG maps, template similarities, conditional probabilities, and fine-lag summaries will be computed within each patient first, then aggregated across patients.

Why:
- The existing exploratory framework is patient-first.
- Pooled time samples would overstate certainty because each patient contributes dense time-series data.
- Patient-first summaries keep the resulting group effects comparable to the rest of the codebase.

Alternatives considered:
- Pooling all aligned samples across patients: rejected because it inflates significance and ignores between-subject heterogeneity.

### Decision: Fine-lag synchrony will remain native-grid and centered on the archetype-conditioned label sequence
The branch will preserve the existing `250 Hz` shared axis and characterize archetype-conditioned EEG synchrony on the native `4 ms` grid near zero lag.

Why:
- The current field-state fine-lag branch already established the value of native-grid synchrony summaries.
- Archetype-conditioned EEG preference should be evaluated on the actual shared sample grid rather than interpolated lags.

Alternatives considered:
- Reusing only coarse lag bins: rejected because the new branch is explicitly about resolving near-zero timing around interpretable archetypes.

### Decision: Archetype-transition to EEG entry/switching will be secondary
The transition follow-up will ask whether SEEG archetype transitions are associated with EEG state entry or switching, but it will be reported as a secondary mechanistic branch rather than the main result.

Why:
- The strongest current evidence is for synchrony and interpretable conditioned maps, not for transition gating.
- Transition-conditioned results are likely weaker and more multiple-comparison heavy.

Alternatives considered:
- Making transition effects the primary branch: rejected because current evidence does not justify that emphasis.

## Risks / Trade-offs

- [Archetype-conditioned EEG maps may be blurred by low-information samples] -> Mitigation: normalize each EEG topography before averaging and persist patient-level sample counts for each archetype.
- [Spatial similarity may remain weak even if label synchrony exists] -> Mitigation: report similarity matrices and conditional state probabilities separately rather than forcing a one-to-one template mapping.
- [Group archetypes may be too coarse for scalp interpretation] -> Mitigation: keep patient-level conditioned maps available and treat group archetypes as shared summaries, not perfect universal states.
- [Transition follow-ups may be noisy after multiple-comparison correction] -> Mitigation: position transition results as secondary and preserve destination-state detail for exploratory follow-up rather than collapsing to a binary headline.
- [Additional EEG-space cache products increase report complexity] -> Mitigation: keep branch identity explicit and reuse existing staged EEG and archetype artifacts.

## Migration Plan

1. Add reusable patient-level archetype-conditioned EEG map artifacts on top of the existing staged EEG and SEEG archetype caches.
2. Add group-level scalp-map summaries, template-similarity outputs, and conditional-probability summaries without changing the existing field-state derivation workflow.
3. Extend exploratory orchestration and report rendering to expose the new topography-alignment branch and secondary archetype-transition follow-ups.
4. Add tests and documentation once the new cache products stabilize.

## Open Questions

- Should the primary conditioned EEG map average all archetype-active samples, or should a GFP-restricted sensitivity analysis also be exposed publicly from the start?
- Should archetype-conditioned EEG preference be summarized only against discrete EEG state labels, or should the branch also export continuous template-expression scores if those are added later?
- How much of the transition follow-up should be public in the first pass: only `any-switch`, or full destination-state summaries by default?
