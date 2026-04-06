## Context

The repository now has a focused staged pipeline that can produce reusable EEG microstate labels and reusable SEEG regional signals for the same `IDE_A` cohort and analysis windows. What is still missing is an exploratory analysis layer for testing richer EEG-SEEG coupling hypotheses than the current state-conditioned activity and connectivity contrasts.

This change is cross-cutting because it affects orchestration, cache design, alignment logic, subject-level summary generation, group-level statistics, and reporting. It also depends on the staged SEEG baseline exposing regional signals as reusable upstream artifacts, so the exploratory layer should be implemented on top of the current region-based pipeline direction rather than the older Yeo17-only framing.

## Goals / Non-Goals

**Goals:**
- Add an explicit exploratory coupling workflow that supports five optional analysis families: EEG event-triggered SEEG activity, EEG-SEEG microstate alignment, EEG event-triggered SEEG connectivity, windowed occupancy/dwell coupling, and EEG state-transition coupling.
- Reuse existing staged EEG labels and staged SEEG regional signals rather than recomputing upstream inputs.
- Standardize exploratory outputs as reusable subject-level caches, group-level summary tables, and report artifacts so each method can be rerun independently.
- Preserve the current focused default workflow as the main public path while making exploratory analyses available on demand.

**Non-Goals:**
- Replace the existing activity-effects and connectivity-effects stages as the primary public outputs.
- Introduce decoding or encoding models in this change.
- Rework EEG preprocessing, EEG microstate fitting, or the staged SEEG regional signal generation baseline.
- Make atlas choice or exploratory hyperparameters fully free-form beyond the explicit method options needed for the initial workflows.

## Decisions

### 1. Exploratory analyses will be exposed through an explicit opt-in orchestration path

The focused default workflow remains `build-index -> run-eeg-states -> run-seeg-networks -> run-activity-effects -> run-connectivity-effects -> render-reports`. Exploratory coupling analyses will be run explicitly through a separate orchestration entry point rather than becoming mandatory downstream stages.

Why:
- The current default workflow is already stable and intentionally narrow.
- The exploratory methods have different runtime costs and scientific roles, so they should remain opt-in.
- This avoids forcing every user to generate large additional caches and figures they may not need.

Alternatives considered:
- Add every exploratory method to the default workflow.
  Rejected because it would make the public path slower and less focused.
- Expose each exploratory method only as an internal helper with no orchestration entry point.
  Rejected because it would make the analyses harder to rerun and validate consistently.

### 2. All exploratory methods will share a subject-first staging pattern

Each exploratory analysis will first write a subject-level cache that captures the method-specific summaries, then optionally derive group-level statistics and report artifacts from those staged subject outputs.

Why:
- The existing pipeline already follows a staged-cache pattern that supports partial reruns.
- Subject-first outputs make it easier to inspect failures, recompute group statistics, and compare methods.
- The five methods differ in feature extraction, but they share the same high-level execution pattern.

Alternatives considered:
- Write only final group-level tables.
  Rejected because it makes debugging and reruns unnecessarily expensive.
- Keep each method’s outputs completely ad hoc.
  Rejected because it would fragment the exploratory layer and make reporting inconsistent.

### 3. Event-based methods will derive reusable EEG event tables before summarizing SEEG data

EEG event-triggered activity, event-triggered connectivity, and transition coupling will all start from derived EEG onset/offset/transition event tables built from staged EEG microstate labels.

Why:
- The event extraction logic is shared across multiple exploratory methods.
- Reusing event tables reduces duplicated alignment code and makes window choices explicit.
- Event tables create a natural audit trail for onset, offset, and transition definitions.

Alternatives considered:
- Recompute event boundaries independently inside each method.
  Rejected because it invites subtle inconsistencies between analyses.

### 4. SEEG microstate alignment remains exploratory and branch-specific

The SEEG microstate alignment method will fit microstates from staged SEEG regional signals only when the exploratory alignment analysis is requested. It will not restore SEEG microstates as a required product of the default staged workflow.

Why:
- This preserves the narrowed public workflow while still making state-to-state correspondence testable.
- SEEG microstate fitting is method-specific and should not gate unrelated analyses.

Alternatives considered:
- Make SEEG microstate fitting a default staged output again.
  Rejected because it would reverse the intentionally focused public workflow.

### 5. Group-level exploratory summaries will enforce minimum subject support

All exploratory group summaries will require configurable minimum subject support before reporting region- or region-pair-level effects, overlaps, or transition summaries.

Why:
- The current downstream results can produce visually prominent rows with very low subject support.
- Exploratory methods increase the number of comparisons and the risk of unstable summaries.
- Enforcing minimum support at the group-summary stage reduces noise before FDR correction and reporting.

Alternatives considered:
- Report every available group row and rely only on FDR.
  Rejected because it produces low-value summaries and weakens interpretation.

### 6. Exploratory reports will integrate with the existing report stage when caches exist

Once exploratory caches exist, the report stage will export the corresponding exploratory figures and tables without requiring a separate reporting command. Running exploratory analyses remains opt-in; rendering their reports is automatic when their caches are present.

Why:
- This preserves a single reporting surface for all cached results.
- It keeps exploratory orchestration focused on computation while `render-reports` remains the export layer.

Alternatives considered:
- Add a separate exploratory reporting command.
  Rejected because it duplicates report-export logic and fragments the output surface.

## Risks / Trade-offs

- [The proposal bundles five exploratory methods into one change] -> Use shared event, cache, and statistics scaffolding so the methods can still be implemented and tested incrementally.
- [Event windows, lag scans, and transition definitions can materially affect results] -> Persist method parameters in cache identity and keep default windows explicit in the workflow configuration.
- [Exploratory connectivity can be computationally expensive] -> Reuse staged regional signals, stage subject-level summaries, and allow reruns by method and connectivity metric.
- [Group-level outputs may remain sparse after minimum-support filtering] -> Treat this as a valid scientific outcome and prioritize stable summaries over inflated result counts.
- [This change depends on the region-based SEEG baseline] -> Implement it only after the current AAL3-oriented staging change is applied or archived into the accepted spec baseline.

## Migration Plan

1. Add exploratory orchestration and shared cache/report conventions.
2. Add shared EEG event extraction and subject/group summary helpers.
3. Implement exploratory methods in priority order: event-triggered activity, SEEG microstate alignment, event-triggered connectivity, windowed coupling, transition coupling.
4. Extend reporting so exploratory outputs are exported when their caches exist.
5. Add tests for cache reuse, method-specific outputs, and group-level minimum-support filtering.

Rollback:
- Remove the exploratory orchestration entry point and ignore the exploratory caches and reports.
- Because the exploratory layer writes distinct artifacts and does not replace the default staged outputs, rollback does not require mutating the existing focused workflow caches.

## Open Questions

- Should the exploratory orchestration be a single command with an `--analysis` selector, or several method-specific commands? The design assumes a single explicit orchestration path, but the exact CLI shape can still be finalized during implementation.
