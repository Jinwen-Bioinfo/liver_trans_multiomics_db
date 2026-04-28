# PXD067270: Normothermic perfusion graft-quality proteomics candidate

## Why this source matters

`PXD067270` is now one of the strongest unresolved direct liver-transplant proteomics candidates in the build queue because it is not just a marker-only paper. It is a clinical **sample-level graft-tissue proteomics** project tied to real transplanted donor livers, with sequential biopsies collected before perfusion, after normothermic machine perfusion, and after reperfusion.

That makes it potentially useful for:

- graft adaptation during normothermic machine perfusion
- ischemia/reperfusion biology in transplanted livers
- linking tissue proteomic trajectories to post-transplant biliary complications
- building a richer direct graft-tissue proteomics layer than article-only differential tables

## Public evidence chain

- Article DOI: `10.1111/liv.70629`
- PubMed: `PMID 41981940`
- PMC: `PMC13080225`
- PRIDE accession: `PXD067270`
- ProteomeXchange summary:
  - `https://proteomecentral.proteomexchange.org/cgi/GetDataset?ID=PXD067270-1&test=no`
- PRIDE FTP directory:
  - `https://ftp.pride.ebi.ac.uk/pride/data/archive/2026/04/PXD067270/`

The public article and PRIDE metadata already agree on the core design:

- `16` transplanted grafts with complete sequential biopsies
- `48` total biopsies
- three time points per graft:
  - `B1` = pre-perfusion / after static cold storage
  - `B2` = post-normothermic machine perfusion
  - `B3` = post-reperfusion
- clinical framing around **biliary complications after transplantation**

## What is already recoverable

This source is no longer just a title and abstract. The PRIDE FTP directory is public and already exposes:

- `48` Thermo raw files
- matching `.msf` files
- matching `.pdResult` result bundles
- `checksum.txt`
- a crucial sample-design workbook:
  - `Link_between_files.xlsx`

The workbook is already enough to map each acquisition file to a graft/timepoint pair.

Recovered structure from `Link_between_files.xlsx`:

- one sheet: `Proteomics`
- `48` sample rows
- columns:
  - `#`
  - `.raw files`
  - `.msf files`
  - `.pdResult`
  - `Graft number`
  - `Time points`

The workbook explicitly maps:

- `jh250422_01b` -> `M1`, `B1`
- `jh250422_02` -> `M1`, `B2`
- `jh250422_03` -> `M1`, `B3`
- ...
- `jh250422_46` -> `M16`, `B1`
- `jh250422_47` -> `M16`, `B2`
- `jh250422_48` -> `M16`, `B3`

So the **sample-to-timepoint design is already public and explicit**.

## What the article adds

From the article metadata and searchable full-text snippet:

- this is a prospective clinical NMP study
- the proteomics question is whether tissue-level proteomic trajectories distinguish grafts **with vs without biliary complications**
- the article lists supporting information:
  - `Appendix S1`
  - `Table S1` viability criteria
  - `Table S2` individual liver viability parameters
  - `Table S3` types and management of biliary complications
  - `Table S4` proteins deregulated between groups with and without complications
  - `Table S5` pathway analysis results
- the supplementary filename exposed in PMC search snippets is:
  - `LIV-46-0-s001.docx`

## Current blocker

This source is closer to promotion than `PXD061119`, but it is not fully ready yet.

What is still missing from explicit public recovery:

- per-graft mapping of `M1` through `M16` to:
  - `with biliary complications`
  - `without biliary complications`
- the actual contents of `Table S2`, `Table S3`, and `Table S4`
- a directly reusable protein-level quantification export if `.pdResult` cannot be parsed in the current lightweight pipeline

The environment has already confirmed that:

- the PRIDE FTP files are public and downloadable
- `Link_between_files.xlsx` is public and downloadable
- the PMC/Wiley supplementary filename is visible

But the actual `LIV-46-0-s001.docx` binary has not yet been recovered from the current environment because the obvious PMC `/bin/` route returns `403`.

## Status decision

Current registry status should be:

- `source_review_needed`

Rationale:

- stronger than a vague candidate because the sample/timepoint design is already explicit
- not yet `ready_to_ingest` because the clinical outcome mapping and reusable feature-level export still need one more recovery step

## Why this is now the next best proteomics target

Compared with the current blocker queue:

- stronger than `PXD061119` for immediate implementation because `M1-M16` and `B1/B2/B3` are already explicit
- cleaner than `PXD010812` because this is not reliant on inferred reporter-channel assignment
- richer than article-only marker papers because full raw/result files are public

## Next step

The next recovery pass should focus on:

1. recovering `LIV-46-0-s001.docx` or an equivalent supporting-information mirror
2. extracting `Table S2` / `Table S3` to assign each graft `M1-M16` to complication status
3. checking whether the `.pdResult` bundle can be converted into a reusable protein-abundance matrix without proprietary software
4. promoting `PXD067270` once those two remaining pieces are explicit enough for a defensible graft-quality/biliary-complication proteomics layer
