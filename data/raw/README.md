# data/raw

## What is here

| File | Committed? | Why |
|---|---|---|
| `sample_nyc_crashes_1000.csv` | Yes (217 KB) | First 1,000 rows of the real extract, so the raw schema is inspectable in the repo |
| `nyc_crashes_2021_2025.csv.meta.json` | Yes | The exact query, retrieval timestamp and row count of the full extract |
| `nyc_crashes_2021_2025.csv` | **No** | 115 MB — above GitHub's 100 MB per-file hard limit |

## Regenerating the full raw extract

The full file is not a manual download. One command reproduces it exactly:

```bash
python src/download_data.py
```

This queries the official NYC Open Data (Socrata) API for dataset `h9gi-nx95`,
filtering to complete calendar years 2021–2025 server-side, and writes:

- `nyc_crashes_2021_2025.csv` — 487,914 rows × 29 columns, ~115 MB
- `nyc_crashes_2021_2025.csv.meta.json` — query, retrieval timestamp, row count

No API key is needed. A Socrata app token is optional and only raises the
anonymous rate limit:

```bash
export SOCRATA_APP_TOKEN=your_token_here   # optional
```

## Why the sidecar metadata matters

The source dataset is updated continuously as NYPD files and amends reports.
Two people running `download_data.py` months apart will not get byte-identical
files. The `.meta.json` records which vintage a given analysis was built on, so
a difference in results can be traced to a difference in the data rather than
to the code.

## Cleaned data

The analysis-ready dataset **is** committed, at
`data/processed/crashes_clean.parquet` (487,914 rows × 49 columns, ~23 MB).
It is produced from the raw extract by:

```bash
python src/preprocess.py
```

Nothing in `data/raw/` is ever edited in place; all cleaning output goes to
`data/processed/`.
