# GSE200340 Pediatric Liver Transplant Blood RNA-seq

GSE200340 is a public whole-blood/PBMC RNA-seq dataset for pediatric liver transplantation monitoring.

## Processed Data

- Samples: 185 blood/PBMC samples.
- States: 75 pre-transplant, 55 early post-transplant, and 55 late post-transplant samples.
- Source matrix: GEO supplementary archive `GSE200340_RAW.tar` containing per-sample RSEM gene-level results.
- Gene identifiers: RSEM `gene_id` field, already represented as gene symbols in the source files.
- Normalization: log2(CPM + 1), computed from RSEM `expected_count` values within the study.

## Contrasts

The database exposes three exploratory monitoring contrasts:

- `early_post_transplant_blood_vs_pre_transplant_blood`
- `late_post_transplant_blood_vs_pre_transplant_blood`
- `late_post_transplant_blood_vs_early_post_transplant_blood`

## Caveat

GEO sample metadata exposes blood sampling time points but not rejection outcome labels. This layer supports longitudinal blood monitoring evidence and should not be interpreted as a rejection-outcome classifier.
