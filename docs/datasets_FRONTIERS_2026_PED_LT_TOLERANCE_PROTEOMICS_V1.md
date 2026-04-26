# FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS V1

Implemented as a **narrow article-figure marker layer**, not as a full supplementary-table ingest.

- Title: *Neutrophil-associated plasma proteomics identifies HDAC1 as a baseline biomarker of immune tolerance during immunosuppressant withdrawal after pediatric liver transplantation*
- Journal: Frontiers in Immunology (2026)
- DOI: `10.3389/fimmu.2026.1800926`
- Full text: [https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2026.1800926/full](https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2026.1800926/full)
- PDF: [https://public-pages-files-2025.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2026.1800926/pdf](https://public-pages-files-2025.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2026.1800926/pdf)

## Why it was promoted despite the unresolved supplement

The original plan was to ingest `DataSheet1.docx`. That exact file is still not directly downloadable here. But the public article already exposes enough high-confidence structure to justify a conservative V1:

- planned withdrawal cohort: `31`
- discovery plasma proteomics: `10` (`IT = 5`, `NIT = 5`)
- validation plasma ELISA cohort: `39` (`IT = 17`, `NIT = 22`)
- differential proteins in discovery analysis: `802`
  - `382` increased in IT
  - `420` decreased in IT
- explicitly discussed marker proteins:
  - `HDAC1`
  - `FCGR3B`
  - `PADI4`
  - `MAPK1`

## What V1 contains

This V1 layer stores:

- article-figure marker evidence for the proteins explicitly discussed in Results/Figure 6
- directionality for `IT vs NIT`
- HDAC1 validation context from the 39-sample ELISA cohort
- discovery cohort and validation cohort provenance

## What V1 does not claim

This V1 does **not** claim:

- full per-protein DIA matrix
- complete 802-protein differential table
- exact fold changes or p-values for each recovered marker

Those remain blocked on the unresolved `DataSheet1.docx` asset path.
