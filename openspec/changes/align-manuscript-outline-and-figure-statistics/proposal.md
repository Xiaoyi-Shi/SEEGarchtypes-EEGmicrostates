## Why

The finalized manuscript figures under `results/figs/` now define the paper story more directly than the older draft outline. The manuscript outline and supplementary statistics workflow need to be realigned so discussion, figure captions, and audit tables all follow the final `fig1`-`fig4` and `figs1`-`figs2` figure set.

## What Changes

- Rewrite `docs/科研路线与论文大纲_改进3.md` into a figure-driven manuscript plan centered on the finalized main and supplementary figures in `results/figs/`.
- Update the manuscript discussion structure so each major result section interprets the evidence presented in the corresponding final figure panel.
- Update `scripts/10_supplementary_figure_statistics_tables.Rmd` to use the final figure files `fig1.pdf`, `fig2.pdf`, `fig3.pdf`, `fig4.pdf`, `figs1.pdf`, and `figs2.pdf`.
- Extend the supplementary statistics workflow so each final figure receives one Excel workbook, with each subfigure/panel written to a separate sheet.
- Preserve CSV side tables and a manifest that maps each figure, panel, sheet, source CSV, output CSV, and interpretation note.
- Add supplementary figure coverage for SEEG electrode/Yeo17 density and model-order evaluation panels where maintained source CSV outputs exist.

## Capabilities

### New Capabilities
- `figure-driven-manuscript-outline`: Defines the maintained paper-outline document as a figure-centered manuscript plan aligned to finalized figure panels and discussion claims.

### Modified Capabilities
- `supplementary-figure-statistics-tables`: Require the table-only R Markdown workflow to target finalized `results/figs` figure files and export one workbook per figure with one sheet per subfigure/panel.

## Impact

- Affected documentation:
  - `docs/科研路线与论文大纲_改进3.md`
- Affected scripts:
  - `scripts/10_supplementary_figure_statistics_tables.Rmd`
- Affected generated outputs:
  - `artifacts/manual/supplementary_figure_statistics/*.csv`
  - `artifacts/manual/supplementary_figure_statistics/*.xlsx`
  - `artifacts/manual/supplementary_figure_statistics/supplementary_figure_statistics_manifest.csv`
- No Python package API or core EEG/SEEG analysis behavior changes are intended.
