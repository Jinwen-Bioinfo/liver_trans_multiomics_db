from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS"
RAW_DIR = ROOT / "data" / "raw" / SOURCE_ID
PROCESSED_DIR = ROOT / "data" / "processed" / SOURCE_ID

ARTICLE_URL = "https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2026.1800926/full"
ARTICLE_PDF_URL = "https://public-pages-files-2025.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2026.1800926/pdf"
XML_URL = "https://public-pages-files-2025.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2026.1800926/xml"

ARTICLE_HTML_PATH = RAW_DIR / "article.html"
ARTICLE_PDF_PATH = RAW_DIR / "article.pdf"
ARTICLE_XML_PATH = RAW_DIR / "article.xml"

IT_STATE = "operational_tolerance"
NIT_STATE = "non_tolerant"
DISCOVERY_N = 5
VALIDATION_IT_N = 17
VALIDATION_NIT_N = 22
TOTAL_WITHDRAWAL_COHORT_N = 31
DISCOVERY_DEP_COUNT = 802
DISCOVERY_UP_IN_IT = 382
DISCOVERY_DOWN_IN_IT = 420
VALIDATION_HD1_AUC = 0.81

PROTEIN_EVIDENCE = [
    {
        "gene_symbol": "HDAC1",
        "primary_uniprot": "Q13547",
        "protein_name": "Histone deacetylase 1",
        "direction": "lower_in_operational_tolerance",
        "reported_significance_symbol": None,
        "figure_panels": ["Figure 4C", "Figure 6A", "Figure 6B", "Figure 7"],
        "narrative_basis": "Explicitly described as lower in IT and prioritized as the candidate marker; validation plasma ELISA AUC reported as 0.81.",
        "validation": {
            "assay": "ELISA",
            "validation_case_state": IT_STATE,
            "validation_control_state": NIT_STATE,
            "validation_case_n": VALIDATION_IT_N,
            "validation_control_n": VALIDATION_NIT_N,
            "validation_auc": VALIDATION_HD1_AUC,
        },
    },
    {
        "gene_symbol": "FCGR3B",
        "primary_uniprot": "O75015",
        "protein_name": "Low affinity immunoglobulin gamma Fc region receptor III-B",
        "direction": "lower_in_operational_tolerance",
        "reported_significance_symbol": "***",
        "figure_panels": ["Figure 6A", "Figure 6B"],
        "narrative_basis": "Named in the Results text as showing group-level differences accompanying lower HDAC1 in IT.",
        "validation": None,
    },
    {
        "gene_symbol": "PADI4",
        "primary_uniprot": "Q9UM07",
        "protein_name": "Protein-arginine deiminase type-4",
        "direction": "lower_in_operational_tolerance",
        "reported_significance_symbol": "**",
        "figure_panels": ["Figure 6A", "Figure 6B"],
        "narrative_basis": "Named in the Results text as a differential neutrophil/NET-associated protein between IT and NIT.",
        "validation": None,
    },
    {
        "gene_symbol": "MAPK1",
        "primary_uniprot": "P28482",
        "protein_name": "Mitogen-activated protein kinase 1",
        "direction": "lower_in_operational_tolerance",
        "reported_significance_symbol": "*",
        "figure_panels": ["Figure 6A", "Figure 6B"],
        "narrative_basis": "Named in the Results text as a differential neutrophil-program protein between IT and NIT.",
        "validation": None,
    },
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path, *, url: str | None = None) -> dict[str, Any]:
    record = {
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if url:
        record["source_url"] = url
    return record


def download_if_missing(url: str, path: Path) -> None:
    if path.exists():
        return
    ensure_dir(path.parent)
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request) as response, path.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def build_samples() -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for patient_index in range(1, DISCOVERY_N + 1):
        samples.append(
            {
                "sample_accession": f"IT_DISCOVERY_{patient_index:02d}",
                "participant_id": f"IT_DISCOVERY_{patient_index:02d}",
                "clinical_state": IT_STATE,
                "sample_origin": "recipient_plasma",
                "assay_modality": "proteomics",
                "assay_role": "discovery_dia_proteomics",
                "timepoint": "baseline_before_withdrawal",
            }
        )
        samples.append(
            {
                "sample_accession": f"NIT_DISCOVERY_{patient_index:02d}",
                "participant_id": f"NIT_DISCOVERY_{patient_index:02d}",
                "clinical_state": NIT_STATE,
                "sample_origin": "recipient_plasma",
                "assay_modality": "proteomics",
                "assay_role": "discovery_dia_proteomics",
                "timepoint": "baseline_before_withdrawal",
            }
        )
    return samples


