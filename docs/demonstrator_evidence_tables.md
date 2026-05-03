# Demonstrator Evidence Tables

This document is the human-readable companion to:

- [demonstrator_evidence_tables.json](/Users/jinwen/Program/liver_trans_multiomics_db/data/registry/demonstrator_evidence_tables.json)

It summarizes the first three demonstrator workflows using the evidence model defined in:

- [project_north_star.md](/Users/jinwen/Program/liver_trans_multiomics_db/docs/project_north_star.md)

## Evidence Grades

| Grade | Meaning |
| --- | --- |
| `A` | Reusable sample-level matrix with explicit per-sample labels |
| `B` | Reusable feature-level table with explicit group contrasts |
| `C` | Marker-layer or partial-table evidence |
| `R` | Reference context only |
| `M` | Metadata-model or unresolved candidate, not yet ready as user-facing evidence |

## 1. Early Injury Versus Rejection

| Dataset | Origin | Modality | Contrast | Grade | Main caveat |
| --- | --- | --- | --- | --- | --- |
| `GSE145780` | graft liver biopsy | bulk RNA | `TCMR_vs_no_rejection` | `A` | Same-study marker evidence remains exploratory until independently reproduced |
| `IJMS_2022_LT_GRAFT_AKI_PROTEOMICS` | graft liver biopsy | proteomics | `moderate_severe_early_aki_vs_no_early_aki` | `B` | Injury-context proxy, not a direct injury-vs-rejection classifier |
| `AGING_2020_LT_SERUM_PROTEOMICS` | serum | proteomics | `stable_post_transplant_vs_acute_rejection` | `C` | Group-summary biomarker evidence, not sample-level matrix |
| `HO1_ACR_LIVER_TX_PROTEOMICS` | serum | proteomics | `acute_cellular_rejection_vs_non_rejection_post_lt` | `C` | Small discovery-set marker evidence |
| `PXD012615` | liver reference | proteome reference | none | `R` | Interpretation only, not direct transplant outcome evidence |

**What this already supports**

- a tissue-level transcriptomic anchor
- an injury-focused graft proteomics layer
- a conservative serum biomarker context

**What it still does not support**

- a resolved multimodal classifier for injury versus rejection
- strong metabolome support
- independent replication across multiple tissue cohorts

## 2. Donor Liver Quality and Graft Viability

| Dataset | Origin | Modality | Contrast | Grade | Main caveat |
| --- | --- | --- | --- | --- | --- |
| `GSE243887` | donor liver biopsy | bulk RNA | `accepted_donor_liver_vs_rejected_donor_liver` | `A` | Selection-status labels are not recipient outcomes |
| `PXD046355` | donor liver bile | proteomics | `high_biliary_viability_donor_liver_vs_low_biliary_viability_donor_liver_at_150min` | `A` | Donor-organ viability biology, not a full recipient-outcome layer |
| `PXD067270` | graft liver biopsy | proteomics candidate | `B1/B2/B3` mapping recovered, outcome annotation unresolved | `M` | Sample-to-timepoint mapping is public, but public complication labels and lightweight protein matrix are still missing |

**What this already supports**

- donor-organ selection transcriptomics
- machine-perfusion viability proteomics
- a clear donor-quality story that is distinct from post-transplant recipient monitoring

**What it still does not support**

- a fully integrated donor-quality pathway view across RNA and proteomics
- a complete graft-quality proteomics layer using `PXD067270`
- strong recipient-outcome linkage for donor-quality markers

## 3. Blood-Based Monitoring and Tolerance Context

| Dataset | Origin | Modality | Contrast | Grade | Main caveat |
| --- | --- | --- | --- | --- | --- |
| `GSE200340` | blood / PBMC | bulk RNA | `early_post_transplant_blood_vs_pre_transplant_blood` | `A` | Monitoring/timepoint evidence, not a rejection-outcome classifier |
| `GSE11881` | PBMC | bulk RNA | `operational_tolerance_vs_non_tolerant` | `A` | Tolerance-focused, should not be flattened into generic rejection-monitoring claims |
| `MDPI_METABO_2024_LT_GRAFT_PATHOLOGY` | serum | metabolomics | `TCMR_vs_biliary_complication` | `A` | Needs independent validation before clinical classification claims |
| `PXD062924` | serum | proteomics | `normal_kidney_function_post_lt_vs_impaired_kidney_function_post_lt` | `B` | Renal-dysfunction monitoring, not rejection-specific |
| `FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS` | plasma | proteomics | `operational_tolerance_vs_non_tolerant` | `C` | Marker-panel evidence while full supplement is unresolved |
| `S-EPMC6493459` | serum | proteomics | `healthy_control_vs_pre_transplant_end_stage_liver_disease` | `C` | Partial peri-transplant context, not a complete sample-level matrix |
| `AGING_2020_LT_SERUM_PROTEOMICS` | serum | proteomics | `stable_post_transplant_vs_acute_rejection` | `C` | Group-summary biomarker evidence only |

**What this already supports**

- longitudinal blood/PBMC monitoring evidence
- PBMC tolerance evidence
- direct serum metabolomics for graft pathology context
- multiple conservative serum proteomics context layers

**What it still does not support**

- a biopsy-replacement blood classifier
- unified outcome labels across all blood modalities
- fully resolved tolerance proteomics beyond the current marker layer

## Recommended Next Product Step

The next product-facing step should be to expose these tables on the three demonstrator use-case pages with:

1. evidence-grade badges
2. sample-origin labels
3. links to artifact files
4. a caveat box per layer

That will turn the current internal discipline into a visible user-facing part of the resource.
