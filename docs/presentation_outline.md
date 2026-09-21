# Presentation Outline — *Three Different Clocks*

**Total: 8 minutes, hard stop. 8 slides.**
**Audience:** classmates and instructor. Assume general data literacy, no traffic-safety background.
**Rule:** no code on any slide. One idea per slide. Every number below is verifiable in `outputs/analysis_summary.md`.

---

## Slide 1 — What does “most dangerous” mean in crash data?
**0:00 – 0:45 (45s)**

| | |
|---|---|
| **Main message** | "Dangerous" is not one measure, and the audience is about to discover that two competing intuitions can both reflect the data. |
| **Visual** | Title slide. Large text only: *"When does New York City's crash data look most dangerous?"* with two answers side by side: **5 PM — rush hour** / **3 AM — empty streets**. No chart. |

**Say:** "Quick show of hands. Which hour would look most dangerous in New York City's crash records — rush hour, or three in the morning?" *(pause, let hands go up both times)* "That split is exactly the problem. One answer describes when crashes happen most; the other describes when reported crashes are most often fatal. The gap between those questions is the story in this dataset."

> **Delivery note:** the show of hands is the hook. Don't skip it and don't let it run past 15 seconds.

---

## Slide 2 — 488,000 crashes, five years, one question
**0:45 – 1:30 (45s)**

| | |
|---|---|
| **Main message** | Establish the data and — critically — the metric, before any result appears. |
| **Visual** | Four large stat tiles: **487,914** reported crashes · **2021–2025** · **40%** injured someone · **1,304** fatal. Below: the metric definition in one line. |

**Say:** "NYPD publishes every reported collision. We use five complete years, 2021 through 2025 — 488,000 crashes. We left out 2026 because it is a partial year and would skew every comparison. Our severity measure is the **share of reported crashes that injured at least one person.** Not how many people were hurt — just whether anyone was. These are rates among reported crashes, not the risk of taking a trip at that hour."

---

## Slide 3 — When do crashes happen?
**1:30 – 2:30 (60s)**

| | |
|---|---|
| **Main message** | Frequency peaks at evening rush hour. Sets up the expectation the next slide breaks. |
| **Visual** | `figures/fig1_crashes_by_hour.png` |

**Say:** "Here's when crashes happen. No surprises — it climbs all day and peaks between 5 and 6 PM, just over 30,000 crashes in that hour across five years. The quietest hour, 3 to 4 AM, has fewer than 9,000. So far this is exactly the chart you'd predict. Now here's the question we actually care about: **is that also when crashes hurt people?**"

> **Delivery note:** end on the question, out loud. It is the pivot into the whole talk.

---

## Slide 4 — No. The data split into three clocks.
**2:30 – 4:00 (90s) — THE CORE SLIDE**

| | |
|---|---|
| **Main message** | The overnight hours have the *lowest* injury rate, not the highest — and the fatality rate then inverts that completely. Three peaks, three times. |
| **Visual** | `figures/fig3_three_clocks.png` |

**Say:** "We expected late nights to be when crashes most often injure someone. Among reported crashes, the opposite appears: the injury share is 33% at 2 AM, versus 45% at 9 PM.

But look at the third panel. Swap 'injured' for 'killed' and the day flips over. The fatality rate among reported crashes is about 7 per thousand at 3 AM versus 1 per thousand at 4 PM — a 6.6-fold descriptive difference. Fatal crashes are rare, so the broad overnight-versus-afternoon contrast matters more than the exact ranking of one hour.

So there are three peaks at three different times. Most crashes: 5 PM. Highest injury share: 9 PM. Highest fatality rate: 3 AM. One word — 'dangerous' — was hiding three different measures."

> **Delivery note:** this is 90 seconds and it is the whole talk. Rehearse it. Walk the three panels top to bottom with your hand. Do not rush the flip.

---

## Slide 5 — It's the evening, every single day
**4:00 – 5:15 (75s)**

| | |
|---|---|
| **Main message** | The evening pattern is time-of-day, not a weekend or one-day artefact — and it is robust, not a small-sample effect. |
| **Visual** | `figures/fig4_weekday_hour_heatmap.png` |

**Say:** "Is this a weekend thing? No. Every row is a day, every column an hour, and colour is the injury share among reported crashes. The pattern is horizontal, not vertical — pale on the left, dark on the right, on all seven days. Day of week changes by 2.9 points from lowest to highest, compared with a 12-point swing across hours.

And this isn't thin data. All 168 cells here have at least 683 crashes in them, so none needed suppression. Late evening — 8 PM to midnight — is the clearest single window where injury share and fatality rate are both elevated."

---

