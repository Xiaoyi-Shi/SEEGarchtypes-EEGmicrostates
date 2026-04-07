## Context

The current repository already behaves like a staged, cache-first workflow built around three maintained upstream products: a selected IDE-state cohort/index, EEG microstate labels generated from an active `pycrostates` template, and staged SEEG region signals for downstream activity and connectivity analyses. The accepted specs, however, still describe two important behaviors that no longer match the intended operating model: fitting a new EEG template by default and treating `IDE_A` as the only supported analysis state.

At the same time, the current maintained downstream analyses emphasize state-conditioned SEEG regional activity and connectivity summaries. Those analyses remain the right mainline, but they are not the most sensitive tools for asking whether EEG and SEEG state sequences couple directly in time. Earlier SEEG-microstate alignment ideas were removed because they risked becoming a second maintained mainline. This change reintroduces direct state coupling only as an explicit exploratory branch with separate caches, separate reports, and separate statistical assumptions.

## Goals / Non-Goals

**Goals:**
- Make configured EEG templates the default contract for the public EEG state stage, with explicit precedence for `--template-fif` overrides.
- Treat `analysis_state` as a first-class workflow dimension with `IDE_A` as the default and `IDE_S` as an optional supported mode.
- Add a direct EEG-SEEG state-coupling exploratory branch that derives SEEG state sequences from a reduced-space SEEG representation and computes synchronous, lagged, and transition-aware coupling summaries.
- Preserve the current AAL3 activity/connectivity workflow as the maintained mainline.
- Keep all new exploratory outputs cacheable, branch-specific, and compatible with the existing report/export model.

**Non-Goals:**
- Reintroduce fit-by-default EEG template generation in the public stage.
- Make SEEG state fitting a required upstream product for the main workflow.
- Replace or remove the existing event-, window-, and transition-based region-signal exploratory analyses.
- Generalize the workflow beyond the currently supported `IDE_A` and `IDE_S` analysis states.
- Introduce a full generic framework for arbitrary SEEG state-space reducers in this change.

## Decisions

### 1. The public EEG stage will resolve an active template instead of fitting one by default

The EEG stage will always label against an active `pycrostates` `.fif` template selected by the following precedence:

1. explicit `--template-fif` override
2. configured default template path
3. fail early with a clear missing-template error

The staged EEG model artifact will remain a canonical copy of the active template used for labeling so downstream stages and reports have stable provenance.

Why:
- This matches the current intended operating model better than a fit-by-default contract.
- It keeps runs reproducible when users curate or standardize templates outside the repository.
- It avoids silently mixing “fit a new template” and “reuse a curated template” semantics inside one public stage.

Alternatives considered:
- Fit a new cohort template whenever no override is supplied.
  Rejected because it conflicts with the intended default and makes reruns less reproducible.
- Keep both fit-by-default and configured-template-by-default as equal public modes.
  Rejected because users would have to infer which semantics produced a given staged artifact.

### 2. `analysis_state` will become a first-class cache and workflow dimension

The selected IDE state will be treated as part of the public workflow contract rather than a hidden implementation detail. `IDE_A` remains the default state, but `IDE_S` becomes an explicitly supported override across repository scanning, segment materialization, staged caches, downstream analyses, logs, and reports.

Why:
- The CLI and config already partially expose this dimension.
- Keeping the public docs/specs `IDE_A`-only while the code accepts `IDE_S` creates ambiguity.
- Analysis-state-specific cache identity avoids accidental reuse across biologically different segments.

Alternatives considered:
- Keep `IDE_S` as an undocumented internal capability.
  Rejected because it preserves spec drift and makes support expectations ambiguous.
- Add separate top-level commands for `IDE_S`.
  Rejected because the existing `--analysis-state` axis is simpler and already coherent with the staged workflow.

### 3. Direct EEG-SEEG state coupling will remain an opt-in downstream exploratory branch

The maintained mainline will stay defined as staged EEG labels plus staged SEEG region signals feeding activity and connectivity analyses. Direct EEG-SEEG state coupling will be implemented as a separate exploratory branch that derives additional SEEG state artifacts only when explicitly requested.

Why:
- The main workflow contract remains interpretable and stable.
- Null or weak mainline results justify richer exploratory analyses, but not a second co-equal public pipeline.
- Separate branch-specific artifacts make it clear which outputs depend on exploratory state-fitting assumptions.

Alternatives considered:
- Restore EEG-SEEG state correspondence as a maintained upstream branch.
  Rejected because it would reintroduce the dual-mainline problem that earlier cleanup removed.
- Replace the region-based mainline with direct state coupling.
  Rejected because the current activity/connectivity outputs remain the primary maintained deliverables.

### 4. The initial direct-coupling branch will use a reduced SEEG state space rather than raw AAL3 state fitting

