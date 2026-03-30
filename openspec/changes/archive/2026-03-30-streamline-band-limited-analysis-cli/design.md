## Context

The repository started as an exploratory platform with multiple public analysis branches: `main` EEG microstates, HFA-based SEEG coupling, band-limited EEG/SEEG microstate overlap, and band-limited connectivity. That exploration produced useful building blocks, but the public CLI now exposes more paths than the intended scientific workflow needs.

The desired workflow is narrower:

- `IDE_A` cohort preparation
- `1-40 Hz` EEG microstate state generation
- `1-40 Hz` SEEG Yeo17 network signal generation
- state-conditioned Yeo17 activity effects as a supplemental analysis
- state-conditioned Yeo17 connectivity effects as the primary analysis
- report and table export

The main constraint is to keep intermediate caches explicit so users can rerun and inspect stages independently. Another constraint is to avoid painting the codebase into a corner if future work adds new frequency bands or new connectivity methods.

## Goals / Non-Goals

**Goals:**
- Expose a single public CLI workflow centered on the `1-40 Hz` analysis path.
- Keep the workflow staged in roughly 4-6 commands so intermediate artifacts remain inspectable and debuggable.
- Make connectivity the primary downstream product and activity the supplemental downstream product.
- Keep future band and method extension points in parameters and configuration rather than multiplying public commands.
- Preserve cache reuse between shared upstream stages and downstream analyses.

**Non-Goals:**
- Reworking cohort eligibility or IDE_A segmentation rules.
- Redesigning the underlying EEG microstate algorithm.
- Committing to immediate deletion of every low-level helper if a temporary internal reuse path is still useful during migration.
- Expanding the scientific scope beyond `IDE_A`, `1-40 Hz`, Yeo17 activity, and Yeo17 connectivity.

## Decisions

### Decision: Replace branch-centric CLI exposure with stage-centric CLI exposure
The public CLI will be organized around stages such as `build-index`, `run-eeg-states`, `run-seeg-networks`, `run-activity-effects`, `run-connectivity-effects`, and `render-reports`.

Rationale:
- These names match the scientific workflow rather than the implementation history.
- They reduce cognitive load for users who only care about the focused band-limited pipeline.
- They keep a clear place to stop and inspect caches.

Alternative considered:
- Keep the existing commands and only hide legacy ones in documentation. Rejected because the command surface would still imply multiple first-class workflows.

### Decision: Keep shared upstream caches explicit and reusable
EEG state generation and SEEG network signal generation will remain separate stages with persistent caches. Activity and connectivity stages will consume those caches rather than recomputing upstream results.

Rationale:
- This keeps debugging practical.
- It avoids recomputation when only downstream statistics or methods change.
- It supports future extensions to additional connectivity methods without re-running EEG microstate fitting.

Alternative considered:
- Collapse everything into a single monolithic `run-main-analysis` command. Rejected because it hides useful intermediate states and makes debugging harder.

### Decision: Treat activity and connectivity as sibling downstream stages with different analytical priority
The workflow will preserve both analyses, but reports, CLI wording, and documentation will present connectivity as the primary output and activity as a supplemental output.

Rationale:
- This matches the current scientific intent.
- It avoids deleting useful supplemental analysis while still clarifying what the project is optimizing for.

Alternative considered:
- Drop activity entirely. Rejected because the supplemental activity view remains scientifically useful and shares the same upstream caches.

### Decision: Keep extensibility in parameters, not public command sprawl
The public workflow will default to the `1-40 Hz` path, but internal and configuration boundaries will remain able to accept alternative bands or connectivity methods in the future.

Rationale:
- The project can stay focused now without making future band/method expansion awkward.
- `corr`, `PLV`, and `wPLI` already demonstrate that method variation belongs under one stage, not separate top-level workflows.

Alternative considered:
- Hard-code all naming and cache layout exclusively around `1-40 Hz`. Rejected because it would make later extension unnecessarily invasive.

### Decision: Remove cross-modal SEEG microstate overlap from the primary public workflow
EEG/SEEG microstate overlap outputs will no longer define the main band-limited branch. The mainline will be EEG-state-conditioned activity and connectivity.

Rationale:
- The project’s main question is no longer state-to-state correspondence.
- Removing that branch from the primary CLI keeps the workflow aligned with the active scientific aim.

Alternative considered:
- Keep overlap as a co-equal public stage. Rejected because it dilutes the mainline and preserves the same command sprawl this change is trying to remove.

## Risks / Trade-offs

- [Breaking CLI changes] → Document explicit old-to-new command mapping in README and proposal, and keep cache boundaries recognizable so users can reorient quickly.
- [Legacy implementation may still reference removed branches] → Treat low-level cleanup as an implementation task, with public CLI simplification first and dead-path cleanup second.
- [The cross-modal overlap branch may still be useful later] → Demote it from the mainline rather than forbidding reintroduction; if needed later it can return as an optional/internal capability.
- [Future band expansion could reopen CLI complexity] → Keep the public surface narrow and place band/method variability under stage parameters instead of new commands.

## Migration Plan

- Define the new staged CLI contract in specs before implementation.
- Rework the public commands and report flow to match the staged `1-40 Hz` pipeline.
- Retarget documentation, tests, and report naming to the new primary/supplemental hierarchy.
- Remove or demote legacy public commands and update any cached-output expectations accordingly.
- If necessary during implementation, keep thin internal compatibility shims temporarily, but do not preserve them as part of the final public CLI contract.

## Open Questions

- Whether any hidden/internal command should remain for cross-modal SEEG microstate overlap, or whether that path should be fully removed.
- Whether the final public CLI should expose band as a parameter immediately or keep `1-40 Hz` implicit until a second band is actually needed.
- Whether activity outputs should emphasize absolute network strength, relative network prominence, or both in the supplemental reporting layer.
