from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "AGING_2020_LT_SERUM_PROTEOMICS"
RAW_DIR = ROOT / "data" / "raw" / SOURCE_ID
PROCESSED_DIR = ROOT / "data" / "processed" / SOURCE_ID

ARTICLE_URL = "https://www.aging-us.com/article/103381/text"
ARTICLE_PDF_URL = "https://cdn.aging-us.com/article/103381/pdf.pdf"
SUPPLEMENTARY_SD1_URL = (
    "https://cdn.aging-us.com/article/103381/supplementary/SD1/0/"
    "aging-v12i12-103381-supplementary-material-SD1.pdf"
)
SUPPLEMENTARY_SD2_URL = (
    "https://cdn.aging-us.com/article/103381/supplementary/SD2/0/"
    "aging-v12i12-103381-supplementary-material-SD2.pdf"
)

ARTICLE_HTML_PATH = RAW_DIR / "article_text.html"
ARTICLE_PDF_PATH = RAW_DIR / "aging_2020_liver_transplant_serum_proteomics.pdf"
SD1_PATH = RAW_DIR / "aging_2020_liver_transplant_serum_proteomics_supplementary_figure.pdf"
SD2_PATH = RAW_DIR / "aging_2020_liver_transplant_serum_proteomics_supplementary_tables.pdf"

SAMPLE_GROUPS = [
    ("healthy_control", "recipient_serum", 10),
    ("stable_post_transplant", "recipient_serum", 10),
    ("pre_transplant_end_stage_liver_disease", "recipient_serum", 10),
    ("acute_rejection", "recipient_serum", 10),
    ("ischemic_type_biliary_lesion", "recipient_serum", 9),
]

PEAK_PROTEIN_MAP = {
    "1949.82": {
        "gene_symbol": "ACLY",
        "primary_uniprot": "P53396",
        "protein_name": "ATP citrate lyase",
        "peptide_sequence": "K.ILIIGGSIANFTNVAATFK.G",
    },
    "1950.06": {
        "gene_symbol": "ACLY",
        "primary_uniprot": "P53396",
        "protein_name": "ATP citrate lyase",
        "peptide_sequence": "K.ILIIGGSIANFTNVAATFK.G",
    },
    "1949.99": {
        "gene_symbol": "ACLY",
        "primary_uniprot": "P53396",
        "protein_name": "ATP citrate lyase",
        "peptide_sequence": "K.ILIIGGSIANFTNVAATFK.G",
    },
    "4100.54": {
        "gene_symbol": "APOA1",
        "primary_uniprot": "P02647",
        "protein_name": "Apolipoprotein A-I precursor",
        "peptide_sequence": "Q.DEPPQSPWDRVKDLATVYVDVLKDSGRDYVSQFEGS.A",
    },
    "2666.86": {
        "gene_symbol": "FGA",
        "primary_uniprot": "P02671",
        "protein_name": "Isoform 1 of Fibrinogen alpha chain precursor",
        "peptide_sequence": "A.DEAGSEADHEGTHSTKRGHAKSRPV.R",
    },
    "2087.90": {
        "gene_symbol": "FGA",
        "primary_uniprot": "P02671",
        "protein_name": "Isoform 1 of Fibrinogen alpha chain precursor",
        "peptide_sequence": "Y.KMADEAGSEADHEGTHSTKRGHAKSRPV.R",
    },
    "2087.92": {
        "gene_symbol": "FGA",
        "primary_uniprot": "P02671",
        "protein_name": "Isoform 1 of Fibrinogen alpha chain precursor",
        "peptide_sequence": "Y.KMADEAGSEADHEGTHSTKRGHAKSRPV.R",
    },
}

