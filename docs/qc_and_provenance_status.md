# QC and Provenance Status

This page summarizes the current state of QC and provenance coverage in LiverTx-OmicsDB.

## Current Coverage

The resource already has a meaningful amount of processed coverage:

- multiple studies expose sample summaries
- many studies expose downloadable processed artifacts
- provenance is available for a substantial subset of processed layers

That means QC and provenance are no longer abstract plans. They are partially implemented resource capabilities.

## What Is Working Now

The strongest current pieces are:

1. processed sample summaries for the main transcriptomic and non-transcriptomic evidence layers
2. downloadable artifact registries for processed studies
3. provenance files for many processed studies and feature layers

## What Is Still Missing

The biggest remaining gaps are:

1. dedicated study-level QC pages
2. a unified release-level provenance summary
3. a user-facing explanation of how QC differs across transcriptome, proteome, metabolome, microbiome, and single-cell layers

## Why This Matters

For a database resource, QC and provenance are not back-office implementation details. They determine whether a reviewer or collaborator can tell:

- which layers are reusable
- which results are exploratory
- what was downloaded and processed
- what still remains unresolved

## Immediate Next Steps

1. add a unified reviewer-facing QC/provenance page
2. expose per-study QC status alongside downloads and provenance
3. add release-level provenance summary for the current build
