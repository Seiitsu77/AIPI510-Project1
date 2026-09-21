"""Unit tests for raw-data validation and preprocessing helpers."""

from pathlib import Path
import sys
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from preprocess import (  # noqa: E402
    coerce_casualties,
    flag_midnight_placeholder,
    parse_datetime,
    run,
)


class DatetimeParsingTests(unittest.TestCase):
    def test_valid_clock_values_are_parsed(self):
        df = pd.DataFrame(
            {
                "crash_date": ["2025-01-02", "2025-01-02"],
                "crash_time": ["9:05", "21:30"],
            }
        )

        result = parse_datetime(df)

        self.assertEqual(result["crash_hour"].tolist(), [9, 21])
        self.assertEqual(result["crash_minute"].tolist(), [5, 30])
        self.assertEqual(
            result["crash_datetime"].dt.strftime("%Y-%m-%d %H:%M").tolist(),
            ["2025-01-02 09:05", "2025-01-02 21:30"],
        )

    def test_invalid_clock_values_become_missing(self):
        df = pd.DataFrame(
            {
                "crash_date": ["2025-01-02"] * 3,
                "crash_time": ["25:00", "10:60", None],
            }
        )

        result = parse_datetime(df)

        self.assertTrue(result["crash_hour"].isna().all())
        self.assertTrue(result["crash_datetime"].isna().all())

    def test_exact_midnight_is_flagged(self):
        df = pd.DataFrame(
            {
                "crash_hour": pd.Series([0, 0, 1], dtype="Int64"),
                "crash_minute": pd.Series([0, 1, 0], dtype="Int64"),
            }
        )

        result = flag_midnight_placeholder(df)

        self.assertEqual(result["midnight_placeholder"].tolist(), [True, False, False])


class CasualtyCleaningTests(unittest.TestCase):
    def test_non_numeric_missing_and_negative_values_become_zero(self):
        df = pd.DataFrame(
            {"number_of_persons_injured": ["2", "unknown", None, -3]}
        )

        result = coerce_casualties(df)

        self.assertEqual(result["number_of_persons_injured"].tolist(), [2, 0, 0, 0])
        self.assertEqual(str(result["number_of_persons_injured"].dtype), "int64")


class SchemaValidationTests(unittest.TestCase):
    def test_pipeline_fails_early_when_required_columns_are_missing(self):
        incomplete = pd.DataFrame(
            {
                "crash_date": ["2025-01-02"],
                "crash_time": ["09:05"],
                "collision_id": [1],
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw_path = tmp_path / "raw.csv"
            incomplete.to_csv(raw_path, index=False)

            with self.assertRaisesRegex(SystemExit, "required columns"):
                run(
                    raw_path,
                    tmp_path / "processed.parquet",
                    tmp_path / "tables",
                    2021,
                    2025,
                )


if __name__ == "__main__":
    unittest.main()
