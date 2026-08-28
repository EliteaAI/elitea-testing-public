# Surface digest — settings-analytics

> Handle cache from live exploration, not a source of truth. Verify a handle
> as you use it. One writer at a time (analyst, whoever is active this
> session) — see `test-case-analysis` § 2b.

## Where it lives

- URL: `/settings/analytics` (route registered under `Settings` parent route,
  `EliteaUI/src/[fsd]/app/routes/ProtectedRoutes.jsx:364`)
- Source: `EliteaUI/src/[fsd]/features/settings/ui/analytics/` —
  `AnalyticsContainer.jsx` (page shell: header, date filter, tab bar, tab
  routing) + one component per tab (`AnalyticsOverview`, `AnalyticsCosts`,
  `AnalyticsAgents`, `AnalyticsTools`, `AnalyticsUsers`, `AnalyticsHealth`,
  `AnalyticsGuide`) + `AnalyticsUserDetailed`/`AnalyticsAgentDetailed`/
  `AnalyticsToolDetailed` drill-down views.
- **Confirmed (2026-08-05, `git fetch origin` fresh): `AnalyticsContainer.jsx`
  is byte-identical on `main` and `automation/testids`** (same blob SHA) —
  the whole Analytics feature is already on `main`, not testids-only.

## Confirmed live behaviour (2026-08-05, localhost, project "UI Testing")

