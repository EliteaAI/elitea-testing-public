# Recharts hover tooltips — the shared `ChartTooltip` across every Analytics chart

> Part of the `settings-analytics` exploration digest — index: [`_surface.md`](../_surface.md).
> Handle cache from live exploration, not a source of truth: verify a handle as you use it.

_Confirmed live 2026-08-28 (ELITEA-2326/2327/2328/2329 cluster), localhost:5173, projects
"Elitea Testing Team" and "Private", preset `Last 30d`. Zero console errors across the whole walk._

## One component, one shape, everywhere

Every chart on this surface renders its hover tooltip through the SAME shared
`analytics/components/ChartTooltip.jsx`, passed as `<RechartsTooltip content={<ChartTooltip />} />`.
Its markup is always:

```
line 1          the Recharts `label`   (a date for area charts, the category name for bar charts)
lines 2..N      "{series name}: {value}"   one per payload entry, in <Area>/<Bar> declaration order
```

Two properties that make it pleasant to automate — both live-confirmed:

- **It returns `null` when `!active`**, so on mouse-out the tooltip node **unmounts**: assert
  `count() == 0`, not `not_to_be_visible()`. (Verified on `analytics-user-detail-chart-tooltip`:
  count 1 while hovering -> 0 after moving away.)
- **It takes a `testId` prop** which lands directly on the tooltip `Box`. Wiring a tooltip testid is
  therefore **call-site-only — never a shared-component change**. Wire it ONLY at the call site your
  case touches (`ChartTooltip` is consumed by Overview, Costs, Tokens, Agents ×2, Tools, Health,
  UserDetailed, AgentDetailed, ToolDetailed).

Values go through `AnalyticCommonHelpers.fmtNum` (no `formatter` prop at any of these call sites),
so `3800` renders `3.8K`. Python port: `fmt_num()` in `automation/utils/analytics_format.py`
(extracted there from `tests/ui/admin/test_analytics_overview_kpi_cards.py` during the
ELITEA-2326/2327/2328/2329 implementation, on its third consumer — Hard Rule 7).

## Tooltip testid inventory

| Chart | Call site | Tooltip testid | State 2026-08-28 |
|---|---|---|---|
| Overview `Daily Activity` | `AnalyticsOverview.jsx:174` | `analytics-overview-daily-chart-tooltip` | added EliteaAI/EliteaUI@c926ba66, on `automation/testids` (ELITEA-2326) |
| Agents `Most Active Agents & Pipelines` | `AnalyticsAgents.jsx:153` | `analytics-agents-chart-tooltip` | added EliteaAI/EliteaUI@c926ba66, on `automation/testids` (ELITEA-2327) |
| Agents `Chat Messages` | `AnalyticsAgents.jsx:218` | — | none; out of scope so far |
| Tools `Most Popular Tools` | `AnalyticsTools.jsx:123` | `analytics-tools-chart-tooltip` | added EliteaAI/EliteaUI@c926ba66, on `automation/testids` (ELITEA-2328) |
| Health `Requests vs Errors` | `AnalyticsHealth.jsx` | `analytics-health-chart-tooltip` | on `automation/testids` |
| User detail `Daily Activity` | `AnalyticsUserDetailed.jsx:246` | `analytics-user-detail-chart-tooltip` | **on `main` ✓** |

## Driving the hover honestly

A real `page.mouse.move()` / `Locator.hover()` — **never** a `page.evaluate`-dispatched synthetic
event (that would make the test the producer of the observable). Recharts tracks the pointer on the
plot `<svg>`, so:

- **Area charts** — move to a fractional x of the *container* bounding box. Recharts snaps to the
  nearest category, so no exact datum-pixel maths is needed: read whichever date it landed on out of
  the response and assert against that entry. 25% and 75% of the width reliably landed on different
  days over a 30-day range.
- **Bar charts** — move to the *bar's own* bounding box centre, taken from
  `container.locator(RECHARTS_BAR_FILL)` (`pages/analytics_page.py:192`). This is what makes bar
  index `i` <-> response `rows[i]` exact.
- Hovering fires **no network request** — the tooltip is a pure client-side render over the
  RTK-Query cache. Don't wait on a response after a hover.
- Recharts' `<path>` nodes (`.recharts-bar-rectangle path`, `.recharts-area-area`) mount **one
  animation tick after the container becomes visible** — wait on `.first` attached, never a sleep.
  These are #579 exception-1 scoped raw handles and the page object already owns both constants.

## Per-chart series contracts (live)

| Chart | Legend? | Label = | Series (name -> dataKey) |
|---|---|---|---|
| Overview `Daily Activity` | **yes** | `daily_activity[i].date` | `LLM Calls`->`llm_calls`, `Tool Runs`->`tool_runs`, `Agent & Pipeline Runs`->`agent_runs`, `Active Users`->`active_users` **(only when `!isPersonalProject`)** |
| Agents bar chart | **no** | `rows[i].entity_name \|\| "Agent #"+entity_id` | `Runs` -> `rows[i].events` |
| Tools bar chart | **no** | `rows[i].tool_name` | `Calls` -> `rows[i].calls` |
| Health area chart | **no** | date | `Total Requests`, `Errors` |
| User-detail `Daily Activity` | **no** | `daily_activity[i].date` | `LLM`->`llm`, `Tool`->`tool`, `Chat Msg`->`chat`, `Agent`->`agent` |

