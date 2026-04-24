from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "HO1_ACR_LIVER_TX_PROTEOMICS"
RAW_DIR = ROOT / "data" / "raw" / SOURCE_ID
PROCESSED_DIR = ROOT / "data" / "processed" / SOURCE_ID

ARTICLE_URL = "https://atm.amegroups.org/article/view/37242/html"
TABLE_S1_URL = "https://cdn.amegroups.cn/journals/amepc/files/journals/16/articles/37242/public/37242-PB16-1466-R1.png"
TABLE_S2_URL = "https://cdn.amegroups.cn/journals/amepc/files/journals/16/articles/37242/public/37242-PB17-2864-R1.png"

ARTICLE_HTML_PATH = RAW_DIR / "article.html"
TABLE_S1_PATH = RAW_DIR / "table_s1.png"
TABLE_S2_PATH = RAW_DIR / "table_s2.png"
TABLE_S1_OCR_PATH = RAW_DIR / "table_s1_ocr.txt"
TABLE_S2_OCR_PATH = RAW_DIR / "table_s2_ocr.txt"

ACR_STATE = "acute_cellular_rejection"
NON_REJECTION_STATE = "non_rejection_post_lt"
ACR_N = 3
NON_REJECTION_N = 3
REPORTED_DEP_COUNT = 287

TAG_MAP = {
    ACR_STATE: ["118", "119", "121"],
    NON_REJECTION_STATE: ["113", "115", "117"],
}

