## Context

The final figures in `results/figs/` have become the authoritative manuscript layout:

- `fig1.pdf`: EEG microstate and SEEG global-field state identification, plus Yeo17 archetype brain maps.
- `fig2.pdf`: SEEG archetype loading, patient support, dwell-time contrasts, assignment similarity, and transition probabilities.
- `fig3.pdf`: EEG-SEEG spatial similarity, conditional preference, switching, fine-lag synchrony, and subject peak effects.
- `fig4.pdf`: seizure-stage versus IDE-A baseline state-dynamic changes.
- `figs1.pdf`: SEEG electrode/touchpoint and Yeo17 coverage support.
- `figs2.pdf`: SEEG field-state model-order evaluation.

The current manuscript outline still reflects an older seven-main-figure plan, and the current supplementary statistics R Markdown still maps to older manually assembled figure filenames such as `fig1.archetype_brain_maps.pdf`. The R Markdown already has useful building blocks: source CSV validation, table registration, CSV side-table writing, and Excel workbook writing. The change should preserve those strengths while updating the mapping and output contract to match the finalized figure set.

## Goals / Non-Goals

**Goals:**
- Make `docs/科研路线与论文大纲_改进3.md` a figure-driven manuscript outline that discusses the study around the final `fig1`-`fig4` and `figs1`-`figs2` evidence chain.
- Keep the outline scientifically coherent: Figure 1 establishes state extraction, Figure 2 validates SEEG archetypes, Figure 3 interprets EEG-SEEG synchrony, Figure 4 extends the state space to seizure stages, and supplementary figures document coverage/model-order support.
- Update `scripts/10_supplementary_figure_statistics_tables.Rmd` so final figure PDFs are the required figure inputs.
- Export one Excel workbook per final figure, with one sheet per labeled panel or subfigure.
- Keep individual CSV side tables and a manifest for traceability.

**Non-Goals:**
- Do not regenerate or modify the final PDF/AI figure artwork in `results/figs/`.
- Do not rerun core EEG/SEEG analysis, state extraction, archetype fitting, or coupling analyses.
- Do not infer numerical values by parsing the visual PDF/SVG artwork.
- Do not change Python package APIs.

## Decisions

### Decision 1: Treat `results/figs/fig说明.txt` as the narrative guide, not as a machine-parsed source of truth

The outline rewrite should use the finalized figure descriptions and panel order in `fig说明.txt`. The implementation should not depend on fragile text parsing of Chinese prose. Instead, maintain an explicit panel registry in the R Markdown script with stable figure file names, panel labels, descriptions, and source CSV families.

Alternative considered: parse `fig说明.txt` dynamically. This would be brittle because the captions are prose, line wrapping is inconsistent, and panel order can be edited for writing without preserving machine-readable structure.

### Decision 2: Use one canonical panel registry for both CSV/manifest and workbook output

The R Markdown should register every generated or skipped panel-level table with:

- figure file
- figure label
- panel label
- sheet name
- table title/caption
- source CSV path(s)
- output CSV path
- notes

The Excel workbooks should be generated from this registry so workbook contents and the manifest cannot drift.

Alternative considered: write workbooks as a separate post-processing step over emitted CSV files. This adds another source of mapping truth and makes skipped optional panels harder to audit.

### Decision 3: Sheet names should be panel-centered

Each workbook sheet should correspond to a subfigure/panel, using names such as `Fig1A`, `Fig1B`, `Fig2C`, `FigS1D`, and `FigS2A`. If a panel requires multiple related tables, the preferred implementation is to combine them into one sheet with section markers or use stable suffixes only when one-sheet-per-panel would make the data unreadable.

Alternative considered: keep `table_id` sheet names. That is less aligned with the user's requested supplement structure and forces readers to look up panel-table mapping in the manifest.

### Decision 4: Supplementary figure statistics are first-class outputs

The table workflow should include `figs1.pdf` and `figs2.pdf` rather than only the four main figures. S1 should draw from maintained electrode/touchpoint and Yeo17 coverage CSVs in `artifacts/manual/maintext_validation/`; S2 should draw from model-order CSVs in the same family.

Alternative considered: omit supplementary figures from the table workflow and document them manually. That would leave the final supplement without the requested per-panel data audit trail.

## Risks / Trade-offs

- [Risk] Some final visual panels are illustrative and do not have direct inferential statistics. -> Mitigation: write descriptive support tables where source CSVs exist, and register explicit notes for panels without inferential tests.
- [Risk] A panel may naturally require multiple source tables. -> Mitigation: use a panel sheet with clear section labels or a deterministic suffix while keeping the manifest explicit.
- [Risk] Existing artifact directories contain multiple historical runtime hashes. -> Mitigation: keep `runtime_hash` as a parameter and require source files with the selected hash for hash-specific outputs.
- [Risk] Excel sheet names have a 31-character limit and restricted characters. -> Mitigation: sanitize and uniquify sheet names while keeping panel labels visible in the sheet contents and manifest.
- [Risk] Some current OpenSpec main specs are older-format documents. -> Mitigation: this change only creates delta specs for relevant capabilities and does not require broad spec-format migration.
