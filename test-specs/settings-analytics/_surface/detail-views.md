# Drill-down detail views (user / agent-pipeline)

> Part of the `settings-analytics` exploration digest — index: [`_surface.md`](../_surface.md).
> Handle cache from live exploration, not a source of truth: verify a handle as you use it.

## User Detail view (`AnalyticsUserDetailed.jsx`) — confirmed live 2026-08-05, ELITEA-2313

- **Confirmed (fresh `git fetch origin`): `AnalyticsUserDetailed.jsx` is
  byte-identical on `main` and `automation/testids`** — already fully on `main`,
  like the rest of the Analytics feature.
- **Not a route** — clicking a Users-tab row is a same-page React state swap
  (`AnalyticsUsers.jsx`'s `selectedUserId` state), not a URL navigation. The
  browser URL stays `/settings/analytics` throughout; there is no per-user deep
  link. Don't wait on a URL change — wait on the
  `analytics_user_detail/prompt_lib/` GET response + the view's own loading
  spinner instead.
- **KPI cards: TEN**, not six: `ACTIVE DAYS, LLM CALLS, TOOL CALLS,
  AGENT & PIPELINE RUNS, CHAT MSG, ERRORS, TOTAL TOKENS, INPUT TOKENS,
  OUTPUT TOKENS, TOTAL COST`. Same stale-case-text family as the tab/KPI/column
  counts elsewhere in this feature — this time for ELITEA-2313's case text.
  Filed elitea-testing-public#1191.
- **Errors KPI color rule matches the Users-table rule exactly**
  (`AnalyticsUserDetailed.jsx:99`): `color: kpis.errors > 0 ? palette.status.rejected
  : undefined`. Confirmed live: `errors=75` → `rgb(215, 22, 22)`; the other 9
  cards render `rgb(255, 255, 255)` (default). Unlike the Users-table Errors
  column (#1188), **ELITEA-2313's case text is NOT stale here** — it says
  "greater than 0", matching source/live exactly.
- **Summary panel labels**: "Models Used", "Tools Used", "**Agents & Pipelines
  Used**" (not "Agents Used" — same stale-case-text pattern; the live label
  matches the Analytics tab's own "Agents & Pipelines" naming). Each panel
  shows a count line (`"{N} models"` etc.) and, when N>0, a scrollable list of
  name+count rows; when N=0, an empty-state string ("No tool usage" etc.).
- **`KpiCard.jsx` and `ChartTooltip.jsx` are SHARED components** (also consumed
  by `AnalyticsOverview`, `AnalyticsCosts`, `AnalyticsAgentDetailed`,
  `AnalyticsToolDetailed`, `UsageSummary`) — any testid on them must be a
  caller-supplied prop (`testId`/`valueTestId` on `KpiCard`, a render-prop-
  threaded `testId` on `ChartTooltip` since Recharts injects `active`/
  `payload`/`label` at render time), wired ONLY at the `AnalyticsUserDetailed`
  call sites this case touches — not at the other consumers.
- **Chart hover tooltip works** — confirmed via a synthetic `mouseover`/
  `mousemove` dispatch during exploration (Recharts' internal hover-tracking
  listens on the whole plot `<svg>`); the ACTUAL automated test must use a real
  `page.mouse.move()`/`.hover()` at coordinates from a testid'd chart-container
  bounding box, never `page.evaluate`-dispatched synthetic events (exploration-
  only per the pristine-repro-gate rule).
- **A user with no `user_email` set renders a BLANK detail-view title** — no
  fallback to `User {id}` the way the list row has. Filed as a genuine defect,
  elitea-testing-public#1192 (not a case-text clarification — the case's
  premise assumes an email always exists). Pick a row WITH an email for any
  future case's happy-path assertions in this view (e.g. `testbot@elitea.ai`
  in the "Private" project).
- **Data endpoint**: `GET /api/v2/elitea_core/analytics_user_detail/prompt_lib/
  {project_id}?user_id={id}&date_from=...&date_to=...` — fires once per row
  click; 200 OK, no console errors. No new request fires on back-navigation
  (`handleBack` only resets local state; the Users-tab query result stays
  cached by RTK-Query from the original tab-mount fetch).

