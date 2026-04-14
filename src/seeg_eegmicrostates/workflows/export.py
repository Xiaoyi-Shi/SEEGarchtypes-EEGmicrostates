from __future__ import annotations

from .shared import *

def _paper_asset_path(cfg: AnalysisConfig, *, stem: str, ext: str, bundle: str, kind: str) -> Path:
    subdir_map = {
        ("main", "figure"): _MAIN_FIGURE_SUBDIR,
        ("main", "table"): _MAIN_TABLE_SUBDIR,
        ("supplementary", "figure"): _SUPPLEMENTARY_FIGURE_SUBDIR,
        ("supplementary", "table"): _SUPPLEMENTARY_TABLE_SUBDIR,
    }
    return cfg.report_path(stem, ext=ext, subdir=subdir_map[(bundle, kind)], branch=_PAPER_REPORT_BRANCH)


def _paper_asset_stem(*, bundle: str, kind: str, order: int, label: str, cfg: AnalysisConfig) -> str:
    prefix_map = {
        ("main", "figure"): "figure",
        ("main", "table"): "table",
        ("supplementary", "figure"): "supplementary_figure",
        ("supplementary", "table"): "supplementary_table",
    }
    return f"{prefix_map[(bundle, kind)]}_{order:02d}_{cfg.branch_name(label)}"


def _traceable_dataframe(df: pd.DataFrame, *, family: str, branch: str, source_path: Path | None = None) -> pd.DataFrame:
    traced = df.copy()
    traced.insert(0, "analysis_family", family)
    traced.insert(1, "analysis_branch", branch)
    if source_path is not None:
        traced.insert(2, "source_cache", str(source_path))
    return traced


def _stable_columns(df: pd.DataFrame, ordered: tuple[str, ...]) -> pd.DataFrame:
    columns = [column for column in ordered if column in df.columns]
    remaining = [column for column in df.columns if column not in columns]
    return df.loc[:, [*columns, *remaining]]


def _paper_ready_group_rows(df: pd.DataFrame, *, min_subjects: int) -> pd.DataFrame:
    if "n_subjects" not in df.columns:
        return df.copy()
    filtered = df[df["n_subjects"].fillna(0).astype(float) >= float(min_subjects)].copy()
    return filtered.reset_index(drop=True)


def _finalize_field_state_model_order_subject_table(
    subject_df: pd.DataFrame,
    *,
    candidate_ks: tuple[int, ...],
    retained_k: int,
) -> pd.DataFrame:
    if subject_df.empty:
        return subject_df.copy()
    data = subject_df.copy().sort_values(["patient_id", "n_states"]).reset_index(drop=True)
    data["fit_gain_from_prev_k"] = pd.NA
    grouped = data.groupby("patient_id", sort=False)
    for _, index in grouped.groups.items():
        patient_rows = data.loc[index].sort_values("n_states")
        gain = patient_rows["mean_template_fit"].astype(float).diff()
        data.loc[patient_rows.index, "fit_gain_from_prev_k"] = gain.to_numpy()
    data["fit_gain_from_prev_k"] = pd.to_numeric(data["fit_gain_from_prev_k"], errors="coerce")
    data["k_range"] = f"{candidate_ks[0]}-{candidate_ks[-1]}"
    data["retained_main_text_default"] = data["n_states"].astype(int) == int(retained_k)
    return data


def _append_manifest_row(
    manifest_rows: list[dict[str, object]],
    *,
    cfg: AnalysisConfig,
    bundle: str,
    kind: str,
    order: int,
    family: str,
    label: str,
    analysis_branch: str,
    output_csv_path: Path | None,
    output_xlsx_path: Path | None,
    source_paths: tuple[Path, ...],
    dataframe: pd.DataFrame | None = None,
) -> None:
    min_subject_support = None
    max_subject_support = None
    if dataframe is not None and "n_subjects" in dataframe.columns and not dataframe.empty:
        numeric_support = pd.to_numeric(dataframe["n_subjects"], errors="coerce").dropna()
        if not numeric_support.empty:
            min_subject_support = int(numeric_support.min())
            max_subject_support = int(numeric_support.max())

    parameter_columns = (
        "peak_metric",
        "normalization",
        "n_states",
        "min_duration_ms",
        "k_range",
        "comparison_space",
        "global_metric_label",
        "metric_definition",
        "weighting_strategy",
        "network_scope",
    )
    parameter_summary = None
    if dataframe is not None and not dataframe.empty:
        fragments: list[str] = []
        for column in parameter_columns:
            if column not in dataframe.columns:
                continue
            values = sorted({str(value) for value in dataframe[column].dropna().tolist()})
            if not values:
                continue
            preview = ",".join(values[:4])
            if len(values) > 4:
                preview = f"{preview},..."
            fragments.append(f"{column}={preview}")
        if fragments:
            parameter_summary = "; ".join(fragments)

    manifest_rows.append(
        {
            "run_id": cfg.run_timestamp,
            "analysis_state": cfg.analysis_state,
            "runtime_hash": cfg.runtime_hash,
            "bundle": bundle,
            "asset_kind": kind,
            "bundle_order": order,
            "family": family,
            "label": label,
            "analysis_branch": analysis_branch,
            "output_csv_path": str(output_csv_path) if output_csv_path is not None else "",
            "output_xlsx_path": str(output_xlsx_path) if output_xlsx_path is not None else "",
            "source_caches": ";".join(str(path) for path in source_paths),
            "row_count": 0 if dataframe is None else int(len(dataframe)),
            "column_count": 0 if dataframe is None else int(len(dataframe.columns)),
            "subject_support_column": "n_subjects" if dataframe is not None and "n_subjects" in dataframe.columns else "",
            "min_subject_support": min_subject_support,
            "max_subject_support": max_subject_support,
            "parameter_summary": parameter_summary or "",
        }
    )


