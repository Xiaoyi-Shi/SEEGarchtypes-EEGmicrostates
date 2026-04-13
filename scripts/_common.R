library(ggplot2)
library(dplyr)
library(readxl)
library(scales)
library(tidyr)
library(patchwork)

paper_theme <- function() {
  theme_minimal(base_size = 11) +
    theme(
      panel.grid.minor = element_blank(),
      panel.grid.major.x = element_blank(),
      strip.text = element_text(face = "bold"),
      plot.title = element_text(face = "bold", size = 12),
      plot.subtitle = element_text(size = 10),
      axis.title = element_text(face = "bold")
    )
}

resolve_manifest <- function(report_root = NULL, manifest_path = NULL) {
  resolve_candidate <- function(path) {
    if (file.exists(path)) {
      return(normalizePath(path, winslash = "/", mustWork = TRUE))
    }
    parent_candidate <- file.path("..", path)
    if (file.exists(parent_candidate)) {
      return(normalizePath(parent_candidate, winslash = "/", mustWork = TRUE))
    }
    NULL
  }
  resolve_glob <- function(path_pattern) {
    direct_matches <- Sys.glob(path_pattern)
    if (length(direct_matches) > 0) {
      return(normalizePath(direct_matches[[1]], winslash = "/", mustWork = TRUE))
    }
    parent_matches <- Sys.glob(file.path("..", path_pattern))
    if (length(parent_matches) > 0) {
      return(normalizePath(parent_matches[[1]], winslash = "/", mustWork = TRUE))
    }
    NULL
  }

  if (!is.null(manifest_path) && nzchar(manifest_path)) {
    resolved <- resolve_candidate(manifest_path)
    if (!is.null(resolved)) {
      return(resolved)
    }
    stop("Could not resolve manifest_path.")
  }
  if (is.null(report_root) || !nzchar(report_root)) {
    stop("Provide either report_root or manifest_path.")
  }
  candidate_csv <- resolve_glob(file.path(report_root, "manifests", "paper_report_manifest*.csv"))
  candidate_xlsx <- resolve_glob(file.path(report_root, "manifests", "paper_report_manifest*.xlsx"))
  if (!is.null(candidate_csv)) {
    return(candidate_csv)
  }
  if (!is.null(candidate_xlsx)) {
    return(candidate_xlsx)
  }
  stop("Could not find paper report manifest under report_root/manifests.")
}

read_manifest <- function(report_root = NULL, manifest_path = NULL) {
  manifest <- resolve_manifest(report_root = report_root, manifest_path = manifest_path)
  if (grepl("\\.csv$", manifest, ignore.case = TRUE)) {
    df <- read.csv(manifest, stringsAsFactors = FALSE)
  } else {
    df <- readxl::read_excel(manifest)
  }
  required_cols <- c(
    "run_id",
    "analysis_state",
    "runtime_hash",
    "bundle",
    "asset_kind",
    "bundle_order",
    "family",
    "label",
    "analysis_branch",
    "output_csv_path",
    "output_xlsx_path",
    "source_caches",
    "row_count",
    "column_count",
    "parameter_summary"
  )
  missing_cols <- setdiff(required_cols, names(df))
  if (length(missing_cols) > 0) {
    stop(paste("Manifest missing columns:", paste(missing_cols, collapse = ", ")))
  }
  df
}

read_bundle_table <- function(manifest, label_pattern, bundle = NULL) {
  rows <- manifest %>%
    filter(asset_kind == "table", grepl(label_pattern, label))
  if (!is.null(bundle)) {
    rows <- rows %>% filter(bundle == !!bundle)
  }
  if (nrow(rows) < 1) {
    stop(paste("No manifest row matched label pattern:", label_pattern))
  }
  path <- rows$output_xlsx_path[[1]]
  resolved <- path
  if (!file.exists(resolved)) {
    parent_candidate <- file.path("..", path)
    if (file.exists(parent_candidate)) {
      resolved <- parent_candidate
    }
  }
  if (!file.exists(resolved)) {
    stop(paste("Missing exported table:", path))
  }
  readxl::read_excel(resolved)
}

ensure_output_dir <- function(output_dir) {
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  normalizePath(output_dir, winslash = "/", mustWork = TRUE)
}

save_panel <- function(plot_obj, output_path, width = 8, height = 5, dpi = 320) {
  ggplot2::ggsave(output_path, plot = plot_obj, width = width, height = height, dpi = dpi, bg = "white")
  output_path
}

