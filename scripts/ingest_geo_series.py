from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
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
    },
    "GSE13440": {
        "url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE13nnn/GSE13440/matrix/GSE13440_series_matrix.txt.gz",
        "title_label_rules": [
            {
                "pattern": "ACR-predominant",
                "original_label": "ACR-predominant with superimposed RHC",
                "clinical_state": "ACR",
                "display_label": "Acute cellular rejection predominant with recurrent HCV",
            },
            {
                "pattern": "RHC with no ACR",
                "original_label": "RHC with no ACR",
                "clinical_state": "RHC_no_ACR",
                "display_label": "Recurrent hepatitis C without acute cellular rejection",
            },
        ],
        "sample_origin": "graft_liver_biopsy",
        "transplant_phase": "post_transplant",
        "assay_modality": "bulk_rna",
    },
    "GSE11881": {
        "url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE11nnn/GSE11881/matrix/GSE11881_series_matrix.txt.gz",
        "title_label_rules": [
            {
                "pattern": "^Tolerant PBMC",
                "original_label": "tolerant_liver_transplant_recipient",
                "clinical_state": "operational_tolerance",
                "display_label": "Operationally tolerant liver transplant recipient",
            },
            {
                "pattern": "^Non-tolerant PBMC",
                "original_label": "non_tolerant_liver_transplant_recipient",
                "clinical_state": "non_tolerant",
                "display_label": "Non-tolerant liver transplant recipient under immunosuppression",
            },
        ],
        "sample_origin": "recipient_blood",
        "transplant_phase": "post_transplant",
        "assay_modality": "bulk_rna",
    },
    "GSE243887": {
        "url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE243nnn/GSE243887/matrix/GSE243887_series_matrix.txt.gz",
        "characteristic_label_field": "transplant-selection",
        "characteristic_label_map": {
            "accepted": {
                "original_label": "Accepted donor liver",
                "clinical_state": "accepted_donor_liver",
                "display_label": "Donor liver accepted for transplantation",
            },
            "rejected": {
                "original_label": "Rejected donor liver",
                "clinical_state": "rejected_donor_liver",
                "display_label": "Donor liver rejected for transplantation",
            },
        },
        "sample_origin": "donor_liver",
        "transplant_phase": "donor_recovery",
        "assay_modality": "bulk_rna",
        "count_matrix_column_field": "description",
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    cluster_value = None
    cluster: dict[str, str] = {}
    standardization_rule = "unmapped"
    if "cluster_field" in config:
        cluster_value = characteristics.get(config["cluster_field"])
        cluster = config["cluster_map"].get(str(cluster_value), {})
        standardization_rule = f"characteristics:{config['cluster_field']}={cluster_value}"
    elif "characteristic_label_field" in config:
        label_field = config["characteristic_label_field"]
        label_value = characteristics.get(label_field, "")
        cluster = config["characteristic_label_map"].get(label_value.lower(), {})
        standardization_rule = f"characteristics:{label_field}={label_value}"
    elif "title_label_rules" in config:
        title = str(sample.get("title", ""))
        haystack = " ".join([title, *sample.get("characteristics_ch1", [])])
        for rule in config["title_label_rules"]:
            if re.search(rule["pattern"], haystack, flags=re.IGNORECASE):
                cluster = {
                    "original_label": rule["original_label"],
                    "clinical_state": rule["clinical_state"],
                    "display_label": rule["display_label"],
                }
                standardization_rule = f"title_or_characteristics_regex:{rule['pattern']}"
                break
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
        "standardization_rule": standardization_rule,
        "raw_characteristics": sample.get("characteristics_ch1", []),
        "supplementary_file": sample.get("supplementary_file"),
        "platform_id": sample.get("platform_id"),
        "matrix_sample_id": sample.get(config.get("count_matrix_column_field", ""), sample.get("geo_accession")),
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
        "source_file": {
            "path": str(raw_path.relative_to(ROOT)),
            "bytes": raw_path.stat().st_size,
            "sha256": sha256_file(raw_path),
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "parser": "scripts/ingest_geo_series.py",
        "standardization_rules": {
            "cluster_field": config.get("cluster_field"),
            "cluster_map": config.get("cluster_map"),
            "characteristic_label_field": config.get("characteristic_label_field"),
            "characteristic_label_map": config.get("characteristic_label_map"),
            "title_label_rules": config.get("title_label_rules"),
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
