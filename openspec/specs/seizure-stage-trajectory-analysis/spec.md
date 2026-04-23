## ADDED Requirements

### Requirement: Seizure-stage segments SHALL be materialized from workbook annotations
The system SHALL read seizure rows from the workbook `annot_info` sheet, SHALL combine `status1` and `status2` into a seizure recording identifier, and SHALL materialize one segment row per annotated seizure stage using `pre`, `LVFA`, `SZ`, and `post` timing triples.

#### Scenario: Workbook contains a valid annotated seizure row
- **WHEN** `annot_info` contains a row whose `status1` starts with `SZ` and whose `pre`, `LVFA`, `SZ`, and `post` start/end/duration triples are valid
- **THEN** the system SHALL emit four segment rows with `patient_id`, `seizure_id`, `seizure_type`, `recording_state`, `stage`, `start_sec`, `end_sec`, `duration_sec`, and `usable_segment`
- **AND** the stage rows SHALL preserve the canonical order `pre`, `LVFA`, `SZ`, `post`

#### Scenario: Stage timing has a small floating-point boundary discrepancy
- **WHEN** adjacent stage boundaries differ only within the configured timing tolerance
- **THEN** the system SHALL treat the segment timing as usable
- **AND** the system SHALL retain QC metadata indicating the tolerated discrepancy

#### Scenario: Stage timing is missing or materially inconsistent
- **WHEN** a seizure-stage timing triple is missing, non-positive, or differs beyond the configured tolerance
- **THEN** the system SHALL mark that stage segment unusable
- **AND** the system SHALL write a QC reason that identifies the affected patient, seizure, stage, and timing fields

### Requirement: Seizure recordings SHALL be indexed independently from IDE analysis states
The system SHALL scan patient data directories for seizure recording assets whose names match the workbook-derived `SZ*_<type>` recording identifiers and SHALL resolve EEG, reference SEEG, bipolar SEEG, and atlas paths without modifying IDE_A/IDE_S indexing.

#### Scenario: A seizure recording has paired EEG, SEEG, bipolar SEEG, and atlas assets
- **WHEN** a patient directory contains `ref/<recording_state>_eeg.fif`, `ref/<recording_state>_seeg.fif`, `bipolar/<recording_state>_seeg.fif`, and `MNI/Atlas.tsv`
- **THEN** the seizure index SHALL mark the recording eligible for paired EEG-SEEG stage analysis

#### Scenario: A seizure recording has SEEG assets but no EEG asset
- **WHEN** a patient directory contains reference SEEG, bipolar SEEG, and atlas assets for a seizure recording but lacks the EEG FIF
- **THEN** the seizure index SHALL mark the recording eligible for SEEG-only stage analysis
- **AND** the seizure index SHALL mark it ineligible for EEG microstate and paired EEG-SEEG relationship summaries

#### Scenario: A required SEEG or atlas asset is missing
- **WHEN** a seizure recording lacks bipolar SEEG or atlas assets required for SEEG-stage analysis
- **THEN** the seizure index SHALL record the missing asset
- **AND** the recording SHALL NOT be included in SEEG-stage metric computation

### Requirement: Seizure-stage data SHALL be projected into fixed IDE_A-derived state spaces
The system SHALL use the retained IDE_A-derived EEG microstate template and SEEG field-state archetype/template artifacts as the primary reference state space for labeling seizure-stage windows.

#### Scenario: Fixed IDE_A reference artifacts are available
- **WHEN** the seizure-stage workflow runs and required IDE_A reference templates or archetype artifacts exist
- **THEN** the system SHALL label seizure-stage EEG and SEEG samples by projection/backfitting into those fixed references
- **AND** labels SHALL remain comparable across `pre`, `LVFA`, `SZ`, and `post`

#### Scenario: Required reference artifacts are missing
- **WHEN** the seizure-stage workflow runs without the required IDE_A EEG microstate or SEEG archetype reference artifacts
- **THEN** the workflow SHALL stop with a clear error that identifies the missing artifact and the prerequisite command or output family

#### Scenario: Stage-specific reclustering is not requested
- **WHEN** the primary seizure-stage workflow runs
- **THEN** the system SHALL NOT recluster EEG microstates or SEEG archetypes separately within each seizure stage

### Requirement: Seizure-stage metrics SHALL be exported for EEG, SEEG, and cross-modal summaries
The system SHALL export R-ready long tables and analysis caches that summarize seizure-stage EEG microstate parameters, SEEG archetype parameters, common-space/Yeo loading profiles, and EEG-SEEG relationship metrics.

#### Scenario: EEG data are available for a usable seizure stage
- **WHEN** a usable stage segment belongs to a paired EEG-SEEG eligible recording
- **THEN** the system SHALL export EEG microstate occupancy, duration, occurrence, transition, GFP, and quality metrics keyed by patient, seizure, seizure type, and stage

#### Scenario: SEEG data are available for a usable seizure stage
- **WHEN** a usable stage segment belongs to a SEEG-stage eligible recording
- **THEN** the system SHALL export SEEG archetype occupancy, duration, transition, assignment-similarity, and common-space loading metrics keyed by patient, seizure, seizure type, and stage

#### Scenario: Paired EEG and SEEG labels are available for a usable seizure stage
- **WHEN** aligned EEG microstate labels and SEEG archetype labels exist for the same stage window
- **THEN** the system SHALL export EEG-SEEG relationship summaries including archetype-conditioned EEG microstate preference, coupling strength, and lag or synchrony diagnostics when available

### Requirement: Seizure-stage summaries SHALL preserve repeated-event structure
The system SHALL keep patient, seizure, seizure type, and stage identifiers in all stage-level outputs and SHALL provide patient-level summaries suitable for patient-first statistics.

#### Scenario: Multiple seizures exist for the same patient
- **WHEN** the workflow computes group-facing seizure-stage summaries
- **THEN** the system SHALL retain seizure-level rows for traceability
- **AND** the system SHALL export patient-level aggregates so downstream statistics do not treat repeated seizures as independent patients

#### Scenario: Stage denominators differ across metric families
- **WHEN** EEG, SEEG, and paired relationship metrics have different eligible recording counts
- **THEN** the exported summaries SHALL include metric-family denominators and eligibility labels
- **AND** the report-ready outputs SHALL not merge SEEG-only and paired EEG-SEEG cohorts without explicit cohort labels

### Requirement: Seizure-stage QC SHALL be exported with analysis outputs
The system SHALL emit QC tables for seizure-stage workflow inputs and derived outputs, including timing validity, asset availability, channel coverage, stage duration, and metric-family eligibility.

#### Scenario: The seizure-stage workflow completes
- **WHEN** any seizure-stage analysis outputs are written
- **THEN** the system SHALL also write QC tables that allow users to identify excluded recordings, excluded stages, tolerated timing discrepancies, missing EEG assets, and missing SEEG or atlas assets

#### Scenario: No usable paired EEG-SEEG seizure stages are available
- **WHEN** SEEG-only stages exist but no paired EEG-SEEG stages pass eligibility checks
- **THEN** the workflow SHALL still allow SEEG-only exports
- **AND** it SHALL clearly report that EEG microstate and cross-modal relationship outputs were not produced because paired EEG eligibility was empty