plot_lag_curve <- function(df, title, x_col = "lag_ms", y_col = "mean_effect") {
  ggplot(df, aes(x = .data[[x_col]], y = .data[[y_col]])) +
    geom_hline(yintercept = 0, color = "grey70", linewidth = 0.4) +
    geom_line(color = "#1b4d6b", linewidth = 0.9) +
    geom_point(aes(color = q_fdr < 0.05), size = 2) +
    scale_color_manual(values = c(`TRUE` = "#b22222", `FALSE` = "#1b4d6b"), guide = "none") +
    labs(title = title, x = "Lag (ms)", y = "Mean effect") +
    paper_theme()
}

plot_state_heatmap <- function(df, x, y, fill, title, midpoint = 0) {
  ggplot(df, aes(x = .data[[x]], y = .data[[y]], fill = .data[[fill]])) +
    geom_tile(color = "white", linewidth = 0.4) +
    scale_fill_gradient2(low = "#2166ac", mid = "white", high = "#b2182b", midpoint = midpoint) +
    labs(title = title, x = NULL, y = NULL, fill = fill) +
    paper_theme()
}

plot_support_summary <- function(df, title, value_col = "mean_similarity") {
  ggplot(df, aes(x = factor(archetype), y = .data[[value_col]])) +
    geom_col(fill = "#2c7fb8", width = 0.7) +
    geom_text(aes(label = n_subjects), vjust = -0.4, size = 3) +
    labs(title = title, x = "Archetype", y = value_col, subtitle = "Labels above bars show supporting subjects") +
    paper_theme()
}

plot_channel_heatmap <- function(df, title) {
  channel_cols <- setdiff(
    names(df),
    c(
      "analysis_family", "analysis_branch", "source_cache", "comparison_space", "assigned_archetype",
      "n_subjects", "total_samples", "peak_metric", "normalization", "n_states", "min_duration_ms", "patient_id"
    )
  )
  long_df <- df %>%
    select(assigned_archetype, all_of(channel_cols)) %>%
    pivot_longer(cols = all_of(channel_cols), names_to = "channel", values_to = "value")
  plot_state_heatmap(long_df, "channel", "assigned_archetype", "value", title = title, midpoint = 0) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1))
}

plot_archetype_loadings <- function(df, title) {
  network_cols <- setdiff(
    names(df),
    c(
      "analysis_family", "analysis_branch", "source_cache", "comparison_space", "archetype", "n_subjects",
      "n_state_assignments", "mean_similarity", "median_similarity", "min_similarity", "peak_metric",
      "normalization", "n_states", "min_duration_ms", "n_mapped_channels", "n_common_units",
      "orientation_sign", "patient_id", "n_channels", "n_peak_maps"
    )
  )
  long_df <- df %>%
    group_by(archetype) %>%
    summarise(across(all_of(network_cols), ~mean(.x, na.rm = TRUE)), .groups = "drop") %>%
    pivot_longer(cols = all_of(network_cols), names_to = "network", values_to = "loading")
  plot_state_heatmap(long_df, "network", "archetype", "loading", title = title, midpoint = 0) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1))
}

plot_model_order_curve <- function(subject_df, group_df, subject_y, group_y, title, y_label, retained_k = 4) {
  ggplot() +
    geom_vline(xintercept = retained_k, color = "#b22222", linewidth = 0.6, linetype = "dashed") +
    geom_line(
      data = subject_df,
      aes(x = n_states, y = .data[[subject_y]], group = patient_id),
      color = "grey70",
      linewidth = 0.4,
      alpha = 0.6
    ) +
    geom_point(
      data = subject_df,
      aes(x = n_states, y = .data[[subject_y]]),
      color = "grey70",
      size = 1.1,
      alpha = 0.6
    ) +
    geom_line(
      data = group_df,
      aes(x = n_states, y = .data[[group_y]]),
      color = "#1b4d6b",
      linewidth = 0.9
    ) +
    geom_point(
      data = group_df,
      aes(x = n_states, y = .data[[group_y]], fill = retained_main_text_default),
      color = "#1b4d6b",
      shape = 21,
      size = 2.3
    ) +
    scale_fill_manual(values = c(`TRUE` = "#b22222", `FALSE` = "white"), guide = "none") +
    scale_x_continuous(breaks = sort(unique(group_df$n_states))) +
    labs(title = title, x = "Number of field states (K)", y = y_label) +
    paper_theme()
}
