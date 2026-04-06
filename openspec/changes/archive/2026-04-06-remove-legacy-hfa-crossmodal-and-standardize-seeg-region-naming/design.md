## Context

The active public workflow now stages three things: the `IDE_A` cohort, EEG microstate labels derived from a configured EEG template, and `AAL3` same-region SEEG signals. Despite that, the codebase still contains three older design layers:

- an internal HFA staging and coupling path
- a band-limited SEEG-microstate overlap branch
- a wide compatibility layer that still uses `network` naming even when the public workflow is region-based

Those layers no longer define the maintained analysis path, but they still shape helper names, exploratory method availability, and user-facing command naming. The cleanup must simplify the current workflow without hardcoding the repository into an AAL3-only architecture that would make a future switch back to `Yeo17` unnecessarily expensive.

## Goals / Non-Goals

**Goals:**
- Remove the HFA and old SEEG-microstate cross-modal branches from the maintained workflow.
- Rename the public SEEG staging command to `run-seeg-regions`.
- Make the public AAL3 workflow consistently region-oriented in CLI help, cache/report stems, table columns, plotting helpers, and workflow exports.
- Preserve the existing parcellation configuration knobs so future changes can swap the backend parcellation without reviving misleading legacy naming.

**Non-Goals:**
- Reintroduce `Yeo17` as an active public workflow in this change.
- Redesign the maintained downstream statistics beyond the already accepted four-state omnibus/post-hoc workflow.
- Add a brand-new exploratory replacement for state-alignment in the same change.

## Decisions

### 1. Remove HFA as a maintained internal branch

The HFA staging and coupling path will be deleted rather than left as dormant internal code.

Why:
- It no longer participates in the public CLI.
- It preserves on/off-era subject/group effect code paths that now diverge from the main workflow.
- Leaving it in place keeps old branch semantics alive in cache families and helper naming.

Alternative considered:
- Keep HFA as an undocumented internal utility.
  Rejected because it would continue to preserve obsolete branch assumptions and complicate future refactors.

### 2. Retire the old SEEG-microstate overlap branch instead of keeping a second maintained downstream path

The standalone band-limited SEEG-microstate cross-modal branch will be removed as a maintained workflow path. Exploratory methods that depend on fitting a separate SEEG microstate branch, especially state-alignment, will be removed rather than carried forward under the new region-oriented workflow.

Why:
- The maintained downstream workflow already uses staged EEG labels plus staged SEEG region signals.
- The overlap branch reintroduces a second analysis philosophy with its own cached model and label families.
- Keeping it alongside event-based and windowed exploratory methods blurs what the maintained upstream contract actually is.

Alternative considered:
- Keep the branch but mark it legacy-only.
  Rejected because it would still force the codebase to preserve dual abstractions and duplicate naming support.

### 3. Rename the public SEEG staging command and user-visible artifacts to `region` terminology

The public command becomes `run-seeg-regions`, and user-visible staged artifact/report families will use `region` terminology rather than `network`.

Why:
- The current staging backend is explicitly `AAL3`.
- `run-seeg-networks` is now materially misleading for users.
- Public-facing names should reflect the actual scientific unit being analyzed.

Alternative considered:
- Keep the command name for backward familiarity.
  Rejected because the mismatch is now larger than the convenience.

### 4. Remove the broad `network` compatibility layer, but keep parcellation selection abstract

Helpers, exports, and visualizations will stop carrying `network`/`region` dual fallbacks when they only serve the public AAL3 workflow. At the same time, the configuration-level parcellation identifiers and atlas-column-based mapping entry points will remain, so a future change can reintroduce `Yeo17` or another parcellation as an explicit backend switch.

Why:
- The current compatibility layer is mostly technical debt masquerading as flexibility.
- Future atlas switching should happen through explicit parcellation configuration, not by keeping the entire AAL3 workflow named as if it were still network-based.

Alternative considered:
- Rewrite everything to a fully generic `parcel` terminology now.
  Rejected because the public workflow is explicitly AAL3 today, and a half-completed generic layer would add churn without an immediate consumer.

### 5. Limit this cleanup to maintained workflows and user-visible outputs

The change will focus on CLI, workflows, caches, reports, plots, and tests that describe supported behavior. It will not attempt a repo-wide theoretical renaming of every historical helper if that helper is deleted together with its legacy branch.

Why:
- The goal is to remove obsolete paths and simplify the maintained contract.
- A targeted cleanup is safer than a broad symbolic rename with no remaining behavioral value.

## Risks / Trade-offs

- [Breaking CLI rename] → Mitigation: update README, workflow docs, tests, and report examples in the same change.
- [Loss of state-alignment exploratory outputs] → Mitigation: keep the remaining exploratory methods intact and describe the removal clearly in specs and docs.
- [Future Yeo17 switch could still require another rename pass] → Mitigation: keep `seeg_parcellation_name` and `seeg_parcellation_column` as the actual abstraction boundary instead of preserving misleading `network` wrappers now.
- [Cache/report churn from renamed stems] → Mitigation: treat the rename as an intentional cache break and update render/report discovery logic in one pass.

## Migration Plan

1. Rename the public command surface and workflow exports from `networks` to `regions`.
2. Remove HFA and old SEEG-microstate overlap/state-alignment branches from CLI-accessible and internally maintained paths.
3. Rename surviving region-based helper, cache, report, and plotting interfaces to region terminology.
4. Update docs and tests to the new command names and supported exploratory method set.
5. Regenerate caches and reports under the new stems on the next full workflow run.

Rollback would be a normal code revert; no persistent data migration is required beyond discarding caches created under the new stems if the change is reverted.

## Open Questions

- Whether a future `Yeo17` return should reuse `region` terminology publicly or introduce a more generic `parcel` surface should be decided in a later change, not in this cleanup.
