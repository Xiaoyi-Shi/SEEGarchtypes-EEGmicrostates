from __future__ import annotations

from seeg_eegmicrostates.eeg import load_microstate_model as _load_microstate_model

from . import core as _core
from . import exploratory as _exploratory
from . import export as _export
from . import shared as _shared

_run_exploratory_field_state_archetypes_stage_impl = _exploratory.run_exploratory_field_state_archetypes_stage

_eligible_rows = _core._eligible_rows
_load_patient_eeg_topography_trace = _core._load_patient_eeg_topography_trace
_exploratory_branch = _shared._exploratory_branch
_field_state_artifact_branch = _shared._field_state_artifact_branch
_retained_field_state_artifact_branch = _shared._retained_field_state_artifact_branch
align_eeg_gfp_and_field_state_labels = _shared.align_eeg_gfp_and_field_state_labels
build_state_transition_table = _shared.build_state_transition_table
preprocess_eeg_recording = _shared.preprocess_eeg_recording
save_raw_fif = _shared.save_raw_fif
_ensure_exploratory_event_tables = _exploratory._ensure_exploratory_event_tables
_ensure_seeg_field_state_artifacts = _exploratory._ensure_seeg_field_state_artifacts
_ensure_seeg_field_state_archetype_artifacts = _exploratory._ensure_seeg_field_state_archetype_artifacts
_ensure_seeg_global_metric_artifacts = _exploratory._ensure_seeg_global_metric_artifacts
load_microstate_model = _load_microstate_model


def _sync_core_hooks() -> None:
    _core._eligible_rows = _eligible_rows
    _core.preprocess_eeg_recording = preprocess_eeg_recording
    _core.save_raw_fif = save_raw_fif


def build_index_artifacts(*args, **kwargs):
    return _core.build_index_artifacts(*args, **kwargs)


def build_seizure_stage_index_artifacts(*args, **kwargs):
    from . import seizure as _seizure

    return _seizure.build_seizure_stage_index_artifacts(*args, **kwargs)


def run_eeg_microstate_branch(*args, **kwargs):
    _sync_core_hooks()
    return _core.run_eeg_microstate_branch(*args, **kwargs)


def run_eeg_states_stage(*args, **kwargs):
    _sync_core_hooks()
    return _core.run_eeg_states_stage(*args, **kwargs)


def run_seeg_band_limited_region_branch(*args, **kwargs):
    _sync_core_hooks()
    return _core.run_seeg_band_limited_region_branch(*args, **kwargs)


def run_seeg_regions_stage(*args, **kwargs):
    _sync_core_hooks()
    return _core.run_seeg_regions_stage(*args, **kwargs)


def _sync_exploratory_hooks() -> None:
    _sync_core_hooks()
    _exploratory.run_eeg_states_stage = run_eeg_states_stage
    _exploratory.run_seeg_regions_stage = run_seeg_regions_stage
    _exploratory._eligible_rows = _eligible_rows
    _exploratory._load_patient_eeg_topography_trace = _load_patient_eeg_topography_trace
    _exploratory._ensure_exploratory_event_tables = _ensure_exploratory_event_tables
    _exploratory._ensure_seeg_field_state_artifacts = _ensure_seeg_field_state_artifacts
    _exploratory._ensure_seeg_field_state_archetype_artifacts = _ensure_seeg_field_state_archetype_artifacts
    _exploratory._ensure_seeg_global_metric_artifacts = _ensure_seeg_global_metric_artifacts
    _exploratory.run_exploratory_field_state_archetypes_stage = run_exploratory_field_state_archetypes_stage
    _exploratory.load_microstate_model = load_microstate_model


def run_exploratory_field_state_archetypes_stage(*args, **kwargs):
    _sync_exploratory_hooks()
    return _run_exploratory_field_state_archetypes_stage_impl(*args, **kwargs)


def run_exploratory_coupling_stage(*args, **kwargs):
    _sync_exploratory_hooks()
    return _exploratory.run_exploratory_coupling_stage(*args, **kwargs)


def export_paper_tables(*args, **kwargs):
    return _export.export_paper_tables(*args, **kwargs)


def run_seizure_stage_analysis(*args, **kwargs):
    from . import seizure as _seizure

    return _seizure.run_seizure_stage_analysis(*args, **kwargs)


def export_seizure_stage_tables(*args, **kwargs):
    from . import seizure as _seizure

    return _seizure.export_seizure_stage_tables(*args, **kwargs)
