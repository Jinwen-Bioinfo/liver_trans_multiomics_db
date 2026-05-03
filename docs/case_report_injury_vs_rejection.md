# Case Report: Early Injury Versus Rejection

## Question

Can public molecular evidence distinguish early graft injury or ischemia/reperfusion-linked dysfunction from true immune rejection?

## Why This Matters

In liver transplantation, abnormal graft function early after transplant can reflect more than one biological process. Immune rejection is one possibility, but ischemia/reperfusion injury, preservation damage, endothelial stress, infection, and metabolic dysfunction can all create overlapping inflammatory signals. If these states are not separated clearly, the database risks encouraging the same misclassification problem clinicians and researchers already face.

This use case is therefore a good first test of whether LiverTx-OmicsDB can do more than collect datasets. It needs to show that the resource can place different omics layers into one interpretable framework without overclaiming.

## Current Evidence Stack

### Evidence Grade A

- `GSE145780`
  - graft-biopsy bulk transcriptome
  - usable transplant states:
    - `no_rejection`
    - `TCMR`
    - `early_injury`
    - `fibrosis`
  - primary contrast already exposed:
    - `TCMR_vs_no_rejection`

### Evidence Grade B

- `IJMS_2022_LT_GRAFT_AKI_PROTEOMICS`
  - direct graft-tissue proteomics
  - current contrast:
    - `moderate_severe_early_aki_vs_no_early_aki`

### Evidence Grade C

- `AGING_2020_LT_SERUM_PROTEOMICS`
  - serum biomarker evidence
  - useful contrast:
    - `stable_post_transplant_vs_acute_rejection`
- `HO1_ACR_LIVER_TX_PROTEOMICS`
  - direct serum ACR marker layer
  - current contrast:
    - `acute_cellular_rejection_vs_non_rejection_post_lt`

### Evidence Grade R

- `PXD012615`
  - liver-cell proteome reference

## Cross-Omics Interpretation

The current mapping scaffold suggests four biologically useful interpretation groups.

### 1. IFN-gamma chemokine and cytotoxic rejection program

Core entities:

- `CXCL9`
- `CXCL10`
- `IFNG`
- `GZMB`

Interpretation:

This is the clearest rejection-leaning tissue transcriptomic anchor in the current build. It represents adaptive immune activation and cytotoxic effector biology, and it is the most defensible place to start when explaining why `TCMR` should not be collapsed into generic graft inflammation.

### 2. Heme metabolism and oxidative-stress response

Core entities:

- `HMOX1`
- `BLVRA`
- `HDAC1`

Interpretation:

This group helps connect serum proteomic stress-response signals to graft dysfunction. It is biologically plausible in both inflammatory and injury-linked contexts, which is precisely why it is useful here: it reminds us that some visible blood signals are not specific to rejection.

### 3. Endothelial injury and acute-phase inflammation

Core entities:

- `SAA2`
- `PLA2G2A`
- `PECAM1`
- `CTSC`

Interpretation:

This is the strongest current proteomic injury-context group. It comes from direct graft tissue rather than serum and provides the main counterbalance to a purely rejection-centric reading of early graft dysfunction.

### 4. Coagulation, lipid transport, and metabolic stress

Core entities:

- `FGA`
- `APOA1`
- `ACLY`

Interpretation:

This group is useful as systemic graft dysfunction context, especially in serum. It is biologically informative, but not specific enough to resolve injury versus rejection on its own.

## What This Demonstrator Already Supports

At the current stage, the database can already support these claims:

1. a biopsy-derived rejection axis exists and is queryable
2. a distinct injury-oriented graft proteomics layer also exists
3. serum biomarker layers provide useful but weaker context
4. reference-cell proteomics can help interpret whether signals are plausibly hepatocyte, endothelial, Kupffer, or stromal linked

That is already enough to say that the resource is moving beyond accession browsing toward question-centered evidence assembly.

## What It Does Not Yet Support

This use case should **not** yet be presented as:

- a validated injury-versus-rejection classifier
- a solved multimodal prediction model
- a serum-only rejection decision tool
- a clinically calibrated differential diagnosis engine

The biggest current limits are:

- too much dependence on a single bulk tissue anchor
- only moderate tissue-level replication outside that anchor
- serum proteomics layers that are still mostly evidence Grade C
- no strong metabolomics layer yet dedicated to this question

## Recommended Next Step

The next work for this use case should be:

1. build an evidence-grade panel directly into the use-case page
2. create pathway-level summaries for:
   - IFN/cytotoxic rejection
   - endothelial injury
   - oxidative stress
   - coagulation/metabolic stress
3. explicitly compare `early_injury` versus `TCMR` at the transcriptome level
4. keep serum layers framed as context until stronger sample-level cohorts are public

## Bottom Line

This use case is already scientifically meaningful, but the resource should currently present it as **structured multimodal context**, not as a resolved diagnostic solution. That restraint is a strength, not a weakness.
