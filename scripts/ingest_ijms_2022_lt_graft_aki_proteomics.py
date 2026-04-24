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


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "IJMS_2022_LT_GRAFT_AKI_PROTEOMICS"
RAW_DIR = ROOT / "data" / "raw" / SOURCE_ID
PROCESSED_DIR = ROOT / "data" / "processed" / SOURCE_ID

ARTICLE_URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC9569532/"
ARTICLE_PDF_URL = "https://rcastoragev2.blob.core.windows.net/5c2e5a699d6f5e790237713eacc60869/PMC9569532.pdf"
ARTICLE_PDF_PATH = RAW_DIR / "ijms_2022_lt_graft_aki_proteomics.pdf"
LAYOUT_TEXT_PATH = RAW_DIR / "ijms_2022_lt_graft_aki_proteomics.layout.txt"

CASE_STATE = "moderate_severe_early_aki"
CONTROL_STATE = "no_early_aki"
CASE_N = 7
CONTROL_N = 7

ACCESSION_LINE_PREFIXES = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

TITLE_SENTINEL = "Table 2. List of proteins differentially expressed"
END_SENTINEL = "For an overall assessment of proteomic similarities"

MANUAL_NAME_OVERRIDES = {
    "PLA2G2A": "Phospholipase A2, membrane associated",
    "SCARB2": "Lysosome membrane protein 2",
    "GSTA2": "Glutathione S-transferase A2",
    "MFAP2": "Microfibrillar-associated protein 2",
    "PECAM1": "Platelet endothelial cell adhesion molecule",
    "NAGLU": "Alpha-N-acetylglucosaminidase",
    "STAB1": "Stabilin-1",
    "COQ10B": "Coenzyme Q-binding protein COQ10 homolog B",
    "SULT2A1": "Bile salt sulfotransferase",
    "PARP4": "Protein mono-ADP-ribosyltransferase PARP4",
    "SLC13A3": "Solute carrier family 13 member 3",
}


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
    return round(value, digits)


