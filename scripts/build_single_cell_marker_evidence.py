from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import numpy as np
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]

STUDY_CONFIG = {
    "GSE189539": {
        "matrix_url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE189nnn/GSE189539/suppl/GSE189539_Filtered_gene_counts_matrix.csv.gz",
        "matrix_filename": "GSE189539_Filtered_gene_counts_matrix.csv.gz",
        "limitations": [
            "The GEO supplementary matrix provides cell-level counts but no reusable cell-to-sample or cell-type annotation table.",
            "This V1 layer summarizes pre-specified marker genes and marker programs across the full public matrix; it is not a full re-clustering, sample-level contrast, or cell-type composition analysis.",
            "The public sample labels capture before-LT cold perfusion and after-LT portal reperfusion states, not biopsy-proven rejection outcomes.",
        ],
    }
}

MARKER_PROGRAMS = {
    "EAD_PATHOGENIC_IMMUNE_NICHE": {
        "label": "Early allograft dysfunction immune niche markers",
        "genes": ["S100A12", "S100A8", "S100A9", "GZMB", "GZMK", "NKG7", "GNLY", "KLRB1", "TRAV1-2"],
        "interpretation": "Marker program drawn from the reported MAIT, GZMB+GZMK+ NK, and S100A12+ neutrophil niche.",
    },
    "T_NK_CYTOTOXICITY": {
        "label": "T/NK cytotoxicity",
        "genes": ["NKG7", "GNLY", "GZMB", "GZMK", "PRF1", "IFNG"],
        "interpretation": "Cytotoxic lymphocyte marker program for graft immune activation.",
    },
    "NEUTROPHIL_INFLAMMATION": {
        "label": "Neutrophil inflammation",
        "genes": ["S100A8", "S100A9", "S100A12", "FCGR3B", "CSF3R"],
        "interpretation": "Neutrophil-associated inflammatory marker program.",
    },
    "HEPATOCYTE_FUNCTION": {
        "label": "Hepatocyte function",
        "genes": ["ALB", "APOA1", "APOB", "CYP3A4", "TTR"],
        "interpretation": "Parenchymal liver function marker program.",
    },
    "ENDOTHELIAL_ACTIVATION": {
        "label": "Endothelial activation",
        "genes": ["PECAM1", "VWF", "KDR", "SELE", "ICAM1"],
        "interpretation": "Endothelial and vascular activation marker program.",
    },
    "MYELOID_MONOCYTE": {
        "label": "Myeloid and monocyte markers",
        "genes": ["LST1", "LYZ", "FCGR3A", "S100A8", "S100A9"],
        "interpretation": "Monocyte/myeloid inflammatory marker program.",
    },
}

MARKER_GENES = sorted({gene for program in MARKER_PROGRAMS.values() for gene in program["genes"]})


def download(url: str, target: Path, force: bool = False) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not force:
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


