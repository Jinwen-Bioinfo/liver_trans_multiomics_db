from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "S-EPMC6493459"
RAW_DIR = ROOT / "data" / "raw" / SOURCE_ID
PROCESSED_DIR = ROOT / "data" / "processed" / SOURCE_ID

ARTICLE_URL = "https://www.oncotarget.com/article/26761/text/"
ARTICLE_HTML_PATH = RAW_DIR / "article.html"

HEALTHY_STATE = "healthy_control"
PRE_LT_STATE = "pre_transplant_hcc_lt_candidate"
POST_LT_DAY_1_STATE = "post_lt_day_1"
POST_LT_DAY_3_STATE = "post_lt_day_3"
POST_LT_DAY_7_STATE = "post_lt_day_7"

HEALTHY_N = 9
LT_PATIENT_N = 9
TIMEPOINT_N = 9
REPORTED_TOTAL_IDENTIFIED_PROTEIN_COUNT = 1399
REPORTED_PRE_LT_UPREGULATED_COUNT = 112

TABLE1_PROTEINS = [
    {
        "protein_id": "tr|J3QRK0|J3QRK0_HUMAN",
        "primary_uniprot": "J3QRK0",
        "gene_symbol": "ITGB4",
        "protein_name": "Integrin beta-4 (Fragment)",
        "ratio_b_vs_a": 10.0,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "tr|B4DUI8|B4DUI8_HUMAN",
        "primary_uniprot": "B4DUI8",
        "gene_symbol": "ACTA2",
        "protein_name": "cDNA FLJ52761, highly similar to Actin, aortic smooth muscle",
        "ratio_b_vs_a": 10.0,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "sp|Q3SY84|K2C71_HUMAN",
        "primary_uniprot": "Q3SY84",
        "gene_symbol": "KRT71",
        "protein_name": "Keratin, type II cytoskeletal 71",
        "ratio_b_vs_a": 10.0,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "sp|Q8IYL3|CA174_HUMAN",
        "primary_uniprot": "Q8IYL3",
        "gene_symbol": "C1ORF174",
        "protein_name": "UPF0688 protein C1orf174",
        "ratio_b_vs_a": 10.0,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "tr|J3KSQ2|J3KSQ2_HUMAN",
        "primary_uniprot": "J3KSQ2",
        "gene_symbol": "CLTC",
        "protein_name": "Clathrin heavy chain 1 (Fragment)",
        "ratio_b_vs_a": 9.594,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "tr|A8K6A5|A8K6A5_HUMAN",
        "primary_uniprot": "A8K6A5",
        "gene_symbol": "ITGA5",
        "protein_name": "cDNA FLJ77742, highly similar to Homo sapiens integrin alpha 5",
        "ratio_b_vs_a": 9.575,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "tr|Q86UW0|Q86UW0_HUMAN",
        "primary_uniprot": "Q86UW0",
        "gene_symbol": "OVGP1",
        "protein_name": "Ovarian epithelial carcinoma-related protein",
        "ratio_b_vs_a": 8.757,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "tr|A0A024R2T8|A0A024R2T8_HUMAN",
        "primary_uniprot": "A0A024R2T8",
        "gene_symbol": "ENDOGL1",
        "protein_name": "Endonuclease G-like 1, isoform CRA_b",
        "ratio_b_vs_a": 7.551,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "tr|D6RGG3|D6RGG3_HUMAN",
        "primary_uniprot": "D6RGG3",
        "gene_symbol": "COL12A1",
        "protein_name": "Collagen alpha-1(XII) chain",
        "ratio_b_vs_a": 6.66,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "sp|P25815|S100P_HUMAN",
        "primary_uniprot": "P25815",
        "gene_symbol": "S100P",
        "protein_name": "Protein S100-P",
        "ratio_b_vs_a": 5.38,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "sp|Q7L523|RRAGA_HUMAN",
        "primary_uniprot": "Q7L523",
        "gene_symbol": "RRAGA",
        "protein_name": "Ras-related GTP-binding protein A",
        "ratio_b_vs_a": 4.567,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "tr|Q7Z3Y6|Q7Z3Y6_HUMAN",
        "primary_uniprot": "Q7Z3Y6",
        "gene_symbol": "VH4-34",
        "protein_name": "Rearranged VH4-34 V gene segment (Fragment)",
        "ratio_b_vs_a": 4.433,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "tr|A0A0C4DH43|A0A0C4DH43_HUMAN",
        "primary_uniprot": "A0A0C4DH43",
        "gene_symbol": "A0A0C4DH43",
        "protein_name": "Uncharacterized protein (Fragment)",
        "ratio_b_vs_a": 2.93,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "tr|Q9UL79|Q9UL79_HUMAN",
        "primary_uniprot": "Q9UL79",
        "gene_symbol": "IGLV",
        "protein_name": "Myosin-reactive immunoglobulin light chain variable region (Fragment)",
        "ratio_b_vs_a": 2.865,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "sp|Q9UM07|PADI4_HUMAN",
        "primary_uniprot": "Q9UM07",
        "gene_symbol": "PADI4",
        "protein_name": "Protein-arginine deiminase type-4",
        "ratio_b_vs_a": 2.683,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "tr|B4E380|B4E380_HUMAN",
        "primary_uniprot": "B4E380",
        "gene_symbol": "H3C1",
        "protein_name": "Histone H3",
        "ratio_b_vs_a": 2.605,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "tr|D6RF35|D6RF35_HUMAN",
        "primary_uniprot": "D6RF35",
        "gene_symbol": "GC",
        "protein_name": "Vitamin D-binding protein",
        "ratio_b_vs_a": 2.355,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "tr|B1AH77|B1AH77_HUMAN",
        "primary_uniprot": "B1AH77",
        "gene_symbol": "RAC2",
        "protein_name": "Ras-related C3 botulinum toxin substrate 2",
        "ratio_b_vs_a": 2.195,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "sp|P62805|H4_HUMAN",
        "primary_uniprot": "P62805",
        "gene_symbol": "HIST1H4L",
        "protein_name": "Histone H4",
        "ratio_b_vs_a": 2.172,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "tr|Q5NV63|Q5NV63_HUMAN",
        "primary_uniprot": "Q5NV63",
        "gene_symbol": "V1-4",
        "protein_name": "V1-4 protein (Fragment)",
        "ratio_b_vs_a": 2.092,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "sp|P68871|HBB_HUMAN",
        "primary_uniprot": "P68871",
        "gene_symbol": "HBB",
        "protein_name": "Hemoglobin beta",
        "ratio_b_vs_a": 2.081,
        "table_label": "Table 1 (part of data)",
    },
    {
        "protein_id": "tr|D6R9C5|D6R9C5_HUMAN",
        "primary_uniprot": "D6R9C5",
        "gene_symbol": "SPP1",
        "protein_name": "Osteopontin (Fragment)",
        "ratio_b_vs_a": 2.078,
        "table_label": "Table 1 (part of data)",
    },
]

