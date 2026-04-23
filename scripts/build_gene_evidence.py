from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any
from urllib.request import urlopen

import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED_URLS = {
    "GSE145780": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE145nnn/GSE145780/suppl/GSE145780_normalized_data_with_all_controls.txt.gz",
    "GSE13440": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE13nnn/GSE13440/matrix/GSE13440_series_matrix.txt.gz",
}
PLATFORM_URLS = {
    "GPL15207": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GPL15207&targ=self&form=text&view=data",
    "GPL1291": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GPL1291&targ=self&form=text&view=data",
}
STUDY_CONFIG = {
    "GSE145780": {
        "platform": "GPL15207",
        "matrix_filename": "GSE145780_normalized_data_with_all_controls.txt.gz",
        "matrix_source": "supplementary_matrix",
        "sample_match": "title_cel",
        "assay_scale": "normalized log2 microarray intensity",
        "contrasts": [
            ("TCMR", "no_rejection"),
            ("early_injury", "no_rejection"),
            ("fibrosis", "no_rejection"),
            ("TCMR", "early_injury"),
        ],
        "limitations": [
            "GSE145780 molecular states come from the source study labels, so diagnostic claims require independent validation.",
            "Microarray values are suitable for within-study comparison; cross-platform harmonization is not implemented yet.",
        ],
    },
    "GSE13440": {
        "platform": "GPL1291",
        "matrix_filename": "GSE13440_series_matrix.txt.gz",
        "matrix_source": "series_matrix_table",
        "sample_match": "geo_accession",
        "assay_scale": "source-normalized microarray log ratio",
        "contrasts": [("ACR", "RHC_no_ACR")],
        "limitations": [
            "GSE13440 compares ACR-predominant biopsies against recurrent hepatitis C without ACR, so rejection signals are interpreted in the recurrent-HCV context.",
            "The source matrix is a GEO series-matrix expression table from a two-color microarray platform; values are analyzed within-study only.",
        ],
    },
}


def download(url: str, target: Path, force: bool = False) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not force:
        return
    tmp = target.with_suffix(target.suffix + ".tmp")
    with urlopen(url, timeout=120) as response, tmp.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    tmp.replace(target)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def safe_stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return stdev(values)


def summarize_values(values: list[float]) -> dict[str, float | int]:
    clean = [value for value in values if not math.isnan(value)]
    if not clean:
        return {"n": 0, "mean": math.nan, "median": math.nan, "sd": math.nan, "min": math.nan, "max": math.nan}
    return {
        "n": len(clean),
        "mean": round(mean(clean), 4),
        "median": round(median(clean), 4),
        "sd": round(safe_stdev(clean), 4),
        "min": round(min(clean), 4),
        "max": round(max(clean), 4),
    }


def first_token(value: str, separator: str = " /// ") -> str | None:
    for token in value.split(separator):
        token = token.strip()
        if token and token != "---":
            return token
    return None


def first_present(row: dict[str, str], columns: list[str]) -> str:
    for column in columns:
        value = row.get(column, "").strip()
        if value:
            return value
    return ""


