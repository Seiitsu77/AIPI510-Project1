"""Build the final figures from the summary tables.

Run after src/analysis.py:

    python src/visualize.py

Every figure is drawn from a CSV in outputs/summary_tables/, never from the raw
data, so what appears in a chart is exactly what the evidence base reports.

Figures are written to figures/ as both PNG (200 dpi, for slides and the blog)
and SVG (for crisp scaling). Each one carries a plain-language title, units on
the axes, and the denominator it was computed from.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import DAY_NAME_ORDER  # noqa: E402

# ---------------------------------------------------------------------------
# House style
# ---------------------------------------------------------------------------
INK = "#1d2433"
MUTED = "#6b7280"
GRID = "#e2e5ea"

BLUE = "#2f6f9f"      # crash counts / neutral volume
AMBER = "#d1741f"     # injury-crash rate
CRIMSON = "#9e2a2b"   # fatality

ROAD_USER_COLOURS = {"Pedestrian": "#b5483d", "Cyclist": "#2f6f9f", "Motorist": "#8a8f98"}

plt.rcParams.update(
    {
        "figure.dpi": 110,
        "savefig.dpi": 200,
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.labelsize": 11.5,
        "axes.labelcolor": INK,
        "axes.edgecolor": GRID,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
    }
)

HOUR_TICKS = [0, 3, 6, 9, 12, 15, 18, 21]
HOUR_TICK_LABELS = ["12 AM", "3 AM", "6 AM", "9 AM", "noon", "3 PM", "6 PM", "9 PM"]

# Repeated on every figure so a chart lifted onto a slide still carries it.
CONDITIONAL_NOTE = (
    "Rates are the share of REPORTED crashes, not per-trip risk: this dataset counts crashes, "
    "not how many people were\ndriving, walking or cycling at the time."
)
SOURCE_NOTE = "Source: NYC Open Data / NYPD, Motor Vehicle Collisions - Crashes, 2021-2025 (487,914 reported crashes)."


def style_hour_axis(ax, xlabel=True):
    ax.set_xticks(HOUR_TICKS)
    ax.set_xticklabels(HOUR_TICK_LABELS)
    ax.set_xlim(-0.7, 23.7)
    if xlabel:
        ax.set_xlabel("Time of day (hour the crash was recorded)")


def tidy(ax):
    ax.yaxis.grid(True, color=GRID, linewidth=0.9)
    ax.set_axisbelow(True)


def add_titles(fig, title, subtitle, x=0.075, title_y=0.975, sub_y=0.905):
    """Left-aligned title block placed in space reserved by subplots_adjust.

    ax.set_title(pad=...) plus a text at y>1 in axes coordinates collides as
    soon as either string is long, so the header gets its own reserved band and
    figure coordinates instead.
    """
    fig.text(x, title_y, title, ha="left", va="top", fontsize=17,
             fontweight="bold", color=INK)
    fig.text(x, sub_y, subtitle, ha="left", va="top", fontsize=11.5,
             color=MUTED, linespacing=1.4)


def add_caption(fig, text, x=0.075, y=0.085):
    fig.text(x, y, text, ha="left", va="top", fontsize=8.5,
             color=MUTED, linespacing=1.55)


def save(fig, outdir: Path, name: str):
    outdir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(outdir / f"{name}.{ext}")
    plt.close(fig)
    print(f"[fig ] {name}.png / .svg")


# ---------------------------------------------------------------------------
# Figure 1 -- when crashes happen
# ---------------------------------------------------------------------------
def fig1_crash_counts(h: pd.DataFrame, outdir: Path):
    fig, ax = plt.subplots(figsize=(10, 6.0))
    fig.subplots_adjust(top=0.80, bottom=0.20, left=0.10, right=0.97)

    peak_hour = int(h.loc[h["n"].idxmax(), "crash_hour"])
    peak_n = int(h["n"].max())
    trough_hour = int(h.loc[h["n"].idxmin(), "crash_hour"])
    trough_n = int(h["n"].min())

    colours = [AMBER if hh == peak_hour else BLUE for hh in h["crash_hour"]]
    ax.bar(h["crash_hour"], h["n"], color=colours, width=0.78)

    ax.set_ylabel("Reported crashes")
    ax.set_ylim(0, peak_n * 1.30)
    style_hour_axis(ax)
    tidy(ax)
    ax.yaxis.set_major_formatter(lambda v, _: f"{int(v):,}")

    ax.annotate(
        f"Busiest hour of the day:\n{peak_n:,} crashes at 5-6 PM",
        xy=(peak_hour, peak_n), xytext=(peak_hour - 7.6, peak_n * 1.17),
        fontsize=11, color=INK, fontweight="bold", va="center",
        arrowprops=dict(arrowstyle="-", color=AMBER, lw=1.6,
                        connectionstyle="angle,angleA=0,angleB=90,rad=6"),
    )
    # Sits in the empty band above the pre-dawn bars, not over the 7 AM bar.
    ax.annotate(
        f"Quietest: {trough_n:,} at 3-4 AM",
        xy=(trough_hour, trough_n), xytext=(1.1, peak_n * 0.55),
        fontsize=10.5, color=MUTED, va="center", ha="left", zorder=6,
        arrowprops=dict(arrowstyle="-", color=MUTED, lw=1.1),
    )

    add_titles(
        fig,
        "When Do New York City Crashes Happen?",
        "Reported motor-vehicle crashes by time of day, 2021-2025",
    )
    add_caption(fig, SOURCE_NOTE)
    save(fig, outdir, "fig1_crashes_by_hour")


# ---------------------------------------------------------------------------
# Figure 2 -- when crashes hurt people
# ---------------------------------------------------------------------------
def fig2_injury_rate(h: pd.DataFrame, outdir: Path):
    fig, ax = plt.subplots(figsize=(10, 6.2))
    fig.subplots_adjust(top=0.80, bottom=0.22, left=0.10, right=0.97)

    ax.fill_between(h["crash_hour"], h["ci_low_pct"], h["ci_high_pct"],
                    color=AMBER, alpha=0.20, lw=0)
    ax.plot(h["crash_hour"], h["rate_pct"], color=AMBER, lw=2.6, zorder=3)
    ax.scatter(h["crash_hour"], h["rate_pct"], color=AMBER, s=26, zorder=4)

    peak = h.loc[h["rate_pct"].idxmax()]
    trough = h.loc[h["rate_pct"].idxmin()]
    count_peak_hour = int(h.loc[h["n"].idxmax(), "crash_hour"])

    ax.set_ylabel("Reported crashes involving an injury (%)")
    ax.set_ylim(29, 51)
    style_hour_axis(ax)
    tidy(ax)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")

    # Reference line: the hour with the MOST crashes is not the hour with the
    # highest injury share. That gap is the point of the figure.
    ax.axvline(count_peak_hour, color=BLUE, lw=1.4, ls=(0, (4, 3)), zorder=1)
    ax.text(count_peak_hour - 0.4, 29.6, "busiest hour for crashes",
            rotation=90, ha="right", va="bottom", fontsize=9.5, color=BLUE)

    ax.annotate(
        f"Highest: {peak.rate_pct:.0f}% of crashes\ninjure someone (9-10 PM)",
        xy=(int(peak.crash_hour), peak.rate_pct),
        xytext=(11.0, 49.4),
        fontsize=11, fontweight="bold", color=INK, va="center",
        arrowprops=dict(arrowstyle="-", color=AMBER, lw=1.6),
    )
    ax.annotate(
        f"Lowest: {trough.rate_pct:.0f}% (2-3 AM)",
        xy=(int(trough.crash_hour), trough.rate_pct),
        xytext=(4.6, 30.7),
        fontsize=10.5, color=MUTED, va="center",
        arrowprops=dict(arrowstyle="-", color=MUTED, lw=1.1),
    )

    add_titles(
        fig,
        "When Is a Crash Most Likely to Hurt Someone?",
        "Share of reported crashes that injured at least one person, by time of day",
    )
    add_caption(
        fig,
        "Shaded band shows the 95% confidence interval. Vertical axis starts at 29%.\n" + CONDITIONAL_NOTE,
        y=0.115,
    )
    save(fig, outdir, "fig2_injury_rate_by_hour")


# ---------------------------------------------------------------------------
# Figure 3 -- the central finding
# ---------------------------------------------------------------------------
def fig3_three_clocks(h: pd.DataFrame, outdir: Path):
    """Three panels, three y-axes, three different peaks.

    Deliberately NOT normalised onto one axis: the three quantities have
    genuinely different units (a count, a percentage, a per-1,000 rate), and
    indexing them to a common scale would invite the reader to compare
    magnitudes that are not comparable. A shared x-axis and marked peaks carry
    the comparison instead.
    """
    fig, axes = plt.subplots(3, 1, figsize=(10, 10.5), sharex=True)
    fig.subplots_adjust(top=0.855, bottom=0.155, left=0.115, right=0.97, hspace=0.42)

    panels = [
        dict(ax=axes[0], y=h["n"], colour=BLUE,
             title="1.  How many crashes happen",
             ylabel="Reported crashes",
             fmt=lambda v, _: f"{int(v / 1000)}k",
             note="Peak: 5-6 PM", zero=True),
        dict(ax=axes[1], y=h["rate_pct"], colour=AMBER,
             title="2.  How often a crash injures someone",
             ylabel="Crashes with an injury (%)",
             fmt=lambda v, _: f"{v:.0f}%",
             note="Peak: 9-10 PM", zero=False),
        dict(ax=axes[2], y=h["fatal_per_1k_excl_placeholder"], colour=CRIMSON,
             title="3.  How often a crash is fatal",
             ylabel="Fatal crashes per 1,000",
             fmt=lambda v, _: f"{v:.0f}",
             note="Peak: 3-4 AM", zero=True),
    ]

    for p in panels:
        ax, y = p["ax"], p["y"]
        ax.plot(h["crash_hour"], y, color=p["colour"], lw=2.8, zorder=3)

        lo, hi = float(y.min()), float(y.max())
        if p["zero"]:
            ax.fill_between(h["crash_hour"], 0, y, color=p["colour"], alpha=0.12, lw=0)
            ax.set_ylim(0, hi * 1.28)
        else:
            # Rate panel: zoomed so a real 12-point swing is visible rather
            # than flattened against a zero baseline. Called out in the caption.
            span = hi - lo
            ax.set_ylim(lo - span * 0.22, hi + span * 0.42)

        peak_i = int(np.argmax(y.values))
        peak_hour = int(h["crash_hour"].iloc[peak_i])
        peak_val = float(y.iloc[peak_i])
        ax.scatter([peak_hour], [peak_val], color=p["colour"], s=120,
                   zorder=5, edgecolor="white", linewidth=2)

        # Place the label on whichever side of the peak has room, lifted clear
        # of the line so it never sits on top of the series.
        y0, y1 = ax.get_ylim()
        lift = (y1 - y0) * 0.085
        if peak_hour < 12:
            tx, ha = peak_hour + 1.1, "left"
        else:
            tx, ha = peak_hour - 1.1, "right"
        ax.annotate(p["note"], xy=(tx, peak_val + lift), ha=ha, va="bottom",
                    fontsize=11.5, fontweight="bold", color=p["colour"])

        ax.set_title(p["title"], loc="left", fontsize=13.5,
                     fontweight="bold", color=INK, pad=9)
        ax.set_ylabel(p["ylabel"])
        ax.yaxis.set_major_formatter(p["fmt"])
        tidy(ax)

    style_hour_axis(axes[2])
    for ax in axes[:2]:
        ax.set_xlabel("")

    add_titles(
        fig,
        "Three Different Clocks",
        "The busiest hour for crashes, the hour crashes most often injure someone, and the hour\n"
        "they are most often fatal are three different times of day.",
        x=0.085, title_y=0.985, sub_y=0.935,
    )
    add_caption(
        fig,
        "Panel 2's vertical axis is zoomed to show the shape of a 12-point swing; panels 1 and 3 start at zero.\n"
        "Panel 3 excludes records timestamped exactly 00:00, which behave as a placeholder for an unknown time.\n"
        + CONDITIONAL_NOTE,
        x=0.085, y=0.072,
    )
    save(fig, outdir, "fig3_three_clocks")


# ---------------------------------------------------------------------------
# Figure 4 -- day x hour heatmap
# ---------------------------------------------------------------------------
def fig4_heatmap(wh: pd.DataFrame, outdir: Path):
    pivot = (
        wh.pivot(index="day_name", columns="crash_hour", values="rate_pct")
        .reindex(DAY_NAME_ORDER)
    )
    counts = wh.pivot(index="day_name", columns="crash_hour", values="n").reindex(DAY_NAME_ORDER)

    cmap = LinearSegmentedColormap.from_list(
        "injury", ["#f7f4ec", "#f3d9a4", "#e0a355", "#c56b34", "#96331f"]
    )

    fig, ax = plt.subplots(figsize=(15, 6.6))
    fig.subplots_adjust(top=0.80, bottom=0.21, left=0.075, right=0.955)

    vmin, vmax = np.floor(pivot.values.min()), np.ceil(pivot.values.max())
    im = ax.imshow(pivot.values, cmap=cmap, aspect="auto", vmin=vmin, vmax=vmax)

    ax.set_xticks(range(24))
    ax.set_xticklabels([str(hh) for hh in range(24)], fontsize=9.5)
    ax.set_yticks(range(7))
    ax.set_yticklabels(DAY_NAME_ORDER, fontsize=11.5, color=INK)
    ax.set_xlabel("Hour of day (24-hour clock)")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Value labels; white text on the dark end for contrast.
    threshold = vmin + (vmax - vmin) * 0.62
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            ax.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=8.6,
                    color="white" if val > threshold else "#4a3c2f")

    cbar = fig.colorbar(im, ax=ax, pad=0.008, fraction=0.022)
    cbar.set_label("Crashes involving an injury (%)", fontsize=10)
    cbar.outline.set_visible(False)
    cbar.ax.tick_params(length=0, labelsize=9)

    add_titles(
        fig,
        "The Evening Pattern Holds Every Day of the Week",
        "Share of reported crashes that injured at least one person (%), by day and hour",
        x=0.075, title_y=0.975, sub_y=0.905,
    )
    add_caption(
        fig,
        f"All 168 day-by-hour cells are shown: the smallest holds {int(counts.values.min()):,} reported "
        f"crashes, so none needed suppression.\n" + CONDITIONAL_NOTE,
        x=0.075, y=0.105,
    )
    save(fig, outdir, "fig4_weekday_hour_heatmap")


# ---------------------------------------------------------------------------
# Figure 5 -- who gets hurt
# ---------------------------------------------------------------------------
def fig5_road_users(ru: pd.DataFrame, outdir: Path):
    fig, ax = plt.subplots(figsize=(10, 6.2))
    fig.subplots_adjust(top=0.80, bottom=0.22, left=0.10, right=0.97)

    series = {}
    for user in ["Motorist", "Pedestrian", "Cyclist"]:
        sub = ru[ru["road_user"] == user].sort_values("crash_hour")
        series[user] = sub.set_index("crash_hour")["rate_pct"]
        ax.plot(sub["crash_hour"], sub["rate_pct"], lw=2.8,
                color=ROAD_USER_COLOURS[user], zorder=3)

    # Direct labels instead of a legend, placed where the three lines are
    # furthest apart rather than at the right edge where two of them converge.
    for user, at_hour, dy, va in [
        ("Motorist", 2, 1.4, "bottom"),
        ("Pedestrian", 18, 1.4, "bottom"),
        ("Cyclist", 18, -1.4, "top"),
    ]:
        ax.text(at_hour, series[user].loc[at_hour] + dy, user,
                ha="center", va=va, fontsize=12, fontweight="bold",
                color=ROAD_USER_COLOURS[user], zorder=6)

    ped = series["Pedestrian"]

    ax.set_ylabel("Share of reported crashes (%)")
    style_hour_axis(ax)
    ax.set_xlim(-0.7, 23.9)
    ax.set_ylim(0, 34)
    tidy(ax)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")

    # No leader line: the series is already directly labelled, so an arrow would
    # only add a diagonal cutting across the other two lines.
    ax.text(
        7.2, 17.4,
        f"Pedestrian casualties climb from {ped.min():.0f}% of crashes\n"
        f"before dawn to {ped.max():.0f}% in the early evening",
        fontsize=10.5, color=INK, va="center", ha="left",
    )

    add_titles(
        fig,
        "Evening Crashes More Often Hurt Someone Outside a Car",
        "Share of reported crashes in which each road user was injured or killed, by time of day",
    )
    add_caption(
        fig,
        "These lines show WHO WAS HURT, not who was on the road: the dataset records casualties, not the presence\n"
        "of a road user. They cannot be read as one group being more at risk than another.",
        y=0.115,
    )
    save(fig, outdir, "fig5_road_user_by_hour")


# ---------------------------------------------------------------------------
def run(tables_dir: Path, outdir: Path):
    def load(name):
        path = tables_dir / f"{name}.csv"
        if not path.exists():
            raise SystemExit(f"[fail] {path} not found. Run:  python src/analysis.py")
        return pd.read_csv(path)

    h = load("crashes_by_hour").sort_values("crash_hour").reset_index(drop=True)
    wh = load("injury_rate_weekday_hour")
    ru = load("road_user_casualty_by_hour")

    outdir.mkdir(parents=True, exist_ok=True)
    fig1_crash_counts(h, outdir)
    fig2_injury_rate(h, outdir)
    fig3_three_clocks(h, outdir)
    fig4_heatmap(wh, outdir)
    fig5_road_users(ru, outdir)
    print(f"\n[done] 5 figures written to {outdir}/ (PNG + SVG)")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Render the final figures.")
    p.add_argument("--tables", type=Path, default=Path("outputs/summary_tables"))
    p.add_argument("--outdir", type=Path, default=Path("figures"))
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    run(args.tables, args.outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
