# S-EPMC6493459

Processed direct serum proteomics layer derived from:

- Title: *Comparative proteomic analysis of human serum before and after liver transplantation using quantitative proteomics*
- Journal: Oncotarget (2019)
- DOI: `10.18632/oncotarget.26761`
- Full text: [https://www.oncotarget.com/article/26761/text/](https://www.oncotarget.com/article/26761/text/)

## Why this source is useful

This source adds a direct liver-transplant serum proteomics cohort with a peri-transplant timecourse:

- healthy controls: `n = 9`
- the same liver-transplant recipients sampled:
  - pre-transplant: `n = 9`
  - day 1 post-LT: `n = 9`
  - day 3 post-LT: `n = 9`
  - day 7 post-LT: `n = 9`

It is not a rejection dataset, but it does add blood-based peri-transplant proteomic context that is still missing from most transplant databases.

## Publicly recoverable evidence

The public Oncotarget full text exposes:

- study design and group sizes (Table 3)
- `1,399` identified proteins
- `112` proteins upregulated in pre-transplant serum versus healthy controls
- a visible partial `Table 1` with the highest-ratio proteins, including:
  - `S100P`
  - `ITGB4`
  - `CLTC`
  - `PADI4`
  - `SPP1`
- `Table 2` retinol-metabolism proteins with lower pre-transplant abundance, including:
  - `AOX1`
  - `ADH1A`
  - `ADH1B`
  - `ADH4`
  - `ADH6`

## V1 database framing

This source is promoted as:

- direct liver-transplant serum proteomics
- peri-transplant / pre-vs-post context
- partial published-table evidence

It is **not** promoted as:

- a complete sample-level iTRAQ matrix
- a rejection or tolerance classifier
- a full longitudinal feature table for day 1/day 3/day 7 post-transplant contrasts

## Main limitations

- Only a partial visible subset of protein rows is machine-recoverable from the public article text.
- The directly reusable feature ratios are limited to `pre-transplant vs healthy control`.
- The post-transplant days are documented at the cohort-design level, but reusable day-specific protein tables are not exposed in the article text.

## Why it still belongs in the database

Even with those limits, this source is worth keeping because it:

- strengthens the serum proteomics side of the database
- adds peri-transplant temporal context rather than only complication/rejection snapshots
- provides queryable liver-transplant-linked protein evidence for `S100P`, `AOX1`, and retinol-metabolism proteins
