## Context

The existing package is organized around staged IDE analysis: `analysis_state` selects `IDE_A` by default or `IDE_S` as an override, `segment/ide_a.py` materializes one rest-like window per patient, `io/index.py` resolves `IDE_*` assets, and the downstream EEG, SEEG, coupling, export, and R Markdown layers consume those patient-level caches. The workbook now also contains manually annotated seizure rows in `annot_info`, where `status1/status2` combine into recording IDs such as `SZ1_CPS` and stage windows are stored in `pre_*`, `LVFA_*`, `SZ_*`, and `post_*` columns.

This change introduces a separate seizure-stage trajectory path rather than overloading `analysis_state`. The seizure data are repeated-event data: one patient can have multiple seizure recordings, each seizure has multiple stages, and paired EEG is not available for every seizure even when SEEG and atlas assets are available.

## Goals / Non-Goals

**Goals:**

- Materialize seizure-stage segments from `datas/info_patient.xlsx` with explicit patient, seizure, seizure type, stage, timing, and QC metadata.
- Index `SZ*_<type>` EEG, reference SEEG, bipolar SEEG, and atlas assets independently from the existing IDE index.
- Project seizure-stage data into the fixed IDE_A-derived EEG microstate and SEEG field-state archetype state space so stages are directly comparable.
- Export stage-level and patient-level EEG microstate, SEEG archetype, Yeo/common-space loading, and EEG-SEEG relationship summaries.
- Preserve separate eligibility for SEEG-only analyses and paired EEG-SEEG analyses.
- Provide R-ready tables and an R Markdown figure workflow that matches the existing manuscript style and SVG output convention.

**Non-Goals:**

- Do not replace the IDE_A paper-core workflow or change its default outputs.
- Do not treat each seizure as an independent group-level subject in inferential summaries.
- Do not perform stage-specific reclustering as the primary analysis.
- Do not add raw patient-derived FIF exports to git.
- Do not require EEG for SEEG-only seizure-stage summaries.

## Decisions

### Use a dedicated seizure workflow instead of extending `analysis_state`

`analysis_state` currently models one IDE state per patient and drives file names such as `IDE_A_eeg.fif`. Seizure stages are a different shape: multiple `SZ*_<type>` recordings per patient and multiple annotated windows per recording. A dedicated workflow keeps the IDE cache contract stable and avoids adding unbounded state names like `SZ1_CPS` to `SUPPORTED_ANALYSIS_STATES`.

Alternative considered: extend `SUPPORTED_ANALYSIS_STATES` with every `SZ*_<type>` value. This was rejected because it would make command-line state choices patient-specific, break the one-row-per-patient cohort assumption, and mix seizure-event logic into IDE indexing.

### Use fixed IDE_A-derived templates for primary stage comparisons

The primary seizure-stage analysis SHALL label EEG and SEEG seizure windows by projecting into a fixed state space derived from the retained IDE_A workflow. This makes `pre`, `LVFA`, `SZ`, and `post` stage comparisons interpretable because state labels remain stable across stages.

Alternative considered: recluster each stage independently. This may be useful as an exploratory supplement, but it is not the primary path because labels would not align cleanly across stages or patients.

### Maintain two eligibility cohorts

The workflow SHALL distinguish a SEEG-stage cohort from a paired EEG-SEEG cohort. Workbook inspection shows SEEG and atlas assets are available for all annotated seizure rows, while EEG is missing for a subset. SEEG-only archetype and Yeo loading summaries should retain all usable seizure recordings; EEG microstate and cross-modal relationship summaries should require paired EEG and SEEG.

Alternative considered: require paired EEG for all seizure-stage outputs. This was rejected because it would discard usable SEEG-stage information without methodological need.

### Treat stage windows as annotated intervals with tolerance-aware QC

Stage timing should be materialized from workbook start/end/duration triples. Tiny floating-point discrepancies at boundaries should be tolerated, but missing, non-positive, inconsistent, or materially mismatched timing values should be surfaced in QC outputs. The workflow should not silently infer corrected seizure-stage windows without recording the issue.

### Export R-ready tables before rendering figures

Python should perform data loading, projection, metric computation, QC, and table export. R Markdown should read those exported tables and render publication-style SVG figures. This follows the current repository split where Python owns analysis caches and R Markdown owns manuscript figure composition.

## Risks / Trade-offs

- [Risk] Seizure-stage signals may be dominated by large-amplitude epileptiform activity rather than canonical resting EEG microstates. → Mitigation: export GFP/amplitude summaries and provide GFP-aware or amplitude-stratified tables where possible.
- [Risk] Repeated seizures from the same patient can inflate sample size if analyzed as independent. → Mitigation: export patient-level summaries and include patient/seizure identifiers for mixed-effects or patient-first statistics.
- [Risk] Missing EEG recordings reduce paired EEG-SEEG power. → Mitigation: keep SEEG-only and paired cohorts separate, and report denominators per metric family.
- [Risk] Workbook timing semantics may encode onset/progression annotations that are not strictly non-overlapping in future data. → Mitigation: preserve raw stage columns, materialize stage rows explicitly, and write QC diagnostics for overlap/order assumptions.
- [Risk] Fixed-template projection can miss seizure-specific states. → Mitigation: state this as a primary-analysis trade-off and leave stage-specific reclustering as a future supplementary extension.

## Migration Plan

1. Add seizure-stage segment and index builders without changing IDE_A/IDE_S paths.
2. Add seizure workflow commands behind new CLI subcommands.
3. Export seizure-stage caches and manual/R-ready tables under seizure-specific stems.
4. Add the R Markdown seizure-stage figure script after the tables are available.
5. Validate the new change with synthetic tests and run existing IDE commands to confirm no regression.

Rollback is straightforward: remove the new seizure commands and generated seizure-specific caches while leaving existing IDE_A/IDE_S outputs untouched.

## Open Questions

- Should `LVFA` always be treated as a distinct stage between `pre` and `SZ`, or should it also be summarized as seizure onset in a combined onset panel?
- Which stage ordering should figures use when a future workbook contains additional phases beyond `pre`, `LVFA`, `SZ`, and `post`?
- Should the first implementation include mixed-effects model fitting, or only export model-ready long tables for downstream statistical analysis?
