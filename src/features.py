"""Feature engineering for the NYC crash analysis.

Every derived column used anywhere in the project is defined here, once, so the
scripts, the notebook and the figures cannot drift apart.

Two conventions worth stating explicitly, because they shape every downstream
number:

1. Outcome flags are booleans, not counts. ``injury_crash`` answers "did this
   crash injure at least one person?", not "how many?". The project's headline
   metric is the *share of reported crashes* that involved an injury, so a
   crash that injured six people counts once, exactly like a crash that injured
   one. That keeps the metric a well-defined proportion with an honest
   denominator.

2. Road-user flags record *who was hurt*, not *who was present*. The source
   data has no "a pedestrian was involved" field -- only counts of pedestrians
   injured and killed. So ``pedestrian_injury_crash`` means "a pedestrian was
   injured or killed in this crash". It is NOT a measure of pedestrian
   involvement, and it must never be used as one: by construction every
   pedestrian_injury_crash is also an injury_crash, so comparing injury rates
   *between* road-user flags is circular. See docs/ and outputs/analysis_summary.md.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Time-of-day bands
# ---------------------------------------------------------------------------
# Chosen to match how New Yorkers actually move through a day rather than to
# split the clock into equal pieces: two commute peaks, the working day between
# them, the evening after them, and the small hours. Boundaries are documented
# in the README so a reader can judge them.
TIME_PERIOD_BOUNDS = [
    ("Late Night", 0, 5),        # 00:00-05:59
    ("Morning Commute", 6, 9),   # 06:00-09:59
    ("Daytime", 10, 15),         # 10:00-15:59
    ("Evening Commute", 16, 19),# 16:00-19:59
    ("Night", 20, 23),           # 20:00-23:59
]

TIME_PERIOD_ORDER = [name for name, _, _ in TIME_PERIOD_BOUNDS]

DAY_NAME_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# Casualty count columns, kept in one place so preprocessing and feature
# engineering agree on what must be numeric.
CASUALTY_COLUMNS = [
    "number_of_persons_injured",
    "number_of_persons_killed",
    "number_of_pedestrians_injured",
    "number_of_pedestrians_killed",
    "number_of_cyclist_injured",
    "number_of_cyclist_killed",
    "number_of_motorist_injured",
    "number_of_motorist_killed",
]


def assign_time_period(hour: pd.Series) -> pd.Series:
    """Map hour-of-day (0-23) onto the named bands above."""
    period = pd.Series(pd.NA, index=hour.index, dtype="object")
    for name, low, high in TIME_PERIOD_BOUNDS:
        # Nullable integer inputs produce <NA> in the boolean condition.
        # Treat that as no match so missing hours remain unclassified.
        in_period = hour.between(low, high).fillna(False)
        period = period.mask(in_period, name)
    return pd.Categorical(period, categories=TIME_PERIOD_ORDER, ordered=True)


def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive calendar and clock features from crash_datetime / crash_hour.

    Expects preprocess.py to have already produced ``crash_datetime`` (a real
    timestamp) and ``crash_hour`` (Int64).
    """
    out = df.copy()
    ts = out["crash_datetime"]

    out["year"] = ts.dt.year.astype("Int64")
    out["month"] = ts.dt.month.astype("Int64")
    out["month_name"] = ts.dt.month_name()
    out["day_of_week"] = ts.dt.dayofweek.astype("Int64")  # Monday = 0
    out["day_name"] = pd.Categorical(
        ts.dt.day_name(), categories=DAY_NAME_ORDER, ordered=True
    )
    out["is_weekend"] = out["day_of_week"] >= 5
    out["week_part"] = np.where(out["is_weekend"], "Weekend", "Weekday")
    out["time_period"] = assign_time_period(out["crash_hour"])

    return out


def add_outcome_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the boolean crash-outcome flags.

    See the module docstring for why these are booleans and why the road-user
    flags describe who was *hurt* rather than who was *present*.
    """
    out = df.copy()

    ped = out["number_of_pedestrians_injured"] + out["number_of_pedestrians_killed"]
    cyc = out["number_of_cyclist_injured"] + out["number_of_cyclist_killed"]
    mot = out["number_of_motorist_injured"] + out["number_of_motorist_killed"]

    out["injury_crash"] = out["number_of_persons_injured"] > 0
    out["fatal_crash"] = out["number_of_persons_killed"] > 0

    out["pedestrian_injury_crash"] = ped > 0
    out["cyclist_injury_crash"] = cyc > 0
    out["motorist_injury_crash"] = mot > 0

    # "Vulnerable road user" = pedestrian or cyclist. Used to describe the
    # changing composition of casualties across the day.
    out["vulnerable_road_user_injury"] = out["pedestrian_injury_crash"] | out["cyclist_injury_crash"]

    # Crashes where nobody outside a vehicle was hurt. Lets us ask how much of
    # the hourly swing in the overall injury rate survives once the changing
    # pedestrian/cyclist mix is held aside.
    out["no_vru_casualty"] = ~out["vulnerable_road_user_injury"]

    return out


def add_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """Full feature pipeline: temporal features then outcome flags."""
    return add_outcome_features(add_temporal_features(df))


# ---------------------------------------------------------------------------
# Rate helpers
# ---------------------------------------------------------------------------
def wilson_interval(successes, total, z: float = 1.96):
    """Wilson score interval for a binomial proportion.

    Preferred over the normal approximation because several of the groups we
    report (fatal crashes in a single hour) have small success counts, where the
    normal interval misbehaves and can run below zero. Implemented directly so
    the project does not need scipy.

    Returns (low, high) as proportions. Groups with total == 0 return NaN.
    """
    successes = np.asarray(successes, dtype=float)
    total = np.asarray(total, dtype=float)

    with np.errstate(divide="ignore", invalid="ignore"):
        phat = np.divide(successes, total, out=np.full_like(total, np.nan), where=total > 0)
        denom = 1.0 + (z**2) / total
        centre = phat + (z**2) / (2 * total)
        margin = z * np.sqrt((phat * (1 - phat) + (z**2) / (4 * total)) / total)
        low = (centre - margin) / denom
        high = (centre + margin) / denom

    low = np.where(total > 0, np.clip(low, 0.0, 1.0), np.nan)
    high = np.where(total > 0, np.clip(high, 0.0, 1.0), np.nan)
    return low, high


def rate_table(df: pd.DataFrame, by, flag: str, min_n: int = 0) -> pd.DataFrame:
    """Group-wise rate of a boolean ``flag`` with sample size and Wilson CI.

    Always returns ``n`` alongside the rate: no rate in this project is ever
    reported without the denominator it was computed from. ``min_n`` marks
    (never silently drops) groups too small to interpret.
    """
    grouped = df.groupby(by, observed=True)[flag].agg(["size", "sum"])
    grouped.columns = ["n", "successes"]

    grouped["rate"] = grouped["successes"] / grouped["n"]
    low, high = wilson_interval(grouped["successes"], grouped["n"])
    grouped["ci_low"] = low
    grouped["ci_high"] = high
    grouped["rate_pct"] = grouped["rate"] * 100
    grouped["ci_low_pct"] = grouped["ci_low"] * 100
    grouped["ci_high_pct"] = grouped["ci_high"] * 100
    grouped["reliable"] = grouped["n"] >= min_n

    return grouped.reset_index()
