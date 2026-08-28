---
name: A chart's presence assertion cannot prove the chart updated
description: count()==1 is invariant under a stale render — assert the rendered axis against the new response's series.
type: feedback
aliases: [chart presence, stale chart, chart updated, presence-iff-data]
tags: [area/charts, type/assertion-strength]
created: 2026-08-28
updated: 2026-08-28
---

## The finding

ELITEA-2318's case says "note the Chat Messages chart data" (step 2) and "verify both charts
update their data" (step 4). The first implementation satisfied both with
`chart_container.count() == (1 if response_has_data else 0)`.

**A chart frozen on the PREVIOUS range's series is still exactly one container**, so the step-4
assertion passed unchanged whether or not anything re-rendered. Presence-iff-data is a good
guard for a *conditionally rendered* component; it is not an assertion that the component's
DATA changed. Review round 1 blocked it.

## The shape that works

Read the chart's own rendered axis and compare it to the response that was just captured:

- ticks ⊆ the response's series dates,
- last tick == the series' last date,
- rendered span ≥ the series' span − a thinning slack.

Deterministic (the response is the oracle), no fabricated expectation, and the stale case now
fails on the span comparison. The tick labels come from recharts' internal SVG — a #579-scoped
handle chained off the chart container's real testid, declared in the page-object docstring.

Related: [[recharts_axis_ticks_are_year_less]]