def _write_manuscript_table(
    cfg: AnalysisConfig,
    *,
    dataframe: pd.DataFrame,
    bundle: str,
    order: int,
    family: str,
    label: str,
    analysis_branch: str,
    source_paths: tuple[Path, ...],
) -> tuple[Path, Path]:
    stem = _paper_asset_stem(bundle=bundle, kind="table", order=order, label=label, cfg=cfg)
    xlsx_path = _paper_asset_path(cfg, stem=stem, ext="xlsx", bundle=bundle, kind="table")
    csv_path = _paper_asset_path(cfg, stem=stem, ext="csv", bundle=bundle, kind="table")
    write_excel_dataframe(dataframe, xlsx_path)
    write_csv_dataframe(dataframe, csv_path)
    return csv_path, xlsx_path


def _write_manuscript_manifest(cfg: AnalysisConfig, manifest_rows: list[dict[str, object]]) -> dict[str, Path]:
    if not manifest_rows:
        return {}
    manifest_df = pd.DataFrame(manifest_rows).sort_values(["bundle", "asset_kind", "bundle_order", "family"]).reset_index(drop=True)
    csv_path = cfg.report_path("paper_report_manifest", ext="csv", subdir=_MANIFEST_SUBDIR, branch=_PAPER_REPORT_BRANCH)
    xlsx_path = cfg.report_path("paper_report_manifest", ext="xlsx", subdir=_MANIFEST_SUBDIR, branch=_PAPER_REPORT_BRANCH)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_df.to_csv(csv_path, index=False)
    write_excel_dataframe(manifest_df, xlsx_path)
    return {"paper_manifest_csv": csv_path, "paper_manifest_excel": xlsx_path}


def _merged_archetype_support_table(archetype_df: pd.DataFrame, support_df: pd.DataFrame) -> pd.DataFrame:
    left = archetype_df.rename(columns={"field_state": "archetype"}).copy()
    right = support_df.rename(columns={"field_state": "archetype"}).copy()
    merged = left.merge(
        right,
        on=["comparison_space", "archetype", "peak_metric", "normalization", "n_states", "min_duration_ms"],
        how="left",
        suffixes=("", "_support"),
    )
    return merged


def _next_paper_order(counters: dict[str, int], *, bundle: str, kind: str) -> int:
    key = f"{bundle}_{kind}"
    counters[key] = counters.get(key, 0) + 1
    return counters[key]


def _emit_manuscript_figure(
    cfg: AnalysisConfig,
    *,
    outputs: dict[str, Path],
    manifest_rows: list[dict[str, object]],
    counters: dict[str, int],
    bundle: str,
    family: str,
    label: str,
    analysis_branch: str,
    source_paths: tuple[Path, ...],
    render_fn,
) -> Path:
    _ = (cfg, outputs, manifest_rows, counters, bundle, family, label, analysis_branch, source_paths, render_fn)
    stem = _paper_asset_stem(bundle=bundle, kind="figure", order=1, label=label, cfg=cfg)
    return _paper_asset_path(cfg, stem=stem, ext="png", bundle=bundle, kind="figure")


def _emit_manuscript_table(
    cfg: AnalysisConfig,
    *,
    outputs: dict[str, Path],
    manifest_rows: list[dict[str, object]],
    counters: dict[str, int],
    dataframe: pd.DataFrame,
    bundle: str,
    family: str,
    label: str,
    analysis_branch: str,
    source_paths: tuple[Path, ...],
) -> Path:
    order = _next_paper_order(counters, bundle=bundle, kind="table")
    csv_path, xlsx_path = _write_manuscript_table(
        cfg,
        dataframe=dataframe,
        bundle=bundle,
        order=order,
        family=family,
        label=label,
        analysis_branch=analysis_branch,
        source_paths=source_paths,
    )
    outputs[f"{bundle}_table_csv_{cfg.branch_name(label)}"] = csv_path
    outputs[f"{bundle}_table_xlsx_{cfg.branch_name(label)}"] = xlsx_path
    _append_manifest_row(
        manifest_rows,
        cfg=cfg,
        bundle=bundle,
        kind="table",
        order=order,
        family=family,
        label=label,
        analysis_branch=analysis_branch,
        output_csv_path=csv_path,
        output_xlsx_path=xlsx_path,
        source_paths=source_paths,
        dataframe=dataframe,
    )
    return xlsx_path


def _transition_figure_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty or "response_kind" not in dataframe.columns:
        return dataframe
    normalized = dataframe["response_kind"].astype(str).str.strip().str.lower()
    if (normalized == "any-switch").any():
        return dataframe.loc[normalized == "any-switch"].copy()
    return dataframe.drop_duplicates(subset=["from_state", "to_state"], keep="first").copy()