- **Tabs: SEVEN**, in this order: `Overview, Costs, Agents & Pipelines, Tools,
  Users, Health, Guide` — role `tablist` → 7 `tab` children. (Several sibling
  TMS cases in this family, e.g. ELITEA-2311/2320, describe "six tabs" /
  "Agents tab" — that phrasing is stale; the live tab set is the one above.
  See elitea-testing-public#1185.)
- **Date presets: four**, `Last 24h / Last 7d / Last 30d / Last 90d`
  (`TabGroupButton` + `TabButtonItem`, `DEFAULT_PRESETS` array,
  `AnalyticsContainer.jsx:35-39`). Default selected = **Last 24h**
  (`selectedDatePreset` initial state = `1`) → default From/To span is
  **1 day**, not 7. A 5th "Custom" preset appears only after the user edits
  a picker directly (`isCustomRange` branch) — not present on initial load.
- **Overview tab is selected by default** (`activeTab` initial state = `0`).
- **KPI cards on Overview: EIGHT**, not six — `TEAM, AI ACTIVE, LLM CALLS,
  TOOL RUNS, CHAT MSG, AGENT & PIPELINE RUNS, TOKENS, COST`
  (`AnalyticsOverview.jsx`). Same stale-case-text pattern as the tab count —
  flag if you hit a case claiming "six KPI cards" (e.g. ELITEA-2311).
- Loading state: `CircularProgress` shown only while `needsOverview &&
  isFetching` (`needsOverview` = Overview or Health tab active). Resolves
  quickly (~200 OK observed on `GET /api/v2/elitea_core/analytics/
  prompt_lib/{project_id}?date_from=...&date_to=...`), no console errors.
- Project badge (`Project: {name}`) only renders when a project is selected
  (`projectName` truthy) — precondition, not always-visible chrome.

## Testids

**Zero pre-existing testids** on anything in `AnalyticsContainer.jsx` except
`analytics-export-button` (Export to Excel icon button, already on `main`).
Header title, project badge, date presets, From/To pickers, and all 7 tabs
have NO testid — every case touching them needs `add-data-testid` work. Full
naming set + PROVENANCE for ELITEA-2310's touched elements:
`test-specs/settings-analytics/l2_analytics-page-default-load_ELITEA-2310.md`
§ Concrete Handles. Reuse those exact names for sibling cases that touch the
same elements (tabs, presets, title, badge) — don't re-derive/rename.

Shared-component wiring notes for the implementer:
- `TabButtonItem.jsx` (preset buttons) spreads `{...item.buttonProps}` onto
  its `ToggleButton` — pass `buttonProps: {'data-testid': '...'}` per preset
  item in `DEFAULT_PRESETS`.
- `BaseTab.jsx` spreads `{...restProps}` onto MUI `Tab`, which forwards
  unknown props to the underlying DOM button — pass `data-testid` directly
  on each `<BaseTab>` in the `.map()` at `AnalyticsContainer.jsx:278-284`.
- Date pickers currently share one `datePickerCommonProps` object between
  From and To — needs splitting (or a per-field override) so From/To can
  carry distinct testids via `slotProps.textField.inputProps`.

## No page object yet

`pages/analytics_page.py` does not exist — ELITEA-2310 is the first case in
this feature area. First implementer creates it.

## Users tab (`AnalyticsUsers.jsx`) — confirmed live 2026-08-05, ELITEA-2312

- **Confirmed (fresh `git fetch origin`): `AnalyticsUsers.jsx` is byte-identical
  on `main` and `automation/testids`** (blob `c7b6ff4b68aec5e6f8b72e433cbe8c62126e5d04`
  on both) — like the rest of the Analytics feature, already fully on `main`.
- **Zero pre-existing testids** on `AnalyticsUsers.jsx` or the shared
  `src/components/SearchInput.jsx` it renders — every element this tab's cases
  touch needs `add-data-testid` work (10 new testids specced in ELITEA-2312's
  AFS: title, count, search input via a new `testId` prop on the shared
  component, table-header row, repeated row/errors-cell testids, and 4
  `TablePagination` `slotProps` wirings).
- **Table has 9 columns**, not the 8 several sibling case texts describe:
  `User, Active Days, LLM Calls, Tool Calls, Agent/Pipeline Runs, Chat Msg,
  Errors, Total Tokens, Total Cost` — no "Events" column exists. Same
  stale-case-text family as the tab/KPI counts above. Filed
  elitea-testing-public#1188.
- **Errors column color rule** (`AnalyticsUsers.jsx:144-151`):
  `color: u.errors > 0 ? palette.status.rejected : undefined` — red only when
  `errors > 0`; `errors === 0` renders default text color (confirmed live:
  `rgb(255, 255, 255)`). Case texts describing "red when ≥ 0" are stale — same
  issue #1188.
- **Search input live-filters** on every keystroke (`onChange` → `search`
  state → query param), no debounce/Enter/blur needed — confirmed live
  (typing "testbot" narrowed 3→1 row, updated count + pagination label).
- **Pagination**: MUI `TablePagination`, `rowsPerPageOptions=[10,20,50]`,
  default `rowsPerPage=20`. With ≤20 total users it's a single page — both
  prev/next arrows disabled, range label `"1–{total} of {total}"`.
- **Data endpoint**: `GET /api/v2/elitea_core/analytics_users/prompt_lib/
  {project_id}?date_from=...&date_to=...&limit=...&offset=...&sort_by=total_events&sort_order=desc`
  — distinct from the Overview/Health endpoint (`.../analytics/prompt_lib/...`,
  no `_users`); fires on tab mount and on every search-input change. 200 OK,
  no console errors, in both cases observed.
- **No positive-case (`errors > 0`) live data available** in the "UI Testing"
  exploration project — all 3 users observed have `errors: 0`. The red-color
  branch is source-confirmed but not live-exercised; ELITEA-2312's AFS
  documents this as a Blocked Step, not a defect. **Resolved during ELITEA-2312
  implementation**: the `auth_state` fixture's actual default project is
  **"Private" (project id `399`)**, distinct from the analyst's exploration
  project "UI Testing" — "Private" has real `errors > 0` rows (`User 6250`:
  errors=78, `testbot@elitea.ai`: errors=75, live in the default "Last 24h"
  range) so the positive branch is live-exercisable with no seeding. Confirmed
  again during ELITEA-2313 exploration (2026-08-05) — switch the project
  selector to "Private" (`select-option-399` — no dedicated testid on the
  option itself, MUI Select generates it) for any future case in this feature
  needing `errors > 0` fixture data.

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

## Date filter (presets + From/To pickers) — confirmed live 2026-08-28, ELITEA-2314..2319

**⚠️ The "Tabs: SEVEN" note above is now STALE.** The live tab bar has **EIGHT** tabs, in this
order: `Overview, Costs, Tokens, Agents & Pipelines, Tools, Users, Health, Guide` — a **Tokens**
tab (`AnalyticsTokens`, `activeTab === 2`, testid `analytics-tab-tokens`) was added after
ELITEA-2310 shipped and is **on `main`**. Consequences the next agent must know:
`AnalyticsPage.get_tabs_in_order()` still returns seven Locators and has no `tab_tokens` field, and
ELITEA-2310's merged spec still asserts a 7-label tuple — see elitea-testing-public issue filed
from the ELITEA-2314..2319 run. `needsOverview` is still `activeTab === 0 || activeTab === 6`
(Overview / Health), which is correct for the 8-tab indexing.

- **Presets fire one `analytics/prompt_lib/` GET per click**, `date_from = now - Ndays`,
  `date_to = now`; the four spans were live-verified (1/7/30/90 days, ±minutes). Clicking the
  ALREADY-active preset is a deliberate no-op (`handleDatePresetChange` returns early on MUI's
  exclusive-`ToggleButtonGroup` `null`), so a test that starts by clicking the default preset
  observes nothing.
- **Editing either picker switches the control to `Custom`**: a FIFTH chip appears
  (`PRESETS_WITH_CUSTOM`) and is `aria-pressed="true"` while all four predefined presets go
  `false`. It now carries `analytics-date-preset-custom` (added 2026-08-28).
- **Picker mechanics** (`@mui/x-date-pickers` v7 `DateTimePicker`, `format dd/MM/yyyy HH:mm`,
  `ampm: false`): the field is a plain editable `<input>` (`input_value()` works). The action bar
  is `['clear','accept']` with `okButtonLabel: 'Apply'` — the confirm button reads **"Apply"**, not
  "Ok" as several case texts say. **Selecting a day fires the data GET immediately** (`onChange`);
  **Apply only closes the popper and fires nothing** — wait on the response around the day click.
- **Constraint pair**: From has `maxDateTime={dateTo}`, To has `minDateTime={dateFrom}`. Live: with
  To = 23/08, the From calendar renders 24..31 disabled and "Next month" disabled; with From =
  10/08, the To calendar renders 1..9 disabled and "Previous month" disabled. This is the whole
  mechanism behind ELITEA-2316 — there is no error message, the prevention is the disabled state.
- **New testids (EliteaAI/EliteaUI@22ff73c0, `automation/testids`, awaiting human cherry-pick to
  `main`)**: `analytics-date-preset-custom`, `analytics-date-{from,to}-open-button`,
  `analytics-date-{from,to}-popper`, `analytics-overview-kpi-card`, `analytics-overview-kpi-value`,
  `analytics-overview-daily-chart-container`, `analytics-overview-leaderboard(-row)`,
  `analytics-overview-model-usage-table(-row)`, `analytics-tools-details-title`,
  `analytics-tools-count`, `analytics-tools-table-header`, `analytics-tools-row`,
  `analytics-tools-loading-indicator`.
- **Resolved/added during ELITEA-2318 implementation (fix round 2)**: the Tools tab's
  **"Most Popular Tools" `BarChart` had no handles at all** — `analytics-tools-chart-subtitle`
  and `analytics-tools-chart-container` added in EliteaAI/EliteaUI@b74c4d90 on
  `automation/testids` (awaiting human cherry-pick to `main`). Both land on existing nodes;
  the chart-wrapper `Box` was only reformatted to multi-line to host the attribute.
- **Inside the popper everything is MUI-internal** — day cells (`button.MuiPickersDay-root`), the
  month header, the month-nav arrows and the Clear/Apply buttons cannot carry an app testid without
  overriding MUI slot components (a functional change). They are reached as **scoped raw handles
  inside the `analytics-date-{from,to}-popper` testid**, the `.agents/testing.md` § Locator policy
  #579 exception 1, declared in `AnalyticsPage`'s method docstrings.
- **Overview content is data-conditional**: `ModelUsageTable` returns `null` for an empty `models`
  list, and the leaderboard renders "No AI activity data." instead of rows when `top_ai_users` is
  empty. Live 2026-08-28, project 471 "Elitea Testing Team": `Last 7d` → all-zero KPIs, no
  leaderboard rows, no Model Usage table; `Last 30d` → LLM CALLS 218, leaderboard + 4 model rows.
  **Do not write "the numbers must differ" assertions** — assert the rendered content against the
  captured response body instead (`.agents/testing.md` § Fidelity policy).
- **Daily Activity X-axis** renders `MM-DD` labels (`tickFormatter: d => d?.slice(5)`) and recharts
  THINS them (30-day range showed 10 ticks, 07-31…08-28, skipping days) — assert the span and the
  last tick, never a tick-per-day count.
- **Date filter state survives every tab switch** (it lives in `AnalyticsContainer`, above the tab
  bodies): live-verified across Agents & Pipelines → Tools → Users → Health → Guide → Overview, all
  six holding From `29/07/2026 18:27` / To `28/08/2026 18:27` with `Last 30d` pressed.
- **⚠️ Dev-server gotcha (cost ~15 min this run):** Vite's file watcher did NOT see edits to
  `../EliteaUI/src` (OneDrive-backed clone) — the server kept serving the pre-edit module for both
  the plain and `?t=` URLs even after `touch`, so new testids were invisible in the browser while
  present on disk. **Restarting the dev server fixed it.** Verify a new testid via
  `curl -s 'http://localhost:5173/src/%5Bfsd%5D/.../File.jsx' | grep <testid>` before concluding the
  testid is wrong.

### Resolved/added during ELITEA-2314..2319 implementation (2026-08-28)

- **Wide-range analytics queries are SLOW.** `Last 30d`/`Last 90d` on the `auth_state` fixture's
  project (id **399**, the one the pytest session lands on — distinct from the project a
  Playwright-MCP browser session shows) regularly need **more than 15 s** to answer, while
  `Last 24h`/`Last 7d` come back in a few seconds. `NAVIGATION_TIMEOUT` (15 s) is NOT enough:
  `AnalyticsPage` now has `DATA_QUERY_TIMEOUT = 60_000` for every range-changing wait. A
  `TimeoutError: … waiting for event "response"` on a preset click is this, not a missing request.
- **Recharts axis ticks need `all_text_contents()`, never `all_inner_texts()`** — SVG `<text>`
  nodes have no `innerText`, so `all_inner_texts()` yields `None` entries and blows up on `.strip()`.
- **MUI keeps the outgoing month grid mounted during a picker month transition** — right after a
  "Previous month" click the same day number resolves to 2-4 nodes (measured: 4 across a 3-month
  walk), a strict-mode violation. `AnalyticsPage.get_picker_day_cell()` now waits for the match to
  settle to exactly one (`expect(...).to_have_count(1)`) — a condition wait, not a sleep.
- **Response ≠ render on every tab**: `expect_response` returning does not mean rows exist yet.
  `AnalyticsPage.wait_for_tab_settled(surface)` (public, additive sibling of the private
  `_wait_for_*_settled` helpers) closes the gap for overview/users/agents/tools.
- **Two MERGED analytics specs are RED on `automation/base` for product drift** (verified with a
  pristine-page-object control run, identical failures): the Users-tab table now has extra columns
  (`INPUT TOKENS`, `OUTPUT TOKENS`, `INPUT TOKEN COST`, …) vs ELITEA-2312's 9-column tuple, and the
  Agents & Pipelines table likewise (`TOTAL COST`, `INPUT TOKEN COST`, `OUTPUT TOKEN COST`,
  `CACHE READ TOKENS`, `CACHE WRITE TOKENS`, …) vs ELITEA-2320's 8-column tuple.
  `test_analytics_default_load.py` still passes. This is `adjust-automated-test` work, unrelated to
  the date-filter cases.

### Resolved/added during ELITEA-2314..2319 fix round 1 (2026-08-28)

- **`wait_for_tab_settled(surface)` now genuinely exists** on `AnalyticsPage` (surface-keyed
  `_loading_indicator()` + a `wait_for(state="hidden")`). The previous round documented it here
  and called it from five spec sites without ever defining it — a spec in that state raises
  `AttributeError` on the first call, so it cannot have been run. Pinned by
  `tests/unit/test_analytics_date_filter_spec_invariants.py`, which AST-walks both specs and
  checks every `analytics_page.<attr>` against the page object's real MRO members.
- **Recharts tick labels are YEAR-LESS (`date.slice(5)` → `"MM-DD"`).** Never difference them
  arithmetically: a Last-30d window straddling New Year renders `12-11…01-10`, which
  month-arithmetic scores as **-331 days**. Resolve each tick back to the full `YYYY-MM-DD` entry
  of the response's own series first (`_response_dates` / `_chart_tick_span_days` in
  `test_analytics_date_filter_content_refresh.py`).
