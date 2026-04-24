# PXD062924

- Source article: [Frontiers full text](https://www.frontiersin.org/journals/transplantation/articles/10.3389/frtra.2025.1572852/full)
- PRIDE accession: [PXD062924](https://www.ebi.ac.uk/pride/archive/projects/PXD062924)
- Title: `Metabolomic and proteomic analyses of renal function after liver transplantation`
- Journal: `Frontiers in Transplantation` (2025)
- DOI: `10.3389/frtra.2025.1572852`
- Modality: `proteomics`
- Sample origin: `post-transplant recipient serum`
- Clinical comparison: `normal kidney function post-LT (n=5)` vs `impaired kidney function post-LT (n=4)`, with `1` recovered patient described separately

## Why it matters

This is a direct liver-transplant serum proteomics cohort tied to a concrete post-transplant clinical complication: renal dysfunction. That makes it useful for the database because it adds a blood-based protein layer that is:

- directly linked to liver transplantation rather than a generic kidney cohort
- mechanistically adjacent to post-LT injury monitoring
- complementary to blood RNA and serum metabolomics layers already in the database

Representative proteins from the published differential table include:

- `B2M`
- `AMBP`
- `TF`
- `APOA1`
- `SLPI`

## Publicly reusable artifact

The reusable public artifact for V1 is the published **Table 3 differential protein list** in the article body, combined with **Table 4 Reactome pathway annotations**. Together they expose:

- `UniProt accession`
- `protein name`
- `peptide count`
- `p value`
- `fold change (Normal-KF / Impaired-KF)`
- pathway-number links to Reactome pathway names

What is **not** publicly reusable in this version:

- a sample-by-protein abundance matrix
- per-patient longitudinal intensities at week 2 and week 5
- direct recovered-patient protein abundance values

## Database interpretation

Inside this database, `PXD062924` should be framed as:

- `direct transplant proteomics evidence`
- `recipient-serum renal dysfunction monitoring`
- **not** a rejection classifier
- **not** a reusable per-sample proteomics matrix

## Current ingest status

- `processed_feature_ready`
- Exposed as `protein_features.json`, `proteomics_summary.json`, `samples.json`, `sample_summary.json`, and `analysis_provenance.json`
- Queryable through `/api/features/{symbol}/protein`

## Main caveat

The article clearly reports `45` differential proteins and `174` quantified proteins, but the public evidence layer is still derived from the article table rather than from raw-spectrum or per-sample processed abundances. So it should be described honestly as **published serum differential-table evidence for post-LT renal dysfunction monitoring**.
