# Surface digest — Analytics (`/settings/analytics`)

Seeded 2026-07-24 by GAP-073 analysis. Handle cache for the Analytics
feature family (Overview / Agents / Tools / Users / Health / Guide tabs) —
verify every handle below live before trusting it; this is a cache, not a
substitute for execution.

## Routing (confirmed live — non-obvious, read before navigating)

Analytics is a **Settings sub-route**, not top-level: `AnalyticsContainer`
is mounted at `path="analytics"` nested under `RouteDefinitions.Settings`
(`/settings`) — `ProtectedRoutes.jsx:359-362`. The real URL is
`/settings/analytics`. A bare `/analytics` navigation 404s ("Page not
found", confirmed live) — several GAP case texts (070–074, 073) just say
"Navigate to the Analytics page" without the path; this is a case-text gap
across the whole family, not a one-off. File/flag it once per case
(clarification, not a defect) rather than re-discovering it each time.

## Tab model (`AnalyticsContainer.jsx`, single source of truth)

Six tabs, index-addressed (`activeTab` state, `BaseTabs`/`BaseTab`):
`0=Overview, 1=Agents, 2=Tools, 3=Users, 4=Health, 5=Guide`. Overview (0)
and Health (4) share one data fetch (`needsOverview = activeTab===0 ||
activeTab===4`, `useProjectAnalyticsQuery`) — Agents/Tools/Users fetch
independently per-tab with their own `projectId`/`dateFrom`/`dateTo` props.

**Cross-tab drill-down pattern (the GAP-073 mechanism, likely reused by
GAP-072's Tools-tab equivalent):**
- `AnalyticsContainer` owns `pendingUserId` state and passes
  `onUserClick={handleOverviewUserClick}` into `AnalyticsOverview`.
  `handleOverviewUserClick(userId)` → `setPendingUserId(userId)` +
  `setActiveTab(3)`.
- `AnalyticsUsers` receives `initialUserId={pendingUserId}` +
  `onBackToSource={handleBackToOverview}`. It seeds
  `selectedUserId = useState(initialUserId || null)` AND separately captures
  `cameFromExternal = useState(() => !!initialUserId)` — a **lazy
  initializer frozen at mount**, so it stays `true` for this mount's
  lifetime even after `pendingUserId` is cleared. `handleBack` branches on
  `cameFromExternal`: `true` → `onBackToSource()` (→ Overview, tab 0);
  `false` → `setSelectedUserId(null)` (→ back to the User Activity list,
  same tab). This is TWO distinct, valid test paths through the same
  `handleBack` — don't assume "Back" always means "→ Overview".
- Because `selectedUserId` is seeded truthy on the FIRST render when arriving
  cross-tab, `AnalyticsUsers`'s own User Activity list (table header +
  `StyledSearchInput`) is never constructed via an early `if (selectedUserId)
  return <AnalyticsUserDetailed .../>` — genuine mutual exclusion by control
  flow, not a visibility toggle. Safe to assert "list is absent" as a
  structural invariant, not just an incidental one.
- `AnalyticsTools`/`AnalyticsAgents` likely have an analogous detail
  component (`AnalyticsToolDetailed.jsx`, `AnalyticsAgentDetailed.jsx` — both
  confirmed to exist, same `IconButton onClick={onBack}` + `ArrowBackIcon`
  shape as `AnalyticsUserDetailed`) but their OWN cross-tab-drill-down wiring
  (if any exists — GAP-072 targets `AnalyticsTools.jsx` specifically) was
  **not verified this run**; re-check `AnalyticsContainer.jsx` for an
  equivalent `handleOverviewToolClick`/`onToolClick` prop before assuming
  the pattern is identical. As of GAP-073's read of `AnalyticsContainer.jsx`,
  only `onUserClick`/`handleOverviewUserClick` exists — no analogous
  tool/agent click handler is wired from Overview. GAP-072's title
  ("Tools tab: clicking a tool row … Back returns to the table") describes
  an in-tab drill (Tools list → Tool detail → Back to Tools list), NOT a
  cross-tab Overview→Tools jump — likely the SAME single-branch shape as
  `AnalyticsUsers`'s native (non-external) Back path, not the GAP-073
  cross-tab mechanism. Re-verify live, don't assume.

## KPICard — shared component, no testid prop yet (as of 2026-07-24)

`ui/components/KpiCard.jsx` (displayName `KpiCard`, imported as `KPICard`)
renders `label`/`value`/`valueSuffix`/`subtitle`/`color`/`badge` props —
**zero `data-testid` support today**. Used by:
- `AnalyticsOverview.jsx` — 6 cards: TEAM, AI ACTIVE, LLM CALLS, TOOL RUNS,
  CHAT MSG, AGENT RUNS.
- `AnalyticsUserDetailed.jsx` — 6 cards: LLM Calls, Tool Calls, Chat Msg,
  Agent Runs, Active Days, Errors.
- `AnalyticsAgentDetailed.jsx` / `AnalyticsToolDetailed.jsx` — not read in
  detail this run; presumably similar per-entity KPI rows (check before
  reusing testid names — GAP-072/GAP-074 will need their own).

**Shared-component ruling applies** (`.agents/testing.md` § Locator
policy): add an optional `testId` prop to `KpiCard.jsx` itself
(`data-testid={testId}` on the root `Box`), then wire it ONLY at the call
sites each case's test actually touches — never blanket-add across all
KPI cards project-wide. GAP-073 wires 7 of the ~12+ existing `KpiCard`
call sites (TEAM in Overview + all 6 in UserDetailed); GAP-070/071/072/074
will each need their own subset wired when they land, following the same
`testId` prop, never a hardcoded value inside `KpiCard.jsx`.

## SearchInput — shared component, no testid prop yet (as of 2026-07-24)

`@/components/SearchInput` (displayName `StyledSearchInput`) — plain MUI
`Input` wrapper, `search`/`onChangeSearch`/`sx`/`placeholder` props, zero
`data-testid` support. Used by `AnalyticsTools.jsx`, `AnalyticsUsers.jsx`,
`AnalyticsAgents.jsx` (confirmed via `grep -rln "components/SearchInput"`)
— GAP-070/071 (Agents/Tools search-filter cases) will need their OWN
`testId` prop wiring at their own call sites; GAP-073 only needed one
(`AnalyticsUsers.jsx`'s, for an ABSENCE check, not an interaction).

## Date filter (`TabGroupButton`, `AnalyticsContainer.jsx`)

`DATE_FILTER_PRESETS` = `Last 24h`(1) / `Last 7d`(7) / `Last 30d`(30) /
`Last 90d`(90), default `selectedDatePreset=1` (Last 24h) on page load.
**No testids captured this run** — GAP-073 only needed to click "Last 30d"
once and didn't assert on the control itself; a future case testing the
date filter directly (custom From/To pickers, preset switching assertions)
should add testids there. No confirmed live default-preset leaderboard
row count — with `Last 24h` the Top 5 AI Adopters card may render 0 rows
depending on recent shared-suite activity; `Last 30d` reliably rendered 1
row (`testbot@elitea.ai`) at analysis time. This is incidental, mutable,
shared dev-project data — not a seeded fixture; don't hardcode the exact
row count or email as an invariant, read it live.

## Network / data shape

Single `useProjectAnalyticsQuery` (Overview+Health) response shape (from
live capture): `{ kpis: {...}, top_ai_users: [{user_id, user_email,
llm_calls, tool_runs, agent_runs, ai_events}], daily_activity: [...],
models: [...] }`. Per-user detail (`useAnalyticsUserDetailQuery`):
`{ user_email, kpis: {llm_events, tool_events, chat_events, agent_events,
active_days, errors}, models, tools, agents, daily_activity }`. No
WebSocket involved anywhere on this surface (unlike Chat) — ordinary
awaited REST responses, Playwright's auto-retrying `expect()` is
sufficient, no custom wait helper needed.

## Browser-lane note (2026-07-24, GAP-073)

The shared Playwright MCP browser (lane 0) was occupied by a concurrent
session at dispatch time (`navigate`/`snapshot` both errored "Browser is
already in use"). Fell back to an isolated `browser-verify` (CDP) Chrome
instance on a dedicated port (`--remote-debugging-port`, own
`--user-data-dir`) per `.agents/role-overrides.md` browser-lane discipline
— the default `chrome-launcher.sh` script uses a FIXED port (9222) and
FIXED user-data-dir/pidfile, so it is NOT itself safe for concurrent
isolated use across parallel analyst lanes; launch Chrome manually with
unique `--remote-debugging-port`/`--user-data-dir` and point `cdp.mjs` at
it via `CDP_PORT=<port>` if the default port may collide. Also note:
`cdp.mjs`'s `evaluate` command takes a raw JS *expression* (via CDP
`Runtime.evaluate`), not a function to be auto-invoked — wrap arrow
functions in an IIFE (`(() => {...})()`), or `Runtime.evaluate` just
returns the function value itself (`{"type":"function"}`) without running
it. `get-network`/`get-console` are scoped to a single CLI process's
lifetime (a fresh `node cdp.mjs` invocation each time) — they do NOT
persist across separate command invocations the way a stateful Playwright
MCP session does; capture what you need within one command, not across
several.