def _render_paper_field_state_core(
    cfg: AnalysisConfig,
    *,
    outputs: dict[str, Path],
    manifest_rows: list[dict[str, object]],
    counters: dict[str, int],
) -> None:
    state_label = cfg.analysis_state.replace("_", " ")
    branch = _retained_field_state_artifact_branch(cfg)
    template_path = cfg.cache_path("coupling", _FIELD_STATE_TEMPLATES_STEM, ext="parquet", branch=branch)
    if template_path.exists():
        template_df = read_dataframe(template_path)
        if template_df.empty:
            return
        profile_path = cfg.cache_path("coupling", _FIELD_STATE_PROFILES_STEM, ext="parquet", branch=branch)
        transition_path = cfg.cache_path("coupling", _FIELD_STATE_TRANSITION_PROFILES_STEM, ext="parquet", branch=branch)
        source_paths = tuple(path for path in (template_path, profile_path, transition_path) if path.exists())
        _emit_manuscript_figure(
            cfg,
            outputs=outputs,
            manifest_rows=manifest_rows,
            counters=counters,
            bundle="main",
            family="field-state-shared",
            label=f"subject_field_state_templates_{branch}",
            analysis_branch=branch,
            source_paths=source_paths,
            render_fn=lambda path, df=template_df: plot_subject_template_panels(
                df,
                path,
                title=f"{state_label} subject-level SEEG global-field-state templates",
            ),
        )
        if profile_path.exists():
            profile_df = _stable_columns(
                _traceable_dataframe(read_dataframe(profile_path), family="field-state-shared", branch=branch, source_path=profile_path),
                (
                    "analysis_family",
                    "analysis_branch",
                    "source_cache",
                    "patient_id",
                    "field_state",
                    "occupancy",
                    "mean_dwell_sec",
                    "n_samples",
                    "n_runs",
                    "peak_metric",
                    "normalization",
                    "n_states",
                    "min_duration_ms",
                ),
            )
            _emit_manuscript_table(
                cfg,
                outputs=outputs,
                manifest_rows=manifest_rows,
                counters=counters,
                dataframe=profile_df,
                bundle="main",
                family="field-state-shared",
                label=f"subject_field_state_profiles_{branch}",
                analysis_branch=branch,
                source_paths=(profile_path,),
            )
            _emit_manuscript_figure(
                cfg,
                outputs=outputs,
                manifest_rows=manifest_rows,
                counters=counters,
                bundle="supplementary",
                family="field-state-shared",
                label=f"subject_field_state_occupancy_{branch}",
                analysis_branch=branch,
                source_paths=(profile_path,),
                render_fn=lambda path, df=read_dataframe(profile_path): plot_subject_state_profile_heatmap(
                    df,
                    path,
                    title=f"{state_label} subject-level SEEG field-state occupancy",
                    state_column="field_state",
                    value_column="occupancy",
                ),
            )
        if transition_path.exists():
            transition_df = _stable_columns(
                _traceable_dataframe(read_dataframe(transition_path), family="field-state-shared", branch=branch, source_path=transition_path),
                (
                    "analysis_family",
                    "analysis_branch",
                    "source_cache",
                    "patient_id",
                    "from_state",
                    "to_state",
                    "n_transitions",
                    "transition_probability",
                    "peak_metric",
                    "normalization",
                    "n_states",
                    "min_duration_ms",
                ),
            )
            _emit_manuscript_table(
                cfg,
                outputs=outputs,
                manifest_rows=manifest_rows,
                counters=counters,
                dataframe=transition_df,
                bundle="supplementary",
                family="field-state-shared",
                label=f"subject_field_state_transition_profiles_{branch}",
                analysis_branch=branch,
                    source_paths=(transition_path,),
                )

    for branch, group_path in _discover_branch_paths(cfg, "stats", _FIELD_STATE_GROUP_STEM, ext="parquet"):
        group_df = _paper_ready_group_rows(read_dataframe(group_path), min_subjects=cfg.min_group_subjects)
        if group_df.empty:
            continue
        subject_path = cfg.cache_path("coupling", _FIELD_STATE_SUBJECT_STEM, ext="parquet", branch=branch)
        subject_df = read_dataframe(subject_path) if subject_path.exists() else None
        source_paths = tuple(path for path in (group_path, subject_path) if path.exists())
        _emit_manuscript_figure(
            cfg,
            outputs=outputs,
            manifest_rows=manifest_rows,
            counters=counters,
            bundle="main",
            family="field-state-coupling",
            label=f"field_state_synchronous_coupling_{branch}",
            analysis_branch=branch,
            source_paths=source_paths,
            render_fn=lambda path, gdf=group_df, sdf=subject_df: plot_effect_curve(
                gdf,
                path,
                title=f"{state_label} EEG microstate versus SEEG field-state synchrony",
                x_column="lag_ms",
                x_label="Lag (ms)",
                y_column="mean_effect",
                y_label="Mean coupling effect",
                subject_df=sdf,
                subject_x_column="lag_ms" if sdf is not None else None,
                subject_y_column="effect_mean_diff" if sdf is not None else None,
            ),
        )
        table_df = _stable_columns(
            _traceable_dataframe(group_df, family="field-state-coupling", branch=branch, source_path=group_path),
            (
                "analysis_family",
                "analysis_branch",
                "source_cache",
                "lag_ms",
                "n_subjects",
                "mean_effect",
                "median_effect",
                "p_perm",
                "q_fdr",
                "peak_metric",
                "normalization",
                "n_states",
                "min_duration_ms",
            ),
        )
        _emit_manuscript_table(
            cfg,
            outputs=outputs,
            manifest_rows=manifest_rows,
            counters=counters,
            dataframe=table_df,
            bundle="main",
            family="field-state-coupling",
            label=f"field_state_synchronous_coupling_{branch}",
            analysis_branch=branch,
            source_paths=(group_path,),
        )

    for branch, group_path in _discover_branch_paths(cfg, "stats", _FINE_LAG_FIELD_STATE_GROUP_STEM, ext="parquet"):
        group_df = _paper_ready_group_rows(read_dataframe(group_path), min_subjects=cfg.min_group_subjects)
        if group_df.empty:
            continue
        subject_curve_path = cfg.cache_path("coupling", _FINE_LAG_FIELD_STATE_SUBJECT_STEM, ext="parquet", branch=branch)
        subject_curve_df = read_dataframe(subject_curve_path) if subject_curve_path.exists() else None
        subject_peak_path = cfg.cache_path("coupling", _FINE_LAG_FIELD_STATE_PEAK_SUBJECT_STEM, ext="parquet", branch=branch)
        group_peak_path = cfg.cache_path("stats", _FINE_LAG_FIELD_STATE_PEAK_GROUP_STEM, ext="parquet", branch=branch)
        source_paths = tuple(path for path in (group_path, subject_curve_path) if path.exists())
        _emit_manuscript_figure(
            cfg,
            outputs=outputs,
            manifest_rows=manifest_rows,
            counters=counters,
            bundle="main",
            family="fine-lag-field-state-coupling",
            label=f"field_state_fine_lag_synchrony_{branch}",
            analysis_branch=branch,
            source_paths=source_paths,
            render_fn=lambda path, gdf=group_df, sdf=subject_curve_df: plot_effect_curve(
                gdf,
                path,
                title=f"{state_label} EEG microstate versus SEEG field-state fine-lag synchrony",
                x_column="lag_ms",
                x_label="Lag (ms)",
                y_column="mean_effect",
                y_label="Mean coupling effect",
                subject_df=sdf,
                subject_x_column="lag_ms" if sdf is not None else None,
                subject_y_column="effect_mean_diff" if sdf is not None else None,
            ),
        )
        lag_table = _stable_columns(
            _traceable_dataframe(group_df, family="fine-lag-field-state-coupling", branch=branch, source_path=group_path),
            (
                "analysis_family",
                "analysis_branch",
                "source_cache",
                "lag_ms",
                "n_subjects",
                "mean_effect",
                "median_effect",
                "p_perm",
                "q_fdr",
                "peak_metric",
                "normalization",
                "n_states",
                "min_duration_ms",
            ),
        )
        _emit_manuscript_table(
            cfg,
            outputs=outputs,
            manifest_rows=manifest_rows,
            counters=counters,
            dataframe=lag_table,
            bundle="main",
            family="fine-lag-field-state-coupling",
            label=f"field_state_fine_lag_synchrony_{branch}",
            analysis_branch=branch,
            source_paths=(group_path,),
        )
        if subject_peak_path.exists():
            peak_subject_df = read_dataframe(subject_peak_path)
            if not peak_subject_df.empty:
                peak_long = peak_subject_df.melt(
                    id_vars=["patient_id"],
                    value_vars=["peak_lag_ms", "peak_effect_mean_diff", "peak_width_ms"],
                    var_name="summary_kind",
                    value_name="summary_value",
                )
                _emit_manuscript_figure(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    bundle="supplementary",
                    family="fine-lag-field-state-coupling",
                    label=f"field_state_fine_lag_peak_summary_{branch}",
                    analysis_branch=branch,
                    source_paths=(subject_peak_path,),
                    render_fn=lambda path, df=peak_long: plot_subject_state_profile_heatmap(
                        df,
                        path,
                        title=f"{state_label} fine-lag field-state peak summaries",
                        state_column="summary_kind",
                        value_column="summary_value",
                    ),
                )
                peak_subject_table = _stable_columns(
                    _traceable_dataframe(peak_subject_df, family="fine-lag-field-state-coupling", branch=branch, source_path=subject_peak_path),
                    (
                        "analysis_family",
                        "analysis_branch",
                        "source_cache",
                        "patient_id",
                        "peak_lag_ms",
                        "peak_effect_mean_diff",
                        "peak_observed_coupling",
                        "peak_null_mean_coupling",
                        "peak_p_perm",
                        "peak_width_ms",
                        "n_lags",
                    ),
                )
                _emit_manuscript_table(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    dataframe=peak_subject_table,
                    bundle="supplementary",
                    family="fine-lag-field-state-coupling",
                    label=f"field_state_fine_lag_subject_peaks_{branch}",
                    analysis_branch=branch,
                    source_paths=(subject_peak_path,),
                )
        if group_peak_path.exists():
            peak_group_df = _paper_ready_group_rows(read_dataframe(group_peak_path), min_subjects=cfg.min_group_subjects)
            if not peak_group_df.empty:
                peak_group_table = _stable_columns(
                    _traceable_dataframe(peak_group_df, family="fine-lag-field-state-coupling", branch=branch, source_path=group_peak_path),
                    (
                        "analysis_family",
                        "analysis_branch",
                        "source_cache",
                        "summary_kind",
                        "n_subjects",
                        "mean_effect",
                        "median_effect",
                        "p_perm",
                        "q_fdr",
                    ),
                )
                _emit_manuscript_table(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    dataframe=peak_group_table,
                    bundle="supplementary",
                    family="fine-lag-field-state-coupling",
                    label=f"field_state_fine_lag_group_peaks_{branch}",
                    analysis_branch=branch,
                    source_paths=(group_peak_path,),
                )


