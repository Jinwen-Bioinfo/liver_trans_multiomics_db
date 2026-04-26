from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "PXD046355"
RAW_DIR = ROOT / "data" / "raw" / SOURCE_ID
PROCESSED_DIR = ROOT / "data" / "processed" / SOURCE_ID

PRIDE_REPORT_URL = "https://ftp.pride.ebi.ac.uk/pride/data/archive/2023/11/PXD046355/NMP_Bile_Proteomics_Report.txt"
SOURCE_DATA_URL = (
    "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-023-43368-y/"
    "MediaObjects/41467_2023_43368_MOESM4_ESM.xlsx"
)
SUPPLEMENT_PDF_URL = (
    "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-023-43368-y/"
    "MediaObjects/41467_2023_43368_MOESM1_ESM.pdf"
)
ARTICLE_URL = "https://www.nature.com/articles/s41467-023-43368-y"

REPORT_PATH = RAW_DIR / "NMP_Bile_Proteomics_Report.txt"
SOURCE_DATA_PATH = RAW_DIR / "source_data.xlsx"
SUPPLEMENT_PDF_PATH = RAW_DIR / "supplementary_information.pdf"
SUPPLEMENT_TEXT_PATH = RAW_DIR / "supplementary_information.txt"

HIGH_STATE = "high_biliary_viability_donor_liver"
LOW_STATE = "low_biliary_viability_donor_liver"
STATE_MAP = {"High": HIGH_STATE, "Low": LOW_STATE}
CONTRAST_TIMEPOINTS = ("30min", "150min")

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


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


def pdf_to_text(pdf_path: Path, text_path: Path) -> None:
    if text_path.exists():
        return
    import subprocess

    result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    text_path.write_text(result.stdout, encoding="utf-8")


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(t.text or "" for t in node.iter(f"{{{NS['main']}}}t"))
        for node in root
    ]


def _sheet_target_map(archive: zipfile.ZipFile) -> dict[str, str]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
    target_map: dict[str, str] = {}
    for sheet in workbook.find("main:sheets", NS):
        name = sheet.attrib["name"]
        rel_id = sheet.attrib[f"{{{NS['rel']}}}id"]
        target_map[name] = f"xl/{rel_map[rel_id]}"
    return target_map