def load_samples(accession: str) -> list[dict[str, Any]]:
    path = ROOT / "data" / "processed" / accession / "samples.json"
    if not path.exists():
        raise FileNotFoundError(f"Run scripts/ingest_geo_series.py {accession} first; missing {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def benjamini_hochberg(rows: list[dict[str, Any]]) -> None:
    indexed = [(index, row["p_value"]) for index, row in enumerate(rows) if row.get("p_value") is not None]
    indexed.sort(key=lambda item: item[1])
    m = len(indexed)
    prev = 1.0
    adjusted: dict[int, float] = {}
    for rank_from_end, (index, p_value) in enumerate(reversed(indexed), start=1):
        rank = m - rank_from_end + 1
        prev = min(prev, p_value * m / rank)
        adjusted[index] = min(prev, 1.0)
    for index, row in enumerate(rows):
        row["adj_p_value_bh"] = adjusted.get(index)


def finite_mean(values: list[float]) -> float | None:
    clean_values = [value for value in values if not math.isnan(value)]
    if not clean_values:
        return None
    return round(float(np.mean(clean_values)), 4)


def welch(case_values: list[float], control_values: list[float]) -> dict[str, Any]:
    case = np.array([value for value in case_values if not math.isnan(value)], dtype=float)
    control = np.array([value for value in control_values if not math.isnan(value)], dtype=float)
    result = {
        "n_case": int(case.size),
        "n_control": int(control.size),
        "mean_case": round(float(np.mean(case)), 4) if case.size else None,
        "mean_control": round(float(np.mean(control)), 4) if control.size else None,
        "mean_difference": None,
        "welch_t": None,
        "p_value": None,
    }
    if case.size and control.size:
        result["mean_difference"] = round(float(np.mean(case) - np.mean(control)), 4)
    if case.size >= 2 and control.size >= 2 and (np.var(case) > 0 or np.var(control) > 0):
        test = stats.ttest_ind(case, control, equal_var=False, nan_policy="omit")
        result["welch_t"] = round(float(test.statistic), 4)
        result["p_value"] = float(test.pvalue)
    return result


def cell_sample_prefix(cell_id: str) -> str:
    return cell_id.split("_", 1)[0]


def parse_marker_counts(matrix_path: Path) -> dict[str, Any]:
    marker_set = set(MARKER_GENES)
    with gzip.open(matrix_path, "rt", encoding="utf-8", errors="replace", newline="") as handle:
        header = next(csv.reader([handle.readline()]))
        cell_ids = header[1:]

        marker_counts: dict[str, np.ndarray] = {}
        observed_gene_count = 0
        for line in handle:
            observed_gene_count += 1
            gene_token, sep, rest = line.partition(",")
            if not sep:
                continue
            gene = gene_token.strip().strip('"').upper()
            if gene not in marker_set:
                continue
            values = np.fromstring(rest, sep=",", dtype=float)
            if values.size != len(cell_ids):
                continue
            marker_counts[gene] = values

    return {
        "cell_ids": cell_ids,
        "marker_counts": marker_counts,
        "observed_gene_count": observed_gene_count,
    }


def summarize_gene(
    gene: str,
    counts: np.ndarray,
) -> dict[str, Any]:
    mean_log1p = float(np.mean(np.log1p(counts)))
    pct_detected = float(np.mean(counts > 0) * 100)
    return {
        "gene_symbol": gene,
        "assay_scale": "mean_log1p_umi_per_cell",
        "whole_matrix_summary": {
            "cell_count": int(counts.size),
            "detected_cell_count": int(np.sum(counts > 0)),
            "pct_cells_detected": round(pct_detected, 3),
            "mean_umi_per_cell": round(float(np.mean(counts)), 4),
            "mean_log1p_umi_per_cell": round(mean_log1p, 4),
        },
    }


def build(accession: str, force: bool = False) -> dict[str, Any]:
    if accession not in STUDY_CONFIG:
        raise ValueError(f"Unsupported accession: {accession}")
    config = STUDY_CONFIG[accession]
    raw_path = ROOT / "data" / "raw" / accession / config["matrix_filename"]
    output_dir = ROOT / "data" / "processed" / accession
    download(config["matrix_url"], raw_path, force=force)

    samples = load_samples(accession)
    parsed = parse_marker_counts(raw_path)
    cell_count = len(parsed["cell_ids"])

    marker_summaries = {}
    for gene in MARKER_GENES:
        counts = parsed["marker_counts"].get(gene)
        if counts is None:
            continue
        summary = summarize_gene(gene, counts)
        summary["statistical_contrasts"] = {}
        marker_summaries[gene] = summary

    module_summaries = {}
    for module_id, module in MARKER_PROGRAMS.items():
        available_genes = [gene for gene in module["genes"] if gene in marker_summaries]
        marker_scores = [
            marker_summaries[gene]["whole_matrix_summary"]["mean_log1p_umi_per_cell"]
            for gene in available_genes
        ]
        module_summaries[module_id] = {
            "module_id": module_id,
            "label": module["label"],
            "interpretation": module["interpretation"],
            "genes": module["genes"],
            "available_genes": available_genes,
            "assay_scale": "mean marker-level log1p UMI per cell",
            "whole_matrix_summary": {
                "cell_count": cell_count,
                "available_gene_count": len(marker_scores),
                "mean_module_score": round(float(np.mean(marker_scores)), 4) if marker_scores else None,
            },
            "statistical_contrasts": {},
        }

    generated_at = datetime.now(timezone.utc).isoformat()
    sample_summary = {
        "study_accession": accession,
        "sample_count": len(samples),
        "cell_count": cell_count,
        "by_clinical_state": dict(Counter(sample["clinical_state"] for sample in samples)),
        "cell_to_sample_mapping_status": "unavailable_in_geo_filtered_matrix",
        "cell_count_by_sample": {},
        "cell_count_by_clinical_state": {},
        "assay_modality": "single_cell_rna",
        "generated_at_utc": generated_at,
    }
    marker_payload = {
        "study_accession": accession,
        "generated_at_utc": generated_at,
        "source_url": config["matrix_url"],
        "assay_modality": "single_cell_rna",
        "assay_scale": "mean_log1p_umi_per_cell",
        "sample_count": len(samples),
        "cell_count": cell_count,
        "cell_to_sample_mapping_status": "unavailable_in_geo_filtered_matrix",
        "observed_gene_count": parsed["observed_gene_count"],
        "marker_gene_count": len(marker_summaries),
        "contrast_method": "Not computed because the GEO filtered matrix does not expose a reusable cell-to-sample or cell-type metadata table.",
        "markers": marker_summaries,
    }
    module_payload = {
        "study_accession": accession,
        "generated_at_utc": generated_at,
        "source_url": config["matrix_url"],
        "assay_modality": "single_cell_rna",
        "sample_count": len(samples),
        "cell_count": cell_count,
        "cell_to_sample_mapping_status": "unavailable_in_geo_filtered_matrix",
        "module_count": len(module_summaries),
        "modules": module_summaries,
    }
    provenance = {
        "study_accession": accession,
        "generated_at_utc": generated_at,
        "parser": "scripts/build_single_cell_marker_evidence.py",
        "source": {
            "url": config["matrix_url"],
            **file_record(raw_path),
        },
        "outputs": {},
        "methods": [
            "GEO series metadata was ingested separately to map the eight samples to before-LT cold perfusion or after-LT portal reperfusion states.",
            "The public filtered single-cell gene-count matrix was scanned for a pre-specified marker panel instead of serializing the full cell-by-gene matrix.",
            "The GEO matrix column IDs do not contain sample accessions and no public cell metadata table was found in the GEO record, so marker evidence is summarized across the full matrix only.",
            "For each marker gene, evidence is summarized as percent detected cells, mean UMI per cell, and mean log1p UMI per cell across all cells.",
            "No sample-level, phase-level, cell-type-level, or rejection-outcome statistical contrast is computed in this V1 artifact.",
        ],
        "marker_programs": MARKER_PROGRAMS,
        "limitations": config["limitations"],
    }

    artifacts = {
        "samples": samples,
        "sample_summary": sample_summary,
        "single_cell_marker_summary": marker_payload,
        "single_cell_module_summary": module_payload,
        "analysis_provenance": provenance,
    }
    filenames = {
        "samples": "samples.json",
        "sample_summary": "sample_summary.json",
        "single_cell_marker_summary": "single_cell_marker_summary.json",
        "single_cell_module_summary": "single_cell_module_summary.json",
        "analysis_provenance": "analysis_provenance.json",
    }
    for artifact, payload in artifacts.items():
        path = output_dir / filenames[artifact]
        write_json(path, payload)
        provenance["outputs"][artifact] = file_record(path)
    write_json(output_dir / "analysis_provenance.json", provenance)
    return {
        "study_accession": accession,
        "sample_count": sample_summary["sample_count"],
        "cell_count": cell_count,
        "marker_gene_count": len(marker_summaries),
        "artifacts": sorted(filenames),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build lightweight single-cell marker evidence for a processed study.")
    parser.add_argument("accession", choices=sorted(STUDY_CONFIG))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.accession, force=args.force), indent=2))


if __name__ == "__main__":
    main()
