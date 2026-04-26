from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_PATH = ROOT / "data" / "discovery" / "public_liver_tx_dataset_discovery.json"
SUPPLEMENTARY_PATH = ROOT / "data" / "discovery" / "supplementary_source_discovery.json"
OUT_PATH = ROOT / "data" / "registry" / "dataset_triage.json"

CURATED_PRIORITY_ACCESSIONS = {
    "GSE145780": {
        "priority": "P0",
        "triage_status": "processed_baseline",
        "next_action": "Keep as the initial INTERLIVER bulk-transcriptome baseline, but mark same-study marker evidence as exploratory until independently reproduced.",
        "scientific_value": ["TCMR molecular biopsy phenotypes", "fibrosis/chronic injury markers", "graft transcriptome reference"],
    },
    "GSE13440": {
        "priority": "P0",
        "triage_status": "ready_to_ingest",
        "next_action": "Download GEO matrix and metadata; test acute cellular rejection contrasts as an independent transcriptome replication layer.",
        "scientific_value": ["independent rejection replication", "recurrent hepatitis C confounding context"],
    },
    "GSE11881": {
        "priority": "P0",
        "triage_status": "ready_to_ingest",
        "next_action": "Download GEO/GDS data; curate operational tolerance versus immune activation phenotypes for blood-based transplant monitoring.",
        "scientific_value": ["operational tolerance", "blood immune monitoring", "cross-organ transplant biomarker comparison"],
    },
    "GDS3282": {
        "priority": "P0",
        "triage_status": "ready_to_ingest",
        "next_action": "Resolve GDS3282 to its GEO series/platform, download matrix, and map PBMC tolerance phenotypes.",
        "scientific_value": ["operational tolerance", "PBMC transcriptome", "non-invasive monitoring"],
    },
    "GSE14951": {
        "priority": "P1",
        "triage_status": "ready_to_ingest",
        "next_action": "Ingest liver graft expression data and map orthotopic transplant time/state labels.",
        "scientific_value": ["orthotopic liver transplantation", "graft expression trajectory"],
    },
    "GSE15480": {
        "priority": "P1",
        "triage_status": "ready_to_ingest",
        "next_action": "Ingest donor liver ischemic preconditioning expression data; map donor/graft quality and ischemia phenotypes.",
        "scientific_value": ["ischemia/reperfusion", "donor liver quality", "early graft injury"],
    },
    "E-MTAB-11688": {
        "priority": "P1",
        "triage_status": "ready_to_ingest",
        "next_action": "Use ArrayExpress/BioStudies files to ingest post-transplant NASH and fibrosis transcriptome contrasts.",
        "scientific_value": ["post-transplant NASH", "rapid fibrosis", "graft chronic injury"],
    },
    "DFI_MICROBIOME_LT_2024": {
        "priority": "P0",
        "triage_status": "processed_summary",
        "next_action": "Promote current summaries into feature-level microbiome/metabolome tables with infection contrasts and compound/taxon normalization.",
        "scientific_value": ["postoperative infection", "fecal metabolome", "gut microbiome"],
    },
    "GSE243887": {
        "priority": "P0",
        "triage_status": "processed_expression",
        "next_action": "Use as donor-liver quality RNA-seq evidence, then extend interpretation with pathway/module scores while keeping accepted/rejected labels clearly separated from post-transplant graft outcomes.",
        "scientific_value": ["donor liver quality", "accepted vs rejected donor liver", "direct donor liver RNA-seq evidence"],
    },
    "GSE200340": {
        "priority": "P1",
        "triage_status": "processed_expression",
        "next_action": "Add publication-linked rejection outcome labels only if reusable public tables can be verified; keep the current layer framed as blood time-point monitoring evidence.",
        "scientific_value": ["blood immune monitoring", "longitudinal pediatric liver transplant RNA-seq", "non-invasive time-point evidence"],
    },
    "GSE189539": {
        "priority": "P1",
        "triage_status": "processed_single_cell_marker",
        "next_action": "Use as single-cell marker matrix evidence, and recover reusable cell-to-sample and cell-type annotations if available; until then keep the layer framed as public matrix marker/module evidence.",
        "scientific_value": ["single-cell graft landscape", "early allograft dysfunction", "pathogenic immune niche"],
    },
    "PXD012615": {
        "priority": "P1",
        "triage_status": "processed_protein_reference",
        "next_action": "Use as a processed human liver cell proteome reference, then cross-link protein feature pages with RNA and single-cell evidence while keeping this layer separate from transplant-specific outcome claims.",
        "scientific_value": ["liver proteome reference", "protein feature normalization"],
    },
    "FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS": {
        "priority": "P1",
        "triage_status": "processed_feature_ready",
        "next_action": "Use the current article-figure V1 marker layer for pediatric baseline withdrawal-risk stratification, and upgrade it if the unresolved DataSheet1 supplementary proteomics table becomes directly downloadable.",
        "scientific_value": ["operational tolerance", "pediatric plasma proteomics", "immunosuppression withdrawal risk stratification"],
    },
    "AGING_2020_LT_SERUM_PROTEOMICS": {
        "priority": "P0",
        "triage_status": "processed_feature_ready",
        "next_action": "Use as a direct post-transplant serum proteomics biomarker layer for acute rejection versus stable graft function and ischemic-type biliary lesion contrasts, while keeping it framed as published group-summary MALDI-TOF evidence rather than a full per-sample proteome matrix.",
        "scientific_value": ["acute rejection serum proteomics", "biliary complication biomarkers", "non-invasive graft monitoring"],
    },
    "HO1_ACR_LIVER_TX_PROTEOMICS": {
        "priority": "P0",
        "triage_status": "processed_feature_ready",
        "next_action": "Use as a direct acute cellular rejection proteomics layer for serum ACR versus non-rejection after liver transplantation, while keeping it framed as OCR-recovered supplementary-table evidence rather than a reusable per-sample iTRAQ matrix.",
        "scientific_value": ["acute cellular rejection proteomics", "HO-1 axis biomarkers", "direct serum rejection evidence"],
    },
    "IJMS_2022_LT_GRAFT_AKI_PROTEOMICS": {
        "priority": "P1",
        "triage_status": "processed_feature_ready",
        "next_action": "Use as an ischemia/reperfusion-linked graft injury proteomics layer for moderate/severe early AKI versus no early AKI, while keeping it framed as published differential-table tissue proteomics rather than a per-sample intensity matrix.",
        "scientific_value": ["ischemia/reperfusion-linked graft injury proteomics", "postreperfusion graft biopsy", "early AKI tissue proteomics"],
    },
    "PXD062924": {
        "priority": "P1",
        "triage_status": "processed_feature_ready",
        "next_action": "Use as a direct post-transplant serum proteomics layer for normal versus impaired kidney-function monitoring, while keeping it framed as a published differential-table evidence layer rather than a reusable per-sample PRIDE intensity matrix.",
        "scientific_value": ["post-transplant renal dysfunction monitoring", "direct serum proteomics", "blood-based complication evidence after liver transplantation"],
    },
    "S-EPMC6493459": {
        "priority": "P1",
        "triage_status": "processed_feature_ready",
        "next_action": "Use as a direct peri-transplant serum proteomics layer for healthy-control versus pre-transplant HCC recipient contrasts, while keeping it framed as a partial published-table timecourse layer rather than a reusable per-sample iTRAQ matrix.",
        "scientific_value": ["peri-transplant serum proteomics", "pre-versus-post transplant blood context", "retinol-metabolism and S100P/AOX1 biomarker context"],
    },
    "MDPI_METABO_2024_LT_GRAFT_PATHOLOGY": {
        "priority": "P0",
        "triage_status": "processed_feature_ready",
        "next_action": "Use as a processed direct serum metabolomics layer for TCMR, biliary complications, and post-transplant MASH, and extend interpretation with pathway-level metabolite modules without overstating cohort size or classification performance.",
        "scientific_value": ["direct post-transplant serum metabolomics", "TCMR vs biliary vs MASH discrimination", "non-invasive graft pathology biomarkers"],
    },
}

