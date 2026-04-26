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
    assert "GSE13440" in accessions
    assert "GSE11881" in accessions
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
    assert payload["multiomics_feature_count"] >= 900
    assert payload["multiomics_feature_counts_by_modality"]["metabolomics"] >= 100
    assert payload["multiomics_feature_counts_by_modality"]["microbiome"] >= 700


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


def test_independent_geo_metadata_ingest_is_available() -> None:
    gse13440 = client.get("/api/studies/GSE13440").json()
    assert gse13440["sample_summary"]["sample_count"] == 22
    assert gse13440["sample_summary"]["by_clinical_state"]["ACR"] == 9
    assert gse13440["sample_summary"]["by_clinical_state"]["RHC_no_ACR"] == 13

    gse11881 = client.get("/api/studies/GSE11881").json()
    assert gse11881["sample_summary"]["sample_count"] == 17
    assert gse11881["sample_summary"]["by_clinical_state"]["operational_tolerance"] == 9
    assert gse11881["sample_summary"]["by_clinical_state"]["non_tolerant"] == 8

    gse243887 = client.get("/api/studies/GSE243887").json()
    assert gse243887["sample_summary"]["sample_count"] == 32
    assert gse243887["sample_summary"]["by_clinical_state"]["accepted_donor_liver"] == 10
    assert gse243887["sample_summary"]["by_clinical_state"]["rejected_donor_liver"] == 22

    gse200340 = client.get("/api/studies/GSE200340").json()
    assert gse200340["sample_summary"]["sample_count"] == 185
    assert gse200340["sample_summary"]["by_clinical_state"]["pre_transplant_blood"] == 75
    assert gse200340["sample_summary"]["by_clinical_state"]["early_post_transplant_blood"] == 55
    assert gse200340["sample_summary"]["by_clinical_state"]["late_post_transplant_blood"] == 55

    gse189539 = client.get("/api/studies/GSE189539").json()
    assert gse189539["sample_summary"]["sample_count"] == 8
    assert gse189539["sample_summary"]["cell_count"] == 58243
    assert gse189539["sample_summary"]["by_clinical_state"]["cold_perfusion_before_lt"] == 4
    assert gse189539["sample_summary"]["by_clinical_state"]["portal_reperfusion_after_lt"] == 4
    assert gse189539["sample_summary"]["cell_to_sample_mapping_status"] == "unavailable_in_geo_filtered_matrix"

    aging2020 = client.get("/api/studies/AGING_2020_LT_SERUM_PROTEOMICS").json()
    assert aging2020["sample_summary"]["sample_count"] == 49
    assert aging2020["sample_summary"]["by_clinical_state"]["stable_post_transplant"] == 10
    assert aging2020["sample_summary"]["by_clinical_state"]["acute_rejection"] == 10
    assert aging2020["sample_summary"]["by_clinical_state"]["ischemic_type_biliary_lesion"] == 9

    ijms2022 = client.get("/api/studies/IJMS_2022_LT_GRAFT_AKI_PROTEOMICS").json()
    assert ijms2022["sample_summary"]["sample_count"] == 14
    assert ijms2022["sample_summary"]["by_clinical_state"]["moderate_severe_early_aki"] == 7
    assert ijms2022["sample_summary"]["by_clinical_state"]["no_early_aki"] == 7

    ho1 = client.get("/api/studies/HO1_ACR_LIVER_TX_PROTEOMICS").json()
    assert ho1["sample_summary"]["sample_count"] == 6
    assert ho1["sample_summary"]["by_clinical_state"]["acute_cellular_rejection"] == 3
    assert ho1["sample_summary"]["by_clinical_state"]["non_rejection_post_lt"] == 3


