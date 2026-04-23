from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.data_loader import (
    available_study_downloads,
    filter_study_samples,
    get_study,
    get_download_path,
    get_dataset_triage,
    get_multiomics_feature,
    load_data_model_schema,
    list_studies,
    list_dataset_triage,
    load_study_provenance,
    load_study_sample_summary,
    load_study_samples,
    get_feature_expression,
    get_feature_protein,
    get_feature_single_cell,
    get_signature_score,
    get_single_cell_modules,
    get_use_case,
    get_multiomics_source,
    get_omics_layer,
    list_source_types,
    list_signature_scores,
    list_multiomics_features,
    list_multiomics_sources,
    list_omics_layers,
    nar_readiness,
    list_use_cases,
    search_entities,
)


app = FastAPI(
    title="LiverTx-OmicsDB",
    description="Public multi-omics evidence resource for liver transplantation.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", include_in_schema=False)
def portal() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "resource": "LiverTx-OmicsDB"}


@app.get("/api/studies")
def studies(
    query: str | None = None,
    modality: str | None = None,
    clinical_state: str | None = None,
    sample_origin: str | None = None,
) -> dict[str, object]:
    items = list_studies(
        query=query,
        modality=modality,
        clinical_state=clinical_state,
        sample_origin=sample_origin,
    )
    return {"count": len(items), "studies": items}


@app.get("/api/studies/{accession}")
def study_detail(accession: str) -> dict[str, object]:
    study = get_study(accession)
    if study is None:
        raise HTTPException(status_code=404, detail="Study accession not registered")
    summary = load_study_sample_summary(accession)
    if summary:
        return {**study, "sample_summary": summary}
    return study


@app.get("/api/studies/{accession}/samples")
def study_samples(
    accession: str,
    clinical_state: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, object]:
    if get_study(accession) is None:
        raise HTTPException(status_code=404, detail="Study accession not registered")
    return filter_study_samples(
        accession,
        clinical_state=clinical_state,
        limit=limit,
        offset=offset,
    )


@app.get("/api/studies/{accession}/provenance")
def study_provenance(accession: str) -> dict[str, object]:
    if get_study(accession) is None:
        raise HTTPException(status_code=404, detail="Study accession not registered")
    provenance = load_study_provenance(accession)
    if provenance is None:
        raise HTTPException(status_code=404, detail="No processed provenance available")
    return provenance


@app.get("/api/studies/{accession}/downloads")
def study_downloads(accession: str) -> dict[str, object]:
    if get_study(accession) is None:
        raise HTTPException(status_code=404, detail="Study accession not registered")
    downloads = available_study_downloads(accession)
    return {"count": len(downloads), "downloads": downloads}


@app.get("/api/studies/{accession}/downloads/{artifact}")
def study_download(accession: str, artifact: str) -> FileResponse:
    if get_study(accession) is None:
        raise HTTPException(status_code=404, detail="Study accession not registered")
    path = get_download_path(accession, artifact)
    if path is None:
        raise HTTPException(status_code=404, detail="Artifact is not available")
    return FileResponse(path, filename=path.name, media_type="application/json")


@app.get("/api/search")
def search(query: str = Query(..., min_length=1)) -> dict[str, object]:
    return {"query": query, "results": search_entities(query)}


@app.get("/api/use-cases")
def use_cases() -> dict[str, object]:
    items = list_use_cases()
    return {"count": len(items), "use_cases": items}


@app.get("/api/use-cases/{use_case_id}")
def use_case_detail(use_case_id: str) -> dict[str, object]:
    item = get_use_case(use_case_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Use case is not registered")
    return item


@app.get("/api/omics-layers")
def omics_layers() -> dict[str, object]:
    items = list_omics_layers()
    return {"count": len(items), "omics_layers": items}


@app.get("/api/omics-layers/{layer_id}")
def omics_layer_detail(layer_id: str) -> dict[str, object]:
    item = get_omics_layer(layer_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Omics layer is not registered")
    return item


@app.get("/api/multiomics-sources")
def multiomics_sources(layer: str | None = None) -> dict[str, object]:
    items = list_multiomics_sources(layer=layer)
    return {"count": len(items), "sources": items}


@app.get("/api/multiomics-sources/{source_id}")
def multiomics_source_detail(source_id: str) -> dict[str, object]:
    item = get_multiomics_source(source_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Multi-omics source is not registered")
    return item


@app.get("/api/multiomics-features")
def multiomics_features(
    query: str | None = None,
    modality: str | None = None,
    feature_type: str | None = None,
    source_id: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, object]:
    return list_multiomics_features(
        query=query,
        modality=modality,
        feature_type=feature_type,
        source_id=source_id,
        limit=limit,
        offset=offset,
    )


@app.get("/api/multiomics-features/{source_id}/{feature_type}/{feature_id}")
def multiomics_feature_detail(source_id: str, feature_type: str, feature_id: str) -> dict[str, object]:
    feature = get_multiomics_feature(source_id, feature_type, feature_id)
    if feature is None:
        raise HTTPException(status_code=404, detail="Multi-omics feature is not available")
    return feature


@app.get("/api/source-types")
def source_types() -> dict[str, object]:
    return list_source_types()


@app.get("/api/data-model")
def data_model() -> dict[str, object]:
    return load_data_model_schema()


@app.get("/api/dataset-triage")
def dataset_triage(
    status: str | None = None,
    priority: str | None = None,
    modality: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, object]:
    return list_dataset_triage(
        status=status,
        priority=priority,
        modality=modality,
        limit=limit,
        offset=offset,
    )


@app.get("/api/dataset-triage/{accession}")
def dataset_triage_detail(accession: str) -> dict[str, object]:
    item = get_dataset_triage(accession)
    if item is None:
        raise HTTPException(status_code=404, detail="Dataset triage record is not available")
    return item


@app.get("/api/features/{symbol}/expression")
def feature_expression(symbol: str) -> dict[str, object]:
    return get_feature_expression(symbol)


@app.get("/api/features/{symbol}/single-cell")
def feature_single_cell(symbol: str) -> dict[str, object]:
    return get_feature_single_cell(symbol)


@app.get("/api/features/{symbol}/protein")
def feature_protein(symbol: str) -> dict[str, object]:
    return get_feature_protein(symbol)


@app.get("/api/studies/{accession}/single-cell/modules")
def study_single_cell_modules(accession: str) -> dict[str, object]:
    modules = get_single_cell_modules(accession)
    if modules is None:
        raise HTTPException(status_code=404, detail="Single-cell module evidence is not available")
    return modules


@app.get("/api/signatures")
def signatures() -> dict[str, object]:
    return list_signature_scores()


@app.get("/api/signatures/{signature_id}/scores")
def signature_scores(signature_id: str) -> dict[str, object]:
    return get_signature_score(signature_id)


@app.get("/api/nar/readiness")
def readiness() -> dict[str, object]:
    return nar_readiness()
