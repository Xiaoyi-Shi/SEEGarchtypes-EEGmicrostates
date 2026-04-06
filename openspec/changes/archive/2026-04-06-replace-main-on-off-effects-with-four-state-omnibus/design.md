## Context

The focused public workflow currently stages EEG labels and `AAL3` SEEG region signals, then computes main activity and connectivity outputs by collapsing each EEG microstate into a `state` versus `off-state` contrast. In code, the subject-level activity and connectivity helpers emit one `effect_mean_diff` per `patient x unit x microstate`, and the group layer applies sign-flip permutation testing to that single contrast column.

That structure is now the main constraint. It makes the current workflow simple, but it cannot express a true four-state omnibus test or a clean pairwise post-hoc analysis. The report layer also assumes `effect_mean_diff`-shaped outputs, so replacing `on/off` semantics affects subject summaries, group statistics, cached artifact names, and report export behavior across the main activity and connectivity stages.

This change is intentionally limited to the focused main workflow. Exploratory event-locked, windowed, transition, and alignment analyses remain separate because they are not `state-vs-rest` tests.

## Goals / Non-Goals

**Goals:**
- Replace main activity `state-vs-rest` summaries with subject-level four-state activity profiles.
- Replace main connectivity `state-vs-rest` summaries with subject-level four-state connectivity profiles.
- Add group-level omnibus outputs and pairwise post-hoc outputs for the main activity and connectivity stages.
- Keep the existing public CLI surface and staged cache reuse model intact.
- Export main-workflow reports and tables that match the new omnibus/post-hoc semantics.

**Non-Goals:**
- Do not change EEG/SEEG staging, cohort construction, or `AAL3` mapping.
- Do not change exploratory `pre/post`, `transition`, `windowed`, or `state-alignment` analyses.
- Do not redesign the exploratory report layer beyond whatever compatibility is needed to keep main reports working.
- Do not preserve backward-compatible `effect_mean_diff` schemas for the main activity/connectivity outputs.

## Decisions

### 1. Main subject-level outputs will store four-state profiles, not `on/off` contrasts

For each `patient x region`, the activity stage will compute one summary row per EEG microstate containing the state-specific mean value and sample count. For each `patient x method x region_a x region_b`, the connectivity stage will compute one summary row per EEG microstate containing the state-specific connectivity value and sample count.

Why:
- Omnibus and pairwise post-hoc tests both need the same four-state within-subject profile.
- Reconstructing a four-state profile from `state-vs-rest` contrasts is indirect and brittle.
- Keeping subject-level outputs in profile form makes activity and connectivity follow the same analysis contract.

Alternatives considered:
- Keep `on/off` subject summaries and derive omnibus tests from those contrasts. Rejected because the contrasts are not independent and no longer represent the desired hypothesis.
- Store only group-level omnibus results. Rejected because it removes reusable staged subject summaries needed for debugging and post-hoc testing.

### 2. Group statistics will use within-subject omnibus testing plus paired post-hoc comparisons

The group layer will consume subject-level four-state profiles and compute:
- one omnibus result per `region` for activity
- one omnibus result per `method x region_a x region_b` for connectivity
- pairwise post-hoc comparisons across the six EEG-state pairs for the same units

Why:
- The user requirement is specifically `4-state omnibus + post-hoc`, not a new `state-vs-rest` reformulation.
- The current codebase already uses permutation-style group inference, so a within-subject permutation path is more coherent than introducing a normality-dependent parametric-only layer.

Alternatives considered:
- Repeated-measures ANOVA only. Rejected as the sole path because it would be a larger methodological shift away from the current permutation-first design.
- Omnibus only, without post-hoc outputs. Rejected because it would answer whether differences exist but not which state pairs drive them.

### 3. Main activity and connectivity caches will use new omnibus/post-hoc artifact stems

The main stages will stop treating the old `subject_*_effects` and `group_*_effects` files as the canonical outputs for the public workflow. Instead, the workflow will write distinct profile, omnibus, and post-hoc artifacts for activity and connectivity.

Why:
- The old filenames imply `effect_mean_diff` semantics that will no longer be true.
- Reusing those stems would make stale cached outputs and old downstream consumers harder to reason about.
- New stems let the report layer discover the correct artifact family without ambiguous schema branching.

Alternatives considered:
- Keep the old filenames and change their columns in place. Rejected because it silently breaks downstream consumers and makes cache identity harder to trust.

### 4. The focused workflow will change only the main stages, not exploratory analyses

Exploratory event-locked analyses compare `pre` versus `post` windows, transition analyses compare `from_state -> to_state` events, and windowed analyses compute occupancy/value coupling. They are not the same hypothesis family as main `state-vs-rest` activity or connectivity.

Why:
- The user asked to change the main workflow first.
- Forcing all exploratory outputs into omnibus/post-hoc form would mix distinct statistical questions and increase scope sharply.

Alternatives considered:
- Unify all exploratory outputs under omnibus/post-hoc. Rejected as a separate future change.

### 5. Report rendering will export separate omnibus and post-hoc outputs

The report stage will render and export the new main activity/connectivity artifact families as distinct omnibus and pairwise result sets rather than a single `effect_mean_diff` heatmap per stage.

Why:
- The visual contract changes once the main result is no longer one scalar contrast per state.
- Keeping omnibus and post-hoc outputs separate preserves interpretability.

Alternatives considered:
- Collapse omnibus and pairwise into one oversized report table. Rejected because it would be harder to read and harder to test.

## Risks / Trade-offs

- [More pairwise outputs increase multiple-comparison burden] → Keep omnibus and post-hoc outputs as separate artifact families and document the correction scope explicitly.
- [Connectivity group stats could become more expensive] → Compute subject-level four-state profiles first so group inference operates on compact summaries rather than raw aligned time series.
- [Existing scripts that expect `effect_mean_diff` main outputs will break] → Treat this change as breaking, use new artifact stems, and update README plus processing documentation.
- [Omnibus statistic choice may affect interpretability] → Keep the spec at the behavior level and settle the exact statistic during implementation with tests that validate within-subject four-state inference.

## Migration Plan

- Add new subject/profile, omnibus, and post-hoc cache/report artifact families for the main activity and connectivity stages.
- Update report rendering to read the new artifact families.
- Rerun the main workflow stages to populate the new cache/report outputs.
- Leave existing historical `on/off` outputs in earlier run directories untouched; they remain historical artifacts rather than current canonical outputs.
- If rollback is needed, revert to the previous implementation and rerun the old main stages against the existing cache inputs.

## Open Questions

- Which omnibus statistic should back the within-subject permutation test in implementation: a repeated-measures ANOVA-style statistic, a rank-based Friedman-style statistic, or another equivalent four-state summary?
- Should post-hoc pairwise outputs be generated for all eligible units, or only for units that pass the omnibus threshold?
- What exact figure forms best communicate omnibus activity and omnibus connectivity results without overwhelming the current report set?