def _render_paper_archetype_core(
    cfg: AnalysisConfig,
    *,
    outputs: dict[str, Path],
    manifest_rows: list[dict[str, object]],
    counters: dict[str, int],
) -> None:
    state_label = cfg.analysis_state.replace("_", " ")
    for branch, archetype_path in _discover_branch_paths(cfg, "coupling", _FIELD_ARCHETYPE_TEMPLATES_STEM, ext="parquet"):
        archetype_df = read_dataframe(archetype_path)
        if archetype_df.empty:
            continue
        assignment_path = cfg.cache_path("coupling", _FIELD_ARCHETYPE_ASSIGNMENTS_STEM, ext="parquet", branch=branch)
        support_path = cfg.cache_path("stats", _FIELD_ARCHETYPE_SUPPORT_STEM, ext="parquet", branch=branch)
        source_paths = tuple(path for path in (archetype_path, assignment_path, support_path) if path.exists())
        _emit_manuscript_figure(
            cfg,
            outputs=outputs,
            manifest_rows=manifest_rows,
            counters=counters,
            bundle="main",
            family="field-state-archetypes",
            label=f"group_field_state_archetypes_{branch}",
            analysis_branch=branch,
            source_paths=source_paths,
            render_fn=lambda path, df=archetype_df: plot_subject_template_panels(
                df,
                path,
                title=f"{state_label} SEEG field-state archetypes in common space",
                subject_column="patient_id",
                x_label="Common-space unit",
            ),
        )
        archetype_table_df = archetype_df.rename(columns={"field_state": "archetype"})
        if support_path.exists():
            support_df = _paper_ready_group_rows(read_dataframe(support_path), min_subjects=cfg.min_group_subjects)
            if not support_df.empty:
                archetype_table_df = _merged_archetype_support_table(archetype_df, support_df)
        archetype_table = _stable_columns(
            _traceable_dataframe(archetype_table_df, family="field-state-archetypes", branch=branch, source_path=archetype_path),
            (
                "analysis_family",
                "analysis_branch",
                "source_cache",
                "comparison_space",
                "archetype",
                "n_subjects",
                "n_state_assignments",
                "mean_similarity",
                "median_similarity",
                "min_similarity",
                "peak_metric",
                "normalization",
                "n_states",
                "min_duration_ms",
                "n_mapped_channels",
                "n_common_units",
                "orientation_sign",
            ),
        )
        _emit_manuscript_table(
            cfg,
            outputs=outputs,
            manifest_rows=manifest_rows,
            counters=counters,
            dataframe=archetype_table,
            bundle="main",
            family="field-state-archetypes",
            label=f"group_field_state_archetypes_{branch}",
            analysis_branch=branch,
            source_paths=tuple(path for path in (archetype_path, support_path) if path.exists()),
        )
        if assignment_path.exists():
            assignment_df = read_dataframe(assignment_path)
            _emit_manuscript_figure(
                cfg,
                outputs=outputs,
                manifest_rows=manifest_rows,
                counters=counters,
                bundle="supplementary",
                family="field-state-archetypes",
                label=f"field_state_archetype_assignments_{branch}",
                analysis_branch=branch,
                source_paths=(assignment_path,),
                render_fn=lambda path, df=assignment_df: plot_subject_state_profile_heatmap(
                    df,
                    path,
                    title=f"{state_label} subject-to-archetype assignment similarity",
                    state_column="assigned_archetype",
                    value_column="assignment_similarity",
                ),
            )
            assignment_table = _stable_columns(
                _traceable_dataframe(assignment_df, family="field-state-archetypes", branch=branch, source_path=assignment_path),
                (
                    "analysis_family",
                    "analysis_branch",
                    "source_cache",
                    "patient_id",
                    "field_state",
                    "assigned_archetype",
                    "assignment_similarity",
                    "orientation_sign",
                    "comparison_space",
                    "peak_metric",
                    "normalization",
                    "n_states",
                    "min_duration_ms",
                ),
            )
            _emit_manuscript_table(
                cfg,
                outputs=outputs,
                manifest_rows=manifest_rows,
                counters=counters,
                dataframe=assignment_table,
                bundle="supplementary",
                family="field-state-archetypes",
                label=f"field_state_archetype_assignments_{branch}",
                analysis_branch=branch,
                source_paths=(assignment_path,),
            )


