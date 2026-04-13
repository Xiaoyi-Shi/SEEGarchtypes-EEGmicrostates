from __future__ import annotations

from pathlib import Path
import subprocess

import pandas as pd

from seeg_eegmicrostates._utils import write_csv_dataframe, write_excel_dataframe


def _manifest_row(*, bundle: str, order: int, family: str, label: str, path: Path, df: pd.DataFrame) -> dict[str, object]:
    return {
        "run_id": "20260408_131613",
        "analysis_state": "IDE_A",
        "runtime_hash": "55bd14ef4d",
        "bundle": bundle,
        "asset_kind": "table",
        "bundle_order": order,
        "family": family,
        "label": label,
        "analysis_branch": "paper_workflow",
        "output_csv_path": str(path.with_suffix(".csv")),
        "output_xlsx_path": str(path),
        "source_caches": "synthetic.parquet",
        "row_count": len(df),
        "column_count": len(df.columns),
        "subject_support_column": "n_subjects" if "n_subjects" in df.columns else "",
        "min_subject_support": int(df["n_subjects"].min()) if "n_subjects" in df.columns else None,
        "max_subject_support": int(df["n_subjects"].max()) if "n_subjects" in df.columns else None,
        "parameter_summary": "",
    }


def _write_bundle_table(base: Path, subdir: str, stem: str, df: pd.DataFrame) -> Path:
    path = base / subdir / f"{stem}.xlsx"
    write_excel_dataframe(df, path)
    write_csv_dataframe(df, path.with_suffix(".csv"))
    return path


