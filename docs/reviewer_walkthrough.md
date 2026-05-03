# Reviewer Walkthrough

This walkthrough is for collaborators, internal reviewers, and future manuscript reviewers who need to judge whether LiverTx-OmicsDB is more than a dataset catalog.

## What Reviewers Should Look For

Reviewers should confirm that the resource:

1. is organized around transplant questions rather than accessions
2. distinguishes evidence strength visibly
3. keeps donor quality, blood monitoring, injury, rejection, and reference context separate
4. exposes downloadable artifacts and provenance
5. avoids overclaiming beyond what public evidence supports

## Review Path 1: Donor Quality Differentiator

Open:

- `#use-case/DONOR_LIVER_QUALITY`
- `#study/GSE243887`
- `#study/PXD046355`
- `#feature/CYP3A4`

What to verify:

- accepted versus rejected donor-organ RNA evidence is explicit
- biliary viability proteomics is separate from recipient outcome claims
- unresolved donor-quality candidates remain clearly marked as metadata-only or documentation-only

## Review Path 2: Injury Versus Rejection Framing

Open:

- `#use-case/INJURY_VS_REJECTION`
- `#study/GSE145780`
- `#study/IJMS_2022_LT_GRAFT_AKI_PROTEOMICS`
- `#feature/CXCL10`

What to verify:

- tissue transcriptomics and graft proteomics are shown in one question frame
- serum marker layers are visible but weaker
- the page explicitly states what the current resource does not yet support

## Review Path 3: Blood Multi-Omics Context

Open:

- `#use-case/BLOOD_MONITORING`
- `#study/GSE200340`
- `#study/MDPI_METABO_2024_LT_GRAFT_PATHOLOGY`
- `#feature/CXCL10`

What to verify:

- blood/PBMC RNA, serum metabolomics, and serum/plasma proteomics are all present
- monitoring and tolerance are related but not flattened into a single claim
- evidence grades are visible and interpretable

## Resource-Level Checks

Reviewers should also check:

- `/api/quickstart`
- `/api/resource-metadata`
- `docs/user_quickstart.md`
- `docs/resource_release_and_citation.md`
- `docs/nar_submission_readiness.md`

These items show whether the project is maturing into a durable resource rather than just a local analysis portal.

## Current Honest Limits

At the present stage, reviewers should expect:

- a strong local prototype
- explicit evidence grading
- question-driven views
- incomplete public deployment and DOI/citation infrastructure
- still-evolving QC, glossary, and long-form tutorial layers

That is acceptable as long as the resource stays transparent about those limits.
