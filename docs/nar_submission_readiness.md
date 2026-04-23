# NAR Database Issue Readiness Plan

This document converts NAR Database Issue expectations into build requirements for LiverTx-OmicsDB.

Current target: **pre-submission inquiry for the NAR Database Issue after the database is fully functional online**.

## Hard Gates

| NAR expectation | Build requirement | Current status |
| --- | --- | --- |
| Database is freely available via web | Public production URL, stable domain, no login for public content | Not started |
| New database inquiry includes URL and description | Prepare a short plain-text proposal after V1 launch | Not started |
| Must explain how it is different and substantially better than similar resources | Maintain a living differentiation statement and comparison table | Started |
| Broad biological value | Frame as transplant immunology, graft injury, donor organ quality, and human disease omics integration | Started |
| Not a venue for unpublished computational/experimental results | Keep primary omics data tied to public repositories; mark derived analyses as value-added curation | Designed |
| Underlying sequence/expression/proteomics data public | Track accession URLs and public/controlled access status per study | Started |
| Help materials for first-time users | Add help pages, tutorials, examples, API docs, and glossary | Started |
| Legal and ethical responsibility for public data | Record license/access caveats and avoid redistributing controlled individual-level data | Designed |
| Maintainability and availability | Add 5-year maintenance plan, release cadence, archival snapshots, funding/contact information | Not started |

## Build Checklist

### V0: Public Skeleton

- [x] Local FastAPI portal.
- [x] Anonymous public API.
- [x] Curated accession registry.
- [x] NAR readiness endpoint.
- [x] Initial help section.
- [ ] Production deployment.
- [ ] Public domain name.
- [ ] Contact email and citation page.

### V1: Curation Depth

- [ ] Verify file-level public access for each accession.
- [ ] Store original sample labels and standardized transplant labels.
- [ ] Add study-level QC pages.
- [ ] Add data download endpoints for normalized matrices and derived tables. Transcriptome summaries/contrasts and DFI metabolomics/microbiome feature tables are already downloadable.
- [ ] Add provenance for every derived result. Baseline provenance exists for processed GEO studies and the DFI feature ingest; release-level provenance remains pending.
- [ ] Add release versioning.

### V2: Value-Added Biology

- [ ] Differential expression for priority contrasts. Started for GSE145780, GSE13440, and GSE11881.
- [ ] Signature scoring across studies. Started for processed transcriptome cohorts; signature validation caveats remain visible.
- [x] Gene pages with cross-study evidence.
- [ ] Cell-type pages for single-cell studies.
- [ ] Pathway and marker-gene summaries.
- [ ] Case studies demonstrating rejection, gut-liver infection risk, donor liver quality, and blood monitoring use cases. Donor liver quality now has GSE243887 gene-level evidence; written tutorial still pending.

### V3: Submission Package

- [ ] Public URL stable for review.
- [ ] Manuscript outline.
- [ ] Plain-text pre-submission inquiry.
- [ ] Comparison against GEO, NGDC, PRIDE, MetaboLights, MGnify, and transplant-specific resources.
- [ ] Data availability and legal/ethical statement.
- [ ] Help/tutorial pages complete.
- [ ] Maintenance plan and update policy.

## Practical Acceptance Strategy

The strongest NAR argument should be:

LiverTx-OmicsDB is not another repository. It transforms scattered public liver transplantation omics studies into a curated, queryable evidence graph centered on transplant phase, graft state, sample origin, omics modality, genes, metabolites, taxa, pathways, and cell types.

The submission should avoid claiming new primary biological discoveries as the main contribution. The main contribution should be the online resource, its curation model, and its retrieval/analysis functions.
