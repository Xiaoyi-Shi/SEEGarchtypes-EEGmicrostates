## MODIFIED Requirements

### Requirement: Exploratory analyses SHALL be limited to the retained manuscript framework
The exploratory analysis layer SHALL expose only the retained manuscript-facing SEEG field-state analyses together with the supplementary GFP/global, GFP-controlled, and SEEG-to-EEG switching follow-ups explicitly used by the paper-focused workflow, SHALL keep model-order evaluation as the retained supplementary support branch, and SHALL remove lagged global or other exploratory variants that are not part of the retained manuscript framework.

#### Scenario: User inspects exploratory analysis choices
- **WHEN** a user requests help for the exploratory coupling entry point
- **THEN** the system SHALL expose `field-state-coupling`, `field-state-model-order-evaluation`, `field-state-archetypes`, `archetype-conditioned-eeg-topography`, `fine-lag-field-state-coupling`, `gfp-global-coupling`, `peak-gfp-global-coupling`, `gfp-controlled-microstate`, `gfp-controlled-transition`, `field-state-to-eeg-switching`, and `gfp-controlled-field-state-to-eeg-switching`
- **AND** the help surface SHALL NOT expose `lagged-gfp-global-coupling` or retired non-paper exploratory analyses

#### Scenario: Retained exploratory outputs are exported for downstream paper tooling
- **WHEN** retained paper-core or supplementary exploratory caches exist for the selected analysis state
- **THEN** the export layer SHALL write only the corresponding manuscript-ready tables and manifest metadata for those retained analyses
- **AND** the maintained Python package SHALL not be required to render the corresponding figures