SAMPLE_METADATA = [
    {
        "sample_accession": "ACR_118",
        "clinical_state": ACR_STATE,
        "itraq_tag": "118",
        "patient_index": 1,
        "age_years": 56,
        "sex": "female",
        "diagnosis": "cirrhosis_hbv",
        "rejection_day_after_lt": 35,
    },
    {
        "sample_accession": "ACR_119",
        "clinical_state": ACR_STATE,
        "itraq_tag": "119",
        "patient_index": 2,
        "age_years": 54,
        "sex": "female",
        "diagnosis": "cirrhosis_hbv",
        "rejection_day_after_lt": 24,
    },
    {
        "sample_accession": "ACR_121",
        "clinical_state": ACR_STATE,
        "itraq_tag": "121",
        "patient_index": 3,
        "age_years": 34,
        "sex": "male",
        "diagnosis": "cirrhosis_hbv",
        "rejection_day_after_lt": 13,
    },
    {
        "sample_accession": "NREJ_113",
        "clinical_state": NON_REJECTION_STATE,
        "itraq_tag": "113",
        "patient_index": 1,
        "age_years": 51,
        "sex": "female",
        "diagnosis": "cirrhosis_hbv",
        "rejection_day_after_lt": None,
    },
    {
        "sample_accession": "NREJ_115",
        "clinical_state": NON_REJECTION_STATE,
        "itraq_tag": "115",
        "patient_index": 2,
        "age_years": 48,
        "sex": "male",
        "diagnosis": "cirrhosis_hbv",
        "rejection_day_after_lt": None,
    },
    {
        "sample_accession": "NREJ_117",
        "clinical_state": NON_REJECTION_STATE,
        "itraq_tag": "117",
        "patient_index": 3,
        "age_years": 38,
        "sex": "male",
        "diagnosis": "cirrhosis_hbv",
        "rejection_day_after_lt": None,
    },
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def round_or_none(value: float | None, digits: int = 6) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return float(f"{value:.{digits}g}")


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


def extract_tag_mapping(article_html: str) -> dict[str, list[str]]:
    pattern = re.compile(
        r"rejection group samples were labeled with ([0-9,\sand]+) iTRAQ tags respectively,"
        r" and the non-rejection group samples were labeled with ([0-9,\sand]+) iTRAQ tags",
        re.IGNORECASE,
    )
    match = pattern.search(article_html)
    if not match:
        return TAG_MAP

    def normalize_tags(raw: str) -> list[str]:
        return re.findall(r"\b\d{3}\b", raw)

    return {
        ACR_STATE: normalize_tags(match.group(1)),
        NON_REJECTION_STATE: normalize_tags(match.group(2)),
    }


def ocr_png(image_path: Path, output_path: Path) -> str:
    if output_path.exists():
        return output_path.read_text(encoding="utf-8")
    try:
        from PIL import Image
        import pytesseract
    except Exception as exc:  # pragma: no cover - local environment fallback
        raise RuntimeError("pytesseract and Pillow are required to OCR the supplementary PNG tables") from exc

    text = pytesseract.image_to_string(Image.open(image_path), config="--psm 6")
    output_path.write_text(text, encoding="utf-8")
    return text


def normalize_accession(token: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", token).upper()
    if cleaned.startswith("0"):
        cleaned = "O" + cleaned[1:]
    if cleaned.startswith("PO"):
        cleaned = "P0" + cleaned[2:]
    return cleaned


def split_gene_symbol(tokens: list[str]) -> tuple[str, list[str]]:
    if len(tokens) >= 2 and tokens[-1].isdigit() and re.fullmatch(r"[A-Z0-9-]+", tokens[-2]):
        return f"{tokens[-2]}{tokens[-1]}", tokens[:-2]
    return tokens[-1], tokens[:-1]


def parse_dep_lines(ocr_text: str) -> tuple[list[dict[str, Any]], int]:
    proteins: list[dict[str, Any]] = []
    upregulated_count = 0
    section = "header"
    for raw_line in ocr_text.splitlines():
        line = " ".join(raw_line.strip().split())
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("up-regulated proteins"):
            section = "up"
            continue
        if lower.startswith("down-regulated proteins"):
            section = "down"
            continue
        if section not in {"up", "down"}:
            continue
        if not re.search(r"\d+\.\d+$", line):
            continue
        tokens = line.split()
        if len(tokens) < 4:
            continue
        fold_change = float(tokens[-1])
        accession = normalize_accession(tokens[0])
        gene_symbol, protein_name_tokens = split_gene_symbol(tokens[1:-1])
        gene_symbol = re.sub(r"[^A-Za-z0-9-]", "", gene_symbol).upper()
        protein_name = " ".join(protein_name_tokens).strip()
        if not gene_symbol or not protein_name:
            continue
        direction = "higher_in_acute_cellular_rejection" if section == "up" else "higher_in_non_rejection_post_lt"
        proteins.append(
            {
                "accession": accession,
                "gene_symbol": gene_symbol,
                "protein_name": protein_name,
                "fold_change": fold_change,
                "direction": direction,
                "section": section,
            }
        )
        if section == "up":
            upregulated_count += 1
    return proteins, upregulated_count


def build_samples() -> list[dict[str, Any]]:
    samples = []
    for sample in SAMPLE_METADATA:
        samples.append(
            {
                **sample,
                "title": f"{sample['clinical_state'].replace('_', ' ')} patient {sample['patient_index']}",
                "sample_origin": "recipient_serum",
                "assay_modality": "proteomics",
                "collection_timepoint": "post_transplant_rejection_workup_discovery_training_set",
                "sample_id_origin": "published_itrq_training_set_tags_and_supplementary_table_s1",
            }
        )
    return samples


def build_sample_summary(generated_at: str) -> dict[str, Any]:
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "sample_count": len(SAMPLE_METADATA),
        "by_clinical_state": {
            ACR_STATE: ACR_N,
            NON_REJECTION_STATE: NON_REJECTION_N,
        },
        "by_sample_origin": {"recipient_serum": len(SAMPLE_METADATA)},
        "by_assay_modality": {"proteomics": len(SAMPLE_METADATA)},
        "limitations": [
            "Samples are a small iTRAQ discovery training set reconstructed from article text and supplementary Table S1 rather than a reusable sample-level intensity matrix.",
            "This layer should be interpreted as acute-cellular-rejection biomarker discovery evidence, not as a validated classifier.",
        ],
    }


def build_cohort_summary(generated_at: str, tag_map: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "sample_scope": "recipient_serum_rejection_discovery_training_set",
        "cohort_design": "published_iTRAQ_training_set",
        "group_counts": {
            ACR_STATE: ACR_N,
            NON_REJECTION_STATE: NON_REJECTION_N,
        },
        "itraq_tag_mapping": tag_map,
        "reported_selection_rule": {
            "upregulated_threshold": "> 1.2",
            "downregulated_threshold": "< 0.833",
            "article_text_requirement": "p < 0.05",
        },
    }


def build_proteomics_payload(
    proteins: list[dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    protein_records: dict[str, dict[str, Any]] = {}
    for item in proteins:
        gene_symbol = item["gene_symbol"]
        protein_records[gene_symbol] = {
            "gene_symbol": gene_symbol,
            "primary_uniprot": item["accession"],
            "protein_name": item["protein_name"],
            "evidence_kind": "direct_transplant_protein_biomarker",
            "sample_scope": "recipient_serum_rejection_discovery_training_set",
            "summary_level": "ocr_recovered_published_differential_table",
            "measurement_type": "itraq_relative_protein_abundance_fold_change",
            "reported_group_counts": {
                ACR_STATE: {"n": ACR_N, "itraq_tags": TAG_MAP[ACR_STATE]},
                NON_REJECTION_STATE: {"n": NON_REJECTION_N, "itraq_tags": TAG_MAP[NON_REJECTION_STATE]},
            },
            "published_contrasts": [
                {
                    "contrast_id": f"{ACR_STATE}_vs_{NON_REJECTION_STATE}",
                    "context": "serum_rejection_biomarker_discovery",
                    "case_state": ACR_STATE,
                    "control_state": NON_REJECTION_STATE,
                    "case_n": ACR_N,
                    "control_n": NON_REJECTION_N,
                    "direction": item["direction"],
                    "effect_scale": "published_fold_change_ratio_ocr_recovered",
                    "mean_difference": round_or_none(math.log2(item["fold_change"])),
                    "published_fold_change_average_value": round_or_none(item["fold_change"]),
                    "selection_rule": "fold change threshold plus article-level p<0.05 rule",
                    "feature_level_p_value_available": False,
                }
            ],
            "reported_annotations": {
                "table_section": "up_regulated" if item["section"] == "up" else "down_regulated",
            },
            "limitations": [
                "Feature evidence is reconstructed from OCR of a supplementary PNG table rather than from an author-provided TSV/XLSX matrix.",
                "The public supplementary table exposes fold changes but not per-feature reusable p-values, means, or sample-level abundances.",
                "This is a six-sample iTRAQ training set and should not be overstated as validated clinical performance.",
            ],
        }
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "source_url": ARTICLE_URL,
        "assay_modality": "proteomics",
        "assay_scale": "direct_transplant_serum_biomarker_discovery",
        "sample_scope": "recipient_serum_rejection_discovery_training_set",
        "protein_count": len(protein_records),
        "proteins": protein_records,
        "limitations": [
            "This layer is reconstructed from OCR of a supplementary image table and therefore may retain minor identifier normalization noise.",
            "No reusable per-sample protein intensity matrix is public in this V1 implementation.",
            "The training set compares acute cellular rejection versus non-rejection after liver transplantation in serum, not donor-liver quality or perioperative injury.",
        ],
    }


def build_proteomics_summary(proteins: list[dict[str, Any]], upregulated_count: int, generated_at: str) -> dict[str, Any]:
    downregulated_count = len(proteins) - upregulated_count
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "sample_scope": "recipient_serum_rejection_discovery_training_set",
        "protein_count": len(proteins),
        "reported_dep_count_from_article": REPORTED_DEP_COUNT,
        "upregulated_in_acute_cellular_rejection": upregulated_count,
        "upregulated_in_non_rejection_post_lt": downregulated_count,
        "contrast_ids": [f"{ACR_STATE}_vs_{NON_REJECTION_STATE}"],
        "effect_scale": "published_fold_change_ratio_ocr_recovered",
    }


def build_analysis_provenance(
    generated_at: str,
    *,
    article_html: str,
    proteins: list[dict[str, Any]],
    upregulated_count: int,
) -> dict[str, Any]:
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "processing_script": "scripts/ingest_ho1_acr_liver_tx_proteomics.py",
        "source_url": ARTICLE_URL,
        "source_files": {
            "article_html": file_record(ARTICLE_HTML_PATH, url=ARTICLE_URL),
            "table_s1_png": file_record(TABLE_S1_PATH, url=TABLE_S1_URL),
            "table_s2_png": file_record(TABLE_S2_PATH, url=TABLE_S2_URL),
            "table_s1_ocr": file_record(TABLE_S1_OCR_PATH),
            "table_s2_ocr": file_record(TABLE_S2_OCR_PATH),
        },
        "cohort_verification": {
            "table_s1_training_set_size": {ACR_STATE: ACR_N, NON_REJECTION_STATE: NON_REJECTION_N},
            "article_text_tag_mapping": extract_tag_mapping(article_html),
        },
        "feature_extraction": {
            "table": "Supplementary Table S2",
            "reported_dep_count_from_article": REPORTED_DEP_COUNT,
            "parsed_feature_count": len(proteins),
            "parsed_upregulated_count": upregulated_count,
            "parsed_downregulated_count": len(proteins) - upregulated_count,
            "identifier_rule": "first token = UniProt accession after OCR normalization; last token before fold-change = gene symbol",
            "effect_scale": "published_fold_change_ratio_ocr_recovered",
            "selection_rule": "Article states DEPs were selected with fold-change threshold and p<0.05, but per-feature p-values are not exposed in the OCR-recovered supplementary table.",
        },
        "limitations": [
            "The source table was publicly exposed as a PNG image, so OCR recovery is used instead of a machine-readable author table.",
            "Per-feature fold changes are available, but reusable per-feature p-values, raw reporter intensities, and sample-level abundances are not.",
            "This layer is a small serum discovery training set for acute cellular rejection versus non-rejection after liver transplantation.",
        ],
    }


