## Context

The maintained paper workflow already derives subject-level SEEG field states with `K=4` and uses those outputs for occupancy, dwell, archetype, and fine-lag analyses. What is missing is a maintained supplementary model-order evaluation that explains why `K=4` remains the manuscript default. The design must stay aligned with the current discovery space: patient-level bipolar peak maps, polarity-invariant template matching, patient-first summaries, and the existing paper export plus R Markdown rendering pipeline.

## Goals / Non-Goals

**Goals:**
- Add a maintained supplementary evaluation of subject-level field-state model order for `K=2..7`
- Quantify model-order support using fit plateau, incremental gain, stability, and interpretability diagnostics
- Export manuscript-ready supplementary tables and manifest rows for the model-order analysis
- Add an R Markdown supplementary figure family that can justify the retained main-text `K=4`

**Non-Goals:**
- Changing the default manuscript field-state count away from `K=4`
- Replacing the current subject-level field-state discovery algorithm
- Reframing archetype discovery or fine-lag synchrony around pooled multi-`K` results
- Treating the model-order figure as a main-text figure family

## Decisions

### Decision: Keep model-order evaluation in the subject-level discovery space
The evaluation will be performed on the same patient-level bipolar peak maps used by the maintained `K=4` field-state workflow, not on Yeo17-projected templates and not on pooled cross-patient peak maps.

Rationale:
- The scientific question is whether the retained subject-level state count is justified
- Cross-patient pooled clustering would change the discovery problem and confound model-order support with coverage heterogeneity
- Using the existing subject-level discovery space preserves compatibility with the current paper storyline

Alternative considered:
- Evaluate `K` after Yeo17 projection. Rejected because it would assess common-space archetypes rather than the retained subject-level field-state model order.

### Decision: Use fit, gain, stability, and occupancy-collapse as the maintained evidence set
The maintained evaluation will summarize candidate `K` values using four diagnostics:
- template-fit summary from the same polarity-invariant matching objective used by discovery
- incremental gain from `K-1` to `K`
- stability across repeated derivations or split subsets
- interpretability diagnostics that flag occupancy collapse or near-empty states

Rationale:
- An elbow-style fit curve alone is not sufficient because fit usually improves monotonically with `K`
- Stability is required to avoid over-interpreting fragile higher-`K` solutions
- Occupancy-collapse diagnostics keep the manuscript claim grounded in interpretable states rather than mathematically valid but biologically thin partitions

Alternative considered:
- Use only a simple elbow plot. Rejected because it is too weak to support a manuscript claim that `K=4` is retained by fit plateau, stability, and interpretability together.

### Decision: Preserve `K=4` as the default paper-core branch and route model-order outputs to supplementary exports
The maintained exploratory and paper export surface will continue to treat `K=4` as the default field-state configuration. The new model-order branch will be supplementary and SHALL not replace or rename existing core field-state outputs.

Rationale:
- The paper-core results and current manuscript-facing outputs are already written around `K=4`
- The requested addition is justification, not a new primary analysis family
- This keeps implementation risk low and preserves reproducibility of the current headline results

Alternative considered:
- Let the model-order branch auto-select a new default `K`. Rejected because it would change the accepted paper storyline and would require re-basing all downstream outputs.

### Decision: Export model-order results as categorized supplementary tables first, with R Markdown owning final figure composition
Python will compute and export stable supplementary tables and manifest metadata for model-order evaluation. The maintained R Markdown workflow will render the final supplementary figure family from those exports.

Rationale:
- This matches the current paper pipeline boundary
- It keeps figure grammar centralized in the R Markdown workflow
- It allows manuscript text and figure assembly to evolve without reopening Python rendering code

Alternative considered:
- Add an ad hoc Python-only diagnostic plot. Rejected because Python plotting has already been retired from the maintained paper workflow.

## Risks / Trade-offs

- [Risk] Higher-`K` solutions may show modest fit improvements that tempt over-interpretation. → Mitigation: require gain and stability summaries alongside fit curves, and phrase the manuscript support as plateau plus interpretability rather than as a single optimality proof.
- [Risk] Stability metrics can vary depending on the exact resampling or repeated-seed procedure. → Mitigation: define one maintained stability workflow and expose its parameters in manifest metadata.
- [Risk] Supplementary figure complexity may dilute the paper if too many diagnostics are shown at once. → Mitigation: keep the primary figure family limited to fit, gain, and stability, with collapse diagnostics routed to a paired table.
- [Risk] Recomputing `K=2..7` for every patient adds runtime. → Mitigation: isolate the branch behind dedicated cache identity and supplementary export paths so it only runs when requested.

## Migration Plan

1. Add a supplementary field-state model-order branch with distinct cache identity.
2. Persist patient-level and group-level model-order summaries for `K=2..7`.
3. Extend paper-table export and manifest generation to classify those outputs as supplementary.
4. Add an R Markdown supplementary figure family that consumes the exported tables.
5. Update manuscript-facing docs to state that `K=4` remains the default and is justified by fit plateau, stability, and interpretability.

Rollback is straightforward: remove the supplementary model-order branch and its export/figure hooks without changing the retained `K=4` paper-core outputs.

## Open Questions

- Whether the maintained stability metric should be repeated-seed agreement, split-half template similarity, or both
- Whether occupancy-collapse should be summarized as minimum occupancy, minimum peak-count support, or both in the primary supplementary table