CURATED_MANUAL_SOURCE_METADATA = {
    "DFI_MICROBIOME_LT_2024": {
        "title": "Fecal metabolite and microbiome profiling of liver transplant recipients at risk for postoperative infection",
        "repository": "external_curated_registry",
        "repository_url": None,
        "source_type": "author_repository",
        "directness": "direct_liver_transplant",
        "omics_modalities": ["microbiome", "metabolomics"],
        "sample_origins": ["stool"],
        "clinical_states": ["postoperative_infection"],
    },
    "PXD012615": {
        "title": "Human liver cells proteome",
        "repository": "PRIDE",
        "repository_url": "https://www.ebi.ac.uk/pride/archive/projects/PXD012615",
        "source_type": "repository_accession",
        "directness": "reference_not_direct_liver_transplant",
        "omics_modalities": ["proteomics"],
        "sample_origins": ["liver_reference"],
        "clinical_states": ["reference"],
    },
    "FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS": {
        "title": "Neutrophil-associated plasma proteomics identifies HDAC1 as a baseline biomarker of immune tolerance during immunosuppressant withdrawal after pediatric liver transplantation",
        "repository": "Frontiers supplementary",
        "repository_url": "https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2026.1800926/full",
        "source_type": "supplementary_table",
        "directness": "direct_liver_transplant",
        "omics_modalities": ["proteomics"],
        "sample_origins": ["plasma_serum"],
        "clinical_states": ["operational_tolerance", "non_tolerant"],
    },
    "AGING_2020_LT_SERUM_PROTEOMICS": {
        "title": "Serum proteomic biomarkers of liver transplant effectiveness, acute rejection, and ischemic-type biliary lesion",
        "repository": "Aging-US supplementary",
        "repository_url": "https://www.aging-us.com/article/103381/text",
        "source_type": "supplementary_table",
        "directness": "direct_liver_transplant",
        "omics_modalities": ["proteomics"],
        "sample_origins": ["plasma_serum"],
        "clinical_states": ["TCMR_or_ACR", "post_transplant_biliary_complications"],
    },
    "HO1_ACR_LIVER_TX_PROTEOMICS": {
        "title": "Identification of HO-1 as a novel biomarker for graft acute cellular rejection and prognosis prediction after liver transplantation",
        "repository": "ATM supplementary PNG tables",
        "repository_url": "https://atm.amegroups.org/article/view/37242/html",
        "source_type": "supplementary_table",
        "directness": "direct_liver_transplant",
        "omics_modalities": ["proteomics"],
        "sample_origins": ["plasma_serum"],
        "clinical_states": ["TCMR_or_ACR"],
    },
    "IJMS_2022_LT_GRAFT_AKI_PROTEOMICS": {
        "title": "Liver graft proteomics reveals potential incipient mechanisms behind early renal dysfunction after liver transplantation",
        "repository": "IJMS supplementary PDF table",
        "repository_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9569532/",
        "source_type": "supplementary_table",
        "directness": "direct_liver_transplant",
        "omics_modalities": ["proteomics"],
        "sample_origins": ["graft_liver_biopsy"],
        "clinical_states": ["ischemia_reperfusion", "early_aki_after_liver_transplant"],
    },
    "PXD062924": {
        "title": "Metabolomic and proteomic analyses of renal function after liver transplantation",
        "repository": "PRIDE",
        "repository_url": "https://www.ebi.ac.uk/pride/archive/projects/PXD062924",
        "source_type": "repository_accession",
        "directness": "direct_liver_transplant",
        "omics_modalities": ["proteomics", "metabolomics"],
        "sample_origins": ["plasma_serum"],
        "clinical_states": ["post_transplant_renal_dysfunction"],
    },
    "S-EPMC6493459": {
        "title": "Comparative proteomic analysis of human serum before and after liver transplantation using quantitative proteomics",
        "repository": "Oncotarget article",
        "repository_url": "https://www.oncotarget.com/article/26761/text/",
        "source_type": "article_table",
        "directness": "direct_liver_transplant",
        "omics_modalities": ["proteomics"],
        "sample_origins": ["plasma_serum"],
        "clinical_states": ["peri_transplant_monitoring", "pre_transplant_hcc_context"],
    },
    "MDPI_METABO_2024_LT_GRAFT_PATHOLOGY": {
        "title": "Harnessing Metabolites as Serum Biomarkers for Liver Graft Pathology Prediction Using Machine Learning",
        "repository": "MDPI supplementary",
        "repository_url": "https://doi.org/10.3390/metabo14050254",
        "source_type": "supplementary_table",
        "directness": "direct_liver_transplant",
        "omics_modalities": ["metabolomics"],
        "sample_origins": ["plasma_serum"],
        "clinical_states": ["TCMR_or_ACR", "post_transplant_nash_fibrosis"],
    },
}