def build_sample_summary(samples: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "sample_count": len(samples),
        "participant_count": len(samples),
        "by_clinical_state": {
            IT_STATE: DISCOVERY_N,
            NIT_STATE: DISCOVERY_N,
        },
        "by_sample_origin": {"recipient_plasma": len(samples)},
        "by_assay_modality": {"proteomics": len(samples)},
        "reported_total_withdrawal_cohort_n": TOTAL_WITHDRAWAL_COHORT_N,
        "reported_validation_elisa_n": VALIDATION_IT_N + VALIDATION_NIT_N,
        "limitations": [
            "The reusable feature layer is restricted to the 10-sample discovery proteomics subset rather than the full 31-patient withdrawal cohort.",
            "Feature-level values are reconstructed from article text and figure panels because the supplementary DataSheet1 asset URL remains unresolved in this environment.",
            "Exact per-feature effect sizes are not publicly readable from the article figures, so this V1 layer preserves directionality and validation context rather than sample-level abundance matrices.",
        ],
    }


def build_protein_payload(generated_at: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    proteins: dict[str, dict[str, Any]] = {}
    contrasts: list[dict[str, Any]] = []
    for record in PROTEIN_EVIDENCE:
        contrast = {
            "contrast_id": f"{IT_STATE}_vs_{NIT_STATE}",
            "context": "baseline_withdrawal_tolerance_risk",
            "case_state": IT_STATE,
            "control_state": NIT_STATE,
            "case_n": DISCOVERY_N,
            "control_n": DISCOVERY_N,
            "mean_difference": None,
            "effect_scale": "article_figure_relative_expression_level",
            "p_value": None,
            "adj_p_value_bh": None,
            "direction": record["direction"],
            "feature_level_p_value_available": False,
            "selection_rule": "Article text and Figure 6A/6B report group separation for this protein in baseline IT versus NIT plasma proteomics.",
            "reported_significance_symbol": record["reported_significance_symbol"],
        }
        protein_record = {
            "gene_symbol": record["gene_symbol"],
            "primary_uniprot": record["primary_uniprot"],
            "protein_name": record["protein_name"],
            "evidence_kind": "direct_transplant_protein_biomarker",
            "sample_scope": "recipient_plasma_withdrawal_tolerance_discovery_set",
            "summary_level": "article_figure_marker_panel",
            "measurement_type": "dia_plasma_proteomics_article_figure_signal",
            "reported_group_counts": {
                IT_STATE: {"n": DISCOVERY_N},
                NIT_STATE: {"n": DISCOVERY_N},
            },
            "published_contrasts": [contrast],
            "reported_annotations": {
                "figure_panels": record["figure_panels"],
                "narrative_basis": record["narrative_basis"],
                "reported_total_discovery_dep_count": DISCOVERY_DEP_COUNT,
                "reported_dep_up_in_it": DISCOVERY_UP_IN_IT,
                "reported_dep_down_in_it": DISCOVERY_DOWN_IN_IT,
                "supplementary_asset_unresolved": "DataSheet1.docx",
                "validation": record["validation"],
            },
            "limitations": [
                "This layer is reconstructed from article text and figure panels rather than a downloadable supplementary protein table or sample-level matrix.",
                "Directionality is preserved, but exact fold changes and reusable per-feature p-values are not exposed in the article figure panels.",
                "The main clinical framing is baseline withdrawal-risk stratification in pediatric liver transplantation, not biopsy-proven rejection diagnosis.",
            ],
        }
        proteins[record["gene_symbol"]] = protein_record
        contrasts.append({**contrast, "gene_symbol": record["gene_symbol"]})

    payload = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "source_url": ARTICLE_URL,
        "assay_modality": "proteomics",
        "assay_scale": "article_figure_relative_expression_level",
        "sample_scope": "recipient_plasma_withdrawal_tolerance_discovery_set",
        "protein_count": len(proteins),
        "reported_total_discovery_dep_count": DISCOVERY_DEP_COUNT,
        "reported_dep_up_in_it": DISCOVERY_UP_IN_IT,
        "reported_dep_down_in_it": DISCOVERY_DOWN_IN_IT,
        "proteins": proteins,
        "limitations": [
            "The discovery proteomics cohort contains only 10 baseline plasma samples (5 IT, 5 NIT).",
            "The unresolved DataSheet1 supplement means this V1 layer is intentionally limited to article-figure marker evidence rather than a broad differential table.",
            "Only HDAC1 has an explicitly reported downstream plasma validation cohort in the article text.",
        ],
    }
    return payload, contrasts


def build_summary(generated_at: str, protein_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "assay_modality": "proteomics",
        "sample_scope": "recipient_plasma_withdrawal_tolerance_discovery_set",
        "sample_count": DISCOVERY_N * 2,
        "validation_sample_count": VALIDATION_IT_N + VALIDATION_NIT_N,
        "protein_feature_count": protein_payload["protein_count"],
        "reported_total_discovery_dep_count": DISCOVERY_DEP_COUNT,
        "reported_dep_up_in_it": DISCOVERY_UP_IN_IT,
        "reported_dep_down_in_it": DISCOVERY_DOWN_IN_IT,
        "reported_validation_hdac1_auc": VALIDATION_HD1_AUC,
        "clinical_group_counts": {IT_STATE: DISCOVERY_N, NIT_STATE: DISCOVERY_N},
        "feature_symbols": sorted(protein_payload["proteins"].keys()),
        "limitations": protein_payload["limitations"],
    }


