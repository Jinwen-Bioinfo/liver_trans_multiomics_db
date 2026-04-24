from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "PXD062924"
RAW_DIR = ROOT / "data" / "raw" / SOURCE_ID
PROCESSED_DIR = ROOT / "data" / "processed" / SOURCE_ID

ARTICLE_URL = "https://www.frontiersin.org/journals/transplantation/articles/10.3389/frtra.2025.1572852/full"
PRIDE_URL = "https://www.ebi.ac.uk/pride/archive/projects/PXD062924"
ARTICLE_HTML_PATH = RAW_DIR / "pxd062924_frontiers_article.html"
PROTEIN_TABLE_PATH = RAW_DIR / "pxd062924_table3_proteins.tsv"
PATHWAY_TABLE_PATH = RAW_DIR / "pxd062924_table4_pathways.tsv"
UNIPROT_MAPPING_PATH = RAW_DIR / "pxd062924_uniprot_mapping.tsv"

NORMAL_STATE = "normal_kidney_function_post_lt"
IMPAIRED_STATE = "impaired_kidney_function_post_lt"
RECOVERED_STATE = "recovered_kidney_function_post_lt"
NORMAL_N = 5
IMPAIRED_N = 4
RECOVERED_N = 1
REPORTED_LONGITUDINAL_SAMPLE_COUNT = 20
REPORTED_DIFFERENTIAL_PROTEIN_COUNT = 45
REPORTED_TOTAL_QUANTIFIED_PROTEIN_COUNT = 174


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


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def round_or_none(value: float | None, digits: int = 6) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return float(f"{value:.{digits}g}")


def download_if_missing(url: str, path: Path) -> None:
    if path.exists():
        return
    ensure_dir(path.parent)
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request) as response, path.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def parse_scientific_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    normalized = (
        text.replace("\u2009", "")
        .replace("\u202f", "")
        .replace("−", "-")
        .replace("×10", "e")
        .replace("x10", "e")
        .replace("X10", "e")
    )
    return float(normalized)


