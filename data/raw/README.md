# data/raw

This directory holds the unmodified API extract. **Its contents are gitignored.**

`nyc_crashes_2021_2025.csv` is roughly 115 MB, which does not belong in a git
repository, and it is fully regenerable from a documented query. Recreate it with:

```bash
python src/download_data.py
```

That writes two files:

| File | Purpose |
|---|---|
| `nyc_crashes_2021_2025.csv` | 487,914 rows, 29 columns, straight from the API |
| `nyc_crashes_2021_2025.csv.meta.json` | The exact query, retrieval timestamp and row count |

The sidecar metadata matters because the source dataset is updated continuously.
Two people running the pipeline months apart will not get byte-identical files,
and the metadata is what lets them tell why.

Nothing in this directory is ever edited in place. Cleaning output goes to
`data/processed/`.
