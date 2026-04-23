from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "discovery"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEARCH_TERMS = [
    "liver transplant",
    "liver transplantation",
    "liver allograft",
    "hepatic allograft",
    "INTERLIVER",
    "post-transplant NASH",
    "liver transplant rejection",
    "liver transplant biopsy",
    "liver transplant microbiome",
    "liver transplant metabolomics",
    "liver transplant proteomics",
    "liver transplant single cell",
    "liver transplant cell-free DNA",
]

NCBI_SEARCHES = {
    "gds_liver_transplant": ("gds", '("liver transplantation" OR "liver transplant")'),
    "gds_liver_allograft": ("gds", '("liver allograft" OR "hepatic allograft")'),
    "sra_liver_transplant": ("sra", '("liver transplantation" OR "liver transplant")'),
    "bioproject_liver_transplant": ("bioproject", '("liver transplantation" OR "liver transplant")'),
    "pubmed_liver_transplant_omics": (
        "pubmed",
        '("liver transplantation" OR "liver transplant") AND '
        "(transcriptomics OR transcriptome OR RNA-seq OR proteomics OR metabolomics OR microbiome OR metagenomics OR single-cell OR methylation)",
    ),
}

DIRECT_PATTERNS = [
    "liver transplant",
    "liver transplantation",
    "liver allograft",
    "hepatic allograft",
    "interliver",
    "transplant biops",
]
MODALITY_KEYWORDS = {
    "bulk_transcriptomics": ["transcriptom", "rna-seq", "rna seq", "expression", "microarray"],
    "single_cell": ["single-cell", "single cell", "scrna", "snrna"],
    "methylation_cfDNA": ["methylat", "cell-free", "cfdna", "bisulfite"],
    "proteomics": ["proteom", "protein"],
    "metabolomics": ["metabolom", "metabolite", "bile acid", "short-chain fatty acid", "scfa"],
    "microbiome": ["microbiome", "metagenom", "metaphlan", "taxon", "pathobiont"],
    "small_rna": ["small rna", "mirna", "microrna", "exosome"],
}


def fetch_json(url: str, timeout: int = 60) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "LiverTx-OmicsDB-discovery/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def ncbi_url(db: str, endpoint: str, **params: Any) -> str:
    base = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/{endpoint}.fcgi"
    params["db"] = db
    params["retmode"] = "json"
    return base + "?" + urllib.parse.urlencode(params)


def clean_text(*values: Any) -> str:
    return " ".join(str(value or "") for value in values).lower()


def classify_directness(text: str) -> str:
    if any(pattern in text for pattern in DIRECT_PATTERNS):
        return "direct_liver_transplant"
    if "transplant" in text and "liver" in text:
        return "probable_liver_transplant"
    if "liver" in text:
        return "liver_reference_or_adjacent"
    if "transplant" in text:
        return "non_liver_transplant_adjacent"
    return "background_or_false_positive"


def classify_modalities(text: str, existing: list[str] | None = None) -> list[str]:
    labels = set(existing or [])
    for label, keywords in MODALITY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            labels.add(label)
    return sorted(labels) or ["unknown"]


def normalize_accession(accession: str) -> str:
    accession = accession.strip()
    accession = accession.replace("E-GEOD-", "GSE")
    return accession


def add_candidate(candidates: dict[str, dict[str, Any]], candidate: dict[str, Any]) -> None:
    accession = normalize_accession(candidate["accession"])
    text = clean_text(candidate.get("title"), candidate.get("description"), candidate.get("repository"))
    existing = candidates.get(accession, {})
    sources = sorted(set(existing.get("discovered_via", [])) | set(candidate.get("discovered_via", [])))
    merged = {
        **existing,
        **candidate,
        "accession": accession,
        "discovered_via": sources,
        "directness": classify_directness(text),
        "inferred_modalities": classify_modalities(text, candidate.get("omics_modalities")),
    }
    if existing.get("description") and candidate.get("description"):
        merged["description"] = existing["description"] if len(existing["description"]) >= len(candidate["description"]) else candidate["description"]
    candidates[accession] = merged


def discover_omicsdi(candidates: dict[str, dict[str, Any]], queries: list[str]) -> list[dict[str, Any]]:
    summaries = []
    for query in queries:
        url = "https://www.omicsdi.org/ws/dataset/search?" + urllib.parse.urlencode({"query": query, "size": 100})
        try:
            payload = fetch_json(url)
        except (HTTPError, URLError, TimeoutError) as exc:
            summaries.append({"source": "OmicsDI", "query": query, "count": None, "url": url, "error": str(exc)})
            continue
        summaries.append({"source": "OmicsDI", "query": query, "count": payload.get("count"), "url": url})
        for record in payload.get("datasets", []):
            accession = record.get("id")
            if not accession:
                continue
            add_candidate(
                candidates,
                {
                    "accession": accession,
                    "repository": record.get("source", "OmicsDI"),
                    "repository_url": f"https://www.omicsdi.org/dataset/{record.get('source')}/{accession}",
                    "title": record.get("title", ""),
                    "description": record.get("description", ""),
                    "organisms": [item.get("name") for item in (record.get("organisms") or []) if item.get("name")],
                    "omics_modalities": record.get("omicsType", []),
                    "publication_date": record.get("publicationDate"),
                    "discovered_via": [f"OmicsDI:{query}"],
                },
            )
    return summaries


