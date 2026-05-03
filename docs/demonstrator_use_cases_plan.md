# Demonstrator Use Cases Plan

This document narrows the first execution wave to three demonstrator questions. These are the questions that should become the first fully convincing end-to-end workflows in LiverTx-OmicsDB.

The goal is not to make these the only supported questions. The goal is to use them as the first proof that the resource can deliver:

- question-first navigation
- cross-omics evidence aggregation
- explicit evidence grading
- visible caveats
- downloadable artifacts with provenance

## Why These Three

The first demonstrator set should maximize:

1. clinical relevance
2. cross-omics breadth
3. current data readiness
4. NAR database-story strength

The chosen three are:

1. **Early injury versus rejection**
2. **Donor liver quality and graft viability**
3. **Blood-based non-invasive monitoring and tolerance context**

## Demonstrator 1: Early Injury Versus Rejection

### Scientific question

Can public molecular evidence distinguish early graft injury or ischemia/reperfusion-linked dysfunction from true immune rejection?

### Why this is a good demonstrator

- it is clinically important
- it forces cross-omics comparison
- it exposes the difference between tissue, serum, and reference-context evidence
- it is a good test of whether the database can avoid overclaiming

### Current evidence stack

#### Level A

- `GSE145780`
  - bulk graft-biopsy transcriptome
  - explicit states include `no_rejection`, `TCMR`, `early_injury`, and `fibrosis`

#### Level B

- `IJMS_2022_LT_GRAFT_AKI_PROTEOMICS`
  - direct graft-tissue proteomics
  - `moderate_severe_early_aki` versus `no_early_aki`

#### Level C

- `AGING_2020_LT_SERUM_PROTEOMICS`
  - published group-summary serum proteomics
  - acute rejection, stable function, and ITBL contexts
- `HO1_ACR_LIVER_TX_PROTEOMICS`
  - small iTRAQ rejection discovery set
  - useful marker-level serum evidence

#### Level R

- `PXD012615`
  - liver-cell proteome reference

### What the demonstrator must show

1. transcriptomic contrast between `early_injury` and `TCMR`
2. injury-associated versus rejection-associated marker sets
3. tissue proteomics context from graft injury
4. clear separation between:
   - biopsy tissue evidence
   - serum biomarker evidence
   - reference-cell context

### Current gaps

- pathway-level cross-omics summary is still missing
- evidence grading is not yet surfaced in the product
- serum injury-versus-rejection evidence is still mostly Level C
- metabolome support is weak or absent for this question

### Next-week deliverables

1. create an `injury_vs_rejection` evidence table with per-layer evidence grades
2. generate a unified marker/pathway panel:
   - rejection-associated
   - injury-associated
   - ambiguous/shared inflammatory
3. create a markdown case study with caveats
4. wire the use-case page to display evidence grades and origin labels

## Demonstrator 2: Donor Liver Quality and Graft Viability

### Scientific question

Can donor-organ molecular features contextualize accepted versus rejected livers and machine-perfusion viability biology?

### Why this is a good demonstrator

- it is a clear transplant-specific differentiator
- it brings donor biology into the database, which generic repositories do not organize well
- it naturally supports future machine-perfusion expansion

### Current evidence stack

#### Level A

- `GSE243887`
  - donor liver RNA-seq
  - `accepted_donor_liver` versus `rejected_donor_liver`

#### Level A/B boundary

- `PXD046355`
  - donor-liver bile proteomics
  - high-versus-low biliary viability contrasts
  - partial transplanted/non-transplanted context

#### Level M, likely future upgrade

- `PXD067270`
  - strong direct graft proteomics candidate
  - explicit `M1-M16` and `B1/B2/B3` file mapping already recovered
  - outcome annotation still unresolved

### What the demonstrator must show

1. accepted vs rejected donor-organ transcriptome evidence
2. hepatocyte-function / stress / fibrosis-style marker interpretation
3. bile proteomics context for viability and biliary biology
4. visible distinction between:
   - donor-organ selection labels
   - machine-perfusion viability labels
   - recipient post-transplant outcomes

### Current gaps

- transcriptome modules for donor quality are not yet formalized
- donor-quality pathways are not yet summarized across omics
- `PXD067270` is not yet connected strongly enough to public outcome labels
- the product does not yet clearly explain donor-quality evidence versus recipient-outcome evidence

