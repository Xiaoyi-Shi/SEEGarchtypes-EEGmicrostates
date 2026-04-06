## 1. Exploratory orchestration and shared scaffolding

- [x] 1.1 Add an explicit exploratory coupling orchestration entry point and method-selection interface that reuses the existing staged index, EEG, and SEEG inputs.
- [x] 1.2 Add shared cache naming, parameter hashing, and report-discovery conventions for exploratory subject-level, group-level, and figure outputs.
- [x] 1.3 Add shared EEG event and transition extraction helpers plus minimum-subject filtering utilities for exploratory group summaries.

## 2. Event-triggered activity and state alignment

- [x] 2.1 Implement event-locked SEEG regional activity summaries from staged EEG microstate events and persist subject-level and group-level outputs.
- [x] 2.2 Restore exploratory SEEG microstate fitting from staged SEEG regional signals and persist EEG-SEEG alignment plus lagged-overlap summary outputs.
- [x] 2.3 Add figures and exported tables for event-locked activity and exploratory state-alignment results.

## 3. Event-triggered connectivity and windowed coupling

- [x] 3.1 Implement event-locked SEEG region-pair connectivity summaries for supported connectivity methods and persist method-specific subject-level and group-level outputs.
- [x] 3.2 Implement windowed EEG occupancy/dwell summaries aligned with windowed SEEG regional metrics and persist the resulting slow-timescale coupling outputs.
- [x] 3.3 Add figures and exported tables for event-locked connectivity and windowed coupling analyses.

## 4. Transition coupling

- [x] 4.1 Implement EEG state-transition event tables and transition-locked SEEG regional or region-pair summary outputs stratified by source and destination state.
- [x] 4.2 Add group-level transition summaries, minimum-support filtering, and report exports for transition coupling outputs.

## 5. Verification and documentation

- [x] 5.1 Add or update tests for exploratory CLI/orchestration behavior, cache reuse, and method-specific output schemas.
- [x] 5.2 Add focused tests for event-triggered, alignment, windowed, and transition summary helpers together with minimum-subject filtering behavior.
- [x] 5.3 Update README or other user-facing workflow documentation for the exploratory coupling methods and run the relevant test suite before closing the change.