def download_if_missing(url: str, path: Path) -> None:
    if path.exists():
        return
    ensure_dir(path.parent)
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request) as response, path.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def pdf_to_layout_text(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def is_accession_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped[0] not in ACCESSION_LINE_PREFIXES:
        return False
    parts = stripped.split()
    if len(parts) < 5:
        return False
    accession = parts[0]
    symbol = parts[1]
    return accession[0].isalnum() and symbol.isupper()


def skip_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    return any(
        token in stripped
        for token in [
            "Table 2.",
            "Int. J. Mol. Sci.",
            "Accession",
            "Fold Changes",
            "Gene",
            "Symbol",
            "\x0c",
        ]
    )


def split_line_fields(raw: str) -> tuple[str, str, str, float, str, float, str]:
    stripped = raw.rstrip()
    parts = stripped.split()
    accession = parts[0]
    symbol = parts[1]

    fold_index = None
    for idx in range(2, len(parts)):
        token = parts[idx]
        try:
            float(token)
        except ValueError:
            continue
        next_token = parts[idx + 1] if idx + 1 < len(parts) else ""
        if next_token.startswith("<") or next_token.replace(".", "", 1).isdigit():
            fold_index = idx
            break
    if fold_index is None:
        raise ValueError(f"Could not parse fold change from line: {raw}")

    description = " ".join(parts[2:fold_index]).strip()
    fold_change = float(parts[fold_index])
    p_token = parts[fold_index + 1]
    tail = " ".join(parts[fold_index + 2 :]).strip()
    p_value_numeric = float(p_token.lstrip("<"))
    return accession, symbol, description, fold_change, p_token, p_value_numeric, tail


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\u2019", "'").split())


def protein_name_from_parts(symbol: str, description: str, post_lines: list[str]) -> str:
    if description:
        return description
    if symbol in MANUAL_NAME_OVERRIDES:
        return MANUAL_NAME_OVERRIDES[symbol]
    continuation = []
    for line in post_lines[:2]:
        left = normalize_text(line[:40].strip())
        if left and len(left.split()) <= 6:
            continuation.append(left)
    joined = normalize_text(" ".join(continuation))
    return joined or symbol


def extract_table_rows(layout_text: str) -> list[dict[str, Any]]:
    start = layout_text.index(TITLE_SENTINEL)
    end = layout_text.index(END_SENTINEL)
    block = layout_text[start:end]
    data_started = False
    rows: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    pending: list[str] = []

    for raw_line in block.splitlines():
        if skip_line(raw_line):
            continue
        if not data_started:
            if is_accession_line(raw_line):
                data_started = True
            else:
                continue

        if is_accession_line(raw_line):
            if current is not None:
                rows.append(current)
            accession, symbol, description, fold_change, p_token, p_value, tail = split_line_fields(raw_line)
            current = {
                "accession": accession,
                "gene_symbol": symbol,
                "description_fragment": description,
                "fold_change": fold_change,
                "p_value_text": p_token,
                "p_value": p_value,
                "tail_fragment": tail,
                "pre_lines": pending[:],
                "post_lines": [],
            }
            pending.clear()
            continue

        if current is None:
            pending.append(raw_line.strip())
        else:
            current["post_lines"].append(raw_line.rstrip())

    if current is not None:
        rows.append(current)

    cleaned = []
    for row in rows:
        protein_name = protein_name_from_parts(
            row["gene_symbol"],
            normalize_text(row["description_fragment"]),
            row["post_lines"],
        )
        cleaned.append(
            {
                "primary_uniprot": row["accession"],
                "gene_symbol": row["gene_symbol"],
                "protein_name": protein_name,
                "published_fold_change_average_value": row["fold_change"],
                "p_value": row["p_value"],
                "p_value_text": row["p_value_text"],
                "log2_fold_change": round_or_none(math.log2(row["fold_change"])),
                "direction": "higher_in_moderate_severe_early_aki"
                if row["fold_change"] > 1
                else "lower_in_moderate_severe_early_aki",
                "biological_process_or_function_excerpt": normalize_text(row["tail_fragment"]),
                "layout_parse_context": {
                    "pre_lines": [normalize_text(item) for item in row["pre_lines"] if normalize_text(item)],
                    "post_lines": [normalize_text(item) for item in row["post_lines"] if normalize_text(item)],
                },
            }
        )
    return cleaned


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


def build_samples() -> list[dict[str, Any]]:
    samples = []
    for state, prefix, count in [
        (CASE_STATE, "AKI", CASE_N),
        (CONTROL_STATE, "NOAKI", CONTROL_N),
    ]:
        for index in range(1, count + 1):
            samples.append(
                {
                    "sample_accession": f"{prefix}{index:02d}",
                    "title": f"{state.replace('_', ' ')} graft biopsy sample {index}",
                    "clinical_state": state,
                    "sample_origin": "graft_liver_biopsy",
                    "assay_modality": "proteomics",
                    "collection_timepoint": "postreperfusion_liver_graft_biopsy",
                    "sample_id_origin": "synthetic_group_placeholder_from_published_counts",
                }
            )
    return samples


def build_sample_summary(samples: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    by_state: dict[str, int] = {}
    for sample in samples:
        by_state[sample["clinical_state"]] = by_state.get(sample["clinical_state"], 0) + 1
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "sample_count": len(samples),
        "by_clinical_state": by_state,
        "by_sample_origin": {"graft_liver_biopsy": len(samples)},
        "by_assay_modality": {"proteomics": len(samples)},
        "limitations": [
            "Sample identifiers are synthetic placeholders generated from published group counts.",
            "The public article exposes a differential protein table, not a reusable per-sample abundance matrix.",
        ],
    }


def build_protein_payload(rows: list[dict[str, Any]], generated_at: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    contrasts: list[dict[str, Any]] = []
    proteins: dict[str, dict[str, Any]] = {}
    for row in rows:
        contrast = {
            "contrast_id": f"{CASE_STATE}_vs_{CONTROL_STATE}",
            "context": "postreperfusion_graft_biopsy",
            "case_state": CASE_STATE,
            "control_state": CONTROL_STATE,
            "case_n": CASE_N,
            "control_n": CONTROL_N,
            "mean_difference": row["log2_fold_change"],
            "effect_scale": "published_average_abundance_log2_ratio",
            "published_fold_change_average_value": row["published_fold_change_average_value"],
            "p_value": row["p_value"],
            "p_value_text": row["p_value_text"],
            "direction": row["direction"],
        }
        contrasts.append(contrast)
        proteins[row["gene_symbol"]] = {
            "gene_symbol": row["gene_symbol"],
            "primary_uniprot": row["primary_uniprot"],
            "protein_name": row["protein_name"],
            "evidence_kind": "direct_transplant_protein_biomarker",
            "sample_scope": "graft_postreperfusion_biopsy_aki_risk",
            "summary_level": "published_differential_table",
            "measurement_type": "published_tissue_protein_abundance_ratio",
            "reported_group_counts": {
                CASE_STATE: {"n": CASE_N},
                CONTROL_STATE: {"n": CONTROL_N},
            },
            "published_contrasts": [contrast],
            "reported_annotations": {
                "biological_process_or_function_excerpt": row["biological_process_or_function_excerpt"],
            },
            "limitations": [
                "This layer is reconstructed from the published differential protein table rather than a public per-sample tissue proteomics matrix.",
                "Fold changes and p-values come from the article's reported table and are not recomputed from raw intensities.",
                "The comparison reflects early AKI risk after transplantation and should not be treated as rejection-specific evidence.",
            ],
        }

    benjamini_hochberg(contrasts)

    payload = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "source_url": ARTICLE_URL,
        "assay_modality": "proteomics",
        "assay_scale": "published_average_abundance_log2_ratio",
        "sample_scope": "graft_postreperfusion_biopsy_aki_risk",
        "protein_count": len(proteins),
        "reported_table_row_count": len(rows),
        "reported_article_differential_protein_count": 136,
        "proteins": proteins,
        "limitations": [
            "This source exposes a published differential tissue proteomics table from postreperfusion graft biopsies, not a reusable per-sample abundance matrix.",
            "The article reports 136 differentially expressed proteins; the current layout-based parser recovered the queryable subset present in the PDF text extraction.",
            "This layer is best interpreted as early graft-injury / AKI-context proteomics rather than rejection-specific evidence.",
        ],
    }
    return payload, contrasts


def build_summary(generated_at: str, protein_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "assay_modality": "proteomics",
        "sample_scope": "graft_postreperfusion_biopsy_aki_risk",
        "sample_count": CASE_N + CONTROL_N,
        "protein_feature_count": protein_payload["protein_count"],
        "reported_table_row_count": protein_payload["reported_table_row_count"],
        "reported_article_differential_protein_count": protein_payload["reported_article_differential_protein_count"],
        "clinical_group_counts": {
            CASE_STATE: CASE_N,
            CONTROL_STATE: CONTROL_N,
        },
        "feature_symbols": sorted(protein_payload["proteins"].keys()),
        "limitations": protein_payload["limitations"],
    }


def build_provenance(generated_at: str, layout_text: str, output_paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "parser": "scripts/ingest_ijms_2022_lt_graft_aki_proteomics.py",
        "source_files": {
            "article_pdf": {
                "url": ARTICLE_PDF_URL,
                **file_record(ARTICLE_PDF_PATH),
            },
            "layout_text": {
                **file_record(LAYOUT_TEXT_PATH),
            },
        },
        "methods": [
            "Downloaded the public PDF for the IJMS 2022 liver-transplant graft proteomics article.",
            "Converted the PDF to layout-preserving plain text with pdftotext -layout.",
            "Parsed Table 2 differential protein rows from the published PDF text.",
            "Represented the reported early AKI versus no AKI comparison as a direct transplant graft-tissue proteomics evidence layer.",
            "Applied Benjamini-Hochberg correction across the extracted published p-values for the exposed feature table.",
            "Generated synthetic sample placeholders from the published cohort counts because public per-sample identifiers were not reusable.",
        ],
        "identifier_mapping_rule": "Used the article's published UniProt accession and gene symbol columns directly from Table 2.",
        "normalization_rule": "Used the article's published average fold-change ratios and reported p-values as-is; no re-normalization or raw-spectrum reprocessing was performed.",
        "text_hashes": {
            "layout_text_sha256": hashlib.sha256(layout_text.encode("utf-8")).hexdigest(),
        },
        "outputs": {artifact: file_record(path) for artifact, path in output_paths.items()},
        "limitations": [
            "No public per-sample intensity matrix was available, so this source is exposed as published differential-table evidence.",
            "The PDF layout parser may miss a minority of wrapped rows; the article-reported total differential count is retained separately for provenance.",
            "The source addresses early AKI / graft injury context and should not be treated as a rejection-specific classifier.",
        ],
    }


def build(force: bool = False) -> dict[str, Any]:
    ensure_dir(RAW_DIR)
    ensure_dir(PROCESSED_DIR)
    if force and ARTICLE_PDF_PATH.exists():
        ARTICLE_PDF_PATH.unlink()
    download_if_missing(ARTICLE_PDF_URL, ARTICLE_PDF_PATH)

    layout_text = pdf_to_layout_text(ARTICLE_PDF_PATH)
    LAYOUT_TEXT_PATH.write_text(layout_text, encoding="utf-8")
    rows = extract_table_rows(layout_text)
    generated_at = datetime.now(timezone.utc).isoformat()
    samples = build_samples()
    sample_summary = build_sample_summary(samples, generated_at)
    protein_payload, all_contrasts = build_protein_payload(rows, generated_at)
    summary = build_summary(generated_at, protein_payload)
    cohort_summary = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "sample_count": len(samples),
        "patient_count": len(samples),
        "clinical_group_counts": {
            CASE_STATE: CASE_N,
            CONTROL_STATE: CONTROL_N,
        },
        "biopsy_timing": "postreperfusion_liver_graft_biopsy",
        "protein_feature_count": protein_payload["protein_count"],
        "reported_article_differential_protein_count": 136,
        "limitations": sample_summary["limitations"],
    }
    source_inventory = {
        "study_accession": SOURCE_ID,
        "generated_at_utc": generated_at,
        "files": [
            {"label": "article_pdf", **file_record(ARTICLE_PDF_PATH)},
            {"label": "layout_text", **file_record(LAYOUT_TEXT_PATH)},
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
    provenance = build_provenance(generated_at, layout_text, output_paths)
    provenance_path = PROCESSED_DIR / "analysis_provenance.json"
    write_json(provenance_path, provenance)
    output_paths["analysis_provenance"] = provenance_path

    return {
        "study_accession": SOURCE_ID,
        "sample_count": len(samples),
        "protein_feature_count": protein_payload["protein_count"],
        "reported_table_row_count": len(rows),
        "reported_article_differential_protein_count": 136,
        "contrast_count": len(all_contrasts),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build IJMS 2022 liver graft AKI proteomics evidence layer.")
    parser.add_argument("--force", action="store_true", help="Re-download the source PDF before rebuilding outputs.")
    args = parser.parse_args()
    result = build(force=args.force)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
