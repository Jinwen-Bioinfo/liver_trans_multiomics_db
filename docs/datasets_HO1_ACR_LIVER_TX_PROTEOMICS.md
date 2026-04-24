# HO-1 ACR liver-transplant proteomics direct evidence layer

## Source

- PMID: `32309368`
- PMCID: `PMC7154463`
- Article URL: `https://atm.amegroups.org/article/view/37242/html`

Title:

`Identification of HO-1 as a novel biomarker for graft acute cellular rejection and prognosis prediction after liver transplantation`

## Current status

This source is now implemented locally as `HO1_ACR_LIVER_TX_PROTEOMICS`, using OCR-recovered Supplementary Table S2 plus article-text iTRAQ tag mapping and Supplementary Table S1 cohort metadata.

## Public facts already confirmed

- direct liver-transplant rejection context
- iTRAQ-based proteomics in a training set comparing acute cellular rejection versus non-rejection recipients
- training-set size reported in the article:
  - `n=3` acute cellular rejection
  - `n=3` non-rejection
- exact iTRAQ labels reported in the article:
  - ACR: `118`, `119`, `121`
  - non-rejection: `113`, `115`, `117`
- reported DEP count:
  - `287` differential proteins
- article text explicitly states that detailed DEPs are listed in `Table S2`

## What the current implementation does

- exposes a direct transplant serum proteomics layer for:
  - `acute_cellular_rejection`
  - `non_rejection_post_lt`
- reconstructs the six-sample training set:
  - `n=3` acute cellular rejection
  - `n=3` non-rejection
- makes OCR-recovered differential proteins queryable, including:
  - `HMOX1`
  - `BLVRA`
  - `ACLY`
  - `HDAC1`
  - `CYP3A4`
- keeps the layer explicitly labeled as published differential-table evidence rather than a reusable per-sample matrix

## Best use-case fit

This layer currently supports:

- molecular rejection context
- injury-versus-rejection separation
- protein-level transplant biomarker evidence

It still should not be overstated as a matrix-level cohort, because the public supplementary evidence is exposed as PNG tables and the V1 database layer is OCR-recovered rather than author-supplied machine-readable quantification.
