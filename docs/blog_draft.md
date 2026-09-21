# Three Different Clocks

### One deceptively simple question about New York City's reported crashes produces three different answers

---

When does New York City's crash data look most dangerous — rush hour, or three in the morning?

Most people have one of two instincts. Either rush hour — all that traffic, all those near-misses — or the small hours of the morning, when the roads are empty and the crashes that do happen can feel especially severe.

Both instincts capture something real, but neither answers the whole question. The gap between them turns out to be the most interesting thing in five years of the city's own collision records.

## Why this is worth an afternoon

For New Yorkers, road-safety advocates and local decision-makers, crash counts are often the first signal that a time or place deserves attention. That is sensible, but a count measures how much is happening, which is not the same as how much harm is happening. A hundred minor collisions and five fatal ones are different problems, even though both can be summarized with a single number.

So it is worth asking whether the times that produce the most collisions are also the times that produce the worst ones.

## The data

New York City publishes a record of every motor-vehicle collision reported to the police: when and roughly where it happened, and how many people were hurt or killed — separated into people in vehicles, people on bikes, and people on foot.

We used five complete years, 2021 through 2025: **487,914 reported collisions**. Around 40% injured at least one person; about 1,300 involved someone being killed.

One idea to hold onto, because everything below depends on it: our measure of seriousness is the **share of reported crashes that injured at least one person**. Not how many people were hurt — just whether anyone was. These are rates *among reported crashes*, not the risk of taking a trip at a particular hour.

## What we expected to find

We expected a clean story: crashes pile up at rush hour, but the ones that really hurt people happen late at night. Frequency in the afternoon, severity at 3 AM.

The first half checked out immediately. Reported collisions climb through the day and peak between **5 and 6 PM**, with just over 30,000 in that hour across five years. The quietest hour, 3 to 4 AM, has fewer than 9,000.

![When do NYC crashes happen?](../figures/fig1_crashes_by_hour.png)

## The turn

Then we calculated how often a reported crash hurts someone, hour by hour — and the second half of that expectation fell apart.

The overnight hours are not when crashes are most likely to injure someone. They are when crashes are **least** likely to injure someone. At 2 to 3 AM, about **33%** of reported collisions involve an injury. That is the lowest figure of the entire day.

The highest is in the evening — around **45%** between 9 and 10 PM. Nearly half of the collisions reported in that hour hurt somebody.

![When is a crash most likely to hurt someone?](../figures/fig2_injury_rate_by_hour.png)

Notice also that the injury peak does not sit on top of the crash peak. The busiest hour is 5 PM; the hour when reported crashes most often injure someone is around 9 PM. They are about four hours apart. Frequency and harm really are two different clocks — just not in the direction we had assumed.

## Unless you change what "serious" means

At this point the folk wisdom about late nights looked simply wrong. But it depends entirely on how you define seriousness.

Swap "did anyone get injured?" for "did anyone die?" and the day flips over.

Among reported crashes, the fatality rate is highest overnight. Between 3 and 4 AM, about **7 in every 1,000 reported crashes** involve a death. At 4 to 5 PM — near the busiest part of the day — it is **about 1 in 1,000.** That is a 6.6-fold descriptive difference. Fatal crashes are rare and the highest and lowest hours were selected from 24 possibilities, so the broad overnight-versus-afternoon contrast matters more than declaring one exact hour uniquely dangerous.

![Three different clocks](../figures/fig3_three_clocks.png)

So there are three peaks, at three different times:

- **The most crashes: 5–6 PM.**
- **The highest injury share among reported crashes: 9–10 PM.**
- **The highest fatality rate among reported crashes: 3–4 AM.**

The small hours produce fewer reported collisions and a lower injury share, yet a much higher fatality rate. Rush hour produces many more collisions with a comparatively low fatality rate. "Dangerous" was never one question.

## The midnight that may not be midnight

Before trusting the overnight pattern, we checked whether the clock itself behaved sensibly. One timestamp failed that reality check.

Exactly `00:00` appears 8,527 times, but only one of those crashes was fatal. Each hourly bin from 1 to 6 AM contains a similar number of crashes — between 8,678 and 11,741 — yet 53 to 62 fatal crashes.

That does not prove that every midnight record is wrong. It does strongly suggest that many were entered as `00:00` when the precise time was unknown. We did not simply delete them. We flagged them, kept them in the overall dataset, and excluded them only from the fatality-by-hour calculation they would otherwise distort. Before trusting a pattern, the data first had to behave like the thing they claimed to measure.

If you want a single window where both measures are bad at once, it is the late evening, roughly 8 PM to midnight: a high injury share *and* the second-highest fatality rate of the day. And this evening pattern is not a weekend effect. It shows up on all seven days.

![The evening pattern holds every day](../figures/fig4_weekday_hour_heatmap.png)

## Who is in the evening picture

Part of what changes across the day is who gets hurt.

In the pre-dawn hours, fewer than 4% of reported crashes injure someone on foot. By early evening that has risen to over 12%. Crashes that injure someone on a bicycle follow the same curve, from under 2% to over 7%. The evening is when the city's collisions most often involve people who are not surrounded by a car.

![Who gets hurt, and when](../figures/fig5_road_user_by_hour.png)

That is part of the explanation — but only part. If we set aside every crash that hurt someone walking or cycling, the evening rise in injuries shrinks, yet roughly three-quarters of it remains. The changing casualty mix does not explain the full pattern, but the data do not tell us what causes the remainder.

## What this cannot tell you

A caution that matters more than any finding above.

This data counts **crashes**. It does not count trips, or cars, or people walking home. So we cannot tell you that driving at 2 AM is more dangerous than driving at 2 PM, or that walking at 5 PM carries more risk than walking at dawn. Those statements would require knowing how many people were out at each hour, and this dataset does not contain that.

Everything here is conditional: *given that a crash was reported, how often did it hurt someone?* That is a genuinely useful question, and it is the only one these records can answer.

Two more caveats. These are collisions reported to police, and minor ones go unreported at rates we cannot measure. And the "contributing factor" recorded on each report is an officer's classification made at the scene, not an investigated cause — the single most common entry is "Unspecified."

## The takeaway

The most common hour for a reported crash in New York City is 5 PM. Among reported crashes, the injury share peaks at 9 PM and the fatality rate peaks at 3 AM.

None of those numbers contradicts the others. They are answers to three different questions that we tend to collapse into one word — *dangerous* — and then argue about.

The lesson travels well beyond traffic. Before comparing how often things happen, ask what outcome and denominator the data actually measure. Sometimes the most useful finding is not a surprising number. It is discovering that the question had more than one answer all along.

---

*Data: NYC Open Data / NYPD, "Motor Vehicle Collisions – Crashes," 2021–2025. Analysis code, figures and full statistical detail are available in the project repository.*
