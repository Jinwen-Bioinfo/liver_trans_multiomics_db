from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import struct
import subprocess
import urllib.error
import zlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "PXD022881"
RAW_DIR = ROOT / "data" / "raw" / SOURCE_ID
PROCESSED_DIR = ROOT / "data" / "processed" / SOURCE_ID

PRIDE_PROJECT_URL = "https://www.ebi.ac.uk/pride/archive/projects/PXD022881"
COMBINED_ZIP_URL = "https://ftp.pride.ebi.ac.uk/pride/data/archive/2022/02/PXD022881/combined.zip"
ARTICLE_URL = "https://clinicalproteomicsjournal.biomedcentral.com/articles/10.1186/s12014-021-09333-x"
SUPPLEMENT_PDF_URL = (
    "https://static-content.springer.com/esm/art%3A10.1186%2Fs12014-021-09333-x/"
    "MediaObjects/12014_2021_9333_MOESM1_ESM.pdf"
)

DESIGN_MEMBER = "combined/experimentalDesignTemplate.txt"
SUMMARY_MEMBER = "combined/txt/summary.txt"
PARAMETERS_MEMBER = "combined/txt/parameters.txt"
PROTEIN_GROUPS_MEMBER = "combined/txt/proteinGroups.txt"

DESIGN_PATH = RAW_DIR / "experimentalDesignTemplate.txt"
SUMMARY_PATH = RAW_DIR / "summary.txt"
PARAMETERS_PATH = RAW_DIR / "parameters.txt"
PROTEIN_GROUPS_PATH = RAW_DIR / "proteinGroups.txt"
SUPPLEMENT_PDF_PATH = RAW_DIR / "supplementary_figure_s1.pdf"
SUPPLEMENT_TEXT_PATH = RAW_DIR / "supplementary_figure_s1.txt"

CASE_STATE = "subsequent_post_lt_hcc_recurrence"
CONTROL_STATE = "no_post_lt_hcc_recurrence"
CONTRAST_ID = f"{CASE_STATE}_vs_{CONTROL_STATE}"

PUBLISHED_SAMPLE_STATUS = {
    1: CASE_STATE,
    2: CASE_STATE,
    3: CONTROL_STATE,
    4: CONTROL_STATE,
    5: CASE_STATE,
    6: CASE_STATE,
    7: CASE_STATE,
    9: CASE_STATE,
    10: CONTROL_STATE,
    11: CONTROL_STATE,
    12: CASE_STATE,
}
UNLABELED_DESIGN_SAMPLES = {8}


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
    return round(value, digits)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path, label: str) -> dict[str, Any]:
    return {
        "label": label,
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def download_if_missing(url: str, path: Path) -> None:
    if path.exists():
        return
    ensure_dir(path.parent)
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request) as response, path.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def http_range(url: str, start: int, end_inclusive: int) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Range": f"bytes={start}-{end_inclusive}",
        },
    )
    with urlopen(request) as response:
        return response.read()


def remote_size(url: str) -> int:
    request = Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request) as response:
        return int(response.headers["Content-Length"])


