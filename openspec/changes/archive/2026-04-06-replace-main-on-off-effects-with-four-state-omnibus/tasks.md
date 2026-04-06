## 1. Statistical scaffolding

- [x] 1.1 Add subject-level four-state summary builders for main activity and main connectivity outputs.
- [x] 1.2 Add group-level omnibus and pairwise post-hoc statistics helpers for within-subject four-state analyses.
- [x] 1.3 Define new cache/report artifact stems and table schemas for main-workflow profiles, omnibus results, and post-hoc results.

## 2. Main activity workflow

- [x] 2.1 Replace the main activity stage subject summaries so they persist `patient x region x microstate` four-state profiles instead of `on/off` effect rows.
- [x] 2.2 Update the main activity stage to write separate group-level omnibus and pairwise post-hoc outputs and return those artifact paths.

## 3. Main connectivity workflow

- [x] 3.1 Replace the main connectivity stage subject summaries so they persist `patient x method x region_a x region_b x microstate` four-state profiles instead of `state/off-state` effect rows.
- [x] 3.2 Update the main connectivity stage to write separate method-specific omnibus and pairwise post-hoc outputs and return those artifact paths.

## 4. Reports, docs, and verification

- [x] 4.1 Update report rendering and plotting so the main workflow exports omnibus and post-hoc figures and Excel tables for activity and connectivity.
- [x] 4.2 Update README and processing-flow documentation to describe the new main-workflow statistics and output families.
- [x] 4.3 Update and extend tests to cover the new subject schemas, group-level omnibus/post-hoc outputs, report discovery, and cache reuse behavior.