CONTROLLED_ACCESS_PREFIXES = ("EGA", "EGAD", "EGAS", "PHSA", "EGA")
REPOSITORY_URL_PREFIX = {
    "GSE": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=",
    "GDS": "https://www.ncbi.nlm.nih.gov/sites/GDSbrowser?acc=",
    "PXD": "https://www.ebi.ac.uk/pride/archive/projects/",
    "MTBLS": "https://www.ebi.ac.uk/metabolights/",
}
SUPPLEMENTARY_READY_REPOS = {"biostudies-arrayexpress", "arrayexpress", "biostudies"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def accession_family(accession: str) -> str:
    if accession.startswith("GSE"):
        return "GEO Series"
    if accession.startswith("GDS"):
        return "GEO DataSet"
    if accession.startswith("E-MTAB"):
        return "ArrayExpress/BioStudies"
    if accession.startswith(("EGAD", "EGAS")):
        return "EGA controlled access"
    if accession.startswith("PXD"):
        return "PRIDE"
    if accession.startswith("MTBLS"):
        return "MetaboLights"
    if accession.startswith("SRP") or accession.startswith("PRJ"):
        return "SRA/BioProject"
    return "other"


def source_type_for(candidate: dict[str, Any]) -> str:
    accession = candidate.get("accession", "")
    repo = str(candidate.get("repository", "")).lower()
    if accession.startswith(CONTROLLED_ACCESS_PREFIXES) or repo == "ega":
        return "controlled_access"
    if repo in SUPPLEMENTARY_READY_REPOS or accession.startswith("E-MTAB"):
        return "repository_accession"
    if accession.startswith(("GSE", "GDS", "PXD", "MTBLS", "SRP", "PRJ")):
        return "repository_accession"
    return "literature_or_index_record"


def canonical_url(candidate: dict[str, Any]) -> str | None:
    accession = candidate.get("accession", "")
    for prefix, base in REPOSITORY_URL_PREFIX.items():
        if accession.startswith(prefix):
            return base + accession
    return candidate.get("repository_url")


def normalized_modalities(candidate: dict[str, Any]) -> list[str]:
    aliases = {
        "Transcriptomics": "bulk_transcriptomics",
        "Genomics": "genomics",
        "Genomic": "genomics",
        "Proteomics": "proteomics",
        "Metabolomics": "metabolomics",
        "Other": "other",
        "Unknown": "unknown",
    }
    labels = []
    for modality in candidate.get("inferred_modalities", []) + candidate.get("omics_modalities", []):
        labels.append(aliases.get(modality, modality))
    return sorted(set(labels)) or ["unknown"]


def infer_sample_origins(text: str) -> list[str]:
    rules = {
        "graft_liver_biopsy": ["biopsy", "allograft", "graft", "transplanted liver", "liver tissue"],
        "blood_pbmc": ["pbmc", "peripheral blood", "blood"],
        "plasma_serum": ["plasma", "serum", "cell-free", "cfdna"],
        "stool": ["stool", "fecal", "faecal", "gut microbiome"],
        "donor_liver": ["donor liver", "deceased donor", "living donor"],
    }
    origins = [label for label, keywords in rules.items() if any(keyword in text for keyword in keywords)]
    return origins or ["not_curated"]


def infer_clinical_states(text: str) -> list[str]:
    rules = {
        "TCMR_or_ACR": ["acute cellular rejection", "t cell-mediated rejection", "tcmr", "rejection"],
        "operational_tolerance": ["operational tolerance", "tolerance", "tolerant"],
        "ischemia_reperfusion": ["ischemia", "ischaemia", "reperfusion", "preconditioning"],
        "post_transplant_nash_fibrosis": ["nash", "fibrosis", "steatohepatitis"],
        "postoperative_infection": ["infection", "pathobiont"],
        "donor_graft_quality": ["donor", "graft quality", "living donor", "deceased donor"],
    }
    states = [label for label, keywords in rules.items() if any(keyword in text for keyword in keywords)]
    return states or ["not_curated"]


def default_triage(candidate: dict[str, Any]) -> tuple[str, str, str]:
    accession = candidate.get("accession", "")
    source_type = source_type_for(candidate)
    directness = candidate.get("directness")
    modalities = set(normalized_modalities(candidate))
    if source_type == "controlled_access":
        return (
            "controlled_access_register_only",
            "P3",
            "Register metadata only; do not ingest into public demo until access permissions and redistribution rules are clear.",
        )
    if directness != "direct_liver_transplant":
        return (
            "defer_false_positive_or_adjacent",
            "P3",
            "Manual review needed; automated search matched liver/transplant text but not a clear liver transplantation omics dataset.",
        )
    if accession.startswith(("GSE", "GDS", "E-MTAB")) and modalities & {"bulk_transcriptomics", "single_cell", "proteomics"}:
        return (
            "ready_to_ingest",
            "P1",
            "Verify repository files, download public matrices or supplementary tables, then map samples to standardized transplant states.",
        )
    if modalities & {"microbiome", "metabolomics", "proteomics", "methylation_cfDNA", "small_rna"}:
        return (
            "source_review_needed",
            "P2",
            "Inspect repository or publication supplements for reusable matrices; promote only if feature-level data can be obtained.",
        )
    return (
        "manual_review_needed",
        "P2",
        "Review title, abstract, and repository landing page before promotion.",
    )


def score_sort_key(item: dict[str, Any]) -> tuple[int, str, str]:
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    status_order = {
        "processed_baseline": 0,
        "processed_summary": 1,
        "processed_expression": 2,
        "processed_single_cell_marker": 3,
        "processed_protein_reference": 4,
        "processed_feature_ready": 5,
        "ready_to_ingest": 6,
        "source_review_needed": 7,
        "manual_review_needed": 8,
        "registered_reference": 9,
        "controlled_access_register_only": 10,
        "defer_false_positive_or_adjacent": 11,
    }
    return (
        priority_order.get(item["priority"], 9),
        status_order.get(item["triage_status"], 9),
        item["accession"],
    )


def build_candidate_item(candidate: dict[str, Any]) -> dict[str, Any]:
    accession = candidate["accession"]
    text = " ".join(
        str(candidate.get(field, ""))
        for field in ["title", "description", "repository", "accession"]
    ).lower()
    status, priority, next_action = default_triage(candidate)
    curated = CURATED_PRIORITY_ACCESSIONS.get(accession)
    if curated:
        status = curated["triage_status"]
        priority = curated["priority"]
        next_action = curated["next_action"]
    item = {
        "accession": accession,
        "title": candidate.get("title", ""),
        "repository": candidate.get("repository", ""),
        "repository_url": canonical_url(candidate),
        "accession_family": accession_family(accession),
        "source_type": source_type_for(candidate),
        "directness": candidate.get("directness"),
        "triage_status": status,
        "priority": priority,
        "omics_modalities": normalized_modalities(candidate),
        "sample_origins": infer_sample_origins(text),
        "clinical_states": infer_clinical_states(text),
        "organisms": candidate.get("organisms", []),
        "publication_date": candidate.get("publication_date"),
        "discovered_via": candidate.get("discovered_via", []),
        "scientific_value": curated.get("scientific_value", []) if curated else [],
        "next_action": next_action,
        "triage_reason": triage_reason(status, candidate),
    }
    return item


def triage_reason(status: str, candidate: dict[str, Any]) -> str:
    if candidate.get("accession") == "FRONTIERS_2026_PED_LT_TOLERANCE_PROTEOMICS":
        return "Frontiers XML exposes a supplementary DataSheet1.docx and the article explicitly reports baseline pediatric liver-transplant plasma proteomics comparing immune-tolerant versus non-tolerant withdrawal outcomes; the current database layer exposes a conservative article-figure marker panel while the full supplementary table remains unresolved."
    if candidate.get("accession") == "HO1_ACR_LIVER_TX_PROTEOMICS":
        return "The public ATM article exposes exact iTRAQ tag mapping for rejection versus non-rejection serum samples and Supplementary Table S2 provides an OCR-recoverable differential protein list centered on the HO-1 axis."
    if candidate.get("accession") == "PXD010812":
        return "PRIDE exposes a reusable MaxQuant search.zip archive for this direct liver-transplant ischemia/reperfusion cohort, including TQ01/TQ02/TQ03 batches with proteinGroups.txt and mqpar.xml, but the recovered MaxQuant experiment fields are blank so reporter-channel mapping for ischemic versus reperfused graft samples still cannot be defended."

    if candidate.get("accession") == "MDPI_METABO_2024_LT_GRAFT_PATHOLOGY":
        return "Public article text states that Supplementary Table S4 contains per-sample absolute metabolite concentrations for a liver transplant serum cohort spanning TCMR, biliary complications, and post-transplant MASH."
    if candidate.get("accession") == "PXD062924":
        return "Frontiers article Table 3 exposes 45 differential serum proteins for normal versus impaired kidney-function monitoring after liver transplantation, and the linked PRIDE accession documents the direct post-transplant cohort."
    if candidate.get("accession") == "S-EPMC6493459":
        return "The public Oncotarget full text exposes the peri-transplant liver-transplant serum iTRAQ study design, a partial visible pre-transplant versus healthy-control protein table including S100P, and a retinol-metabolism subset including AOX1 and ADH-family proteins."
    if status.startswith("processed"):
        return "Already has local processed artifacts and is part of the current demo evidence layer."
    if status == "ready_to_ingest":
        return "Public repository accession appears directly liver-transplant related and likely has reusable expression or omics data."
    if status == "source_review_needed":
        return "Relevant modality signal exists, but reusable feature-level files must be verified before ingest."
    if status == "controlled_access_register_only":
        return "Human data appear controlled-access; metadata can be listed but public redistribution requires permission."
    if status == "registered_reference":
        return "Useful normalization/reference layer but not direct transplant evidence."
    if status == "defer_false_positive_or_adjacent":
        return "Automated discovery signal is adjacent or likely false positive for liver transplantation."
    return "Requires manual curation before promotion."


def supplementary_overview() -> dict[str, Any]:
    if not SUPPLEMENTARY_PATH.exists():
        return {}
    payload = load_json(SUPPLEMENTARY_PATH)
    results = payload.get("results", {})
    return {
        "source": payload.get("source"),
        "generated_at_utc": payload.get("generated_at_utc"),
        "query_counts": {
            name: result.get("count")
            for name, result in results.items()
        },
        "note": "Supplementary material counts are broad hit counts. Individual articles need file-level review before registry promotion.",
    }


def main() -> None:
    discovery = load_json(DISCOVERY_PATH)
    candidates = [build_candidate_item(item) for item in discovery.get("all_candidates", [])]

    existing_accessions = {item["accession"] for item in candidates}
    for accession, curated in CURATED_PRIORITY_ACCESSIONS.items():
        if accession in existing_accessions:
            continue
        metadata = CURATED_MANUAL_SOURCE_METADATA.get(accession, {})
        candidates.append(
            {
                "accession": accession,
                "title": metadata.get("title", accession),
                "repository": metadata.get("repository", "external_curated_registry"),
                "repository_url": metadata.get("repository_url"),
                "accession_family": accession_family(accession),
                "source_type": metadata.get("source_type", source_type_for({"accession": accession})),
                "directness": metadata.get("directness", "direct_liver_transplant"),
                "triage_status": curated["triage_status"],
                "priority": curated["priority"],
                "omics_modalities": metadata.get("omics_modalities", ["proteomics"]),
                "sample_origins": metadata.get("sample_origins", ["liver_reference"]),
                "clinical_states": metadata.get("clinical_states", ["reference"]),
                "organisms": ["Homo sapiens"],
                "publication_date": None,
                "discovered_via": ["manual_curated_source"],
                "scientific_value": curated["scientific_value"],
                "next_action": curated["next_action"],
                "triage_reason": triage_reason(curated["triage_status"], {"accession": accession}),
            }
        )

    candidates = sorted(candidates, key=score_sort_key)
    status_counts = Counter(item["triage_status"] for item in candidates)
    priority_counts = Counter(item["priority"] for item in candidates)
    modality_counts = Counter(modality for item in candidates for modality in item["omics_modalities"])

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_discovery_file": str(DISCOVERY_PATH.relative_to(ROOT)),
        "scope": "Executable triage of public liver transplantation omics candidates for LiverTx-OmicsDB ingest planning.",
        "triage_policy": {
            "ready_to_ingest": "Direct liver transplantation public repository accessions with likely reusable matrices or tables.",
            "processed_expression": "Processed transcriptome-style evidence already exists locally and should stay above raw ingest candidates.",
            "processed_single_cell_marker": "Processed single-cell marker/module evidence already exists locally.",
            "processed_protein_reference": "Processed protein feature reference evidence already exists locally.",
            "source_review_needed": "Relevant non-transcriptomic or ambiguous public records requiring file-level verification.",
            "controlled_access_register_only": "Human controlled-access records; metadata only until permissions are resolved.",
            "defer_false_positive_or_adjacent": "Automated broad-search matches that should not drive the database build.",
        },
        "summary": {
            "candidate_count": len(candidates),
            "status_counts": dict(sorted(status_counts.items())),
            "priority_counts": dict(sorted(priority_counts.items())),
            "modality_counts": dict(sorted(modality_counts.items())),
            "p0_or_p1_count": sum(1 for item in candidates if item["priority"] in {"P0", "P1"}),
            "ready_or_processed_count": sum(
                1
                for item in candidates
                if item["triage_status"] in {
                    "ready_to_ingest",
                    "processed_baseline",
                    "processed_summary",
                    "processed_expression",
                    "processed_single_cell_marker",
                    "processed_protein_reference",
                    "processed_feature_ready",
                }
            ),
        },
        "priority_queue": [
            item for item in candidates if item["priority"] in {"P0", "P1"} and item["triage_status"] != "defer_false_positive_or_adjacent"
        ][:80],
        "candidates": candidates,
        "supplementary_source_overview": supplementary_overview(),
        "limitations": [
            "This file is a build-planning registry, not a final curated dataset registry.",
            "Automated labels must be verified at accession landing pages and publication supplements before ingest.",
            "Controlled-access records are not public redistributable data until access and license conditions are resolved.",
        ],
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output_path": str(OUT_PATH.relative_to(ROOT)),
                **payload["summary"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
