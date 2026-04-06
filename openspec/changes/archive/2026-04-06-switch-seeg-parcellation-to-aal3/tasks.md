## 1. Configuration and SEEG mapping

- [x] 1.1 Add an explicit SEEG parcellation configuration for `AAL3` and ensure the runtime hash/cache identity changes when the public SEEG atlas changes.
- [x] 1.2 Replace the Yeo17-specific bipolar mapping logic with `AAL3` same-region mapping that uses full `AAL3` labels and treats empty or `N/A` labels as missing.
- [x] 1.3 Update SEEG aggregation and coverage helpers so staged artifacts and summaries use region-oriented semantics instead of Yeo17 network semantics.

## 2. Staged workflow and user-visible outputs

- [x] 2.1 Update the staged SEEG workflow to write and read `AAL3` region mapping, coverage, and band-limited time-series artifacts for downstream activity and connectivity stages.
- [x] 2.2 Update downstream activity, connectivity, and report-generation paths so user-visible outputs describe `AAL3` regions and region pairs while keeping the existing top-level command entry points.
- [x] 2.3 Update CLI help text and README workflow documentation to describe the public SEEG stage as producing `AAL3` region outputs.

## 3. Verification

- [x] 3.1 Replace or extend SEEG mapping tests to cover `AAL3` label handling, same-region bipolar validation, and cache invalidation behavior.
- [x] 3.2 Update CLI, workflow, and report tests to expect `AAL3` region terminology and region-based staged artifacts.
- [x] 3.3 Run `uv run pytest` and verify the staged outputs exercised by the tests no longer depend on Yeo17-specific public artifacts.
