# Presentation Outline — *Three Different Clocks*

**Total: 8 minutes, hard stop. 8 slides.**
**Audience:** classmates and instructor. Assume general data literacy, no traffic-safety background.
**Rule:** no code on any slide. One idea per slide. Every number below is verifiable in `outputs/analysis_summary.md`.

---

## Slide 1 — What's the most dangerous hour to be on the road?
**0:00 – 0:45 (45s)**

| | |
|---|---|
| **Main message** | "Dangerous" is not one question, and the audience is about to discover they hold two contradictory beliefs at once. |
| **Visual** | Title slide. Large text only: *"When is New York City's most dangerous hour?"* with two answers side by side: **5 PM — rush hour** / **3 AM — empty streets**. No chart. |

**Say:** "Quick show of hands. Most dangerous hour to be on New York's streets — rush hour, or three in the morning?" *(pause, let hands go up both times)* "You're split. Good — because you're all right. Those are answers to two different questions, and for the next eight minutes I want to convince you that the gap between them is the most interesting thing in this dataset."

> **Delivery note:** the show of hands is the hook. Don't skip it and don't let it run past 15 seconds.

---

## Slide 2 — 488,000 crashes, five years, one question
**0:45 – 1:30 (45s)**

| | |
|---|---|
| **Main message** | Establish the data and — critically — the metric, before any result appears. |
| **Visual** | Four large stat tiles: **487,914** reported crashes · **2021–2025** · **40%** injured someone · **1,304** fatal. Below: the metric definition in one line. |

**Say:** "NYPD publishes every reported collision. Five complete years, 2021 through 2025 — 488,000 crashes. I deliberately left out 2026 because it's a partial year and would skew every comparison. My severity measure is simple and I want it on the record before I show you anything: **the share of reported crashes that injured at least one person.** Not how many people were hurt — just whether anyone was. That keeps it an honest proportion."

---

## Slide 3 — When do crashes happen?
**1:30 – 2:30 (60s)**

| | |
|---|---|
| **Main message** | Frequency peaks at evening rush hour. Sets up the expectation the next slide breaks. |
| **Visual** | `figures/fig1_crashes_by_hour.png` |

**Say:** "Here's when crashes happen. No surprises — it climbs all day and peaks between 5 and 6 PM, just over 30,000 crashes in that hour across five years. The quietest hour, 3 to 4 AM, has fewer than 9,000. So far this is exactly the chart you'd predict. Now here's the question I actually care about: **is that also when crashes hurt people?**"

> **Delivery note:** end on the question, out loud. It is the pivot into the whole talk.

---

## Slide 4 — No. It's the opposite of what I expected.
**2:30 – 4:00 (90s) — THE CORE SLIDE**

| | |
|---|---|
| **Main message** | The overnight hours have the *lowest* injury rate, not the highest — and the fatality rate then inverts that completely. Three peaks, three times. |
| **Visual** | `figures/fig3_three_clocks.png` |

**Say:** "I expected late nights to be when crashes turn serious. They're not — they're the *least* likely to injure anyone. 33% at 2 AM, versus 45% at 9 PM. My hypothesis was backwards.

But look at the third panel. Swap 'injured' for 'killed' and the day flips over. Overnight crashes are the *most* likely to be fatal — about 7 per thousand at 3 AM versus 1 per thousand at 4 PM. That's 6.6 times higher, and the confidence intervals don't overlap.

So there are three peaks at three different times. Most crashes: 5 PM. Most likely to injure: 9 PM. Most likely to kill: 3 AM. The small hours produce very few crashes, and most hurt nobody — but the ones that go wrong go badly wrong."

> **Delivery note:** this is 90 seconds and it is the whole talk. Rehearse it. Walk the three panels top to bottom with your hand. Do not rush the flip.

---

## Slide 5 — It's the evening, every single day
**4:00 – 5:15 (75s)**

| | |
|---|---|
| **Main message** | The evening pattern is time-of-day, not a weekend or one-day artefact — and it is robust, not a small-sample effect. |
| **Visual** | `figures/fig4_weekday_hour_heatmap.png` |

