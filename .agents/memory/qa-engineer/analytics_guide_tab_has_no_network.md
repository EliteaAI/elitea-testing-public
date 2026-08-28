---
name: Analytics Guide tab issues no request at all
description: The Elitea Analytics Guide tab is a pure render of a bundled constant — an expect_response or networkidle wait there hangs on a request that never fires
type: feedback
aliases: [guide tab wait, static tab no request, GUIDE_SECTIONS]
tags: [area/analytics, type/timing]
created: 2026-08-28
updated: 2026-08-28
---

Every other Analytics tab has its own GET (`analytics/`, `analytics_users/`, `analytics_agents/`,
`analytics_tools/`). The **Guide** tab has none: `AnalyticsGuide.jsx` renders
`AnalyticsCommonConstants.GUIDE_SECTIONS` (9 sections, 43 metrics) and is project- and
date-range-independent.

Consequences for a spec on that tab:
- No `expect_response` wait — there is nothing to wait for.
- No `networkidle` either (wrong on this app anyway: a persistent Socket.IO polling transport keeps
  it racy — `.agents/testing.md` § Known issues, #1847).
- Wait on the first `analytics-guide-section` becoming visible.

Also worth knowing: `Calculation:` renders on 14 of 43 metrics and `Data source:` on 7 — both are
`{m.x && ...}` conditionals — so "each metric shows both" is never a safe assertion
(case-text drift filed as elitea-testing-public#1950).

Related: [[chart_series_names_live_only_in_the_hover_tooltip]]
