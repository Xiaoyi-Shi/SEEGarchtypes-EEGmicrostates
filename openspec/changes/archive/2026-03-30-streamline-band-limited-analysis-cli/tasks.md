## 1. Public CLI Restructuring

- [x] 1.1 Replace the branch-centric public CLI with a staged `1-40 Hz` command set for index preparation, EEG states, SEEG networks, activity effects, connectivity effects, and report rendering
- [x] 1.2 Remove or demote legacy public commands for `main` EEG, HFA coupling, and cross-modal overlap so they no longer define the primary public workflow
- [x] 1.3 Update command help text and user-facing naming so connectivity is presented as the primary downstream stage and activity as the supplemental downstream stage

## 2. Shared Staged Artifacts

- [x] 2.1 Refactor workflow orchestration so EEG state generation is a standalone reusable `1-40 Hz` stage with stable caches
- [x] 2.2 Refactor workflow orchestration so SEEG Yeo17 network signal generation is a standalone reusable `1-40 Hz` stage with stable caches
- [x] 2.3 Ensure downstream stages reuse the staged EEG and SEEG caches instead of recomputing upstream work when only analysis methods or statistics change

## 3. Downstream Analyses

- [x] 3.1 Implement the staged band-limited activity-effects workflow and persist subject/group-level supplemental outputs
- [x] 3.2 Rework the staged band-limited connectivity-effects workflow so method-specific outputs remain distinct while sharing the same upstream artifacts
- [x] 3.3 Remove the requirement for band-limited SEEG microstate overlap outputs from the primary public workflow and clean up any report or cache paths that only support that legacy branch

## 4. Reports, Tables, and Validation

- [x] 4.1 Update report rendering so figures and Excel tables are produced from the staged activity and connectivity outputs with clear primary/supplemental labeling
- [x] 4.2 Revise automated tests to cover the new staged CLI, shared-cache reuse, and the retirement of legacy public commands
- [x] 4.3 Update README and related user documentation to reflect the streamlined `1-40 Hz` workflow and its staged command order