def test_donor_liver_samples_filter_by_selection_state() -> None:
    response = client.get(
        "/api/studies/GSE243887/samples",
        params={"clinical_state": "accepted_donor_liver", "limit": 50},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 10
    assert all(sample["clinical_state"] == "accepted_donor_liver" for sample in payload["samples"])
    assert all(sample["matrix_sample_id"].startswith("HL") for sample in payload["samples"])


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
    assert "metabolomics_features" in artifacts
    assert "microbiome_summary" in artifacts
    assert "microbiome_features" in artifacts


def test_download_registry_exposes_mdpi_serum_metabolomics_artifacts() -> None:
    response = client.get("/api/studies/MDPI_METABO_2024_LT_GRAFT_PATHOLOGY/downloads")
    assert response.status_code == 200
    artifacts = {item["artifact"] for item in response.json()["downloads"]}
    assert "samples" in artifacts
    assert "sample_summary" in artifacts
    assert "cohort_summary" in artifacts
    assert "metabolomics_summary" in artifacts
    assert "metabolomics_features" in artifacts
    assert "source_file_inventory" in artifacts
    assert "provenance" in artifacts


def test_multiomics_feature_search_finds_metabolites() -> None:
    response = client.get(
        "/api/multiomics-features",
        params={"query": "oxochenodeoxycholic", "modality": "metabolomics"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    feature = payload["features"][0]
    assert feature["source_id"] == "DFI_MICROBIOME_LT_2024"
    assert feature["feature_type"] == "metabolite"
    assert "infection_positive_vs_negative" in feature["contrasts"]


def test_multiomics_feature_search_finds_mdpi_serotonin() -> None:
    response = client.get(
        "/api/multiomics-features",
        params={"query": "Serotonin", "modality": "metabolomics"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    feature = next(item for item in payload["features"] if item["source_id"] == "MDPI_METABO_2024_LT_GRAFT_PATHOLOGY")
    assert feature["feature_type"] == "metabolite"
    assert "TCMR_vs_biliary_complication" in feature["contrasts"]
    assert feature["measurement"] == "uM"


def test_multiomics_feature_search_finds_microbiome_taxa() -> None:
    response = client.get(
        "/api/multiomics-features",
        params={"query": "Enterococcus faecium", "modality": "microbiome"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    feature = payload["features"][0]
    assert feature["feature_type"] == "taxon"
    assert feature["measurement"] == "relative_abundance"
    assert feature["sample_count"] >= 1


def test_multiomics_feature_detail_returns_full_record() -> None:
    response = client.get(
        "/api/multiomics-features/DFI_MICROBIOME_LT_2024/taxon/"
        "firmicutes_lactobacillales_enterococcaceae_enterococcus_enterococcus_faecium"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["display_name"].endswith("Enterococcus faecium")
    assert payload["contrasts"]["infection_positive_vs_negative"]["case_state"] == "infection_positive"


def test_multiomics_feature_detail_returns_mdpi_metabolite_record() -> None:
    response = client.get("/api/multiomics-features/MDPI_METABO_2024_LT_GRAFT_PATHOLOGY/metabolite/serotonin")
    assert response.status_code == 200
    payload = response.json()
    assert payload["display_name"] == "Serotonin"
    contrast = payload["contrasts"]["TCMR_vs_biliary_complication"]
    assert contrast["case_state"] == "TCMR"
    assert contrast["control_state"] == "biliary_complication"
    assert contrast["effect_scale"] == "absolute_concentration_uM"


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


def test_feature_expression_includes_independent_rejection_dataset() -> None:
    response = client.get("/api/features/CXCL9/expression")
    assert response.status_code == 200
    payload = response.json()
    accessions = {item["study_accession"] for item in payload["expression_evidence"]}
    assert "GSE145780" in accessions
    assert "GSE13440" in accessions
    independent = next(item for item in payload["expression_evidence"] if item["study_accession"] == "GSE13440")
    assert "ACR_vs_RHC_no_ACR" in independent["statistical_contrasts"]
    contrast = independent["statistical_contrasts"]["ACR_vs_RHC_no_ACR"]
    assert contrast["case_state"] == "ACR"
    assert contrast["control_state"] == "RHC_no_ACR"
    assert "adj_p_value_bh" in contrast


def test_independent_rejection_dataset_downloads_expression_artifacts() -> None:
    response = client.get("/api/studies/GSE13440/downloads")
    assert response.status_code == 200
    artifacts = {item["artifact"] for item in response.json()["downloads"]}
    assert "gene_expression_summary" in artifacts
    assert "differential_expression" in artifacts
    assert "analysis_provenance" in artifacts


def test_operational_tolerance_dataset_has_blood_expression_evidence() -> None:
    response = client.get("/api/features/FOXP3/expression")
    assert response.status_code == 200
    payload = response.json()
    accessions = {item["study_accession"] for item in payload["expression_evidence"]}
    assert "GSE11881" in accessions
    evidence = next(item for item in payload["expression_evidence"] if item["study_accession"] == "GSE11881")
    contrast = evidence["statistical_contrasts"]["operational_tolerance_vs_non_tolerant"]
    assert contrast["case_state"] == "operational_tolerance"
    assert contrast["control_state"] == "non_tolerant"
    assert contrast["effect_scale"] == "source-normalized Affymetrix microarray intensity"
    assert contrast["fold_change_approx"] is None


def test_operational_tolerance_dataset_downloads_expression_artifacts() -> None:
    response = client.get("/api/studies/GSE11881/downloads")
    assert response.status_code == 200
    artifacts = {item["artifact"] for item in response.json()["downloads"]}
    assert "gene_expression_summary" in artifacts
    assert "differential_expression" in artifacts
    assert "signature_scores" in artifacts


def test_donor_liver_quality_dataset_has_expression_evidence() -> None:
    response = client.get("/api/features/ALB/expression")
    assert response.status_code == 200
    payload = response.json()
    evidence = next(item for item in payload["expression_evidence"] if item["study_accession"] == "GSE243887")
    contrast = evidence["statistical_contrasts"]["accepted_donor_liver_vs_rejected_donor_liver"]
    assert contrast["case_state"] == "accepted_donor_liver"
    assert contrast["control_state"] == "rejected_donor_liver"
    assert contrast["effect_scale"] == "log2CPM"
    assert "mean_difference" in contrast
    assert "p_value" in contrast
    assert "adj_p_value_bh" in contrast


def test_donor_liver_quality_downloads_expression_artifacts() -> None:
    response = client.get("/api/studies/GSE243887/downloads")
    assert response.status_code == 200
    artifacts = {item["artifact"] for item in response.json()["downloads"]}
    assert "samples" in artifacts
    assert "sample_summary" in artifacts
    assert "gene_expression_summary" in artifacts
    assert "gene_sample_values" in artifacts
    assert "differential_expression" in artifacts
    assert "analysis_provenance" in artifacts


def test_blood_monitoring_dataset_has_timepoint_expression_evidence() -> None:
    response = client.get("/api/features/CXCL10/expression")
    assert response.status_code == 200
    payload = response.json()
    evidence = next(item for item in payload["expression_evidence"] if item["study_accession"] == "GSE200340")
    contrast = evidence["statistical_contrasts"]["early_post_transplant_blood_vs_pre_transplant_blood"]
    assert contrast["case_state"] == "early_post_transplant_blood"
    assert contrast["control_state"] == "pre_transplant_blood"
    assert contrast["effect_scale"] == "log2CPM"
    assert "mean_difference" in contrast
    assert "p_value" in contrast
    assert "adj_p_value_bh" in contrast


def test_blood_monitoring_dataset_downloads_expression_artifacts() -> None:
    response = client.get("/api/studies/GSE200340/downloads")
    assert response.status_code == 200
    artifacts = {item["artifact"] for item in response.json()["downloads"]}
    assert "samples" in artifacts
    assert "sample_summary" in artifacts
    assert "gene_expression_summary" in artifacts
    assert "gene_sample_values" in artifacts
    assert "differential_expression" in artifacts
    assert "analysis_provenance" in artifacts


def test_single_cell_marker_endpoint_returns_gse189539_evidence() -> None:
    response = client.get("/api/features/NKG7/single-cell")
    assert response.status_code == 200
    payload = response.json()
    evidence = next(item for item in payload["single_cell_evidence"] if item["study_accession"] == "GSE189539")
    assert evidence["cell_count"] == 58243
    assert evidence["cell_to_sample_mapping_status"] == "unavailable_in_geo_filtered_matrix"
    assert evidence["whole_matrix_summary"]["pct_cells_detected"] > 60
    assert evidence["statistical_contrasts"] == {}


def test_single_cell_modules_and_downloads_are_available() -> None:
    modules = client.get("/api/studies/GSE189539/single-cell/modules")
    assert modules.status_code == 200
    module_payload = modules.json()
    assert module_payload["module_count"] >= 1
    assert "EAD_PATHOGENIC_IMMUNE_NICHE" in module_payload["modules"]

    downloads = client.get("/api/studies/GSE189539/downloads")
    assert downloads.status_code == 200
    artifacts = {item["artifact"] for item in downloads.json()["downloads"]}
    assert "single_cell_marker_summary" in artifacts
    assert "single_cell_module_summary" in artifacts
    assert "analysis_provenance" in artifacts


def test_protein_reference_endpoint_returns_pxd012615_evidence() -> None:
    response = client.get("/api/features/CYP3A4/protein")
    assert response.status_code == 200
    payload = response.json()
    evidence = next(item for item in payload["protein_evidence"] if item["study_accession"] == "PXD012615")
    assert evidence["primary_uniprot"] == "P08684"
    assert evidence["best_cell_type_by_mean_log2_intensity"] == "hepatocyte"
    assert evidence["cell_type_summary"]["hepatocyte"]["detected_replicate_count"] == 3
    assert evidence["sample_scope"] == "reference_human_liver_cells"


def test_direct_transplant_protein_endpoint_returns_aging2020_evidence() -> None:
    response = client.get("/api/features/ACLY/protein")
    assert response.status_code == 200
    payload = response.json()
    assert payload["protein_evidence"][0]["study_accession"] == "AGING_2020_LT_SERUM_PROTEOMICS"
    evidence = payload["protein_evidence"][0]
    assert evidence["evidence_kind"] == "direct_transplant_protein_biomarker"
    assert evidence["primary_uniprot"] == "P53396"
    assert evidence["sample_scope"] == "recipient_serum_complication_monitoring"
    assert any(item["context"] == "acute_rejection" for item in evidence["mapped_peaks"])
    assert any(
        contrast["contrast_id"] == "acute_rejection:stable_post_transplant_vs_acute_rejection"
        for contrast in evidence["published_contrasts"]
    )


def test_direct_graft_aki_protein_endpoint_returns_ijms2022_evidence() -> None:
    response = client.get("/api/features/SAA2/protein")
    assert response.status_code == 200
    payload = response.json()
    evidence = next(
        item for item in payload["protein_evidence"] if item["study_accession"] == "IJMS_2022_LT_GRAFT_AKI_PROTEOMICS"
    )
    assert evidence["evidence_kind"] == "direct_transplant_protein_biomarker"
    assert evidence["primary_uniprot"] == "P0DJI9"
    assert evidence["sample_scope"] == "graft_postreperfusion_biopsy_aki_risk"
    assert any(
        contrast["contrast_id"] == "moderate_severe_early_aki_vs_no_early_aki"
        for contrast in evidence["published_contrasts"]
    )


def test_direct_renal_monitoring_protein_endpoint_returns_pxd062924_evidence() -> None:
    response = client.get("/api/features/B2M/protein")
    assert response.status_code == 200
    payload = response.json()
    evidence = next(item for item in payload["protein_evidence"] if item["study_accession"] == "PXD062924")
    assert evidence["evidence_kind"] == "direct_transplant_protein_biomarker"
    assert evidence["primary_uniprot"] == "P61769"
    assert evidence["sample_scope"] == "recipient_serum_renal_function_monitoring"
    assert any(
        contrast["contrast_id"] == "normal_kidney_function_post_lt_vs_impaired_kidney_function_post_lt"
        for contrast in evidence["published_contrasts"]
    )


def test_direct_acr_protein_endpoint_returns_ho1_evidence() -> None:
    response = client.get("/api/features/HMOX1/protein")
    assert response.status_code == 200
    payload = response.json()
    evidence = next(item for item in payload["protein_evidence"] if item["study_accession"] == "HO1_ACR_LIVER_TX_PROTEOMICS")
    assert evidence["evidence_kind"] == "direct_transplant_protein_biomarker"
    assert evidence["primary_uniprot"] == "P09601"
    assert evidence["sample_scope"] == "recipient_serum_rejection_discovery_training_set"
    assert any(
        contrast["contrast_id"] == "acute_cellular_rejection_vs_non_rejection_post_lt"
        for contrast in evidence["published_contrasts"]
    )


def test_direct_tolerance_protein_endpoint_returns_frontiers2026_evidence() -> None:
    response = client.get("/api/features/FCGR3B/protein")
    assert response.status_code == 200
    payload = response.json()
    evidence = next(
        item
        for item in payload["protein_evidence"]
        if item["study_accession"] == "FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS"
    )
    assert evidence["evidence_kind"] == "direct_transplant_protein_biomarker"
    assert evidence["primary_uniprot"] == "O75015"
    assert evidence["sample_scope"] == "recipient_plasma_withdrawal_tolerance_discovery_set"
    assert any(
        contrast["contrast_id"] == "operational_tolerance_vs_non_tolerant"
        for contrast in evidence["published_contrasts"]
    )


def test_direct_peri_transplant_protein_endpoint_returns_sepmc6493459_evidence() -> None:
    response = client.get("/api/features/S100P/protein")
    assert response.status_code == 200
    payload = response.json()
    evidence = next(item for item in payload["protein_evidence"] if item["study_accession"] == "S-EPMC6493459")
    assert evidence["evidence_kind"] == "direct_transplant_protein_biomarker"
    assert evidence["primary_uniprot"] == "P25815"
    assert evidence["sample_scope"] == "recipient_serum_peri_transplant_hcc_timecourse"
    assert any(
        contrast["contrast_id"] == "pre_transplant_hcc_lt_candidate_vs_healthy_control"
        for contrast in evidence["published_contrasts"]
    )


def test_protein_reference_downloads_are_available() -> None:
    response = client.get("/api/studies/PXD012615/downloads")
    assert response.status_code == 200
    artifacts = {item["artifact"] for item in response.json()["downloads"]}
    assert "proteomics_summary" in artifacts
    assert "protein_features" in artifacts
    assert "analysis_provenance" in artifacts


def test_direct_transplant_proteomics_downloads_are_available() -> None:
    response = client.get("/api/studies/AGING_2020_LT_SERUM_PROTEOMICS/downloads")
    assert response.status_code == 200
    artifacts = {item["artifact"] for item in response.json()["downloads"]}
    assert "samples" in artifacts
    assert "sample_summary" in artifacts
    assert "cohort_summary" in artifacts
    assert "proteomics_summary" in artifacts
    assert "protein_features" in artifacts
    assert "analysis_provenance" in artifacts


def test_direct_graft_aki_proteomics_downloads_are_available() -> None:
    response = client.get("/api/studies/IJMS_2022_LT_GRAFT_AKI_PROTEOMICS/downloads")
    assert response.status_code == 200
    artifacts = {item["artifact"] for item in response.json()["downloads"]}
    assert "samples" in artifacts
    assert "sample_summary" in artifacts
    assert "cohort_summary" in artifacts
    assert "proteomics_summary" in artifacts
    assert "protein_features" in artifacts
    assert "analysis_provenance" in artifacts


def test_direct_renal_monitoring_study_detail_is_available() -> None:
    response = client.get("/api/studies/PXD062924")
    assert response.status_code == 200
    payload = response.json()
    assert payload["processing_status"] == "protein_feature_direct_evidence_ready"
    assert payload["sample_summary"]["sample_count"] == 10
    assert payload["sample_summary"]["by_clinical_state"]["normal_kidney_function_post_lt"] == 5
    assert payload["sample_summary"]["by_clinical_state"]["impaired_kidney_function_post_lt"] == 4


def test_direct_renal_monitoring_proteomics_downloads_are_available() -> None:
    response = client.get("/api/studies/PXD062924/downloads")
    assert response.status_code == 200
    artifacts = {item["artifact"] for item in response.json()["downloads"]}
    assert "samples" in artifacts
    assert "sample_summary" in artifacts
    assert "cohort_summary" in artifacts
    assert "proteomics_summary" in artifacts
    assert "protein_features" in artifacts
    assert "analysis_provenance" in artifacts


def test_direct_acr_proteomics_downloads_are_available() -> None:
    response = client.get("/api/studies/HO1_ACR_LIVER_TX_PROTEOMICS/downloads")
    assert response.status_code == 200
    artifacts = {item["artifact"] for item in response.json()["downloads"]}
    assert "samples" in artifacts
    assert "sample_summary" in artifacts
    assert "cohort_summary" in artifacts
    assert "proteomics_summary" in artifacts
    assert "protein_features" in artifacts
    assert "analysis_provenance" in artifacts


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
    assert "GSE243887" in payload["processed_accessions"]
    assert "GSE200340" in payload["processed_accessions"]
    assert "data/processed/GSE243887/gene_expression_summary.json" in payload["current_artifacts"]
    assert "data/processed/GSE200340/gene_expression_summary.json" in payload["current_artifacts"]

    single_cell = client.get("/api/omics-layers/single_cell").json()
    assert single_cell["readiness"] == "marker_matrix_evidence_ready"
    assert "GSE189539" in single_cell["processed_accessions"]
    assert "data/processed/GSE189539/single_cell_marker_summary.json" in single_cell["current_artifacts"]


def test_non_transcriptomic_layers_have_registered_external_sources() -> None:
    metabolome = client.get("/api/omics-layers/metabolome").json()
    microbiome = client.get("/api/omics-layers/microbiome").json()
    proteome = client.get("/api/omics-layers/proteome").json()
    assert "DFI_MICROBIOME_LT_2024" in metabolome["registered_accessions"]
    assert "MDPI_METABO_2024_LT_GRAFT_PATHOLOGY" in metabolome["registered_accessions"]
    assert "MDPI_METABO_2024_LT_GRAFT_PATHOLOGY" in metabolome["processed_accessions"]
    assert "DFI_MICROBIOME_LT_2024" in microbiome["registered_accessions"]
    assert "PXD012615" in proteome["registered_accessions"]
    assert "PXD012615" in proteome["processed_accessions"]
    assert "AGING_2020_LT_SERUM_PROTEOMICS" in proteome["registered_accessions"]
    assert "AGING_2020_LT_SERUM_PROTEOMICS" in proteome["processed_accessions"]
    assert "IJMS_2022_LT_GRAFT_AKI_PROTEOMICS" in proteome["registered_accessions"]
    assert "IJMS_2022_LT_GRAFT_AKI_PROTEOMICS" in proteome["processed_accessions"]
    assert "PXD062924" in proteome["registered_accessions"]
    assert "PXD062924" in proteome["processed_accessions"]
    assert "FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS" in proteome["registered_accessions"]
    assert "FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS" in proteome["processed_accessions"]
    assert "HO1_ACR_LIVER_TX_PROTEOMICS" in proteome["registered_accessions"]
    assert "HO1_ACR_LIVER_TX_PROTEOMICS" in proteome["processed_accessions"]
    assert "S-EPMC6493459" in proteome["registered_accessions"]
    assert "S-EPMC6493459" in proteome["processed_accessions"]


def test_non_transcriptomic_layer_details_link_feature_artifacts() -> None:
    metabolome = client.get("/api/omics-layers/metabolome").json()
    microbiome = client.get("/api/omics-layers/microbiome").json()
    proteome = client.get("/api/omics-layers/proteome").json()
    assert "data/processed/DFI_MICROBIOME_LT_2024/metabolomics_features.json" in metabolome["current_artifacts"]
    assert "data/processed/MDPI_METABO_2024_LT_GRAFT_PATHOLOGY/metabolomics_features.json" in metabolome["current_artifacts"]
    assert "data/processed/DFI_MICROBIOME_LT_2024/microbiome_features.json" in microbiome["current_artifacts"]
    assert "data/processed/PXD012615/protein_features.json" in proteome["current_artifacts"]
    assert "data/processed/AGING_2020_LT_SERUM_PROTEOMICS/protein_features.json" in proteome["current_artifacts"]
    assert "data/processed/FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS/protein_features.json" in proteome["current_artifacts"]
    assert "data/processed/IJMS_2022_LT_GRAFT_AKI_PROTEOMICS/protein_features.json" in proteome["current_artifacts"]
    assert "data/processed/PXD062924/protein_features.json" in proteome["current_artifacts"]
    assert "data/processed/HO1_ACR_LIVER_TX_PROTEOMICS/protein_features.json" in proteome["current_artifacts"]
    assert "data/processed/S-EPMC6493459/protein_features.json" in proteome["current_artifacts"]
    assert metabolome["readiness"] == "processed_feature_ready"
    assert microbiome["readiness"] == "processed_feature_ready"
    assert proteome["readiness"] == "protein_feature_direct_and_reference_ready"


def test_multiomics_source_registry_exposes_direct_liver_transplant_layer() -> None:
    response = client.get("/api/multiomics-sources/DFI_MICROBIOME_LT_2024")
    assert response.status_code == 200
    payload = response.json()
    assert "metabolomics" in payload["omics_modalities"]
    assert "microbiome" in payload["omics_modalities"]
    assert payload["source_type"] == "author_repository"
    assert payload["local_status"] == "processed_feature_ready"
    assert "data/processed/DFI_MICROBIOME_LT_2024/metabolomics_features.json" in payload["processed_artifacts"]
    assert "data/processed/DFI_MICROBIOME_LT_2024/microbiome_features.json" in payload["processed_artifacts"]


def test_multiomics_source_registry_exposes_mdpi_supplementary_metabolomics_layer() -> None:
    response = client.get("/api/multiomics-sources/MDPI_METABO_2024_LT_GRAFT_PATHOLOGY")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "supplementary_table"
    assert payload["local_status"] == "processed_feature_ready"
    assert payload["sample_origins"] == ["recipient_serum"]
    assert "data/processed/MDPI_METABO_2024_LT_GRAFT_PATHOLOGY/metabolomics_features.json" in payload["processed_artifacts"]


def test_multiomics_source_registry_exposes_protein_reference_layer() -> None:
    response = client.get("/api/multiomics-sources/PXD012615")
    assert response.status_code == 200
    payload = response.json()
    assert payload["local_status"] == "protein_feature_reference_ready"
    assert "proteomics" in payload["omics_modalities"]
    assert "data/processed/PXD012615/protein_features.json" in payload["processed_artifacts"]


def test_multiomics_source_registry_exposes_direct_transplant_proteomics_layer() -> None:
    response = client.get("/api/multiomics-sources/AGING_2020_LT_SERUM_PROTEOMICS")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "supplementary_table"
    assert payload["local_status"] == "protein_feature_direct_evidence_ready"
    assert payload["sample_origins"] == ["recipient_serum"]
    assert "acute_rejection" in payload["clinical_states"]
    assert "data/processed/AGING_2020_LT_SERUM_PROTEOMICS/protein_features.json" in payload["processed_artifacts"]


def test_multiomics_source_registry_exposes_direct_graft_aki_proteomics_layer() -> None:
    response = client.get("/api/multiomics-sources/IJMS_2022_LT_GRAFT_AKI_PROTEOMICS")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "supplementary_table"
    assert payload["local_status"] == "protein_feature_direct_evidence_ready"
    assert payload["sample_origins"] == ["graft_liver_biopsy"]
    assert "moderate_severe_early_aki" in payload["clinical_states"]
    assert "data/processed/IJMS_2022_LT_GRAFT_AKI_PROTEOMICS/protein_features.json" in payload["processed_artifacts"]


def test_multiomics_source_registry_exposes_direct_renal_monitoring_proteomics_layer() -> None:
    response = client.get("/api/multiomics-sources/PXD062924")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "repository_accession"
    assert payload["local_status"] == "protein_feature_direct_evidence_ready"
    assert payload["sample_origins"] == ["recipient_serum"]
    assert "impaired_kidney_function_post_lt" in payload["clinical_states"]
    assert "data/processed/PXD062924/protein_features.json" in payload["processed_artifacts"]


def test_multiomics_source_registry_exposes_pediatric_tolerance_proteomics_layer() -> None:
    response = client.get("/api/multiomics-sources/FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "article_figure"
    assert payload["local_status"] == "protein_feature_direct_evidence_ready"
    assert payload["sample_origins"] == ["recipient_plasma"]
    assert "operational_tolerance" in payload["clinical_states"]
    assert "data/processed/FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS/protein_features.json" in payload["processed_artifacts"]


def test_multiomics_source_registry_exposes_direct_acr_proteomics_layer() -> None:
    response = client.get("/api/multiomics-sources/HO1_ACR_LIVER_TX_PROTEOMICS")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "supplementary_table"
    assert payload["local_status"] == "protein_feature_direct_evidence_ready"
    assert payload["sample_origins"] == ["recipient_serum"]
    assert "acute_cellular_rejection" in payload["clinical_states"]
    assert "data/processed/HO1_ACR_LIVER_TX_PROTEOMICS/protein_features.json" in payload["processed_artifacts"]


def test_multiomics_source_registry_exposes_peri_transplant_serum_proteomics_layer() -> None:
    response = client.get("/api/multiomics-sources/S-EPMC6493459")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "article_table"
    assert payload["local_status"] == "protein_feature_direct_evidence_ready"
    assert payload["sample_origins"] == ["recipient_serum"]
    assert "pre_transplant_hcc_lt_candidate" in payload["clinical_states"]
    assert "data/processed/S-EPMC6493459/protein_features.json" in payload["processed_artifacts"]


def test_source_type_registry_includes_supplementary_tables() -> None:
    response = client.get("/api/source-types")
    assert response.status_code == 200
    payload = response.json()
    source_types = {item["source_type"] for item in payload["source_types"]}
    assert "supplementary_table" in source_types
    assert "repository_accession" in source_types
    assert "author_repository" in source_types


def test_dataset_triage_exposes_priority_queue() -> None:
    response = client.get("/api/dataset-triage", params={"priority": "P0"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 4
    accessions = {item["accession"] for item in payload["candidates"]}
    assert "GSE145780" in accessions
    assert "GSE13440" in accessions
    assert "DFI_MICROBIOME_LT_2024" in accessions
    assert "MDPI_METABO_2024_LT_GRAFT_PATHOLOGY" in accessions


def test_dataset_triage_detail_explains_next_action() -> None:
    response = client.get("/api/dataset-triage/GSE13440")
    assert response.status_code == 200
    payload = response.json()
    assert payload["triage_status"] == "ready_to_ingest"
    assert payload["priority"] == "P0"
    assert "independent transcriptome replication" in payload["next_action"]


def test_dataset_triage_marks_donor_liver_quality_processed() -> None:
    response = client.get("/api/dataset-triage/GSE243887")
    assert response.status_code == 200
    payload = response.json()
    assert payload["triage_status"] == "processed_expression"
    assert "donor-liver quality RNA-seq evidence" in payload["next_action"]


def test_dataset_triage_marks_pxd062924_processed_feature_ready() -> None:
    response = client.get("/api/dataset-triage/PXD062924")
    assert response.status_code == 200
    payload = response.json()
    assert payload["triage_status"] == "processed_feature_ready"
    assert payload["priority"] == "P1"
    assert "kidney-function monitoring" in payload["next_action"]


def test_dataset_triage_marks_blood_monitoring_processed() -> None:
    response = client.get("/api/dataset-triage/GSE200340")
    assert response.status_code == 200
    payload = response.json()
    assert payload["triage_status"] == "processed_expression"
    assert "blood time-point monitoring evidence" in payload["next_action"]


def test_dataset_triage_marks_single_cell_marker_matrix_processed() -> None:
    response = client.get("/api/dataset-triage/GSE189539")
    assert response.status_code == 200
    payload = response.json()
    assert payload["triage_status"] == "processed_single_cell_marker"
    assert "single-cell marker matrix evidence" in payload["next_action"]


def test_dataset_triage_marks_protein_reference_processed() -> None:
    response = client.get("/api/dataset-triage/PXD012615")
    assert response.status_code == 200
    payload = response.json()
    assert payload["triage_status"] == "processed_protein_reference"
    assert "human liver cell proteome reference" in payload["next_action"]


def test_dataset_triage_marks_direct_transplant_proteomics_processed() -> None:
    response = client.get("/api/dataset-triage/AGING_2020_LT_SERUM_PROTEOMICS")
    assert response.status_code == 200
    payload = response.json()
    assert payload["triage_status"] == "processed_feature_ready"
    assert payload["priority"] == "P0"
    assert "acute rejection versus stable graft function" in payload["next_action"]


def test_dataset_triage_marks_direct_graft_aki_proteomics_processed() -> None:
    response = client.get("/api/dataset-triage/IJMS_2022_LT_GRAFT_AKI_PROTEOMICS")
    assert response.status_code == 200
    payload = response.json()
    assert payload["triage_status"] == "processed_feature_ready"
    assert payload["priority"] == "P1"
    assert "ischemia/reperfusion-linked graft injury proteomics" in payload["next_action"]


def test_dataset_triage_marks_direct_acr_proteomics_processed() -> None:
    response = client.get("/api/dataset-triage/HO1_ACR_LIVER_TX_PROTEOMICS")
    assert response.status_code == 200
    payload = response.json()
    assert payload["triage_status"] == "processed_feature_ready"
    assert payload["priority"] == "P0"
    assert "acute cellular rejection proteomics" in payload["next_action"]


def test_data_model_schema_exposes_core_entities() -> None:
    response = client.get("/api/data-model")
    assert response.status_code == 200
    payload = response.json()
    entities = {item["entity"] for item in payload["entities"]}
    assert "study" in entities
    assert "sample" in entities
    assert "assay" in entities
    assert "feature" in entities
    assert "analysis_result" in entities
    assert "provenance" in entities


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
    assert "HOST_MICROBIOME_INFECTION_REJECTION" in ids


def test_use_case_detail_links_data_and_signatures() -> None:
    response = client.get("/api/use-cases/MOLECULAR_TCMR_DIAGNOSIS")
    assert response.status_code == 200
    payload = response.json()
    assert "GSE145780" in payload["primary_datasets"]
    assert "TCMR_IFNG_CYTOTOXIC" in payload["signatures"]
    assert payload["primary_dataset_records"][0]["accession"] == "GSE145780"


def test_donor_liver_quality_use_case_links_processed_expression() -> None:
    response = client.get("/api/use-cases/DONOR_LIVER_QUALITY")
    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness"] == "donor_expression_evidence_ready"
    assert payload["primary_dataset_records"][0]["accession"] == "GSE243887"
    assert any("log2(CPM + 1)" in line for line in payload["current_evidence"])


def test_gut_liver_axis_use_case_links_feature_level_dfi_source() -> None:
    response = client.get("/api/use-cases/HOST_MICROBIOME_INFECTION_REJECTION")
    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness"] == "feature_level_infection_evidence"
    assert "DFI_MICROBIOME_LT_2024" in payload["primary_datasets"]
    assert payload["primary_dataset_records"][0]["accession"] == "DFI_MICROBIOME_LT_2024"
    assert any("156 metabolite" in line for line in payload["current_evidence"])


def test_single_cell_use_case_links_gse189539_marker_evidence() -> None:
    response = client.get("/api/use-cases/SINGLE_CELL_MECHANISM")
    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness"] == "single_cell_marker_matrix_ready"
    assert "GSE189539" in payload["primary_datasets"]
    assert payload["primary_dataset_records"][0]["accession"] == "GSE189539"
    assert any("58,243 cells" in line for line in payload["current_evidence"])


def test_blood_monitoring_use_case_links_processed_timepoint_expression() -> None:
    response = client.get("/api/use-cases/BLOOD_MONITORING")
    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness"] == "blood_multimodal_monitoring_evidence_ready"
    assert "GSE200340" in payload["primary_datasets"]
    assert "MDPI_METABO_2024_LT_GRAFT_PATHOLOGY" in payload["supporting_datasets"]
    assert "AGING_2020_LT_SERUM_PROTEOMICS" in payload["supporting_datasets"]
    assert "PXD062924" in payload["supporting_datasets"]
    assert "FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS" in payload["supporting_datasets"]
    assert "S-EPMC6493459" in payload["supporting_datasets"]
    assert payload["primary_dataset_records"][0]["accession"] == "GSE200340"
    assert any("185 pediatric" in line for line in payload["current_evidence"])
    assert any("55 post-transplant serum metabolomics" in line for line in payload["current_evidence"])
    assert any("ACLY, FGA, and APOA1" in line for line in payload["current_evidence"])
    assert any("45 differential proteins" in line for line in payload["current_evidence"])
    assert any("baseline pediatric plasma proteomics" in line for line in payload["current_evidence"])
    assert any("S-EPMC6493459 adds direct peri-transplant serum iTRAQ proteomics" in line for line in payload["current_evidence"])


def test_operational_tolerance_use_case_links_frontiers_proteomics() -> None:
    response = client.get("/api/use-cases/OPERATIONAL_TOLERANCE")
    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness"] == "blood_tolerance_multimodal_evidence_ready"
    assert "GSE11881" in payload["primary_datasets"]
    assert "FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS" in payload["supporting_datasets"]
    assert any("802 reported DEPs" in line for line in payload["current_evidence"])


def test_injury_vs_rejection_use_case_links_direct_transplant_proteomics() -> None:
    response = client.get("/api/use-cases/INJURY_VS_REJECTION")
    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness"] == "multimodal_injury_rejection_context_ready"
    assert "AGING_2020_LT_SERUM_PROTEOMICS" in payload["supporting_datasets"]
    assert "IJMS_2022_LT_GRAFT_AKI_PROTEOMICS" in payload["supporting_datasets"]
    assert "HO1_ACR_LIVER_TX_PROTEOMICS" in payload["supporting_datasets"]
    assert "HMOX1" in payload["markers"]
    assert any("serum proteomic biomarker evidence" in line for line in payload["current_evidence"])
    assert any("postreperfusion graft proteomics" in line for line in payload["current_evidence"])
