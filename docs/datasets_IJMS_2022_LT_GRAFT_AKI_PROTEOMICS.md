# IJMS_2022_LT_GRAFT_AKI_PROTEOMICS

- Source article: [PMC9569532](https://pmc.ncbi.nlm.nih.gov/articles/PMC9569532/)
- Title: `Liver Graft Proteomics Reveals Potential Incipient Mechanisms behind Early Renal Dysfunction after Liver Transplantation`
- Journal: `International Journal of Molecular Sciences` (2022)
- DOI: `10.3390/ijms231911929`
- Modality: `proteomics`
- Sample origin: `postreperfusion liver graft biopsy`
- Clinical comparison: `moderate/severe early AKI (n=7)` vs `no early AKI (n=7)`

## Why it matters

This is a direct liver-transplant graft-tissue proteomics cohort, which makes it much more valuable than generic liver reference proteomes when we want to study early graft injury biology. It helps bridge the gap between:

- graft transcriptomic injury/rejection states
- serum biomarker layers
- tissue-level inflammatory and endothelial protein signals

Representative proteins highlighted by the published table and validation sections include:

- `SAA2`
- `PLA2G2A`
- `PECAM1`
- `APOA1`
- `CTSC`

## Publicly reusable artifact

The currently reusable public artifact is the published **Table 2 differential protein list** in the article PDF. It includes:

- `UniProt accession`
- `gene symbol`
- `fold change (average value)`
- `p value`

What is **not** publicly reusable in this version:

- a per-sample protein abundance matrix
- raw-spectrum reprocessing outputs connected to sample-level intensities

## Database interpretation

In this database, the layer is intentionally framed as:

- `direct transplant proteomics evidence`
- `tissue-level postreperfusion graft injury context`
- **not** a rejection-specific classifier
- **not** a per-sample proteomics matrix

## Current ingest status

- `processed_feature_ready`
- Exposed as `protein_features.json`, `proteomics_summary.json`, `samples.json`, `sample_summary.json`, and `analysis_provenance.json`
- Queryable through `/api/features/{symbol}/protein`

## Main caveat

The article reports `136` differentially expressed proteins, while the current PDF-layout parser exposes the queryable subset recoverable from the public PDF text extraction. This is still useful as a direct transplant proteomics layer, but it should be described honestly as **published differential-table evidence**.