def zip64_members(url: str) -> dict[str, dict[str, Any]]:
    size = remote_size(url)
    tail_span = min(size, 512000)
    tail_start = size - tail_span
    tail = http_range(url, tail_start, size - 1)

    locator_offset = tail.rfind(b"PK\x06\x07")
    if locator_offset == -1:
        raise ValueError("Zip64 locator not found in combined.zip tail.")

    zip64_eocd_offset = struct.unpack_from("<Q", tail, locator_offset + 8)[0]
    zip64_record = http_range(url, zip64_eocd_offset, min(size - 1, zip64_eocd_offset + 2047))
    if not zip64_record.startswith(b"PK\x06\x06"):
        raise ValueError("Zip64 EOCD not found at advertised offset.")

    fields = struct.unpack_from("<4sQ2H2I4Q", zip64_record, 0)
    central_directory_size = fields[-2]
    central_directory_offset = fields[-1]
    central_directory = http_range(
        url,
        central_directory_offset,
        central_directory_offset + central_directory_size - 1,
    )

    members: dict[str, dict[str, Any]] = {}
    pointer = 0
    while pointer < len(central_directory) and central_directory[pointer : pointer + 4] == b"PK\x01\x02":
        header = struct.unpack_from("<4s6H3I5H2I", central_directory, pointer)
        compression_method = header[4]
        compressed_size_32 = header[8]
        uncompressed_size_32 = header[9]
        name_length = header[10]
        extra_length = header[11]
        comment_length = header[12]
        local_header_offset_32 = header[16]

        name_start = pointer + 46
        name_end = name_start + name_length
        extra_end = name_end + extra_length
        comment_end = extra_end + comment_length
        name = central_directory[name_start:name_end].decode("utf-8", "replace")
        extra = central_directory[name_end:extra_end]

        compressed_size = compressed_size_32
        uncompressed_size = uncompressed_size_32
        local_header_offset = local_header_offset_32
        extra_pointer = 0
        while extra_pointer + 4 <= len(extra):
            header_id, payload_size = struct.unpack_from("<HH", extra, extra_pointer)
            payload = extra[extra_pointer + 4 : extra_pointer + 4 + payload_size]
            if header_id == 0x0001:
                values = [struct.unpack_from("<Q", payload, idx)[0] for idx in range(0, len(payload), 8) if idx + 8 <= len(payload)]
                value_index = 0
                if uncompressed_size_32 == 0xFFFFFFFF:
                    uncompressed_size = values[value_index]
                    value_index += 1
                if compressed_size_32 == 0xFFFFFFFF:
                    compressed_size = values[value_index]
                    value_index += 1
                if local_header_offset_32 == 0xFFFFFFFF:
                    local_header_offset = values[value_index]
            extra_pointer += 4 + payload_size

        members[name] = {
            "compression_method": compression_method,
            "compressed_size": compressed_size,
            "uncompressed_size": uncompressed_size,
            "local_header_offset": local_header_offset,
        }
        pointer = comment_end
    return members


def extract_zip_member(url: str, member_name: str, destination: Path, members: dict[str, dict[str, Any]]) -> None:
    if destination.exists():
        return
    info = members[member_name]
    local_header_offset = info["local_header_offset"]
    compressed_size = info["compressed_size"]
    header_block = http_range(url, local_header_offset, local_header_offset + 30 + 4096 + compressed_size + 512)
    if header_block[:4] != b"PK\x03\x04":
        raise ValueError(f"Local header missing for {member_name}.")

    _, _, _, compression_method, _, _, _, _, _, name_length, extra_length = struct.unpack_from(
        "<4s5H3I2H", header_block, 0
    )
    data_start = 30 + name_length + extra_length
    compressed_payload = header_block[data_start : data_start + compressed_size]
    if len(compressed_payload) < compressed_size:
        raise ValueError(f"Truncated remote payload for {member_name}.")

    if compression_method == 0:
        raw = compressed_payload
    elif compression_method == 8:
        raw = zlib.decompress(compressed_payload, -15)
    else:
        raise ValueError(f"Unsupported compression method {compression_method} for {member_name}.")

    ensure_dir(destination.parent)
    destination.write_bytes(raw)


def pdf_to_text(pdf_path: Path, text_path: Path) -> None:
    if text_path.exists():
        return
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    text_path.write_text(result.stdout, encoding="utf-8")


def sample_accession(sample_number: int) -> str:
    return f"HCC_LiverTissue_Sample{sample_number}"


def sample_title(sample_number: int) -> str:
    return f"HCC tumor explant proteomics sample {sample_number}"


def parse_design() -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    with DESIGN_PATH.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            name = row["Name"]
            experiment = int(row["Experiment"])
            if "_Fraction" not in name:
                continue
            sample_label, fraction_label = name.split("_Fraction", 1)
            fraction = int(fraction_label)
            rows.setdefault(
                experiment,
                {
                    "sample_accession": sample_label,
                    "experiment_id": experiment,
                    "fractions": [],
                },
            )["fractions"].append(fraction)
    if not rows:
        raise ValueError("No sample rows parsed from experimentalDesignTemplate.txt.")
    return rows