TABLE2_PROTEINS = [
    {
        "protein_id": "sp|P00325|ADH1B_HUMAN",
        "primary_uniprot": "P00325",
        "gene_symbol": "ADH1B",
        "protein_name": "Alcohol dehydrogenase IB (Class I), beta polypeptide, isoform CRA_a",
        "ratio_b_vs_a": 0.299,
        "table_label": "Table 2",
    },
    {
        "protein_id": "sp|P07327|ADH1A_HUMAN",
        "primary_uniprot": "P07327",
        "gene_symbol": "ADH1A",
        "protein_name": "Alcohol dehydrogenase 1A",
        "ratio_b_vs_a": 0.399,
        "table_label": "Table 2",
    },
    {
        "protein_id": "sp|P08319|ADH4_HUMAN",
        "primary_uniprot": "P08319",
        "gene_symbol": "ADH4",
        "protein_name": "Alcohol dehydrogenase 4",
        "ratio_b_vs_a": 0.438,
        "table_label": "Table 2",
    },
    {
        "protein_id": "sp|Q06278|AOXA_HUMAN",
        "primary_uniprot": "Q06278",
        "gene_symbol": "AOX1",
        "protein_name": "Aldehyde oxidase",
        "ratio_b_vs_a": 0.68,
        "table_label": "Table 2",
    },
    {
        "protein_id": "sp|P28332|ADH6_HUMAN",
        "primary_uniprot": "P28332",
        "gene_symbol": "ADH6",
        "protein_name": "Alcohol dehydrogenase 6",
        "ratio_b_vs_a": 0.721,
        "table_label": "Table 2",
    },
    {
        "protein_id": "tr|V9HVX6|V9HVX6_HUMAN",
        "primary_uniprot": "V9HVX6",
        "gene_symbol": "HEL-9",
        "protein_name": "Epididymis luminal protein 9",
        "ratio_b_vs_a": 0.808,
        "table_label": "Table 2",
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


def round_or_none(value: float | None, digits: int = 6) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return float(f"{value:.{digits}g}")


def all_proteins() -> list[dict[str, Any]]:
    return TABLE1_PROTEINS + TABLE2_PROTEINS


def build_samples() -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for patient_index in range(1, HEALTHY_N + 1):
        samples.append(
            {
                "sample_accession": f"HC_{patient_index:02d}",
                "participant_id": f"HC_{patient_index:02d}",
                "sample_origin": "recipient_serum",
                "clinical_state": HEALTHY_STATE,
                "timepoint": "healthy_baseline",
                "patient_index": patient_index,
                "cohort_role": "control",
            }
        )
    for patient_index in range(1, LT_PATIENT_N + 1):
        participant_id = f"LT_{patient_index:02d}"
        for clinical_state, timepoint in [
            (PRE_LT_STATE, "pre_transplant"),
            (POST_LT_DAY_1_STATE, "day_1_post_lt"),
            (POST_LT_DAY_3_STATE, "day_3_post_lt"),
            (POST_LT_DAY_7_STATE, "day_7_post_lt"),
        ]:
            samples.append(
                {
                    "sample_accession": f"{participant_id}_{timepoint.upper()}",
                    "participant_id": participant_id,
                    "sample_origin": "recipient_serum",
                    "clinical_state": clinical_state,
                    "timepoint": timepoint,
                    "patient_index": patient_index,
                    "cohort_role": "lt_recipient",
                }
            )
    return samples


def build_sample_summary(samples: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    by_state: dict[str, int] = {}
    for state in [HEALTHY_STATE, PRE_LT_STATE, POST_LT_DAY_1_STATE, POST_LT_DAY_3_STATE, POST_LT_DAY_7_STATE]:
        by_state[state] = sum(1 for sample in samples if sample["clinical_state"] == state)
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "sample_count": len(samples),
        "participant_count": HEALTHY_N + LT_PATIENT_N,
        "lt_participant_count": LT_PATIENT_N,
        "healthy_control_count": HEALTHY_N,
        "repeated_measure_design": True,
        "by_clinical_state": by_state,
        "by_sample_origin": {"recipient_serum": len(samples)},
        "by_assay_modality": {"proteomics": len(samples)},
        "limitations": [
            "The same nine liver-transplant patients were sampled across four peri-transplant timepoints, so this is a repeated-measures cohort rather than five independent groups.",
            "The published proteomics tables exposed only the pre-transplant versus healthy-control differential subset in machine-readable article text.",
            "No reusable per-sample iTRAQ intensity matrix or complete post-transplant differential table was publicly exposed in this V1 layer.",
        ],
    }


def build_protein_payload(generated_at: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    proteins: dict[str, dict[str, Any]] = {}
    contrasts: list[dict[str, Any]] = []
    for row in all_proteins():
        fold_change = float(row["ratio_b_vs_a"])
        direction = (
            "higher_in_pre_transplant_hcc_lt_candidate"
            if fold_change > 1
            else "higher_in_healthy_control"
        )
        contrast = {
            "contrast_id": f"{PRE_LT_STATE}_vs_{HEALTHY_STATE}",
            "context": "peri_transplant_hcc_serum_proteomics",
            "case_state": PRE_LT_STATE,
            "control_state": HEALTHY_STATE,
            "case_n": LT_PATIENT_N,
            "control_n": HEALTHY_N,
            "mean_difference": round_or_none(math.log2(fold_change)),
            "effect_scale": "published_itraq_ratio_pretransplant_vs_healthy_control",
            "published_fold_change_average_value": round_or_none(fold_change),
            "direction": direction,
            "feature_level_p_value_available": False,
            "selection_rule": (
                "Visible article table row reported in Oncotarget full-text Table 1 (partial upregulated list) "
                "or Table 2 (retinol-metabolism subset)."
            ),
        }
        protein_record = {
            "gene_symbol": row["gene_symbol"],
            "primary_uniprot": row["primary_uniprot"],
            "protein_name": row["protein_name"],
            "evidence_kind": "direct_transplant_protein_biomarker",
            "sample_scope": "recipient_serum_peri_transplant_hcc_timecourse",
            "summary_level": "partial_published_differential_table",
            "measurement_type": "published_itraq_relative_protein_ratio",
            "reported_group_counts": {
                HEALTHY_STATE: {"n": HEALTHY_N},
                PRE_LT_STATE: {"n": LT_PATIENT_N},
                POST_LT_DAY_1_STATE: {"n": TIMEPOINT_N},
                POST_LT_DAY_3_STATE: {"n": TIMEPOINT_N},
                POST_LT_DAY_7_STATE: {"n": TIMEPOINT_N},
            },
            "published_contrasts": [contrast],
            "reported_annotations": {
                "article_table_label": row["table_label"],
                "article_protein_id": row["protein_id"],
                "post_transplant_timepoints_profiled": ["day_1_post_lt", "day_3_post_lt", "day_7_post_lt"],
                "complete_post_transplant_feature_table_publicly_exposed": False,
            },
            "limitations": [
                "This layer is reconstructed from article-visible partial tables rather than a reusable per-sample iTRAQ matrix.",
                "Only pre-transplant versus healthy-control fold-change rows are directly machine-exposed in the public text; the day 1/day 3/day 7 post-transplant comparisons are described narratively but not provided as reusable feature tables here.",
                "The cohort consists of HCC recipients undergoing liver transplantation, so the biological framing is peri-transplant disease/reset context rather than rejection-specific classification.",
            ],
        }
        proteins[row["gene_symbol"]] = protein_record
        contrasts.append({**contrast, "gene_symbol": row["gene_symbol"]})

    payload = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "source_url": ARTICLE_URL,
        "assay_modality": "proteomics",
        "assay_scale": "published_itraq_ratio_pretransplant_vs_healthy_control",
        "sample_scope": "recipient_serum_peri_transplant_hcc_timecourse",
        "protein_count": len(proteins),
        "reported_total_identified_protein_count": REPORTED_TOTAL_IDENTIFIED_PROTEIN_COUNT,
        "reported_pre_lt_upregulated_count": REPORTED_PRE_LT_UPREGULATED_COUNT,
        "proteins": proteins,
        "limitations": [
            "The article identifies 1,399 proteins overall, but the public full text exposes only a partial visible subset of protein rows suitable for V1 database query.",
            "This V1 layer intentionally exposes only the directly published pre-transplant versus healthy-control iTRAQ ratios; it does not claim complete longitudinal post-transplant feature coverage.",
            "No reusable per-feature p-values were exposed in the public article text for these protein rows.",
        ],
    }
    return payload, contrasts


def build_summary(generated_at: str, protein_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "assay_modality": "proteomics",
        "sample_scope": "recipient_serum_peri_transplant_hcc_timecourse",
        "sample_count": HEALTHY_N + (LT_PATIENT_N * 4),
        "participant_count": HEALTHY_N + LT_PATIENT_N,
        "protein_feature_count": protein_payload["protein_count"],
        "reported_total_identified_protein_count": REPORTED_TOTAL_IDENTIFIED_PROTEIN_COUNT,
        "reported_pre_lt_upregulated_count": REPORTED_PRE_LT_UPREGULATED_COUNT,
        "clinical_group_counts": {
            HEALTHY_STATE: HEALTHY_N,
            PRE_LT_STATE: LT_PATIENT_N,
            POST_LT_DAY_1_STATE: TIMEPOINT_N,
            POST_LT_DAY_3_STATE: TIMEPOINT_N,
            POST_LT_DAY_7_STATE: TIMEPOINT_N,
        },
        "feature_symbols": sorted(protein_payload["proteins"].keys()),
        "limitations": protein_payload["limitations"],
    }


def build_provenance(generated_at: str, output_paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "parser": "scripts/ingest_sepmc6493459_lt_serum_proteomics.py",
        "source_files": {
            "article_html": {
                "url": ARTICLE_URL,
                **file_record(ARTICLE_HTML_PATH),
            }
        },
        "methods": [
            "Downloaded the Oncotarget full-text article landing page for the peri-transplant serum iTRAQ study.",
            "Curated directly visible protein rows from Table 1 (partial upregulated list) and Table 2 (retinol-metabolism subset) into a queryable published-table evidence layer.",
            "Represented the cohort as repeated-measures serum placeholders spanning healthy controls plus pre-transplant and day 1/day 3/day 7 post-transplant sampling.",
            "Computed log2 fold-change summaries from the article-reported Ratio_B_114/A_113 values for database display only.",
        ],
        "identifier_mapping_rule": "Used the UniProt accessions and gene symbols explicitly visible in the article text tables; no secondary remapping service was required.",
        "normalization_rule": "Used the article-reported iTRAQ pre-transplant versus healthy-control ratios exactly as shown; no raw-spectrum reprocessing or additional normalization was performed.",
        "outputs": {artifact: file_record(path) for artifact, path in output_paths.items()},
        "limitations": [
            "The public article text exposes only partial feature rows and does not provide a complete reusable sample-by-protein intensity matrix.",
            "Post-transplant day 1/day 3/day 7 comparisons are present at the study-design level but not as reusable feature tables in this V1 ingestion layer.",
            "This cohort is centered on HCC recipients undergoing transplantation, so the evidence should not be overstated as general rejection monitoring.",
        ],
    }


def build(force: bool = False) -> dict[str, Any]:
    ensure_dir(RAW_DIR)
    ensure_dir(PROCESSED_DIR)
    if force and ARTICLE_HTML_PATH.exists():
        ARTICLE_HTML_PATH.unlink()
    download_if_missing(ARTICLE_URL, ARTICLE_HTML_PATH)

    generated_at = datetime.now(timezone.utc).isoformat()
    samples = build_samples()
    sample_summary = build_sample_summary(samples, generated_at)
    protein_payload, contrasts = build_protein_payload(generated_at)
    summary = build_summary(generated_at, protein_payload)
    cohort_summary = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "participant_count": HEALTHY_N + LT_PATIENT_N,
        "lt_patient_count": LT_PATIENT_N,
        "sample_count": len(samples),
        "protein_feature_count": protein_payload["protein_count"],
        "reported_total_identified_protein_count": REPORTED_TOTAL_IDENTIFIED_PROTEIN_COUNT,
        "reported_pre_lt_upregulated_count": REPORTED_PRE_LT_UPREGULATED_COUNT,
        "limitations": sample_summary["limitations"],
    }
    source_inventory = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "files": [{"label": "article_html", **file_record(ARTICLE_HTML_PATH)}],
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
        "participant_count": HEALTHY_N + LT_PATIENT_N,
        "sample_count": len(samples),
        "protein_feature_count": protein_payload["protein_count"],
        "contrast_count": len(contrasts),
        "feature_symbols": sorted(protein_payload["proteins"].keys())[:10],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build S-EPMC6493459 peri-transplant serum proteomics evidence layer.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(force=args.force), indent=2))


if __name__ == "__main__":
    main()
