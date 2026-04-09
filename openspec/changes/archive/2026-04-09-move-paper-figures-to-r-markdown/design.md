## Context

The repository currently has a paper-focused analysis surface, but the maintained Python package still owns both scientific computation and manuscript plotting. The accepted workflow writes staged analysis outputs, transforms them into manuscript-facing bundles, and still depends on Python `viz` modules plus a `render-reports` command to generate final figures.

That design is now mismatched with the project direction in [科研路线与论文大纲_改进.md](F:/uv_env/SEEG-EEGmicrostates/docs/科研路线与论文大纲_改进.md). The paper storyline is stable enough that the engineering boundary can be redrawn:
- Python should own preprocessing, state derivation, inference, and standardized table export.
- R Markdown should own figure composition and statistical graphics in `scripts/`.
- The maintained public surface should become table-first and figure-agnostic on the Python side.

The main constraints are:
- The accepted paper workflow already depends on stable `main_tables` / `supplementary_tables` naming and manifest metadata.
- Existing specs still require Python-side figure bundles and figure grammar.
- Historical exploratory branches and old plot code may still exist internally, but the maintained contract should no longer depend on them.

## Goals / Non-Goals

**Goals:**
- Reframe the maintained Python workflow around categorized scientific table exports and manifest metadata.
- Define a maintained R Markdown figure workflow under `scripts/` for paper figures derived from exported tables.
- Remove Python plotting from the maintained contract and retire Python `viz` modules from the public paper workflow.
- Keep paper-core and supplementary outputs clearly separated for both table export and downstream figure rendering.
- Preserve traceability from any R-generated figure back to the staged run, export manifest, and source tables.

**Non-Goals:**
- Changing the scientific conclusions, analysis families, or retained paper storyline.
- Redesigning subject-level or group-level statistics beyond what is needed to stabilize exported schemas.
- Introducing a Python-driven plot wrapper around R; the maintained design treats Python export and R rendering as separate steps.
- Preserving backward compatibility for Python-generated manuscript figures.

## Decisions

### Decision: Python becomes table-first and stops owning manuscript figure rendering
Python will retain staged analysis, manuscript-facing table classification, and manifest generation only. Final paper figures will no longer be rendered from Python.

Rationale:
- This matches the user's desired workflow and removes a large maintenance surface from the package.
- It separates scientific data generation from presentation code, which is easier to validate and easier to rewrite for a manuscript.

Alternatives considered:
- Keep Python plotting and add R as an optional second renderer. Rejected because it preserves duplicated figure logic.
- Shell out from Python to `Rscript` or `quarto`. Rejected for the initial contract because it couples runtime dependencies and complicates failure handling.

### Decision: The report/export stage will produce categorized tables plus manifests, not final Python figure bundles
The maintained export stage will write stable `main_tables`, `supplementary_tables`, and `manifests` directories. Figure directories remain manuscript-facing outputs, but they are populated by the R Markdown workflow rather than by Python.

Rationale:
- Categorized tables are the durable scientific contract.
- The manuscript directory layout can remain recognizable while the rendering responsibility moves out of Python.

Alternatives considered:
- Replace all report directories with a new `r_inputs` tree. Rejected because it would create unnecessary migration churn in docs and paper references.

### Decision: R Markdown scripts in `scripts/` are a first-class maintained workflow
The repository will maintain paper-facing R Markdown scripts under `scripts/` that consume manifests and categorized tables to generate main and supplementary figures.

Rationale:
- The user explicitly wants R-based figure generation.
- R Markdown is well suited to manuscript graphics and figure assembly.

Alternatives considered:
- Raw `.R` scripts only. Rejected because the project wants a reproducible manuscript-oriented figure workflow rather than ad hoc plotting snippets.

### Decision: Stable table schemas must become stricter, analysis-family-specific contracts
Each retained analysis family will export a stable schema with consistent column order, analysis identifiers, support diagnostics, and significance metrics so that R Markdown code does not need cache-specific reshaping logic.

Rationale:
- The current Python figure layer implicitly carries reshaping and labeling logic that would otherwise be lost.
- Moving figures to R only works if the table contract is explicit and stable.

Alternatives considered:
- Let R scripts read raw cache tables and reshape freely. Rejected because it would move too much fragile pipeline logic out of the tested Python workflow.

### Decision: Public CLI/report semantics will shift from `render-reports` to paper export
The maintained public surface should describe Python's responsibility accurately. The public export command will become a paper-table export stage rather than a Python rendering stage.

Rationale:
- A command named `render-reports` is misleading if Python no longer renders figures.
- The new command contract should reflect the actual boundary between computation and presentation.

Alternatives considered:
- Keep the old command name but silently stop producing figures. Rejected because it obscures the breaking change and makes docs harder to read.

## Risks / Trade-offs

- [Risk] Existing figure-oriented tests and docs will break when Python stops producing figure files.  
  Mitigation: migrate tests and docs around table exports, manifests, and the R Markdown workflow in the same change.

- [Risk] R Markdown may become under-specified if the table schemas are not strict enough.  
  Mitigation: define analysis-family-specific export schemas and require manifests to map tables to figure panels.

- [Risk] Users may still rely on historical Python `viz` code internally.  
  Mitigation: keep the spec language explicit that this is a breaking change to the maintained public workflow while preserving historical caches as archival artifacts.

- [Risk] The pipeline could become harder to run end-to-end if Python and R steps are not clearly linked.  
  Mitigation: define a documented `export -> render` sequence and a manifest-driven input contract for the R scripts.

## Migration Plan

1. Define the new paper export contract: categorized tables, manifests, and stable schemas for each retained analysis family.
2. Add the maintained R Markdown scripts in `scripts/` and document how they consume the export bundles.
3. Update CLI and pipeline orchestration so Python exports paper tables instead of rendering figures.
4. Remove Python plotting code from the maintained workflow and retire `src/seeg_eegmicrostates/viz/` from the public contract.
5. Rewrite tests and docs around the new table-first plus R Markdown workflow.

Rollback would consist of restoring the old Python `render-reports` behavior, but the intended direction of this change is explicitly breaking rather than dual-path compatibility.

## Open Questions

- Should the new public command be a renamed export command or a repurposed `render-reports` alias during migration?
- Should the maintained R workflow render to `reports/main_figures` and `reports/supplementary_figures`, or to a separate figure root under `results/`?
- Should the canonical table format be XLSX only, CSV only, or paired CSV plus XLSX for each manuscript-facing table?
