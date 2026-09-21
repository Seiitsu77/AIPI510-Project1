"""Clean the raw NYC crash extract and write an analysis-ready dataset.

Run after src/download_data.py:

    python src/preprocess.py

Design rules
------------
* Raw data is never modified in place. ``data/raw`` is read-only input;
  everything this script produces lands in ``data/processed``.
* Every row-removing step reports rows before, rows after, rows removed and the
  percentage removed, and the reason. The full ledger is written to
  ``outputs/summary_tables/filter_ledger.csv`` so nothing disappears quietly.
* Records with a suspect timestamp are FLAGGED, not dropped. See
  ``flag_midnight_placeholder`` -- dropping them would be a large, silent,
  non-random deletion.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import CASUALTY_COLUMNS, add_all_features  # noqa: E402

# Columns the analysis depends on, with the names actually published by the
# Socrata API. Several differ from the display names in the NYC Open Data web
# UI and from the plural forms one would guess -- see SCHEMA_NOTES.
EXPECTED_COLUMNS = [
    "crash_date",
    "crash_time",
    "borough",
    "zip_code",
    "latitude",
    "longitude",
    "collision_id",
    "contributing_factor_vehicle_1",
    "vehicle_type_code1",
] + CASUALTY_COLUMNS

SCHEMA_NOTES = {
    "number_of_cyclist_injured": "singular 'cyclist', not 'cyclists' as the project brief assumed",
    "number_of_cyclist_killed": "singular 'cyclist', not 'cyclists'",
    "number_of_motorist_injured": "singular 'motorist', not 'motorists'",
    "number_of_motorist_killed": "singular 'motorist', not 'motorists'",
    "vehicle_type_code1": "no underscore before the 1, unlike vehicle_type_code_3/_4/_5",
    "crash_time": "stored as free text 'H:MM', not a time type",
    "crash_date": "date only; the time of day lives entirely in crash_time",
}

# Fields whose missingness materially affects interpretation.
MISSINGNESS_FIELDS = [
    "borough",
    "zip_code",
    "latitude",
    "longitude",
    "contributing_factor_vehicle_1",
    "vehicle_type_code1",
    "crash_time",
    "number_of_persons_injured",
    "number_of_persons_killed",
]


class FilterLedger:
    """Records every row-count change so filtering is auditable."""

    def __init__(self, initial_rows: int):
        self.rows = initial_rows
        self.entries = []
        print(f"[rows] start: {initial_rows:,}")

    def record(self, step: str, new_rows: int, reason: str) -> None:
        removed = self.rows - new_rows
        pct = (removed / self.rows * 100) if self.rows else 0.0
        self.entries.append(
            {
                "step": step,
                "rows_before": self.rows,
                "rows_after": new_rows,
                "rows_removed": removed,
                "pct_removed": round(pct, 4),
                "reason": reason,
            }
        )
        print(
            f"[rows] {step}: {self.rows:,} -> {new_rows:,} "
            f"(removed {removed:,}, {pct:.3f}%) | {reason}"
        )
        self.rows = new_rows

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.entries)


def check_schema(df: pd.DataFrame) -> list[str]:
    """Report any expected column that the published data does not contain."""
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        print(f"[warn] expected columns absent from the extract: {missing}")
    else:
        print(f"[ok  ] all {len(EXPECTED_COLUMNS)} expected columns present")
    return missing


def parse_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Combine the date column and the free-text time column into a timestamp."""
    out = df.copy()

    date = pd.to_datetime(out["crash_date"], errors="coerce")

    # crash_time is text like '9:35' or '21:05'. Parse defensively rather than
    # assuming zero padding.
    parts = out["crash_time"].astype("string").str.strip().str.split(":", n=1, expand=True)
    hour = pd.to_numeric(parts[0], errors="coerce")
    minute = pd.to_numeric(parts[1], errors="coerce") if parts.shape[1] > 1 else pd.Series(np.nan, index=out.index)

    # Nullable string inputs can produce <NA> here. Treat missing clock parts
    # as invalid rather than allowing fillna(0) below to turn them into 00:00.
    valid_clock = (hour.between(0, 23) & minute.between(0, 59)).fillna(False)
    hour = hour.where(valid_clock)
    minute = minute.where(valid_clock)

    out["crash_date_only"] = date
    out["crash_hour"] = hour.astype("Int64")
    out["crash_minute"] = minute.astype("Int64")
    out["crash_datetime"] = date + pd.to_timedelta(hour.fillna(0), unit="h") + pd.to_timedelta(
        minute.fillna(0), unit="m"
    )
    out.loc[date.isna() | ~valid_clock, "crash_datetime"] = pd.NaT

    return out