def parse_platform(platform: str, force: bool = False) -> dict[str, Any]:
    if platform not in PLATFORM_URLS:
        raise ValueError(f"Unsupported platform {platform}")

    raw_path = ROOT / "data" / "raw" / "geo" / platform / f"{platform}_platform_table.txt"
    download(PLATFORM_URLS[platform], raw_path, force=force)

    rows: list[dict[str, str]] = []
    in_table = False
    header: list[str] | None = None
    with raw_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if line == "!platform_table_begin":
                in_table = True
                continue
            if line == "!platform_table_end":
                break
            if not in_table:
                continue
            if header is None:
                header = line.split("\t")
                continue
            values = line.split("\t")
            rows.append(dict(zip(header, values, strict=False)))

    probe_to_gene: dict[str, dict[str, Any]] = {}
    symbol_to_probes: dict[str, list[str]] = defaultdict(list)
    ambiguous_symbol_count = 0
    for row in rows:
        probe_id = row.get("ID", "").strip()
        symbol = first_token(first_present(row, ["Gene Symbol", "Symbol", "GENE_SYMBOL", "gene_assignment"]))
        if not probe_id or not symbol:
            continue
        raw_symbol_field = first_present(row, ["Gene Symbol", "Symbol", "GENE_SYMBOL", "gene_assignment"])
        raw_symbols = [item.strip() for item in raw_symbol_field.split(" /// ") if item.strip() and item != "---"]
        if len(raw_symbols) > 1:
            ambiguous_symbol_count += 1
        symbol = symbol.upper()
        record = {
            "probe_id": probe_id,
            "gene_symbol": symbol,
            "gene_title": first_token(first_present(row, ["Gene Title", "GeneName", "Description"])) or "",
            "entrez_gene": first_token(first_present(row, ["Entrez Gene", "Entrez Gene ID", "ENTREZ_GENE_ID"])),
            "ensembl_gene": first_token(row.get("Ensembl", "")),
            "chromosomal_location": first_token(row.get("Chromosomal Location", "")),
        }
        probe_to_gene[probe_id] = record
        symbol_to_probes[symbol].append(probe_id)

    output_dir = ROOT / "data" / "processed" / platform
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "platform_gene_map.json"
    payload = {
        "platform": platform,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": PLATFORM_URLS[platform],
        "raw_file": file_record(raw_path),
        "probe_count": len(probe_to_gene),
        "gene_count": len(symbol_to_probes),
        "ambiguous_probe_symbol_count": ambiguous_symbol_count,
        "probe_to_gene": probe_to_gene,
        "symbol_to_probes": {symbol: sorted(probes) for symbol, probes in sorted(symbol_to_probes.items())},
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def read_expression_matrix(
    raw_path: Path,
    *,
    matrix_source: str,
) -> tuple[list[str], list[list[str]]]:
    rows: list[list[str]] = []
    opener = gzip.open if raw_path.suffix == ".gz" else open
    with opener(raw_path, "rt", encoding="utf-8", errors="replace", newline="") as handle:
        if matrix_source == "series_matrix_table":
            for line in handle:
                if line.rstrip("\n") == "!series_matrix_table_begin":
                    break
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader)
        for row in reader:
            if not row:
                continue
            if row[0] == "!series_matrix_table_end":
                break
            rows.append(row)
    return [clean_header(value) for value in header], rows


