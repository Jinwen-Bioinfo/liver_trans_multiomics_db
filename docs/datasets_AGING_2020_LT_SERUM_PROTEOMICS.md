# AGING_2020_LT_SERUM_PROTEOMICS

Direct liver-transplant serum proteomics biomarker layer derived from the public Aging-US article and supplementary tables:

- Article: [https://www.aging-us.com/article/103381/text](https://www.aging-us.com/article/103381/text)
- DOI: `10.18632/aging.103381`
- Supplementary quantitative tables: `aging-v12i12-103381-supplementary-material-SD2.pdf`

## Why it matters

This source adds a transplant-specific proteomics layer to the database, rather than only a liver-cell reference proteome. It is useful for:

- acute rejection versus stable post-transplant serum biomarker interpretation
- ischemic-type biliary lesion versus stable post-transplant comparison
- perioperative pre/post-transplant effectiveness context
- non-invasive blood-monitoring use cases

## Publicly reusable evidence

The publication exposes group-level MALDI-TOF peak summaries with mean, SD, and sample count in Supplementary Tables 2-4. The full text links peaks to proteins in Table 1.

Current queryable proteins:

- `ACLY` / `P53396`
- `FGA` / `P02671`
- `APOA1` / `P02647`

Clinical groups represented:

- `healthy_control` (`n=10`)
- `pre_transplant_end_stage_liver_disease` (`n=10`)
- `stable_post_transplant` (`n=10`)
- `acute_rejection` (`n=10`)
- `ischemic_type_biliary_lesion` (`n=9`)

## Processing choices

- data source: article text plus supplementary PDF tables
- effect scale: `relative_maldi_tof_peak_intensity`
- statistics: Welch t-test from published summary statistics with BH correction
- output artifacts:
  - `samples.json`
  - `sample_summary.json`
  - `cohort_summary.json`
  - `proteomics_summary.json`
  - `protein_features.json`
  - `source_file_inventory.json`
  - `analysis_provenance.json`

## Caveats

- This is not a reusable per-sample proteome matrix.
- Evidence is reconstructed from published group means and SDs.
- Protein-level interpretation depends on the article's explicit peptide-peak identification table.
- This layer should be treated as direct transplant proteomics biomarker evidence, but not as a full discovery proteomics cohort.
