from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_study_registry_lists_priority_accessions() -> None:
    response = client.get("/api/studies")
    assert response.status_code == 200
    payload = response.json()
    accessions = {study["accession"] for study in payload["studies"]}
    assert "GSE145780" in accessions
    assert "GSE243887" in accessions
    assert "DFI_MICROBIOME_LT_2024" in accessions


def test_study_filter_by_modality() -> None:
    response = client.get("/api/studies", params={"modality": "single_cell_rna"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert all("single_cell_rna" in study["omics_modalities"] for study in payload["studies"])


def test_study_search_matches_featured_genes() -> None:
    response = client.get("/api/studies", params={"query": "CXCL9"})
    assert response.status_code == 200
    accessions = {study["accession"] for study in response.json()["studies"]}
    assert "GSE145780" in accessions


def test_search_finds_featured_gene() -> None:
    response = client.get("/api/search", params={"query": "CXCL9"})
    assert response.status_code == 200
    labels = {item["label"] for item in response.json()["results"]}
    assert "CXCL9" in labels


def test_nar_readiness_exposes_criteria() -> None:
    response = client.get("/api/nar/readiness")
    assert response.status_code == 200
    payload = response.json()
    assert payload["target_journal"] == "Nucleic Acids Research Database Issue"
    assert payload["registered_study_count"] >= 5
    assert payload["registered_omics_layer_count"] >= 6
    assert payload["registered_multiomics_source_count"] >= 2
    assert payload["curated_study_count"] >= 1


def test_processed_samples_endpoint_is_stable_when_empty_or_loaded() -> None:
    response = client.get("/api/studies/GSE145780/samples", params={"limit": 3})
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 235
    assert payload["limit"] == 3
    assert len(payload["samples"]) == 3
    assert payload["samples"][0]["study_accession"] == "GSE145780"


def test_samples_endpoint_filters_by_clinical_state() -> None:
    response = client.get(
        "/api/studies/GSE145780/samples",
        params={"clinical_state": "TCMR", "limit": 500},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 37
    assert all(sample["clinical_state"] == "TCMR" for sample in payload["samples"])


def test_processed_study_detail_includes_sample_summary() -> None:
    response = client.get("/api/studies/GSE145780")
    assert response.status_code == 200
    summary = response.json()["sample_summary"]
    assert summary["sample_count"] == 235
    assert summary["by_clinical_state"]["TCMR"] == 37


def test_processed_provenance_is_available() -> None:
    response = client.get("/api/studies/GSE145780/provenance")
    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata_ingestion"]["study_accession"] == "GSE145780"
    assert payload["metadata_ingestion"]["parser"] == "scripts/ingest_geo_series.py"
    assert payload["analysis"]["parser"] == "scripts/build_gene_evidence.py"
    assert "sha256" in payload["analysis"]["source_files"]["normalized_expression"]


def test_download_registry_exposes_processed_artifacts() -> None:
    response = client.get("/api/studies/GSE145780/downloads")
    assert response.status_code == 200
    artifacts = {item["artifact"] for item in response.json()["downloads"]}
    assert "samples" in artifacts
    assert "signature_scores" in artifacts


def test_download_registry_exposes_processed_non_transcriptomic_artifacts() -> None:
    response = client.get("/api/studies/DFI_MICROBIOME_LT_2024/downloads")
    assert response.status_code == 200
    artifacts = {item["artifact"] for item in response.json()["downloads"]}
    assert "cohort_summary" in artifacts
    assert "metabolomics_summary" in artifacts
    assert "microbiome_summary" in artifacts


def test_download_endpoint_serves_json_artifact() -> None:
    response = client.get("/api/studies/GSE145780/downloads/sample_summary")
    assert response.status_code == 200
    assert response.json()["sample_count"] == 235


def test_feature_expression_endpoint_returns_marker_evidence() -> None:
    response = client.get("/api/features/CXCL9/expression")
    assert response.status_code == 200
    payload = response.json()
    assert payload["feature"] == "CXCL9"
    assert payload["evidence_count"] >= 1
    evidence = payload["expression_evidence"][0]
    assert evidence["study_accession"] == "GSE145780"
    assert evidence["group_summary"]["TCMR"]["mean"] > evidence["group_summary"]["no_rejection"]["mean"]
    if evidence.get("statistical_contrasts"):
        contrast = evidence["statistical_contrasts"]["TCMR_vs_no_rejection"]
        assert contrast["mean_difference_log2_scale"] > 0
        assert "adj_p_value_bh" in contrast


def test_omics_layer_registry_is_multimodal() -> None:
    response = client.get("/api/omics-layers")
    assert response.status_code == 200
    payload = response.json()
    layer_ids = {item["layer_id"] for item in payload["omics_layers"]}
    assert "transcriptome_bulk" in layer_ids
    assert "proteome" in layer_ids
    assert "metabolome" in layer_ids
    assert "microbiome" in layer_ids


def test_omics_layer_detail_links_processed_artifacts() -> None:
    response = client.get("/api/omics-layers/transcriptome_bulk")
    assert response.status_code == 200
    payload = response.json()
    assert "GSE145780" in payload["processed_accessions"]
    assert payload["registered_study_records"][0]["accession"] == "GSE145780"


def test_non_transcriptomic_layers_have_registered_external_sources() -> None:
    metabolome = client.get("/api/omics-layers/metabolome").json()
    microbiome = client.get("/api/omics-layers/microbiome").json()
    proteome = client.get("/api/omics-layers/proteome").json()
    assert "DFI_MICROBIOME_LT_2024" in metabolome["registered_accessions"]
    assert "DFI_MICROBIOME_LT_2024" in microbiome["registered_accessions"]
    assert "PXD012615" in proteome["registered_accessions"]


def test_multiomics_source_registry_exposes_direct_liver_transplant_layer() -> None:
    response = client.get("/api/multiomics-sources/DFI_MICROBIOME_LT_2024")
    assert response.status_code == 200
    payload = response.json()
    assert "metabolomics" in payload["omics_modalities"]
    assert "microbiome" in payload["omics_modalities"]
    assert payload["source_type"] == "author_repository"
    assert payload["local_status"] == "processed_summary_ready"


def test_source_type_registry_includes_supplementary_tables() -> None:
    response = client.get("/api/source-types")
    assert response.status_code == 200
    payload = response.json()
    source_types = {item["source_type"] for item in payload["source_types"]}
    assert "supplementary_table" in source_types
    assert "repository_accession" in source_types
    assert "author_repository" in source_types


def test_fibrosis_marker_has_expected_direction() -> None:
    response = client.get("/api/features/COL1A1/expression")
    assert response.status_code == 200
    evidence = response.json()["expression_evidence"][0]
    assert evidence["group_summary"]["fibrosis"]["mean"] > evidence["group_summary"]["no_rejection"]["mean"]


def test_gene_explorer_supports_non_marker_gene_after_full_platform_mapping() -> None:
    response = client.get("/api/features/ALB/expression")
    assert response.status_code == 200
    payload = response.json()
    assert payload["feature"] == "ALB"
    assert payload["evidence_count"] >= 1
    evidence = payload["expression_evidence"][0]
    assert evidence["sample_count"] == 235
    assert evidence["probe_count"] >= 1


def test_signature_registry_endpoint() -> None:
    response = client.get("/api/signatures")
    assert response.status_code == 200
    payload = response.json()
    signature_ids = {item["signature_id"] for item in payload["signatures"]}
    assert "TCMR_IFNG_CYTOTOXIC" in signature_ids


def test_tcmr_signature_score_endpoint() -> None:
    response = client.get("/api/signatures/TCMR_IFNG_CYTOTOXIC/scores")
    assert response.status_code == 200
    payload = response.json()
    assert payload["signature_id"] == "TCMR_IFNG_CYTOTOXIC"
    assert payload["evidence_count"] >= 1
    evidence = payload["signature_evidence"][0]
    assert evidence["best_state_by_mean"] == "TCMR"
    assert evidence["expected_pattern_observed"] is True


def test_fibrosis_signature_score_endpoint() -> None:
    response = client.get("/api/signatures/FIBROSIS_ECM/scores")
    assert response.status_code == 200
    payload = response.json()
    evidence = payload["signature_evidence"][0]
    assert evidence["best_state_by_mean"] == "fibrosis"
    assert evidence["expected_pattern_observed"] is True


def test_use_case_registry_exposes_scientific_questions() -> None:
    response = client.get("/api/use-cases")
    assert response.status_code == 200
    payload = response.json()
    ids = {item["use_case_id"] for item in payload["use_cases"]}
    assert "MOLECULAR_TCMR_DIAGNOSIS" in ids
    assert "DONOR_LIVER_QUALITY" in ids


def test_use_case_detail_links_data_and_signatures() -> None:
    response = client.get("/api/use-cases/MOLECULAR_TCMR_DIAGNOSIS")
    assert response.status_code == 200
    payload = response.json()
    assert "GSE145780" in payload["primary_datasets"]
    assert "TCMR_IFNG_CYTOTOXIC" in payload["signatures"]
    assert payload["primary_dataset_records"][0]["accession"] == "GSE145780"
