## Context

The current repository supports two exploratory views of EEG-SEEG coupling that stop short of an electrode-space SEEG state model. One view operates on staged AAL3/Yeo17 region or network averages. The other view derives reduced-space SEEG states from staged region/network signals and tests direct alignment against EEG microstates. Recent GFP-informed analyses showed that EEG GFP and SEEG global magnitude are strongly coupled, while GFP-controlled global microstate effects are weak. Recent direct-state analyses, however, suggested that transition timing may still contain information beyond a shared global drive.

That combination motivates a missing intermediate layer: subject-level SEEG global-field states derived from bipolar electrode-space peak maps. This branch must sit upstream of region/network averaging, because once bipolar channels are collapsed into region means the workflow no longer has access to the instantaneous cross-electrode spatial configuration needed for a microstate-like analysis. At the same time, SEEG does not share EEG's common scalp coordinate frame, so the design must avoid prematurely treating subject-level SEEG field templates as group-level universal templates.

## Goals / Non-Goals

**Goals:**
- Derive subject-level SEEG global-field states from band-limited bipolar SEEG peak maps before region/network averaging.
- Use a peak-detection and backfitting workflow that is intentionally analogous to EEG microstate analysis while remaining robust to bipolar polarity and uneven channel variance.
- Produce continuous subject-level SEEG field-state sequences that can be related to EEG microstates through synchronous, lagged, and transition-conditioned summaries.
- Add GFP-aware follow-ups that ask whether SEEG field-state switching remains associated with EEG microstates or EEG transitions after accounting for EEG GFP context.
- Keep inference patient-first and avoid assuming cross-subject identity of SEEG field-state labels.

**Non-Goals:**
- Defining a universal group-level SEEG field-state template set shared across subjects.
- Replacing the existing Yeo17/AAL3 region workflow or the reduced-space direct-state branch.
- Solving invasive-electrode spatial normalization across subjects in the first implementation.
- Claiming that lag offsets alone establish causal direction.

## Decisions

### 1. SEEG field-state derivation will be subject-level and electrode-space first
The branch will operate on cropped bipolar SEEG after bandpass and resampling, before same-region averaging. Each subject will receive an independent set of SEEG field templates and a continuous SEEG field-state sequence.

Rationale:
- bipolar channel geometry is not shared across subjects
- subject-level derivation avoids false precision from trying to align invasive coverage patterns across patients

Alternatives considered:
- derive field states from staged Yeo17/AAL3 averages: rejected because this is no longer an electrode-space topography problem
- fit a pooled group template directly in electrode space: rejected because channel identities and coverage are not commensurate across subjects

### 2. The primary preprocessing for state discovery will use per-bipolar-channel z-scoring
The branch will standardize each bipolar channel within subject before peak-map clustering. Raw-scale or robust-normalized variants may be added as sensitivity analyses later, but the first branch will treat per-channel z-score as the primary discovery space.

Rationale:
- without channel-wise normalization, clustering is likely to rediscover a small number of high-variance electrodes rather than recurrent spatial configurations
- the project already observed a strong shared global amplitude drive, so the state-discovery step should minimize simple amplitude dominance

Alternatives considered:
- keep raw amplitudes during clustering: rejected as the primary method because it would blur spatial structure with channel variance and coverage effects
- use absolute values per channel: rejected because it discards informative spatial opposition structure too early

### 3. Peak maps will be selected from a predefined SEEG global metric family, with RMS peaks as the primary method
The branch will derive SEEG peak events from a small predefined set of subject-level global metrics. The primary peak metric will be the RMS of z-scored bipolar channels, with spatial-dispersion peaks reserved as a sensitivity family.

Rationale:
- the user is specifically asking for a SEEG analogue of EEG GFP peaks
- a predefined peak family avoids opportunistic peak-definition selection after looking at results

Alternatives considered:
- detect peaks directly on one arbitrary reference channel: rejected because it is not a global-field concept
- search many peak metrics and keep the best one: rejected because it would inflate multiplicity and weaken interpretation

### 4. Template matching and clustering will be polarity-invariant
Peak-map clustering and backfitting will use polarity-invariant similarity such as absolute correlation between instantaneous SEEG maps and SEEG field templates.