def _render_paper_archetype_conditioned_eeg(
    cfg: AnalysisConfig,
    *,
    outputs: dict[str, Path],
    manifest_rows: list[dict[str, object]],
    counters: dict[str, int],
) -> None:
    state_label = cfg.analysis_state.replace("_", " ")
    for branch, group_map_path in _discover_branch_paths(cfg, "coupling", _ARCHETYPE_EEG_MAP_GROUP_STEM, ext="parquet"):
        group_map_df = _paper_ready_group_rows(read_dataframe(group_map_path), min_subjects=cfg.min_group_subjects)
        if group_map_df.empty:
            continue
        _emit_manuscript_figure(
            cfg,
            outputs=outputs,
            manifest_rows=manifest_rows,
            counters=counters,
            bundle="main",
            family="archetype-conditioned-eeg-topography",
            label=f"archetype_conditioned_eeg_topographies_{branch}",
            analysis_branch=branch,
            source_paths=(group_map_path,),
            render_fn=lambda path, df=group_map_df: plot_eeg_topography_panels(
                df,
                path,
                title=f"{state_label} archetype-conditioned EEG scalp topographies",
                state_column="assigned_archetype",
            ),
        )
        raw_map_table = _stable_columns(
            _traceable_dataframe(group_map_df, family="archetype-conditioned-eeg-topography", branch=branch, source_path=group_map_path),
            (
                "analysis_family",
                "analysis_branch",
                "source_cache",
                "comparison_space",
                "assigned_archetype",
                "n_subjects",
                "total_samples",
                "peak_metric",
                "normalization",
                "n_states",
                "min_duration_ms",
            ),
        )
        _emit_manuscript_table(
            cfg,
            outputs=outputs,
            manifest_rows=manifest_rows,
            counters=counters,
            dataframe=raw_map_table,
            bundle="supplementary",
            family="archetype-conditioned-eeg-topography",
            label=f"archetype_conditioned_eeg_maps_{branch}",
            analysis_branch=branch,
            source_paths=(group_map_path,),
        )

        similarity_path = cfg.cache_path("stats", _ARCHETYPE_EEG_SIMILARITY_GROUP_STEM, ext="parquet", branch=branch)
        if similarity_path.exists():
            similarity_df = _paper_ready_group_rows(read_dataframe(similarity_path), min_subjects=cfg.min_group_subjects)
            if not similarity_df.empty:
                _emit_manuscript_figure(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    bundle="supplementary",
                    family="archetype-conditioned-eeg-topography",
                    label=f"archetype_eeg_template_similarity_{branch}",
                    analysis_branch=branch,
                    source_paths=(similarity_path,),
                    render_fn=lambda path, df=similarity_df: plot_group_metric_heatmap(
                        df,
                        path,
                        title=f"{state_label} archetype-conditioned EEG template similarity",
                        value_column="mean_similarity",
                        unit_column="microstate",
                        row_column="assigned_archetype",
                    ),
                )
                similarity_table = _stable_columns(
                    _traceable_dataframe(similarity_df, family="archetype-conditioned-eeg-topography", branch=branch, source_path=similarity_path),
                    (
                        "analysis_family",
                        "analysis_branch",
                        "source_cache",
                        "comparison_space",
                        "assigned_archetype",
                        "microstate",
                        "n_subjects",
                        "mean_similarity",
                        "median_similarity",
                        "min_similarity",
                        "peak_metric",
                        "normalization",
                        "n_states",
                        "min_duration_ms",
                    ),
                )
                _emit_manuscript_table(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    dataframe=similarity_table,
                    bundle="main",
                    family="archetype-conditioned-eeg-topography",
                    label=f"archetype_eeg_template_similarity_{branch}",
                    analysis_branch=branch,
                    source_paths=(similarity_path,),
                )

        preference_path = cfg.cache_path("stats", _ARCHETYPE_EEG_PREFERENCE_GROUP_STEM, ext="parquet", branch=branch)
        if preference_path.exists():
            preference_df = _paper_ready_group_rows(read_dataframe(preference_path), min_subjects=cfg.min_group_subjects)
            if not preference_df.empty:
                _emit_manuscript_figure(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    bundle="supplementary",
                    family="archetype-conditioned-eeg-topography",
                    label=f"archetype_eeg_state_preference_{branch}",
                    analysis_branch=branch,
                    source_paths=(preference_path,),
                    render_fn=lambda path, df=preference_df: plot_group_metric_heatmap(
                        df,
                        path,
                        title=f"{state_label} archetype-conditioned EEG state preference",
                        value_column="mean_effect",
                        unit_column="microstate",
                        row_column="assigned_archetype",
                    ),
                )
                preference_table = _stable_columns(
                    _traceable_dataframe(preference_df, family="archetype-conditioned-eeg-topography", branch=branch, source_path=preference_path),
                    (
                        "analysis_family",
                        "analysis_branch",
                        "source_cache",
                        "comparison_space",
                        "assigned_archetype",
                        "microstate",
                        "n_subjects",
                        "mean_effect",
                        "median_effect",
                        "p_perm",
                        "q_fdr",
                    ),
                )
                _emit_manuscript_table(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    dataframe=preference_table,
                    bundle="supplementary",
                    family="archetype-conditioned-eeg-topography",
                    label=f"archetype_eeg_state_preference_{branch}",
                    analysis_branch=branch,
                    source_paths=(preference_path,),
                )

        lag_group_path = cfg.cache_path("stats", _ARCHETYPE_EEG_FINE_LAG_GROUP_STEM, ext="parquet", branch=branch)
        lag_subject_path = cfg.cache_path("coupling", _ARCHETYPE_EEG_FINE_LAG_SUBJECT_STEM, ext="parquet", branch=branch)
        if lag_group_path.exists():
            lag_df = _paper_ready_group_rows(read_dataframe(lag_group_path), min_subjects=cfg.min_group_subjects)
            if not lag_df.empty:
                lag_subject_df = read_dataframe(lag_subject_path) if lag_subject_path.exists() else None
                source_paths = tuple(path for path in (lag_group_path, lag_subject_path) if path.exists())
                _emit_manuscript_figure(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    bundle="main",
                    family="archetype-conditioned-eeg-topography",
                    label=f"archetype_eeg_fine_lag_synchrony_{branch}",
                    analysis_branch=branch,
                    source_paths=source_paths,
                    render_fn=lambda path, gdf=lag_df, sdf=lag_subject_df: plot_effect_curve(
                        gdf,
                        path,
                        title=f"{state_label} SEEG archetype versus EEG microstate fine-lag synchrony",
                        x_column="lag_ms",
                        x_label="Lag (ms)",
                        y_column="mean_effect",
                        y_label="Mean coupling effect",
                        subject_df=sdf,
                        subject_x_column="lag_ms" if sdf is not None else None,
                        subject_y_column="effect_mean_diff" if sdf is not None else None,
                    ),
                )
                lag_table = _stable_columns(
                    _traceable_dataframe(lag_df, family="archetype-conditioned-eeg-topography", branch=branch, source_path=lag_group_path),
                    (
                        "analysis_family",
                        "analysis_branch",
                        "source_cache",
                        "lag_ms",
                        "n_subjects",
                        "mean_effect",
                        "median_effect",
                        "p_perm",
                        "q_fdr",
                    ),
                )
                _emit_manuscript_table(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    dataframe=lag_table,
                    bundle="main",
                    family="archetype-conditioned-eeg-topography",
                    label=f"archetype_eeg_fine_lag_synchrony_{branch}",
                    analysis_branch=branch,
                    source_paths=(lag_group_path,),
                )

        peak_subject_path = cfg.cache_path("coupling", _ARCHETYPE_EEG_FINE_LAG_PEAK_SUBJECT_STEM, ext="parquet", branch=branch)
        if peak_subject_path.exists():
            peak_subject_df = read_dataframe(peak_subject_path)
            if not peak_subject_df.empty:
                peak_long = peak_subject_df.melt(
                    id_vars=["patient_id"],
                    value_vars=["peak_lag_ms", "peak_effect_mean_diff", "peak_width_ms"],
                    var_name="summary_kind",
                    value_name="summary_value",
                )
                _emit_manuscript_figure(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    bundle="supplementary",
                    family="archetype-conditioned-eeg-topography",
                    label=f"archetype_eeg_fine_lag_peaks_{branch}",
                    analysis_branch=branch,
                    source_paths=(peak_subject_path,),
                    render_fn=lambda path, df=peak_long: plot_subject_state_profile_heatmap(
                        df,
                        path,
                        title=f"{state_label} archetype-conditioned EEG fine-lag peak summaries",
                        state_column="summary_kind",
                        value_column="summary_value",
                    ),
                )
                peak_subject_table = _stable_columns(
                    _traceable_dataframe(peak_subject_df, family="archetype-conditioned-eeg-topography", branch=branch, source_path=peak_subject_path),
                    (
                        "analysis_family",
                        "analysis_branch",
                        "source_cache",
                        "patient_id",
                        "peak_lag_ms",
                        "peak_effect_mean_diff",
                        "peak_width_ms",
                        "peak_p_perm",
                    ),
                )
                _emit_manuscript_table(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    dataframe=peak_subject_table,
                    bundle="supplementary",
                    family="archetype-conditioned-eeg-topography",
                    label=f"archetype_eeg_fine_lag_subject_peaks_{branch}",
                    analysis_branch=branch,
                    source_paths=(peak_subject_path,),
                )

        peak_group_path = cfg.cache_path("stats", _ARCHETYPE_EEG_FINE_LAG_PEAK_GROUP_STEM, ext="parquet", branch=branch)
        if peak_group_path.exists():
            peak_group_df = _paper_ready_group_rows(read_dataframe(peak_group_path), min_subjects=cfg.min_group_subjects)
            if not peak_group_df.empty:
                peak_group_table = _stable_columns(
                    _traceable_dataframe(peak_group_df, family="archetype-conditioned-eeg-topography", branch=branch, source_path=peak_group_path),
                    (
                        "analysis_family",
                        "analysis_branch",
                        "source_cache",
                        "summary_kind",
                        "n_subjects",
                        "mean_effect",
                        "median_effect",
                        "p_perm",
                        "q_fdr",
                    ),
                )
                _emit_manuscript_table(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    dataframe=peak_group_table,
                    bundle="supplementary",
                    family="archetype-conditioned-eeg-topography",
                    label=f"archetype_eeg_fine_lag_group_peaks_{branch}",
                    analysis_branch=branch,
                    source_paths=(peak_group_path,),
                )

        transition_group_path = cfg.cache_path("stats", _ARCHETYPE_EEG_TRANSITION_GROUP_STEM, ext="parquet", branch=branch)
        if transition_group_path.exists():
            transition_df = _paper_ready_group_rows(read_dataframe(transition_group_path), min_subjects=cfg.min_group_subjects)
            if not transition_df.empty:
                plotted_df = (
                    transition_df[transition_df["response_kind"] == "any-switch"].copy()
                    if "response_kind" in transition_df.columns
                    else transition_df
                )
                _emit_manuscript_figure(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    bundle="supplementary",
                    family="archetype-conditioned-eeg-topography",
                    label=f"archetype_to_eeg_switching_{branch}",
                    analysis_branch=branch,
                    source_paths=(transition_group_path,),
                    render_fn=lambda path, df=plotted_df: plot_state_transition_matrix(
                        df,
                        path,
                        title=f"{state_label} SEEG archetype-led EEG switching",
                        x_label="SEEG archetype to_state",
                        y_label="SEEG archetype from_state",
                    ),
                )
                transition_table = _stable_columns(
                    _traceable_dataframe(transition_df, family="archetype-conditioned-eeg-topography", branch=branch, source_path=transition_group_path),
                    (
                        "analysis_family",
                        "analysis_branch",
                        "source_cache",
                        "from_state",
                        "to_state",
                        "response_kind",
                        "response_state",
                        "n_subjects",
                        "mean_effect",
                        "median_effect",
                        "p_perm",
                        "q_fdr",
                    ),
                )
                _emit_manuscript_table(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    dataframe=transition_table,
                    bundle="supplementary",
                    family="archetype-conditioned-eeg-topography",
                    label=f"archetype_to_eeg_switching_{branch}",
                    analysis_branch=branch,
                    source_paths=(transition_group_path,),
                )


