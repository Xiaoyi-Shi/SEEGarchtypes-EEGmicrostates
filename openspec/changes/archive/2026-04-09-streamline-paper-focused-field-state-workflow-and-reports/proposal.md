## Why

The codebase has accumulated multiple exploratory branches and cache-mirroring reports around earlier hypotheses, but the strongest current evidence supports a much narrower paper storyline centered on SEEG global-field states, group archetypes, archetype-conditioned EEG topography, and native `4 ms` near-zero-lag synchrony. The current public workflow and report surface are broader than the scientific narrative, which makes the implementation heavier than necessary and makes manuscript-grade figures and tables harder to produce consistently.

## What Changes

- Narrow the maintained paper-facing workflow to the field-state line: staged EEG, subject-level SEEG field-state derivation, group archetypes, archetype-conditioned EEG topography, and fine-lag synchrony.
- Keep GFP-informed global coupling and SEEG-led switching as supplementary follow-ups rather than co-equal headline analyses.
- Retire or remove redundant region-signal exploratory branches and legacy field-state diagnostics that do not support the paper-focused field-state narrative, while leaving non-paper legacy capabilities outside this cleanup scope. **BREAKING**
- Replace cache-shaped report exports with manuscript-ready figure and table bundles that separate main figures/tables from supplementary outputs, use stable naming, and preserve effect sizes, significance, and support diagnostics in a paper-oriented layout. **BREAKING**
- Simplify CLI help, report discovery, cache/report routing, and documentation so the supported workflow reflects the paper narrative instead of the full historical exploratory surface.

## Capabilities

### New Capabilities
- `manuscript-ready-report-export`: paper-oriented figure/table bundles, numbering, naming, and output organization for main and supplementary results

### Modified Capabilities
- `analysis-cli-orchestration`: narrow the maintained exploratory workflow and report/export surface to the paper-focused field-state pipeline and manuscript-oriented outputs
- `exploratory-cross-modal-coupling`: reduce the maintained exploratory surface to the field-state/archetype/fine-lag core plus explicitly supplementary GFP and switching follow-ups, and retire region-signal exploratory branches from the maintained public surface
- `gfp-informed-global-cross-modal-coupling`: clarify that GFP-informed global analyses are supplementary follow-ups with manuscript-ready supplementary outputs
- `seeg-global-field-state-coupling`: keep the field-state branch focused on the subject-level state derivation and coupling outputs needed by the paper storyline
- `seeg-global-field-state-archetypes`: tighten archetype outputs around common-space summaries and manuscript-grade support/loading tables
- `seeg-archetype-conditioned-eeg-topography`: standardize conditioned EEG topography, template-similarity, state-preference, and fine-lag outputs for publication-ready reporting

## Impact

- Affected code: `src/seeg_eegmicrostates/workflows/`, `src/seeg_eegmicrostates/coupling/`, `src/seeg_eegmicrostates/viz/`, `src/seeg_eegmicrostates/cli.py`
- Affected outputs: report figure/table names, report directory organization, and exploratory analysis exposure
- Affected docs: README, workflow documentation, and manuscript-facing research notes
- Breaking surface: some region-signal exploratory analyses, legacy field-state diagnostics, and cache-mirroring reports will be removed, hidden, or renamed in favor of the paper-focused workflow
