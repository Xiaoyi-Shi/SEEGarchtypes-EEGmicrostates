# Paper Figure Workflow

The maintained paper workflow is:

1. Run the staged Python analyses.
2. Export categorized paper tables and manifests:

```powershell
uv run seeg-eegmicrostates export-paper-tables --seeg-parcellation-name yeo17 --run-id 20260408_131613
```

3. Render manuscript figures from the exported tables:

```powershell
Rscript -e "rmarkdown::render('scripts/01_main_figures.Rmd', params=list(report_root='artifacts/runs/20260408_131613/reports'))"
Rscript -e "rmarkdown::render('scripts/02_supplementary_figures.Rmd', params=list(report_root='artifacts/runs/20260408_131613/reports'))"
```

Both R Markdown documents read `reports/manifests/paper_report_manifest.csv` or `.xlsx`, validate the standardized table-export contract, and write PNG figures into:

- `reports/main_figures/`
- `reports/supplementary_figures/`

The Python package no longer owns manuscript figure rendering.