def read_sheet_rows(path: Path, sheet_name: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        strings = _shared_strings(archive)
        target = _sheet_target_map(archive)[sheet_name]
        root = ET.fromstring(archive.read(target))
        rows: list[dict[str, str]] = []
        for row in root.findall(".//main:sheetData/main:row", NS):
            values: dict[str, str] = {}
            for cell in row.findall("main:c", NS):
                ref = "".join(ch for ch in cell.attrib.get("r", "") if ch.isalpha())
                value_node = cell.find("main:v", NS)
                if value_node is None:
                    continue
                raw = value_node.text or ""
                values[ref] = strings[int(raw)] if cell.attrib.get("t") == "s" else raw
            if values:
                rows.append(values)
        return rows


def normalize_sheet_table(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    header_row: dict[str, str] | None = None
    for row in rows:
        values = set(row.values())
        if "Sample" in values or "Liver number" in values:
            header_row = row
            break
    if header_row is None:
        raise ValueError("Could not identify header row in source data sheet.")

    column_map = {column: label for column, label in header_row.items() if label}
    normalized: list[dict[str, str]] = []
    started = False
    for row in rows:
        if row is header_row:
            started = True
            continue
        if not started:
            continue
        record = {column_map[column]: value for column, value in row.items() if column in column_map}
        if any(value not in ("", None) for value in record.values()):
            normalized.append(record)
    return normalized


def parse_liver_metadata() -> dict[str, dict[str, Any]]:
    rows = read_sheet_rows(SOURCE_DATA_PATH, "Figure 2e")
    metadata: dict[str, dict[str, Any]] = {}
    last_bdi_score: str | None = None
    last_bdi_group: str | None = None

    for row in rows:
        liver_number = row.get("B")
        if liver_number in {None, "Figure 2e", "Liver number"}:
            continue
        explicit_bdi_score = row.get("C")
        explicit_bdi_group = row.get("D")
        viability_group = row.get("E")
        if explicit_bdi_score:
            last_bdi_score = explicit_bdi_score
        if explicit_bdi_group:
            last_bdi_group = explicit_bdi_group
        metadata[liver_number] = {
            "liver_number": liver_number,
            "biliary_viability_score_group_raw": viability_group,
            "clinical_state": STATE_MAP.get(viability_group, viability_group),
            "total_bdi_score": explicit_bdi_score or last_bdi_score,
            "total_bdi_score_group": explicit_bdi_group or last_bdi_group,
            "bdi_group_recovered_from_merged_cell_layout": explicit_bdi_group is None,
        }
    return metadata


def parse_sample_metadata(liver_metadata: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = normalize_sheet_table(read_sheet_rows(SOURCE_DATA_PATH, "Figure 3a"))
    samples: list[dict[str, Any]] = []
    for row in rows:
        liver_number = row["Liver number"]
        liver_meta = liver_metadata[liver_number]
        timepoint = row["Timepoint"]
        sample_id = row["Sample"]
        samples.append(
            {
                "sample_accession": sample_id,
                "title": f"NMP donor bile proteomics {sample_id}",
                "sample_origin": "donor_liver",
                "biospecimen": "bile_during_normothermic_machine_perfusion",
                "clinical_state": liver_meta["clinical_state"],
                "clinical_state_raw": liver_meta["biliary_viability_score_group_raw"],
                "assay_modality": "proteomics",
                "collection_timepoint": timepoint,
                "donor_liver_number": liver_number,
                "source_table": "Figure 3a metadata + Figure 2e viability labels",
                "metadata_annotations": {
                    "biliary_viability_score_group": liver_meta["biliary_viability_score_group_raw"],
                    "total_bdi_score": liver_meta["total_bdi_score"],
                    "total_bdi_score_group": liver_meta["total_bdi_score_group"],
                    "bdi_group_recovered_from_merged_cell_layout": liver_meta[
                        "bdi_group_recovered_from_merged_cell_layout"
                    ],
                },
            }
        )
    return samples


def numeric_summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    median = ordered[midpoint] if len(ordered) % 2 else (ordered[midpoint - 1] + ordered[midpoint]) / 2
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / max(len(values) - 1, 1)
    return {
        "n": len(values),
        "mean": round_or_none(mean),
        "median": round_or_none(median),
        "min": round_or_none(min(values)),
        "max": round_or_none(max(values)),
        "sd": round_or_none(math.sqrt(variance)),
    }


def benjamini_hochberg(rows: list[dict[str, Any]], p_key: str = "p_value") -> None:
    indexed = [(index, row.get(p_key)) for index, row in enumerate(rows) if row.get(p_key) is not None]
    indexed.sort(key=lambda item: item[1])
    total = len(indexed)
    adjusted = [None] * len(rows)
    running = 1.0
    for rank, (index, p_value) in reversed(list(enumerate(indexed, start=1))):
        candidate = min(running, p_value * total / rank)
        running = candidate
        adjusted[index] = round_or_none(candidate)
    for index, row in enumerate(rows):
        row["adj_p_value_bh"] = adjusted[index]


def parse_report_matrix(samples: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    sample_lookup = {sample["sample_accession"]: sample for sample in samples}
    contrast_rows: dict[str, list[dict[str, Any]]] = {
        f"{HIGH_STATE}_vs_{LOW_STATE}_at_{timepoint}": [] for timepoint in CONTRAST_TIMEPOINTS
    }
    proteins: dict[str, dict[str, Any]] = {}
    protein_group_count = 0
    sample_ids_from_report: list[str] = []

    with REPORT_PATH.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        quantity_columns = [field for field in reader.fieldnames or [] if field.endswith(".PG.Quantity")]
        sample_ids_from_report = [
            column.split("] ", 1)[1].replace(".raw.PG.Quantity", "") for column in quantity_columns
        ]

        for row in reader:
            protein_group_count += 1
            gene_field = (row.get("PG.Genes") or "").strip()
            if not gene_field:
                continue
            accession_field = (row.get("PG.ProteinAccessions") or row.get("PG.ProteinGroups") or "").strip()
            primary_uniprot = accession_field.split(";")[0] if accession_field else None
            gene_symbols = [token.strip() for token in gene_field.split(";") if token.strip()]

            sample_values: list[dict[str, Any]] = []
            per_timepoint: dict[str, dict[str, list[float]]] = {
                timepoint: {HIGH_STATE: [], LOW_STATE: []} for timepoint in CONTRAST_TIMEPOINTS
            }
            all_log2_values: list[float] = []
            detected_sample_count = 0

            for column, sample_id in zip(quantity_columns, sample_ids_from_report, strict=True):
                value_text = row.get(column)
                if value_text in {None, "", "NA", "NaN", "null"}:
                    continue
                try:
                    raw_value = float(value_text)
                except ValueError:
                    continue
                log2_value = math.log2(raw_value + 1.0)
                sample_meta = sample_lookup.get(sample_id)
                if sample_meta is None:
                    continue
                detected_sample_count += 1
                all_log2_values.append(log2_value)
                sample_values.append(
                    {
                        "sample_accession": sample_id,
                        "collection_timepoint": sample_meta["collection_timepoint"],
                        "clinical_state": sample_meta["clinical_state"],
                        "log2_pg_quantity": round_or_none(log2_value),
                    }
                )
                timepoint = sample_meta["collection_timepoint"]
                state = sample_meta["clinical_state"]
                if timepoint in per_timepoint and state in per_timepoint[timepoint]:
                    per_timepoint[timepoint][state].append(log2_value)

            if not detected_sample_count:
                continue

            base_feature = {
                "evidence_kind": "direct_transplant_protein_biomarker",
                "gene_symbol": gene_symbols[0],
                "gene_aliases": gene_symbols,
                "primary_uniprot": primary_uniprot,
                "protein_group_id": row.get("PG.ProteinGroups"),
                "protein_accessions": accession_field.split(";") if accession_field else [],
                "protein_name": f"{gene_symbols[0]} protein group",
                "measurement_type": "pride_search_engine_pg_quantity",
                "summary_level": "sample_level_matrix_summary",
                "sample_scope": "donor_bile_nmp_viability_timecourse",
                "sample_count": len(samples),
                "detected_sample_count": detected_sample_count,
                "all_samples": numeric_summary(all_log2_values),
                "group_summaries": {},
                "published_contrasts": [],
                "limitations": [
                    "This layer uses the PRIDE search-engine protein-group quantity report as the quantitative matrix and Nature source-data sheets for sample metadata recovery.",
                    "Biliary-viability labels are recovered at the donor-liver level from Figure 2e and joined onto bile samples by liver number; they should be interpreted as donor-organ viability context rather than post-transplant recipient outcome.",
                    "Total BDI score/group metadata are partially inferred from merged-cell supplementary layout and are retained as descriptive annotations rather than the primary contrast definition.",
                ],
                "reported_annotations": {
                    "timepoints_observed": sorted({item["collection_timepoint"] for item in samples}),
                    "reported_gene_symbols": gene_symbols,
                    "reported_sample_value_count": detected_sample_count,
                },
                "reported_group_counts": {
                    HIGH_STATE: {"n": sum(1 for sample in samples if sample["clinical_state"] == HIGH_STATE)},
                    LOW_STATE: {"n": sum(1 for sample in samples if sample["clinical_state"] == LOW_STATE)},
                },
            }

            for timepoint in CONTRAST_TIMEPOINTS:
                case_values = per_timepoint[timepoint][HIGH_STATE]
                control_values = per_timepoint[timepoint][LOW_STATE]
                base_feature["group_summaries"][timepoint] = {
                    HIGH_STATE: numeric_summary(case_values),
                    LOW_STATE: numeric_summary(control_values),
                }
                contrast_id = f"{HIGH_STATE}_vs_{LOW_STATE}_at_{timepoint}"
                contrast = {
                    "contrast_id": contrast_id,
                    "context": f"donor_bile_nmp_{timepoint}",
                    "case_state": HIGH_STATE,
                    "control_state": LOW_STATE,
                    "case_n": len(case_values),
                    "control_n": len(control_values),
                    "effect_scale": "log2_pg_quantity",
                    "mean_difference": None,
                    "p_value": None,
                }
                if len(case_values) >= 2 and len(control_values) >= 2:
                    contrast["mean_difference"] = round_or_none(
                        (sum(case_values) / len(case_values)) - (sum(control_values) / len(control_values))
                    )
                    test = stats.ttest_ind(case_values, control_values, equal_var=False, nan_policy="omit")
                    contrast["p_value"] = round_or_none(float(test.pvalue))
                base_feature["published_contrasts"].append(contrast)
                contrast_rows[contrast_id].append(
                    {
                        "gene_symbol": gene_symbols[0],
                        "primary_uniprot": primary_uniprot,
                        "p_value": contrast["p_value"],
                    }
                )

            for gene_symbol in gene_symbols:
                proteins[gene_symbol] = {
                    **base_feature,
                    "gene_symbol": gene_symbol,
                }

    for contrast_id, rows in contrast_rows.items():
        benjamini_hochberg(rows)
        adjusted_by_gene = {row["gene_symbol"]: row["adj_p_value_bh"] for row in rows}
        for feature in proteins.values():
            for contrast in feature["published_contrasts"]:
                if contrast["contrast_id"] == contrast_id:
                    contrast["adj_p_value_bh"] = adjusted_by_gene.get(feature["gene_symbol"])

    summary = {
        "source_id": SOURCE_ID,
        "assay_modality": "proteomics",
        "assay_scale": "log2_pg_quantity",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sample_origin": "donor_liver",
        "sample_scope": "donor_bile_nmp_viability_timecourse",
        "sample_count": len(samples),
        "donor_liver_count": len({sample["donor_liver_number"] for sample in samples}),
        "protein_group_count": protein_group_count,
        "gene_query_count": len(proteins),
        "clinical_group_counts": dict(sorted(Counter(sample["clinical_state"] for sample in samples).items())),
        "timepoint_counts": dict(sorted(Counter(sample["collection_timepoint"] for sample in samples).items())),
        "contrast_ids": sorted(contrast_rows),
        "limitations": [
            "Low-biliary-viability end-of-perfusion samples are sparse (n=2), so V1 only exposes 30min and 150min viability contrasts.",
            "Sample-level transplantability annotations are only recoverable for a subset of figure-linked samples and are therefore not used as the primary contrast axis in this layer.",
        ],
    }

    return proteins, summary


def build_outputs() -> dict[str, Any]:
    liver_metadata = parse_liver_metadata()
    samples = parse_sample_metadata(liver_metadata)
    proteins, proteomics_summary = parse_report_matrix(samples)

    sample_summary = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": proteomics_summary["generated_at_utc"],
        "sample_count": len(samples),
        "by_clinical_state": dict(sorted(Counter(sample["clinical_state"] for sample in samples).items())),
        "by_sample_origin": {"donor_liver": len(samples)},
        "by_assay_modality": {"proteomics": len(samples)},
        "by_collection_timepoint": dict(sorted(Counter(sample["collection_timepoint"] for sample in samples).items())),
    }

    cohort_summary = {
        "source_id": SOURCE_ID,
        "generated_at_utc": proteomics_summary["generated_at_utc"],
        "donor_liver_count": len(liver_metadata),
        "sample_count": len(samples),
        "clinical_group_counts": sample_summary["by_clinical_state"],
        "liver_level_biliary_viability_counts": dict(
            sorted(Counter(meta["clinical_state"] for meta in liver_metadata.values()).items())
        ),
        "sample_origin": "donor_liver",
        "context": "bile proteomics during normothermic machine perfusion of discarded donor livers",
    }

    protein_features = {
        "study_accession": SOURCE_ID,
        "source_url": ARTICLE_URL,
        "assay_modality": "proteomics",
        "assay_scale": "log2_pg_quantity",
        "sample_scope": "donor_bile_nmp_viability_timecourse",
        "generated_at_utc": proteomics_summary["generated_at_utc"],
        "protein_count": len(proteins),
        "reported_protein_group_count": proteomics_summary["protein_group_count"],
        "limitations": [
            "Protein-group quantities come from the public PRIDE search-engine output report and are summarized at the gene-query level.",
            "This V1 layer focuses on donor-liver biliary viability rather than post-transplant recipient outcome classification.",
            "Sample-level transplantability is intentionally not used as the main contrast because only a figure-linked subset exposes explicit transplant labels.",
        ],
        "proteins": proteins,
    }

    provenance = {
        "generated_at_utc": proteomics_summary["generated_at_utc"],
        "processing_script": "scripts/ingest_pxd046355_donor_bile_proteomics.py",
        "source_urls": {
            "article": ARTICLE_URL,
            "pride_report": PRIDE_REPORT_URL,
            "source_data_xlsx": SOURCE_DATA_URL,
            "supplementary_pdf": SUPPLEMENT_PDF_URL,
        },
        "identifier_mapping_rule": "Used the report's PG.Genes column as the gene-query surface and duplicated semicolon-delimited gene aliases for direct lookup; primary_uniprot is the first accession listed in PG.ProteinAccessions.",
        "sample_metadata_rule": "Recovered sample IDs, liver numbers, and timepoints from Nature source-data Figure 3a; recovered liver-level biliary-viability labels from Figure 2e and joined them by donor liver number.",
        "normalization_rule": "Exploratory contrasts are computed on log2(PG.Quantity + 1) values from the public PRIDE report.",
        "contrast_method": "Welch two-sample t-test across high versus low biliary-viability donor livers within each timepoint, with Benjamini-Hochberg FDR per contrast.",
        "limitations": protein_features["limitations"]
        + [
            "Merged-cell layout in the source-data workbook means some BDI annotations are inferred by carry-forward within the same sheet and therefore treated as descriptive metadata only.",
            "The current public supplement cleanly supports 30min and 150min viability contrasts, while low-viability end-perfusion samples are too sparse for a stable third contrast.",
        ],
    }

    inventory = {
        "files": [
            file_record(REPORT_PATH, "pride_search_engine_report"),
            file_record(SOURCE_DATA_PATH, "nature_source_data_xlsx"),
            file_record(SUPPLEMENT_PDF_PATH, "nature_supplementary_pdf"),
            file_record(SUPPLEMENT_TEXT_PATH, "nature_supplementary_text"),
        ]
    }

    return {
        "samples": samples,
        "sample_summary": sample_summary,
        "cohort_summary": cohort_summary,
        "proteomics_summary": proteomics_summary,
        "protein_features": protein_features,
        "analysis_provenance": provenance,
        "source_file_inventory": inventory,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build donor-liver bile proteomics evidence for PXD046355.")
    parser.add_argument("--skip-download", action="store_true", help="Use existing local files without downloading.")
    args = parser.parse_args()

    ensure_dir(RAW_DIR)
    ensure_dir(PROCESSED_DIR)

    if not args.skip_download:
        download_if_missing(PRIDE_REPORT_URL, REPORT_PATH)
        download_if_missing(SOURCE_DATA_URL, SOURCE_DATA_PATH)
        download_if_missing(SUPPLEMENT_PDF_URL, SUPPLEMENT_PDF_PATH)
    pdf_to_text(SUPPLEMENT_PDF_PATH, SUPPLEMENT_TEXT_PATH)

    outputs = build_outputs()
    for name, payload in outputs.items():
        write_json(PROCESSED_DIR / f"{name}.json", payload)

    print(
        json.dumps(
            {
                "source_id": SOURCE_ID,
                "sample_count": outputs["sample_summary"]["sample_count"],
                "protein_count": outputs["protein_features"]["protein_count"],
                "clinical_states": outputs["sample_summary"]["by_clinical_state"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
