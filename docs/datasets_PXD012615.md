# PXD012615 human liver cell proteome reference

## Scope

PXD012615 is a PRIDE project containing mass-spectrometry proteomics for major human liver cell compartments. It is a reference human liver proteome, not a liver transplantation cohort.

## What is processed

- Source: PRIDE `MaxQuant_Output.zip`, parsed from `proteinGroups.txt`.
- 10,138 MaxQuant protein group rows.
- 9,445 rows retained after filtering reverse hits, potential contaminants, site-only identifications, and rows without gene symbols.
- 9,037 queryable gene-symbol protein features.
- Four reference compartments:
  - hepatocyte
  - liver sinusoidal endothelial cell
  - Kupffer cell
  - hepatic stellate cell

## Evidence model

For each gene/protein, the resource stores:

- primary UniProt accession from the majority protein IDs
- protein name
- peptide and unique peptide counts
- MaxQuant score and q-value
- detected reference compartments
- mean `log2(MaxQuant intensity + 1)` by compartment
- best compartment by mean log2 intensity

## Example features

- `CYP3A4`: hepatocyte-high protein evidence.
- `COL1A1`: hepatic stellate cell-high extracellular matrix evidence.
- `VWF`: liver sinusoidal endothelial cell-high vascular evidence.
- `LST1`: Kupffer cell-high myeloid evidence.

## Caveats

PXD012615 should be used as protein reference context only. It should not be interpreted as rejection, donor quality, drug exposure, or graft outcome evidence. Serum albumin (`ALB`) is excluded because it is marked as a potential contaminant in the MaxQuant protein group table.

## API examples

- `/api/features/CYP3A4/protein`
- `/api/features/COL1A1/protein`
- `/api/features/VWF/protein`
- `/api/studies/PXD012615/downloads`