def test_r_markdown_scripts_render_from_standardized_table_exports(tmp_path: Path) -> None:
    report_root = tmp_path / "reports"
    manifest_rows: list[dict[str, object]] = []

    main_tables = {
        "table_01_subject_field_state_profiles": pd.DataFrame(
            {"patient_id": ["sub-01", "sub-01"], "field_state": [0, 1], "occupancy": [0.4, 0.6], "mean_dwell_sec": [0.1, 0.12]}
        ),
        "table_02_field_state_synchronous_coupling": pd.DataFrame(
            {"lag_ms": [0], "mean_effect": [0.2], "q_fdr": [0.01], "n_subjects": [8]}
        ),
        "table_03_field_state_fine_lag_synchrony": pd.DataFrame(
            {"lag_ms": [-4, 0, 4], "mean_effect": [0.1, 0.3, 0.12], "q_fdr": [0.05, 0.01, 0.05], "n_subjects": [8, 8, 8]}
        ),
        "table_04_group_field_state_archetypes": pd.DataFrame(
            {
                "archetype": [0, 1],
                "n_subjects": [8, 8],
                "mean_similarity": [0.5, 0.45],
                "ContA": [0.4, -0.2],
                "ContB": [-0.1, 0.3],
                "DefaultA": [0.2, -0.3],
            }
        ),
        "table_05_archetype_eeg_template_similarity": pd.DataFrame(
            {"assigned_archetype": [0, 0, 1, 1], "microstate": [0, 1, 0, 1], "mean_similarity": [0.2, 0.1, 0.15, 0.18], "n_subjects": [8, 8, 8, 8]}
        ),
        "table_06_archetype_eeg_fine_lag_synchrony": pd.DataFrame(
            {"lag_ms": [-4, 0, 4], "mean_effect": [0.11, 0.25, 0.1], "q_fdr": [0.05, 0.01, 0.05], "n_subjects": [8, 8, 8]}
        ),
    }
    supplementary_tables = {
        "supplementary_table_01_subject_field_state_transition_profiles": pd.DataFrame(
            {"from_state": [0, 1], "to_state": [1, 0], "transition_probability": [0.4, 0.6]}
        ),
        "supplementary_table_02_field_state_fine_lag_subject_peaks": pd.DataFrame(
            {"patient_id": ["sub-01", "sub-02"], "peak_lag_ms": [0, 4], "peak_effect_mean_diff": [0.2, 0.25], "peak_width_ms": [16, 20]}
        ),
        "supplementary_table_04_field_state_archetype_assignments": pd.DataFrame(
            {"patient_id": ["sub-01", "sub-02"], "assigned_archetype": [0, 1], "assignment_similarity": [0.5, 0.4]}
        ),
        "supplementary_table_05_archetype_conditioned_eeg_maps": pd.DataFrame(
            {"assigned_archetype": [0, 1], "Fp1": [0.1, -0.1], "F3": [0.2, -0.2], "Cz": [-0.1, 0.1], "Pz": [-0.2, 0.2]}
        ),
        "supplementary_table_06_archetype_eeg_state_preference": pd.DataFrame(
            {"assigned_archetype": [0, 1], "microstate": [0, 1], "mean_effect": [0.12, 0.09]}
        ),
        "supplementary_table_09_archetype_to_eeg_switching": pd.DataFrame(
            {"from_state": [0, 1], "to_state": [1, 0], "response_kind": ["any-switch", "any-switch"], "mean_effect": [0.07, -0.03]}
        ),
        "supplementary_table_10_gfp_global_coupling": pd.DataFrame(
            {"lag_ms": [0], "mean_effect": [0.12], "q_fdr": [0.001], "n_subjects": [8]}
        ),
        "supplementary_table_11_peak_gfp_global_coupling": pd.DataFrame(
            {"offset_ms": [-4, 0, 4], "mean_effect": [-0.01, -0.02, -0.01], "q_fdr": [0.02, 0.01, 0.02], "n_subjects": [8, 8, 8]}
        ),
        "supplementary_table_12_gfp_controlled_microstate": pd.DataFrame(
            {"global_metric_label": ["rms__equal"], "mean_state_0": [0.1], "mean_state_1": [0.2], "mean_state_2": [0.15], "mean_state_3": [0.3]}
        ),
        "supplementary_table_13_gfp_controlled_transition": pd.DataFrame(
            {"from_state": [0], "to_state": [1], "mean_effect": [0.05]}
        ),
        "supplementary_table_14_field_state_model_order_subject": pd.DataFrame(
            {
                "patient_id": ["sub-01", "sub-01", "sub-02", "sub-02"],
                "n_states": [2, 4, 2, 4],
                "k_range": ["2-7", "2-7", "2-7", "2-7"],
                "retained_main_text_default": [False, True, False, True],
                "mean_template_fit": [0.80, 0.85, 0.81, 0.86],
                "fit_gain_from_prev_k": [pd.NA, 0.05, pd.NA, 0.05],
                "split_half_stability": [0.72, 0.80, 0.74, 0.82],
            }
        ),
        "supplementary_table_15_field_state_model_order_group": pd.DataFrame(
            {
                "n_states": [2, 4],
                "k_range": ["2-7", "2-7"],
                "retained_main_text_default": [False, True],
                "n_subjects": [8, 8],
                "median_template_fit": [0.805, 0.855],
                "median_fit_gain_from_prev_k": [pd.NA, 0.05],
                "median_split_half_stability": [0.73, 0.81],
            }
        ),
    }

    order = 1
    for stem, df in main_tables.items():
        xlsx_path = _write_bundle_table(report_root, "main_tables", stem, df)
        manifest_rows.append(_manifest_row(bundle="main", order=order, family="main-family", label=stem, path=xlsx_path, df=df))
        order += 1

    order = 1
    for stem, df in supplementary_tables.items():
        xlsx_path = _write_bundle_table(report_root, "supplementary_tables", stem, df)
        manifest_rows.append(
            _manifest_row(bundle="supplementary", order=order, family="supp-family", label=stem, path=xlsx_path, df=df)
        )
        order += 1

    manifest_df = pd.DataFrame(manifest_rows)
    write_csv_dataframe(manifest_df, report_root / "manifests" / "paper_report_manifest.csv")
    write_excel_dataframe(manifest_df, report_root / "manifests" / "paper_report_manifest.xlsx")

    main_cmd = [
        "Rscript",
        "-e",
        f"rmarkdown::render('scripts/01_main_figures.Rmd', output_file='main_figures_test.html', output_dir='{tmp_path.as_posix()}', params=list(report_root='{report_root.as_posix()}'))",
    ]
    supplementary_cmd = [
        "Rscript",
        "-e",
        f"rmarkdown::render('scripts/02_supplementary_figures.Rmd', output_file='supplementary_figures_test.html', output_dir='{tmp_path.as_posix()}', params=list(report_root='{report_root.as_posix()}'))",
    ]

    subprocess.run(main_cmd, check=True, cwd=Path.cwd())
    subprocess.run(supplementary_cmd, check=True, cwd=Path.cwd())

    assert (tmp_path / "main_figures_test.html").exists()
    assert (tmp_path / "supplementary_figures_test.html").exists()
    assert (report_root / "main_figures" / "figure_01_subject_field_state_profiles.png").exists()
    assert (report_root / "main_figures" / "figure_06_archetype_eeg_fine_lag_synchrony.png").exists()
    assert (report_root / "supplementary_figures" / "supplementary_figure_01_field_state_transition_profiles.png").exists()
    assert (report_root / "supplementary_figures" / "supplementary_figure_08_gfp_controlled_followups.png").exists()
    assert (report_root / "supplementary_figures" / "supplementary_figure_09_field_state_model_order.png").exists()


