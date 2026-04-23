from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import numpy as np


ROOT = Path(__file__).resolve().parents[1]

PRIDE_FILES_URL = "https://www.ebi.ac.uk/pride/ws/archive/v2/projects/PXD012615/files?pageSize=200"
PXD012615_ZIP_URL = "https://ftp.pride.ebi.ac.uk/pride/data/archive/2020/04/PXD012615/MaxQuant_Output.zip"

CELL_TYPES = {
    "HC": "hepatocyte",
    "EC": "liver_sinusoidal_endothelial_cell",
    "KC": "kupffer_cell",
    "SC": "hepatic_stellate_cell",
}


def download(url: str, target: Path, force: bool = False) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 0 and not force:
        return
    tmp = target.with_suffix(target.suffix + ".tmp")
    with urlopen(url, timeout=120) as response, tmp.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    tmp.replace(target)


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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def parse_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def mean_log2_intensity(values: list[float]) -> float | None:
    positive = [value for value in values if value > 0]
    if not positive:
        return None
    return round(float(np.mean(np.log2(np.array(positive, dtype=float) + 1.0))), 4)


def first_token(value: str) -> str:
    return value.split(";", 1)[0].strip()


def parse_protein_groups(zip_path: Path) -> dict[str, Any]:
    proteins: dict[str, Any] = {}
    source_counts = Counter()
    with zipfile.ZipFile(zip_path) as archive, archive.open("proteinGroups.txt") as raw:
        reader = csv.DictReader((line.decode("utf-8", "replace") for line in raw), delimiter="\t")
        for row in reader:
            source_counts["protein_group_rows"] += 1
            if row.get("Reverse") == "+":
                source_counts["reverse_rows"] += 1
                continue
            if row.get("Potential contaminant") == "+":
                source_counts["contaminant_rows"] += 1
                continue
            if row.get("Only identified by site") == "+":
                source_counts["site_only_rows"] += 1
                continue
            gene_symbols = [token.strip().upper() for token in row.get("Gene names", "").split(";") if token.strip()]
            if not gene_symbols:
                source_counts["missing_gene_symbol_rows"] += 1
                continue
            gene_symbol = gene_symbols[0]
            cell_type_summary = {}
            means = {}
            detected_cell_types = []
            for prefix, label in CELL_TYPES.items():
                replicate_values = [
                    parse_float(row.get(f"Intensity {prefix}{replicate}", "0"))
                    for replicate in (1, 2, 3)
                ]
                detected_replicates = sum(1 for value in replicate_values if value > 0)
                mean_log2 = mean_log2_intensity(replicate_values)
                if mean_log2 is not None:
                    means[label] = mean_log2
                    detected_cell_types.append(label)
                cell_type_summary[label] = {
                    "replicate_count": 3,
                    "detected_replicate_count": detected_replicates,
                    "mean_log2_intensity": mean_log2,
                    "raw_intensity_values": [round(value, 4) for value in replicate_values],
                }
            best_cell_type = None
            if means:
                best_cell_type = max(means, key=means.get)
            feature = {
                "gene_symbol": gene_symbol,
                "protein_ids": row.get("Protein IDs", "").split(";"),
                "majority_protein_ids": row.get("Majority protein IDs", "").split(";"),
                "primary_uniprot": first_token(row.get("Majority protein IDs", "")),
                "protein_name": row.get("Protein names", ""),
                "peptide_count": int(parse_float(row.get("Peptides", "0"))),
                "unique_peptide_count": int(parse_float(row.get("Unique peptides", "0"))),
                "razor_unique_peptide_count": int(parse_float(row.get("Razor + unique peptides", "0"))),
                "score": parse_float(row.get("Score", "0")),
                "q_value": parse_float(row.get("Q-value", "0")),
                "molecular_weight_kda": parse_float(row.get("Mol. weight [kDa]", "0")),
                "detected_cell_types": detected_cell_types,
                "best_cell_type_by_mean_log2_intensity": best_cell_type,
                "cell_type_summary": cell_type_summary,
            }
            current = proteins.get(gene_symbol)
            if current is None or feature["score"] > current.get("score", 0):
                proteins[gene_symbol] = feature
            source_counts["kept_rows"] += 1
    return {"proteins": proteins, "source_counts": dict(source_counts)}


