from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STUDY_REGISTRY = ROOT / "data" / "registry" / "studies.json"
SIGNATURE_REGISTRY = ROOT / "data" / "registry" / "signatures.json"
USE_CASE_REGISTRY = ROOT / "data" / "registry" / "use_cases.json"
OMICS_LAYER_REGISTRY = ROOT / "data" / "registry" / "omics_layers.json"
MULTIOMICS_SOURCE_REGISTRY = ROOT / "data" / "registry" / "multiomics_sources.json"
SOURCE_TYPE_REGISTRY = ROOT / "data" / "registry" / "source_types.json"
DATASET_TRIAGE_REGISTRY = ROOT / "data" / "registry" / "dataset_triage.json"
DATA_MODEL_SCHEMA = ROOT / "data" / "schema" / "livertx_omicsdb_schema.json"
PROCESSED_DIR = ROOT / "data" / "processed"
DOWNLOAD_ARTIFACTS = {
    "samples": "samples.json",
    "sample_summary": "sample_summary.json",
    "provenance": "provenance.json",
    "analysis_provenance": "analysis_provenance.json",
    "gene_expression_summary": "gene_expression_summary.json",
    "gene_sample_values": "gene_sample_values.json",
    "differential_expression": "differential_expression.json",
    "signature_scores": "signature_scores.json",
    "source_file_inventory": "source_file_inventory.json",
    "cohort_summary": "cohort_summary.json",
    "metabolomics_summary": "metabolomics_summary.json",
    "microbiome_summary": "microbiome_summary.json",
}


@lru_cache(maxsize=1)
def load_studies() -> list[dict[str, Any]]:
    with STUDY_REGISTRY.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["studies"]


@lru_cache(maxsize=1)
def load_use_cases() -> list[dict[str, Any]]:
    with USE_CASE_REGISTRY.open("r", encoding="utf-8") as handle:
        return json.load(handle)["use_cases"]


@lru_cache(maxsize=1)
def load_omics_layers() -> list[dict[str, Any]]:
    with OMICS_LAYER_REGISTRY.open("r", encoding="utf-8") as handle:
        return json.load(handle)["omics_layers"]


@lru_cache(maxsize=1)
def load_multiomics_sources() -> list[dict[str, Any]]:
    with MULTIOMICS_SOURCE_REGISTRY.open("r", encoding="utf-8") as handle:
        return json.load(handle)["sources"]


@lru_cache(maxsize=1)
def load_source_type_payload() -> dict[str, Any]:
    with SOURCE_TYPE_REGISTRY.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def list_source_types() -> dict[str, Any]:
    return load_source_type_payload()


