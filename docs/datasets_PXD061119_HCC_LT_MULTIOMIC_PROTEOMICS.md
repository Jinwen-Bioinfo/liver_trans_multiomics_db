# PXD061119: HCC liver-transplant multi-omic proteomics candidate

## Why this source matters

`PXD061119` is a high-value direct liver-transplant proteomics candidate because it is tied to a large transplant-recipient tumor cohort rather than a small marker-only paper. The linked Nature Communications study analyzes HCC patients who underwent liver transplantation beyond the Milan criteria and explicitly states that proteomics was performed on the derivation cohort.

That makes it potentially useful for:

- post-LT HCC biology
- recurrence-risk stratification
- transplant-specific tumor proteomics
- integrating a larger-scale proteomics matrix than most article-only transplant studies

## Public evidence chain

- Article: `10.1038/s41467-025-59745-8`
- PubMed: `PMID 40355422`
- PMC: `PMC12069600`
- Proteomics repository identifier stated in the article:
  - `PXD061119`
- iProX project page stated in the article:
  - `https://www.iprox.cn/page/project.html?id=IPX0011178000`

The article text states:

- the derivation cohort included `122` explant tumors
- `94` of those were suitable for proteomics
- the proteomics data were deposited in iProX as `PXD061119`

## What is already recoverable

This source is stronger than a metadata-only entry because the iProX public project endpoints expose a direct processed matrix:

- `Protein_matrix.txt`

The matrix is publicly reachable through the iProX download controller and is already confirmed to contain:

- `4,578` protein rows
- `97` total columns
- `94` quantitative sample columns
- three annotation columns:
  - `Protein accession`
  - `Gene name`
  - `Protein description`

The sample columns use IDs like:

- `L001`
- `L012`
- `L041`
- `L103`

The sample count exactly matches the article's statement that `94` derivation-cohort tumors were suitable for proteomics.

## Current blocker

The blocker is no longer matrix availability. The blocker is sample-label interpretation.

What still needs to be recovered from explicit public metadata:

- how each `L###` sample maps to the clinical cohort table
- whether `L###` labels can be joined to recurrence, survival, or molecular subgroup outcomes
- which samples belong to each transcriptomic/proteomic subgroup described in the paper
- whether the publicly available matrix is already normalized log-intensity, z-scored abundance, or another transformed scale

The PMC XML confirms that the article has:

- `Supplementary Data 1`
- `Source Data`
- a stated data-availability paragraph that points to the iProX proteomics deposition

Those supplementary files are the most likely place where sample-to-subgroup mapping would live.

## What has now been checked directly

The recovery path is now much stronger than before:

- the Nature article page exposes direct `static-content.springer.com` links for:
  - `41467_2025_59745_MOESM1_ESM.docx`
  - `41467_2025_59745_MOESM3_ESM.xlsx`
  - `41467_2025_59745_MOESM6_ESM.xlsx`
- all three files are now locally recoverable
- the iProX project XML and subproject XML are also directly recoverable

What those files do and do not provide:

- `MOESM1`:
  - contains supplementary figures and aggregate supplementary tables
  - confirms cohort-level summaries for the derivation cohort (`n = 100`) and validation cohort (`n = 80`)
  - contains a transcriptomic validation signature table
  - does **not** expose `L###`-level proteomics sample mapping
- `MOESM3`:
  - contains the validation-cohort high-expression gene lists used for transcriptomic grouping
  - does **not** expose proteomics sample IDs
- `MOESM6`:
  - contains source-data sheets for figure panels (`Figure 5`, `Figure 6`, `Figure S11`)
  - does **not** contain the derivation-cohort proteomics matrix or `L###` sample annotations
- iProX XML:
  - confirms the public file list and public download routes
  - does **not** include assay/sample metadata linking `L###` to recurrence, survival, or subgroup

So the missing piece is no longer download access. The missing piece is still the public metadata needed to assign biological labels to the `L###` columns.

## Status decision

Current registry status can remain:

- `source_review_needed`

Rationale:

- a direct sample-level transplant proteomics matrix is already public
- the cohort size is strong enough to matter
- but promoting this to an ingest layer should wait until the `L###` sample labels can be mapped to explicit public outcomes or subgroups, or until a clearly defined unsupervised exploratory layer is intentionally chosen

## Next step

The next recovery pass should focus on:

1. checking whether any additional Nature-hosted source-data artifact beyond `MOESM6` contains the hidden derivation-cohort panel used for `Figure 2D–G`
2. checking whether any iProX-side metadata outside the project XML expose assay/sample annotations for `L###`
3. promoting `PXD061119` once that sample mapping is explicit enough for a defensible post-LT HCC proteomics layer
