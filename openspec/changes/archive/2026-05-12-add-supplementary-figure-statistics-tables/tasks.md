## 1. Workflow Setup

- [x] 1.1 Add `scripts/10_supplementary_figure_statistics_tables.Rmd` with parameters for `fig_dir`, `manual_root`, `runtime_hash`, and `output_dir`.
- [x] 1.2 Source `scripts/_common.R` and add local helpers for repo-relative path resolution, required/optional CSV validation, output directory creation, numeric formatting, and table writing.
- [x] 1.3 Define the final figure-family mapping from `results/figs` filenames to `artifacts/manual` directories and labeled panels from `results/figs/fig说明.txt`.
- [x] 1.4 Add a table registry structure that records table ID, figure file, panel label, source CSV path, output CSV path, caption, and notes.

## 2. Supplement Table Builders

- [x] 2.1 Implement Figure 1 table builders for archetype/Yeo17 map summaries and available descriptive/support tables, with explicit notes for illustrative waveform panels lacking statistical CSV sources.
- [x] 2.2 Implement Figure 2 table builders for Yeo17 loading, coverage/support metrics, dwell-time paired contrasts, assignment-similarity rankings, and transition-probability summaries.
- [x] 2.3 Implement Figure 3 table builders for EEG-SEEG template similarity, state preference, switching effects, fine-lag coupling, and subject peak summaries.
- [x] 2.4 Implement Figure 4 table builders for IDE-A versus seizure-stage primary deltas, complete-case support, duration/projection QC, Yeo17 loading deltas, relationship deltas, seizure-type summaries, and repeated-seizure sensitivity where source CSVs exist.

## 3. Rendering and Exports

- [x] 3.1 Render each supplement table as a three-line table in the R Markdown output using stable captions, row ordering, units, and rounded numeric formatting.
- [x] 3.2 Write one CSV file per generated supplement table under `artifacts/manual/supplementary_figure_statistics/`.
- [x] 3.3 Write `supplementary_figure_statistics_manifest.csv` with figure/panel/source/output traceability for all generated and skipped tables.
- [x] 3.4 Ensure missing required CSVs stop with clear errors and missing optional CSVs generate explicit unavailable-source notes.

## 4. Documentation and Verification

- [x] 4.1 Update `scripts/README.md` with the new table-only supplementary statistics workflow, inputs, outputs, and an example render command.
- [x] 4.2 Render the new R Markdown against the current `results/figs/` and `artifacts/manual/` outputs.
- [x] 4.3 Verify the expected CSV side tables and manifest are written and that no figure files are generated or overwritten.
- [x] 4.4 Run OpenSpec validation/status checks for `add-supplementary-figure-statistics-tables` and confirm the change is apply-ready.