Only the Overview chart renders a Legend — on every other chart the **series names exist in the DOM
only inside the tooltip**, which is what makes these tooltip assertions load-bearing rather than
cosmetic.

## Traps worth remembering

- **Bar-chart x-axis categories are NOT unique.** Live top-20 on the Agents chart contained
  `guardrails_test_agent` ×3 and `elitea-1735-skills-agent` ×6 — distinct entities sharing a name.
  Never assert "a different bar shows a different name"; key on the bar **index** against `rows[i]`
  and compare the *full* tooltip text (label + value) for the "it updated" check.
- **Both bar charts are conditionally rendered** (`agentChartData.length > 0` /
  `toolChartData.length > 0`). Live 2026-08-28 project "Elitea Testing Team" over `Last 30d` had
  `0 agents & pipelines` and therefore **no Agents bar chart at all**, while "Private" had 899. Any
  chart spec must assert its precondition off the captured response (`len(rows) >= 2` when the case
  needs a second data point) so an unsuitable fixture project fails loudly instead of timing out on
  a locator.
- **Zero-valued series still render** — a day with all zeros shows `LLM: 0 / Tool: 0 / ...`, the
  lines do not disappear. Don't treat a zero day as "the tooltip is broken".
- After clicking a tab, a row locator's `.count()` can read 0 while `.first` still resolves via
  auto-waiting. Wait on the locator before counting.

## Resolved/added during ELITEA-2326/2327/2328/2329 implementation (2026-08-28, test-automation-engineer)

Facts the analyst pass could not have had, all learned by running the specs live. They live in
`AnalyticsPage` now, so a later case gets them for free.

- **The three tooltip testids above exist** — EliteaAI/EliteaUI@c926ba66, call-site-only wiring of the
  shared `ChartTooltip`'s `testId` prop, pushed to `automation/testids` (human cherry-picks to `main`).
  `AnalyticsAgents.jsx:218` (the Chat Messages tooltip) was deliberately left untouched.
- **Mouse-out only deactivates a BAR chart's tooltip if the pointer TRAVELS.** A single-jump
  `page.mouse.move()` off the chart left both bar-chart tooltips stuck active (screenshots confirmed
  the cursor had landed in the table below / the sibling chart, tooltip still rendered), while the same
  jump off the Overview *area* chart did deactivate it. `AnalyticsPage.move_mouse_off_chart()` now moves
  with `steps=20` to the page header — the stream of intermediate `mousemove`s a real mouse emits, so it
  is a MORE faithful gesture, not a workaround. If a future chart's mouse-out assertion hangs at
  `count() == 1`, this is why.
- **Capture bar bounding boxes in ONE pass BEFORE hovering.** Hovering changes Recharts' active index,
  re-renders the `<Bar>` series and re-runs its grow animation, so a box read *after* a hover can come
  back `None` (a zero-height path is not "visible" to Playwright) — this cost a full red run on the
  Agents chart. `AnalyticsPage.get_chart_bar_boxes()` does the single pass; a zero-valued row also has
  no usable box, so pick the hoverable indices from the captured list and key assertions on that index
  against `rows[i]`.
- **Scroll the chart into view before hovering.** `hover_chart_at_fraction()` calls
  `scroll_into_view_if_needed()` first. EL-6267 added six KPI cards above the user-detail chart
  (EliteaAI/EliteaUI@f084ea12 + @ce8115c6), pushing its vertical centre below the viewport, which
  silently broke the raw `page.mouse.move()` the merged ELITEA-2313 spec used (tooltip never appeared).
- **Product drift on the user-detail view, unrelated to these cases but discovered here:** the KPI row
  is now **16 cards**, not 10 — `ACTIVE DAYS, LLM CALLS, TOOL CALLS, AGENT & PIPELINE RUNS, CHAT MSG,
  ERRORS, TOTAL TOKENS, INPUT TOKENS, OUTPUT TOKENS, CACHE READ TOKENS, CACHE WRITE TOKENS,
  CACHE READ COST, CACHE WRITE COST, TOTAL COST, INPUT TOKEN COST, OUTPUT TOKEN COST`
  (source-confirmed `AnalyticsUserDetailed.jsx:73-188`, all unconditional). ELITEA-2313's merged spec
  asserted 10 and was RED on `automation/base` before this branch existed (pristine-HEAD control run:
  byte-identical failure).
- **`fmt_num()` now lives in `automation/utils/analytics_format.py`** (extracted on its third consumer),
  not in `tests/ui/admin/test_analytics_overview_kpi_cards.py`.
