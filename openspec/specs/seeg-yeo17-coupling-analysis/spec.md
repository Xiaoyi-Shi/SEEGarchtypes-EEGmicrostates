## REMOVED Requirements

### Requirement: IDE_A bipolar SEEG is summarized as network-level HFA
**Reason**: The focused public workflow no longer centers Yeo17 analysis on HFA summaries. The mainline now operates on `1-40 Hz` Yeo17 network signals shared by both activity and connectivity stages.
**Migration**: Replace HFA-first downstream use with the staged `1-40 Hz` SEEG network generation step.

### Requirement: Microstate-network coupling effects are produced at subject and group level
**Reason**: The original requirement described a single HFA-centered coupling product. The focused workflow now separates Yeo17 activity effects and Yeo17 connectivity effects, with connectivity treated as the primary downstream product.
**Migration**: Use the new activity-effects stage for supplemental network-strength outputs and the new connectivity-effects stage for primary network-pair results.

### Requirement: IDE_A bipolar SEEG SHALL be summarized as band-limited Yeo17 network signals
**Reason**: The primary public workflow is switching from Schaefer/Yeo17 network staging to `AAL3` anatomical region staging using the atlas labels already present in each patient `Atlas.tsv`.
**Migration**: Regenerate staged SEEG outputs using the `AAL3` region workflow defined by `seeg-aal3-coupling-analysis`.

### Requirement: State-conditioned Yeo17 activity effects SHALL be produced as supplemental outputs
**Reason**: Supplemental downstream effects in the public workflow will now be interpreted over `AAL3` anatomical regions rather than Yeo17 functional networks.
**Migration**: Recompute the activity-effects stage against staged `AAL3` region signals and use the new `AAL3` activity summaries for reporting.

### Requirement: State-conditioned Yeo17 connectivity effects SHALL be produced as the primary outputs
**Reason**: Primary downstream connectivity in the public workflow will now be interpreted over `AAL3` region pairs rather than Yeo17 network pairs.
**Migration**: Recompute the connectivity-effects stage against staged `AAL3` region signals and use the new `AAL3` connectivity outputs for reporting.