def clean_header(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    return value


def sample_key_for(sample: dict[str, Any], mode: str) -> str:
    if mode == "title_cel":
        return f"{sample['title']}.CEL"
    if mode == "geo_accession":
        return sample["sample_accession"]
    raise ValueError(f"Unsupported sample match mode: {mode}")


def welch_result(values_a: np.ndarray, values_b: np.ndarray) -> dict[str, Any]:
    values_a = values_a[~np.isnan(values_a)]
    values_b = values_b[~np.isnan(values_b)]
    if len(values_a) < 2 or len(values_b) < 2:
        return {"p_value": math.nan, "statistic": math.nan}
    result = stats.ttest_ind(values_a, values_b, equal_var=False, nan_policy="omit")
    return {
        "p_value": float(result.pvalue) if not math.isnan(float(result.pvalue)) else math.nan,
        "statistic": float(result.statistic) if not math.isnan(float(result.statistic)) else math.nan,
    }


def build_expression_summary(accession: str, force: bool = False) -> dict[str, Any]:
    if accession not in NORMALIZED_URLS:
        supported = ", ".join(sorted(NORMALIZED_URLS))
        raise ValueError(f"Unsupported accession {accession}. Supported: {supported}")

    config = STUDY_CONFIG[accession]
    platform = config["platform"]
    platform_map = parse_platform(platform, force=force)
    probe_to_gene = platform_map["probe_to_gene"]

    samples = load_json(ROOT / "data" / "processed" / accession / "samples.json")
    raw_path = ROOT / "data" / "raw" / "geo" / accession / config["matrix_filename"]
    output_dir = ROOT / "data" / "processed" / accession
    output_dir.mkdir(parents=True, exist_ok=True)
    download(NORMALIZED_URLS[accession], raw_path, force=force)

    matrix_sample_to_sample = {sample_key_for(sample, config["sample_match"]): sample for sample in samples}
    sample_ids: list[str] = []
    gene_sums: dict[str, np.ndarray] = {}
    gene_counts: dict[str, np.ndarray] = {}
    gene_meta: dict[str, dict[str, Any]] = {}
    observed_probe_count = 0

    header, matrix_rows = read_expression_matrix(raw_path, matrix_source=config["matrix_source"])
    matrix_sample_columns = header[1:]
    sample_ids = [sample_name.removesuffix(".CEL") for sample_name in matrix_sample_columns if sample_name in matrix_sample_to_sample]
    sample_indices = [index for index, sample_name in enumerate(matrix_sample_columns) if sample_name in matrix_sample_to_sample]
    selected_matrix_sample_names = [matrix_sample_columns[index] for index in sample_indices]
    for row in matrix_rows:
        probe_id = clean_header(row[0])
        mapping = probe_to_gene.get(probe_id)
        if not mapping:
            continue
        symbol = mapping["gene_symbol"]
        if symbol not in gene_sums:
            gene_sums[symbol] = np.zeros(len(sample_indices), dtype=float)
            gene_counts[symbol] = np.zeros(len(sample_indices), dtype=float)
            gene_meta[symbol] = {
                "gene_symbol": symbol,
                "gene_title": mapping.get("gene_title", ""),
                "entrez_gene": mapping.get("entrez_gene"),
                "ensembl_gene": mapping.get("ensembl_gene"),
                "platform": platform,
                "probe_ids": [],
                "mapping_source": "GEO platform annotation",
                "mapping_source_url": PLATFORM_URLS[platform],
            }
        gene_meta[symbol]["probe_ids"].append(probe_id)
        observed_probe_count += 1
        values = []
        for index in sample_indices:
            value = row[index + 1] if index + 1 < len(row) else ""
            values.append(float(value) if value not in {"", "NA", "null"} else math.nan)
        vector = np.array(values, dtype=float)
        mask = ~np.isnan(vector)
        gene_sums[symbol][mask] += vector[mask]
        gene_counts[symbol][mask] += 1

    sample_states = [matrix_sample_to_sample[name]["clinical_state"] for name in selected_matrix_sample_names]
    indices_by_state: dict[str, list[int]] = defaultdict(list)
    for index, state in enumerate(sample_states):
        indices_by_state[state].append(index)

    gene_vectors: dict[str, np.ndarray] = {}
    gene_sample_payload: dict[str, dict[str, float]] = {}
    gene_summaries: dict[str, Any] = {}
    contrast_rows: dict[str, list[dict[str, Any]]] = {f"{case}_vs_{control}": [] for case, control in config["contrasts"]}

    for symbol in sorted(gene_sums):
        values = np.divide(
            gene_sums[symbol],
            gene_counts[symbol],
            out=np.full_like(gene_sums[symbol], np.nan),
            where=gene_counts[symbol] != 0,
        )
        gene_vectors[symbol] = values
        gene_sample_payload[symbol] = {
            sample_id: round(float(value), 4)
            for sample_id, value in zip(sample_ids, values, strict=True)
            if not math.isnan(float(value))
        }

        group_summary = {
            state: summarize_values([float(values[index]) for index in indices])
            for state, indices in sorted(indices_by_state.items())
        }
        contrasts: dict[str, Any] = {}
        for case, control in config["contrasts"]:
            contrast_id = f"{case}_vs_{control}"
            if case not in indices_by_state or control not in indices_by_state:
                continue
            case_values = values[indices_by_state[case]]
            control_values = values[indices_by_state[control]]
            case_clean = case_values[~np.isnan(case_values)]
            control_clean = control_values[~np.isnan(control_values)]
            test = welch_result(case_values, control_values)
            mean_case = float(np.mean(case_clean)) if len(case_clean) else math.nan
            mean_control = float(np.mean(control_clean)) if len(control_clean) else math.nan
            delta = mean_case - mean_control if not math.isnan(mean_case) and not math.isnan(mean_control) else math.nan
            row = {
                "gene_symbol": symbol,
                "gene_title": gene_meta[symbol]["gene_title"],
                "case_state": case,
                "control_state": control,
                "n_case": int(len(case_clean)),
                "n_control": int(len(control_clean)),
                "mean_case": round(mean_case, 4) if not math.isnan(mean_case) else math.nan,
                "mean_control": round(mean_control, 4) if not math.isnan(mean_control) else math.nan,
                "mean_difference_log2_scale": round(delta, 4) if not math.isnan(delta) else math.nan,
                "fold_change_approx": round(math.pow(2, delta), 4) if not math.isnan(delta) else math.nan,
                "welch_t": round(test["statistic"], 4) if not math.isnan(test["statistic"]) else math.nan,
                "p_value": test["p_value"],
            }
            contrasts[contrast_id] = row
            contrast_rows[contrast_id].append(row)

        gene_summaries[symbol] = {
            **gene_meta[symbol],
            "assay_scale": config["assay_scale"],
            "sample_count": int(np.sum(~np.isnan(values))),
            "probe_count": len(gene_meta[symbol]["probe_ids"]),
            "probe_ids": sorted(gene_meta[symbol]["probe_ids"]),
            "group_summary": group_summary,
            "contrasts": contrasts,
        }

    for contrast_id, rows in contrast_rows.items():
        valid_indices = [index for index, row in enumerate(rows) if not math.isnan(float(row["p_value"]))]
        p_values = [rows[index]["p_value"] for index in valid_indices]
        fdr_values = multipletests(p_values, method="fdr_bh")[1] if p_values else []
        for row in rows:
            row["adj_p_value_bh"] = math.nan
        for index, fdr in zip(valid_indices, fdr_values, strict=True):
            rows[index]["adj_p_value_bh"] = float(fdr)
        for row in rows:
            symbol = row["gene_symbol"]
            gene_summaries[symbol]["contrasts"][contrast_id]["adj_p_value_bh"] = row["adj_p_value_bh"]

    expression_payload = {
        "study_accession": accession,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": NORMALIZED_URLS[accession],
        "platform": platform,
        "assay_scale": config["assay_scale"],
        "sample_count": len(sample_ids),
        "gene_count": len(gene_summaries),
        "observed_platform_probe_count": observed_probe_count,
        "contrast_method": "Welch two-sample t-test on gene-level within-study expression values; Benjamini-Hochberg FDR within each contrast.",
        "raw_path": str(raw_path.relative_to(ROOT)),
        "genes": gene_summaries,
    }
    output_path = output_dir / "gene_expression_summary.json"
    output_path.write_text(json.dumps(expression_payload, indent=2, allow_nan=True) + "\n", encoding="utf-8")

    sample_value_path = output_dir / "gene_sample_values.json"
    sample_value_path.write_text(json.dumps(gene_sample_payload, separators=(",", ":"), allow_nan=True) + "\n", encoding="utf-8")

    differential_payload = {
        "study_accession": accession,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": expression_payload["contrast_method"],
        "contrasts": {
            contrast_id: sorted(rows, key=lambda row: (math.inf if math.isnan(float(row["adj_p_value_bh"])) else row["adj_p_value_bh"]))
            for contrast_id, rows in contrast_rows.items()
        },
    }
    differential_path = output_dir / "differential_expression.json"
    differential_path.write_text(json.dumps(differential_payload, indent=2, allow_nan=True) + "\n", encoding="utf-8")

    provenance_path = output_dir / "analysis_provenance.json"
    output_records = [file_record(output_path), file_record(sample_value_path), file_record(differential_path)]
    provenance_payload = {
        "study_accession": accession,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "parser": "scripts/build_gene_evidence.py",
        "processing_code_version": "full-platform-gene-expression-v2",
        "source_files": {
            "normalized_expression": {
                "url": NORMALIZED_URLS[accession],
                **file_record(raw_path),
            },
            "platform_annotation": {
                "url": PLATFORM_URLS[platform],
                **platform_map["raw_file"],
            },
        },
        "outputs": output_records,
        "methods": [
            f"GEO {platform} platform table parsed from !platform_table_begin/!platform_table_end.",
            "Probe sets mapped to the first non-empty Gene Symbol entry; probes with ambiguous symbols are counted in platform metadata.",
            "Multiple probes per gene are averaged per sample before group summaries and contrasts.",
            "Welch two-sample t-test is computed on gene-level within-study expression values; Benjamini-Hochberg FDR is applied within each contrast.",
        ],
        "limitations": config["limitations"],
    }
    provenance_path.write_text(json.dumps(provenance_payload, indent=2) + "\n", encoding="utf-8")

    return {
        "accession": accession,
        "platform": platform,
        "gene_count": len(gene_summaries),
        "sample_count": len(sample_ids),
        "observed_platform_probe_count": observed_probe_count,
        "output_path": str(output_path.relative_to(ROOT)),
        "sample_value_path": str(sample_value_path.relative_to(ROOT)),
        "differential_path": str(differential_path.relative_to(ROOT)),
        "analysis_provenance_path": str(provenance_path.relative_to(ROOT)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build gene-level expression evidence for a processed study.")
    parser.add_argument("accession", choices=sorted(STUDY_CONFIG))
    parser.add_argument("--force", action="store_true", help="Redownload the normalized matrix/platform table even if cached.")
    args = parser.parse_args()
    print(json.dumps(build_expression_summary(args.accession, force=args.force), indent=2))


if __name__ == "__main__":
    main()
