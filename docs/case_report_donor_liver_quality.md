# Case Report: Donor Liver Quality and Graft Viability

## Question

Can donor-organ molecular features contextualize accepted versus rejected livers and machine-perfusion viability biology?

## Why This Matters

Donor liver quality is one of the most transplant-specific questions in the whole project. Generic repositories do not organize donor selection, viability, and perfusion-associated biology into a usable evidence layer. If LiverTx-OmicsDB can do this well, it becomes much more clearly differentiated from GEO, PRIDE, and other general-purpose omics resources.

This use case is also valuable because it separates three concepts that are often blurred together:

1. donor-organ acceptance versus rejection at selection
2. machine-perfusion viability biology
3. recipient post-transplant outcome

The database has to make those distinctions explicit.

## Current Evidence Stack

### Evidence Grade A

- `GSE243887`
  - donor liver RNA-seq
  - current contrast:
    - `accepted_donor_liver_vs_rejected_donor_liver`

- `PXD046355`
  - donor-liver bile proteomics
  - current contrasts include:
    - `high_biliary_viability_donor_liver_vs_low_biliary_viability_donor_liver_at_30min`
    - `high_biliary_viability_donor_liver_vs_low_biliary_viability_donor_liver_at_150min`

### Evidence Grade M

- `PXD067270`
  - direct graft biopsy proteomics candidate
  - sample-to-timepoint mapping already recovered:
    - `M1-M16`
    - `B1/B2/B3`
  - public outcome annotation still unresolved

## Cross-Omics Interpretation

The first-pass mapping scaffold currently organizes donor-quality biology into three groups.

### 1. Hepatocyte synthetic and xenobiotic-metabolism competence

Core entities:

- `ALB`
- `CYP3A4`
- `APOA1`

Interpretation:

This is the main donor-quality transcriptomic competence axis. If these features are preserved, they support a reading of stronger hepatocyte identity and metabolic function.

### 2. Stress-response and extracellular-matrix remodeling

Core entities:

- `HMOX1`
- `COL1A1`

Interpretation:

This group provides the “cost” side of donor-quality interpretation: stress-response activation and matrix-remodeling context that may accompany poorer donor-organ biology.

### 3. Biliary and epithelial viability surface program

Core entities:

- `FCGBP`
- `ANPEP`
- `ACE2`
- `DPP4`
- `CTSZ`

Interpretation:

This is the strongest current proteomic donor-viability layer and gives the database something that looks much more like transplant-specific organ-quality biology than a generic liver dataset.

## What This Demonstrator Already Supports

At this stage, the database can already support these claims:

1. donor-organ RNA evidence can be queried by accepted versus rejected selection status
2. donor-liver bile proteomics can be queried for biliary viability context
3. donor-quality interpretation can already be framed as a balance between:
   - preserved hepatocyte function
   - stress/fibrosis-linked remodeling
   - biliary/perfusion viability signals

This is a meaningful V1 story and is one of the strongest transplant-specific differentiators in the project.

## What It Does Not Yet Support

This use case should **not** yet be presented as:

- a recipient-outcome predictor
- a complete donor-organ triage model
- a comprehensive machine-perfusion multi-omics classifier

The main gaps are:

- donor-quality pathway modules are not yet formalized in the resource
- transcriptome and proteome are not yet joined in one user-facing question report
- `PXD067270` is promising but still unresolved as a usable graft-quality proteomics layer

## Why `PXD067270` Matters Next

`PXD067270` has become the next strongest donor-quality follow-up because:

- it is direct graft-tissue proteomics
- it already has public sample-to-timepoint mapping
- it appears clinically aligned with graft quality and biliary complications

What still blocks it:

- public per-graft complication annotation
- lightweight reusable protein-level export

That means it is closer to promotion than many other unresolved proteomics candidates, but not ready to be treated as evidence yet.

## Recommended Next Step

The next work for this use case should be:

1. define donor-quality modules formally:
   - hepatocyte competence
   - oxidative stress
   - ECM/fibrosis
   - biliary viability
2. create a donor-quality evidence matrix that puts `GSE243887` and `PXD046355` side by side
3. keep donor-organ selection labels visibly separate from recipient outcomes
4. continue targeted recovery work on `PXD067270`

## Bottom Line

This is already one of the most compelling database questions in the project. The current build can credibly present donor-quality molecular context, as long as it stays disciplined about distinguishing donor-organ biology from downstream recipient prognosis.