## Slide 6 — Who's in the evening picture
**5:15 – 6:15 (60s)**

| | |
|---|---|
| **Main message** | The mix of who gets hurt shifts across the day — and that explains part, but only part, of the evening peak. |
| **Visual** | `figures/fig5_road_user_by_hour.png` |

**Say:** "Part of what changes is *who* gets hurt. Before dawn, under 4% of reported crashes injure someone on foot. By early evening it is over 12%. Cyclists follow the same curve.

Important caveat: this is who was *hurt*, not who was *there*. The data has no field for 'a pedestrian was present,' so we cannot compare risk between these groups.

And this only explains part of it. If we set aside every crash that hurt a pedestrian or cyclist, about three-quarters of the evening rise remains. The changing casualty mix does not explain the full pattern, but this dataset cannot tell us what causes the remainder."

---

## Slide 7 — What the data can — and cannot — say
**6:15 – 7:10 (55s)**

| | |
|---|---|
| **Main message** | Name the limits plainly, and show that one of them produced a genuine finding. |
| **Visual** | Three bullets, large type. Optional small inset: the `00:00` table — **8,527 records stamped midnight, 1 fatal crash**. |

**Say:** "Three limits. First, this counts crashes, not trips, so we cannot compare the risk of taking a trip at 2 AM and 2 PM. Second, a recorded 'contributing factor' is an officer's classification, not an established cause. Third, borough is missing on 30% of records, so there is no map in this talk.

One data-quality clue: 8,527 crashes are stamped exactly midnight, but only one is fatal. Comparable-sized hourly bins from 1 to 6 AM contain 53 to 62 fatal crashes each. That strongly suggests many exact-midnight timestamps mean 'time unknown.' We kept and flagged them, excluding them only from the fatality-by-hour chart they would distort."

> **Delivery note:** the midnight finding lands well — it shows the data was interrogated, not just plotted. But it's the first thing to cut if you're running long.

---

## Slide 8 — Ask which question you're answering
**7:10 – 8:00 (50s)**

| | |
|---|---|
| **Main message** | The three-clock result restated, then the transferable lesson. |
| **Visual** | Three lines, large type: **Most crashes → 5 PM** / **Highest injury share → 9 PM** / **Highest fatality rate → 3 AM** |

**Say:** "Three numbers to leave you with. Most reported crashes: 5 PM. Highest injury share among reported crashes: 9 PM. Highest fatality rate among reported crashes: 3 AM.

None of those contradicts the others. They're three answers to three questions we collapse into one word — *dangerous* — and then argue about.

We expected one clean contrast between frequency and severity. Instead, 'severity' was not one thing either. Before comparing how often things happen, ask what outcome and denominator the data actually measure. Sometimes the best finding is realising that the question had more than one answer. Thank you."

---

## Timing summary

| Slide | Segment | Start | Length |
|---|---|---|---|
| 1 | Hook + audience | 0:00 | 45s |
| 2 | Dataset + metric | 0:45 | 45s |
| 3 | First pattern | 1:30 | 60s |
| 4 | **Core finding** | 2:30 | **90s** |
| 5 | Deeper temporal | 4:00 | 75s |
| 6 | Road users | 5:15 | 60s |
| 7 | Limitations / ethics | 6:15 | 55s |
| 8 | Takeaway | 7:10 | 50s |

## If you are running long

Cut in this order:
1. The midnight-placeholder story on slide 7 (~15s) — interesting, not load-bearing.
2. The "all 168 cells" robustness line on slide 5 (~10s).
3. The composition caveat on slide 6 (~15s) — but **keep** the "who was hurt, not who was there" sentence. That one is not optional; dropping it makes a claim the data cannot support.

## Anticipated questions

| Question | Answer |
|---|---|
| "Isn't the overnight injury rate low just because minor crashes go unreported at night?" | Under-reporting of minor overnight crashes would *shrink* the denominator and push the overnight rate **up**. We observe the lowest rate of the day despite that. It cuts against the finding, not for it. |
| "Could the fatality spike be a few unlucky nights?" | There are 1,304 fatal crashes total and 62 in the 3 AM hour. The per-hour Wilson intervals do not overlap, but the peak and trough were selected from 24 hours. We therefore emphasize the broad overnight-versus-afternoon contrast, not a specific hour ranking. |
| "Why not compare boroughs?" | Borough is missing on 30% of records and almost certainly not at random — highway crashes disproportionately lack one. Any ranking would be an artefact of the missingness. |
| "Why did the injury rate rise from 35% in 2021 to 44% in 2025?" | Real in the reported data, but reported crash volume fell 23% over the same period. That pattern is consistent with a change in what gets reported, so we show it for context and do not interpret it as a safety trend. |
