---
name: Recharts ChartTooltip automation on Elitea Analytics
description: How to hover-test any Elitea Analytics chart honestly — testId prop, unmount-on-mouseout, bar-box vs container-fraction, non-unique categories
type: feedback
aliases: [chart tooltip, recharts hover, ChartTooltip testId, analytics tooltip, hover tooltip]
tags: [area/settings-analytics, type/technique]
created: 2026-08-28
updated: 2026-08-28
---

## The shared component

Every Elitea Analytics chart tooltip is the same `analytics/components/ChartTooltip.jsx`.

- It **already has a `testId` prop** -> wiring a tooltip testid is **call-site-only**, never a
  shared-component change. Shape: `<RechartsTooltip content={<ChartTooltip testId="x" />} />`.
- It returns `null` when `!active` -> on mouse-out the node **unmounts**. Assert `count() == 0`,
  not `not_to_be_visible()`.
- Markup is always: line 1 = label (date for area charts, category name for bar charts),
  lines 2..N = `"{series name}: {value}"` in declaration order.
- Values render through `fmtNum` (3800 -> `3.8K`).

## Hovering honestly

Real `page.mouse.move()` only — never a `page.evaluate` synthetic dispatch (that makes the test the
producer of the observable).

- **Area charts**: move to a fractional x of the *container* box; Recharts snaps to the nearest
  category, so read whichever date it landed on out of the captured response and assert against
  that entry. 25% / 75% reliably land on different days over 30 days.
- **Bar charts**: move to the *bar's own* bounding box centre (`container.locator(".recharts-bar-rectangle path")`).
  That is what makes bar index i <-> response `rows[i]` exact.
- Hovering fires **no network request**. Don't wait on a response.
- Recharts `<path>` nodes mount **one animation tick after** the container is visible — wait on
  `.first` attached.

## The trap that would have produced a wrong assertion

**Bar-chart x-axis categories are not unique** — the Agents chart's live top-20 had
`guardrails_test_agent` ×3 and `elitea-1735-skills-agent` ×6 (distinct entities, same name). So
"hover a different bar -> a different name appears" is FALSE. Key on index against `rows[i]` and
compare the full tooltip text for the update check.

Related: [[analytics_chart_conditional_rendering]]
