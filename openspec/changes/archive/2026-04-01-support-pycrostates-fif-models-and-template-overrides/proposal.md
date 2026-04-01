## Why

The current EEG microstate stage saves a custom `.npz` model artifact and renders a matrix-style template image, which diverges from the native `pycrostates` workflow and makes template reuse less direct. This change is needed now to standardize model persistence on `pycrostates` `.fif` cluster files, allow whole-template replacement with a user-supplied template file, and generate the expected group topographic map outputs.

## What Changes

- Replace the staged EEG microstate model artifact with a standard `pycrostates` `ModKMeans` `.fif` cluster solution.
- Allow the EEG state stage to skip fitting and reuse a user-supplied `pycrostates` template `.fif` file as the active model for labeling.
- Align EEG microstate labeling and report rendering with the loaded or fitted `ModKMeans` object instead of the current custom model dictionary path.
- Export group EEG microstate topographic figures using `ModKMeans.plot()` rather than the current template-by-channel heatmap.
- Update tests and documentation to reflect the new model artifact format, override path, and report output expectations.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `eeg-microstate-processing`: EEG state generation requirements change to persist reusable `pycrostates` `.fif` model artifacts, support whole-template file overrides, and export group microstate topographic plots.
- `analysis-cli-orchestration`: The staged EEG/report workflow requirements change to expose template-file override behavior and render EEG microstate figures from native `pycrostates` model artifacts.

## Impact

Affected areas include EEG microstate fitting/labeling code, workflow orchestration, report rendering, tests, and README usage guidance. The change alters the staged model artifact format from custom `.npz` files to standard `pycrostates` `.fif` cluster files and adds a public template override path for the EEG state stage.
