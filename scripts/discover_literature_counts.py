from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "discovery"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_ENTITY = '("Liver Transplantation"[Mesh] OR "liver transplant*"[tiab] OR "hepatic transplant*"[tiab] OR "liver allograft*"[tiab] OR "hepatic allograft*"[tiab])'
QUERIES = {
    "liver_transplant_all_broad": BASE_ENTITY,
    "liver_transplant_omics_any": f"({BASE_ENTITY} AND (omics[tiab] OR multiomics[tiab] OR \"multi-omics\"[tiab] OR transcriptom*[tiab] OR proteom*[tiab] OR metabolom*[tiab] OR metagenom*[tiab] OR microbiom*[tiab] OR \"single-cell\"[tiab] OR \"single cell\"[tiab] OR scRNA[tiab] OR methylom*[tiab] OR epigenom*[tiab] OR \"cell-free DNA\"[tiab] OR cfDNA[tiab] OR \"gene expression\"[tiab] OR microarray[tiab] OR \"RNA-seq\"[tiab] OR sequencing[tiab]))",
    "gene_expression_transcriptomics": f"({BASE_ENTITY} AND (transcriptom*[tiab] OR \"gene expression\"[tiab] OR microarray[tiab] OR \"RNA-seq\"[tiab] OR \"RNA seq\"[tiab] OR \"messenger RNA\"[tiab]))",
    "single_cell": f"({BASE_ENTITY} AND (\"single-cell\"[tiab] OR \"single cell\"[tiab] OR scRNA[tiab] OR snRNA[tiab] OR \"single-nucleus\"[tiab] OR \"single nucleus\"[tiab]))",
    "proteomics": f"({BASE_ENTITY} AND (proteom*[tiab] OR peptidom*[tiab] OR \"mass spectrometry\"[tiab]))",
    "metabolomics": f"({BASE_ENTITY} AND (metabolom*[tiab] OR metabonom*[tiab] OR metabolite*[tiab] OR \"bile acid*\"[tiab] OR lipidom*[tiab]))",
    "microbiome": f"({BASE_ENTITY} AND (microbiom*[tiab] OR microbiota[tiab] OR metagenom*[tiab] OR pathobiont*[tiab] OR dysbiosis[tiab]))",
    "methylation_cfdna_epigenomics": f"({BASE_ENTITY} AND (methylom*[tiab] OR methylation[tiab] OR epigenom*[tiab] OR \"cell-free DNA\"[tiab] OR cfDNA[tiab] OR \"donor-derived cell-free DNA\"[tiab] OR ddcfDNA[tiab]))",
    "genomics_variants_hla": f"({BASE_ENTITY} AND (genom*[tiab] OR polymorphism*[tiab] OR variant*[tiab] OR SNP[tiab] OR HLA[tiab] OR histocompatib*[tiab]))",
    "spatial_pathology_imaging_omics": f"({BASE_ENTITY} AND (spatial[tiab] OR histopatholog*[tiab] OR pathology[tiab] OR imaging[tiab]) AND (omics[tiab] OR transcriptom*[tiab] OR proteom*[tiab] OR metabolom*[tiab]))",
    "multiomics_explicit": f"({BASE_ENTITY} AND (multiomics[tiab] OR \"multi-omics\"[tiab] OR \"multi omics\"[tiab]))",
}


def esearch_count(term: str, *, year: int | None = None) -> dict[str, object]:
    params = {"db": "pubmed", "term": term, "retmode": "json", "retmax": 5, "sort": "relevance"}
    if year is not None:
        params.update({"mindate": str(year), "maxdate": str(year), "datetype": "pdat", "retmax": 0})
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = json.load(response)
    result = payload["esearchresult"]
    return {
        "count": int(result["count"]),
        "top_pmids": result.get("idlist", []),
        "url": url,
    }


def main() -> None:
    counts = {name: {"query": query, **esearch_count(query)} for name, query in QUERIES.items()}
    omics_year_counts = {}
    for year in range(2000, 2027):
        count = esearch_count(QUERIES["liver_transplant_omics_any"], year=year)["count"]
        if count:
            omics_year_counts[str(year)] = count
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "NCBI PubMed E-utilities esearch",
        "counts": counts,
        "omics_any_year_counts": omics_year_counts,
        "interpretation_notes": [
            "PubMed counts are literature hit counts, not unique public datasets.",
            "Broad omics terms include adjacent liver disease, transplant medicine, biomarker, and review articles.",
            "Dataset-ready studies require a second pass for accession, supplementary table, controlled-access status, and reusable matrix availability.",
        ],
    }
    output_path = OUT_DIR / "pubmed_liver_tx_omics_literature_counts.json"
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output_path": str(output_path.relative_to(ROOT)),
        "liver_transplant_all_broad": counts["liver_transplant_all_broad"]["count"],
        "liver_transplant_omics_any": counts["liver_transplant_omics_any"]["count"],
        "multiomics_explicit": counts["multiomics_explicit"]["count"],
    }, indent=2))


if __name__ == "__main__":
    main()