def test_supplementary_r_markdown_fails_clearly_when_model_order_tables_are_missing(tmp_path: Path) -> None:
    report_root = tmp_path / "reports"
    supplementary_tables = {
        "supplementary_table_01_subject_field_state_transition_profiles": pd.DataFrame(
            {"from_state": [0], "to_state": [1], "transition_probability": [0.5]}
        ),
        "supplementary_table_02_field_state_fine_lag_subject_peaks": pd.DataFrame(
            {"patient_id": ["sub-01"], "peak_lag_ms": [0], "peak_effect_mean_diff": [0.2], "peak_width_ms": [16]}
        ),
        "supplementary_table_04_field_state_archetype_assignments": pd.DataFrame(
            {"patient_id": ["sub-01"], "assigned_archetype": [0], "assignment_similarity": [0.5]}
        ),
        "supplementary_table_05_archetype_conditioned_eeg_maps": pd.DataFrame(
            {"assigned_archetype": [0], "Fp1": [0.1], "F3": [0.2], "Cz": [-0.1], "Pz": [-0.2]}
        ),
        "supplementary_table_06_archetype_eeg_state_preference": pd.DataFrame(
            {"assigned_archetype": [0], "microstate": [0], "mean_effect": [0.12]}
        ),
        "supplementary_table_09_archetype_to_eeg_switching": pd.DataFrame(
            {"from_state": [0], "to_state": [1], "response_kind": ["any-switch"], "mean_effect": [0.07]}
        ),
        "supplementary_table_10_gfp_global_coupling": pd.DataFrame(
            {"lag_ms": [0], "mean_effect": [0.12], "q_fdr": [0.001], "n_subjects": [8]}
        ),
        "supplementary_table_11_peak_gfp_global_coupling": pd.DataFrame(
            {"offset_ms": [0], "mean_effect": [-0.02], "q_fdr": [0.01], "n_subjects": [8]}
        ),
        "supplementary_table_12_gfp_controlled_microstate": pd.DataFrame(
            {"global_metric_label": ["rms__equal"], "mean_state_0": [0.1], "mean_state_1": [0.2], "mean_state_2": [0.15], "mean_state_3": [0.3]}
        ),
        "supplementary_table_13_gfp_controlled_transition": pd.DataFrame(
            {"from_state": [0], "to_state": [1], "mean_effect": [0.05]}
        ),
    }
    manifest_rows = []
    order = 1
    for stem, df in supplementary_tables.items():
        xlsx_path = _write_bundle_table(report_root, "supplementary_tables", stem, df)
        manifest_rows.append(_manifest_row(bundle="supplementary", order=order, family="supp-family", label=stem, path=xlsx_path, df=df))
        order += 1
    manifest_df = pd.DataFrame(manifest_rows)
    write_csv_dataframe(manifest_df, report_root / "manifests" / "paper_report_manifest.csv")
    write_excel_dataframe(manifest_df, report_root / "manifests" / "paper_report_manifest.xlsx")

    supplementary_cmd = [
        "Rscript",
        "-e",
        f"rmarkdown::render('scripts/02_supplementary_figures.Rmd', output_file='supplementary_figures_test.html', output_dir='{tmp_path.as_posix()}', params=list(report_root='{report_root.as_posix()}'))",
    ]

    completed = subprocess.run(
        supplementary_cmd,
        cwd=Path.cwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )
    combined_output = completed.stdout.decode("utf-8", errors="replace") + completed.stderr.decode("utf-8", errors="replace")

    assert completed.returncode != 0
    assert "field_state_model_order_subject" in combined_output
