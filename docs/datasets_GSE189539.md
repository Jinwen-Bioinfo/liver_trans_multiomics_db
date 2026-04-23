# GSE189539 single-cell graft liver marker evidence

## Scope

GSE189539 is a public GEO single-cell RNA-seq study of human liver transplantation samples collected before liver transplantation during cold perfusion and after portal reperfusion. The processed V1 layer uses the public filtered count matrix from GEO.

## What is processed

- 8 registered graft-liver samples.
- 58,243 cells in the public filtered gene-count matrix.
- 26 pre-specified marker genes covering EAD immune niche, T/NK cytotoxicity, neutrophil inflammation, myeloid, endothelial, and hepatocyte programs.
- Whole-matrix marker summaries: detected cell count, percent detected cells, mean UMI per cell, and mean log1p UMI per cell.
- Marker-program summaries for queryable single-cell mechanism evidence.

## Important limitation

The GEO filtered matrix column IDs do not expose sample accessions, and the GEO record does not provide a reusable cell metadata table with sample or cell-type annotations. Therefore V1 does **not** compute sample-level, before/after, cell-type, or rejection-outcome contrasts for this dataset. It is a marker-level single-cell evidence layer, not a full reanalysis.

## API examples

- `/api/features/NKG7/single-cell`
- `/api/features/S100A12/single-cell`
- `/api/studies/GSE189539/single-cell/modules`
- `/api/studies/GSE189539/downloads`
