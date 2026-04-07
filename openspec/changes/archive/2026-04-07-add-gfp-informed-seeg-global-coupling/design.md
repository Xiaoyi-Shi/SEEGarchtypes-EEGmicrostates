## Context

The repository currently stages EEG microstate labels, transition tables, and SEEG region/network signals, then analyzes region-wise activity, connectivity, and direct EEG-SEEG state coupling. EEG global field power (GFP) is already central to template fitting, but the workflow does not persist continuous GFP traces or GFP peak events as reusable downstream artifacts, and it does not test whether cross-modal coupling is better explained by shared global amplitude dynamics than by state identity alone.

Recent Yeo17 exploratory results sharpen the problem. Main network-level activity and connectivity analyses remained negative, while direct transition-conditioned state coupling showed a clearer signal than tonic network summaries. That pattern suggests the pipeline is missing an intermediate explanatory layer: before interpreting microstate or transition effects as state-specific EEG-SEEG coupling, the workflow should quantify shared EEG GFP versus SEEG global dynamics and then ask whether state effects survive after GFP is accounted for.

The change also has a multiple-definition problem. For SEEG there is no single universally accepted analogue to EEG GFP. The workflow therefore needs a predeclared primary SEEG global metric plus a small, explicit set of sensitivity metrics, instead of selecting a definition retrospectively from whichever result looks strongest.

## Goals / Non-Goals

**Goals:**
- Persist reusable EEG GFP time series and GFP peak artifacts on the same staged time axis as the existing EEG microstate outputs.
- Define a GFP-informed exploratory branch that compares continuous EEG GFP against multiple predefined SEEG global metrics derived from staged Yeo17 signals.
- Support synchronous, lagged, and symmetric peak-centered EEG GFP versus SEEG global analyses without assuming EEG leads or lags SEEG a priori.
- Add follow-up analyses that test whether EEG microstate and transition effects on SEEG remain after accounting for EEG GFP.
- Keep inference patient-first and preserve temporal structure in null procedures.

**Non-Goals:**
- Changing the main staged activity/connectivity workflow or replacing existing direct state-coupling analyses.
- Claiming causal direction from lag offsets alone.
- Generalizing the first implementation to every parcellation/backend combination if the exploratory contract is explicitly Yeo17-focused.
- Searching a large space of SEEG global definitions opportunistically.

## Decisions

### 1. Persist EEG GFP artifacts from the staged EEG branch
The EEG stage will be treated as the source of truth for downstream GFP-informed analyses. In addition to labels and the active template artifact, it should persist:
- a continuous GFP trace aligned to the staged EEG sample axis
- a GFP peak/event table derived from the same preprocessed EEG used for labeling

Rationale:
- downstream exploratory methods can reuse the staged EEG branch without recomputing from raw FIF files
- the time base remains consistent with microstate labels and transition tables

Alternatives considered:
- Recompute GFP on demand inside each exploratory method: rejected because it duplicates work and risks subtle drift in preprocessing assumptions.

### 2. Use predefined SEEG global metrics with one primary metric and limited sensitivities
The branch should support multiple SEEG global metrics, but only from a small predefined family:
- primary: equal-weight RMS of within-patient, within-network standardized Yeo17 signals
- sensitivity: envelope RMS of the same standardized signals
- sensitivity: spatial-dispersion style standard deviation across standardized signals
- optional sensitivity: `sqrt(n_bipolar_channels)` weighting rather than full channel-count weighting

Rationale:
- equal-weight RMS is robust to bipolar sign cancellation and does not let high-coverage networks dominate by default
- envelope RMS better reflects amplitude/energy style coupling
- spatial dispersion is the closest analogue to EEG GFP as a cross-network spread measure

Alternatives considered:
- signed cross-network mean: rejected because bipolar polarity and phase cancellation make it unstable
- full channel-count weighting as the default: rejected because coverage imbalance would let Default/Control networks dominate the “global” summary

