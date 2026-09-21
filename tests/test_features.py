"""Unit tests for feature engineering and rate calculations."""

from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from features import (  # noqa: E402
    add_outcome_features,
    assign_time_period,
    rate_table,
    wilson_interval,
)


class TimePeriodTests(unittest.TestCase):
    def test_all_time_period_boundaries(self):
        hours = pd.Series([0, 5, 6, 9, 10, 15, 16, 19, 20, 23], dtype="Int64")
        expected = [
            "Late Night",
            "Late Night",
            "Morning Commute",
            "Morning Commute",
            "Daytime",
            "Daytime",
            "Evening Commute",
            "Evening Commute",
            "Night",
            "Night",
        ]

        actual = assign_time_period(hours).astype("object").tolist()
        self.assertEqual(actual, expected)

    def test_missing_or_invalid_hour_is_unclassified(self):
        hours = pd.Series([-1, 24, pd.NA], dtype="Int64")
        actual = assign_time_period(hours)
        self.assertTrue(pd.isna(actual).all())


class OutcomeFeatureTests(unittest.TestCase):
    def test_outcome_flags_use_injured_and_killed_counts(self):
        df = pd.DataFrame(
            {
                "number_of_persons_injured": [0, 2, 0],
                "number_of_persons_killed": [0, 0, 1],
                "number_of_pedestrians_injured": [0, 0, 0],
                "number_of_pedestrians_killed": [0, 1, 0],
                "number_of_cyclist_injured": [0, 0, 1],
                "number_of_cyclist_killed": [0, 0, 0],
                "number_of_motorist_injured": [0, 1, 0],
                "number_of_motorist_killed": [0, 0, 0],
            }
        )

        result = add_outcome_features(df)

        self.assertEqual(result["injury_crash"].tolist(), [False, True, False])
        self.assertEqual(result["fatal_crash"].tolist(), [False, False, True])
        self.assertEqual(
            result["pedestrian_injury_crash"].tolist(), [False, True, False]
        )
        self.assertEqual(
            result["cyclist_injury_crash"].tolist(), [False, False, True]
        )
        self.assertEqual(
            result["vulnerable_road_user_injury"].tolist(), [False, True, True]
        )
        self.assertEqual(result["no_vru_casualty"].tolist(), [True, False, False])


class RateCalculationTests(unittest.TestCase):
    def test_wilson_interval_is_bounded(self):
        low, high = wilson_interval([0, 5, 10], [10, 10, 10])

        self.assertTrue(np.all(low >= 0))
        self.assertTrue(np.all(high <= 1))
        self.assertTrue(np.all(low <= high))

    def test_wilson_interval_with_zero_total_is_nan(self):
        low, high = wilson_interval([0], [0])

        self.assertTrue(np.isnan(low[0]))
        self.assertTrue(np.isnan(high[0]))

    def test_rate_table_reports_denominator_rate_and_reliability(self):
        df = pd.DataFrame(
            {
                "period": ["A", "A", "B"],
                "injury_crash": [True, False, True],
            }
        )

        result = rate_table(df, "period", "injury_crash", min_n=2).set_index(
            "period"
        )

        self.assertEqual(int(result.loc["A", "n"]), 2)
        self.assertEqual(int(result.loc["A", "successes"]), 1)
        self.assertAlmostEqual(float(result.loc["A", "rate"]), 0.5)
        self.assertTrue(bool(result.loc["A", "reliable"]))
        self.assertFalse(bool(result.loc["B", "reliable"]))


if __name__ == "__main__":
    unittest.main()
