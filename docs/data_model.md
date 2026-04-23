# LiverTx-OmicsDB Data Model

The canonical machine-readable schema is:

- `data/schema/livertx_omicsdb_schema.json`

The schema is intentionally conservative. It separates source metadata, standardized transplant labels, feature-level measurements, analysis results, artifacts, and provenance so that the database can grow without overclaiming evidence.

## Core Entities

| Entity | Purpose |
| --- | --- |
| `study` | Public accession, author repository, supplementary table source, or controlled-access metadata record. |
| `sample` | Biospecimen or analyzed sample with original labels and standardized transplant-state labels. |
| `assay` | Measurement layer such as bulk transcriptome, single-cell RNA, proteome, metabolome, microbiome, methylation, or pathology metadata. |
| `feature` | Gene, probe, protein, metabolite, taxon, cell type, pathway, or methylation region. |
| `measurement_summary` | Feature-level group summaries used by the feature explorer. |
| `analysis_result` | Statistical contrast, signature score, validation result, or cross-study evidence statement. |
| `artifact` | Local or remote input/output file with checksum and size. |
| `provenance` | Reproducibility record for download, parsing, normalization, analysis, and manual curation. |

## Label Policy

Every dataset keeps both:

- original source labels, such as GEO characteristics, author phenotype fields, or supplementary table labels
- standardized database labels, such as `TCMR`, `no_rejection`, `early_injury`, `fibrosis`, `operational_tolerance`, or `postoperative_infection`

The standardized label must include `standardization_confidence` and, when manually curated, the curation rule and reviewer.

## Artifact Policy

Raw files are cached outside Git under `data/raw/`. Processed summaries can be versioned when small enough for GitHub. Large processed matrices should be moved to release assets, object storage, or Git LFS before the resource grows further.

Every evidence-ready dataset must provide:

- source URL
- downloaded timestamp
- input checksum
- input file size
- processing script
- code commit
- output checksum or artifact inventory
- limitations

## Normalization Policy

Normalization is modality-specific:

| Layer | Policy |
| --- | --- |
| Microarray | Platform annotation, probe-to-gene mapping, probe retention, gene-level collapse, log-scale caveat. |
| RNA-seq | Prefer raw counts with DESeq2/edgeR-style contrasts; otherwise preserve source-normalized scale. |
| Single-cell | Preserve source object metadata; export sample-level pseudobulk and cell-type summaries when permitted. |
| Proteomics | Map protein groups to UniProt/gene symbols; retain missingness and intensity scale. |
| Metabolomics | Preserve source compound names and scale; map to HMDB/ChEBI/PubChem when possible. |
| Microbiome | Preserve taxon rank/name; distinguish relative abundance from counts; map taxonomy where possible. |

## API

The schema is exposed at:

- `/api/data-model`
