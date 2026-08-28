---
name: Chart series names live only in the hover tooltip
description: A recharts chart without a Legend exposes its series names nowhere in the static DOM — hover is the only way to assert "the chart has series X and Y"
type: feedback
aliases: [recharts series name, chart legend missing, dual-series assertion, ChartTooltip testId]
tags: [area/analytics, type/handle-discovery]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

A case that says *"a dual-series area chart is shown with **Total Requests** and **Errors**
series"* looks like a text assertion. It is not: recharts only renders a series NAME if the chart
declares a `<Legend />`. Elitea's Analytics Health chart
(`AnalyticsHealth.jsx`) declares none — the `name="Total Requests"` / `name="Errors"` props on
its two `<Area>` elements reach the DOM **only** through the hover tooltip.

Without hovering, the strongest available assertion degrades to "there are two coloured SVG paths",
which still passes if the series are swapped, renamed, or bound to the wrong `dataKey`.

## What to do

1. Give the chart's wrapper `<Box>` a real testid, and hover it with a real `Locator.hover()`
   (never a `page.evaluate`-dispatched synthetic `mouseover` — that is exploration-only).
2. Assert on the tooltip. `components/ChartTooltip.jsx` in this repo already accepts a `testId`
   prop (added for ELITEA-2313), threaded through the render-prop form recharts requires:
   `content={<ChartTooltip testId="analytics-health-chart-tooltip" />}`.
3. Live-verified 2026-08-28: tooltip text `2026-08-13 | Total Requests: 129 | Errors: 0`.

## Generalisation

Before promising a case's "chart shows series X" assertion, grep the component for `<Legend`.
No legend ⇒ the name is a hover-only observable, and the AFS must say so — otherwise the
implementer discovers it at Phase 3 and improvises a weaker assertion.

Related: [[analytics_guide_tab_has_no_network]]
