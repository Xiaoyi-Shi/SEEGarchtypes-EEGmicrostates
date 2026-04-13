# Scripts Workflow

`scripts/` is the home for plotting and special paper-support tooling.

The maintained boundary is:

1. The Python package under `src/` performs analysis, caching, and result-table export.
2. `scripts/` consumes exported tables or cached outputs to render figures or run one-off support tools.

## Figure Rendering

Run the staged Python analyses first, then export categorized paper tables and manifests:

```powershell
uv run seeg-eegmicrostates export-paper-tables --seeg-parcellation-name yeo17 --run-id 20260408_131613
```

Render manuscript figures from the exported tables:

```powershell
Rscript -e "rmarkdown::render('scripts/01_main_figures.Rmd', params=list(report_root='artifacts/runs/20260408_131613/reports'))"
Rscript -e "rmarkdown::render('scripts/02_supplementary_figures.Rmd', params=list(report_root='artifacts/runs/20260408_131613/reports'))"
```

Both R Markdown documents read `reports/manifests/paper_report_manifest.csv` or `.xlsx`, validate the standardized table-export contract, and write PNG figures into:

- `reports/main_figures/`
- `reports/supplementary_figures/`

The Python package no longer owns manuscript figure rendering or other special paper-support utilities.

## Maintained Supplementary Figure Inputs

`scripts/02_supplementary_figures.Rmd` expects retained supplementary tables such as:

- `gfp_global_coupling`
- `peak_gfp_global_coupling`
- `gfp_controlled_microstate`
- `gfp_controlled_transition`
- `field_state_model_order_subject`
- `field_state_model_order_group`

The field-state model-order figure family supports the manuscript statement that retained `K=4` remains the main-text default because fit, gain, stability, and interpretability collectively support it better than a single elbow heuristic.