## Agent/Pipeline Detail view (`AnalyticsAgentDetailed.jsx`) — confirmed live 2026-08-05, ELITEA-2321

- **Zero pre-existing testids** on the file (mirrors the Users-detail/Agents-tab
  finding); reachable from the Agents & Pipelines tab's row click
  (`AnalyticsAgents.jsx`'s `handleAgentClick`/`selectedAgent` state) — the SAME
  same-page state-swap pattern as the Users-tab → user-detail transition, NOT a
  route/URL change. `pages/analytics_page.py`'s `open_agent_detail_by_row()`
  (ELITEA-2320) already waits on the response but stops there — ELITEA-2320's own
  spec explicitly scoped the sub-view's CONTENT out of bounds; ELITEA-2321 is the
  first case to assert it.
- **KPI cards: EIGHT**, not five: `TOTAL RUNS, UNIQUE USERS, TOTAL COST, TOTAL
  TOKENS, INPUT TOKENS, OUTPUT TOKENS, AVG LATENCY, ERRORS`
  (`AnalyticsAgentDetailed.jsx:67-110`). There is **no "Error Rate" KPI at all** —
  a case-text invention, not present in source or live product. Filed
  elitea-testing-public#1199.
- **Chart is titled "Runs by Day"**, not "Daily Usage" (`AnalyticsAgentDetailed.jsx:118`,
  conditional on `daily_usage.length > 0`). Same clarification issue (#1199).
- **Users panel columns are `User, Runs, Avg Latency, Errors`** — the second column
  is "Runs", NOT "Events" (case-text says EVENTS; same Events→Runs naming drift
  already documented for the Activity table itself, #1195). Subtitle format:
  `"{N} users used this agent / pipeline"`.
- **Tools panel columns are `Tool, Calls`** — matches case text exactly, no drift.
  Subtitle format: `"{N} tools used by this agent / pipeline"`; empty state renders
  literal text **"No tool data"** when N=0 (`AnalyticsAgentDetailed.jsx:291-297`) —
  also matches case text exactly, no drift here.
- **Errors KPI color rule**: `AnalyticsAgentDetailed.jsx:107`,
  `color: kpis.errors > 0 ? palette.status.rejected : undefined` — identical shape
  to the Users-tab/user-detail Errors cards. **No positive-branch live data** in
  "Private" at analysis time (same gap as ELITEA-2320's Activity-table Errors
  column) — negative branch only was live-verified.
- **`KpiCard.jsx` reused, same `testId`/`valueTestId` prop pair** added for
  ELITEA-2313's `AnalyticsUserDetailed` call site — this is a second call site for
  the SAME shared-component props, no new component-level work needed, just wire
  the props at `AnalyticsAgentDetailed`'s 8 `<KPICard>` call sites.
- **Title (`entity_name`) has no known blank-value gap** — unlike
  `AnalyticsUserDetailed`'s `user_email` (#1192), `entity_name` was populated on
  every row checked this run (an agent/pipeline's name, unlike a user's email,
  isn't user-optional data).
- **Test-data trick for the Tools-panel empty-state branch**: no need for a second
  project — within "Private" itself, `guardrails_test_agent` (row 1, has tool
  calls) and a low-usage pipeline row near the end of the table (e.g.
  `autotest_test_empty_pipeline_exe...`, 1 run, $0.00 cost, 0 tokens) exercise the
  populated vs. empty Tools-panel branches respectively — both reachable via one
  project, no project-switch round trip needed for this case (unlike
  ELITEA-2320's Users-column / chart-presence branches, which DO need the
  "UI Testing" project).
- **Data endpoint**: `GET /api/v2/elitea_core/analytics_agent_detail/prompt_lib/
  {project_id}?entity_id={id}&date_from=...&date_to=...` — fires once per row
  click; 200 OK, no console errors. No new request fires on back-navigation
  (`handleBack` — `AnalyticsAgents.jsx:83` — only resets local `selectedAgent`
  state; live-confirmed via `browser_network_requests` before/after the back
  click, identical request list both times).
