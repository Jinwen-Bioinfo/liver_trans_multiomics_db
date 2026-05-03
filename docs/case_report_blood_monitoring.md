# Case Report: Blood-Based Monitoring and Tolerance Context

## Question

Can blood, PBMC, plasma, serum, metabolite, and proteomic evidence support non-invasive monitoring and tolerance-related stratification after liver transplantation?

## Why This Matters

This is one of the most attractive use cases for a translational database because it directly connects to the hope of reducing biopsy dependence. It is also a very good stress test for whether the resource can manage complexity honestly.

Blood-based evidence is not one thing. In the current project it spans:

- longitudinal blood transcriptomics
- PBMC tolerance biology
- serum metabolomics linked to graft pathology
- multiple serum/plasma proteomics layers with different evidence strengths

The scientific value is high, but so is the risk of overclaiming. That is why this demonstrator needs strong evidence grading and explicit caveats.

## Current Evidence Stack

### Evidence Grade A

- `GSE200340`
  - pediatric blood/PBMC RNA-seq
  - current contrast:
    - `early_post_transplant_blood_vs_pre_transplant_blood`

- `GSE11881`
  - PBMC tolerance transcriptomics
  - current contrast:
    - `operational_tolerance_vs_non_tolerant`

- `MDPI_METABO_2024_LT_GRAFT_PATHOLOGY`
  - serum metabolomics
  - current contrast:
    - `TCMR_vs_biliary_complication`

### Evidence Grade B

- `PXD062924`
  - serum proteomics
  - current contrast:
    - `normal_kidney_function_post_lt_vs_impaired_kidney_function_post_lt`

### Evidence Grade C

- `FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS`
  - tolerance proteomics marker layer
- `S-EPMC6493459`
  - peri-transplant serum proteomics context
- `AGING_2020_LT_SERUM_PROTEOMICS`
  - serum biomarker summary layer

## Cross-Omics Interpretation

The first-pass mapping scaffold organizes the blood use case into four groups.

### 1. Interferon and inflammatory blood-monitoring program

Core entities:

- `CXCL10`
- `ISG15`
- `IFI27`

Interpretation:

This is the main longitudinal blood-monitoring RNA program and the clearest example of a non-invasive inflammatory tracking layer in the current build.

### 2. Tolerance and immune homeostasis program

Core entities:

- transcript side:
  - `IL7R`
  - `FOXP3`
  - `IL10`
  - `IFNG`
- proteomic side:
  - `HDAC1`
  - `FCGR3B`
  - `PADI4`
  - `MAPK1`

Interpretation:

This group is the main bridge between PBMC tolerance transcriptomics and baseline plasma withdrawal-risk proteomics.

### 3. Serum protein stress, transport, and complication context

Core entities:

- `ACLY`
- `FGA`
- `APOA1`
- `B2M`
- `AMBP`
- `TF`
- `S100P`
- `AOX1`

Interpretation:

This group explains why serum proteomics in the current build should be treated as broad monitoring context rather than a single clean rejection signature. It includes complication, transport, and systemic stress signals.

### 4. Energy, amino-acid, and lipid metabolism context

Core metabolites:

- `Glucose`
- `Lactic_acid`
- `Citric_acid`
- `Taurine`
- `Trimethylamine_N-oxide`

Interpretation:

This is the main metabolomics layer for the blood demonstrator and gives the use case genuine modality breadth beyond transcriptome-plus-proteome.

## What This Demonstrator Already Supports

The current build can already support these claims:

1. blood/PBMC molecular states can be organized for longitudinal monitoring
2. tolerance-related PBMC evidence can be separated from generic inflammatory monitoring
3. serum metabolomics can add pathology-aware blood context
4. serum proteomics can be added cautiously as supportive monitoring context

This is enough for a credible V1 multi-omics monitoring story, provided the caveats stay visible.

## What It Does Not Yet Support

This use case should **not** yet be presented as:

- a validated non-invasive rejection classifier
- a blood substitute for biopsy
- a unified multi-omic decision rule with known clinical performance

The main limits are:

- blood monitoring and tolerance are still semantically close and need a cleaner product separation
- proteomic support is mixed in strength and often context-specific
- some blood cohorts lack direct biopsy-defined rejection outcome labels
- cross-study calibration is not yet strong enough for clinical performance claims

## Recommended Next Step

The next work for this use case should be:

1. split the product view into:
   - monitoring
   - tolerance / withdrawal-risk context
2. expose evidence grades directly on the use-case page
3. add a compact marker panel view for:
   - interferon/inflammatory markers
   - tolerance markers
   - serum complication proteins
   - pathology-linked metabolites
4. include a user-visible section called:
   - `What this does not yet support`

## Bottom Line

This is already one of the richest multi-omics use cases in the resource, but its value comes from disciplined framing. The database can credibly present it as **non-invasive monitoring context**, not as a finished blood-based diagnostic product.
