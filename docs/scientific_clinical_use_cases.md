# Scientific and Clinical Use Cases

LiverTx-OmicsDB should be developed around transplant questions rather than around repository accessions. The database is most defensible for a NAR Database Issue submission if every feature demonstrates a value-added answer to a scientific or clinical question.

## Core Position

The resource asks:

**Can public multi-omics data be harmonized to define molecular states of liver allograft health, rejection, injury, fibrosis, donor quality, and monitoring?**

## Priority Use Cases

| Use case | Clinical/scientific question | V1 evidence status |
| --- | --- | --- |
| Molecular TCMR diagnosis | Can molecular signals separate TCMR from no rejection? | Full-platform bulk expression contrast in GSE145780; independent validation still required |
| Injury vs rejection | Can early injury be distinguished from immune rejection? | Full-platform contrast available; injury pathway/proteome/metabolome layers pending |
| Fibrosis/chronic injury | Which ECM signals track graft fibrosis? | ECM marker-panel score and full-gene contrast in GSE145780; fibrosis group is small |
| Donor liver quality | Can donor transcriptomics contextualize accepted vs rejected organs? | Dataset registered |
| Blood monitoring | Can blood signatures support non-invasive graft monitoring? | Dataset registered |
| Single-cell mechanism | Which cell types drive rejection markers and immune activation? | Datasets registered |
| Gut-liver microbiome | Do microbial taxa/functions associate with infection, rejection-like inflammation, or immunosuppression? | Omics layer registered; public dataset discovery pending |
| Immunosuppression pharmacogenomics | How do drug exposure and pharmacogenetic context relate to graft molecular state? | Metadata model ready; data discovery pending |

## NAR Case Study Plan

1. **TCMR molecular evidence**
   Use GSE145780 to expose full-platform gene summaries and `TCMR_vs_no_rejection` contrasts with BH-FDR. IFN-gamma/cytotoxic markers are pre-specified evidence examples, not circular diagnostic validation.

2. **Fibrosis molecular evidence**
   Use GSE145780 to evaluate an ECM marker panel and fibrosis contrasts, with an explicit caveat that the fibrosis group has only eight samples.

3. **Future single-cell interpretation**
   Use registered single-cell datasets to map bulk rejection markers to cell types such as CD8_TRM, myeloid cells, endothelial cells, and B cells.

4. **Non-transcriptomic evidence expansion**
   Treat proteome, metabolome, microbiome, and immunogenetics as first-class omics layers. They should remain discovery/registered layers until public datasets are actually ingested and linked to artifacts.

## What This Database Should Not Claim Yet

- It should not claim clinical diagnostic performance before independent validation.
- It should not claim causality from public observational datasets alone.
- It should not treat small demonstration signatures as final clinical classifiers.
- It should not combine human, mouse, liver, blood, and donor data without visible caveats.
- It should not call itself multi-omics on the strength of transcriptome data alone; non-transcriptomic layers must be visibly marked as pending until processed.

## What It Can Credibly Claim in V1

- Public data can be curated into transplant-specific states.
- Molecular evidence can be queried by gene, signature, dataset, clinical state, and omics layer.
- Each derived result preserves accession provenance and processing rules.
- The resource offers a transplant-centered layer that generic repositories do not provide.