def sample_records(design: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for experiment_id in sorted(design):
        clinical_state = PUBLISHED_SAMPLE_STATUS.get(experiment_id)
        records.append(
            {
                "sample_accession": design[experiment_id]["sample_accession"],
                "title": sample_title(experiment_id),
                "sample_origin": "recipient_liver_explant_tumor",
                "biospecimen": "hcc_tumor_explant_at_liver_transplant",
                "clinical_state": clinical_state,
                "clinical_state_raw": clinical_state,
                "assay_modality": "proteomics",
                "collection_timepoint": "transplant_explant",
                "published_analysis_subset_included": experiment_id in PUBLISHED_SAMPLE_STATUS,
                "source_table": "experimentalDesignTemplate.txt + Supplementary Figure S1 PCA labels",
                "metadata_annotations": {
                    "experiment_id": experiment_id,
                    "fraction_count": len(design[experiment_id]["fractions"]),
                    "fractions": sorted(design[experiment_id]["fractions"]),
                    "label_recovery_rule": (
                        "Supplementary Figure S1 panel C labels recurrent samples in red and non-recurrent samples in blue."
                    ),
                    "published_analysis_subset_included": experiment_id in PUBLISHED_SAMPLE_STATUS,
                    "excluded_or_unlabeled_reason": (
                        "Present in PRIDE experimental design and LFQ matrix, but absent from the published 11-sample PCA-labeled subset."
                        if experiment_id in UNLABELED_DESIGN_SAMPLES
                        else None
                    ),
                },
            }
        )
    return records


def summary_stats(values: list[float]) -> dict[str, Any]:
    ordered = sorted(values)
    mean = sum(values) / len(values)
    if len(ordered) % 2:
        median = ordered[len(ordered) // 2]
    else:
        midpoint = len(ordered) // 2
        median = (ordered[midpoint - 1] + ordered[midpoint]) / 2
    if len(values) > 1:
        variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
        sd = math.sqrt(variance)
    else:
        sd = 0.0
    return {
        "n": len(values),
        "mean": round_or_none(mean),
        "median": round_or_none(median),
        "sd": round_or_none(sd),
        "min": round_or_none(min(values)),
        "max": round_or_none(max(values)),
    }


def parse_protein_groups() -> list[dict[str, Any]]:
    sample_columns = {sample_number: f"LFQ intensity {sample_number}" for sample_number in range(1, 13)}
    rows: list[dict[str, Any]] = []
    with PROTEIN_GROUPS_PATH.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if row.get("Only identified by site") == "+":
                continue
            if row.get("Reverse") == "+":
                continue
            if row.get("Potential contaminant") == "+":
                continue

            gene_names = [item.strip() for item in row.get("Gene names", "").split(";") if item.strip()]
            if not gene_names:
                continue

            log2_values: dict[int, float] = {}
            for sample_number, column in sample_columns.items():
                raw = row.get(column, "").strip()
                if raw in {"", "0"}:
                    continue
                value = float(raw)
                if value <= 0:
                    continue
                log2_values[sample_number] = math.log2(value)

            if not log2_values:
                continue

            recurrent_values = [log2_values[idx] for idx in sorted(PUBLISHED_SAMPLE_STATUS) if PUBLISHED_SAMPLE_STATUS[idx] == CASE_STATE and idx in log2_values]
            non_recurrent_values = [log2_values[idx] for idx in sorted(PUBLISHED_SAMPLE_STATUS) if PUBLISHED_SAMPLE_STATUS[idx] == CONTROL_STATE and idx in log2_values]

            p_value = None
            mean_difference = None
            if len(recurrent_values) >= 2 and len(non_recurrent_values) >= 2:
                test = stats.ttest_ind(recurrent_values, non_recurrent_values, equal_var=False)
                p_value = float(test.pvalue)
                mean_difference = (sum(recurrent_values) / len(recurrent_values)) - (
                    sum(non_recurrent_values) / len(non_recurrent_values)
                )

            rows.append(
                {
                    "protein_group_id": row["Protein IDs"],
                    "primary_uniprot": row["Majority protein IDs"].split(";")[0].strip(),
                    "protein_accessions": [item.strip() for item in row["Protein IDs"].split(";") if item.strip()],
                    "majority_protein_ids": [item.strip() for item in row["Majority protein IDs"].split(";") if item.strip()],
                    "protein_name": row["Protein names"].split(";")[0].strip() if row["Protein names"].strip() else row["Majority protein IDs"].split(";")[0].strip(),
                    "gene_names": gene_names,
                    "sample_log2_lfq": log2_values,
                    "detected_sample_count": len(log2_values),
                    "all_samples": summary_stats(list(log2_values.values())),
                    "group_summaries": {
                        CASE_STATE: summary_stats(recurrent_values) if recurrent_values else None,
                        CONTROL_STATE: summary_stats(non_recurrent_values) if non_recurrent_values else None,
                    },
                    "p_value": p_value,
                    "mean_difference": mean_difference,
                }
            )
    if not rows:
        raise ValueError("No usable protein-group rows parsed from proteinGroups.txt.")
    return rows


def benjamini_hochberg(rows: list[dict[str, Any]]) -> None:
    indexed = [(index, row["p_value"]) for index, row in enumerate(rows) if row.get("p_value") is not None]
    indexed.sort(key=lambda item: item[1])
    adjusted: list[float | None] = [None] * len(rows)
    running = 1.0
    total = len(indexed)
    for rank, (index, p_value) in reversed(list(enumerate(indexed, start=1))):
        candidate = min(running, p_value * total / rank)
        running = candidate
        adjusted[index] = candidate
    for index, value in enumerate(adjusted):
        rows[index]["adj_p_value_bh"] = round_or_none(value)


def build_protein_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    gene_to_best: dict[str, dict[str, Any]] = {}
    for row in rows:
        for gene in row["gene_names"]:
            current = gene_to_best.get(gene)
            current_score = (
                current.get("adj_p_value_bh") if current and current.get("adj_p_value_bh") is not None else 999.0,
                -(current.get("detected_sample_count", 0) if current else 0),
            )
            row_score = (
                row.get("adj_p_value_bh") if row.get("adj_p_value_bh") is not None else 999.0,
                -row.get("detected_sample_count", 0),
            )
            if current is None or row_score < current_score:
                gene_to_best[gene] = row

    proteins: dict[str, Any] = {}
    for gene_symbol, row in sorted(gene_to_best.items()):
        proteins[gene_symbol] = {
            "protein_group_id": row["protein_group_id"],
            "primary_uniprot": row["primary_uniprot"],
            "protein_accessions": row["protein_accessions"],
            "majority_protein_ids": row["majority_protein_ids"],
            "protein_name": row["protein_name"],
            "gene_symbol": gene_symbol,
            "gene_aliases": row["gene_names"],
            "evidence_kind": "direct_transplant_protein_biomarker",
            "measurement_type": "maxquant_lfq_intensity_log2",
            "sample_scope": "hcc_tumor_explant_recurrence_discovery_subset",
            "summary_level": "sample_level_pride_lfq_with_published_subset_labels",
            "sample_count": 12,
            "detected_sample_count": row["detected_sample_count"],
            "reported_group_counts": {
                CASE_STATE: {"n": 7},
                CONTROL_STATE: {"n": 4},
                "unlabeled_public_design_sample": {"n": 1},
            },
            "all_samples": row["all_samples"],
            "group_summaries": {
                state: summary
                for state, summary in row["group_summaries"].items()
                if summary is not None
            },
            "published_contrasts": [
                {
                    "contrast_id": CONTRAST_ID,
                    "context": "post_transplant_hcc_recurrence_risk",
                    "case_state": CASE_STATE,
                    "control_state": CONTROL_STATE,
                    "case_n": row["group_summaries"][CASE_STATE]["n"] if row["group_summaries"][CASE_STATE] else 0,
                    "control_n": row["group_summaries"][CONTROL_STATE]["n"] if row["group_summaries"][CONTROL_STATE] else 0,
                    "effect_scale": "log2_lfq_intensity",
                    "mean_difference": round_or_none(row["mean_difference"]),
                    "p_value": round_or_none(row["p_value"]),
                    "adj_p_value_bh": row.get("adj_p_value_bh"),
                    "direction": (
                        "higher_in_subsequent_post_lt_hcc_recurrence"
                        if row.get("mean_difference") is not None and row["mean_difference"] > 0
                        else "lower_in_subsequent_post_lt_hcc_recurrence"
                        if row.get("mean_difference") is not None
                        else "undetermined"
                    ),
                    "subset_only": True,
                    "selection_rule": (
                        "Only the 11 published discovery-set samples with explicit Figure S1 recurrence labels are included; Sample 8 remains unlabeled."
                    ),
                }
            ],
            "reported_annotations": {
                "raw_design_sample_count": 12,
                "published_analysis_subset_sample_count": 11,
                "published_case_n": 7,
                "published_control_n": 4,
                "unlabeled_design_samples": [sample_accession(item) for item in sorted(UNLABELED_DESIGN_SAMPLES)],
                "label_recovery_basis": (
                    "Supplementary Figure S1 panel C labels recurrent samples in red and non-recurrent samples in blue; article abstract and methods report 7 recurrent versus 4 non-recurrent tumor explants."
                ),
            },
            "limitations": [
                "Recurrence labels are recoverable for 11 published discovery-set samples via Supplementary Figure S1 panel C, but one PRIDE design sample (Sample 8) is unlabeled and excluded from contrasts.",
                "This layer uses observed MaxQuant LFQ values without the article's internal imputation workflow, so effect sizes and adjusted p-values should be treated as database-level exploratory evidence rather than a formal re-analysis of the publication.",
                "The biological question is post-transplant HCC recurrence risk from tumor-explant proteomics beyond Milan criteria, not biopsy-proven rejection or non-invasive blood monitoring.",
            ],
        }
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "assay_scale": "protein_group_lfq_matrix",
        "sample_scope": "hcc_tumor_explant_recurrence_discovery_subset",
        "limitations": [
            "One design sample is publicly present but not labeled in the published recurrence-vs-non-recurrence subset.",
            "Feature statistics are derived from the labeled 11-sample subset only.",
        ],
        "proteins": proteins,
    }


def build_sample_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    state_counts = Counter(sample["clinical_state"] for sample in samples if sample["clinical_state"])
    return {
        "sample_count": len(samples),
        "published_analysis_subset_sample_count": sum(1 for sample in samples if sample["published_analysis_subset_included"]),
        "unlabeled_design_sample_count": sum(1 for sample in samples if not sample["published_analysis_subset_included"]),
        "by_clinical_state": dict(state_counts),
        "fraction_count_per_sample": sorted(
            {sample["metadata_annotations"]["fraction_count"] for sample in samples}
        ),
    }


def build_cohort_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sample_count": len(samples),
        "published_analysis_subset_sample_count": sum(1 for sample in samples if sample["published_analysis_subset_included"]),
        "published_case_n": sum(1 for sample in samples if sample["clinical_state"] == CASE_STATE),
        "published_control_n": sum(1 for sample in samples if sample["clinical_state"] == CONTROL_STATE),
        "unlabeled_design_samples": [
            sample["sample_accession"] for sample in samples if not sample["published_analysis_subset_included"]
        ],
    }