### Next-week deliverables

1. define donor-quality module set:
   - hepatocyte function
   - oxidative stress
   - ECM/fibrosis
   - inflammatory injury
2. produce a donor-quality evidence matrix across RNA and proteomics
3. write a donor-quality markdown report with explicit caveat language
4. add evidence-grade language to the use-case page

## Demonstrator 3: Blood-Based Monitoring and Tolerance Context

### Scientific question

Can blood, PBMC, plasma, serum, metabolite, and proteomic evidence support non-invasive monitoring and tolerance-related stratification?

### Why this is a good demonstrator

- it is highly valuable clinically
- it showcases true multi-omics breadth
- it supports both monitoring and tolerance narratives
- it is a strong NAR story because it links multiple public modalities into one use-case family

### Current evidence stack

#### Level A

- `GSE200340`
  - pediatric blood/PBMC RNA-seq timepoint monitoring
- `GSE11881`
  - PBMC tolerance transcriptomics
- `MDPI_METABO_2024_LT_GRAFT_PATHOLOGY`
  - serum metabolomics with explicit pathology groups

#### Level B/C

- `PXD062924`
  - renal dysfunction monitoring proteomics
  - useful for blood complication context, not rejection diagnosis
- `FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS`
  - narrow baseline tolerance marker layer
- `S-EPMC6493459`
  - peri-transplant serum proteomics context
- `AGING_2020_LT_SERUM_PROTEOMICS`
  - group-summary serum biomarker evidence

### What the demonstrator must show

1. separation between:
   - monitoring
   - tolerance/withdrawal risk
   - complication context
2. blood transcriptome, serum metabolome, and serum proteome evidence in one question family
3. visible evidence-grade differences between stronger and weaker layers
4. clear statement that current blood evidence is not yet a biopsy-replacement classifier

### Current gaps

- monitoring and tolerance are still semantically close but not cleanly separated in the product
- blood-based evidence is not yet summarized across modalities in one view
- rejection outcome labels are incomplete for some blood datasets
- some proteomics support is still only Level C

### Next-week deliverables

1. split this demonstrator into two linked subviews:
   - monitoring
   - tolerance/withdrawal risk
2. build a blood-evidence matrix by modality and evidence grade
3. define a small cross-omics marker panel:
   - inflammatory/IFN markers
   - tolerance-associated markers
   - complication-associated proteins/metabolites
4. write a markdown case study with a section called `What this does not yet support`

## Shared Deliverables for All Three Demonstrators

These should be produced in parallel for the three chosen use cases.

### 1. Evidence-grade table

Each use case should get a table with:

- dataset
- sample origin
- modality
- contrast
- evidence grade
- artifact path
- main caveat

Initial artifact:

- [demonstrator_evidence_tables.json](/Users/jinwen/Program/liver_trans_multiomics_db/data/registry/demonstrator_evidence_tables.json)
- [demonstrator_evidence_tables.md](/Users/jinwen/Program/liver_trans_multiomics_db/docs/demonstrator_evidence_tables.md)

### 2. Cross-omics mapping table

Each use case should get a compact mapping file that links:

- genes
- proteins
- metabolites
- taxa when relevant
- pathways

### 3. Question report

Each use case should get a markdown report containing:

- question
- why it matters
- data sources
- key signals
- evidence grades
- caveats
- next validation needs

### 4. Product integration targets

Each use case page should eventually show:

- primary datasets
- supporting datasets
- evidence-grade badges
- downloadable artifacts
- provenance links
- caveat box

## What Should Wait

To stay disciplined, the following should not lead the next sprint:

- adding more unresolved proteomics candidates
- broad UI polishing unrelated to demonstrator workflows
- immunogenetics implementation before the first three demonstrators are coherent
- adding new omics layers that do not materially strengthen one of these three questions

## Success Criteria for the First Demonstrator Sprint

This sprint succeeds if, for each of the three demonstrators, we can point to:

1. a stable question definition
2. a graded evidence table
3. a cross-omics mapping artifact
4. a case-study markdown report
5. a product plan for how the user will access it

If we do that, the project will stop drifting and start behaving like a database resource rather than a dataset collection exercise.
