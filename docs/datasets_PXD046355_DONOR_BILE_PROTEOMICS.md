# PXD046355 donor-liver bile proteomics

## Why this source matters

`PXD046355` is one of the stronger direct donor-liver proteomics sources we have found so far because it is not limited to a published marker table. It exposes a reusable PRIDE search-engine report with `4,408` protein groups across `142` bile samples collected during normothermic machine perfusion (NMP) of human donor livers.

That makes it a useful bridge between:

- donor-liver quality
- biliary viability during machine perfusion
- early regenerative biology
- proteomics evidence that is richer than article-only differential summaries

## Public evidence chain

- PRIDE project: [PXD046355](https://www.ebi.ac.uk/pride/archive/projects/PXD046355)
- Article: [Nature Communications 2023](https://www.nature.com/articles/s41467-023-43368-y)
- PRIDE processed report:
  - `NMP_Bile_Proteomics_Report.txt`
- Nature source data:
  - `41467_2023_43368_MOESM4_ESM.xlsx`
- Supplementary PDF:
  - `41467_2023_43368_MOESM1_ESM.pdf`

## What is reusable right now

### Strongly reusable

- sample-level protein-group quantity matrix from PRIDE
- `142` sample columns
- `4,400+` gene-annotated protein-group rows
- sample IDs matching the Nature source-data workbook

### Recoverable metadata

From Nature source-data sheets we can recover:

- sample accession
- donor liver number
- NMP timepoint
  - `30min`
  - `150min`
  - `End`
- liver-level biliary viability group
  - `High`
  - `Low`

### Partially recoverable metadata

- total BDI score / BDI group appears in source data but some rows rely on merged-cell layout
- transplantability is visible for a defensible public subset: `114` samples from `44` donor livers can be labeled as `Transplanted` or `Non-transplanted` by joining Figure 4a back to Figure 3a via liver number and timepoint
- the remaining `28` samples from `11` donor livers should stay unlabeled rather than be imputed

## Current V1 decision

This source is strong enough for a **sample-level V1 proteomics layer** if we keep the framing tight:

- main scope: `donor_bile_nmp_viability_timecourse`
- main contrast axis:
  - `high_biliary_viability_donor_liver`
  - `low_biliary_viability_donor_liver`
- secondary public subset axis:
  - `transplanted_donor_liver`
  - `non_transplanted_donor_liver`
- main timepoints:
  - `30min`
  - `150min`

We should **not** overstate:

- low-viability `End` samples are sparse
- transplantability is only explicit for figure-linked subsets
- this is donor-organ viability biology, not recipient post-transplant outcome evidence

## Expected database role

Best fit:

- `DONOR_LIVER_QUALITY`

Possible secondary fit later:

- a dedicated machine-perfusion / biliary-viability use case

## V1 caveats

- Use PRIDE `PG.Quantity` as the quantitative matrix and compute contrasts on `log2(PG.Quantity + 1)`.
- Treat biliary-viability labels as donor-liver context, not recipient outcome.
- Keep BDI-based interpretation descriptive unless merged-cell reconstruction is independently verified.