def _render_paper_supplementary_followups(
    cfg: AnalysisConfig,
    *,
    outputs: dict[str, Path],
    manifest_rows: list[dict[str, object]],
    counters: dict[str, int],
) -> None:
    state_label = cfg.analysis_state.replace("_", " ")
    group_families: tuple[tuple[str, str, str, str], ...] = (
        (_GFP_GLOBAL_GROUP_STEM, "gfp-global-coupling", "gfp_global_coupling", "lag"),
        (_PEAK_GFP_GLOBAL_GROUP_STEM, "peak-gfp-global-coupling", "peak_gfp_global_coupling", "offset"),
        (_GFP_CONTROLLED_MICROSTATE_GROUP_OMNIBUS_STEM, "gfp-controlled-microstate", "gfp_controlled_microstate", "heatmap"),
        (_GFP_CONTROLLED_TRANSITION_GROUP_STEM, "gfp-controlled-transition", "gfp_controlled_transition", "transition"),
        (_FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM, "field-state-to-eeg-switching", "field_state_to_eeg_switching", "transition"),
        (
            _GFP_CONTROLLED_FIELD_STATE_TO_EEG_SWITCHING_GROUP_STEM,
            "gfp-controlled-field-state-to-eeg-switching",
            "gfp_controlled_field_state_to_eeg_switching",
            "transition",
        ),
    )
    for stem, family, label, mode in group_families:
        for branch, group_path in _discover_branch_paths(cfg, "stats", stem, ext="parquet"):
            group_df = _paper_ready_group_rows(read_dataframe(group_path), min_subjects=cfg.min_group_subjects)
            if group_df.empty:
                continue
            if mode == "lag":
                _emit_manuscript_figure(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    bundle="supplementary",
                    family=family,
                    label=f"{label}_{branch}",
                    analysis_branch=branch,
                    source_paths=(group_path,),
                    render_fn=lambda path, df=group_df: plot_effect_curve(
                        df,
                        path,
                        title=f"{state_label} {family.replace('-', ' ')}",
                        x_column="lag_ms",
                        x_label="Lag (ms)",
                        y_column="mean_effect",
                        y_label="Mean effect",
                    ),
                )
            elif mode == "offset":
                _emit_manuscript_figure(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    bundle="supplementary",
                    family=family,
                    label=f"{label}_{branch}",
                    analysis_branch=branch,
                    source_paths=(group_path,),
                    render_fn=lambda path, df=group_df: plot_effect_curve(
                        df,
                        path,
                        title=f"{state_label} {family.replace('-', ' ')}",
                        x_column="offset_ms",
                        x_label="Offset (ms)",
                        y_column="mean_effect",
                        y_label="Mean effect",
                    ),
                )
            elif mode == "heatmap":
                _emit_manuscript_figure(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    bundle="supplementary",
                    family=family,
                    label=f"{label}_{branch}",
                    analysis_branch=branch,
                    source_paths=(group_path,),
                    render_fn=lambda path, df=group_df: plot_group_metric_heatmap(
                        df,
                        path,
                        title=f"{state_label} GFP-controlled microstate omnibus",
                        value_column="statistic",
                        unit_column="n_subjects",
                    ),
                )
            else:
                figure_df = _transition_figure_dataframe(group_df)
                _emit_manuscript_figure(
                    cfg,
                    outputs=outputs,
                    manifest_rows=manifest_rows,
                    counters=counters,
                    bundle="supplementary",
                    family=family,
                    label=f"{label}_{branch}",
                    analysis_branch=branch,
                    source_paths=(group_path,),
                    render_fn=lambda path, df=figure_df: plot_state_transition_matrix(
                        df,
                        path,
                        title=f"{state_label} {family.replace('-', ' ')}",
                    ),
                )
            table_df = _stable_columns(
                _traceable_dataframe(group_df, family=family, branch=branch, source_path=group_path),
                (
                    "analysis_family",
                    "analysis_branch",
                    "source_cache",
                    "global_metric_label",
                    "metric_definition",
                    "weighting_strategy",
                    "network_scope",
                    "lag_ms",
                    "offset_ms",
                    "from_state",
                    "to_state",
                    "response_kind",
                    "response_state",
                    "n_subjects",
                    "mean_effect",
                    "median_effect",
                    "statistic",
                    "p_perm",
                    "q_fdr",
                ),
            )
            _emit_manuscript_table(
                cfg,
                outputs=outputs,
                manifest_rows=manifest_rows,
                counters=counters,
                dataframe=table_df,
                bundle="supplementary",
                family=family,
                label=f"{label}_{branch}",
                analysis_branch=branch,
                source_paths=(group_path,),
            )

    for branch, group_path in _discover_branch_paths(cfg, "stats", _FIELD_STATE_MODEL_ORDER_GROUP_STEM, ext="parquet"):
        group_df = _paper_ready_group_rows(read_dataframe(group_path), min_subjects=cfg.min_group_subjects)
        if group_df.empty:
            continue
        subject_path = cfg.cache_path("coupling", _FIELD_STATE_MODEL_ORDER_SUBJECT_STEM, ext="parquet", branch=branch)
        if subject_path.exists():
            subject_df = _stable_columns(
                _traceable_dataframe(
                    read_dataframe(subject_path),
                    family="field-state-model-order-evaluation",
                    branch=branch,
                    source_path=subject_path,
                ),
                (
                    "analysis_family",
                    "analysis_branch",
                    "source_cache",
                    "patient_id",
                    "n_states",
                    "k_range",
                    "retained_main_text_default",
                    "mean_template_fit",
                    "median_template_fit",
                    "min_template_fit",
                    "fit_gain_from_prev_k",
                    "split_half_stability",
                    "min_state_occupancy",
                    "max_state_occupancy",
                    "min_state_peak_fraction",
                    "max_state_peak_fraction",
                    "occupancy_entropy",
                    "n_channels",
                    "n_peak_maps_total",
                    "peak_metric",
                    "normalization",
                    "min_duration_ms",
                ),
            )
            _emit_manuscript_table(
                cfg,
                outputs=outputs,
                manifest_rows=manifest_rows,
                counters=counters,
                dataframe=subject_df,
                bundle="supplementary",
                family="field-state-model-order-evaluation",
                label=f"field_state_model_order_subject_{branch}",
                analysis_branch=branch,
                source_paths=(subject_path,),
            )
        group_table = _stable_columns(
            _traceable_dataframe(
                group_df,
                family="field-state-model-order-evaluation",
                branch=branch,
                source_path=group_path,
            ),
            (
                "analysis_family",
                "analysis_branch",
                "source_cache",
                "n_states",
                "k_range",
                "retained_main_text_default",
                "n_subjects",
                "mean_template_fit",
                "median_template_fit",
                "mean_fit_gain_from_prev_k",
                "median_fit_gain_from_prev_k",
                "mean_split_half_stability",
                "median_split_half_stability",
                "mean_min_state_occupancy",
                "median_min_state_occupancy",
                "mean_min_state_peak_fraction",
                "median_min_state_peak_fraction",
                "mean_occupancy_entropy",
                "median_occupancy_entropy",
                "peak_metric",
                "normalization",
                "min_duration_ms",
            ),
        )
        _emit_manuscript_table(
            cfg,
            outputs=outputs,
            manifest_rows=manifest_rows,
            counters=counters,
            dataframe=group_table,
            bundle="supplementary",
            family="field-state-model-order-evaluation",
            label=f"field_state_model_order_group_{branch}",
            analysis_branch=branch,
            source_paths=(group_path,),
        )


def _render_manuscript_reports(cfg: AnalysisConfig) -> dict[str, Path]:
    cfg.ensure_cache_directories()
    outputs: dict[str, Path] = {}
    manifest_rows: list[dict[str, object]] = []
    counters: dict[str, int] = {}
    _render_paper_field_state_core(cfg, outputs=outputs, manifest_rows=manifest_rows, counters=counters)
    _render_paper_archetype_core(cfg, outputs=outputs, manifest_rows=manifest_rows, counters=counters)
    _render_paper_archetype_conditioned_eeg(cfg, outputs=outputs, manifest_rows=manifest_rows, counters=counters)
    _render_paper_supplementary_followups(cfg, outputs=outputs, manifest_rows=manifest_rows, counters=counters)
    outputs.update(_write_manuscript_manifest(cfg, manifest_rows))
    return outputs


def export_paper_tables(cfg: AnalysisConfig) -> dict[str, Path]:
    return _render_manuscript_reports(cfg)
