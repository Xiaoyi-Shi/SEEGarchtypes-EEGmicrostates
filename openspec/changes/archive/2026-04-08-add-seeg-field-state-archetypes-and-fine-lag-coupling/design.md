## Context

The accepted SEEG field-state branch already derives subject-level SEEG global-field states from bipolar peak maps, labels them continuously, and measures EEG-SEEG coupling at coarse lag resolution. That branch establishes two useful facts: subject-level SEEG field states are recoverable, and EEG microstate versus SEEG field-state coupling peaks at nominal zero lag. It does not yet answer the next research questions: whether subject-level field states can be aligned into shared group archetypes, whether the near-zero synchronization peak remains centered when examined at native sample resolution, and whether switching analyses should be reframed from SEEG transitions toward EEG transitions.

The codebase already contains the main building blocks for this next step: subject-level field-state artifacts in `field_state.py`, staged EEG labels and GFP traces, and patient-first exploratory statistics in `pipelines.py`. The main constraints are subject-specific electrode coverage, polarity-invariant template matching, and the shared `250 Hz` analysis grid, which implies a native `4 ms` time step.

## Goals / Non-Goals

**Goals:**
- Add a common-space group-archetype layer above subject-level SEEG field states.
- Characterize EEG-SEEG field-state synchrony around zero lag at native `4 ms` resolution rather than only at coarse `100 ms` steps.
- Reframe switching analyses so the primary mechanistic branch asks whether SEEG field-state transitions precede or accompany EEG microstate switching.
- Preserve patient-first statistics, staged cache reuse, and exploratory report export.

**Non-Goals:**
- Do not replace the subject-level field-state discovery workflow or the existing coarse-lag summaries.
- Do not claim causal direction from lag or transition asymmetry alone.
- Do not require a universal electrode-space template shared directly across subjects.
- Do not make fine-lag or archetype analyses part of the main activity/connectivity workflow.

## Decisions

### Decision: Group commonality will be defined in a shared brain-space representation, not direct electrode space
Subject-level field templates will be projected into a common-space regional/network representation before cross-subject matching. The primary group-comparison space will be `Yeo17`, with `AAL3` reserved for descriptive follow-up views rather than the primary matching space.

Why:
- Direct electrode-space matching is not defensible across subjects with different coverage.
- `Yeo17` offers a coarser, more stable shared space for cross-subject archetype discovery.
- `AAL3` remains useful for interpretation after archetypes are established.

Alternatives considered:
- Direct bipolar-channel matching across subjects: rejected because channel identity is not shared.
- `AAL3` as the primary group space: rejected because missing coverage is heavier and matching is less stable.

### Decision: Archetype construction will use sign orientation plus subject-state matching before group summaries
Subject-level field templates will first be sign-oriented consistently in the common-space representation, then matched into group archetypes using similarity-based assignment rather than raw discovery order.

Why:
- Subject-level field-state labels are not semantically aligned across patients.
- Existing field-state derivation is polarity-invariant, so sign orientation must be resolved before interpretable group summaries can be produced.

Alternatives considered:
- Treat discovery order as a shared label: rejected because subject-level labels are arbitrary.
- Ignore sign orientation and summarize absolute loadings only: rejected because it weakens interpretable “positive/negative loading” group patterns.

### Decision: Fine-lag synchrony will be measured at native `4 ms` resolution
Near-zero synchronization will be examined in a narrow lag window sampled directly on the shared `250 Hz` grid, and both analysis resolution and reporting resolution will be `4 ms`.

Why:
- The existing coarse lag grid is sufficient to show a broad zero-lag peak but not to characterize whether the peak is sharply centered at zero.
- Native-grid analysis avoids interpolation artifacts and keeps reported lag values tied to actual samples.

Alternatives considered:
- Interpolating to `5 ms`: rejected because it obscures the actual sample resolution.
- Replacing the coarse lag analysis entirely: rejected because the coarse scan still provides useful broad context.

### Decision: The primary switching question will be SEEG-led rather than EEG-led
The main transition branch will test whether SEEG field-state switching predicts or accompanies subsequent EEG microstate switching. Reverse-direction analyses may remain available as secondary diagnostics, but they will not define the primary mechanistic interpretation.

Why:
- SEEG is closer to local source activity, so a SEEG-to-EEG framing is more defensible physiologically.
- Current EEG-led field-state switching results are weak, so the branch should be reframed around the more interpretable direction.

Alternatives considered:
- Keep EEG-to-SEEG switching as the primary mechanistic analysis: rejected because it bakes in a weaker physiological assumption.
- Remove directionality and only report symmetric overlap: rejected because it loses the main mechanistic question.

### Decision: Patient-first inference and structured nulls remain mandatory
Fine-lag and SEEG-led switching branches will continue to aggregate patient-level effects and use time-structure-preserving surrogates or constrained permutations.

Why:
- Pooled sample inference would overstate evidence in dense time-series data.
- The existing exploratory framework is already organized around patient-first summaries and structured nulls.

Alternatives considered:
- Pooled sample tests: rejected because they inflate apparent significance.
- Unstructured shuffling: rejected because it destroys serial dependence.

## Risks / Trade-offs

- [Cross-subject archetypes may be unstable] -> Mitigation: use `Yeo17` as the primary common-space representation, require minimum subject support, and report assignment stability rather than assuming universal templates.
- [Sign orientation may still be ambiguous in weakly loaded states] -> Mitigation: document the orientation rule explicitly and expose subject-level assignment diagnostics.
- [Fine-lag peaks may remain broad rather than sharply centered] -> Mitigation: report peak width and subject-level peak-lag distributions, not just the maximum lag bin.
- [SEEG-led switching may still be weak after reframing] -> Mitigation: treat switching analyses as mechanistic follow-ups rather than the headline result.
- [Additional exploratory branches increase cache and report complexity] -> Mitigation: keep cache identity explicit and reuse existing staged field-state artifacts wherever possible.

## Migration Plan

1. Add common-space archetype artifacts on top of existing subject-level field-state caches without invalidating prior field-state derivation outputs.
2. Extend `lagged-field-state-coupling` to support a fine native-resolution mode while preserving the current coarse lag workflow.
3. Add a new SEEG-led switching exploratory branch and keep any reverse-direction analysis optional or clearly secondary.
4. Extend report rendering and documentation after the new cache products stabilize.

## Open Questions

- Should the archetype matching step expose both `Yeo17` and `AAL3` as public options immediately, or should `Yeo17` remain the only supported primary matching space at first?
- Should reverse-direction EEG-to-SEEG transition analyses remain user-visible or only internal for diagnostic comparison?
- What minimum subject-support threshold is appropriate for group archetype summaries when coverage is sparse in some common-space parcels?
