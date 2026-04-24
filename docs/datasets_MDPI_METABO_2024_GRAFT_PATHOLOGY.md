# MDPI Metabolites 2024 liver graft pathology serum metabolomics candidate

## Source

- Article: "Harnessing Metabolites as Serum Biomarkers for Liver Graft Pathology Prediction Using Machine Learning"
- Journal: `Metabolites` 2024, 14(5), 254
- DOI: [10.3390/metabo14050254](https://doi.org/10.3390/metabo14050254)
- Public article PDF confirmed at:
  - `https://mdpi-res.com/d_attachment/metabolites/metabolites-14-00254/article_deploy/metabolites-14-00254.pdf`

## Why it matters

This is a direct post-liver-transplant serum metabolomics cohort rather than a reference atlas or an adjacent liver disease dataset. The article describes a biopsy-matched graft pathology cohort including:

- `TCMR` (`n = 18`)
- `biliary complications` (`n = 27`)
- `post-transplant MASH` (`n = 10`)

The study therefore offers a realistic non-invasive graft-injury metabolomics layer that can support:

- rejection versus non-rejection differential interpretation
- biliary injury versus immune injury separation
- post-transplant metabolic injury context

## Public data signal

The public article text explicitly states:

- metabolite concentrations are reported in `uM` absolute units
- the data are available in supplementary material
- `Table S4` contains metabolite concentrations for each sample

This is enough to prioritize the source as `ready_to_ingest` even though the supplementary attachment still needs direct retrieval and checksum capture.

## Planned ingest shape

If Table S4 is recovered as expected, ingest should create a new processed source with:

- cohort summary
- source file inventory
- metabolomics feature table
- pairwise contrasts:
  - `TCMR vs biliary`
  - `TCMR vs post_transplant_MASH`
  - `biliary vs post_transplant_MASH`
- provenance noting:
  - targeted serum metabolomics
  - absolute concentration units
  - single-center pilot cohort
  - no independent external validation cohort

## Caveats

- This is a `single-center` cohort.
- It is a `pilot` study with modest sample size.
- Clinical variables used in the paper's ML model are not fully public; only metabolite concentrations are described as public supplementary data.
- The cohort is about `graft pathology discrimination`, not donor quality or early perioperative graft viability.