def flag_midnight_placeholder(df: pd.DataFrame) -> pd.DataFrame:
    """Flag records timestamped exactly 00:00, which behave like unknown times.

    Exactly-midnight records are roughly twice as common as any other single
    clock minute, and -- decisively -- they contain almost no fatal crashes,
    which is not possible for a genuine hour of the night. They look like a
    default value written when the true time was not recorded.

    They are flagged rather than dropped: they are ~1.7% of the data and their
    injury rate is close to the rest of hour 0, so removing them would be a
    large deletion for a problem that only materially distorts one statistic
    (the hour-0 fatality rate). analysis.py reports that statistic both ways.
    """
    out = df.copy()
    out["midnight_placeholder"] = (out["crash_hour"] == 0) & (out["crash_minute"] == 0)
    n = int(out["midnight_placeholder"].sum())
    print(f"[flag] exactly-00:00 records flagged as suspect timestamps: {n:,} ({n / len(out) * 100:.2f}%)")
    return out


def coerce_casualties(df: pd.DataFrame) -> pd.DataFrame:
    """Force casualty columns to non-negative integers."""
    out = df.copy()
    for col in CASUALTY_COLUMNS:
        if col not in out.columns:
            continue
        numeric = pd.to_numeric(out[col], errors="coerce")
        n_null = int(numeric.isna().sum())
        n_neg = int((numeric < 0).sum())
        if n_null:
            print(f"[fix ] {col}: {n_null:,} non-numeric/missing -> 0")
        if n_neg:
            print(f"[fix ] {col}: {n_neg:,} negative -> 0")
        out[col] = numeric.fillna(0).clip(lower=0).astype("int64")
    return out