def discover_ncbi(candidates: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for label, (db, term) in NCBI_SEARCHES.items():
        search_url = ncbi_url(db, "esearch", term=term, retmax=100)
        try:
            search = fetch_json(search_url)
        except (HTTPError, URLError, TimeoutError) as exc:
            summaries.append({"source": f"NCBI:{db}", "query": label, "count": None, "url": search_url, "error": str(exc)})
            continue
        ids = search.get("esearchresult", {}).get("idlist", [])
        count = int(search.get("esearchresult", {}).get("count", 0))
        summaries.append({"source": f"NCBI:{db}", "query": label, "count": count, "url": search_url})
        if db == "gds" and ids:
            for start in range(0, len(ids), 50):
                chunk = ids[start : start + 50]
                summary_url = ncbi_url(db, "esummary", id=",".join(chunk))
                try:
                    summary = fetch_json(summary_url)
                except (HTTPError, URLError, TimeoutError) as exc:
                    summaries.append({"source": f"NCBI:{db}", "query": f"{label}:summary", "count": None, "url": summary_url, "error": str(exc)})
                    continue
                for uid in summary.get("result", {}).get("uids", []):
                    record = summary["result"][uid]
                    accession = record.get("accession")
                    if not accession:
                        continue
                    add_candidate(
                        candidates,
                        {
                            "accession": accession,
                            "repository": "GEO",
                            "repository_url": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}",
                            "title": record.get("title", ""),
                            "description": record.get("summary", ""),
                            "organisms": [record.get("taxon")] if record.get("taxon") else [],
                            "omics_modalities": [],
                            "publication_date": record.get("PDAT"),
                            "discovered_via": [f"NCBI:{label}"],
                        },
                    )
                time.sleep(0.34)
        time.sleep(0.34)
    return summaries


def main() -> None:
    candidates: dict[str, dict[str, Any]] = {}
    search_summaries = []
    search_summaries.extend(discover_omicsdi(candidates, SEARCH_TERMS))
    search_summaries.extend(discover_ncbi(candidates))

    candidate_list = sorted(
        candidates.values(),
        key=lambda item: (
            {
                "direct_liver_transplant": 0,
                "probable_liver_transplant": 1,
                "liver_reference_or_adjacent": 2,
                "non_liver_transplant_adjacent": 3,
                "background_or_false_positive": 4,
            }.get(item.get("directness"), 9),
            item.get("accession", ""),
        ),
    )
    direct = [item for item in candidate_list if item["directness"] == "direct_liver_transplant"]
    probable = [item for item in candidate_list if item["directness"] == "probable_liver_transplant"]
    adjacent = [item for item in candidate_list if item["directness"] == "liver_reference_or_adjacent"]
    modality_counts = Counter(modality for item in candidate_list for modality in item.get("inferred_modalities", []))
    direct_modality_counts = Counter(modality for item in direct for modality in item.get("inferred_modalities", []))

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Public liver transplantation and liver-allograft omics dataset discovery across OmicsDI and NCBI/GEO/SRA/BioProject/PubMed.",
        "search_summaries": search_summaries,
        "candidate_count": len(candidate_list),
        "direct_liver_transplant_candidate_count": len(direct),
        "probable_liver_transplant_candidate_count": len(probable),
        "liver_reference_or_adjacent_candidate_count": len(adjacent),
        "modality_counts_all_candidates": dict(sorted(modality_counts.items())),
        "modality_counts_direct_liver_transplant": dict(sorted(direct_modality_counts.items())),
        "direct_liver_transplant_candidates": direct,
        "probable_liver_transplant_candidates": probable,
        "liver_reference_or_adjacent_candidates": adjacent[:100],
        "all_candidates": candidate_list,
        "limitations": [
            "Automated discovery is intentionally broad and includes false positives; directness must be manually curated before registry promotion.",
            "Counts from repository search APIs are query-hit counts, not unique ingest-ready datasets.",
            "Controlled-access human data and supplementary-only data may require manual follow-up outside repository APIs.",
        ],
    }
    output_path = OUT_DIR / "public_liver_tx_dataset_discovery.json"
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output_path": str(output_path.relative_to(ROOT)),
        "candidate_count": payload["candidate_count"],
        "direct_liver_transplant_candidate_count": payload["direct_liver_transplant_candidate_count"],
        "probable_liver_transplant_candidate_count": payload["probable_liver_transplant_candidate_count"],
        "modality_counts_direct_liver_transplant": payload["modality_counts_direct_liver_transplant"],
    }, indent=2))


if __name__ == "__main__":
    main()
