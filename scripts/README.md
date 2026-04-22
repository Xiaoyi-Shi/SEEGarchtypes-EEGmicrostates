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

## Peak Segment Export Tool

Use `scripts/export_seeg_peak_segment.py` when you want a one-off inspection bundle for a specific bipolar SEEG time range. The script reads a cropped FIF segment, computes the retained SEEG field peak trace, marks detected peaks, and writes:

- a channel-by-sample matrix CSV/XLSX where the first column is `row_name`
- a standardized channel-by-sample matrix CSV/XLSX using the selected channel normalization (`zscore` by default)
- appended derived rows such as `time_sec`, `relative_time_ms`, `peak_metric_value`, `spatial_std_raw`, `rms_raw`, and `is_peak_sample`
- a peak summary table
- a `channel_layout` table that records the exported `Yeo17` grouping used for plotting when `Atlas.tsv` is available
- waveform images in both `PNG` and `SVG` with a dedicated top-row `peak_trace` line plot, `Yeo17` group labels on the left, bipolar channel labels on the right, and detected peaks overlaid
- standardized waveform images in both `PNG` and `SVG` using the same layout and labels

The `SVG` export keeps labels as editable text nodes (`svg.fonttype=none`), so titles, axes, and channel labels remain directly editable in Adobe Illustrator instead of being converted to outlines.

Example:

```powershell
uv run python scripts/export_seeg_peak_segment.py `
  --seeg-path datas/data_01_seeg/sub-01/seeg_bipolar_raw.fif `
  --start-sec 12.0 `
  --end-sec 14.0 `
  --patient-id sub-01 `
  --output-dir artifacts/manual/seeg_peak_segments
```

The default output directory is `artifacts/manual/seeg_peak_segments/`.

If the input FIF lives inside the standard patient folder layout, the script automatically looks for the neighboring `MNI/Atlas.tsv` and orders the exported rows by `Yeo17`. When at least two bipolar channels have valid same-network `Yeo17` assignments, the script drops `Unmapped` channels from the export and from the waveform plot. You can also pass `--atlas-path` explicitly.

## Patient Archetype Loading Export Tool

Use `scripts/export_patient_archetype_loading_table.py` when you want a one-off wide table with one row per `patient_id x archetype`, patient-level `Yeo17` loadings, and retained field-state summary metrics such as occupancy and mean dwell time.

Example:

```powershell
uv run python scripts/export_patient_archetype_loading_table.py --runtime-hash 97411c0ec4
```

Without `--runtime-hash`, the script chooses the newest cached archetype assignment file under `artifacts/cache/coupling/`. The default output directory is `artifacts/manual/patient_archetype_tables/`, and the script writes both `CSV` and `XLSX`.

## Archetype Brain Map Plot Tool

Use `scripts/plot_archetype_yeo17_mean_maps.py` when you want to read an exported patient-archetype table and render the four mean `Yeo17` archetype maps by directly writing values into the `Yeo2011` `17-network` atlas and then projecting that atlas to an `fsaverage` surface.

Example:

```powershell
uv run python scripts/plot_archetype_yeo17_mean_maps.py `
  --input-table artifacts/manual/patient_archetype_tables/patient_archetype_yeo17_summary_97411c0ec4.csv `
  --output-dir artifacts/manual/archetype_brain_maps `
  --atlas-thickness thick `
  --surf-mesh fsaverage6 `
  --min-support 1
```

The script writes:

- per-archetype summary tables with mean loadings and support counts
- one `NIfTI` map per archetype in direct `Yeo2011 17-network` volume space
- one cortical `PNG` per archetype after direct `Yeo17` surface projection
- one additional high-resolution cortical `PNG` per archetype for screenshots
- one stitched `2x2` `PNG` summary panel for the standard renders
- one single-column high-resolution `PNG` summary panel for the high-resolution renders

The script no longer goes through `Schaefer` or `ENIGMA Toolbox`. It uses `nilearn.datasets.fetch_atlas_yeo_2011(n_networks=17, thickness=...)`, writes each archetype's mean network values back into the true `Yeo2011` label image, and projects that label image to the requested `fsaverage` mesh with `nearest_most_frequent` sampling so the displayed boundaries stay aligned with the `Yeo17` atlas rather than a secondary parcel atlas.

## Archetype Brain Map R Markdown

Use `scripts/03_patient_archetype_yeo17_ggseg_maps.Rmd` when you want a pure `R`/`ggseg` rendering path that reads the exported patient-archetype `CSV`, averages each `Yeo17` loading across patients within archetype, and draws a four-panel `ggsegYeo2011` cortical figure.

Example:

```powershell
Rscript -e "rmarkdown::render('scripts/03_patient_archetype_yeo17_ggseg_maps.Rmd', params=list(input_csv='artifacts/manual/patient_archetype_tables/patient_archetype_yeo17_summary_97411c0ec4.csv', output_dir='artifacts/manual/archetype_brain_maps'))"
```

The document writes:

- one `SVG` per archetype using the `ggsegYeo2011::yeo17()` atlas
- one stitched `SVG` summary panel
- one explicit `CSV` mapping table from project `Yeo17` shorthand (`VisCent`, `DefaultA`, etc.) to `ggseg` regions (`17Networks_1` .. `17Networks_17`)
- one `CSV` of mean loadings
- one long-format summary `CSV`
- one support-count `CSV`

