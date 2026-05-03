# Project North Star

This document is the execution anchor for LiverTx-OmicsDB. It exists to keep the project aligned with its actual goal: a transplant-specific, multi-omics evidence resource that can support a credible NAR Database Issue submission.

## Mission

LiverTx-OmicsDB should transform scattered public liver-transplant omics studies into a curated, queryable, clinically meaningful evidence system organized around transplant states rather than repository accessions.

The project is **not** primarily trying to:

- maximize the number of public datasets ingested
- publish a one-off biomarker paper
- run isolated analyses without durable resource value

The project **is** trying to:

- normalize public data around liver-transplant clinical states
- connect bulk RNA, single-cell RNA, proteomics, metabolomics, and microbiome evidence
- expose transparent provenance, caveats, and evidence strength
- support question-first retrieval for transplant biology and clinical research

## Core Scientific Questions

The database should be judged by whether it helps answer a small set of important questions better than generic repositories.

### 1. Rejection versus non-rejection

Can molecular signals distinguish TCMR/ACR-like states from no rejection and from confounded inflammatory contexts?

Current anchor datasets:

- `GSE145780`
- `GSE13440`
- `HO1_ACR_LIVER_TX_PROTEOMICS`
- `AGING_2020_LT_SERUM_PROTEOMICS`

### 2. Early injury versus immune rejection

Can ischemia/reperfusion injury or early graft dysfunction be separated from true immune rejection biology?

Current anchor datasets:

- `GSE145780`
- `IJMS_2022_LT_GRAFT_AKI_PROTEOMICS`
- `PXD012615` as reference context

### 3. Donor liver quality and graft viability

Can donor-organ molecular features contextualize accepted versus rejected organs and machine-perfusion viability?

Current anchor datasets:

- `GSE243887`
- `PXD046355`
- `PXD067270` as next high-priority unresolved proteomics target

### 4. Blood-based non-invasive monitoring

Can blood, plasma, serum, or PBMC features support non-invasive monitoring of graft state, complications, or risk stratification?

Current anchor datasets:

- `GSE11881`
- `GSE200340`
- `MDPI_METABO_2024_LT_GRAFT_PATHOLOGY`
- `PXD062924`
- `FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS`
- `S-EPMC6493459`

### 5. Operational tolerance and withdrawal risk

Can public molecular evidence support the biology of tolerance, non-tolerant states, and immunosuppression withdrawal risk?

Current anchor datasets:

- `GSE11881`
- `FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS`

### 6. Single-cell mechanism and cell-state interpretation

Which cell compartments and immune niches explain bulk rejection or graft injury signals?

Current anchor datasets:

- `GSE189539`
- supporting single-cell candidates: `HRA002091`, `HRA007802`

### 7. Gut-liver axis, infection, and dysregulation

Do microbiome and metabolome features contextualize infection risk and post-transplant inflammatory states?

Current anchor datasets:

- `DFI_MICROBIOME_LT_2024`

### 8. Post-transplant HCC recurrence biology

Can tumor or peri-transplant proteomic features contextualize recurrence risk after liver transplantation?

Current anchor datasets:

- `PXD022881`
- `S-EPMC6493459`
- `PXD061119` as strong but still blocked sample-label candidate

## What Counts as Success

For each core question, the database should eventually provide:

1. a question page
2. primary and supporting datasets
3. explicit evidence level
4. downloadable derived artifacts
5. visible caveats and provenance
6. cross-omics links where available

If a dataset does not strengthen one of the core questions, it is lower priority by default.

## Evidence Model

The project needs a stable evidence hierarchy so that users do not confuse strong sample-level datasets with partial figure-derived marker layers.

### Evidence Level A: reusable sample-level matrix with explicit labels

Examples:

- full expression matrix with per-sample transplant-state labels
- proteomics abundance matrix with explicit sample-to-outcome mapping
- metabolomics table with per-sample concentrations and cohort labels

This is the strongest V1 resource evidence.

### Evidence Level B: reusable feature-level table with explicit group contrasts

Examples:

- supplementary protein/metabolite tables with group-level differential features
- study-level derived summaries with clear statistical contrasts

Useful and publishable, but below sample-level evidence.

### Evidence Level C: marker-layer evidence recovered from article figures or partial tables

Examples:

- OCR-recovered supplementary lists
- article-figure markers where full tables are unresolved

Valuable for search and context, but must be labeled conservatively.

### Evidence Level R: reference context

Examples:

- `PXD012615` liver cell proteome

These layers support interpretation, not transplant outcome claims.

### Evidence Level M: metadata model only

Examples:

- immunogenetics layer today
- unresolved cohorts with known relevance but insufficient public labels

These should guide discovery, not be shown as ready biological evidence.

## Cross-Omics Integration Rules

The project should stop treating multi-omics as a list of parallel layers and instead enforce explicit mapping rules.

### Shared biological entities

- gene symbol
- UniProt accession / protein group
- metabolite identifier
- microbial taxon
- pathway / process
- sample origin
- transplant phase
- clinical state

### Required mapping outputs

For priority use cases, AI-generated integration should produce:

1. `gene <-> protein` links
2. `gene/protein/metabolite <-> pathway` links
3. `taxon <-> metabolite` context when biologically justified
4. contrast-level joins across modalities
5. caveat-aware evidence tables, not naive merged claims

### Integration principles

- do not merge tissues, blood, donor organs, and stool without visible origin labels
- do not treat reference proteomes as direct transplant evidence
- do not flatten sample-level and figure-level evidence into the same confidence class
- do not hide confounding variables such as recurrent hepatitis C, post-transplant MASH, or timepoint effects