def load_pride_file_metadata() -> dict[str, Any]:
    with urlopen(PRIDE_FILES_URL, timeout=60) as response:
        files = json.load(response)
    for item in files:
        if item.get("fileName") == "MaxQuant_Output.zip":
            return item
    return {}


def build(accession: str, force: bool = False) -> dict[str, Any]:
    if accession != "PXD012615":
        raise ValueError("Only PXD012615 is supported")
    raw_path = ROOT / "data" / "raw" / accession / "MaxQuant_Output.zip"
    output_dir = ROOT / "data" / "processed" / accession
    download(PXD012615_ZIP_URL, raw_path, force=force)
    parsed = parse_protein_groups(raw_path)
    pride_file = load_pride_file_metadata()
    generated_at = datetime.now(timezone.utc).isoformat()

    proteins = parsed["proteins"]
    by_best_cell_type = Counter(
        item["best_cell_type_by_mean_log2_intensity"]
        for item in proteins.values()
        if item.get("best_cell_type_by_mean_log2_intensity")
    )
    summary = {
        "study_accession": accession,
        "generated_at_utc": generated_at,
        "assay_modality": "proteomics",
        "sample_scope": "reference_human_liver_cells",
        "protein_group_rows": parsed["source_counts"].get("protein_group_rows", 0),
        "kept_protein_group_rows": parsed["source_counts"].get("kept_rows", 0),
        "gene_symbol_count": len(proteins),
        "cell_types": list(CELL_TYPES.values()),
        "by_best_cell_type": dict(sorted(by_best_cell_type.items())),
        "source_counts": parsed["source_counts"],
        "limitations": [
            "PXD012615 is a human liver cell reference proteome, not a liver transplant cohort.",
            "Protein evidence is cell-type reference context and should not be interpreted as rejection or donor-outcome evidence.",
            "MaxQuant intensity values are summarized within this dataset only; no cross-study proteomics normalization is performed.",
        ],
    }
    feature_payload = {
        "study_accession": accession,
        "generated_at_utc": generated_at,
        "source_url": PXD012615_ZIP_URL,
        "assay_modality": "proteomics",
        "assay_scale": "log2(MaxQuant intensity + 1)",
        "sample_scope": "reference_human_liver_cells",
        "cell_types": CELL_TYPES,
        "protein_count": len(proteins),
        "proteins": proteins,
        "limitations": summary["limitations"],
    }
    provenance = {
        "study_accession": accession,
        "generated_at_utc": generated_at,
        "parser": "scripts/build_proteome_reference.py",
        "source": {
            "project_api": "https://www.ebi.ac.uk/pride/ws/archive/v2/projects/PXD012615",
            "files_api": PRIDE_FILES_URL,
            "download_url": PXD012615_ZIP_URL,
            "pride_file_metadata": pride_file,
            **file_record(raw_path),
        },
        "methods": [
            "Downloaded PRIDE MaxQuant output archive and parsed proteinGroups.txt.",
            "Filtered reverse hits, potential contaminants, site-only identifications, and rows without gene symbols.",
            "Mapped MaxQuant intensity columns HC, EC, KC, and SC to hepatocyte, liver sinusoidal endothelial cell, Kupffer cell, and hepatic stellate cell reference compartments.",
            "For each gene symbol, retained the highest-scoring protein group and summarized replicate intensities as log2(intensity + 1).",
        ],
        "outputs": {},
        "limitations": summary["limitations"],
    }
    artifacts = {
        "proteomics_summary": summary,
        "protein_features": feature_payload,
        "analysis_provenance": provenance,
    }
    filenames = {
        "proteomics_summary": "proteomics_summary.json",
        "protein_features": "protein_features.json",
        "analysis_provenance": "analysis_provenance.json",
    }
    for artifact, payload in artifacts.items():
        path = output_dir / filenames[artifact]
        write_json(path, payload)
        provenance["outputs"][artifact] = file_record(path)
    write_json(output_dir / "analysis_provenance.json", provenance)
    return {
        "study_accession": accession,
        "gene_symbol_count": len(proteins),
        "cell_types": list(CELL_TYPES.values()),
        "artifacts": sorted(filenames),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build protein feature evidence for PXD012615.")
    parser.add_argument("accession", choices=["PXD012615"])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.accession, force=args.force), indent=2))


if __name__ == "__main__":
    main()
