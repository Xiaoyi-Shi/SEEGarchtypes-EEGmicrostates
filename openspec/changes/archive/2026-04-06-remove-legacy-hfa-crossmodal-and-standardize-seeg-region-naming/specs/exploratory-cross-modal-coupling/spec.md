## REMOVED Requirements

### Requirement: EEG and SEEG microstate sequences SHALL support exploratory alignment summaries
**Reason**: The maintained exploratory workflow is being narrowed to analyses that reuse staged EEG microstate labels plus staged SEEG region signals directly. Keeping a separate SEEG-microstate alignment branch would preserve the same obsolete cross-modal branch abstraction that this change removes elsewhere.
**Migration**: Use the remaining event-locked, windowed, and transition-based exploratory analyses on top of the staged EEG labels and SEEG region signals. If a future change needs state correspondence again, it should reintroduce it as an explicit design rather than as a leftover legacy branch.
