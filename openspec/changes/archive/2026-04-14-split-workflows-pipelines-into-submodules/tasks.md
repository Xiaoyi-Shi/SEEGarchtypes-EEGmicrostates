## 1. Workflow Package Restructuring

- [x] 1.1 Create a responsibility-based module layout under `src/seeg_eegmicrostates/workflows/` for shared helpers, retained staged workflows, retained exploratory workflows, and paper export
- [x] 1.2 Extract shared workflow constants, branch/path helpers, and reusable artifact utilities out of `pipelines.py` into the new internal modules without changing runtime behavior

## 2. Retained Workflow Migration

- [x] 2.1 Move retained staged workflow entry points into the new module layout and keep `seeg_eegmicrostates.workflows` re-exporting the same public functions
- [x] 2.2 Move retained exploratory workflow stages and the exploratory dispatcher into dedicated modules aligned with the maintained analysis surface
- [x] 2.3 Move paper table export and manifest generation into a dedicated export module, and delete legacy report/render workflow glue that no longer belongs in the maintained package

## 3. Cleanup And Verification

- [x] 3.1 Remove or quarantine retired workflow branches so they do not define first-class module boundaries in the refactored package
- [x] 3.2 Update workflow and CLI tests to validate the stable public imports and retained behavior after the refactor
- [x] 3.3 Run `uv run pytest` and fix any regressions introduced by the workflow split
