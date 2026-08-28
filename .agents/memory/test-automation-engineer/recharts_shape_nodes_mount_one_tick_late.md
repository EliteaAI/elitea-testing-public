---
name: Recharts shape nodes mount one animation tick after the container
description: A chart container being visible does NOT mean its bars/areas exist — wait on the first shape node, never a sleep
type: feedback
aliases: [recharts, chart bars, area series, recharts-bar-rectangle, recharts-area-area, chart flake]
tags: [area/ui-charts, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

## The fact

Measured 2026-08-28 (ELITEA-2322/2324, Analytics Tools + Health tabs): after the chart's wrapping
`<Box>` (the app-testid parent) becomes visible, Recharts still has NOT rendered its shape nodes —
`.recharts-bar-rectangle path` counted **0**, and the `.recharts-bar-rectangle` `<g>` groups existed
with EMPTY `innerHTML`. Two seconds later the paths were there. Same for `<Area>` series.

So a container-visible wait is a false settle signal and produces a spurious "expected 20 bars,
got 0".

## The fix (no sleep)

Wait on the first shape node itself:

```python
bars = self.tools_chart_container.locator(RECHARTS_BAR_FILL)   # ".recharts-bar-rectangle path"
bars.first.wait_for(state="attached", timeout=UI_ELEMENT_TIMEOUT)
```

## Node names worth remembering

| What | Selector |
|---|---|
| Bar shapes | `.recharts-bar-rectangle path` (the `<path class="recharts-rectangle">` inside each group) |
| Area series | `.recharts-area-area` (`<path class="recharts-curve recharts-area-area">`, one per `<Area>`) |
| X-axis tick labels | `.recharts-xAxis .recharts-cartesian-axis-tick-value` |

All three are library-internal — #579 exception 1 — so ALWAYS scope them inside the chart's own
app-testid container and declare the exception in the page-object method docstring.

Related: [[mui_tablepagination_rows_per_page_menu_testid]]
