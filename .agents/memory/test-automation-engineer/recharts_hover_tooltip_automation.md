---
name: Recharts hover tooltip automation (Elitea Analytics)
description: Bar-chart tooltips only close if the pointer TRAVELS; capture bar boxes before hovering; scroll the chart into view first
type: feedback
aliases: [recharts tooltip, chart hover, mouse.move steps, bar bounding box None, ChartTooltip]
tags: [area/settings-analytics, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

## Three things that cost a red run each (ELITEA-2326/2327/2328/2329)

1. **Mouse-out only unmounts a BAR chart's Recharts tooltip if the pointer travels.**
   A single-jump `page.mouse.move(x, y)` off the chart left the tooltip stuck `active`
   on BOTH bar charts (screenshots proved the cursor had landed elsewhere), while the
   same jump off an area chart deactivated it fine. Fix: `steps=20` to a far target
   (the page header). This is a *more* faithful gesture than the jump — a real mouse
   emits a stream of intermediate `mousemove`s — so it is not a workaround.

2. **Read every bar's `bounding_box()` in ONE pass BEFORE the first hover.**
   Hovering changes Recharts' active index, re-renders the `<Bar>` series and re-runs
   its grow animation, so a post-hover box read can return `None`. A zero-valued row
   also has a zero-height path and therefore no usable box — pick hoverable indices
   from the captured list, and keep assertions keyed on that index against `rows[i]`.

3. **`scroll_into_view_if_needed()` before measuring a chart for a hover.**
   A merged spec silently broke when the product added KPI cards above the chart and
   pushed its vertical centre below the viewport: the raw `mouse.move` landed nowhere
   and the tooltip never appeared. Nothing in the error said "off-screen".

All three now live in `automation/pages/analytics_page.py`
(`move_mouse_off_chart`, `get_chart_bar_boxes` + `hover_chart_bar_box`,
`hover_chart_at_fraction`, `read_chart_tooltip_lines`, `wait_for_chart_tooltip_change`).

Related: [[project_briefing]]
