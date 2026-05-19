## ADDED Requirements

### Requirement: Manuscript outline SHALL be driven by finalized figure panels
The maintained manuscript outline document SHALL organize the paper storyline around the finalized figure files under `results/figs/`, using the main figures and supplementary figures as the primary evidence chain rather than retaining obsolete draft figure numbering.

#### Scenario: User updates the manuscript outline from final figures
- **WHEN** `results/figs/fig1.pdf`, `fig2.pdf`, `fig3.pdf`, `fig4.pdf`, `figs1.pdf`, `figs2.pdf`, and `fig说明.txt` are available
- **THEN** the outline SHALL define the paper structure around those finalized figures and their labeled panels
- **AND** obsolete seven-main-figure planning sections SHALL be removed or rewritten so the outline no longer conflicts with the final figure set

### Requirement: Manuscript discussion SHALL interpret the figure evidence chain
The maintained outline SHALL frame the Results and Discussion around what each finalized figure demonstrates, connecting panel-level observations to the study claims about SEEG global-field states, Yeo17 archetypes, EEG-SEEG synchrony, and seizure-stage state dynamics.

#### Scenario: User reads the updated Results and Discussion plan
- **WHEN** the outline describes the manuscript Results and Discussion sections
- **THEN** each major claim SHALL be explicitly linked to one or more finalized figure panels
- **AND** the discussion SHALL distinguish primary evidence in main figures from coverage, model-order, or validation support in supplementary figures

### Requirement: Manuscript outline SHALL preserve methodological and statistical traceability
The maintained outline SHALL identify the source workflows and statistical outputs that support each final figure so manuscript writing can trace claims back to maintained analysis exports and supplementary statistics tables.

#### Scenario: User checks figure-to-data traceability in the outline
- **WHEN** the outline lists figure content, key claims, or supplementary material
- **THEN** it SHALL name the maintained scripts or artifact families that provide the corresponding data tables
- **AND** it SHALL describe which panels are descriptive, inferential, validation-focused, or illustrative