Direct EEG-SEEG state coupling will derive SEEG state sequences from a reduced-space SEEG representation that is distinct from the high-dimensional AAL3 reporting space. The initial implementation will favor a low-dimensional, cross-subject-comparable SEEG state space rather than fitting states directly on dense AAL3 regional matrices.

Why:
- A direct state-fitting branch needs a more stable and lower-dimensional SEEG state space than the main AAL3 reporting branch.
- Reduced-space SEEG states are more likely to yield interpretable cross-subject coupling metrics.
- This preserves the main AAL3 outputs while allowing exploratory state models to use a representation better suited for sequence-level coupling.

Alternatives considered:
- Fit SEEG states directly on AAL3 regional matrices.
  Rejected because the dimensionality and patient-specific coverage make the resulting states less stable.
- Fit SEEG states in raw contact space.
  Rejected because contact-space states are harder to compare across patients and less aligned with the current staged abstractions.
- Build a fully generic reducer/plugin system now.
  Rejected because it expands scope before the first direct-coupling branch is validated.

### 5. Direct coupling statistics will be computed patient-first and tested with time-structure-preserving surrogates

The direct branch will compute patient-level coupling summaries first, then aggregate those summaries at the group level. Null models will preserve temporal structure through circular shifts, dwell/run-length-preserving surrogates, or equivalent constrained permutations rather than naive sample shuffling.

Why:
- Sample-level pooling would overstate evidence by ignoring within-patient dependence.
- Circular or dwell-preserving surrogates are better aligned with sequence-coupling questions than iid shuffles.
- Patient-first summaries fit the existing group-level permutation/sign-flip style already used elsewhere in the repository.

Alternatives considered:
- Use naive sample permutations.
  Rejected because they break the temporal structure that defines state sequences.
- Jump directly to coupled HMMs or joint latent-state models as the first implementation.
  Rejected because they add substantial complexity before simpler coupling summaries are evaluated.

### 6. Direct coupling methods will integrate into the existing exploratory CLI/report surface with distinct branch identities

The existing `run-exploratory-coupling` surface will be extended to expose direct state-coupling analyses. Their outputs will live under distinct branch-specific cache and report families keyed by analysis method, reduced-space backend, lag configuration, and other direct-branch parameters.

Why:
- Users already have a single exploratory entry point.
- Direct coupling is exploratory analysis, not a new top-level workflow family.
- Separate branch identities preserve cache safety and output traceability.

Alternatives considered:
- Add a dedicated top-level command for direct state coupling.
  Rejected because it would add command sprawl for a branch that still depends on the same upstream staged artifacts.

## Risks / Trade-offs

- [Direct-coupling SEEG states depend on a reduced-space representation that differs from the AAL3 reporting space] -> Keep the exploratory branch explicitly separate and document the distinction in reports and CLI help.
- [`IDE_S` may have a smaller eligible cohort and weaker statistical support] -> Preserve configurable minimum-subject thresholds and make analysis-state-specific support explicit in outputs.
- [Time-structure-preserving surrogate tests can be computationally expensive] -> Cache branch-specific patient-level and group-level summaries so reruns reuse upstream staging and only recompute changed direct-branch outputs.
- [Users may expect the public EEG stage to fit templates because older specs said so] -> Update specs, README guidance, CLI help text, and failure messages in the same change.
- [Reintroducing direct state coupling could blur workflow ownership] -> Keep the mainline and direct exploratory branch separate in cache families, report names, and requirement language.

## Migration Plan

1. Update the OpenSpec contract, CLI help text, and documentation to define configured-template defaults and explicit `IDE_A`/`IDE_S` support.
2. Ensure indexing, segments, cache naming, and staged/report outputs remain analysis-state-specific and do not mix `IDE_A` and `IDE_S` runs.
3. Extend the exploratory branch to derive reduced-space SEEG state sequences and compute synchronous, lagged, and transition-aware direct coupling summaries.
4. Add branch-specific report exports and tests for the new direct-coupling outputs while preserving the existing region-signal exploratory methods.
5. Regenerate staged caches and exploratory reports under the new contracts as needed; previously generated caches remain valid only for the semantics under which they were created.

Rollback strategy:
- Revert the change and discard any direct-state exploratory caches generated under the new branch names.
- No persistent data migration is required because the exploratory direct-coupling artifacts remain separate from the maintained AAL3 mainline artifacts.

## Open Questions

- Whether the first direct-coupling implementation should expose exactly one reduced-space SEEG backend or more than one is still a scoping choice for implementation.
- Whether SEEG state count should default to the EEG microstate count or be configured independently remains open.
- The default lag range and lag resolution for lagged direct coupling should be chosen to balance interpretability and compute cost during implementation.
