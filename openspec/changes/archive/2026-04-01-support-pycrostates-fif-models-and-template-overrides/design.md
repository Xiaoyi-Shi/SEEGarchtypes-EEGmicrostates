## Context

The current EEG microstate workflow fits a `pycrostates` `ModKMeans` model but immediately converts it into a repository-specific dictionary that is persisted as `.npz`. Label assignment is then performed through custom correlation logic, and the report stage renders a channel-by-template heatmap rather than the native microstate topographic maps.

This split creates three problems. First, the staged model artifact is not directly reusable with `pycrostates` tools. Second, a user cannot cleanly replace the fitted template set with a curated external template file. Third, the rendered figure does not match the expected group microstate topomap view. The change touches EEG fitting, labeling, CLI orchestration, report rendering, and tests, so a design document is warranted.

## Goals / Non-Goals

**Goals:**
- Make the staged EEG microstate model artifact a standard `pycrostates` `.fif` cluster file.
- Support whole-template replacement by loading a user-supplied `pycrostates` template file instead of fitting a new model.
- Keep downstream workflow behavior cache-friendly so activity and connectivity stages continue to reuse EEG state artifacts.
- Render group EEG microstate figures as scalp topographic maps through `ModKMeans.plot()`.
- Preserve the existing downstream label-table shape unless a stronger reason emerges to change it.

**Non-Goals:**
- Introduce partial cluster-center editing inside the repository.
- Redesign the cohort, preprocessing, or montage-restoration workflow.
- Expand the public workflow beyond the current staged `1-40 Hz` path.
- Add a second model format alongside `.fif` as a co-equal long-term artifact.

## Decisions

### Decision: Use native `pycrostates` `.fif` cluster files as the canonical EEG model artifact
The EEG stage will persist the fitted model with `ModKMeans.save()` and treat that `.fif` file as the canonical reusable model artifact. Loading will use `pycrostates.io.read_cluster()`.

Rationale:
- This aligns the repository with the library used to fit the model.
- It makes saved models directly reusable outside this codebase.
- It removes the need to maintain a parallel repository-specific model schema.

Alternatives considered:
- Keep the custom `.npz` schema and add a compatibility export. Rejected because it preserves duplicate artifact paths and unclear canonical ownership.
- Persist both `.npz` and `.fif` indefinitely. Rejected because it increases cache surface and migration burden without adding stable value.

### Decision: Treat template override as whole-file replacement, not map-level mutation
The EEG stage will accept an optional path to an external `pycrostates` `.fif` cluster file. When supplied, the stage will load that file as the active model for labeling and reporting instead of fitting a new model from the current cohort.

Rationale:
- Whole-file replacement matches the user intent and keeps artifact semantics clean.
- A loaded `ModKMeans` object already carries channel metadata, cluster names, labels, and plotting behavior.
- This avoids hand-editing internal fitted-object fields or inventing a custom patch format for individual maps.

Alternatives considered:
- Allow replacing only selected cluster centers. Rejected because it complicates validation and weakens the meaning of the saved fitted object.
- Restrict override support to internal cache files only. Rejected because the point of the change is reusable external template curation.

### Decision: Use the active `ModKMeans` object for both segmentation and figure generation
The workflow will use the loaded or fitted `ModKMeans` object as the source of truth for label generation and for report rendering. The label table may still be normalized into the repository's existing tabular schema after prediction, but prediction should come from `ModKMeans.predict()` rather than the current custom correlation path.

Rationale:
- It keeps model persistence, prediction, and plotting on one object model.
- It reduces divergence between saved artifacts and runtime behavior.
- It makes external template overrides behave the same as freshly fitted templates.

Alternatives considered:
- Keep custom labeling while only changing the saved file format. Rejected because it leaves a behavior split between what is saved and what is actually used.
- Generate topomaps from stored arrays without constructing a `ModKMeans` object. Rejected because it reimplements functionality already provided by `pycrostates`.

### Decision: Surface template override on the EEG stage, not as a separate command
The public staged workflow will remain the same, but the EEG stage will gain an explicit template-file input, for example a `--template-fif` style option, so users can swap the active template set without creating a parallel command.

Rationale:
- Template replacement is a variation of EEG state generation, not a separate workflow branch.
- It preserves the staged CLI shape while exposing the needed override behavior.
- It keeps downstream stages unchanged because they continue to consume the same cache locations.

Alternatives considered:
- Add a dedicated `import-eeg-template` command. Rejected because it increases command sprawl for a single-stage variation.
- Hide override support in code-only configuration. Rejected because user-controlled template selection should be explicit at the workflow surface.

## Risks / Trade-offs

- [External template file uses incompatible channels or montage] -> Validate channel-name compatibility against the shared 11-channel montage and the restored 19-channel EEG representation before prediction and fail with a clear error.
- [Switching to `ModKMeans.predict()` changes labels relative to the current custom correlation implementation] -> Update tests around segmentation outputs and make the algorithm change explicit in the change notes.
- [Existing cached `.npz` artifacts become stale or confusing] -> Define `.fif` as the only canonical EEG model cache for the updated branch and stop reading the legacy `.npz` path in the new workflow.
- [Native topomap rendering may require channel location completeness] -> Keep the current montage-restoration path as the prerequisite for fitting, loading, and plotting EEG templates.

## Migration Plan

1. Update the EEG stage contract so the model artifact path resolves to a `.fif` cluster file.
2. Add model load/save helpers around `ModKMeans.save()` and `pycrostates.io.read_cluster()`.
3. Introduce template-file override handling in the EEG stage entry point while keeping downstream cache paths stable for labels.
4. Replace the current matrix-style microstate report with a `ModKMeans.plot()` export path.
5. Update tests and README examples to reflect the new artifact format and override usage.

Rollback strategy:
- Revert to the previous `.npz`-based model helper and custom plotting path. No raw data migration is required because the change only affects staged artifacts.

## Open Questions

- Whether the EEG stage should copy an external template file into the cache root for provenance, or record only the source path plus generated labels.
- Whether the CLI should expose only `--template-fif` or also a configuration-file field for repeatable batch runs.
- Whether cluster renaming or reordering against a curated external template should be documented as part of this change or deferred until a later usability pass.