def build_proteomics_summary(rows: list[dict[str, Any]], proteins: dict[str, Any]) -> dict[str, Any]:
    contrast_ready = sum(1 for row in rows if row.get("p_value") is not None)
    return {
        "sample_count": 12,
        "published_analysis_subset_sample_count": 11,
        "unlabeled_design_sample_count": 1,
        "protein_group_count": len(rows),
        "queryable_gene_feature_count": len(proteins["proteins"]),
        "contrast_ready_protein_group_count": contrast_ready,
        "clinical_states": [CASE_STATE, CONTROL_STATE],
        "effect_scale": "log2_lfq_intensity",
        "contrast_id": CONTRAST_ID,
    }


def build_provenance(members: dict[str, dict[str, Any]]) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "generated_at_utc": generated_at,
        "study_accession": SOURCE_ID,
        "article_url": ARTICLE_URL,
        "repository_url": PRIDE_PROJECT_URL,
        "source_urls": {
            "combined_zip": COMBINED_ZIP_URL,
            "supplementary_figure_s1_pdf": SUPPLEMENT_PDF_URL,
        },
        "processing_script": str(Path(__file__).relative_to(ROOT)),
        "normalization_method": "Observed MaxQuant LFQ intensities transformed as log2(LFQ intensity) for detected values only.",
        "identifier_mapping_rule": "Gene-level features use the representative protein-group row with the best adjusted recurrence contrast p-value, falling back to higher detected-sample coverage when needed.",
        "label_recovery_rule": "Supplementary Figure S1 panel C red labels map to recurrent cases and blue labels map to non-recurrent cases; this recovers 11 published discovery-set samples and leaves Sample 8 unlabeled.",
        "input_members": {
            DESIGN_MEMBER: members[DESIGN_MEMBER],
            SUMMARY_MEMBER: members[SUMMARY_MEMBER],
            PARAMETERS_MEMBER: members[PARAMETERS_MEMBER],
            PROTEIN_GROUPS_MEMBER: members[PROTEIN_GROUPS_MEMBER],
        },
        "local_files": [
            file_record(DESIGN_PATH, "experimental_design_template"),
            file_record(SUMMARY_PATH, "maxquant_summary"),
            file_record(PARAMETERS_PATH, "maxquant_parameters"),
            file_record(PROTEIN_GROUPS_PATH, "protein_groups"),
            file_record(SUPPLEMENT_PDF_PATH, "supplementary_figure_s1_pdf"),
            file_record(SUPPLEMENT_TEXT_PATH, "supplementary_figure_s1_text"),
        ],
        "limitations": [
            "The direct PRIDE design exposes 12 samples, but only 11 have published recurrence labels recoverable from Supplementary Figure S1.",
            "This layer does not attempt to recreate the article's Perseus imputation pipeline and therefore should not be represented as a full publication-grade differential reanalysis.",
            "The cohort is restricted to HCC beyond Milan criteria and should be interpreted as tumor-explant recurrence-risk biology rather than general liver-transplant rejection biology.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PXD022881 HCC recurrence proteomics evidence.")
    parser.add_argument("--skip-download", action="store_true", help="Reuse any local raw files already present.")
    args = parser.parse_args()

    ensure_dir(RAW_DIR)
    if not args.skip_download:
        members = zip64_members(COMBINED_ZIP_URL)
        extract_zip_member(COMBINED_ZIP_URL, DESIGN_MEMBER, DESIGN_PATH, members)
        extract_zip_member(COMBINED_ZIP_URL, SUMMARY_MEMBER, SUMMARY_PATH, members)
        extract_zip_member(COMBINED_ZIP_URL, PARAMETERS_MEMBER, PARAMETERS_PATH, members)
        extract_zip_member(COMBINED_ZIP_URL, PROTEIN_GROUPS_MEMBER, PROTEIN_GROUPS_PATH, members)
        download_if_missing(SUPPLEMENT_PDF_URL, SUPPLEMENT_PDF_PATH)
    else:
        members = zip64_members(COMBINED_ZIP_URL)

    if not DESIGN_PATH.exists() or not PROTEIN_GROUPS_PATH.exists():
        raise FileNotFoundError("Required raw files are missing. Run without --skip-download first.")

    if not SUPPLEMENT_PDF_PATH.exists():
        download_if_missing(SUPPLEMENT_PDF_URL, SUPPLEMENT_PDF_PATH)
    pdf_to_text(SUPPLEMENT_PDF_PATH, SUPPLEMENT_TEXT_PATH)

    design = parse_design()
    samples = sample_records(design)
    rows = parse_protein_groups()
    benjamini_hochberg(rows)
    proteins = build_protein_payload(rows)

    ensure_dir(PROCESSED_DIR)
    write_json(PROCESSED_DIR / "samples.json", {"study_accession": SOURCE_ID, "samples": samples})
    write_json(PROCESSED_DIR / "sample_summary.json", build_sample_summary(samples))
    write_json(PROCESSED_DIR / "cohort_summary.json", build_cohort_summary(samples))
    write_json(PROCESSED_DIR / "proteomics_summary.json", build_proteomics_summary(rows, proteins))
    write_json(PROCESSED_DIR / "protein_features.json", proteins)
    write_json(
        PROCESSED_DIR / "source_file_inventory.json",
        {
            "study_accession": SOURCE_ID,
            "raw_files": [
                file_record(DESIGN_PATH, "experimental_design_template"),
                file_record(SUMMARY_PATH, "maxquant_summary"),
                file_record(PARAMETERS_PATH, "maxquant_parameters"),
                file_record(PROTEIN_GROUPS_PATH, "protein_groups"),
                file_record(SUPPLEMENT_PDF_PATH, "supplementary_figure_s1_pdf"),
                file_record(SUPPLEMENT_TEXT_PATH, "supplementary_figure_s1_text"),
            ],
        },
    )
    write_json(PROCESSED_DIR / "analysis_provenance.json", build_provenance(members))


if __name__ == "__main__":
    main()
