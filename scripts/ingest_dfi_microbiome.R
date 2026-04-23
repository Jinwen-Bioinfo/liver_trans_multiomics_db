suppressPackageStartupMessages({
  library(jsonlite)
})

args_file <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])
script_path <- if (!is.na(args_file) && nzchar(args_file)) args_file else "scripts/ingest_dfi_microbiome.R"
root <- normalizePath(file.path(dirname(script_path), ".."), mustWork = TRUE)
source_id <- "DFI_MICROBIOME_LT_2024"
raw_dir <- file.path(root, "data", "raw", "external", source_id)
processed_dir <- file.path(root, "data", "processed", source_id)
dir.create(raw_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(processed_dir, recursive = TRUE, showWarnings = FALSE)

base_url <- "https://raw.githubusercontent.com/DFI-Bioinformatics/Microbiome_Liver_Transplant/main/Data"
files <- c(
  "demo_anon.rds",
  "first_samps_anon.rds",
  "metab_qual_anonym.rds",
  "metab_quant_anonym.rds",
  "metaphlan_anon.rds",
  "metaphlan_peri_anon.rds",
  "abx_anon.rds",
  "original_cohort_abx.rds",
  "peri_criteria_all_anon.rds",
  "peri_criteria_best_anon.rds",
  "sample_lookup.rds",
  "validation_cohort_demo.rds",
  "validation_cohort_metab_qual.rds",
  "validation_cohort_metaphlan.rds",
  "validation_cohort_peri_infection.rds"
)

sha256_file <- function(path) {
  parts <- strsplit(system2("shasum", c("-a", "256", path), stdout = TRUE), "\\s+")[[1]]
  parts[[1]]
}

download_if_missing <- function(filename) {
  target <- file.path(raw_dir, filename)
  if (!file.exists(target)) {
    download.file(file.path(base_url, filename), target, mode = "wb", quiet = TRUE)
  }
  target
}

safe_read <- function(filename) {
  path <- download_if_missing(filename)
  readRDS(path)
}

as_plain_df <- function(x) {
  as.data.frame(x, stringsAsFactors = FALSE)
}

field_counts <- function(values) {
  tab <- sort(table(values, useNA = "ifany"), decreasing = TRUE)
  as.list(as.integer(tab)) |>
    setNames(names(tab))
}

numeric_summary <- function(values) {
  values <- suppressWarnings(as.numeric(values))
  values <- values[is.finite(values)]
  if (!length(values)) {
    return(list(n = 0))
  }
  list(
    n = length(values),
    mean = round(mean(values), 6),
    median = round(stats::median(values), 6),
    min = round(min(values), 6),
    max = round(max(values), 6)
  )
}

summarize_rds <- function(filename) {
  path <- file.path(raw_dir, filename)
  obj <- readRDS(path)
  dims <- dim(obj)
  list(
    filename = filename,
    bytes = file.info(path)$size,
    sha256 = sha256_file(path),
    class = class(obj),
    dim = if (is.null(dims)) NULL else as.integer(dims),
    columns = if (is.null(names(obj))) NULL else names(obj)
  )
}

for (filename in files) {
  download_if_missing(filename)
}

demo <- as_plain_df(safe_read("demo_anon.rds"))
first_samps <- as_plain_df(safe_read("first_samps_anon.rds"))
metab_qual <- as_plain_df(safe_read("metab_qual_anonym.rds"))
metab_quant <- as_plain_df(safe_read("metab_quant_anonym.rds"))
metaphlan <- as_plain_df(safe_read("metaphlan_anon.rds"))
metaphlan_peri <- as_plain_df(safe_read("metaphlan_peri_anon.rds"))
abx <- as_plain_df(safe_read("abx_anon.rds"))
original_abx <- as_plain_df(safe_read("original_cohort_abx.rds"))

infection_by_patient <- demo[, c("patientID", "any_infection", "event_type")]
metab_quant_annot <- merge(metab_quant, infection_by_patient, by = "patientID", all.x = TRUE)
metab_qual_annot <- merge(metab_qual, infection_by_patient, by = "patientID", all.x = TRUE)
metaphlan_annot <- merge(metaphlan, infection_by_patient, by = "patientID", all.x = TRUE)

summarize_metabolites <- function(df) {
  compounds <- sort(unique(df$compound))
  rows <- lapply(compounds, function(compound) {
    sub <- df[df$compound == compound, , drop = FALSE]
    infected <- sub[sub$any_infection %in% TRUE, , drop = FALSE]
    not_infected <- sub[sub$any_infection %in% FALSE, , drop = FALSE]
    list(
      compound = compound,
      row_count = nrow(sub),
      patient_count = length(unique(sub$patientID)),
      sample_count = length(unique(sub$sampleID)),
      all_samples = numeric_summary(sub$mvalue),
      infection_positive = numeric_summary(infected$mvalue),
      infection_negative = numeric_summary(not_infected$mvalue)
    )
  })
  rows[order(vapply(rows, function(x) x$sample_count, numeric(1)), decreasing = TRUE)]
}

summarize_taxa <- function(df) {
  name_col <- if ("Species" %in% names(df)) "Species" else "#clade_name"
  value_col <- if ("relative_abundance" %in% names(df)) "relative_abundance" else "count"
  taxa <- sort(unique(df[[name_col]][!is.na(df[[name_col]]) & df[[name_col]] != ""]))
  rows <- lapply(taxa, function(taxon) {
    sub <- df[df[[name_col]] == taxon, , drop = FALSE]
    infected <- sub[sub$any_infection %in% TRUE, , drop = FALSE]
    not_infected <- sub[sub$any_infection %in% FALSE, , drop = FALSE]
    list(
      taxon = taxon,
      taxon_rank = name_col,
      row_count = nrow(sub),
      patient_count = length(unique(sub$patientID)),
      sample_count = length(unique(sub$sampleID)),
      all_samples = numeric_summary(sub[[value_col]]),
      infection_positive = numeric_summary(infected[[value_col]]),
      infection_negative = numeric_summary(not_infected[[value_col]])
    )
  })
  rows[order(vapply(rows, function(x) x$sample_count, numeric(1)), decreasing = TRUE)]
}

inventory <- list(
  source_id = source_id,
  generated_at_utc = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
  source_repository = "https://github.com/DFI-Bioinformatics/Microbiome_Liver_Transplant",
  raw_files = lapply(files[file.exists(file.path(raw_dir, files))], summarize_rds)
)

cohort_summary <- list(
  source_id = source_id,
  generated_at_utc = inventory$generated_at_utc,
  patient_count = length(unique(demo$patientID)),
  first_sample_patient_count = length(unique(first_samps$patientID)),
  infection_counts = field_counts(demo$any_infection),
  event_type_counts = field_counts(demo$event_type),
  sex_counts = field_counts(demo$sex),
  age_summary = numeric_summary(demo$age),
  antibiotic_row_count = nrow(abx),
  original_cohort_antibiotic_row_count = nrow(original_abx)
)

metabolomics_summary <- list(
  source_id = source_id,
  generated_at_utc = inventory$generated_at_utc,
  modality = "metabolomics",
  qualitative = list(
    row_count = nrow(metab_qual),
    patient_count = length(unique(metab_qual$patientID)),
    sample_count = length(unique(metab_qual$sampleID)),
    compound_count = length(unique(metab_qual$compound)),
    top_compounds_by_sample_count = head(summarize_metabolites(metab_qual_annot), 25)
  ),
  quantitative = list(
    row_count = nrow(metab_quant),
    patient_count = length(unique(metab_quant$patientID)),
    sample_count = length(unique(metab_quant$sampleID)),
    compound_count = length(unique(metab_quant$compound)),
    top_compounds_by_sample_count = head(summarize_metabolites(metab_quant_annot), 25)
  )
)

microbiome_summary <- list(
  source_id = source_id,
  generated_at_utc = inventory$generated_at_utc,
  modality = "microbiome",
  full_sample_set = list(
    row_count = nrow(metaphlan),
    patient_count = length(unique(metaphlan$patientID)),
    sample_count = length(unique(metaphlan$sampleID)),
    taxon_count = length(unique(metaphlan$`#clade_name`)),
    species_count = length(unique(metaphlan$Species[!is.na(metaphlan$Species) & metaphlan$Species != ""])),
    top_species_by_sample_count = head(summarize_taxa(metaphlan_annot), 25)
  ),
  peri_transplant_set = list(
    row_count = nrow(metaphlan_peri),
    patient_count = length(unique(metaphlan_peri$patientID)),
    sample_count = length(unique(metaphlan_peri$sampleID)),
    taxon_count = length(unique(metaphlan_peri$`#clade_name`))
  )
)

provenance <- list(
  source_id = source_id,
  generated_at_utc = inventory$generated_at_utc,
  parser = "scripts/ingest_dfi_microbiome.R",
  source_urls = list(
    github = "https://github.com/DFI-Bioinformatics/Microbiome_Liver_Transplant",
    article = "https://www.sciencedirect.com/science/article/pii/S1931312823004651",
    doi = "https://doi.org/10.1016/j.chom.2023.11.016"
  ),
  outputs = c(
    "data/processed/DFI_MICROBIOME_LT_2024/source_file_inventory.json",
    "data/processed/DFI_MICROBIOME_LT_2024/cohort_summary.json",
    "data/processed/DFI_MICROBIOME_LT_2024/metabolomics_summary.json",
    "data/processed/DFI_MICROBIOME_LT_2024/microbiome_summary.json"
  ),
  limitations = c(
    "RDS/RData objects are processed public analysis objects from the source repository, not raw mass spectrometry or shotgun sequencing reads.",
    "This ingest summarizes cohort, metabolite, and taxon tables; it does not yet reproduce the manuscript's multivariable infection-risk models.",
    "Metabolite and taxon identifiers require additional normalization to HMDB/ChEBI/PubChem and NCBI taxonomy."
  )
)

write_json <- function(x, filename) {
  writeLines(toJSON(x, pretty = TRUE, auto_unbox = TRUE, null = "null", na = "null"), file.path(processed_dir, filename))
}

write_json(inventory, "source_file_inventory.json")
write_json(cohort_summary, "cohort_summary.json")
write_json(metabolomics_summary, "metabolomics_summary.json")
write_json(microbiome_summary, "microbiome_summary.json")
write_json(provenance, "provenance.json")

cat(toJSON(list(
  source_id = source_id,
  patient_count = cohort_summary$patient_count,
  qualitative_metabolite_count = metabolomics_summary$qualitative$compound_count,
  quantitative_metabolite_count = metabolomics_summary$quantitative$compound_count,
  microbiome_taxon_count = microbiome_summary$full_sample_set$taxon_count,
  output_dir = file.path("data", "processed", source_id)
), pretty = TRUE, auto_unbox = TRUE))
