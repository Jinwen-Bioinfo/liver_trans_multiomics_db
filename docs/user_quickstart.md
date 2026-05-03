# User Quickstart

This quickstart is the shortest honest path to understanding what LiverTx-OmicsDB already does well.

## Start With a Scientific Question

Do not begin with accession hunting unless you already know exactly what you need. The strongest current entry points are the three demonstrator questions:

1. `INJURY_VS_REJECTION`
2. `DONOR_LIVER_QUALITY`
3. `BLOOD_MONITORING`

These are the most mature examples of question-first evidence organization in the resource.

## Recommended Walkthroughs

### 1. Early Injury Versus Rejection

Open:

- `#use-case/INJURY_VS_REJECTION`

Then inspect:

- `#study/GSE145780`
- `#feature/CXCL10`

Why start here:

- it shows how tissue transcriptomics, graft proteomics, and serum marker layers are kept in one interpretive frame
- it also shows the current restraint of the resource: this is structured multimodal context, not a diagnostic classifier

### 2. Donor Liver Quality and Viability

Open:

- `#use-case/DONOR_LIVER_QUALITY`

Then inspect:

- `#study/GSE243887`
- `#feature/CYP3A4`

Why start here:

- it is one of the clearest transplant-specific differentiators in the project
- it keeps donor selection, biliary viability, and recipient outcome claims visibly separate

### 3. Blood Monitoring and Tolerance Context

Open:

- `#use-case/BLOOD_MONITORING`

Then inspect:

- `#study/GSE200340`
- `#feature/CXCL10`

Why start here:

- it shows the broadest current cross-omics scope
- it also makes the evidence-strength differences between blood transcriptomics, metabolomics, and serum/plasma proteomics visible

## How To Read a Use-Case Page

Each demonstrator use-case page is organized into four sections:

1. `Evidence overview`
2. `Dataset-level evidence`
3. `Biological interpretation`
4. `Practical boundary`

Read them in that order. The page is designed so you can see:

- what the question is
- which layers are strong versus partial
- what cross-omics interpretation is reasonable
- what the database does **not** yet support

## How To Read Evidence Grades

- `A`: reusable sample-level matrix or directly queryable cohort table
- `B`: reusable feature-level or contrast-level evidence
- `C`: marker-layer or figure-recovered evidence
- `R`: reference context
- `M`: metadata-only or unresolved candidate

These grades are there to stop the resource from pretending that every public layer carries the same evidentiary weight.

## What To Download First

If you want to verify visible claims, start with:

- `sample_summary`
- `protein_features` or `metabolomics_features`
- `gene_expression_summary`
- `analysis_provenance`

Those artifacts are usually the fastest route to checking whether a visible claim is backed by a real processed layer.

## What Not To Assume

Do not assume that:

- every proteomics layer is sample-level
- every blood layer is a rejection classifier
- donor-organ acceptance labels equal recipient outcome labels
- reference proteomes are direct transplant evidence

The database is strongest when those boundaries stay explicit.

## Related Resource Documents

- `docs/project_north_star.md`
- `docs/demonstrator_use_cases_plan.md`
- `docs/demonstrator_evidence_tables.md`
- `docs/demonstrator_cross_omics_mappings.md`
