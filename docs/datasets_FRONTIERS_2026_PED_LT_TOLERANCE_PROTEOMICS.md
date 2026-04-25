# FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS

Candidate next-step direct transplant proteomics source.

- Title: *Neutrophil-associated plasma proteomics identifies HDAC1 as a baseline biomarker of immune tolerance during immunosuppressant withdrawal after pediatric liver transplantation*
- Journal: Frontiers in Immunology (2026)
- DOI: `10.3389/fimmu.2026.1800926`
- Full text: [https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2026.1800926/full](https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2026.1800926/full)
- OA package record: [https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC13061671](https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC13061671)

## Why this source matters

This is currently one of the strongest visible next proteomics targets because it is:

- direct liver-transplant human cohort data
- plasma proteomics rather than reference tissue context
- tied to a concrete clinical question: baseline risk stratification for immunosuppressant withdrawal
- likely to include reusable supplementary tables (`DataSheet1.docx`) according to the Frontiers XML

## Public evidence confirmed so far

From the public article and XML:

- primary analytic cohort: `31` pediatric liver transplant recipients undergoing planned withdrawal
- discovery proteomics performed in baseline plasma from `10` recipients
- validation cohort: `39` baseline plasma samples with HDAC1 ELISA
- outcome framing: `immune-tolerant (IT)` vs `non-immune-tolerant (NIT)`
- method: LC-MS DIA proteomics processed in Spectronaut Pulsar with local normalization
- article XML exposes supplementary material handle:
  - `DataSheet1.docx`

## Expected database value

If the supplementary table is downloadable and machine-readable, this source could become:

- a second direct transplant proteomics layer beyond the current Aging serum biomarker source
- the first proteomics layer in the database explicitly aligned to `operational_tolerance / withdrawal risk`
- a natural protein complement to blood-based transcriptome monitoring use cases

## Planned ingest decision

Promote to a processed layer only if `DataSheet1` exposes at least one of:

- per-protein abundance table
- differential protein list with effect size and significance
- enough group-level statistics to reconstruct IT vs NIT protein evidence

If the supplement only contains pathway figures or narrative summaries, keep it in triage and do not overstate readiness.

## Current blocker

As of 2026-04-25, the source is **scientifically promising but not yet machine-ingested** because:

- Frontiers article HTML and `__NUXT_DATA__` confirm a supplementary attachment with:
  - `@_xlink:href = DataSheet1.docx`
  - `@_mimetype = application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- NCBI OA metadata confirms an open-access package for `PMC13061671`
- the obvious public asset paths were tested and failed:
  - standard `frontiersin.org/.../file/DataSheet1.docx` patterns returned `404`
  - `public-pages-files-2025.frontiersin.org/.../DataSheet1.docx` patterns also returned `404`
- so the blocker is now narrow and concrete: **the supplement filename is public, but the resolved downloadable asset URL is still missing**

So the source remains:

- `ready_to_ingest` in triage from a scientific-priority perspective, but still blocked at the asset-resolution step
- not yet promoted into `studies.json` / `multiomics_sources.json`
- not yet exposed as a database protein layer

## Immediate next step

Resolve one of these access paths:

1. download the Frontiers `DataSheet1.docx` manually or via a working OA-package mirror
2. extract the actual supplement URL from a browser session with successful article asset resolution
3. if neither path works, deprioritize for now and continue with the next public direct transplant proteomics cohort
