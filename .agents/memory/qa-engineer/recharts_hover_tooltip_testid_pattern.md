---
name: Recharts hover tooltip — testid pattern
description: Custom Recharts tooltip content components need a render-prop-threaded testId; hover must use real mouse events, not page.evaluate
type: feedback
---

## Context

Elitea's Analytics charts (`AnalyticsOverview`, `AnalyticsUserDetailed`, etc.) use
Recharts `AreaChart`/`BarChart` with a shared custom tooltip component
(`src/[fsd]/features/settings/ui/analytics/components/ChartTooltip.jsx`) passed as
`<RechartsTooltip content={<ChartTooltip />} />`.

## The gotcha

Recharts injects `active`/`payload`/`label` props into the `content` element at
render time. You cannot just add `testId="..."` as a static prop on
`<ChartTooltip />` — Recharts controls the element instantiation. To thread a
caller-supplied testid through, use the render-function form instead:

```jsx
<RechartsTooltip content={props => <ChartTooltip {...props} testId="my-chart-tooltip" />} />
```

Then add an optional `testId` prop to `ChartTooltip.jsx` itself, wired as
`data-testid={testId}` on its outer `Box` — same "shared component, caller-supplied
prop" pattern as `SearchInput.jsx`'s `testId` and `KpiCard.jsx`'s `testId`/
`valueTestId` (see `test-specs/settings-analytics/_surface.md`).

## Hover mechanics

Recharts' hover-tracking listens on the whole plot `<svg>` (class
`.recharts-wrapper svg`), not on a per-datapoint element — so a presence+content
check only needs ONE testid on the chart's wrapping `Box` (for `.bounding_box()`)
plus the tooltip's own testid; no per-datapoint testid is needed. Confirmed live:
`document.querySelector('.recharts-tooltip-wrapper')` appears with
`visibility: visible` after hovering anywhere inside the chart's plotted area.

**Exploration vs. automation — different tool.** During live exploration it's fine
to confirm the mechanism with a synthetic `dispatchEvent(new MouseEvent(...))` via
`browser_evaluate` (fast, no coordinate math). The SHIPPED automated test must use a
real Playwright `page.mouse.move(x, y)` / `.hover()` at coordinates computed from the
chart container's `.bounding_box()` — synthetic dispatch is exploration-only per the
pristine-repro-gate rule (`.agents/role-overrides.md`), and a real automated test
should exercise the actual user gesture, not a JS-injected event.

## Where this came from

ELITEA-2313 analysis (batch `elitea-2313`, 2026-08-05) — `AnalyticsUserDetailed`'s
"Daily Activity" chart hover-tooltip step. Also relevant to sibling case ELITEA-2329
(dedicated hover-depth case) and ELITEA-2326/2327/2328 (other Analytics chart hovers).
