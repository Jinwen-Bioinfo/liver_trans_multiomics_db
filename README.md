# LiverTx-OmicsDB

LiverTx-OmicsDB is being built as a public, transplant-centered multi-omics evidence resource for liver transplantation.

The project is intentionally organized around the expectations of the **Nucleic Acids Research Database Issue**:

- freely accessible web resource with no login for public data
- clear help material for first-time users
- curated public accessions with provenance, licensing, and processing status
- searchable biological entities across studies, samples, omics modalities, and clinical states
- reproducible ingestion and analysis workflows
- explicit differentiation from generic repositories such as GEO, SRA, PRIDE, MetaboLights, and MGnify

## Quick Start

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Then open:

- Portal: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs
- NAR readiness: http://127.0.0.1:8000/api/nar/readiness
- Omics layers: http://127.0.0.1:8000/api/omics-layers
- Public dataset discovery artifact: data/discovery/public_liver_tx_dataset_discovery.json
- Example gene evidence: http://127.0.0.1:8000/api/features/CXCL9/expression
- Example non-marker gene evidence: http://127.0.0.1:8000/api/features/ALB/expression
- Example signature score: http://127.0.0.1:8000/api/signatures/TCMR_IFNG_CYTOTOXIC/scores

## Docker Deployment

The Docker setup keeps Python, R, the API, and ingest scripts in one reproducible environment.
It uses China-friendly defaults for image, Debian apt, and Python package downloads:

```bash
docker compose build
docker compose up -d api
docker compose run --rm worker
docker compose run --rm worker Rscript scripts/ingest_dfi_microbiome.R
```

The API is exposed at http://127.0.0.1:8010/ by default. `data/` is mounted from the host, so raw and processed public datasets persist outside the image.

## Current Scope

V1 focuses on public datasets relevant to:

- liver graft rejection
- donor liver molecular quality
- ischemia/reperfusion and early graft injury
- liver graft fibrosis and chronic injury
- blood-based transplant monitoring
- single-cell immune and stromal mechanisms
- proteome, metabolome, microbiome, and immunogenetics layers as first-class registry objects

See [docs/liver_transplant_multiomics_design.md](/Users/jinwen/Program/liver_trans_multiomics_db/docs/liver_transplant_multiomics_design.md) for the full design.

## Repository Layout

```text
app/
  main.py              FastAPI application and public API
  data_loader.py       Registry loading and search helpers
  static/index.html    Minimal public web portal
data/registry/
  studies.json         Curated public accession registry
  omics_layers.json    Evidence-layer registry across transcriptome, proteome, metabolome, microbiome, and immunogenetics
  multiomics_sources.json  Verified external non-transcriptomic source registry
  gene_probe_map.json  Auditable probe-to-gene mappings for supported arrays
  signatures.json      Curated demonstration signatures
docs/
  public_dataset_discovery.md
  nar_submission_readiness.md
  differentiation_statement.md
tests/
  test_api_contract.py
```

## NAR-Oriented Build Principle

Every dataset must preserve:

- original accession and repository URL
- publication or preprint where available
- public access status and any human-data access caveat
- omics modality, sample origin, and transplant phase
- original labels and standardized labels
- processing status and QC status
- what users can retrieve from the portal

## Current Evidence Layer

`GSE145780` currently supports full-platform bulk transcriptome evidence:

- 235 graft-liver biopsy samples
- 48,873 observed PrimeView probe sets
- 19,460 gene-level summaries
- Welch t-test contrasts with Benjamini-Hochberg FDR
- signed within-study z-score signature scoring
- registered external fecal metabolome/microbiome source for liver transplant postoperative infection
- registered human liver cell proteome reference source

Example:

```bash
curl http://127.0.0.1:8000/api/features/CXCL9/expression
curl http://127.0.0.1:8000/api/features/ALB/expression
curl http://127.0.0.1:8000/api/omics-layers
curl http://127.0.0.1:8000/api/multiomics-sources
curl http://127.0.0.1:8000/api/signatures/TCMR_IFNG_CYTOTOXIC/scores
```

Important caveat: GSE145780 molecular labels come from the source study, so this layer is evidence for exploration and database functionality, not an independently validated diagnostic classifier.
