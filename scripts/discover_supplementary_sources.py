from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "discovery"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_ENTITY = '("liver transplant" OR "liver transplantation" OR "liver allograft" OR "hepatic allograft")'
QUERIES = {
    "supplementary_liver_tx_omics_broad": f"{BASE_ENTITY} AND (omics OR transcriptomics OR proteomics OR metabolomics OR microbiome OR methylation OR cfDNA) HAS_SUPPL:y",
    "supplementary_liver_tx_transcriptomics": f"{BASE_ENTITY} AND (transcriptomics OR transcriptome OR \"gene expression\" OR \"RNA-seq\") HAS_SUPPL:y",
    "supplementary_liver_tx_proteomics": f"{BASE_ENTITY} AND (proteomics OR proteome OR \"mass spectrometry\") HAS_SUPPL:y",
    "supplementary_liver_tx_metabolomics": f"{BASE_ENTITY} AND (metabolomics OR metabolome OR metabolite OR \"bile acid\" OR lipidomics) HAS_SUPPL:y",
    "supplementary_liver_tx_microbiome": f"{BASE_ENTITY} AND (microbiome OR microbiota OR metagenomics OR dysbiosis) HAS_SUPPL:y",
    "supplementary_liver_tx_cfdna_methylation": f"{BASE_ENTITY} AND (methylation OR methylome OR epigenomics OR \"cell-free DNA\" OR cfDNA) HAS_SUPPL:y",
    "supplementary_liver_tx_multiomics_explicit": f"{BASE_ENTITY} AND (multiomics OR \"multi-omics\" OR \"multi omics\") HAS_SUPPL:y",
}


def europepmc_search(query: str, page_size: int = 25) -> dict[str, Any]:
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
        {"query": query, "format": "json", "pageSize": page_size}
    )
    request = urllib.request.Request(url, headers={"User-Agent": "LiverTx-OmicsDB-supplementary-discovery/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    records = []
    for item in payload.get("resultList", {}).get("result", []):
        records.append(
            {
                "pmid": item.get("pmid"),
                "pmcid": item.get("pmcid"),
                "doi": item.get("doi"),
                "title": item.get("title"),
                "journal": item.get("journalTitle"),
                "year": item.get("pubYear"),
                "is_open_access": item.get("isOpenAccess"),
                "source": item.get("source"),
                "cited_by_count": item.get("citedByCount"),
            }
        )
    return {"count": int(payload.get("hitCount", 0)), "url": url, "top_records": records}


def main() -> None:
    results = {name: {"query": query, **europepmc_search(query)} for name, query in QUERIES.items()}
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Europe PMC REST search with HAS_SUPPL:y",
        "results": results,
        "interpretation_notes": [
            "HAS_SUPPL:y indicates supplementary material availability, not necessarily reusable tables.",
            "Europe PMC broad text queries can include adjacent liver disease or transplant literature; manual triage is required.",
            "Records with PMCID/open access are often easiest to inspect programmatically for supplementary file links.",
        ],
    }
    output_path = OUT_DIR / "supplementary_source_discovery.json"
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output_path": str(output_path.relative_to(ROOT)),
                "supplementary_liver_tx_omics_broad": results["supplementary_liver_tx_omics_broad"]["count"],
                "supplementary_liver_tx_multiomics_explicit": results["supplementary_liver_tx_multiomics_explicit"]["count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