**Say:** "Is this a weekend thing? No. Every row is a day, every column an hour, colour is the injury rate. The pattern is horizontal, not vertical — pale on the left, dark on the right, on all seven days. Day of week barely matters: 2.9 points between the best and worst day, against a 12-point swing across hours.

And this isn't thin data. All 168 cells here have at least 683 crashes in them, so I didn't have to suppress a single one. If I had to name one worst window on both measures at once, it's late evening — 8 PM to midnight — high injury share *and* the second-highest fatality rate."

---

## Slide 6 — Who's in the evening picture
**5:15 – 6:15 (60s)**

| | |
|---|---|
| **Main message** | The mix of who gets hurt shifts across the day — and that explains part, but only part, of the evening peak. |
| **Visual** | `figures/fig5_road_user_by_hour.png` |

**Say:** "Part of what changes is *who* gets hurt. Before dawn, under 4% of crashes injure someone on foot. By early evening it's over 12%. Cyclists follow the same curve.

Important caveat, and I want to be precise: this is who was *hurt*, not who was *there*. The data has no field for 'a pedestrian was present,' so I can't compare risk between these groups and I'm not going to.

And this only explains part of it. If I set aside every crash that hurt a pedestrian or cyclist, about three-quarters of the evening rise is still there. So it's both — a different mix of people, *and* something different about evening crashes themselves."

---

## Slide 7 — What this cannot tell you
**6:15 – 7:10 (55s)**

| | |
|---|---|
| **Main message** | Name the limits plainly, and show that one of them produced a genuine finding. |
| **Visual** | Three bullets, large type. Optional small inset: the `00:00` table — **8,527 records stamped midnight, 1 fatal crash**. |

**Say:** "Three things I can't claim.

**One — there's no exposure denominator.** This counts crashes, not trips. I cannot tell you driving at 2 AM is more dangerous than at 2 PM. Everything here is *conditional on a crash being reported*.

**Two — 'contributing factor' is not cause.** The most common entry in that field is literally 'Unspecified.' It's an officer's classification at the scene, not an investigation.

**Three — missing data isn't random.** Borough is missing on 30% of crashes — that's the biggest category in the field, bigger than Brooklyn. So there's no map in this talk.

One bonus: 8,527 crashes are stamped exactly midnight. Among them, *one* fatal crash — while neighbouring night hours run 50 to 70. That's impossible for a real hour. It's a placeholder for 'time unknown.' I flagged them rather than deleting them, and excluded them from the fatality chart."

> **Delivery note:** the midnight finding lands well — it shows the data was interrogated, not just plotted. But it's the first thing to cut if you're running long.

---

## Slide 8 — Ask which question you're answering
**7:10 – 8:00 (50s)**

| | |
|---|---|
| **Main message** | The three-clock result restated, then the transferable lesson. |
| **Visual** | Three lines, large type: **Most crashes → 5 PM** / **Most likely to injure → 9 PM** / **Most likely to kill → 3 AM** |

**Say:** "Three numbers to leave you with. Most crashes: 5 PM. Most likely to injure someone: 9 PM. Most likely to kill someone: 3 AM.

None of those contradicts the others. They're three answers to three questions we collapse into one word — *dangerous* — and then argue about.

I came in expecting one clean contrast between frequency and severity. What I found is that 'severity' isn't one thing either. Before you compare how often things happen, check that you're measuring the thing you actually care about. Sometimes the best finding in a dataset isn't a surprising number — it's realising the question had more than one answer. Thank you."

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
| "Could the fatality spike be a few unlucky nights?" | 1,304 fatal crashes total, 62 in the 3 AM hour. Wilson 95% intervals for the 3 AM peak and the 4 PM trough don't overlap. I'd defend the broad overnight-vs-afternoon contrast, not a specific hour ranking. |
| "Why not compare boroughs?" | Borough is missing on 30% of records and almost certainly not at random — highway crashes disproportionately lack one. Any ranking would be an artefact of the missingness. |
| "Why did the injury rate rise from 35% in 2021 to 44% in 2025?" | Real in the reported data, but reported crash volume fell 23% over the same period. That pattern is consistent with a change in what gets reported, so I show it for context and don't interpret it as a safety trend. |
