from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]

GEO_SERIES = {
    "GSE145780": {
        "url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE145nnn/GSE145780/matrix/GSE145780_series_matrix.txt.gz",
        "cluster_field": "cluster (1, 2, 3, 4)",
        "cluster_map": {
            "1": {
                "original_label": "R1normal",
                "clinical_state": "no_rejection",
                "display_label": "R1 normal/no rejection",
            },
            "2": {
                "original_label": "R2TCMR",
                "clinical_state": "TCMR",
                "display_label": "R2 T cell-mediated rejection",
            },
            "3": {
                "original_label": "R3injury",
                "clinical_state": "early_injury",
                "display_label": "R3 early injury",
            },
            "4": {
                "original_label": "R4late",
                "clinical_state": "fibrosis",
                "display_label": "R4 late/fibrosis",
            },
        },
        "sample_origin": "graft_liver",
        "transplant_phase": "post_transplant",
        "assay_modality": "bulk_rna",
    }
}


def split_geo_values(line: str) -> list[str]:
    return next(csv.reader([line], delimiter="\t"))


def clean(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    return value


def download(url: str, target: Path, force: bool = False) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not force:
        return
    tmp = target.with_suffix(target.suffix + ".tmp")
    with urlopen(url, timeout=90) as response, tmp.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    tmp.replace(target)


def parse_series_matrix(path: Path) -> dict[str, Any]:
    series: dict[str, list[str]] = {}
    sample_rows: list[tuple[str, list[str]]] = []

    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if line == "!series_matrix_table_begin":
                break
            if not line.startswith("!"):
                continue
            parts = split_geo_values(line)
            key = parts[0]
            values = [clean(value) for value in parts[1:]]
            if key.startswith("!Sample_"):
                sample_rows.append((key.removeprefix("!Sample_"), values))
            elif key.startswith("!Series_"):
                series.setdefault(key.removeprefix("!Series_"), []).extend(values)

    accessions = first_sample_row(sample_rows, "geo_accession")
    if not accessions:
        raise ValueError(f"No !Sample_geo_accession row found in {path}")

    samples = [{"geo_accession": accession} for accession in accessions]
    for key, values in sample_rows:
        if len(values) != len(samples):
            continue
        for sample, value in zip(samples, values, strict=True):
            if key == "geo_accession":
                continue
            if key == "characteristics_ch1":
                sample.setdefault("characteristics_ch1", []).append(value)
            else:
                sample[key] = value

    return {"series": series, "samples": samples}


def first_sample_row(rows: list[tuple[str, list[str]]], name: str) -> list[str]:
    for key, values in rows:
        if key == name:
            return values
    return []


def parse_characteristics(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if ":" not in value:
            continue
        key, raw = value.split(":", 1)
        normalized_key = re.sub(r"\s+", " ", key.strip().lower())
        parsed[normalized_key] = raw.strip()
    return parsed


def standardize_sample(sample: dict[str, Any], config: dict[str, Any], accession: str) -> dict[str, Any]:
    characteristics = parse_characteristics(sample.get("characteristics_ch1", []))
    cluster_value = characteristics.get(config["cluster_field"])
    cluster = config["cluster_map"].get(str(cluster_value), {})
    standardized_state = cluster.get("clinical_state", "to_verify")

    return {
        "study_accession": accession,
        "sample_accession": sample["geo_accession"],
        "title": sample.get("title"),
        "organism": sample.get("organism_ch1"),
        "source_name": sample.get("source_name_ch1"),
        "sample_origin": config["sample_origin"],
        "transplant_phase": config["transplant_phase"],
        "assay_modality": config["assay_modality"],
        "original_cluster": cluster_value,
        "original_label": cluster.get("original_label", "to_verify"),
        "display_label": cluster.get("display_label", "To verify"),
        "clinical_state": standardized_state,
        "standardization_confidence": "high" if cluster else "needs_review",
        "raw_characteristics": sample.get("characteristics_ch1", []),
        "supplementary_file": sample.get("supplementary_file"),
        "platform_id": sample.get("platform_id"),
    }


def summarize_samples(samples: list[dict[str, Any]]) -> dict[str, Any]:
    by_state = Counter(sample["clinical_state"] for sample in samples)
    by_label = Counter(sample["original_label"] for sample in samples)
    by_origin = Counter(sample["sample_origin"] for sample in samples)
    by_modality = Counter(sample["assay_modality"] for sample in samples)
    return {
        "sample_count": len(samples),
        "by_clinical_state": dict(sorted(by_state.items())),
        "by_original_label": dict(sorted(by_label.items())),
        "by_sample_origin": dict(sorted(by_origin.items())),
        "by_assay_modality": dict(sorted(by_modality.items())),
    }


def ingest(accession: str, force: bool = False) -> dict[str, Any]:
    if accession not in GEO_SERIES:
        supported = ", ".join(sorted(GEO_SERIES))
        raise ValueError(f"Unsupported accession {accession}. Supported: {supported}")

    config = GEO_SERIES[accession]
    raw_path = ROOT / "data" / "raw" / "geo" / accession / f"{accession}_series_matrix.txt.gz"
    output_dir = ROOT / "data" / "processed" / accession
    output_dir.mkdir(parents=True, exist_ok=True)

    download(config["url"], raw_path, force=force)
    parsed = parse_series_matrix(raw_path)
    samples = [
        standardize_sample(sample, config, accession)
        for sample in parsed["samples"]
    ]
    summary = summarize_samples(samples)
    provenance = {
        "study_accession": accession,
        "source_url": config["url"],
        "raw_path": str(raw_path.relative_to(ROOT)),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "parser": "scripts/ingest_geo_series.py",
        "standardization_rules": {
            "cluster_field": config["cluster_field"],
            "cluster_map": config["cluster_map"],
        },
        "series_title": parsed["series"].get("title", [None])[0],
        "series_pubmed_id": parsed["series"].get("pubmed_id", []),
        "series_summary": parsed["series"].get("summary", [None])[0],
    }

    (output_dir / "samples.json").write_text(json.dumps(samples, indent=2) + "\n", encoding="utf-8")
    (output_dir / "sample_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")

    return {
        "accession": accession,
        "raw_path": str(raw_path.relative_to(ROOT)),
        "output_dir": str(output_dir.relative_to(ROOT)),
        **summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest GEO series metadata into LiverTx-OmicsDB.")
    parser.add_argument("accession", choices=sorted(GEO_SERIES))
    parser.add_argument("--force", action="store_true", help="Redownload the source matrix even if cached.")
    args = parser.parse_args()
    result = ingest(args.accession, force=args.force)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
