## 1. Figure Inventory And Outline Alignment

- [x] 1.1 Read `results/figs/fig说明.txt` and confirm final panel mapping for `fig1.pdf`, `fig2.pdf`, `fig3.pdf`, `fig4.pdf`, `figs1.pdf`, and `figs2.pdf`.
- [x] 1.2 Rewrite `docs/科研路线与论文大纲_改进3.md` around the finalized four-main-figure and two-supplementary-figure evidence chain.
- [x] 1.3 Update Results and Discussion sections so each major claim is linked to specific finalized figure panels.
- [x] 1.4 Update methods, supplementary material, execution priorities, and code-mapping notes so they match the finalized figure set and maintained scripts.

## 2. Supplementary Statistics Workflow Remapping

- [x] 2.1 Update `scripts/10_supplementary_figure_statistics_tables.Rmd` figure registry to require final files under `results/figs/`: `fig1.pdf`, `fig2.pdf`, `fig3.pdf`, `fig4.pdf`, `figs1.pdf`, and `figs2.pdf`.
- [x] 2.2 Replace the old panel map with final figure and panel labels aligned to `fig说明.txt`.
- [x] 2.3 Update existing Figure 1-4 table builders so their `figure_file`, `panel_label`, captions, and notes match the finalized panels.
- [x] 2.4 Add supplementary Figure S1 table builders for SEEG electrode/touchpoint MNI density, Yeo17 patient-network coverage, and network contact summaries from maintained main-text validation exports.
- [x] 2.5 Add supplementary Figure S2 table builders for `K=2..7` model-order fit, incremental gain, and split-half stability from maintained model-order exports.

## 3. Excel Workbook Output

- [x] 3.1 Refactor workbook writing so each final figure receives one `.xlsx` workbook named from the final figure file.
- [x] 3.2 Ensure each labeled panel/subfigure is written to a distinct sheet using sanitized panel-centered sheet names such as `Fig1A`, `Fig2C`, `FigS1D`, and `FigS2A`.
- [x] 3.3 Preserve CSV side-table exports for every generated panel table.
- [x] 3.4 Extend the manifest with workbook path, sheet name, source CSV path, output CSV path, status, and notes for generated and skipped panels.

## 4. Verification And Documentation

- [x] 4.1 Render `scripts/10_supplementary_figure_statistics_tables.Rmd` against current `results/figs/` and `artifacts/manual/` inputs.
- [x] 4.2 Verify that one Excel workbook exists for each final figure with panel-level sheets and that no figure image files are generated or overwritten.
- [x] 4.3 Verify representative CSV outputs and the manifest contain correct final figure filenames, panel labels, source paths, workbook paths, and sheet names.
- [x] 4.4 Run OpenSpec validation for `align-manuscript-outline-and-figure-statistics` and summarize any remaining optional-source gaps.
