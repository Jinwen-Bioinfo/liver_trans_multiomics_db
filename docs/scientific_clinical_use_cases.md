# Scientific and Clinical Use Cases

LiverTx-OmicsDB should be developed around transplant questions rather than around repository accessions. The database is most defensible for a NAR Database Issue submission if every feature demonstrates a value-added answer to a scientific or clinical question.

## Core Position

The resource asks:

**Can public multi-omics data be harmonized to define molecular states of liver allograft health, rejection, injury, fibrosis, donor quality, and monitoring?**

## Priority Use Cases

| Use case | Clinical/scientific question | V1 evidence status |
| --- | --- | --- |
| Molecular TCMR/ACR evidence | Can molecular signals separate rejection-like states from non-rejection or confounded graft injury states? | Full-platform bulk expression contrast in GSE145780; independent ACR-vs-recurrent-HCV expression contrast started in GSE13440 |
| Injury vs rejection | Can early injury be distinguished from immune rejection? | Full-platform contrast available; injury pathway/proteome/metabolome layers pending |
| Fibrosis/chronic injury | Which ECM signals track graft fibrosis? | ECM marker-panel score and full-gene contrast in GSE145780; fibrosis group is small |
| Donor liver quality | Can donor transcriptomics contextualize accepted vs rejected organs? | Dataset registered |
| Blood monitoring | Can blood signatures support non-invasive graft monitoring? | GSE11881 PBMC operational-tolerance expression contrast is processed |
| Single-cell mechanism | Which cell types drive rejection markers and immune activation? | Datasets registered |
| Gut-liver microbiome/metabolome | Do microbial taxa and fecal metabolites associate with postoperative infection risk or immune dysregulation? | DFI_MICROBIOME_LT_2024 processed to feature-level metabolite and taxon summaries |
| Immunosuppression pharmacogenomics | How do drug exposure and pharmacogenetic context relate to graft molecular state? | Metadata model ready; data discovery pending |

## NAR Case Study Plan

1. **TCMR/ACR molecular evidence**
   Use GSE145780 to expose full-platform gene summaries and `TCMR_vs_no_rejection` contrasts with BH-FDR. Use GSE13440 as an independent ACR-predominant liver-allograft biopsy dataset, comparing ACR with recurrent hepatitis C without ACR. IFN-gamma/cytotoxic markers are pre-specified evidence examples, not clinical diagnostic validation.

2. **Fibrosis molecular evidence**
   Use GSE145780 to evaluate an ECM marker panel and fibrosis contrasts, with an explicit caveat that the fibrosis group has only eight samples.

3. **Future single-cell interpretation**
   Use registered single-cell datasets to map bulk rejection markers to cell types such as CD8_TRM, myeloid cells, endothelial cells, and B cells.

4. **Blood immune monitoring**
   Use GSE11881 to expose PBMC expression evidence for operational tolerance versus non-tolerant liver transplant recipients. This is intentionally separated from graft biopsy evidence because tissue origin and clinical question differ.

5. **Gut-liver infection-risk evidence**
   Use DFI_MICROBIOME_LT_2024 to expose stool metabolomics and microbiome features linked to postoperative infection status. The current resource provides 156 metabolite features and 769 MetaPhlAn taxon features with unadjusted infection-positive versus infection-negative summaries. These are searchable feature-level database records, not a reproduced clinical prediction model.

6. **Remaining non-transcriptomic expansion**
   Treat proteome, additional metabolome, microbiome, and immunogenetics records as first-class omics layers. Proteomics and immunogenetics should remain reference/registered layers until public datasets are actually ingested and linked to artifacts.

## What This Database Should Not Claim Yet

- It should not claim clinical diagnostic performance before independent validation.
- It should not claim causality from public observational datasets alone.
- It should not treat small demonstration signatures as final clinical classifiers.
- It should not combine human, mouse, liver, blood, and donor data without visible caveats.
- It should not call every rejection-associated signal replicated just because it has the same direction in one small independent dataset; sample size, missingness, and confounding by recurrent hepatitis C must remain visible.

## What It Can Credibly Claim in V1

- Public data can be curated into transplant-specific states.
- Molecular evidence can be queried by gene, signature, dataset, clinical state, and omics layer.
- Non-transcriptomic liver transplant features can be queried by metabolite or taxon when public reusable tables exist.
- Each derived result preserves accession provenance and processing rules.
- The resource offers a transplant-centered layer that generic repositories do not provide.