- **The Agents tab's "Chat Messages" `AreaChart` is assertable on DATA, not just presence** —
  its XAxis renders `date.slice(5)` of the response's `chat_daily`, so
  `AnalyticsPage.get_agents_chat_chart_tick_labels()` (#579-scoped recharts handle inside
  `analytics-agents-chat-chart-container`) is directly comparable to that array. Measured live
  2026-08-28, project 399: `Last 24h` → `chat_daily` 2 entries / 1-day span, ticks `['08-27',
  '08-28']` / 1-day span; `Last 30d` → 26 entries / 29-day span, 13 ticks `07-31…08-28` /
  **28-day** span. So recharts thinned only 1 day off the span here — the specs' 10-day
  `CHART_TICK_EDGE_SLACK_DAYS` is generous, and a chart still drawing the 24h series under 30d
  (span 1 vs a required ≥19) fails loudly. Presence alone cannot catch that: a stale chart is
  still exactly one container.
- **The Tools tab's "Most Popular Tools" `BarChart` is assertable on DATA too, and more
  strictly than the area charts** — `AnalyticsTools.jsx` charts `data.rows.slice(0, 20)` with
  `dataKey="tool_name"` and **`interval={0}`**, so recharts does NOT thin: every charted series
  renders exactly one tick and the rendered label list **equals** the response's first 20
  `tool_name`s, in order (no subset/slack reasoning needed, unlike the date-axis charts).
  `AnalyticsPage.get_tools_chart_tick_labels()` reads them (#579-scoped recharts handle inside
  `analytics-tools-chart-container`). Measured live 2026-08-28, project 399: `Last 24h` → 1
  charted row, ticks `['list_branches_in_repo']`; `Last 30d` → 20 charted rows, a wholly
  different 20-name list. A chart frozen on the 24h series under 30d renders 1 tick against 20
  expected → fails; presence (`count() == 1`) is invariant across both.