### 3. Restrict the primary Yeo17 global metric to a stable network subset
The primary global metric should use only a predeclared “core” Yeo17 subset with adequate cohort coverage, while sensitivity analyses may use all observed networks or weighting variants.

Rationale:
- some Yeo17 networks are observed in very few subjects, so including them in the primary global summary makes cross-subject comparisons unstable

Alternatives considered:
- use every available network per subject in the primary metric: rejected because the global metric would vary too much in composition across subjects

### 4. Separate continuous global coupling from state-specific follow-ups
The exploratory branch should be organized in two stages:
- Stage A: continuous GFP/global analyses
  - synchronous coupling
  - lagged coupling
  - symmetric peak-centered trajectories
- Stage B: state follow-ups after GFP control
  - GFP-controlled microstate effects on SEEG global metrics
  - GFP-controlled transition-conditioned effects on SEEG global metrics

Rationale:
- this preserves the interpretive hierarchy: shared amplitude drive first, state-specific interpretation second

Alternatives considered:
- jump directly to GFP-controlled state models without first quantifying shared global coupling: rejected because it weakens interpretability

### 5. Use patient-first statistics and structured nulls
Each exploratory summary should be computed at the patient level first and only then aggregated at the group level. Continuous and peak-centered analyses should use temporal-structure-preserving nulls such as circular shifts. Group-level inference should remain sign-flip/permutation style over patient-level effects.

Rationale:
- avoids pooled-sample inflation
- stays consistent with the existing direct state-coupling branch

Alternatives considered:
- pooled raw-sample inference: rejected because temporal dependence and subject imbalance would distort significance

### 6. Use GFP-adjusted patient-level models as the primary “control GFP” strategy
The primary follow-up should use within-patient regression-style adjustment, for example:
- `SEEG_global(t) ~ GFP(t) + microstate(t)`
- `SEEG_global(t) ~ GFP(t) + transition_window_indicator(t)`

The branch may later add GFP-matched stratification as a sensitivity method, but not as the first required implementation.

Rationale:
- regression-style adjustment matches the continuous sample-level data structure already produced by the staged workflow
- it is easier to summarize patient-first coefficients and compare them at the group level than to define exact matching strata across all subjects

Alternatives considered:
- GFP matching/stratification as the only control strategy: rejected for the first change because it is operationally heavier and less natural for continuous traces

## Risks / Trade-offs

- [Metric multiplicity can look like p-hacking] -> Predeclare one primary SEEG global metric and treat the others as sensitivity analyses in both specs and reports.
- [Yeo17 coverage is uneven across subjects] -> Use a core-network subset for the primary metric and reserve weighting/all-network variants for sensitivity checks.
- [Lag offsets may be overinterpreted as causal lead/lag] -> Report them as temporal offsets and keep peak-centered windows symmetric around the EEG event.
- [GFP and microstate are methodologically linked] -> Make GFP-controlled state/transition follow-ups a required part of the branch, not an optional afterthought.
- [Raw 1-40 Hz SEEG traces mix phase and amplitude information] -> Include envelope-based global metrics as a planned sensitivity family.

## Migration Plan

1. Extend staged EEG outputs with reusable GFP traces and peak tables.
2. Add exploratory branch-specific SEEG global-metric artifacts derived from staged Yeo17 signals.
3. Implement continuous global coupling, lag scans, and symmetric peak-centered summaries.
4. Add GFP-adjusted microstate and transition follow-up models plus reports.
5. Validate the branch on the current Yeo17 cohort before considering broader parcellation support.

## Open Questions

- What exact subject-support threshold should define the Yeo17 “core” network subset for the primary metric?
- Should the first implementation expose weighting strategy as a CLI option or keep it fixed in code/tests until the branch stabilizes?
- Should GFP-controlled transition follow-ups operate on per-sample indicators, transition-locked windows, or both?