## Current Strategic Deviation

The project has already built a strong framework, but execution has started drifting.

### What has gone well

- transplant-specific semantic framing is in place
- multiple omics layers are already represented
- API and local portal exist
- many proteomics leads have been verified much more deeply than a normal early-stage database project

### Where execution has drifted

1. **Cohort expansion has outrun resource consolidation**
   Recent work has focused heavily on finding and validating additional proteomics cohorts rather than improving the usability and scientific coherence of the resource itself.

2. **Cross-omics integration is still shallow**
   We have multiple layers, but not enough robust question-level integration across genes, proteins, metabolites, taxa, and pathways.

3. **Evidence grading is not yet consistently surfaced**
   The internal reasoning has become more disciplined than the public-facing resource. The product still needs clearer evidence labels.

4. **NAR engineering maturity is behind data discovery maturity**
   Public deployment, QC pages, release versioning, tutorials, legal/access statements, and maintenance planning still lag behind dataset expansion.

## Anti-Drift Rules

From this point onward, new work should be filtered through these rules.

### Rule 1: Problem before cohort

No new dataset should become a priority unless it strengthens a core scientific question already listed above.

### Rule 2: Quality before quantity

A well-integrated evidence page for one scientific question is worth more than five loosely connected new cohorts.

### Rule 3: Evidence strength must stay visible

Every new result should be classed as Level A, B, C, R, or M before it is treated as a user-facing capability.

### Rule 4: Engineering work is first-class scientific work

The following are not “cleanup”; they are core deliverables:

- provenance
- QC
- tutorials
- release versioning
- stable deployment
- citation and maintenance information

### Rule 5: Default to demonstrator use cases

At any point, the best next task is usually one that makes one of the core questions more convincingly answerable end-to-end.

## Eight-Week Execution Track

This is the default execution plan unless a higher-priority blocker appears.

### Week 0

- finalize this North Star document
- lock the 5-8 core scientific questions
- define evidence levels and cross-omics mapping standards
- define release/version/QC expectations

### Weeks 1-2

Focus on the first three demonstrator questions:

- early injury versus rejection
- donor liver quality
- blood-based monitoring / tolerance

Deliverables:

- cross-omics mapping tables
- evidence-grade labels
- initial question reports with caveats

Execution detail:

- See [demonstrator_use_cases_plan.md](/Users/jinwen/Program/liver_trans_multiomics_db/docs/demonstrator_use_cases_plan.md) for the concrete scope, evidence stacks, current gaps, and next-week deliverables for these first three demonstrator workflows.
- See [demonstrator_evidence_tables.md](/Users/jinwen/Program/liver_trans_multiomics_db/docs/demonstrator_evidence_tables.md) and [demonstrator_evidence_tables.json](/Users/jinwen/Program/liver_trans_multiomics_db/data/registry/demonstrator_evidence_tables.json) for the first machine-readable and human-readable evidence-grade artifact.
- See [demonstrator_cross_omics_mappings.md](/Users/jinwen/Program/liver_trans_multiomics_db/docs/demonstrator_cross_omics_mappings.md) and [demonstrator_cross_omics_mappings.json](/Users/jinwen/Program/liver_trans_multiomics_db/data/registry/demonstrator_cross_omics_mappings.json) for the first question-oriented cross-omics integration scaffold.
- See the first case-report layer for narrative demonstrators:
  - [case_report_injury_vs_rejection.md](/Users/jinwen/Program/liver_trans_multiomics_db/docs/case_report_injury_vs_rejection.md)
  - [case_report_donor_liver_quality.md](/Users/jinwen/Program/liver_trans_multiomics_db/docs/case_report_donor_liver_quality.md)
  - [case_report_blood_monitoring.md](/Users/jinwen/Program/liver_trans_multiomics_db/docs/case_report_blood_monitoring.md)

### Weeks 3-4

Turn those demonstrators into product workflows:

- question-first navigation
- evidence-level display
- provenance and downloads
- better study/source pages
- tutorial-ready examples

### Weeks 5-8

Expand carefully:

- complete remaining core question pages
- strengthen single-cell interpretation
- advance immunogenetics if public evidence becomes tractable
- tighten release engineering for NAR readiness

## Immediate Priorities

The next concrete priorities should be:

1. create cross-omics mapping and evidence-grade infrastructure
2. turn the top 2-3 scientific questions into full demonstrator pages and reports
3. tighten provenance/QC/versioning
4. continue ingest only when a new cohort materially improves one of those demonstrators

## What to Ask AI For

Good AI tasks in this project should look like:

- “For donor liver quality, integrate bulk RNA, proteomics, and metabolomics evidence and return a graded evidence table.”
- “Build a gene-protein-metabolite mapping for early injury versus rejection and summarize only pathways supported by at least two modalities.”
- “Produce a markdown case study for blood monitoring with data sources, contrasts, evidence levels, caveats, and downloadable artifacts.”
- “Add provenance and QC metadata for all datasets supporting operational tolerance.”

Poor AI tasks in this project are:

- “find more datasets”
- “add more proteomics”
- “continue expanding the database”

unless the task is tied to a specific scientific question and evidence gap.

## Decision Rule for Future Work

When deciding the next task, ask:

1. does this strengthen a core scientific question?
2. does it improve evidence quality or integration?
3. does it improve NAR readiness?

If the answer to all three is no, it is probably drift.