def build_source_file_inventory() -> dict[str, Any]:
    inventory = {
        "study_accession": SOURCE_ID,
        "raw_files": [],
    }
    for path, url in [
        (ARTICLE_HTML_PATH, ARTICLE_URL),
        (TABLE_S1_PATH, TABLE_S1_URL),
        (TABLE_S2_PATH, TABLE_S2_URL),
        (TABLE_S1_OCR_PATH, None),
        (TABLE_S2_OCR_PATH, None),
    ]:
        if path.exists():
            inventory["raw_files"].append(file_record(path, url=url))
    return inventory


def main() -> None:
    ensure_dir(RAW_DIR)
    ensure_dir(PROCESSED_DIR)

    download_if_missing(ARTICLE_URL, ARTICLE_HTML_PATH)
    download_if_missing(TABLE_S1_URL, TABLE_S1_PATH)
    download_if_missing(TABLE_S2_URL, TABLE_S2_PATH)

    article_html = ARTICLE_HTML_PATH.read_text(encoding="utf-8")
    tag_map = extract_tag_mapping(article_html)
    table_s1_ocr = ocr_png(TABLE_S1_PATH, TABLE_S1_OCR_PATH)
    table_s2_ocr = ocr_png(TABLE_S2_PATH, TABLE_S2_OCR_PATH)
    _ = table_s1_ocr  # keep OCR artifact on disk for provenance
    proteins, upregulated_count = parse_dep_lines(table_s2_ocr)
    generated_at = datetime.now(timezone.utc).isoformat()

    samples = build_samples()
    write_json(PROCESSED_DIR / "samples.json", samples)
    write_json(PROCESSED_DIR / "sample_summary.json", build_sample_summary(generated_at))
    write_json(PROCESSED_DIR / "cohort_summary.json", build_cohort_summary(generated_at, tag_map))
    write_json(PROCESSED_DIR / "proteomics_summary.json", build_proteomics_summary(proteins, upregulated_count, generated_at))
    write_json(PROCESSED_DIR / "protein_features.json", build_proteomics_payload(proteins, generated_at))
    write_json(PROCESSED_DIR / "source_file_inventory.json", build_source_file_inventory())
    write_json(
        PROCESSED_DIR / "analysis_provenance.json",
        build_analysis_provenance(generated_at, article_html=article_html, proteins=proteins, upregulated_count=upregulated_count),
    )


if __name__ == "__main__":
    main()