The document expects `ggseg >= 2.0`, `ggsegYeo2011 >= 2.0`, and `svglite`. If the atlas package is missing, install it with:

```powershell
Rscript -e "install.packages('ggseg', repos='https://cloud.r-project.org')"
Rscript -e "install.packages('svglite', repos='https://cloud.r-project.org')"
Rscript -e "remotes::install_github('ggseg/ggsegYeo2011', upgrade='never')"
```

## Archetype Parameter Statistics R Markdown

Use `scripts/04_patient_archetype_parameter_statistics.Rmd` when you want descriptive statistics plots for patient-level archetype parameters such as `occupancy`, `mean_dwell_ms`, `assignment_similarity`, `n_peak_maps`, and `Yeo17` coverage counts.

Example:

```powershell
Rscript -e "rmarkdown::render('scripts/04_patient_archetype_parameter_statistics.Rmd', params=list(input_csv='artifacts/manual/patient_archetype_tables/patient_archetype_yeo17_summary_97411c0ec4.csv', output_dir='artifacts/manual/patient_archetype_statistics'))"
```

The document writes:

- a descriptive summary `CSV`
- a long-format parameter `CSV`
- one combined main-panel `SVG`
- one compositional occupancy `SVG` with one 100% stacked bar per patient
- one paired dwell-time estimation `SVG` with bootstrap confidence intervals versus `Archetype 0`
- one ranked assignment-similarity `SVG`
- one patient-by-archetype parameter heatmap `SVG`
- one `archetype x Yeo17 network` signed loading heatmap `SVG`
- one `archetype x Yeo17 network` loading-summary `CSV`

The current styling path depends on `ggdist`, `ggtext`, `paletteer`, `patchwork`, `ggrepel`, and `svglite`.

## SEEG Archetype and EEG Microstate Relationship R Markdown

Use `scripts/05_seeg_archetype_eeg_microstate_relationship.Rmd` when you want relationship plots between group SEEG archetypes and EEG microstates using the exported archetype-conditioned EEG tables.

Example:

```powershell
Rscript -e "rmarkdown::render('scripts/05_seeg_archetype_eeg_microstate_relationship.Rmd', params=list(report_root='artifacts/runs/20260412_140500/reports', runtime_hash='97411c0ec4', output_dir='artifacts/manual/archetype_eeg_microstate_relationship'))"
```

The document writes:

- one combined relationship-panel `SVG`
- one `SEEG archetype x EEG microstate` template-similarity heatmap `SVG`
- one `SEEG archetype x EEG microstate` state-preference heatmap `SVG`
- one fine-lag coupling curve `SVG`
- one subject-level peak-lag/effect `SVG` with anonymized subject table output
- one archetype-transition to EEG-switching heatmap `SVG`
- cleaned summary `CSV` files used by the plots

The current styling path matches the archetype parameter statistics document and depends on `ggdist`, `ggtext`, `paletteer`, `patchwork`, and `svglite`.

## EEG Microstate Overview Export and R Markdown

Use `scripts/export_eeg_microstate_overview.py` when you want to export standalone EEG microstate clustering topographies and subject-level EEG microstate parameters from cached EEG labels.

Example:

```powershell
uv run python scripts/export_eeg_microstate_overview.py --runtime-hash 97411c0ec4 --output-dir artifacts/manual/eeg_microstate_overview
```

The script writes:

- one Python-rendered cluster-topography `SVG` panel and one `PNG` companion
- one `SVG` per EEG microstate topography
- template values and interpolated topomap grid `CSV` files for R rendering
- anonymized subject-level parameter `CSV`
- long-format parameter `CSV`
- group-level parameter summary `CSV`
- group transition-matrix `CSV`
- one representative 19-channel EEG waveform segment `CSV`
- one segment-level EEG GFP trace and GFP peak table `CSV`

Use `scripts/06_eeg_microstate_overview.Rmd` to integrate those outputs into one styled EEG microstate overview figure.

Example:

```powershell
Rscript -e "rmarkdown::render('scripts/06_eeg_microstate_overview.Rmd', params=list(input_dir='artifacts/manual/eeg_microstate_overview', runtime_hash='97411c0ec4', output_dir='artifacts/manual/eeg_microstate_overview'))"
```

The document writes one combined overview `SVG` plus separate `SVG` panels for EEG microstate topographies, parameter distributions, within-participant coverage composition, the EEG microstate transition matrix, and a representative 19-channel EEG waveform with GFP peak markers. Its visual style matches the SEEG archetype statistics and relationship figures.

## Maintained Supplementary Figure Inputs

`scripts/02_supplementary_figures.Rmd` expects retained supplementary tables such as:

- `gfp_global_coupling`
- `peak_gfp_global_coupling`
- `gfp_controlled_microstate`
- `gfp_controlled_transition`
- `field_state_model_order_subject`
- `field_state_model_order_group`

The field-state model-order figure family supports the manuscript statement that retained `K=4` remains the main-text default because fit, gain, stability, and interpretability collectively support it better than a single elbow heuristic.
