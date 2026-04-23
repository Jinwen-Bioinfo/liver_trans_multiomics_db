# GSE145780 Curation Note

## Why This Dataset Is V1 Priority

GSE145780 is the anchor dataset for the first LiverTx-OmicsDB case study because it contains human liver transplant biopsy transcriptomics with clinically interpretable molecular clusters:

| Original cluster | LiverTx-OmicsDB state | Sample count | Interpretation |
| --- | --- | ---: | --- |
| R1normal | no_rejection | 129 | Normal/no rejection molecular state |
| R2TCMR | TCMR | 37 | T cell-mediated rejection-like state |
| R3injury | early_injury | 61 | Early injury state |
| R4late | fibrosis | 8 | Late/fibrosis-associated state |

## Ingestion

The public GEO series matrix is downloaded and parsed by:

```bash
python scripts/ingest_geo_series.py GSE145780
```

Generated outputs:

- `data/processed/GSE145780/samples.json`
- `data/processed/GSE145780/sample_summary.json`
- `data/processed/GSE145780/provenance.json`

The raw GEO matrix is cached under `data/raw/` and ignored by git.

## Current Database Status

- Metadata curation: complete for sample accession, title, source, organism, platform, supplementary CEL file, original cluster, and standardized clinical state.
- Expression evidence: available for the first marker panel: CXCL9, CXCL10, IFNG, GZMB, and COL1A1.
- Signature scoring: available for TCMR IFN-gamma/cytotoxic and fibrosis ECM demonstration signatures.
- QC plots: pending.
- Gene-level evidence endpoint: available at `/api/features/{symbol}/expression`.
- Signature score endpoint: available at `/api/signatures/{signature_id}/scores`.
- Download endpoint for processed derived tables: pending.

## Initial Marker Evidence

The current marker panel is intentionally small and auditable. Probe-to-gene mappings are stored in `data/registry/gene_probe_map.json` and were checked against the GEO GPL15207 platform table.

| Gene | Main V1 use | Expected pattern |
| --- | --- | --- |
| CXCL9 | IFN-gamma rejection chemokine | Higher in TCMR |
| CXCL10 | IFN-gamma rejection chemokine | Higher in TCMR |
| IFNG | T cell activation | Higher in TCMR |
| GZMB | cytotoxic T/NK activity | Higher in TCMR |
| COL1A1 | extracellular matrix/fibrosis | Higher in fibrosis |

Generated output:

- `data/processed/GSE145780/gene_expression_summary.json`
- `data/processed/GSE145780/gene_sample_values.json`
- `data/processed/GSE145780/signature_scores.json`

## Initial Signature Evidence

| Signature | Genes | Expected high state | Observed high state |
| --- | --- | --- | --- |
| TCMR_IFNG_CYTOTOXIC | CXCL9, CXCL10, IFNG, GZMB | TCMR | TCMR |
| FIBROSIS_ECM | COL1A1 | fibrosis | fibrosis |

These are demonstration signatures, not final clinical classifiers. They provide a transparent first proof that the database can link curated transplant states to reproducible molecular evidence.

## NAR Value

This dataset demonstrates the difference between LiverTx-OmicsDB and a primary archive:

GEO provides accession-centered files and metadata. LiverTx-OmicsDB converts the dataset into transplant-centered entities: graft liver biopsy, post-transplant phase, rejection/injury/fibrosis clinical state, assay modality, and future gene/pathway evidence.
