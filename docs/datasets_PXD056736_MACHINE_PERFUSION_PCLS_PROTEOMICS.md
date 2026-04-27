# PXD056736: Human donor-liver machine-perfusion PCLS proteomics candidate

## Why this source matters

`PXD056736` is a strong direct donor-liver proteomics candidate because it is tied to human livers used in a machine-perfusion context rather than an adjacent cell-line or animal model. The linked article focuses on whether mild hyperthermia changes metabolic and stress-response biology in livers that are relevant to graft utilization.

That makes it potentially useful for:

- donor-liver quality biology
- machine-perfusion response
- fatty-liver graft optimization
- transplant-adjacent proteomics richer than a small marker-only table

## Public evidence chain

- PRIDE project: `https://www.ebi.ac.uk/pride/archive/projects/PXD056736`
- Article: `10.14814/phy2.70348`
- PubMed: `PMID 40346031`
- PMC: `PMC12064339`
- Figshare supplementary record: `10.6084/m9.figshare.28495418.v1`

The article explicitly describes proteomic profiling of:

- whole-organ perfusion samples
- precision-cut liver slices (PCLS)
- human donor livers under `37°C` versus `40°C` conditions

## What is already recoverable

PRIDE exposes a reusable processed report:

- `PCLS_report.txt`

That file is directly reusable and currently confirmed to contain:

- `6,028` protein-group rows
- `118` quantitative sample columns
- a gene-symbol annotation column for every row
- per-sample quantity columns named like `PCLS_Sample_6.raw.PG.Quantity`

This means the source is not raw-only. It already contains a sample-level protein matrix.

## What the article makes clear

From the open-access article text we can defensibly recover the high-level study design:

- PCLS experiments were initially conducted on `24` human donor livers
- `6` livers were excluded by ATP-based viability criteria
- proteomics-relevant PCLS experiments continued on `18` donor livers
- slices were studied at `0`, `3`, `24`, and `48 h`
- incubation conditions included both `37°C` and `40°C`
- the article describes timepoint-associated PCA structure and stronger perturbation at `40°C`, especially by `24` and `48 h`

So the biological question is real and the matrix is real.

## Current blocker

The blocker is now sample-design mapping, not matrix availability.

What still cannot be defended from the public files currently in hand:

- which `PCLS_Sample_*` columns correspond to `0 h`, `3 h`, `24 h`, or `48 h`
- which columns correspond to `37°C` versus `40°C`
- which columns belong to the same donor liver
- whether the report contains all PCLS observations used in the main text or a filtered subset

The sample numbering pattern strongly suggests hidden structure:

- present IDs begin at `6`
- there is a complete missing block from `16` to `26`
- another missing block from `72` to `78`
- observed IDs then continue through `141`

That is consistent with mixed acquisition batches or omitted non-PCLS acquisitions, but the current public matrix alone does not assign biological meaning to those blocks.

## Supplementary-material status

The article points to supplementary material on Figshare and states that additional data are available in supplementary materials. However, in the current execution environment:

- the Figshare metadata API is reachable
- the supplementary file record is visible
- direct file download currently fails because the redirected object-store request is not completing cleanly here
- PMC supplementary file URLs are additionally protected by a Recaptcha challenge in this environment

So the most likely route to finish this source is to recover the supplementary PDF or source-data attachment from a network path that does not inject those download barriers.

## Status decision

Current registry status should remain:

- `source_review_needed`

Rationale:

- the source already has a reusable sample-level protein matrix
- the transplant relevance is strong
- but there is still no defensible public mapping from `PCLS_Sample_*` columns to temperature, timepoint, and donor identity

## Next step

The next recovery pass should focus on:

1. obtaining the Figshare supplementary PDF from a working network path
2. checking whether that supplement or any source-data file maps `PCLS_Sample_*` IDs to donor, timepoint, and temperature
3. promoting the source only after those labels can be assigned from explicit public metadata rather than acquisition-order guessing