def missingness_report(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in MISSINGNESS_FIELDS:
        if col not in df.columns:
            continue
        n_missing = int(df[col].isna().sum())
        rows.append(
            {
                "column": col,
                "n_missing": n_missing,
                "pct_missing": round(n_missing / len(df) * 100, 3),
            }
        )
    return pd.DataFrame(rows).sort_values("pct_missing", ascending=False)


def run(raw_path: Path, out_path: Path, tables_dir: Path, start_year: int, end_year: int) -> pd.DataFrame:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    if not raw_path.exists():
        raise SystemExit(
            f"[fail] {raw_path} not found. Run:  python src/download_data.py"
        )

    print(f"[read] {raw_path}")
    df = pd.read_csv(raw_path, low_memory=False)
    print(f"[read] {len(df):,} rows x {df.shape[1]} columns")

    missing_cols = check_schema(df)
    if missing_cols:
        raise SystemExit(
            "[fail] required columns absent from the raw extract: "
            + ", ".join(missing_cols)
        )

    ledger = FilterLedger(len(df))

    # --- duplicates -------------------------------------------------------
    n_exact = int(df.duplicated().sum())
    n_id = int(df["collision_id"].duplicated().sum())
    print(f"[dupe] exact duplicate rows: {n_exact:,} | duplicate collision_id: {n_id:,}")
    if n_id:
        df = df.drop_duplicates(subset="collision_id", keep="first")
        ledger.record("drop_duplicate_collision_id", len(df), "collision_id must uniquely identify a crash")

    # --- parsing ----------------------------------------------------------
    df = parse_datetime(df)
    n_bad_date = int(df["crash_date_only"].isna().sum())
    n_bad_time = int(df["crash_hour"].isna().sum())
    print(f"[time] unparseable dates: {n_bad_date:,} | unparseable times: {n_bad_time:,}")

    before = len(df)
    df = df[df["crash_datetime"].notna()]
    if len(df) != before:
        ledger.record(
            "drop_unparseable_timestamp",
            len(df),
            "hour-of-day is the analysis axis; a row without a usable timestamp cannot be placed on it",
        )

    # --- year window ------------------------------------------------------
    before = len(df)
    df = df[df["crash_datetime"].dt.year.between(start_year, end_year)]
    if len(df) != before:
        ledger.record(
            "restrict_to_complete_years",
            len(df),
            f"analysis covers complete calendar years {start_year}-{end_year}; "
            f"partial years (e.g. 2026) are excluded to avoid seasonal bias",
        )
    else:
        print(f"[ok  ] all rows already within {start_year}-{end_year}")

    # --- values -----------------------------------------------------------
    df = coerce_casualties(df)
    df = flag_midnight_placeholder(df)

    # Latitude/longitude of exactly 0 are null-island placeholders, not a
    # location off the coast of Africa. Blank them so any mapping is honest.
    if {"latitude", "longitude"}.issubset(df.columns):
        lat = pd.to_numeric(df["latitude"], errors="coerce")
        lon = pd.to_numeric(df["longitude"], errors="coerce")
        null_island = (lat == 0) | (lon == 0)
        n_ni = int(null_island.sum())
        if n_ni:
            print(f"[fix ] latitude/longitude == 0 set to missing: {n_ni:,} rows (kept, coords blanked)")
        df["latitude"] = lat.where(~null_island)
        df["longitude"] = lon.where(~null_island)

    if "borough" in df.columns:
        df["borough"] = df["borough"].astype("string").str.strip().str.title()

    # --- features ---------------------------------------------------------
    df = add_all_features(df)

    # --- reports ----------------------------------------------------------
    miss = missingness_report(df)
    miss.to_csv(tables_dir / "missingness.csv", index=False)
    print("\n[miss] missingness in key fields:")
    print(miss.to_string(index=False))

    ledger_df = ledger.to_frame()
    if not ledger_df.empty:
        ledger_df.to_csv(tables_dir / "filter_ledger.csv", index=False)
    else:
        pd.DataFrame(
            [{"step": "none", "rows_before": len(df), "rows_after": len(df),
              "rows_removed": 0, "pct_removed": 0.0,
              "reason": "no rows removed; server-side year filter already matched the analysis window"}]
        ).to_csv(tables_dir / "filter_ledger.csv", index=False)

    df.to_parquet(out_path, index=False)

    summary = {
        "rows_raw": int(ledger.entries[0]["rows_before"]) if ledger.entries else len(df),
        "rows_analysed": int(len(df)),
        "date_min": str(df["crash_datetime"].min()),
        "date_max": str(df["crash_datetime"].max()),
        "years": sorted(int(y) for y in df["year"].dropna().unique()),
        "schema_notes": SCHEMA_NOTES,
    }
    (out_path.parent / "preprocess_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(f"\n[done] processed dataset : {out_path}  ({len(df):,} rows x {df.shape[1]} cols)")
    print(f"[done] date range        : {summary['date_min']} -> {summary['date_max']}")
    return df


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Clean the raw NYC crash extract.")
    p.add_argument("--raw", type=Path, default=Path("data/raw/nyc_crashes_2021_2025.csv"))
    p.add_argument("--out", type=Path, default=Path("data/processed/crashes_clean.parquet"))
    p.add_argument("--tables", type=Path, default=Path("outputs/summary_tables"))
    p.add_argument("--start-year", type=int, default=2021)
    p.add_argument("--end-year", type=int, default=2025)
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    run(args.raw, args.out, args.tables, args.start_year, args.end_year)
    return 0


if __name__ == "__main__":
    sys.exit(main())
