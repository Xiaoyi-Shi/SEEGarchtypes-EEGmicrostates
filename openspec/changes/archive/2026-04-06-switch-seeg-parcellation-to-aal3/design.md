## Context

The current public SEEG staging path assumes Schaefer/Yeo17 functional-network labels at multiple layers: bipolar-contact mapping, per-patient aggregated time series, cached artifact names, CLI help text, report titles, and accepted OpenSpec requirements. The repository data already ships an `AAL3` column in each patient `Atlas.tsv`, and exploratory checks on the existing cohort indicate that strict same-label bipolar aggregation remains viable under `AAL3`.

This change is cross-cutting because it affects the SEEG mapping layer, staged workflow outputs, downstream effect semantics, public documentation, and tests. It also changes the meaning of persisted caches and reports, so migration/invalidation behavior must be explicit.

## Goals / Non-Goals

**Goals:**
- Make `AAL3` the public SEEG parcellation used by staged `1-40 Hz` activity and connectivity analyses.
- Preserve the existing high-level workflow shape so EEG processing, alignment, activity statistics, and connectivity statistics continue to operate on wide SEEG time-series tables.
- Remove Yeo17-specific assumptions from public-facing behavior, cached artifact semantics, and accepted specs for the main workflow.
- Ensure new staged outputs cannot be confused with previously generated Yeo17-based artifacts.

**Non-Goals:**
- Add runtime support for arbitrary atlas selection in this change.
- Change EEG preprocessing, EEG microstate fitting, or connectivity formulas.
- Introduce a new rule for assigning bipolar channels that span different atlas regions.
- Rework the retired experimental HFA or cross-modal microstate-fitting branches beyond the spec-level staged-input updates required by this change.

## Decisions

### 1. The public SEEG parcellation becomes `AAL3`

The staged workflow will use the existing `AAL3` column from `Atlas.tsv` as the single source of truth for SEEG region labels.

Why:
- The user intent is specifically to stop using Yeo17 and switch to the already-available `AAL3` labeling.
- `AAL3` values are direct anatomical labels and do not need the Yeo17-specific prefix parsing currently applied to Schaefer labels.
- A single explicit atlas target keeps the change bounded while still allowing later abstraction if multiple parcellations are needed.

Alternatives considered:
- Make atlas selection fully configurable now.
  Rejected for this change because it expands scope into a general framework decision before the AAL3 path is stabilized.
- Keep Yeo17 as the default and add AAL3 as an optional branch.
  Rejected because it conflicts with the requested workflow change and preserves the wrong public default.

### 2. Bipolar channels remain valid only when both contacts share the same non-empty `AAL3` label

The current same-label aggregation rule will be preserved, but the label comparison will use the complete `AAL3` string rather than Yeo17 network prefixes.

Why:
- This keeps the signal construction rule consistent with the existing workflow philosophy.
- It avoids introducing ambiguous ownership for bipolar channels whose contacts cross anatomical boundaries.
- Exploratory checks indicate that same-label `AAL3` coverage remains sufficient for staged activity and connectivity analyses.

Alternatives considered:
- Assign cross-region bipolar channels to one endpoint or both endpoints.
  Rejected because it creates asymmetric or duplicated region signals that are harder to interpret.
- Collapse `AAL3` labels into coarser anatomical groups.
  Rejected because it discards the granularity the switch is meant to gain.

### 3. Public artifact semantics move from `network` to `region`/`parcel`

The public workflow, cached SEEG artifacts, coverage summaries, and report text will use neutral region terminology rather than Yeo17-network terminology. Internal helper names may transition incrementally, but user-visible outputs should no longer describe AAL3 data as Yeo17 networks.

Why:
- The current public labels would become misleading once the staged data are anatomical regions.
- Neutral naming creates a cleaner path for future atlas work without forcing full generalization in this change.

Alternatives considered:
- Keep existing `network` naming for compatibility.
  Rejected because it would misdescribe the new data products and create avoidable confusion in reports and tests.

### 4. Cache invalidation will be explicit rather than implicit

The change will introduce an explicit SEEG parcellation setting into the analysis configuration and use region-oriented artifact stems for staged SEEG outputs. This ensures previously generated Yeo17 caches are not silently reused after the workflow switches to `AAL3`.

Why:
- Downstream stages currently trust cache existence and do not inspect artifact provenance beyond branch/hash.
- The current config hash does not encode the atlas choice because atlas choice is not yet modeled.
- Renaming region-oriented cache stems makes the semantic change visible to both code and users.

Alternatives considered:
- Reuse the existing cache stems and rely only on manual cleanup.
  Rejected because it is brittle and error-prone.
- Change only the branch token.
  Rejected because the public workflow branch remains conceptually the same staged `1-40 Hz` path; the changed parameter should be captured as configuration instead.

### 5. The staged workflow shape stays intact

The command sequence remains index -> EEG states -> SEEG region staging -> activity/connectivity -> reports. The existing top-level command entry points remain stable in this change, while their help text and outputs are updated to describe `AAL3` region staging. Downstream computations will continue consuming wide time-series tables keyed by `time_sec`, so alignment and statistics logic do not require algorithmic redesign.

Why:
- The downstream code already operates generically on columns representing SEEG units.
- Preserving the workflow shape limits the change surface to mapping, semantics, and public reporting.

Alternatives considered:
- Redesign downstream statistics for anatomy-specific modeling at the same time.
  Rejected because it would bundle a methodology change into what is primarily a parcellation backend switch.

## Risks / Trade-offs

- [More regions and more region pairs increase multiple-testing burden] -> Keep the statistical pipeline unchanged for the first migration and validate group-level output sparsity after rerunning the staged workflow.
- [Long `AAL3` labels can degrade plot readability] -> Update report titles/axes to region terminology and accept that some heatmaps may need larger figures or later label-management follow-up.
- [Partial refactors may leave `network` terminology in internal code paths] -> Treat user-visible text, artifact names, and spec language as mandatory cleanup in this change; defer purely internal helper renames only where they do not leak into outputs.
- [Legacy Yeo17 caches may still exist on disk] -> Ensure the new configuration/hash and region-specific cache stems prevent accidental reuse, and document that staged SEEG outputs must be regenerated.

## Migration Plan

1. Add the AAL3 parcellation setting and region-oriented staged artifact names.
2. Replace Yeo17-specific mapping logic with direct `AAL3` region matching for bipolar contacts.
3. Update staged SEEG generation, downstream loading paths, and reports to consume region artifacts.
4. Update CLI help text, README guidance, and tests to reflect `AAL3` regions as the public SEEG output.
5. Regenerate SEEG-region, activity, connectivity, and report artifacts; do not reuse Yeo17-generated SEEG caches.

Rollback:
- Revert the change and regenerate staged outputs with the previous Yeo17-based configuration.
- Because the new artifacts will have distinct semantics and cache identity, rollback does not require mutating the new files in place.

## Open Questions

- None for proposal scope. Command identifiers remain stable for this change, and internal naming cleanup is limited to user-visible outputs plus the code paths that must change for correct `AAL3` behavior.
