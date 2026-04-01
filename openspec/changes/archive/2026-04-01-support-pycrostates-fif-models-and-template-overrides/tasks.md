## 1. EEG Model Artifacts

- [x] 1.1 Replace the custom EEG microstate model save/load helpers with native `pycrostates` `.fif` cluster save/load helpers.
- [x] 1.2 Update the EEG state stage to persist the canonical staged model artifact as a `ModKMeans` `.fif` file.
- [x] 1.3 Add whole-template override handling so the EEG stage can load an external `.fif` model instead of fitting a new template set.
- [x] 1.4 Validate external template channel compatibility against the shared 11-channel montage or the restored 19-channel EEG representation and raise a clear error on mismatch.

## 2. Labeling And Reports

- [x] 2.1 Switch EEG microstate labeling to use the active `ModKMeans` object for prediction while preserving the existing tabular label output shape.
- [x] 2.2 Update the public EEG stage interface to expose a template-file override input without adding a new top-level command.
- [x] 2.3 Replace the current matrix-style EEG template figure path with a `ModKMeans.plot()` topographic export in the report stage.
- [x] 2.4 Ensure the report stage renders the EEG topographic figure whenever the staged `.fif` model artifact is available.

## 3. Verification And Documentation

- [x] 3.1 Update automated tests for the new `.fif` artifact format, template override workflow, compatibility failures, and report output behavior.
- [x] 3.2 Update README and command usage examples to describe the staged `.fif` model artifact and the template override path.
- [x] 3.3 Run the relevant test suite and confirm the staged EEG/report workflow remains compatible with downstream activity and connectivity stages.
