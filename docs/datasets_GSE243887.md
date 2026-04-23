# GSE243887 Donor Liver Quality RNA-seq

GSE243887 is a public donor-liver RNA-seq dataset with deceased donor liver biopsy samples labeled by transplant-selection status.

## Processed Data

- Samples: 32 donor liver biopsies.
- States: 10 accepted donor livers and 22 rejected donor livers.
- Source matrix: GEO supplementary raw count table `GSE243887_Raw_counts.txt.gz`.
- Gene annotation: GENCODE v40 GTF, with Ensembl gene IDs mapped to gene symbols.
- Normalization: log2(CPM + 1), computed within the study from raw counts.

## Contrast

The database exposes `accepted_donor_liver_vs_rejected_donor_liver` as an exploratory Welch-test contrast with Benjamini-Hochberg FDR correction.

## Caveat

Accepted/rejected labels are donor organ selection labels. They should not be interpreted as post-transplant graft outcome labels without additional outcome-linked validation.
