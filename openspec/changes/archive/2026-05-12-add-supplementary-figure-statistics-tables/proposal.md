## Why

The manuscript figures assembled under `results/figs/` now need companion supplementary-material tables that expose the exact data summaries and statistical results behind each labeled panel. The current R Markdown workflows render manuscript figures and side CSVs, but there is no single supplement-facing document that maps the final figure PDFs back to the relevant `artifacts/manual/` inputs and formats the panel statistics as publication-ready three-line tables.

## What Changes

- Add a maintained R Markdown workflow under `scripts/` that produces supplement-facing statistical tables for the final assembled figures without rendering any figures.
- Use `results/figs/fig说明.txt` and the figure-file naming convention to map final figure PDFs to matching `artifacts/manual/<figure-family>/` directories.
- Read existing CSV outputs from `artifacts/manual/` and compute or collect panel-level descriptive statistics, paired contrasts, permutation/FDR summaries, support counts, and stage-minus-IDE-A deltas.
- Render the tables as three-line manuscript tables in an HTML/Word-friendly R Markdown output and write matching audit-ready CSV outputs.
- Fail clearly when a required source table for a requested figure panel is missing, while allowing optional panels to be skipped with an explicit table note when their source family is absent.

## Capabilities

### New Capabilities
- `supplementary-figure-statistics-tables`: Generate supplement-ready three-line tables containing the concrete statistical values and results corresponding to final manuscript figure panels.

### Modified Capabilities
- `scripts-owned-paper-tooling`: Extend special paper-support tooling to include supplement-facing statistical table assembly from exported/cached manual outputs, not only figure rendering.
- `r-markdown-paper-figure-workflow`: Require the new table-only R Markdown workflow to preserve the same manuscript figure family mapping and reproducibility/audit behavior as the figure-rendering workflows.

## Impact

- Affected scripts: a new R Markdown document under `scripts/`, expected to be named along the existing numbered workflow pattern.
- Affected inputs: `results/figs/`, `results/figs/fig说明.txt`, and existing CSV outputs under `artifacts/manual/archetype_brain_maps/`, `artifacts/manual/patient_archetype_statistics/`, `artifacts/manual/archetype_eeg_microstate_relationship/`, and `artifacts/manual/ide_a_vs_seizure_stage_comparison/`.
- Affected outputs: supplement-ready HTML/Word-compatible R Markdown output plus per-table CSV files under a new manual output directory such as `artifacts/manual/supplementary_figure_statistics/`.
- No changes are expected to the Python package API or core analysis computation.