- **The Users tab renders NO chart** (`AnalyticsUsers.jsx` is table + pagination only) — so
  "repeat the chart steps on the Users tab" has no counterpart there. Worth stating explicitly
  in an AFS rather than leaving the absence implicit.
- **Known noise — a wide-range analytics query can return `502` outright, and the suite's rerun
  filter does NOT catch it.** During fix round 1, one of five invocations of
  `test_presets_update_pickers_and_refresh_content` (ELITEA-2314) failed on
  `AssertionError: Last 30d: analytics request returned 502 / assert 502 == 200` after 38 s; it
  passed standalone immediately after (42.77 s) and in the full-set run that followed
  (14 passed, `reruns.json == {}`). Same family as the "wide-range queries are SLOW" entry above —
  a gateway giving up on the 30-day query, not a code defect.
  ⚠️ `pytest.ini`'s `--only-rerun="502 Server Error"` matches the **requests/HTTPError** wording;
  an assertion that formats the status itself (`returned 502`, `assert 502 == 200`) does not
  contain that phrase, so pytest-rerunfailures does **not** retry it. Any spec asserting
  `response.status == 200` on a slow analytics range is exposed to a hard red from this. Raised to
  the lead as a finding rather than fixed here — widening a shared rerun filter is a
  suite-wide blast radius, not a fix-round change.
