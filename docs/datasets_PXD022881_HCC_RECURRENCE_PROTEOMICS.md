# PXD022881 HCC recurrence proteomics

`PXD022881` is one of the stronger direct liver-transplant proteomics sources we have recovered because it exposes a reusable MaxQuant LFQ matrix instead of only a narrow article marker panel. The biological question is not rejection. It is whether the HCC tumor explant removed at the time of liver transplantation carries molecular features associated with **subsequent post-transplant recurrence** in recipients transplanted **beyond Milan criteria**.

## Why it matters

This source adds a direct tumor-explant protein layer for a clinically important question that is still underrepresented in the database:

- which explant proteins are higher in recipients who later recur after liver transplantation
- whether known markers such as `ALDH1A1`, `LGALS3`, and `LGALS3BP` are queryable inside the database rather than only mentioned in prose
- how to treat partial but defensible sample-label recovery from public supplementary figures without overclaiming full cohort metadata

## Public evidence chain

- PRIDE project: [PXD022881](https://www.ebi.ac.uk/pride/archive/projects/PXD022881)
- Article: [Clinical Proteomics 2021](https://clinicalproteomicsjournal.biomedcentral.com/articles/10.1186/s12014-021-09333-x)
- Supplementary Figure S1 PDF: [MOESM1 PDF](https://static-content.springer.com/esm/art%3A10.1186%2Fs12014-021-09333-x/MediaObjects/12014_2021_9333_MOESM1_ESM.pdf)

The article reports a discovery cohort of **7 recurrent** versus **4 non-recurrent** HCC tumor explants. The PRIDE `combined.zip` bundle independently exposes:

- `combined/experimentalDesignTemplate.txt`
- `combined/txt/summary.txt`
- `combined/txt/parameters.txt`
- `combined/txt/proteinGroups.txt`

Those files are enough to recover a sample-level LFQ matrix without downloading the full 12 GB archive.

## What was recoverable

From the PRIDE design:

- `12` public design samples
- `10` fractions per sample
- sample accessions `HCC_LiverTissue_Sample1` through `HCC_LiverTissue_Sample12`

From Supplementary Figure S1 panel C:

- red labels = recurrent
- blue labels = non-recurrent

This makes the following **11-sample published subset** defensibly recoverable:

- recurrent: `1, 2, 5, 6, 7, 9, 12`
- non-recurrent: `3, 4, 10, 11`

Important caveat:

- `Sample 8` is present in the PRIDE design and LFQ matrix but is **not labeled** in the published PCA panel, so it remains public-but-unlabeled and is excluded from recurrence contrasts.

## Database framing

The current ingest is intentionally conservative:

- sample-level LFQ protein matrix: yes
- recurrence labels for all 12 design samples: no
- recurrence contrasts: yes, but only on the 11 labeled published-subset samples
- full reproduction of the article's imputation workflow: no

So this layer should be described as:

> direct tumor-explant proteomics evidence for post-transplant HCC recurrence risk, using a reusable PRIDE matrix plus partial public label recovery from Supplementary Figure S1

and not as:

> a fully annotated, publication-identical reanalysis of the entire PRIDE cohort

## V1 output

The current database layer provides:

- `12` total design samples
- `11` recurrence-labeled published-subset samples
- `6,196` queryable gene-level protein features
- log2 LFQ group summaries
- Welch t-test and BH-FDR on the labeled subset

Representative features:

- `ALDH1A1`
- `LGALS3`
- `LGALS3BP`
- `S100A10`
- `ANXA2`

## Main limitations

1. `Sample 8` remains unlabeled in the public evidence chain.
2. The article used a more publication-specific missing-value handling workflow than this database V1.
3. This is **tumor-explant prognostic biology**, not rejection biology and not a non-invasive blood classifier.
