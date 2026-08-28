# Agents & Pipelines tab

> Part of the `settings-analytics` exploration digest — index: [`_surface.md`](../_surface.md).
> Handle cache from live exploration, not a source of truth: verify a handle as you use it.

## Agents & Pipelines tab (`AnalyticsAgents.jsx`) — confirmed live 2026-08-05, ELITEA-2320

- **Zero pre-existing testids** on `AnalyticsAgents.jsx` — every element ELITEA-2320's case touches
  needs `add-data-testid` work (16 new testids specced in its AFS). The shared
  `src/components/SearchInput.jsx` **already has a `testId` prop** (added during ELITEA-2312) —
  wiring the search input here is call-site-only, no component change.
- **Both charts (bar + area) are conditionally rendered** — `agentChartData.length > 0` /
  `chat_daily.length > 0` respectively. Confirmed live: project "UI Testing" (id `400`, 0
  agent/pipeline activity in default range) shows NEITHER chart, only the (empty) table. Don't
  assume the charts are always present — the case's own steps implicitly assume active data; use
  "Private" (id `399`) as the positive fixture, "UI Testing" as the negative one.
- **Naming drift matches the established family pattern exactly** (#1185/#1188/#1191 precedent,
  bundled this time as elitea-testing-public#1195): tab "Agents" → live "Agents & Pipelines"; bar
  chart "Most Active Agents" → live "Most Active Agents & Pipelines"; bar-chart subtitle "Top N by
  events" → live "Top N by runs" (`dataKey="runs"`); table "Agent Activity" → live "Agent & Pipeline
  Activity"; count example "2 agents" → live format "{N} agents & pipelines"; search placeholder
  "Search by agent name" → live "Search by agent or pipeline name". The ONE exception: the "Chat
  Messages" chart's title AND subtitle ("User messages per day") match the case text exactly — no
  drift there.
- **Table columns are NOT fixed** — `!isPersonalProject && <Users column>` is a real conditional
  branch (`isPersonalProject` = `useSelectedProjectId() === personal_project_id`). Confirmed live:
  "Private" (personal project) → **8 columns**, no Users column; "UI Testing" (non-personal) → **9
  columns**, Users inserted right after Runs. Full personal-project column order: `Agent / Pipeline,
  Runs, Cost, Total Tokens, Input Tokens, Output Tokens, Avg Latency, Errors`. No "Events" column
  exists anywhere (the case's claimed column) — the equivalent metric is named "Runs".
- **Row click** (`onClick={() => handleAgentClick(a.entity_id)}` on the whole row `Box`, not an
  `<a>`) opens a same-page "agent/pipeline detail" sub-view — same same-page state-swap pattern as
  `AnalyticsUserDetailed` (ELITEA-2313), confirmed live: KPI cards (TOTAL RUNS, UNIQUE USERS, TOTAL
  COST, TOTAL TOKENS, INPUT/OUTPUT TOKENS, AVG LATENCY, ERRORS — 8 cards), a "Runs by Day" chart, and
  Users/Tools breakdown tables, plus a Back button. No dedicated AFS/page-object coverage of this
  detail sub-view's own content yet — ELITEA-2320 only asserts click-navigates (mirrors how
  ELITEA-2312 stopped at "row is clickable" and left the detail view to ELITEA-2313; a future case
  should do the same split here if the detail sub-view needs its own assertions).
- **Errors-column color rule**: identical shape to the Users tab (`AnalyticsAgents.jsx:317`,
  `color: a.errors > 0 ? palette.status.rejected : undefined`). **No positive-branch (`errors > 0`)
  live data available in "Private"'s agent/pipeline Activity rows** at analysis time (unlike the
  Users tab, which DOES have `errors > 0` rows in this same project) — documented as a Blocked Step
  in ELITEA-2320's AFS, not a defect.
- **Data endpoint**: `GET /api/v2/elitea_core/analytics_agents/prompt_lib/{project_id}?date_from=...&date_to=...&limit=...&offset=...&search=...&sort_by=events&sort_order=desc`
  — distinct from Overview/Users endpoints; fires on tab mount and on search-input change. Row click
  fires `GET /api/v2/elitea_core/analytics_agent_detail/prompt_lib/{project_id}?entity_id={id}&date_from=...&date_to=...`
  once. Both 200 OK, no console errors, confirmed in "Private" (25 rows) and "UI Testing" (0 rows).

**Resolved/added during ELITEA-2314..2319 implementation (2026-08-28):**
- **The "Chat Messages" `AreaChart` is assertable on DATA, not just presence** — its XAxis renders
  `date.slice(5)` of the response's `chat_daily`, so
  `AnalyticsPage.get_agents_chat_chart_tick_labels()` (#579-scoped recharts handle inside
  `analytics-agents-chat-chart-container`) is directly comparable to that array. Measured live
  2026-08-28, project 399: `Last 24h` → `chat_daily` 2 entries / 1-day span, ticks
  `['08-27', '08-28']` / 1-day span; `Last 30d` → 26 entries / 29-day span, 13 ticks `07-31…08-28`
  / **28-day** span. Recharts thinned only 1 day off the span here, so the specs' 10-day
  `CHART_TICK_EDGE_SLACK_DAYS` is generous while a chart still drawing the 24h series under 30d
  (span 1 vs a required ≥19) fails loudly. Presence alone cannot catch that: a stale chart is
  still exactly one container.
- **The "Most Active Agents & Pipelines" `BarChart` is a category axis with `interval={0}`**
  (`dataKey="agent_name"`), the same shape as the Tools chart — so its rendered tick list **equals**
  the response's charted names in order, and exact list equality is available (strictly stronger
  than the `Top {N} by runs` subtitle check alone).
- **The merged ELITEA-2320 spec is RED on `automation/base` for product drift** (verified with a
  pristine-page-object control run): the Agent & Pipeline Activity table gained cost/cache columns
  (`TOTAL COST`, `INPUT TOKEN COST`, `OUTPUT TOKEN COST`, `CACHE READ TOKENS`, `CACHE WRITE
  TOKENS`, …) vs its 8-column tuple. `adjust-automated-test` work, unrelated to the date-filter
  cases.
