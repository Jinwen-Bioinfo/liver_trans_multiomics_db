from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def safe_stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return stdev(values)


def summarize(values: list[float]) -> dict[str, int | float]:
    return {
        "n": len(values),
        "mean": round(mean(values), 4),
        "median": round(median(values), 4),
        "sd": round(safe_stdev(values), 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


def build_signature_scores(accession: str) -> dict[str, Any]:
    processed_dir = ROOT / "data" / "processed" / accession
    samples = load_json(processed_dir / "samples.json")
    sample_values = load_json(processed_dir / "gene_sample_values.json")
    signatures = load_json(ROOT / "data" / "registry" / "signatures.json")["signatures"]

    sample_by_key = {}
    for sample in samples:
        sample_by_key[sample["title"]] = sample
        sample_by_key[sample["sample_accession"]] = sample
    signature_payload: dict[str, Any] = {}

    for signature in signatures:
        genes = signature["genes"]
        directions = {gene: int(signature.get("directions", {}).get(gene, 1)) for gene in genes}
        gene_means: dict[str, float] = {}
        gene_sds: dict[str, float] = {}
        for gene in genes:
            values = list(sample_values.get(gene, {}).values())
            if len(values) < 2:
                continue
            gene_means[gene] = mean(values)
            gene_sds[gene] = safe_stdev(values) or 1.0
        sample_scores = []
        scores_by_state: dict[str, list[float]] = defaultdict(list)
        observed_sample_keys = sorted({key for gene in genes for key in sample_values.get(gene, {})})
        for sample_title in observed_sample_keys:
            sample = sample_by_key.get(sample_title)
            if sample is None:
                continue
            gene_values = [
                directions[gene] * ((sample_values[gene][sample_title] - gene_means[gene]) / gene_sds[gene])
                for gene in genes
                if gene in sample_values
                and gene in gene_means
                and gene in gene_sds
                and sample_title in sample_values[gene]
            ]
            if not gene_values:
                continue
            score = mean(gene_values)
            row = {
                "sample_title": sample.get("title"),
                "sample_key": sample_title,
                "sample_accession": sample["sample_accession"],
                "clinical_state": sample["clinical_state"],
                "score": round(score, 4),
                "genes_observed": len(gene_values),
            }
            sample_scores.append(row)
            scores_by_state[sample["clinical_state"]].append(score)

        group_summary = {
            state: summarize(values)
            for state, values in sorted(scores_by_state.items())
            if values
        }
        expected_state = signature.get("expected_high_state")
        best_state = max(group_summary, key=lambda state: group_summary[state]["mean"]) if group_summary else None
        signature_payload[signature["signature_id"]] = {
            **signature,
            "study_accession": accession,
            "assay_scale": "mean signed within-study z-score across observed signature genes",
            "sample_count": len(sample_scores),
            "gene_count_requested": len(genes),
            "gene_count_observed": len(gene_means),
            "genes_observed": sorted(gene_means),
            "missing_genes": sorted(set(genes) - set(gene_means)),
            "scoring_method": "For each gene, z-score normalized log2 intensity across all study samples is multiplied by the curated direction (+1/-1); sample score is the mean of observed signed z-scores.",
            "group_summary": group_summary,
            "best_state_by_mean": best_state,
            "expected_pattern_observed": best_state == expected_state,
            "sample_scores": sample_scores,
        }

    output = {
        "study_accession": accession,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "Signed within-study z-score signature scoring with explicit missing-gene reporting.",
        "signatures": signature_payload,
    }
    output_path = processed_dir / "signature_scores.json"
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return {
        "accession": accession,
        "signature_count": len(signature_payload),
        "signatures": sorted(signature_payload),
        "output_path": str(output_path.relative_to(ROOT)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build signature scores for a processed study.")
    parser.add_argument("accession")
    args = parser.parse_args()
    print(json.dumps(build_signature_scores(args.accession), indent=2))


if __name__ == "__main__":
    main()
