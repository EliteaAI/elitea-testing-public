---
name: Recharts interval={0} makes the X axis exactly equal to the charted series
description: Category bar charts with interval={0} render one tick per series — assert list equality, not the subset/slack shape date axes need
type: feedback
aliases: [recharts ticks, bar chart axis assertion, interval 0, Most Popular Tools chart]
tags: [area/charts, type/pattern]
created: 2026-08-28
updated: 2026-08-28
---

Two recharts shapes in the same app need **different** assertion strength, and using the weaker
one on the stronger chart loses real signal:

| Chart | XAxis | Assert |
|---|---|---|
| Date axis (`AreaChart` over `chat_daily`, Daily Activity) | recharts **thins** labels | ticks ⊆ response dates, last tick == last date, span within a slack constant |
| Category axis with **`interval={0}`** (`AnalyticsTools.jsx` "Most Popular Tools", `dataKey="tool_name"`) | **no thinning — one tick per series** | `ticks == [row["tool_name"] for row in rows[:20]]`, exact list, in order |

Check the JSX for `interval={0}` before choosing. When it is there, exact equality is available and
is strictly stronger — no slack constant to tune, and a stale chart is caught by length alone.

Measured live 2026-08-28 (project 399): `Last 24h` charted 1 tool, `Last 30d` charted 20 — wholly
different lists, while `container.count() == 1` was identical under both. That gap is the whole
reason presence checks are not "the chart updated its data".

Related: [[recharts_axis_ticks_are_year_less]] · [[chart_presence_is_not_chart_data]]
