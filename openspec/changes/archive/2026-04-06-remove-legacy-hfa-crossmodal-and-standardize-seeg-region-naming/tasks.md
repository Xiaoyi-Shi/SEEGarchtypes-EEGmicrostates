## 1. Public Command And Workflow Surface

- [x] 1.1 Rename the public SEEG staging command from `run-seeg-networks` to `run-seeg-regions` across the CLI entry point, workflow exports, and user-facing help text.
- [x] 1.2 Update the main workflow orchestration and report discovery paths so the maintained region workflow uses only the renamed region stage plus the staged EEG labels.

## 2. Legacy Branch Removal

- [x] 2.1 Delete the HFA staging and HFA coupling branches, including their cache/report paths and any tests that preserve them as maintained behavior.
- [x] 2.2 Delete the old SEEG-microstate cross-modal branch and remove exploratory state-alignment support that depends on that branch.

## 3. Region-Oriented Naming Cleanup

- [x] 3.1 Rename surviving region-based helpers, stems, plotting utilities, QC summaries, and table/report outputs from legacy `network` terminology to `region` terminology where they serve the public AAL3 workflow.
- [x] 3.2 Keep the atlas/parcellation configuration boundary intact while removing broad region/network compatibility fallbacks that no longer serve maintained behavior.

## 4. Verification And Documentation

- [x] 4.1 Update README, workflow documentation, and any OpenSpec-facing references to the renamed region stage and the reduced exploratory method set.
- [x] 4.2 Refresh or replace affected tests so the supported CLI surface, workflow outputs, and renamed region-oriented artifacts are covered, then run the test suite.