PEAK_DATA = [
    {
        "peak_id": "perioperative_peak_acly",
        "peak_mz": "1949.82",
        "context": "perioperative_effectiveness",
        "published_global_p_value": 0.000126,
        "groups": {
            "healthy_control": {"n": 10, "mean": 35.35, "sd": 10.79},
            "stable_post_transplant": {"n": 10, "mean": 18.03, "sd": 12.37},
            "pre_transplant_end_stage_liver_disease": {"n": 10, "mean": 3.16, "sd": 1.02},
        },
    },
    {
        "peak_id": "perioperative_peak_apoa1",
        "peak_mz": "4100.54",
        "context": "perioperative_effectiveness",
        "published_global_p_value": 0.000321,
        "groups": {
            "healthy_control": {"n": 10, "mean": 8.31, "sd": 2.18},
            "stable_post_transplant": {"n": 10, "mean": 5.46, "sd": 2.60},
            "pre_transplant_end_stage_liver_disease": {"n": 10, "mean": 2.05, "sd": 1.66},
        },
    },
    {
        "peak_id": "perioperative_peak_fga",
        "peak_mz": "2666.86",
        "context": "perioperative_effectiveness",
        "published_global_p_value": 0.000605,
        "groups": {
            "healthy_control": {"n": 10, "mean": 29.98, "sd": 11.64},
            "stable_post_transplant": {"n": 10, "mean": 19.38, "sd": 8.39},
            "pre_transplant_end_stage_liver_disease": {"n": 10, "mean": 11.81, "sd": 7.78},
        },
    },
    {
        "peak_id": "acute_rejection_peak_acly",
        "peak_mz": "1950.06",
        "context": "acute_rejection",
        "published_global_p_value": 0.0000219,
        "groups": {
            "healthy_control": {"n": 10, "mean": 34.55, "sd": 10.53},
            "stable_post_transplant": {"n": 10, "mean": 12.00, "sd": 4.34},
            "acute_rejection": {"n": 10, "mean": 2.64, "sd": 0.87},
        },
    },
    {
        "peak_id": "acute_rejection_peak_fga",
        "peak_mz": "2087.90",
        "context": "acute_rejection",
        "published_global_p_value": 0.000906,
        "groups": {
            "healthy_control": {"n": 10, "mean": 7.44, "sd": 2.02},
            "stable_post_transplant": {"n": 10, "mean": 4.52, "sd": 1.38},
            "acute_rejection": {"n": 10, "mean": 2.70, "sd": 1.12},
        },
    },
    {
        "peak_id": "itbl_peak_fga",
        "peak_mz": "2087.92",
        "context": "ischemic_type_biliary_lesion",
        "published_global_p_value": 0.000339,
        "groups": {
            "healthy_control": {"n": 10, "mean": 6.94, "sd": 2.08},
            "stable_post_transplant": {"n": 10, "mean": 4.16, "sd": 1.35},
            "ischemic_type_biliary_lesion": {"n": 9, "mean": 2.61, "sd": 0.75},
        },
    },
    {
        "peak_id": "itbl_peak_acly",
        "peak_mz": "1949.99",
        "context": "ischemic_type_biliary_lesion",
        "published_global_p_value": 0.000232,
        "groups": {
            "healthy_control": {"n": 10, "mean": 30.07, "sd": 12.69},
            "stable_post_transplant": {"n": 10, "mean": 11.45, "sd": 4.36},
            "ischemic_type_biliary_lesion": {"n": 9, "mean": 4.87, "sd": 2.49},
        },
    },
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def round_or_none(value: float | None, digits: int = 6) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(value, digits)


def download_if_missing(url: str, path: Path) -> None:
    if path.exists():
        return
    ensure_dir(path.parent)
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request) as response, path.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def pdf_to_text(path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def build_samples() -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for clinical_state, sample_origin, count in SAMPLE_GROUPS:
        prefix = {
            "healthy_control": "HC",
            "stable_post_transplant": "POST",
            "pre_transplant_end_stage_liver_disease": "PRE",
            "acute_rejection": "AR",
            "ischemic_type_biliary_lesion": "ITBL",
        }[clinical_state]
        for index in range(1, count + 1):
            samples.append(
                {
                    "sample_accession": f"{prefix}{index:02d}",
                    "title": f"{clinical_state.replace('_', ' ')} serum sample {index}",
                    "sample_origin": sample_origin,
                    "clinical_state": clinical_state,
                    "assay_modality": "proteomics",
                    "sample_id_origin": "synthetic_group_placeholder_from_published_counts",
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
            "Sample identifiers are synthetic placeholders generated from published group counts.",
            "No public per-sample protein intensity matrix was available; this cohort currently exposes group-level protein evidence only.",
        ],
    }


def summary_stats_to_contrast(
    feature_id: str,
    display_name: str,
    context: str,
    case_state: str,
    control_state: str,
    case_stats: dict[str, Any],
    control_stats: dict[str, Any],
) -> dict[str, Any]:
    statistic, p_value = stats.ttest_ind_from_stats(
        mean1=case_stats["mean"],
        std1=case_stats["sd"],
        nobs1=case_stats["n"],
        mean2=control_stats["mean"],
        std2=control_stats["sd"],
        nobs2=control_stats["n"],
        equal_var=False,
    )
    return {
        "contrast_id": f"{context}:{case_state}_vs_{control_state}",
        "context": context,
        "case_state": case_state,
        "control_state": control_state,
        "case_n": case_stats["n"],
        "control_n": control_stats["n"],
        "case_mean": round_or_none(case_stats["mean"]),
        "control_mean": round_or_none(control_stats["mean"]),
        "case_sd": round_or_none(case_stats["sd"]),
        "control_sd": round_or_none(control_stats["sd"]),
        "mean_difference": round_or_none(case_stats["mean"] - control_stats["mean"]),
        "effect_scale": "relative_maldi_tof_peak_intensity",
        "statistic_welch_t": round_or_none(float(statistic)),
        "p_value": round_or_none(float(p_value)),
    }


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


def build_feature_payload(generated_at: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    proteins: dict[str, dict[str, Any]] = {}
    all_contrasts: list[dict[str, Any]] = []

    for peak in PEAK_DATA:
        mapping = PEAK_PROTEIN_MAP[peak["peak_mz"]]
        symbol = mapping["gene_symbol"]
        record = proteins.setdefault(
            symbol,
            {
                "gene_symbol": symbol,
                "primary_uniprot": mapping["primary_uniprot"],
                "protein_name": mapping["protein_name"],
                "evidence_kind": "direct_transplant_protein_biomarker",
                "sample_scope": "recipient_serum_complication_monitoring",
                "summary_level": "group_level_published_means",
                "measurement_type": "maldi_tof_peak_intensity",
                "mapped_peaks": [],
                "published_group_summaries": {},
                "published_contrasts": [],
                "limitations": [
                    "Feature evidence is reconstructed from published group summaries rather than a public per-sample intensity matrix.",
                    "This serum cohort mixes transplant effectiveness, acute rejection, and ischemic-type biliary lesion contexts.",
                    "Only peptide peaks with published protein identification and quantitative summaries are exposed.",
                ],
            },
        )
        record["mapped_peaks"].append(
            {
                "peak_id": peak["peak_id"],
                "peak_mz": peak["peak_mz"],
                "context": peak["context"],
                "primary_uniprot": mapping["primary_uniprot"],
                "protein_name": mapping["protein_name"],
                "peptide_sequence": mapping["peptide_sequence"],
                "published_global_p_value": peak["published_global_p_value"],
            }
        )
        record["published_group_summaries"][peak["context"]] = {
            state: {
                "n": values["n"],
                "mean": round_or_none(values["mean"]),
                "sd": round_or_none(values["sd"]),
            }
            for state, values in peak["groups"].items()
        }

        states = list(peak["groups"].keys())
        peak_contrasts: list[dict[str, Any]] = []
        for idx, case_state in enumerate(states):
            for control_state in states[idx + 1 :]:
                contrast = summary_stats_to_contrast(
                    feature_id=symbol.lower(),
                    display_name=record["protein_name"],
                    context=peak["context"],
                    case_state=case_state,
                    control_state=control_state,
                    case_stats=peak["groups"][case_state],
                    control_stats=peak["groups"][control_state],
                )
                contrast["peak_mz"] = peak["peak_mz"]
                peak_contrasts.append(contrast)
        benjamini_hochberg(peak_contrasts)
        record["published_contrasts"].extend(peak_contrasts)
        all_contrasts.extend([{**contrast, "gene_symbol": symbol} for contrast in peak_contrasts])

    payload = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "source_url": ARTICLE_URL,
        "assay_modality": "proteomics",
        "assay_scale": "relative_maldi_tof_peak_intensity",
        "sample_scope": "recipient_serum_complication_monitoring",
        "protein_count": len(proteins),
        "proteins": proteins,
        "limitations": [
            "This source provides published serum protein biomarker evidence, not full unbiased tissue proteome quantification.",
            "Per-sample protein values were not publicly reusable; feature records therefore expose group-level summaries and derived Welch contrasts only.",
            "Stable post-transplant recipients, acute rejection, ischemic-type biliary lesion, and perioperative pre/post-transplant comparisons should be interpreted as related but distinct clinical contexts.",
        ],
    }
    return payload, all_contrasts


def build_summary(generated_at: str, protein_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "assay_modality": "proteomics",
        "sample_scope": "recipient_serum_complication_monitoring",
        "sample_count": sum(count for _, _, count in SAMPLE_GROUPS),
        "protein_feature_count": protein_payload["protein_count"],
        "mapped_peak_count": len(PEAK_DATA),
        "clinical_group_counts": {state: count for state, _, count in SAMPLE_GROUPS},
        "feature_symbols": sorted(protein_payload["proteins"].keys()),
        "limitations": protein_payload["limitations"],
    }


def build_provenance(
    generated_at: str,
    article_text: str,
    supplementary_text: str,
    output_paths: dict[str, Path],
) -> dict[str, Any]:
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "parser": "scripts/ingest_aging_2020_serum_proteomics.py",
        "source_files": {
            "article_html": {
                "url": ARTICLE_URL,
                **file_record(ARTICLE_HTML_PATH),
            },
            "article_pdf": {
                "url": ARTICLE_PDF_URL,
                **file_record(ARTICLE_PDF_PATH),
            },
            "supplementary_figure_pdf": {
                "url": SUPPLEMENTARY_SD1_URL,
                **file_record(SD1_PATH),
            },
            "supplementary_tables_pdf": {
                "url": SUPPLEMENTARY_SD2_URL,
                **file_record(SD2_PATH),
            },
        },
        "methods": [
            "Downloaded public Aging-US article text plus supplementary PDFs.",
            "Mapped serum peptide peaks to proteins using the article's Table 1 sequence-identification section and Supplementary Figure 1.",
            "Captured published group means and standard deviations for perioperative, acute rejection, and ITBL peak summaries from Supplementary Tables 2-4.",
            "Derived pairwise contrasts from published summary statistics using Welch t-tests with Benjamini-Hochberg correction within each protein feature.",
            "Generated synthetic sample placeholders from published group counts because public per-sample identifiers were not reusable.",
        ],
        "identifier_mapping_rule": "MALDI-TOF peptide peak m/z values were mapped to UniProt/gene symbols using the article's sequence-identification Table 1.",
        "normalization_rule": "Used published relative MALDI-TOF peak intensities exactly as reported; no cross-study normalization performed.",
        "source_extract_notes": {
            "article_contains_table1_sequence_mapping": "ATP citrate lyase (ACLY), fibrinogen alpha chain (FGA), and apolipoprotein A-I precursor (APOA1) are explicitly named in the full text.",
            "supplementary_tables_confirmed": "Supplementary Tables 2-4 include peak-level mean ± SD values for perioperative, AR, and ITBL contexts.",
            "article_excerpt_contains_validation_means": "Full text reports ELISA mean ± SD values for ACLY and FGA in healthy control, stable post-transplant, and AR groups.",
        },
        "text_hashes": {
            "article_text_sha256": hashlib.sha256(article_text.encode("utf-8")).hexdigest(),
            "supplementary_tables_text_sha256": hashlib.sha256(supplementary_text.encode("utf-8")).hexdigest(),
        },
        "outputs": {artifact: file_record(path) for artifact, path in output_paths.items()},
        "limitations": [
            "No public per-sample protein abundance matrix was available, so this layer is group-summary evidence rather than matrix-level proteomics.",
            "Supplementary Tables provide peptide peak intensities; proteins are inferred through the article's explicit sequence-identification table.",
            "Pairwise statistics are derived from reported means, SDs, and sample sizes and may not exactly reproduce the authors' original modeling choices.",
        ],
    }