Rationale:
- bipolar polarity can flip with electrode orientation and referencing choices
- polarity-invariant similarity is the closest analogue to the way EEG microstate matching focuses on topographic configuration rather than sign alone

Alternatives considered:
- signed correlation: rejected as primary because the same configuration can appear sign-flipped in bipolar space
- channel-wise absolute values before clustering: rejected because it throws away too much relative structure

### 5. The first implementation will use a fixed primary state count and continuous backfitting
The primary branch will use a fixed default SEEG field-state count equal to the EEG microstate count, while allowing sensitivity reruns with nearby values. After clustering peak maps, the system will backfit the templates to the full continuous SEEG time series and apply a minimum-duration smoothing rule.

Rationale:
- fixed `K=4` gives a stable baseline that is easy to compare against EEG microstates
- continuous backfitting is necessary to study lagged alignment and transition timing, not just peak-level contingency

Alternatives considered:
- choose `K` adaptively per subject in the first release: rejected because it complicates branch identity and cross-subject summaries too early
- analyze only peak labels without continuous backfitting: rejected because it cannot support the transition and lag analyses the user actually cares about

### 6. EEG coupling summaries will be patient-first and stratified by analysis question
The branch will summarize EEG-SEEG relations in three layers:
- synchronous and lagged EEG microstate versus SEEG field-state coupling
- EEG transition-conditioned SEEG field-state switching
- GFP-aware follow-ups that model SEEG field-state switching against EEG microstates/transitions with EEG GFP context included

Rationale:
- this mirrors the hierarchy that emerged from previous results: shared drive first, then state timing, then GFP-aware follow-up
- subject-level summaries can be aggregated without forcing state labels to be globally identical across subjects

Alternatives considered:
- directly compare pooled sample-level EEG and SEEG states across the cohort: rejected because subject imbalance and temporal dependence would dominate

### 7. Cross-subject reporting will avoid claiming universal SEEG field-state identities
Reports will present subject-level SEEG template panels and cohort-level coupling statistics, but the first implementation will not claim that subject `state 0` is the same invasive field pattern as another subject's `state 0`.

Rationale:
- subject-level template identities are not naturally aligned in invasive recordings
- the inferential target is the EEG-SEEG relationship, not a universal invasive atlas of states

Alternatives considered:
- perform template matching across subjects in the first change: rejected because spatial normalization of invasive electrode maps is a separate research problem

## Risks / Trade-offs

- [Channel-wise z-scoring may suppress biologically meaningful amplitude dominance] -> Keep it as the primary discovery space but leave raw-scale or robust-normalized reruns as explicit sensitivity directions.
- [Bipolar polarity handling could still distort templates] -> Use polarity-invariant similarity and document that template sign is not meant to be interpreted like scalp EEG polarity.
- [Field-state labels are not naturally aligned across subjects] -> Report subject-level templates separately and make group inference depend on coupling effects, not shared label identity.
- [Peak density may create very small but highly significant effects] -> Predefine peak subsampling and structured nulls, and inspect effect sizes alongside p-values.
- [This branch increases exploratory multiplicity] -> Separate primary versus sensitivity decisions in both design and reports, and keep the first implementation scoped to one primary peak metric and one primary normalization scheme.

## Migration Plan

1. Add an upstream exploratory artifact path that stages subject-level bipolar SEEG peak maps, subject-level SEEG field templates, and continuous SEEG field-state labels.
2. Add new exploratory CLI/report branches for synchronous, lagged, transition-conditioned, and GFP-aware SEEG field-state coupling.
3. Validate the branch on the existing Yeo17 cohort as an exploratory extension, not as a replacement for the maintained workflows.
4. If the branch shows useful signal, consider a later follow-up change for cross-subject template correspondence or anatomical projection of subject-level SEEG field templates.

## Open Questions

- Which sensitivity peak family should be first after RMS peaks: spatial dispersion or envelope-based global energy?
- Should the first GFP-aware follow-up model binary SEEG switching occurrence, time-to-next-switch, or both?
- What minimum-duration rule is most appropriate for invasive field-state backfitting: reuse the EEG-style `30 ms`, or shorten it for faster SEEG dynamics?