def load_article_tables(article_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    tables = pd.read_html(str(article_path))
    protein_table = tables[2].copy()
    pathway_table = tables[3].copy()
    protein_table.to_csv(PROTEIN_TABLE_PATH, sep="\t", index=False)
    pathway_table.to_csv(PATHWAY_TABLE_PATH, sep="\t", index=False)
    return protein_table, pathway_table


def fetch_uniprot_mapping(accessions: list[str]) -> dict[str, dict[str, str]]:
    query = " OR ".join(f"accession:{accession}" for accession in accessions)
    url = (
        "https://rest.uniprot.org/uniprotkb/search?query="
        + quote(query)
        + "&fields=accession,gene_primary,protein_name&format=tsv&size=500"
    )
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    text = urlopen(request).read().decode("utf-8")
    UNIPROT_MAPPING_PATH.write_text(text, encoding="utf-8")
    mapping_rows = pd.read_csv(StringIO(text), sep="\t")
    mapping: dict[str, dict[str, str]] = {}
    for row in mapping_rows.to_dict("records"):
        mapping[str(row["Entry"])] = {
            "gene_symbol": str(row.get("Gene Names (primary)", "") or "").strip(),
            "protein_name": str(row.get("Protein names", "") or "").strip(),
        }
    return mapping


def build_pathway_map(pathway_table: pd.DataFrame) -> dict[int, dict[str, Any]]:
    pathway_map: dict[int, dict[str, Any]] = {}
    for row in pathway_table.to_dict("records"):
        pathway_index = int(row["No."])
        pathway_map[pathway_index] = {
            "pathway_index": pathway_index,
            "pathway_id": row["Pathway identifier"],
            "pathway_name": row["Pathway name"],
            "entities_found": int(row["#Entities found"]),
            "entities_total": int(row["#Entities total"]),
            "entities_p_value": round_or_none(parse_scientific_number(row["Entities p-value"])),
            "entities_fdr": round_or_none(parse_scientific_number(row["Entities FDR"])),
        }
    return pathway_map


def benjamini_hochberg(rows: list[dict[str, Any]]) -> None:
    indexed = [(idx, row["p_value"]) for idx, row in enumerate(rows) if row.get("p_value") is not None]
    indexed.sort(key=lambda item: item[1])
    total = len(indexed)
    adjusted = [None] * len(rows)
    running = 1.0
    for rank, (idx, p_value) in reversed(list(enumerate(indexed, start=1))):
        candidate = min(running, p_value * total / rank)
        running = candidate
        adjusted[idx] = round_or_none(candidate)
    for idx, row in enumerate(rows):
        row["adj_p_value_bh"] = adjusted[idx]


def parse_pathway_indexes(value: Any) -> list[int]:
    if value is None:
        return []
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []
    return [int(token.strip()) for token in text.split(",") if token.strip()]


def build_samples() -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for state, prefix, count in [
        (NORMAL_STATE, "NKF", NORMAL_N),
        (IMPAIRED_STATE, "IKF", IMPAIRED_N),
        (RECOVERED_STATE, "RKF", RECOVERED_N),
    ]:
        for index in range(1, count + 1):
            samples.append(
                {
                    "sample_accession": f"{prefix}{index:02d}",
                    "title": f"{state.replace('_', ' ')} patient {index}",
                    "clinical_state": state,
                    "sample_origin": "recipient_serum",
                    "assay_modality": "proteomics",
                    "collection_timepoint": "patient_level_average_of_week2_and_week5_serum_profiles",
                    "sample_id_origin": "synthetic_patient_placeholder_from_published_group_counts",
                }
            )
    return samples


def build_sample_summary(samples: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    by_state: dict[str, int] = {}
    for sample in samples:
        state = sample["clinical_state"]
        by_state[state] = by_state.get(state, 0) + 1
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "sample_count": len(samples),
        "by_clinical_state": by_state,
        "by_sample_origin": {"recipient_serum": len(samples)},
        "by_assay_modality": {"proteomics": len(samples)},
        "limitations": [
            "Sample identifiers are synthetic patient placeholders generated from published group counts.",
            "The public article collected serum at week 2 and week 5 post-transplant, but the exposed comparison is interpreted at the patient-group level rather than as a reusable per-sample intensity matrix.",
        ],
    }


def build_protein_payload(
    protein_table: pd.DataFrame,
    pathway_map: dict[int, dict[str, Any]],
    uniprot_mapping: dict[str, dict[str, str]],
    generated_at: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    proteins: dict[str, dict[str, Any]] = {}
    contrasts: list[dict[str, Any]] = []

    for row in protein_table.to_dict("records"):
        accession = str(row["UniProt number"]).strip()
        mapping = uniprot_mapping.get(accession, {})
        gene_symbol = mapping.get("gene_symbol") or accession
        if gene_symbol.lower() == "nan":
            gene_symbol = accession
        protein_name = mapping.get("protein_name") or str(row["Proteins"]).strip()
        if protein_name.lower() == "nan":
            protein_name = str(row["Proteins"]).strip()
        fold_change = float(row["Fold change Normal-KF/Impaired-KF"])
        p_value = parse_scientific_number(row["p-value Normal-KF vs. Impaired-KF"])
        pathway_indexes = parse_pathway_indexes(row["Reactome Pathway No."])
        pathway_records = [pathway_map[index] for index in pathway_indexes if index in pathway_map]
        direction = (
            "higher_in_normal_kidney_function_post_lt"
            if fold_change > 1
            else "higher_in_impaired_kidney_function_post_lt"
        )
        contrast = {
            "contrast_id": f"{NORMAL_STATE}_vs_{IMPAIRED_STATE}",
            "context": "post_lt_renal_function_monitoring",
            "case_state": NORMAL_STATE,
            "control_state": IMPAIRED_STATE,
            "case_n": NORMAL_N,
            "control_n": IMPAIRED_N,
            "mean_difference": round_or_none(math.log2(fold_change)),
            "effect_scale": "published_average_abundance_log2_ratio",
            "published_fold_change_average_value": round_or_none(fold_change),
            "p_value": round_or_none(p_value),
            "direction": direction,
        }
        protein_record = {
            "gene_symbol": gene_symbol,
            "primary_uniprot": accession,
            "protein_name": protein_name,
            "evidence_kind": "direct_transplant_protein_biomarker",
            "sample_scope": "recipient_serum_renal_function_monitoring",
            "summary_level": "published_differential_table",
            "measurement_type": "published_serum_protein_abundance_ratio",
            "reported_group_counts": {
                NORMAL_STATE: {"n": NORMAL_N},
                IMPAIRED_STATE: {"n": IMPAIRED_N},
                RECOVERED_STATE: {"n": RECOVERED_N},
            },
            "published_contrasts": [contrast],
            "reported_annotations": {
                "article_table_label": "Table 3",
                "article_protein_label": str(row["Proteins"]).strip(),
                "peptide_count": int(row["peptide count"]),
                "reactome_pathway_indexes": pathway_indexes,
                "reactome_pathways": pathway_records,
            },
            "limitations": [
                "This layer is reconstructed from the published differential serum proteomics table rather than a public per-sample abundance matrix.",
                "Fold changes and p-values come from the article's reported Normal-KF versus Impaired-KF comparison and are not recomputed from raw PRIDE intensities.",
                "The recovered patient is part of cohort-level context only; no reusable per-protein recovered-patient abundance table was publicly exposed in this V1 layer.",
            ],
        }
        proteins[gene_symbol] = protein_record
        contrasts.append({**contrast, "gene_symbol": gene_symbol})

    benjamini_hochberg(contrasts)
    for contrast in contrasts:
        proteins[contrast["gene_symbol"]]["published_contrasts"][0]["adj_p_value_bh"] = contrast["adj_p_value_bh"]

    payload = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "source_url": ARTICLE_URL,
        "assay_modality": "proteomics",
        "assay_scale": "published_average_abundance_log2_ratio",
        "sample_scope": "recipient_serum_renal_function_monitoring",
        "protein_count": len(proteins),
        "reported_differential_protein_count": REPORTED_DIFFERENTIAL_PROTEIN_COUNT,
        "reported_total_quantified_protein_count": REPORTED_TOTAL_QUANTIFIED_PROTEIN_COUNT,
        "proteins": proteins,
        "limitations": [
            "This source exposes a published serum proteomics differential table, not a reusable per-sample abundance matrix.",
            "The article reports two longitudinal serum collections per patient, but this V1 protein layer is intentionally framed as a patient-group comparison between Normal-KF and Impaired-KF.",
            "The main biological signal is post-transplant renal dysfunction monitoring rather than biopsy-defined rejection diagnosis.",
        ],
    }
    return payload, contrasts


def build_summary(generated_at: str, protein_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "assay_modality": "proteomics",
        "sample_scope": "recipient_serum_renal_function_monitoring",
        "sample_count": NORMAL_N + IMPAIRED_N + RECOVERED_N,
        "reported_longitudinal_serum_collection_count": REPORTED_LONGITUDINAL_SAMPLE_COUNT,
        "protein_feature_count": protein_payload["protein_count"],
        "reported_total_quantified_protein_count": REPORTED_TOTAL_QUANTIFIED_PROTEIN_COUNT,
        "reported_differential_protein_count": REPORTED_DIFFERENTIAL_PROTEIN_COUNT,
        "clinical_group_counts": {
            NORMAL_STATE: NORMAL_N,
            IMPAIRED_STATE: IMPAIRED_N,
            RECOVERED_STATE: RECOVERED_N,
        },
        "feature_symbols": sorted(protein_payload["proteins"].keys()),
        "limitations": protein_payload["limitations"],
    }


def build_provenance(generated_at: str, output_paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "parser": "scripts/ingest_pxd062924_lt_renal_function_proteomics.py",
        "source_files": {
            "article_html": {
                "url": ARTICLE_URL,
                **file_record(ARTICLE_HTML_PATH),
            },
            "protein_table_tsv": {
                **file_record(PROTEIN_TABLE_PATH),
            },
            "pathway_table_tsv": {
                **file_record(PATHWAY_TABLE_PATH),
            },
            "uniprot_mapping_tsv": {
                "url": "https://rest.uniprot.org/uniprotkb/search",
                **file_record(UNIPROT_MAPPING_PATH),
            },
        },
        "methods": [
            "Downloaded the Frontiers full-text article landing page for the PXD062924 study.",
            "Parsed article tables with pandas.read_html and extracted Table 3 differential proteins plus Table 4 Reactome pathways.",
            "Mapped UniProt accessions to primary gene symbols with the public UniProt REST API.",
            "Represented the published Normal-KF versus Impaired-KF protein table as a direct post-transplant serum proteomics evidence layer.",
            "Applied Benjamini-Hochberg correction across the article-reported protein p-values for database query exposure.",
            "Generated synthetic patient placeholders from the published cohort counts because a reusable per-sample protein intensity matrix was not exposed in this V1 layer.",
        ],
        "identifier_mapping_rule": "Used the article's published UniProt accession column and resolved each accession to a primary gene symbol via UniProt REST.",
        "normalization_rule": "Used the article's published fold-change ratios and p-values exactly as reported; no re-normalization or PRIDE raw-spectrum reprocessing was performed.",
        "outputs": {artifact: file_record(path) for artifact, path in output_paths.items()},
        "limitations": [
            "The public article provides a differential protein table, not a full sample-by-protein abundance matrix.",
            "Group labels reflect post-transplant kidney-function trajectories and should not be mislabeled as rejection outcomes.",
            "The recovered patient is described qualitatively in the article but is not represented by a reusable protein table in this V1 ingestion layer.",
        ],
    }


def build(force: bool = False) -> dict[str, Any]:
    ensure_dir(RAW_DIR)
    ensure_dir(PROCESSED_DIR)
    for path in [ARTICLE_HTML_PATH, PROTEIN_TABLE_PATH, PATHWAY_TABLE_PATH, UNIPROT_MAPPING_PATH]:
        if force and path.exists():
            path.unlink()
    download_if_missing(ARTICLE_URL, ARTICLE_HTML_PATH)

    protein_table, pathway_table = load_article_tables(ARTICLE_HTML_PATH)
    pathway_map = build_pathway_map(pathway_table)
    accessions = protein_table["UniProt number"].dropna().astype(str).tolist()
    uniprot_mapping = fetch_uniprot_mapping(accessions)

    generated_at = datetime.now(timezone.utc).isoformat()
    samples = build_samples()
    sample_summary = build_sample_summary(samples, generated_at)
    protein_payload, all_contrasts = build_protein_payload(protein_table, pathway_map, uniprot_mapping, generated_at)
    summary = build_summary(generated_at, protein_payload)
    cohort_summary = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "patient_count": NORMAL_N + IMPAIRED_N + RECOVERED_N,
        "comparison_patient_count": NORMAL_N + IMPAIRED_N,
        "reported_longitudinal_serum_collection_count": REPORTED_LONGITUDINAL_SAMPLE_COUNT,
        "clinical_group_counts": {
            NORMAL_STATE: NORMAL_N,
            IMPAIRED_STATE: IMPAIRED_N,
            RECOVERED_STATE: RECOVERED_N,
        },
        "protein_feature_count": protein_payload["protein_count"],
        "reported_total_quantified_protein_count": REPORTED_TOTAL_QUANTIFIED_PROTEIN_COUNT,
        "reported_differential_protein_count": REPORTED_DIFFERENTIAL_PROTEIN_COUNT,
        "limitations": sample_summary["limitations"],
    }
    source_inventory = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "files": [
            {"label": "article_html", **file_record(ARTICLE_HTML_PATH)},
            {"label": "protein_table_tsv", **file_record(PROTEIN_TABLE_PATH)},
            {"label": "pathway_table_tsv", **file_record(PATHWAY_TABLE_PATH)},
            {"label": "uniprot_mapping_tsv", **file_record(UNIPROT_MAPPING_PATH)},
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
        "patient_count": NORMAL_N + IMPAIRED_N + RECOVERED_N,
        "comparison_patient_count": NORMAL_N + IMPAIRED_N,
        "protein_feature_count": protein_payload["protein_count"],
        "contrast_count": len(all_contrasts),
        "feature_symbols": sorted(protein_payload["proteins"].keys())[:10],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PXD062924 post-LT renal function proteomics evidence layer.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(force=args.force), indent=2))


if __name__ == "__main__":
    main()
