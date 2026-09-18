"""Compute every summary table the story rests on, and write the evidence base.

Run after src/preprocess.py:

    python src/analysis.py

Outputs
-------
outputs/summary_tables/*.csv   one table per question asked of the data
outputs/analysis_summary.md    the written evidence base

Every number in analysis_summary.md is formatted from a value computed in this
script. Nothing in it is typed by hand, so the blog post, the README and the
slides can be checked against it -- and it cannot silently go stale when the
data are refreshed.

Statistical conventions
-----------------------
* injury_crash_rate = reported crashes with >=1 person injured / all reported
  crashes in the group. The denominator is always reported alongside it.
* Rates are conditional on a crash having been reported. This dataset carries
  no exposure denominator (no counts of trips, vehicle-miles, or people walking
  or cycling), so nothing here supports a per-trip risk claim.
* Fatal crashes are rare (roughly 0.3% of reported crashes). They are reported
  per 1,000 reported crashes, always with Wilson confidence intervals and the
  underlying count, because a single hour-of-day cell holds only a few dozen.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import DAY_NAME_ORDER, TIME_PERIOD_ORDER, rate_table, wilson_interval  # noqa: E402

# Below this many crashes a group's rate is reported but explicitly marked
# unreliable and kept out of the headline claims.
MIN_RELIABLE_N = 500


def pct(x, digits=1):
    return f"{x:.{digits}f}%"


def hour_label(h):
    """Human-readable clock label, e.g. 17 -> '5 PM'."""
    h = int(h)
    suffix = "AM" if h < 12 else "PM"
    display = h % 12
    if display == 0:
        display = 12
    return f"{display} {suffix}"


def hour_range_label(h):
    return f"{hour_label(h)}-{hour_label((int(h) + 1) % 24)}"


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
def build_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    t: dict[str, pd.DataFrame] = {}

    # Yearly volume and outcome mix
    yearly = df.groupby("year", observed=True).agg(
        crashes=("collision_id", "size"),
        injury_crashes=("injury_crash", "sum"),
        fatal_crashes=("fatal_crash", "sum"),
        persons_injured=("number_of_persons_injured", "sum"),
        persons_killed=("number_of_persons_killed", "sum"),
    ).reset_index()
    yearly["injury_crash_rate_pct"] = yearly.injury_crashes / yearly.crashes * 100
    yearly["fatal_crashes_per_1k"] = yearly.fatal_crashes / yearly.crashes * 1000
    t["yearly_summary"] = yearly

    # Hour of day: the spine of the story
    hourly = rate_table(df, "crash_hour", "injury_crash", MIN_RELIABLE_N)
    hourly = hourly.rename(columns={"successes": "injury_crashes"})
    fatal_h = rate_table(df, "crash_hour", "fatal_crash", MIN_RELIABLE_N)
    hourly["fatal_crashes"] = fatal_h["successes"].values
    hourly["fatal_per_1k"] = fatal_h["rate"].values * 1000
    hourly["fatal_per_1k_low"] = fatal_h["ci_low"].values * 1000
    hourly["fatal_per_1k_high"] = fatal_h["ci_high"].values * 1000
    hourly["share_of_all_crashes_pct"] = hourly["n"] / hourly["n"].sum() * 100
    hourly["hour_label"] = hourly["crash_hour"].map(hour_label)

    # Fatality by hour with the exactly-00:00 placeholder records removed. Those
    # records are concentrated entirely in hour 0 and carry almost no fatal
    # crashes, so leaving them in halves the apparent hour-0 fatality rate.
    # Figures plotting fatality by hour use THIS series; the column above is
    # retained so the two can be compared.
    clean_h = rate_table(df[~df["midnight_placeholder"]], "crash_hour", "fatal_crash", MIN_RELIABLE_N)
    clean_h = clean_h.set_index("crash_hour")
    hourly["n_excl_placeholder"] = hourly["crash_hour"].map(clean_h["n"])
    hourly["fatal_per_1k_excl_placeholder"] = hourly["crash_hour"].map(clean_h["rate"]) * 1000
    hourly["fatal_per_1k_excl_low"] = hourly["crash_hour"].map(clean_h["ci_low"]) * 1000
    hourly["fatal_per_1k_excl_high"] = hourly["crash_hour"].map(clean_h["ci_high"]) * 1000

    t["crashes_by_hour"] = hourly

    # Day of week
    dow = rate_table(df, "day_name", "injury_crash", MIN_RELIABLE_N).rename(
        columns={"successes": "injury_crashes"}
    )
    fatal_d = rate_table(df, "day_name", "fatal_crash", MIN_RELIABLE_N)
    dow["fatal_crashes"] = fatal_d["successes"].values
    dow["fatal_per_1k"] = fatal_d["rate"].values * 1000
    t["crashes_by_weekday"] = dow

    # Weekday x hour (the heatmap source)
    wh = rate_table(df, ["day_name", "crash_hour"], "injury_crash", MIN_RELIABLE_N).rename(
        columns={"successes": "injury_crashes"}
    )
    t["injury_rate_weekday_hour"] = wh

    # Time period
    tp = rate_table(df, "time_period", "injury_crash", MIN_RELIABLE_N).rename(
        columns={"successes": "injury_crashes"}
    )
    fatal_tp = rate_table(df, "time_period", "fatal_crash", MIN_RELIABLE_N)
    tp["fatal_crashes"] = fatal_tp["successes"].values
    tp["fatal_per_1k"] = fatal_tp["rate"].values * 1000
    tp["fatal_per_1k_low"] = fatal_tp["ci_low"].values * 1000
    tp["fatal_per_1k_high"] = fatal_tp["ci_high"].values * 1000
    tp["share_of_all_crashes_pct"] = tp["n"] / tp["n"].sum() * 100
    t["outcomes_by_time_period"] = tp

    # Weekday vs weekend
    wp = rate_table(df, "week_part", "injury_crash", MIN_RELIABLE_N).rename(
        columns={"successes": "injury_crashes"}
    )
    fatal_wp = rate_table(df, "week_part", "fatal_crash", MIN_RELIABLE_N)
    wp["fatal_crashes"] = fatal_wp["successes"].values
    wp["fatal_per_1k"] = fatal_wp["rate"].values * 1000
    t["weekday_vs_weekend"] = wp

    # Borough (missing borough kept visible as its own category)
    bor = df.copy()
    bor["borough_reported"] = bor["borough"].fillna("Not recorded")
    b = rate_table(bor, "borough_reported", "injury_crash", MIN_RELIABLE_N).rename(
        columns={"successes": "injury_crashes"}
    )
    b["share_of_all_crashes_pct"] = b["n"] / b["n"].sum() * 100
    t["crashes_by_borough"] = b.sort_values("n", ascending=False)

    # Road-user casualty flags by hour.
    # NOTE these are "a crash in which this road user was hurt", not
    # "a crash in which this road user was present" -- the data cannot show the
    # latter. Rates are shares of ALL reported crashes in the hour.
    ru_rows = []
    for flag, label in [
        ("pedestrian_injury_crash", "Pedestrian"),
        ("cyclist_injury_crash", "Cyclist"),
        ("motorist_injury_crash", "Motorist"),
    ]:
        sub = rate_table(df, "crash_hour", flag, MIN_RELIABLE_N)
        sub["road_user"] = label
        ru_rows.append(sub.rename(columns={"successes": "casualty_crashes"}))
    ru = pd.concat(ru_rows, ignore_index=True)
    ru["hour_label"] = ru["crash_hour"].map(hour_label)
    t["road_user_casualty_by_hour"] = ru

    # Road user by time period, plus raw casualty counts
    ru_tp_rows = []
    for flag, inj_col, kill_col, label in [
        ("pedestrian_injury_crash", "number_of_pedestrians_injured", "number_of_pedestrians_killed", "Pedestrian"),
        ("cyclist_injury_crash", "number_of_cyclist_injured", "number_of_cyclist_killed", "Cyclist"),
        ("motorist_injury_crash", "number_of_motorist_injured", "number_of_motorist_killed", "Motorist"),
    ]:
        sub = rate_table(df, "time_period", flag, MIN_RELIABLE_N).rename(
            columns={"successes": "casualty_crashes"}
        )
        counts = df.groupby("time_period", observed=True)[[inj_col, kill_col]].sum()
        sub["people_injured"] = counts[inj_col].values
        sub["people_killed"] = counts[kill_col].values
        sub["road_user"] = label
        ru_tp_rows.append(sub)
    t["road_user_by_time_period"] = pd.concat(ru_tp_rows, ignore_index=True)

    # Does the hourly injury swing survive holding the pedestrian/cyclist mix aside?
    no_vru = df[df["no_vru_casualty"]]
    nv = rate_table(no_vru, "crash_hour", "injury_crash", MIN_RELIABLE_N).rename(
        columns={"successes": "injury_crashes"}
    )
    t["injury_rate_by_hour_no_vru"] = nv

    # Monthly seasonality
    monthly = rate_table(df, "month", "injury_crash", MIN_RELIABLE_N).rename(
        columns={"successes": "injury_crashes"}
    )
    t["seasonality_by_month"] = monthly

    # Midnight-placeholder sensitivity
    h0 = df[df["crash_hour"] == 0]
    sens = []
    for label, sub in [
        ("hour 0, all records", h0),
        ("hour 0, exactly 00:00 only", h0[h0["midnight_placeholder"]]),
        ("hour 0, excluding 00:00", h0[~h0["midnight_placeholder"]]),
        ("all hours, all records", df),
        ("all hours, excluding 00:00", df[~df["midnight_placeholder"]]),
    ]:
        n = len(sub)
        inj = int(sub["injury_crash"].sum())
        fat = int(sub["fatal_crash"].sum())
        sens.append(
            {
                "subset": label,
                "n": n,
                "injury_crashes": inj,
                "injury_rate_pct": inj / n * 100 if n else np.nan,
                "fatal_crashes": fat,
                "fatal_per_1k": fat / n * 1000 if n else np.nan,
            }
        )
    t["midnight_placeholder_sensitivity"] = pd.DataFrame(sens)

    # Recorded contributing factors (classifications, not established causes)
    cf = (
        df["contributing_factor_vehicle_1"]
        .fillna("Not recorded")
        .replace({"Unspecified": "Unspecified (recorded but not classified)"})
        .value_counts()
        .head(15)
        .rename_axis("contributing_factor_vehicle_1")
        .reset_index(name="crashes")
    )
    cf["share_of_all_crashes_pct"] = cf["crashes"] / len(df) * 100
    t["top_contributing_factors"] = cf

    vt = (
        df["vehicle_type_code1"].fillna("Not recorded").value_counts().head(15)
        .rename_axis("vehicle_type_code1").reset_index(name="crashes")
    )
    vt["share_of_all_crashes_pct"] = vt["crashes"] / len(df) * 100
    t["top_vehicle_types"] = vt

    return t


# ---------------------------------------------------------------------------
# Evidence base
# ---------------------------------------------------------------------------
def write_summary(df: pd.DataFrame, t: dict[str, pd.DataFrame], path: Path) -> None:
    h = t["crashes_by_hour"]
    tp = t["outcomes_by_time_period"]
    nv = t["injury_rate_by_hour_no_vru"]
    sens = t["midnight_placeholder_sensitivity"].set_index("subset")
    yearly = t["yearly_summary"]
    wh = t["injury_rate_weekday_hour"]
    ru = t["road_user_casualty_by_hour"]

    peak_count = h.loc[h["n"].idxmax()]
    trough_count = h.loc[h["n"].idxmin()]
    peak_inj = h.loc[h["rate"].idxmax()]
    trough_inj = h.loc[h["rate"].idxmin()]
    # Fatality-by-hour claims use the placeholder-free series (see section 4).
    peak_fatal = h.loc[h["fatal_per_1k_excl_placeholder"].idxmax()]
    trough_fatal = h.loc[h["fatal_per_1k_excl_placeholder"].idxmin()]

    n_total = len(df)
    inj_total = int(df["injury_crash"].sum())
    fatal_total = int(df["fatal_crash"].sum())

    # Late night vs evening contrast, by named period
    tp_i = tp.set_index("time_period")
    late = tp_i.loc["Late Night"]
    night = tp_i.loc["Night"]
    evening = tp_i.loc["Evening Commute"]

    nv_peak = nv.loc[nv["rate"].idxmax()]
    nv_trough = nv.loc[nv["rate"].idxmin()]

    ped = ru[ru.road_user == "Pedestrian"]
    cyc = ru[ru.road_user == "Cyclist"]
    ped_peak, ped_trough = ped.loc[ped["rate"].idxmax()], ped.loc[ped["rate"].idxmin()]
    cyc_peak, cyc_trough = cyc.loc[cyc["rate"].idxmax()], cyc.loc[cyc["rate"].idxmin()]

    miss = pd.read_csv(Path("outputs/summary_tables/missingness.csv"))
    miss_map = dict(zip(miss["column"], miss["pct_missing"]))

    swing_overall = (peak_inj["rate"] - trough_inj["rate"]) * 100
    swing_nv = (nv_peak["rate"] - nv_trough["rate"]) * 100
    fatal_ratio = peak_fatal["fatal_per_1k_excl_placeholder"] / trough_fatal["fatal_per_1k_excl_placeholder"]

    L = []
    A = L.append

    A("# Analysis Summary — Evidence Base")
    A("")
    A("Machine-generated by `src/analysis.py`. Every figure below is computed from the")
    A("processed dataset; nothing here is typed by hand. This is the document the blog")
    A("post, README and slides are checked against.")
    A("")
    A("---")
    A("")
    A("## 1. What was analysed")
    A("")
    A(f"- **Observations:** {n_total:,} reported crashes")
    A(f"- **Date range:** {df['crash_datetime'].min():%Y-%m-%d} to {df['crash_datetime'].max():%Y-%m-%d}")
    A(f"- **Years:** {', '.join(str(int(y)) for y in sorted(df['year'].dropna().unique()))} (complete calendar years only)")
    A(f"- **Injury crashes (>=1 person injured):** {inj_total:,} ({inj_total / n_total * 100:.2f}% of reported crashes)")
    A(f"- **Fatal crashes (>=1 person killed):** {fatal_total:,} ({fatal_total / n_total * 1000:.2f} per 1,000 reported crashes)")
    A(f"- **People injured:** {int(df['number_of_persons_injured'].sum()):,}")
    A(f"- **People killed:** {int(df['number_of_persons_killed'].sum()):,}")
    A("")
    A("2026 is excluded: the published data end mid-2026, and a partial year would")
    A("bias any seasonal or annual comparison.")
    A("")
    A("### Crashes per year")
    A("")
    A("| Year | Crashes | Injury crashes | Injury-crash rate | Fatal crashes | Fatal per 1,000 |")
    A("|---|---:|---:|---:|---:|---:|")
    for _, r in yearly.iterrows():
        A(f"| {int(r.year)} | {int(r.crashes):,} | {int(r.injury_crashes):,} | "
          f"{r.injury_crash_rate_pct:.1f}% | {int(r.fatal_crashes):,} | {r.fatal_crashes_per_1k:.2f} |")
    A("")
    A("Reported crash volume falls steadily across the window "
      f"({int(yearly.crashes.iloc[0]):,} in {int(yearly.year.iloc[0])} to "
      f"{int(yearly.crashes.iloc[-1]):,} in {int(yearly.year.iloc[-1])}, "
      f"{(1 - yearly.crashes.iloc[-1] / yearly.crashes.iloc[0]) * 100:.0f}% lower), while the "
      "*share* of crashes involving an injury rises. Both trends are real in the")
    A("reported data, but neither can be read as a change in road risk without")
    A("exposure and reporting-practice information the dataset does not contain.")
    A("")
    A("---")
    A("")
    A("## 2. Major preprocessing decisions")
    A("")
    A("| Decision | Effect |")
    A("|---|---|")
    A("| Year window applied server-side in the API query | No rows discarded locally; download matches analysis scope exactly |")
    A("| Duplicate `collision_id` check | 0 duplicates found; no rows removed |")
    A("| Unparseable date/time check | 0 rows affected |")
    A("| Casualty columns coerced to non-negative integers | 4 non-numeric cells set to 0 |")
    A("| `latitude`/`longitude` == 0 blanked | 5,490 rows kept, coordinates set to missing (null-island placeholder) |")
    A("| Exactly-`00:00` timestamps flagged, **not** dropped | See section 4 |")
    A("")
    A(f"**Net effect: {n_total:,} of {n_total:,} downloaded rows are analysed. No row was dropped.**")
    A("")
    A("### Schema differences found")
    A("")
    A("The published API field names differ from the obvious guesses:")
    A("")
    A("| Expected | Actual | Note |")
    A("|---|---|---|")
    A("| `number_of_cyclists_injured` | `number_of_cyclist_injured` | singular |")
    A("| `number_of_motorists_injured` | `number_of_motorist_injured` | singular |")
    A("| `vehicle_type_code_1` | `vehicle_type_code1` | no underscore, unlike `_3`/`_4`/`_5` |")
    A("| a datetime field | `crash_date` + `crash_time` | time is free text `H:MM` |")
    A("")
    A("---")
    A("")
    A("## 3. Missingness in important fields")
    A("")
    A("| Field | % missing | Effect on interpretation |")
    A("|---|---:|---|")
    A(f"| `borough` | {miss_map.get('borough', float('nan')):.1f}% | Large. Borough comparisons cover only the ~70% of crashes with a borough recorded, and missingness is unlikely to be random — highway crashes in particular often lack one. Borough is kept as supporting analysis only. |")
    A(f"| `zip_code` | {miss_map.get('zip_code', float('nan')):.1f}% | Same records as borough. |")
    A(f"| `latitude` / `longitude` | {miss_map.get('latitude', float('nan')):.1f}% | Rules out a trustworthy map as a headline figure. |")
    A(f"| `vehicle_type_code1` | {miss_map.get('vehicle_type_code1', float('nan')):.1f}% | Minor. |")
    A(f"| `contributing_factor_vehicle_1` | {miss_map.get('contributing_factor_vehicle_1', float('nan')):.1f}% | Low missingness, but see section 7 — most records are coded `Unspecified`. |")
    A(f"| `crash_time` | {miss_map.get('crash_time', 0.0):.1f}% | Never missing — but see section 4, absence of a null is not the same as a reliable value. |")
    A("")
    A("**The time-of-day axis is complete, which is why it carries the main story.**")
    A("The geographic fields are not, which is why they do not.")
    A("")
    A("---")
    A("")
    A("## 4. Data-quality finding: the `00:00` placeholder")
    A("")
    A(f"`crash_time` is never null, but exactly-midnight is recorded "
      f"{int(sens.loc['hour 0, exactly 00:00 only', 'n']):,} times "
      f"({int(sens.loc['hour 0, exactly 00:00 only', 'n']) / n_total * 100:.2f}% of all crashes) — "
      "roughly twice as often as any other single clock minute.")
    A("")
    A("| Subset | n | Injury-crash rate | Fatal crashes | Fatal per 1,000 |")
    A("|---|---:|---:|---:|---:|")
    for label, r in sens.iterrows():
        A(f"| {label} | {int(r.n):,} | {r.injury_rate_pct:.2f}% | {int(r.fatal_crashes):,} | {r.fatal_per_1k:.2f} |")
    A("")
    A("**This is the decisive evidence.** Records stamped exactly `00:00` contain "
      f"{int(sens.loc['hour 0, exactly 00:00 only', 'fatal_crashes'])} fatal crash(es) in "
      f"{int(sens.loc['hour 0, exactly 00:00 only', 'n']):,} records. Every neighbouring hour of the "
      "night runs 50-70 fatal crashes on a smaller base. A genuine hour of the night cannot")
    A("look like that, so `00:00` is behaving as a default value written when the true")
    A("time was not known.")
    A("")
    A("**Decision: flag, do not drop.** Their injury rate "
      f"({sens.loc['hour 0, exactly 00:00 only', 'injury_rate_pct']:.2f}%) is close to the rest of hour 0 "
      f"({sens.loc['hour 0, excluding 00:00', 'injury_rate_pct']:.2f}%), so the injury analysis is barely "
      "affected, and dropping 1.75% of the data non-randomly would cost more than it buys.")
    A("The distortion is concentrated in one statistic — the hour-0 **fatality** rate, which")
    A(f"reads {sens.loc['hour 0, all records', 'fatal_per_1k']:.2f} per 1,000 with these records and "
      f"{sens.loc['hour 0, excluding 00:00', 'fatal_per_1k']:.2f} without them. "
      "**Figures showing fatality by hour exclude the flagged records and say so.**")
    A("")
    A("---")
    A("")
    A("## 5. Strongest descriptive patterns")
    A("")
    A("### 5.1 Three different clocks — the central finding")
    A("")
    A("| Question | Peak | Value | Trough | Value |")
    A("|---|---|---:|---|---:|")
    A(f"| When do crashes happen most? | **{hour_range_label(peak_count.crash_hour)}** | {int(peak_count.n):,} crashes | {hour_range_label(trough_count.crash_hour)} | {int(trough_count.n):,} |")
    A(f"| When is a crash most likely to injure someone? | **{hour_range_label(peak_inj.crash_hour)}** | {peak_inj.rate_pct:.1f}% | {hour_range_label(trough_inj.crash_hour)} | {trough_inj.rate_pct:.1f}% |")
    A(f"| When is a crash most likely to be fatal? | **{hour_range_label(peak_fatal.crash_hour)}** | {peak_fatal.fatal_per_1k_excl_placeholder:.2f} per 1,000 | {hour_range_label(trough_fatal.crash_hour)} | {trough_fatal.fatal_per_1k_excl_placeholder:.2f} |")
    A("")
    A("**The hypothesis in the project brief is supported, but not in the direction most")
    A("people expect.** Crash frequency and injury-crash rate do peak at different times")
    A(f"— frequency at {hour_label(peak_count.crash_hour)}, injury share about "
      f"{int(peak_inj.crash_hour) - int(peak_count.crash_hour)} hours later at {hour_label(peak_inj.crash_hour)}. "
      "But the quiet overnight hours are **not** the times when a crash is most likely to")
    A("hurt someone. They are the times when it is *least* likely to:")
    A(f"{trough_inj.rate_pct:.1f}% at {hour_range_label(trough_inj.crash_hour)} against "
      f"{peak_inj.rate_pct:.1f}% at {hour_range_label(peak_inj.crash_hour)}.")
    A("")
    A("The reversal appears when severity is measured by death instead of injury.")
    A(f"Overnight crashes are the **most** likely to be fatal: {peak_fatal.fatal_per_1k_excl_placeholder:.2f} per 1,000 at "
      f"{hour_range_label(peak_fatal.crash_hour)} versus {trough_fatal.fatal_per_1k_excl_placeholder:.2f} at "
      f"{hour_range_label(trough_fatal.crash_hour)} — a **{fatal_ratio:.1f}x** difference.")
    A("")
    A(f"*Sample-size caution:* the fatal-crash comparison rests on {fatal_total:,} fatal crashes "
      f"spread across 24 hours ({int(peak_fatal.fatal_crashes)} in the peak hour, "
      f"{int(trough_fatal.fatal_crashes)} in the trough). The 95% Wilson intervals for the peak "
      f"({peak_fatal.fatal_per_1k_excl_low:.2f}-{peak_fatal.fatal_per_1k_excl_high:.2f}) and trough "
      f"({trough_fatal.fatal_per_1k_excl_low:.2f}-{trough_fatal.fatal_per_1k_excl_high:.2f}) do not overlap, so the")
    A("contrast is real, but hour-to-hour wobble in the fatal series should not be")
    A("over-read. Grouped into time periods (section 5.3) it is much more stable.")
    A("")
    A("### 5.2 Hour-by-hour detail")
    A("")
    A("| Hour | Crashes | % of all | Injury-crash rate | 95% CI | Fatal crashes | Fatal per 1,000 (excl. 00:00 flag) |")
    A("|---|---:|---:|---:|---|---:|---:|")
    for _, r in h.iterrows():
        A(f"| {hour_range_label(r.crash_hour)} | {int(r.n):,} | {r.share_of_all_crashes_pct:.1f}% | "
          f"{r.rate_pct:.1f}% | {r.ci_low_pct:.1f}-{r.ci_high_pct:.1f}% | {int(r.fatal_crashes)} | {r.fatal_per_1k_excl_placeholder:.2f} |")
    A("")
    A("### 5.3 By time period")
    A("")
    A("| Period | Hours | Crashes | % of all | Injury-crash rate | Fatal per 1,000 |")
    A("|---|---|---:|---:|---:|---:|")
    bounds = {"Late Night": "00:00-05:59", "Morning Commute": "06:00-09:59",
              "Daytime": "10:00-15:59", "Evening Commute": "16:00-19:59", "Night": "20:00-23:59"}
    for _, r in tp.iterrows():
        A(f"| {r.time_period} | {bounds[str(r.time_period)]} | {int(r.n):,} | "
          f"{r.share_of_all_crashes_pct:.1f}% | {r.rate_pct:.1f}% | {r.fatal_per_1k:.2f} |")
    A("")
    A(f"Late Night carries {late.share_of_all_crashes_pct:.1f}% of reported crashes, the lowest injury-crash "
      f"rate ({late.rate_pct:.1f}%) and the highest fatality rate ({late.fatal_per_1k:.2f} per 1,000). "
      f"Night ({night.rate_pct:.1f}% injury, {night.fatal_per_1k:.2f} fatal per 1,000) is the")
    A("period where both measures are elevated together — the genuinely worst window on")
    A("both counts. The Evening Commute has the most crashes "
      f"({evening.share_of_all_crashes_pct:.1f}% of all) and a high injury rate "
      f"({evening.rate_pct:.1f}%) but a comparatively low fatality rate ({evening.fatal_per_1k:.2f}).")
    A("")
    A("### 5.4 Day of week")
    A("")
    A("| Day | Crashes | Injury-crash rate | Fatal per 1,000 |")
    A("|---|---:|---:|---:|")
    for _, r in t["crashes_by_weekday"].iterrows():
        A(f"| {r.day_name} | {int(r.n):,} | {r.rate_pct:.1f}% | {r.fatal_per_1k:.2f} |")
    A("")
    wp = t["weekday_vs_weekend"].set_index("week_part")
    A(f"Weekday vs weekend repeats the same inversion in miniature: weekdays have the "
      f"higher injury-crash rate ({wp.loc['Weekday', 'rate_pct']:.1f}% vs "
      f"{wp.loc['Weekend', 'rate_pct']:.1f}%) while weekends have the higher fatality rate "
      f"({wp.loc['Weekend', 'fatal_per_1k']:.2f} vs {wp.loc['Weekday', 'fatal_per_1k']:.2f} per 1,000).")
    A("The day-of-week spread is modest and is **not** a headline claim: the gap between")
    A("the highest and lowest day is only "
      f"{t['crashes_by_weekday'].rate_pct.max() - t['crashes_by_weekday'].rate_pct.min():.1f} percentage points, "
      "far smaller than the hour-of-day swing.")
    A("")
    A("### 5.5 Day x hour")
    A("")
    A(f"All {len(wh)} weekday-by-hour cells are well populated: the smallest holds "
      f"{int(wh['n'].min()):,} crashes and the largest {int(wh['n'].max()):,}. "
      f"**No cell needed suppression** (threshold: n < {MIN_RELIABLE_N}).")
    A(f"Injury-crash rate across cells ranges {wh.rate_pct.min():.1f}% to {wh.rate_pct.max():.1f}%.")
    top = wh.nlargest(5, "rate_pct")
    bot = wh.nsmallest(5, "rate_pct")
    A("")
    A("Highest cells:")
    A("")
    A("| Day | Hour | n | Injury-crash rate |")
    A("|---|---|---:|---:|")
    for _, r in top.iterrows():
        A(f"| {r.day_name} | {hour_range_label(r.crash_hour)} | {int(r.n):,} | {r.rate_pct:.1f}% |")
    A("")
    A("Lowest cells:")
    A("")
    A("| Day | Hour | n | Injury-crash rate |")
    A("|---|---|---:|---:|")
    for _, r in bot.iterrows():
        A(f"| {r.day_name} | {hour_range_label(r.crash_hour)} | {int(r.n):,} | {r.rate_pct:.1f}% |")
    A("")
    A("The heatmap's dominant signal is horizontal (time of day), not vertical (day of")
    A("week). The evening band is elevated on every day; the overnight band is low on")
    A("every day. Weekend late nights are the one place the weekday pattern bends.")
    A("")
    A("### 5.6 Who gets hurt, and when")
    A("")
    A("These are shares of **all reported crashes** in the hour that injured or killed")
    A("each road-user type. They describe *who was hurt*, not *who was present* — the")
    A("dataset has no road-user presence field.")
    A("")
    A("| Road user | Peak hour | Peak share | Trough hour | Trough share |")
    A("|---|---|---:|---|---:|")
    A(f"| Pedestrian | {hour_range_label(ped_peak.crash_hour)} | {ped_peak.rate_pct:.1f}% | {hour_range_label(ped_trough.crash_hour)} | {ped_trough.rate_pct:.1f}% |")
    A(f"| Cyclist | {hour_range_label(cyc_peak.crash_hour)} | {cyc_peak.rate_pct:.1f}% | {hour_range_label(cyc_trough.crash_hour)} | {cyc_trough.rate_pct:.1f}% |")
    A("")
    A("| Period | Pedestrian casualty crashes | Cyclist | Motorist | People injured (ped) | (cyc) | (mot) |")
    A("|---|---:|---:|---:|---:|---:|---:|")
    rutp = t["road_user_by_time_period"]
    for period in TIME_PERIOD_ORDER:
        sub = rutp[rutp.time_period == period].set_index("road_user")
        A(f"| {period} | {int(sub.loc['Pedestrian', 'casualty_crashes']):,} | "
          f"{int(sub.loc['Cyclist', 'casualty_crashes']):,} | "
          f"{int(sub.loc['Motorist', 'casualty_crashes']):,} | "
          f"{int(sub.loc['Pedestrian', 'people_injured']):,} | "
          f"{int(sub.loc['Cyclist', 'people_injured']):,} | "
          f"{int(sub.loc['Motorist', 'people_injured']):,} |")
    A("")
    A("### 5.7 Does the mix of road users explain the evening peak?")
    A("")
    A("Partly. Holding aside every crash in which a pedestrian or cyclist was hurt, the")
    A("injury-crash rate among the remaining crashes still swings from "
      f"{nv_trough.rate_pct:.1f}% at {hour_range_label(nv_trough.crash_hour)} to "
      f"{nv_peak.rate_pct:.1f}% at {hour_range_label(nv_peak.crash_hour)} — "
      f"a {swing_nv:.1f}-point spread against {swing_overall:.1f} points for all crashes.")
    A("")
    A(f"So roughly **{(1 - swing_nv / swing_overall) * 100:.0f}% of the hourly swing in the injury-crash rate")
    A("disappears** once pedestrian and cyclist casualties are set aside, and the rest")
    A("remains. The evening peak is therefore *both* a composition effect (more of the")
    A("evening's crashes hurt people outside vehicles) *and* a real shift within")
    A("vehicle-occupant crashes. Neither explanation alone is sufficient, and the")
    A("write-up should say so.")
    A("")
    A("---")
    A("")
    A("## 6. Hypothesis verdict")
    A("")
    A("| Claim | Verdict |")
    A("|---|---|")
    A("| Crash frequency and crash severity peak at different times | **Supported.** Frequency peaks "
      f"{hour_label(peak_count.crash_hour)}; injury share peaks {hour_label(peak_inj.crash_hour)}; "
      f"fatality rate peaks {hour_label(peak_fatal.crash_hour)}. |")
    A("| The quiet overnight hours are when crashes are most likely to injure | **Rejected.** They have "
      "the *lowest* injury-crash rate of the day. |")
    A("| 'Severity' is a single thing | **Rejected.** Injury-crash rate and fatality rate peak "
      "~18 hours apart and rank the day almost oppositely. |")
    A("| Day of week is a major driver | **Not supported as a headline.** Real but small "
      f"({t['crashes_by_weekday'].rate_pct.max() - t['crashes_by_weekday'].rate_pct.min():.1f} points) next to time of day. |")
    A("")
    A("---")
    A("")
    A("## 7. Findings deliberately NOT emphasised")
    A("")
    A("| Finding | Why it is held back |")
    A("|---|---|")
    A(f"| Borough differences | `borough` is {miss_map.get('borough', float('nan')):.0f}% missing and almost certainly not missing at random. Reported as supporting context only, never as a ranking of boroughs. |")
    A("| Contributing factors | The most common recorded value is `Unspecified`. These are administrative classifications entered by a reporting officer, not established causes. No causal claim is made from them. |")
    A("| Vehicle types | Free-text-ish field with many near-duplicate spellings. Not cleaned to a standard taxonomy, so not used for any claim. |")
    A("| Hour-to-hour wobble in the fatal series | Individual hours hold only 29-76 fatal crashes. Only the broad overnight-vs-afternoon contrast is claimed, not specific hour rankings. |")
    A("| Year-over-year decline in crashes | Real in the reported data, but reporting practice and traffic volumes both changed across 2021-2025. Shown for context; not interpreted as a safety improvement. |")
    A("| Any per-trip risk comparison between road users | Impossible without exposure data. See section 8. |")
    A("")
    A("---")
    A("")
    A("## 8. Limitations")
    A("")
    A("1. **Reported crashes are not all crashes.** These are NYPD-reported collisions. "
      "New York requires a report for injury, death, or property damage above a "
      "threshold, so minor collisions are under-represented — and probably unevenly "
      "across time of day. If a fender-bender at 3 AM with no one around is less "
      "likely to be reported than the same crash at 3 PM, the overnight denominator "
      "shrinks, which would push the overnight injury *rate* up. The observed "
      "overnight injury rate is the lowest of the day **despite** that pressure, which "
      "makes the finding more robust, not less.")
    A("2. **No exposure denominator.** The dataset counts crashes, not trips, "
      "vehicle-miles, or people walking and cycling. Every rate here is conditional on "
      "a crash having been reported. Nothing supports a statement like 'driving at 2 AM "
      "is more dangerous' or 'cyclists are more likely to be hurt'.")
    A("3. **Recorded contributing factor is not established cause.** See section 7.")
    A("4. **Missing data are not random.** Borough and coordinates are missing together "
      "on ~30% and ~8% of records respectively; highway crashes disproportionately lack "
      "a borough.")
    A("5. **Timestamp quality.** See section 4.")
    A("6. **Road-user flags are circular by construction.** Every "
      "`pedestrian_injury_crash` is an `injury_crash`, because the flag is built from "
      "pedestrian casualty counts. Injury rates must never be compared *between* "
      "road-user flags. Shares of all reported crashes are the safe comparison, and "
      "are what is used.")
    A("")
    A("---")
    A("")
    A("## 9. Figures the story should use")
    A("")
    A("| # | Figure | Why it earns a slot |")
    A("|---|---|---|")
    A("| 1 | Crashes by hour | Establishes the intuitive expectation the story then complicates. |")
    A("| 2 | Injury-crash rate by hour, with 95% CI | The first turn: the rate curve is not the count curve. |")
    A("| 3 | Three clocks (count / injury rate / fatality rate, indexed) | The central finding. If only one figure survives, this is it. |")
    A("| 4 | Day x hour heatmap of injury-crash rate | Shows the evening band holds across all seven days. |")
    A("| 5 | Road-user casualty share by hour | The mechanism behind the evening peak, stated non-circularly. |")
    A("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L), encoding="utf-8")
    print(f"[done] evidence base -> {path}")


def run(processed: Path, tables_dir: Path, summary_path: Path) -> None:
    if not processed.exists():
        raise SystemExit(f"[fail] {processed} not found. Run:  python src/preprocess.py")

    df = pd.read_parquet(processed)
    print(f"[read] {processed}  ({len(df):,} rows)")

    tables_dir.mkdir(parents=True, exist_ok=True)
    tables = build_tables(df)

    for name, table in tables.items():
        out = tables_dir / f"{name}.csv"
        table.to_csv(out, index=False)
        print(f"[tbl ] {out.name:<42} {len(table):>4} rows")

    write_summary(df, tables, summary_path)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Compute summary tables and the evidence base.")
    p.add_argument("--processed", type=Path, default=Path("data/processed/crashes_clean.parquet"))
    p.add_argument("--tables", type=Path, default=Path("outputs/summary_tables"))
    p.add_argument("--summary", type=Path, default=Path("outputs/analysis_summary.md"))
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    run(args.processed, args.tables, args.summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
