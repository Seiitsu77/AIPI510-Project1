"""Download NYC Motor Vehicle Collisions - Crashes for a range of complete years.

Source
------
NYC Open Data / NYPD, "Motor Vehicle Collisions - Crashes"
Dataset id : h9gi-nx95
Landing    : https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95
API (SoQL) : https://data.cityofnewyork.us/resource/h9gi-nx95.csv

We use the official Socrata API rather than a third-party mirror so the extract
is dated, filtered server-side, and reproducible by anyone.

Reproducibility notes
---------------------
* Rows are paginated with an explicit ``$order=collision_id``. Socrata does not
  guarantee a stable row order without an ORDER BY, so paging with $limit/$offset
  over an unordered result can silently duplicate or skip rows.
* The year filter is applied server-side, so we never download years we then
  throw away.
* A sidecar ``<file>.meta.json`` records the exact query, the retrieval
  timestamp and the row count, so a later reader can tell which vintage of this
  continuously-updated dataset an analysis was built on.

Example
-------
    python src/download_data.py                      # 2021-2025 (default)
    python src/download_data.py --start-year 2023 --end-year 2025 --force
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DATASET_ID = "h9gi-nx95"
CSV_ENDPOINT = f"https://data.cityofnewyork.us/resource/{DATASET_ID}.csv"
METADATA_ENDPOINT = f"https://data.cityofnewyork.us/api/views/{DATASET_ID}.json"

DEFAULT_START_YEAR = 2021
DEFAULT_END_YEAR = 2025
DEFAULT_PAGE_SIZE = 50_000

TIMEOUT = (30, 600)  # (connect, read) seconds

# Columns the downstream pipeline depends on. Socrata quotes every header field,
# so we compare parsed names rather than a raw string prefix.
REQUIRED_COLUMNS = (
    "crash_date",
    "crash_time",
    "collision_id",
    "number_of_persons_injured",
    "number_of_persons_killed",
)


def build_session(app_token=None):
    """HTTP session with bounded retries on transient Socrata errors."""
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "nyc-crash-story/1.0 (academic research)"})
    if app_token:
        # Optional. Without a token Socrata still serves requests, but throttles
        # anonymous callers more aggressively.
        session.headers["X-App-Token"] = app_token
    return session


def where_clause(start_year, end_year):
    """Half-open date filter [start_year-01-01, end_year+1-01-01)."""
    return (
        "crash_date >= '{0}-01-01T00:00:00'"
        " AND crash_date < '{1}-01-01T00:00:00'"
    ).format(start_year, end_year + 1)


def fetch_dataset_vintage(session):
    """Retrieve publisher metadata so we can record which vintage we pulled."""
    try:
        response = session.get(METADATA_ENDPOINT, timeout=TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        updated = payload.get("rowsUpdatedAt")
        return {
            "dataset_name": payload.get("name"),
            "rows_updated_at": (
                datetime.fromtimestamp(updated, tz=timezone.utc).isoformat()
                if updated
                else None
            ),
        }
    except (requests.RequestException, ValueError) as exc:  # pragma: no cover
        print("[warn] could not read dataset metadata: {0}".format(exc))
        return {}


def download(start_year, end_year, outdir, force, page_size, app_token):
    outdir.mkdir(parents=True, exist_ok=True)
    dest = outdir / "nyc_crashes_{0}_{1}.csv".format(start_year, end_year)

    if dest.exists() and not force:
        size = dest.stat().st_size
        print("[skip] {0} already exists ({1:,} bytes). Use --force to re-download.".format(dest, size))
        return dest

    session = build_session(app_token)
    where = where_clause(start_year, end_year)
    # Write to a temp file and rename on success, so an interrupted run cannot
    # leave a truncated CSV that the idempotency check would then honour.
    tmp = dest.with_suffix(dest.suffix + ".part")

    print("[get ] {0}".format(CSV_ENDPOINT))
    print("[get ] $where = {0}".format(where))

    total_rows = 0
    offset = 0
    pages = 0

    with tmp.open("wb") as handle:
        while True:
            params = {
                "$where": where,
                "$order": "collision_id",  # stable paging; see module docstring
                "$limit": page_size,
                "$offset": offset,
            }
            response = session.get(CSV_ENDPOINT, params=params, timeout=TIMEOUT)
            if response.status_code != 200:
                raise SystemExit(
                    "[fail] HTTP {0} from Socrata: {1}".format(
                        response.status_code, response.text[:500].strip()
                    )
                )

            text = response.text
            if not text.strip():
                break

            # Street-name fields in this dataset contain embedded newlines, so a
            # record is NOT the same thing as a line. Count records with a real
            # CSV parser -- otherwise both the progress figures and the
            # end-of-pagination test below are wrong.
            reader = csv.reader(io.StringIO(text))
            header_row = next(reader, None)
            if header_row is None:
                break
            got = sum(1 for _ in reader)

            if pages == 0:
                missing = [c for c in REQUIRED_COLUMNS if c not in set(header_row)]
                if missing:
                    raise SystemExit(
                        "[fail] Response is missing required columns {0}; "
                        "the published schema may have changed.\n  Header was: {1}".format(
                            missing, ",".join(header_row)[:300]
                        )
                    )
            else:
                # Drop the repeated header line on every page after the first.
                text = text.split("\n", 1)[1] if "\n" in text else ""

            if got == 0:
                break

            handle.write(text.encode("utf-8"))

            total_rows += got
            pages += 1
            offset += page_size
            print("[page] {0:>2}  rows so far: {1:,}".format(pages, total_rows))

            if got < page_size:
                break

    os.replace(tmp, dest)
    size = dest.stat().st_size

    meta = {
        "dataset_id": DATASET_ID,
        "source_url": CSV_ENDPOINT,
        "where_clause": where,
        "order_by": "collision_id",
        "start_year": start_year,
        "end_year": end_year,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows_downloaded": total_rows,
        "file_bytes": size,
    }
    meta.update(fetch_dataset_vintage(session))
    meta_path = dest.with_suffix(dest.suffix + ".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("[done] path      : {0}".format(dest))
    print("[done] size      : {0:,} bytes ({1:.1f} MiB)".format(size, size / 1024 / 1024))
    print("[done] data rows : {0:,}".format(total_rows))
    print("[done] metadata  : {0}".format(meta_path))
    return dest


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Download NYC Motor Vehicle Collisions - Crashes for complete calendar years.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--start-year", type=int, default=DEFAULT_START_YEAR)
    parser.add_argument("--end-year", type=int, default=DEFAULT_END_YEAR)
    parser.add_argument("--outdir", type=Path, default=Path("data/raw"))
    parser.add_argument("--force", action="store_true", help="Re-download even if the file exists")
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    parser.add_argument(
        "--app-token",
        default=os.environ.get("SOCRATA_APP_TOKEN"),
        help="Optional Socrata app token (or set SOCRATA_APP_TOKEN)",
    )

    args = parser.parse_args(argv)
    if args.start_year > args.end_year:
        parser.error("--start-year must not be after --end-year")
    if not 2012 <= args.start_year <= 2100:
        parser.error("--start-year is outside the dataset coverage (data begin in 2012)")
    return args


def main(argv=None):
    args = parse_args(argv)
    download(
        start_year=args.start_year,
        end_year=args.end_year,
        outdir=args.outdir,
        force=args.force,
        page_size=args.page_size,
        app_token=args.app_token,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
