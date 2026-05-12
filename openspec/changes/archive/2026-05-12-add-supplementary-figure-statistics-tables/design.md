## Context

The repository already separates analysis computation from manuscript assembly. Python workflows under `src/` export cached statistics and manuscript-facing tables, while `scripts/` contains R Markdown documents that render figures and write supporting CSV files under `artifacts/manual/`. The final assembled figure PDFs currently live under `results/figs/` and are described by `results/figs/fig说明.txt`. Their names correspond to existing manual-output directories:

- `fig1.archetype_brain_maps.pdf` -> `artifacts/manual/archetype_brain_maps/`
- `fig2.patient_archetype_statistics.pdf` -> `artifacts/manual/patient_archetype_statistics/`
- `fig3.archetype_eeg_microstate_relationship.pdf` -> `artifacts/manual/archetype_eeg_microstate_relationship/`
- `fig4.ide_a_vs_seizure_stage_comparison.pdf` -> `artifacts/manual/ide_a_vs_seizure_stage_comparison/`

Those directories already contain most of the CSV sources needed for supplementary tables: Yeo17 archetype loading summaries, archetype parameter summaries, EEG-SEEG relationship matrices, fine-lag and subject-peak summaries, and IDE-A versus seizure-stage patient/group delta outputs. The missing piece is a table-only supplement workflow that gathers these outputs, computes small additional summaries where needed, and renders publication-ready three-line tables.

## Goals / Non-Goals

**Goals:**
- Add a maintained R Markdown document under `scripts/` that generates supplementary statistical tables for the assembled manuscript figures.
- Preserve the final figure-to-source mapping from `results/figs/` to `artifacts/manual/<figure-family>/`.
- Produce table-only output: HTML/Word-friendly three-line tables plus CSV copies of every generated supplement table.
- Include panel-level table coverage for the currently assembled figures and their labeled subpanels described in `results/figs/fig说明.txt`.
- Fail clearly for missing required tables and record explicit notes for optional or unavailable panel families.

**Non-Goals:**
- Do not regenerate or modify manuscript figures.
- Do not rerun Python analysis pipelines or change core analysis code.
- Do not replace the existing figure-specific R Markdown workflows.
- Do not infer results from PDFs, SVG graphics, or Illustrator files; tables must come from exported CSV sources or deterministic summaries of those sources.

## Decisions

### 1. Add a new numbered table-only R Markdown workflow

Create a new script, expected to follow the existing numbered naming pattern, such as `scripts/10_supplementary_figure_statistics_tables.Rmd`. It will source `scripts/_common.R`, resolve repo-relative paths, validate inputs, and write outputs under `artifacts/manual/supplementary_figure_statistics/` by default.

Alternative considered:
- Extend each existing figure R Markdown file to emit supplement tables. Rejected because the user needs a single supplement-facing document organized around the final assembled PDFs, and spreading this logic across figure scripts would make manuscript assembly harder to audit.

### 2. Treat CSV exports as the statistical source of truth

The workflow should read existing CSV outputs from `artifacts/manual/` and, where useful, compute final table summaries in R from those CSVs. It should not parse PDFs/SVGs or inspect graphical objects. This keeps the tables reproducible and tied to analysis outputs rather than to visual layout files.

Alternative considered:
- Parse final figure PDFs or SVG labels to infer panel values. Rejected because final layout files are presentation artifacts and do not contain complete statistical provenance.

### 3. Use a manifest of generated supplement tables

The R Markdown should write a `supplementary_figure_statistics_manifest.csv` listing table IDs, figure/panel mapping, source CSV files, output CSV files, and short notes. This mirrors existing manifest patterns and lets manuscript authors track which supplementary table supports which figure panel.

Alternative considered:
- Only render tables inside the R Markdown output. Rejected because journal supplements often need standalone tables, and CSV side files make later checking and copy-editing easier.

### 4. Generate three-line tables with existing R dependencies where possible

The workflow should render tables with `knitr::kable` or an already available table package if present, using a booktabs/three-line-table style for PDF/Word/HTML compatibility. It should keep numeric formatting explicit and stable, including units such as percentage points, milliseconds, and similarity/coupling scales.

Alternative considered:
- Add a new dependency solely for table styling. Rejected unless the current R environment lacks a reasonable existing table path, because this workflow is a formatting and organization layer over existing outputs.

### 5. Scope panel coverage to the current assembled figures first

Initial table coverage should prioritize the four current PDFs in `results/figs/`:

- Figure 1: EEG overview, SEEG waveform/loadings, and archetype/Yeo17 template summaries where source tables exist.
- Figure 2: Yeo17 archetype loading, coverage/support metrics, dwell-time paired contrasts, assignment-similarity/rank summaries, and transition probabilities.
- Figure 3: template similarity, state preference, switching, fine-lag coupling, and subject peak summaries.
- Figure 4: IDE-A versus seizure-stage coverage/mean-duration deltas, primary effects, and relationship/transition tendency changes.

If a panel's exact plotted data is not available in `artifacts/manual/<figure-family>/`, the workflow should either use the closest maintained CSV source from another manual directory, such as `maintext_validation`, or emit a clearly labeled unavailable-source note rather than silently inventing a table.

## Risks / Trade-offs

- [Risk] The final assembled figure panels may not exactly match the source CSV names because the PDFs were manually arranged. -> Mitigation: encode a clear figure/panel-to-source table mapping and write it to the output manifest.
- [Risk] Some panels, especially waveform/example panels, may be illustrative rather than statistical. -> Mitigation: generate support/audit tables for those panels when available and mark non-statistical panels as descriptive examples.
- [Risk] Numeric values may be duplicated across existing source CSVs with slightly different formatting. -> Mitigation: prefer the CSV written by the figure-family R Markdown that produced the panel; only fall back to `maintext_validation` or report exports when the figure-family directory lacks the source.
- [Risk] Three-line table rendering can differ across HTML, Word, and PDF outputs. -> Mitigation: keep CSV outputs as the authoritative values and use simple `knitr::kable`/booktabs-compatible rendering in the R Markdown.

## Migration Plan

1. Implement the new R Markdown workflow under `scripts/`.
2. Add default parameters for `fig_dir`, `manual_root`, `runtime_hash`, and `output_dir`.
3. Build helper functions for path resolution, required CSV validation, numeric formatting, and table/manifest writing.
4. Add per-figure table builders that read current manual-output CSVs and create supplement table data frames.
5. Render the document once against the existing `results/figs/` and `artifacts/manual/` outputs and verify that all required table CSVs plus the manifest are written.
6. Update `scripts/README.md` with the new table workflow and command example during implementation.

## Open Questions

- Whether the final journal submission should use HTML, Word, or PDF as the primary rendered supplement-table document.
- Whether Figure 1 waveform/example panels require raw sample-level tables in the supplement, or whether support and source-file audit tables are sufficient.
