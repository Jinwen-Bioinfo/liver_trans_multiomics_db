# Demonstrator Cross-Omics Mappings

This document is the human-readable companion to:

- [demonstrator_cross_omics_mappings.json](/Users/jinwen/Program/liver_trans_multiomics_db/data/registry/demonstrator_cross_omics_mappings.json)

It organizes the first three demonstrator use cases into a small number of biologically interpretable mapping groups. These groups are intended to make the resource more useful for question-level reasoning, not to imply final mechanistic proof.

## 1. Early Injury Versus Rejection

### IFN-gamma chemokine and cytotoxic rejection program

- genes: `CXCL9`, `CXCL10`, `IFNG`, `GZMB`
- main source: `GSE145780`
- interpretation:
  a strong rejection-leaning tissue transcriptome anchor

### Heme metabolism and oxidative-stress response

- genes/proteins: `HMOX1`, `BLVRA`, `HDAC1`
- main source: `HO1_ACR_LIVER_TX_PROTEOMICS`
- interpretation:
  a stress-response bridge between serum proteomics and graft inflammatory biology

### Endothelial injury and acute-phase inflammation

- genes/proteins: `SAA2`, `PLA2G2A`, `PECAM1`, `CTSC`
- main source: `IJMS_2022_LT_GRAFT_AKI_PROTEOMICS`
- interpretation:
  the strongest current proteomic counterweight to a purely rejection-centric reading

### Coagulation, lipid transport, and metabolic stress

- genes/proteins: `FGA`, `APOA1`, `ACLY`
- main sources:
  - `AGING_2020_LT_SERUM_PROTEOMICS`
  - `HO1_ACR_LIVER_TX_PROTEOMICS`
- interpretation:
  useful serum context for graft dysfunction, but not specific enough on its own

## 2. Donor Liver Quality and Graft Viability

### Hepatocyte synthetic and xenobiotic-metabolism competence

- genes/proteins: `ALB`, `CYP3A4`, `APOA1`
- main source: `GSE243887`
- interpretation:
  the primary donor-quality transcriptome axis

### Stress-response and extracellular-matrix remodeling

- genes/proteins: `HMOX1`, `COL1A1`
- main source: `GSE243887`
- interpretation:
  stress and fibrogenic context that complements hepatocyte competence markers

### Biliary and epithelial viability surface program

- genes/proteins: `FCGBP`, `ANPEP`, `ACE2`, `DPP4`, `CTSZ`
- main source: `PXD046355`
- interpretation:
  the main donor-organ proteomics viability layer in the current build

## 3. Blood-Based Monitoring and Tolerance Context

### Interferon and inflammatory blood-monitoring program

- genes: `CXCL10`, `ISG15`, `IFI27`
- main source: `GSE200340`
- interpretation:
  the clearest current blood-RNA monitoring axis

### Tolerance and immune homeostasis program

- genes/proteins:
  - transcript side: `IL7R`, `FOXP3`, `IL10`, `IFNG`
  - proteomic side: `HDAC1`, `FCGR3B`, `PADI4`, `MAPK1`
- main sources:
  - `GSE11881`
  - `FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS`
- interpretation:
  the main withdrawal-risk / tolerance bridge across blood modalities

### Serum protein stress, transport, and complication context

- genes/proteins: `ACLY`, `FGA`, `APOA1`, `B2M`, `AMBP`, `TF`, `S100P`, `AOX1`
- main sources:
  - `AGING_2020_LT_SERUM_PROTEOMICS`
  - `PXD062924`
  - `S-EPMC6493459`
- interpretation:
  broad serum monitoring context, deliberately not reduced to a single rejection signature

### Energy, amino-acid, and lipid metabolism context

- metabolites: `Glucose`, `Lactic_acid`, `Citric_acid`, `Taurine`, `Trimethylamine_N-oxide`
- main source: `MDPI_METABO_2024_LT_GRAFT_PATHOLOGY`
- interpretation:
  the first strong serum metabolomics layer for pathology-aware blood monitoring context

## How These Mappings Should Be Used

These groups should feed the next two deliverables:

1. question-level markdown reports
2. front-end use-case panels that show:
   - evidence grade
   - sample origin
   - modality
   - pathway/theme grouping

## What They Should Not Be Used For Yet

- not as final mechanistic proof
- not as clinical diagnostic models
- not as justification for merging all blood, tissue, donor, and serum signals into one undifferentiated score

They are best treated as the first structured cross-omics scaffold for the three demonstrator workflows.