def build(force: bool = False) -> dict[str, Any]:
    ensure_dir(RAW_DIR)
    ensure_dir(PROCESSED_DIR)
    for url, path in [
        (ARTICLE_URL, ARTICLE_HTML_PATH),
        (ARTICLE_PDF_URL, ARTICLE_PDF_PATH),
        (SUPPLEMENTARY_SD1_URL, SD1_PATH),
        (SUPPLEMENTARY_SD2_URL, SD2_PATH),
    ]:
        if force and path.exists():
            path.unlink()
        download_if_missing(url, path)

    article_text = ARTICLE_HTML_PATH.read_text(encoding="utf-8")
    supplementary_tables_text = pdf_to_text(SD2_PATH)
    generated_at = datetime.now(timezone.utc).isoformat()
    samples = build_samples()
    sample_summary = build_sample_summary(samples, generated_at)
    protein_payload, all_contrasts = build_feature_payload(generated_at)
    summary = build_summary(generated_at, protein_payload)
    cohort_summary = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "sample_count": len(samples),
        "patient_count": len(samples),
        "clinical_group_counts": {state: count for state, _, count in SAMPLE_GROUPS},
        "reported_contexts": [
            "perioperative_effectiveness",
            "acute_rejection",
            "ischemic_type_biliary_lesion",
        ],
        "protein_feature_count": protein_payload["protein_count"],
        "limitations": sample_summary["limitations"],
    }
    source_inventory = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "files": [
            {"label": "article_html", **file_record(ARTICLE_HTML_PATH)},
            {"label": "article_pdf", **file_record(ARTICLE_PDF_PATH)},
            {"label": "supplementary_figure_pdf", **file_record(SD1_PATH)},
            {"label": "supplementary_tables_pdf", **file_record(SD2_PATH)},
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
    provenance = build_provenance(generated_at, article_text, supplementary_tables_text, output_paths)
    write_json(provenance_path, provenance)
    output_paths["analysis_provenance"] = provenance_path

    return {
        "study_accession": SOURCE_ID,
        "sample_count": len(samples),
        "protein_feature_count": protein_payload["protein_count"],
        "contrast_count": len(all_contrasts),
        "feature_symbols": sorted(protein_payload["proteins"].keys()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest direct liver-transplant serum proteomics evidence from Aging 2020.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(force=args.force), indent=2))


if __name__ == "__main__":
    main()