@lru_cache(maxsize=1)
def load_dataset_triage_payload() -> dict[str, Any]:
    with DATASET_TRIAGE_REGISTRY.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def list_dataset_triage(
    *,
    status: str | None = None,
    priority: str | None = None,
    modality: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    payload = load_dataset_triage_payload()
    candidates = payload.get("candidates", [])
    if status:
        candidates = [item for item in candidates if item.get("triage_status") == status]
    if priority:
        candidates = [item for item in candidates if item.get("priority") == priority]
    if modality:
        candidates = [item for item in candidates if modality in item.get("omics_modalities", [])]
    total = len(candidates)
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    return {
        "generated_at_utc": payload.get("generated_at_utc"),
        "summary": payload.get("summary", {}),
        "count": total,
        "limit": limit,
        "offset": offset,
        "candidates": candidates[offset : offset + limit],
    }


def get_dataset_triage(accession: str) -> dict[str, Any] | None:
    accession = accession.upper()
    for item in load_dataset_triage_payload().get("candidates", []):
        if item.get("accession", "").upper() == accession:
            return item
    return None


@lru_cache(maxsize=1)
def load_data_model_schema() -> dict[str, Any]:
    with DATA_MODEL_SCHEMA.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def list_multiomics_sources(layer: str | None = None) -> list[dict[str, Any]]:
    sources = load_multiomics_sources()
    if layer is None:
        return sources
    layer_to_modality = {
        "proteome": "proteomics",
        "metabolome": "metabolomics",
        "microbiome": "microbiome",
    }
    modality = layer_to_modality.get(layer, layer)
    return [source for source in sources if modality in source.get("omics_modalities", [])]


def get_multiomics_source(source_id: str) -> dict[str, Any] | None:
    source_id = source_id.upper()
    for source in load_multiomics_sources():
        if source["source_id"].upper() == source_id:
            return source
    return None


def list_omics_layers() -> list[dict[str, Any]]:
    studies = {study["accession"]: with_processed_summary(study) for study in load_studies()}
    sources = {source["source_id"]: source for source in load_multiomics_sources()}
    layers = []
    for layer in load_omics_layers():
        layers.append(
            {
                **layer,
                "registered_study_records": [
                    studies[accession]
                    for accession in layer.get("registered_accessions", [])
                    if accession in studies
                ],
                "registered_source_records": [
                    sources[accession]
                    for accession in layer.get("registered_accessions", [])
                    if accession in sources
                ],
            }
        )
    return layers


def get_omics_layer(layer_id: str) -> dict[str, Any] | None:
    layer_id = layer_id.lower()
    for layer in list_omics_layers():
        if layer["layer_id"].lower() == layer_id:
            return layer
    return None


def list_studies(
    *,
    query: str | None = None,
    modality: str | None = None,
    clinical_state: str | None = None,
    sample_origin: str | None = None,
) -> list[dict[str, Any]]:
    studies = load_studies()

    def matches(study: dict[str, Any]) -> bool:
        haystack = " ".join(
            str(value)
            for value in [
                study.get("accession"),
                study.get("title"),
                study.get("repository"),
                study.get("summary"),
                " ".join(study.get("keywords", [])),
                " ".join(study.get("featured_genes", [])),
                " ".join(study.get("featured_cell_types", [])),
                " ".join(study.get("featured_pathways", [])),
            ]
        ).lower()
        if query and query.lower() not in haystack:
            return False
        if modality and modality not in study.get("omics_modalities", []):
            return False
        if clinical_state and clinical_state not in study.get("clinical_states", []):
            return False
        if sample_origin and sample_origin not in study.get("sample_origins", []):
            return False
        return True

    return [with_processed_summary(study) for study in studies if matches(study)]


def get_study(accession: str) -> dict[str, Any] | None:
    accession_normalized = accession.lower()
    for study in load_studies():
        if study["accession"].lower() == accession_normalized:
            return with_processed_summary(study)
    return None


def list_use_cases() -> list[dict[str, Any]]:
    studies = {study["accession"]: with_processed_summary(study) for study in load_studies()}
    signatures = {signature["signature_id"]: signature for signature in load_signatures()}
    enriched = []
    for use_case in load_use_cases():
        enriched.append(
            {
                **use_case,
                "primary_dataset_records": [
                    studies[accession]
                    for accession in use_case.get("primary_datasets", [])
                    if accession in studies
                ],
                "signature_records": [
                    signatures[signature_id]
                    for signature_id in use_case.get("signatures", [])
                    if signature_id in signatures
                ],
            }
        )
    return enriched


def get_use_case(use_case_id: str) -> dict[str, Any] | None:
    use_case_id = use_case_id.upper()
    for use_case in list_use_cases():
        if use_case["use_case_id"] == use_case_id:
            return use_case
    return None


def with_processed_summary(study: dict[str, Any]) -> dict[str, Any]:
    summary = load_study_sample_summary(study["accession"])
    cohort_summary = load_study_cohort_summary(study["accession"])
    if summary is None and cohort_summary is None:
        return study
    status = "processed_metadata" if study.get("processing_status") == "pending" else study.get("processing_status")
    payload = {**study, "processing_status": status}
    if summary is not None:
        payload["sample_summary"] = summary
    if cohort_summary is not None:
        payload["cohort_summary"] = cohort_summary
    return payload


@lru_cache(maxsize=16)
def load_study_samples(accession: str) -> list[dict[str, Any]]:
    path = PROCESSED_DIR / accession / "samples.json"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def filter_study_samples(
    accession: str,
    *,
    clinical_state: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    samples = load_study_samples(accession)
    if clinical_state:
        samples = [sample for sample in samples if sample.get("clinical_state") == clinical_state]
    total = len(samples)
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    return {
        "count": total,
        "limit": limit,
        "offset": offset,
        "samples": samples[offset : offset + limit],
    }


@lru_cache(maxsize=16)
def load_study_sample_summary(accession: str) -> dict[str, Any] | None:
    path = PROCESSED_DIR / accession / "sample_summary.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=16)
def load_study_cohort_summary(accession: str) -> dict[str, Any] | None:
    path = PROCESSED_DIR / accession / "cohort_summary.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=16)
def load_study_provenance(accession: str) -> dict[str, Any] | None:
    path = PROCESSED_DIR / accession / "provenance.json"
    analysis_path = PROCESSED_DIR / accession / "analysis_provenance.json"
    if not path.exists() and not analysis_path.exists():
        return None
    payload: dict[str, Any] = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            payload["metadata_ingestion"] = json.load(handle)
    if analysis_path.exists():
        with analysis_path.open("r", encoding="utf-8") as handle:
            payload["analysis"] = json.load(handle)
    return payload


def available_study_downloads(accession: str) -> list[dict[str, Any]]:
    study_dir = PROCESSED_DIR / accession
    downloads = []
    for artifact, filename in DOWNLOAD_ARTIFACTS.items():
        path = study_dir / filename
        if not path.exists():
            continue
        downloads.append(
            {
                "artifact": artifact,
                "filename": filename,
                "bytes": path.stat().st_size,
                "url": f"/api/studies/{accession}/downloads/{artifact}",
            }
        )
    return downloads


def get_download_path(accession: str, artifact: str) -> Path | None:
    filename = DOWNLOAD_ARTIFACTS.get(artifact)
    if filename is None:
        return None
    path = PROCESSED_DIR / accession / filename
    if not path.exists():
        return None
    return path


@lru_cache(maxsize=8)
def load_gene_expression_summary(accession: str) -> dict[str, Any] | None:
    path = PROCESSED_DIR / accession / "gene_expression_summary.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=8)
def load_differential_expression(accession: str) -> dict[str, Any] | None:
    path = PROCESSED_DIR / accession / "differential_expression.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_feature_expression(symbol: str) -> dict[str, Any]:
    symbol_upper = symbol.upper()
    evidence = []
    for study in load_studies():
        expression = load_gene_expression_summary(study["accession"])
        if not expression:
            continue
        gene = expression.get("genes", {}).get(symbol_upper)
        if not gene:
            continue
        differential = load_differential_expression(study["accession"])
        statistical_contrasts = {}
        if differential:
            for contrast_id, rows in differential.get("contrasts", {}).items():
                match = next((row for row in rows if row.get("gene_symbol") == symbol_upper), None)
                if match:
                    statistical_contrasts[contrast_id] = match
        evidence.append(
            {
                "study_accession": study["accession"],
                "study_title": study["title"],
                "repository": study["repository"],
                "repository_url": study["repository_url"],
                "statistical_contrasts": statistical_contrasts,
                **gene,
            }
        )
    return {
        "feature": symbol_upper,
        "feature_type": "gene",
        "evidence_count": len(evidence),
        "expression_evidence": evidence,
    }


@lru_cache(maxsize=1)
def load_signatures() -> list[dict[str, Any]]:
    with SIGNATURE_REGISTRY.open("r", encoding="utf-8") as handle:
        return json.load(handle)["signatures"]


@lru_cache(maxsize=16)
def load_signature_scores(accession: str) -> dict[str, Any] | None:
    path = PROCESSED_DIR / accession / "signature_scores.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def list_signature_scores() -> dict[str, Any]:
    signatures = load_signatures()
    ready = []
    for study in load_studies():
        scores = load_signature_scores(study["accession"])
        if scores:
            ready.append(
                {
                    "study_accession": study["accession"],
                    "signatures": sorted(scores.get("signatures", {})),
                }
            )
    return {"count": len(signatures), "signatures": signatures, "ready_studies": ready}


def get_signature_score(signature_id: str) -> dict[str, Any]:
    signature_id = signature_id.upper()
    evidence = []
    for study in load_studies():
        scores = load_signature_scores(study["accession"])
        if not scores:
            continue
        signature = scores.get("signatures", {}).get(signature_id)
        if not signature:
            continue
        evidence.append(
            {
                "study_accession": study["accession"],
                "study_title": study["title"],
                "repository": study["repository"],
                "repository_url": study["repository_url"],
                **signature,
            }
        )
    return {
        "signature_id": signature_id,
        "evidence_count": len(evidence),
        "signature_evidence": evidence,
    }


def search_entities(query: str) -> list[dict[str, Any]]:
    query_lower = query.lower()
    results: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for study in load_studies():
        for field, entity_type in [
            ("featured_genes", "gene"),
            ("featured_cell_types", "cell_type"),
            ("featured_pathways", "pathway"),
            ("clinical_states", "clinical_state"),
        ]:
            for value in study.get(field, []):
                if query_lower in value.lower():
                    key = (entity_type, value)
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append(
                        {
                            "type": entity_type,
                            "label": value,
                            "supporting_accessions": [
                                item["accession"]
                                for item in load_studies()
                                if value in item.get(field, [])
                            ],
                        }
                    )
    return results


def nar_readiness() -> dict[str, Any]:
    studies = load_studies()
    omics_layers = load_omics_layers()
    multiomics_sources = load_multiomics_sources()
    public_studies = [study for study in studies if study.get("public_access") == "open"]
    processed = [
        study
        for study in studies
        if study.get("processing_status") == "processed"
        or load_study_sample_summary(study["accession"]) is not None
    ]
    curated = [
        study
        for study in studies
        if str(study.get("curation_status", "")).startswith("curated")
    ]

    return {
        "target_journal": "Nucleic Acids Research Database Issue",
        "status": "pre-alpha",
        "criteria": [
            {
                "criterion": "Fully functional public URL",
                "status": "not_started",
                "evidence": "Local prototype exists; production deployment is still required.",
            },
            {
                "criterion": "No login or registration for public data",
                "status": "designed",
                "evidence": "The public API and portal are anonymous by design.",
            },
            {
                "criterion": "Value-added database, not a repository listing",
                "status": "in_progress",
                "evidence": "Registry captures standardized transplant states, sample origins, modalities, and planned evidence summaries.",
            },
            {
                "criterion": "Underlying primary omics data already public",
                "status": "in_progress",
                "evidence": f"{len(public_studies)} registered studies are marked as open public access.",
            },
            {
                "criterion": "Help material for first-time visitors",
                "status": "started",
                "evidence": "The portal has initial Help and About sections; detailed tutorials remain to be written.",
            },
            {
                "criterion": "Long-term maintainability",
                "status": "not_started",
                "evidence": "Funding, domain, archival plan, and update cadence must be documented before submission.",
            },
        ],
        "registered_study_count": len(studies),
        "registered_multiomics_source_count": len(multiomics_sources),
        "registered_omics_layer_count": len(omics_layers),
        "processed_omics_layer_count": sum(1 for layer in omics_layers if layer.get("processed_accessions")),
        "curated_study_count": len(curated),
        "processed_study_count": len(processed),
        "expression_ready_study_count": sum(
            1 for study in studies if load_gene_expression_summary(study["accession"]) is not None
        ),
        "signature_ready_study_count": sum(
            1 for study in studies if load_signature_scores(study["accession"]) is not None
        ),
    }
