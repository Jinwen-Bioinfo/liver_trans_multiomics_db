# Scientific and Clinical Use Cases

LiverTx-OmicsDB should be developed around transplant questions rather than around repository accessions. The database is most defensible for a NAR Database Issue submission if every feature demonstrates a value-added answer to a scientific or clinical question.

## Core Position

The resource asks:

**Can public multi-omics data be harmonized to define molecular states of liver allograft health, rejection, injury, fibrosis, donor quality, and monitoring?**

## Priority Use Cases

| Use case | Clinical/scientific question | V1 evidence status |
| --- | --- | --- |
| Molecular TCMR/ACR evidence | Can molecular signals separate rejection-like states from non-rejection or confounded graft injury states? | Full-platform bulk expression contrast in GSE145780; independent ACR-vs-recurrent-HCV expression contrast started in GSE13440 |
| Injury vs rejection | Can early injury be distinguished from immune rejection? | Full-platform contrast available; PXD012615 adds liver cell protein reference context; injury pathway/metabolome layers pending |
| Fibrosis/chronic injury | Which ECM signals track graft fibrosis? | ECM marker-panel score and full-gene contrast in GSE145780; PXD012615 provides stellate-cell protein context for COL1A1 |
| Donor liver quality | Can donor transcriptomics contextualize accepted vs rejected organs? | GSE243887 donor liver RNA-seq processed with accepted-vs-rejected log2CPM gene contrasts |
| Blood monitoring | Can blood signatures support non-invasive graft monitoring? | GSE11881 PBMC tolerance contrast and GSE200340 pediatric blood time-point RNA-seq are processed |
| Single-cell mechanism | Which cell types drive rejection markers and immune activation? | GSE189539 single-cell graft-liver matrix processed to marker/module evidence; cell metadata still needed for cell-type proportions |
| Gut-liver microbiome/metabolome | Do microbial taxa and fecal metabolites associate with postoperative infection risk or immune dysregulation? | DFI_MICROBIOME_LT_2024 processed to feature-level metabolite and taxon summaries |
| Immunosuppression pharmacogenomics | How do drug exposure and pharmacogenetic context relate to graft molecular state? | Metadata model ready; data discovery pending |

## NAR Case Study Plan

1. **TCMR/ACR molecular evidence**
   Use GSE145780 to expose full-platform gene summaries and `TCMR_vs_no_rejection` contrasts with BH-FDR. Use GSE13440 as an independent ACR-predominant liver-allograft biopsy dataset, comparing ACR with recurrent hepatitis C without ACR. IFN-gamma/cytotoxic markers are pre-specified evidence examples, not clinical diagnostic validation.

2. **Fibrosis molecular evidence**
   Use GSE145780 to evaluate an ECM marker panel and fibrosis contrasts, with an explicit caveat that the fibrosis group has only eight samples.

3. **Single-cell marker interpretation**
   Use GSE189539 to expose searchable marker evidence across a public 58,243-cell graft-liver matrix for EAD-associated immune niche genes such as S100A12, GZMB, GZMK, and NKG7. This is deliberately presented as marker-level evidence because the GEO matrix does not include reusable cell-to-sample or cell-type metadata; cell-type proportion claims require recovered annotations or a full reanalysis.

4. **Blood immune monitoring**
   Use GSE11881 to expose PBMC expression evidence for operational tolerance versus non-tolerant liver transplant recipients. Use GSE200340 to expose pediatric blood/PBMC RNA-seq evidence across pre-transplant, early post-transplant, and late post-transplant time points. These are intentionally separated from graft biopsy evidence because tissue origin and clinical question differ.

5. **Gut-liver infection-risk evidence**
   Use DFI_MICROBIOME_LT_2024 to expose stool metabolomics and microbiome features linked to postoperative infection status. The current resource provides 156 metabolite features and 769 MetaPhlAn taxon features with unadjusted infection-positive versus infection-negative summaries. These are searchable feature-level database records, not a reproduced clinical prediction model.

6. **Donor liver molecular quality**
   Use GSE243887 to expose donor liver RNA-seq evidence for accepted versus rejected donor organs. These labels describe organ selection decisions, not post-transplant outcome, so the resource should present this as donor-quality context rather than graft-survival prediction.

7. **Protein reference context**
   Use PXD012615 to expose a processed human liver cell proteome reference layer across hepatocyte, liver sinusoidal endothelial, Kupffer, and hepatic stellate compartments. Example protein evidence includes CYP3A4 as hepatocyte-high, COL1A1 as stellate-high, VWF as endothelial-high, and LST1 as Kupffer-high. This is reference biology, not transplant outcome evidence.

8. **Remaining non-transcriptomic expansion**
   Treat additional transplant-specific proteome, metabolome, microbiome, and immunogenetics records as first-class omics layers. Immunogenetics should remain a registered layer until public datasets are ingested and linked to artifacts.

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
- Protein reference evidence can be queried by gene/protein and linked to liver cell compartments.
- Single-cell marker evidence can be queried where public count matrices are available, with visible caveats when cell metadata are missing.
- Each derived result preserves accession provenance and processing rules.
- The resource offers a transplant-centered layer that generic repositories do not provide.