def build_provenance(generated_at: str, output_paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "parser": "scripts/ingest_frontiers_2026_ped_lt_tolerance_proteomics.py",
        "source_files": {
            "article_html": {"url": ARTICLE_URL, **file_record(ARTICLE_HTML_PATH)},
            "article_pdf": {"url": ARTICLE_PDF_URL, **file_record(ARTICLE_PDF_PATH)},
            "article_xml": {"url": XML_URL, **file_record(ARTICLE_XML_PATH)},
        },
        "methods": [
            "Downloaded the Frontiers article HTML, PDF, and XML records for the pediatric immunosuppression-withdrawal proteomics study.",
            "Confirmed that the article XML exposes a supplementary asset named DataSheet1.docx, but the actual downloadable asset URL could not be resolved through tested public paths in this environment.",
            "Recovered a conservative V1 marker panel from article text and Figure 6, preserving only proteins explicitly discussed in the Results section and associated figure panels.",
            "Recorded HDAC1 validation context from the article's 39-sample plasma ELISA cohort.",
        ],
        "identifier_mapping_rule": "Used canonical gene symbols and UniProt accessions for proteins explicitly named in the article text and figure panels.",
        "normalization_rule": "No raw or supplementary proteomics table was available; this V1 layer stores article-figure directionality and validation context without inferred quantitative normalization.",
        "outputs": {artifact: file_record(path) for artifact, path in output_paths.items()},
        "limitations": [
            "DataSheet1.docx is referenced in the article metadata but remained unresolved as a downloadable public asset in this environment.",
            "This layer preserves a narrow marker panel rather than the full 802-protein differential set.",
            "Exact effect sizes were not reverse-engineered from the figure graphics.",
        ],
    }


def build(force: bool = False) -> dict[str, Any]:
    ensure_dir(RAW_DIR)
    ensure_dir(PROCESSED_DIR)
    for path in [ARTICLE_HTML_PATH, ARTICLE_PDF_PATH, ARTICLE_XML_PATH]:
        if force and path.exists():
            path.unlink()
    download_if_missing(ARTICLE_URL, ARTICLE_HTML_PATH)
    download_if_missing(ARTICLE_PDF_URL, ARTICLE_PDF_PATH)
    download_if_missing(XML_URL, ARTICLE_XML_PATH)

    generated_at = datetime.now(timezone.utc).isoformat()
    samples = build_samples()
    sample_summary = build_sample_summary(samples, generated_at)
    protein_payload, contrasts = build_protein_payload(generated_at)
    summary = build_summary(generated_at, protein_payload)
    cohort_summary = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "planned_withdrawal_cohort_n": TOTAL_WITHDRAWAL_COHORT_N,
        "discovery_proteomics_n": DISCOVERY_N * 2,
        "validation_elisa_n": VALIDATION_IT_N + VALIDATION_NIT_N,
        "protein_feature_count": protein_payload["protein_count"],
        "reported_total_discovery_dep_count": DISCOVERY_DEP_COUNT,
        "reported_validation_hdac1_auc": VALIDATION_HD1_AUC,
        "limitations": sample_summary["limitations"],
    }
    source_inventory = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "files": [
            {"label": "article_html", **file_record(ARTICLE_HTML_PATH)},
            {"label": "article_pdf", **file_record(ARTICLE_PDF_PATH)},
            {"label": "article_xml", **file_record(ARTICLE_XML_PATH)},
        ],
    }

    output_paths = {
        "samples": PROCESSED_DIR / "samples.json",
        "sample_summary": PROCESSED_DIR / "sample_summary.json",
        "cohort_summary": PROCESSED_DIR / "cohort_summary.json",
        "proteomics_summary": PROCESSED_DIR / "proteomics_summary.json",
        "protein_features": PROCESSED_DIR / "protein_features.json",
        "source_file_inventory": PROCESSED_DIR / "source_file_inventory.json",
    }
    write_json(output_paths["samples"], samples)
    write_json(output_paths["sample_summary"], sample_summary)
    write_json(output_paths["cohort_summary"], cohort_summary)
    write_json(output_paths["proteomics_summary"], summary)
    write_json(output_paths["protein_features"], protein_payload)
    write_json(output_paths["source_file_inventory"], source_inventory)

    provenance_path = PROCESSED_DIR / "analysis_provenance.json"
    provenance = build_provenance(generated_at, output_paths)
    write_json(provenance_path, provenance)
    output_paths["analysis_provenance"] = provenance_path

    return {
        "study_accession": SOURCE_ID,
        "discovery_sample_count": DISCOVERY_N * 2,
        "validation_sample_count": VALIDATION_IT_N + VALIDATION_NIT_N,
        "protein_feature_count": protein_payload["protein_count"],
        "contrast_count": len(contrasts),
        "feature_symbols": sorted(protein_payload["proteins"].keys()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FRONTIERS 2026 pediatric LT tolerance proteomics V1 marker layer.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(force=args.force), indent=2))


if __name__ == "__main__":
    main()
