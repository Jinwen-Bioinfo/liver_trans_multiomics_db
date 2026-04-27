# PXD010812: Direct liver-transplant ischemia/reperfusion proteomics candidate

## Why this source matters

`PXD010812` is one of the strongest unresolved direct-proteomics candidates in the current liver-transplant build queue. It is tied to human graft ischemia/reperfusion injury rather than an adjacent liver-disease context, and PRIDE exposes a reusable processed-results archive instead of raw spectra only.

This makes it scientifically attractive for:

- graft ischemia/reperfusion biology
- early injury versus immune activation context
- direct liver-tissue proteomics evidence aligned with the transplant procedure itself

## Public evidence confirmed

- PRIDE project: `https://www.ebi.ac.uk/pride/archive/projects/PXD010812`
- ProteomeXchange title: `A comprehensive and combined analysis of transcriptome and proteome reveals key factors of ischemia-reperfusion injury in human liver transplantation`
- ATC abstract: `https://atcmeetingabstracts.com/abstract/comprehensive-and-combined-transcriptomic-and-proteomic-analysis-reveals-key-factors-underlying-ischemia-reperfusion-injury-in-human-liver-transplantation/`

The abstract explicitly states that the group performed proteomic analysis on ischemic and reperfused liver samples. It also reports validation in `10 matched clinical samples`, which supports a paired graft-biopsy design rather than a loose cross-sectional cohort.

## What is already recoverable

The PRIDE file list includes a processed result archive:

- `search.zip`

PRIDE's official file API shows the archive size is `585,961,505` bytes and the archive structure contains three MaxQuant result batches:

- `TQ01`
- `TQ02`
- `TQ03`

Using the ZIP central directory and targeted byte-range recovery, the following files are confirmed inside each batch:

- `proteinGroups.txt`
- `evidence.txt`
- `summary.txt`
- `peptides.txt`
- `msms.txt`
- `parameters.txt`
- `mqpar.xml`
- `tables.pdf`

So this is not a raw-only PRIDE submission.

Additional recovered design facts:

- each batch contains `18` LC-MS fractions
- MaxQuant was run in `Reporter ion MS2` mode
- `mqpar.xml` confirms `TMT6plex` reporter definitions, but only four reporter channels are active in this run:
  - `126`
  - `127`
  - `128`
  - `130`
- the complete PRIDE archive is locally readable and contains valid `mqpar.xml`, `summary.txt`, and `proteinGroups.txt` files for all three batches
- `proteinGroups.txt` exposes `Reporter intensity 0/1/2/3` columns for every batch, confirming that the reusable quantitative signal is reporter-channel based rather than only peptide-identification metadata

## Current blocker

The remaining blocker is no longer file availability. The blocker is the experimental-design mapping needed to turn reporter intensities into biologically valid contrasts.

What still needs to be resolved:

- which reporter channels correspond to ischemic graft samples
- which reporter channels correspond to reperfused graft samples
- whether any channels are pooled references or internal controls
- whether `TQ01`, `TQ02`, and `TQ03` are biological replicates, technical batches, or mixed designs
- whether the three MaxQuant batches can be merged without introducing ambiguous sample duplication

Critically, the recovered `mqpar.xml` files leave the `<experiments>` block empty, so the batch-level MaxQuant parameters do not record sample-group labels. `tables.pdf` is the generic MaxQuant column-definition manual, not an experiment-design sheet.

## What can now be inferred, but not yet claimed as ground truth

The public article figures and the now-readable PRIDE archive push the dataset closer to usability than before:

- the ATC abstract and workflow figure explicitly frame the proteomic comparison as **re-perfused livers versus pre-implantation livers**
- many named proteins from the co-regulation figure (`HBB`, `HBG2`, `CA1`, `SLC4A1`, `PLIN2`, `JUNB`, `HBA1`, `MMP9`, `SLC2A1`, `PADI4`) show a repeated within-batch pattern
- in nearly all of those examples:
  - `Reporter intensity 1 > Reporter intensity 0`
  - `Reporter intensity 3 > Reporter intensity 2`

That pattern strongly suggests a paired layout within each batch, most plausibly:

- one pre-implantation / reperfused pair in channels `0 -> 1`
- one pre-implantation / reperfused pair in channels `2 -> 3`

and therefore a high-confidence working hypothesis:

- channels `0` and `2` correspond to pre-implantation samples
- channels `1` and `3` correspond to reperfused samples

However, this is still an **inference from directional consistency**, not an author-exposed sample sheet. The public metadata do not yet say this explicitly, and that distinction matters for a database layer intended to support publication-grade provenance.

## Status decision

Current registry status should remain:

- `source_review_needed`

Rationale:

- processed protein-level outputs are publicly reusable
- direct transplant relevance is high
- matrix-level ingest should wait until reporter-channel interpretation is defensible from an explicit public design source rather than a strong but still inferred pattern

## Next step

The next recovery pass should focus on:

1. finding any author-exposed sample sheet, supplementary table, or repository-side metadata that explicitly ties channels to pre-implantation versus reperfused graft samples
2. checking whether any associated article figure legends or non-PRIDE repository assets encode chip/channel semantics more explicitly
3. only then promoting `PXD010812` to a direct proteomics ingest script, unless the project deliberately chooses to support an explicitly labeled `inferred_state_mapping` exploratory layer
