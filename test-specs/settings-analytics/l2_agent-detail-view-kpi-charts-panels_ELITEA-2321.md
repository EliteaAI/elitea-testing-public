# Test Case: Clicking an agent row in Agents tab opens the agent detail view

## Metadata
- **TMS ID**: ELITEA-2321
- **Linked Story**: none
- **Priority**: l2 (case priority "medium"; l2 matches the established naming for this
  feature's sibling cases ELITEA-2310/2312/2313/2320 — same "medium" TMS priority)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI`
  `automation/testids` — dev server serves this branch; source read directly from
  `../EliteaUI/src/[fsd]/features/settings/ui/analytics/AnalyticsAgentDetailed.jsx`,
  same file tree as the other Analytics feature files already confirmed on `main`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost — no manual login)
- **Analyst**: qa-engineer (analyst slot), batch `elitea-2321`
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (`auth_state` fixture — localhost skips login via `VITE_DEV_TOKEN`).
- Project switched to "Private" (id `399`, same fixture project ELITEA-2312/2313/2320
  use) — **not** "UI Testing" (id `400`), which has zero agent/pipeline activity in the
  default "Last 24h" range (confirmed live, same finding as ELITEA-2320's Preconditions).
  "Private" has 25 agents/pipelines with runs; live-observed detail rows:
  - `guardrails_test_agent` (entity_id `7580`, row 1): `TOTAL RUNS=4, UNIQUE USERS=1,
    TOTAL COST=$0.008022, TOTAL TOKENS=13.5K, INPUT TOKENS=12.9K, OUTPUT TOKENS=573,
    AVG LATENCY=190ms, ERRORS=0`; Users panel: 1 user (`testbot@elitea.ai`, 4 runs,
    190ms, 0 errors); Tools panel: 1 tool (`get_issue`, 4 calls) — used to exercise the
    **populated** Tools-panel branch.
  - `autotest_test_empty_pipeline_exe...` (a pipeline, near end of the table, 1 run,
    $0.00 cost, 0 tokens): Users panel has 1 user (`testbot@elitea.ai`, 1 run, 163ms,
    0 errors); Tools panel is **empty** — "0 tools used by this agent / pipeline" +
    "No tool data" — used to exercise the **empty-state** Tools-panel branch (case
    step 8).
- **Errors-positive-branch gap inherited from ELITEA-2320**: all 25 rows in "Private"'s
  default range have `errors: 0` at analysis time — the Errors KPI card's red-color
  branch (`kpis.errors > 0`) is source-confirmed only, not live-exercised in this
  session. Same blocked-step precedent as ELITEA-2320's Errors-column positive branch;
  do not block merging on it (see § Blocked Steps).

## Test Data
### reuse-existing
- No test data required — read-only assertions against the `auth_state` fixture's
  existing "Private" project analytics data. Exact numeric values are not hardcoded as
  pass/fail criteria except where explicitly noted (structural/format contracts only,
  same approach as ELITEA-2312/2313/2320).

## Test Steps
1. Navigate to Settings → Analytics, switch to the "Private" project, and click the
   "Agents & Pipelines" tab (reuse `AnalyticsPage.navigate()` + `switch_project("399")`
   + `open_agents_pipelines_tab()`, all already on `main`/`automation/base` from
   ELITEA-2310/2320). Click the `guardrails_test_agent` row (reuse
   `AnalyticsPage.open_agent_detail_by_row(index)` from ELITEA-2320 — merged, but its
   own case explicitly scoped OUT asserting the sub-view's own content beyond
   "navigation succeeds, no console error"; this case is the first to assert that
   content).
   - **Verify**: the Agent & Pipeline Activity table panel is replaced by the detail
     view (no URL change — confirmed via source: `AnalyticsAgents.jsx`'s
     `handleAgentClick` sets local `selectedAgent` state, which conditionally renders
     `<AnalyticAgentDetailed>` in place — same same-page state-swap pattern as
     ELITEA-2313's user-detail view). Wait on the
     `analytics_agent_detail/prompt_lib/` GET response (`open_agent_detail_by_row`
     already does this), then on the detail view's own loading spinner going hidden,
     before asserting content.
2. Verify the detail view's title is the agent/pipeline's name (`guardrails_test_agent`
   in the live fixture) and a back-arrow icon button is present to its left.
   - **No drift** — case step 3 ("agent name as title with a back arrow") matches live
     exactly (`AnalyticsAgentDetailed.jsx:52-64`).
3. Verify exactly **eight** KPI cards are shown, in this order: `TOTAL RUNS, UNIQUE
   USERS, TOTAL COST, TOTAL TOKENS, INPUT TOKENS, OUTPUT TOKENS, AVG LATENCY, ERRORS`.
   — **Case-text drift** (see § Known Defects, filed elitea-testing-public#1199): the
   case's step 4 lists **five** KPI cards (`Total Events, Unique Users, Avg Latency,
   Errors, Error Rate`) — no "Error Rate" KPI exists at all, "Total Events" is
   actually named `TOTAL RUNS`, and `TOTAL COST, TOTAL TOKENS, INPUT TOKENS, OUTPUT
   TOKENS` are omitted entirely. Live product (and source,
   `AnalyticsAgentDetailed.jsx:67-110`) confirms eight cards. Same stale-count family
   as ELITEA-2310/2312/2313/2320; this AFS asserts the live eight-card contract, not
   the case's five.
4. Verify the Errors KPI card's value renders in the red/rejected color when
   `errors > 0`, and in the default text color otherwise (source:
   `AnalyticsAgentDetailed.jsx:107`: `color={kpis.errors > 0 ? palette.status.rejected
   : undefined}` — same `> 0` threshold pattern as the Users-tab/user-detail Errors
   cards). **Live-verified only the negative branch** (all visible "Private" rows have
   `errors: 0` — see § Preconditions / § Blocked Steps for the positive-branch gap,
   inherited from ELITEA-2320's identical blocker on the same project/range).
5. Verify a "Runs by Day" area chart is shown, conditional on `daily_usage.length > 0`
   (live-observed: chart renders with 1 day of data for `guardrails_test_agent`).
   — **Case-text drift**: case step 5 calls it a "Daily Usage" chart; live/source
   (`AnalyticsAgentDetailed.jsx:118`) titles it "Runs by Day". This AFS asserts the
   live title (filed #1199).
6. Verify a "Users" panel is shown below the chart, listing users who used this
   agent/pipeline, with column headers `User, Runs, Avg Latency, Errors` and a count
   subtitle `"{N} users used this agent / pipeline"` (live-observed for
   `guardrails_test_agent`: "1 users used this agent / pipeline" →
   `testbot@elitea.ai | 4 | 190ms | 0`).
   — **Case-text drift**: case step 6 lists columns `USER, EVENTS, AVG LATENCY,
   ERRORS`; live/source (`AnalyticsAgentDetailed.jsx:204-207`) is `User, Runs, Avg
   Latency, Errors` — second column is "Runs", not "Events" (same naming drift already
   documented for the Agent & Pipeline Activity table itself, elitea-testing-public#1195).
   This AFS asserts the live column set (filed #1199).
7. Verify a "Tools" panel is shown alongside the Users panel, listing tools used by
   this agent/pipeline, with column headers `Tool, Calls` and a count subtitle
   `"{N} tools used by this agent / pipeline"` (live-observed for
   `guardrails_test_agent`: "1 tools used by this agent / pipeline" →
   `get_issue | 4`).
   — **No drift** — case step 7 (`TOOL, CALLS` columns) matches live/source
   (`AnalyticsAgentDetailed.jsx:271-272`) exactly.
8. Switch to the pipeline row with zero tool usage (`autotest_test_empty_pipeline_exe...`,
   near the end of the table) and verify its Tools panel shows "No tool data" instead
   of a tool list (live-verified: subtitle "0 tools used by this agent / pipeline",
   table body renders the single-line text "No tool data" —
   `AnalyticsAgentDetailed.jsx:291-297`).
   — **No drift** — case step 8's exact wording matches live/source exactly.
9. Click the back arrow — verify the view returns to the Agent & Pipeline Activity
   table (live-verified: `analytics-agents-table-header` visible again,
   `analytics-agents-activity-title` / `analytics-agents-count` restored). No new
   network request fires on back (source: `handleBack` — `AnalyticsAgents.jsx:83` —
   just resets local `selectedAgent` state to `null`; live-confirmed via
   `browser_network_requests`: only the original tab-mount `analytics_agents` request
   and the one `analytics_agent_detail` request from step 1 appear before AND after
   the back click, no third request).
   — **No drift** — case step 9 matches live behaviour exactly (same same-page
   state-swap pattern as ELITEA-2313's Users-tab back navigation).

## Expected Results
- Clicking an agent/pipeline row swaps the Agent & Pipeline Activity table for the
  agent/pipeline detail view: entity-name title + back arrow, 8 KPI cards (Errors red
  only when > 0), a conditional "Runs by Day" chart, and two side-by-side summary
  panels (Users / Tools) — all render without console errors.
- The GET `.../analytics_agent_detail/prompt_lib/{project_id}?entity_id={id}&date_from=...&date_to=...`
  request resolves 200 and the view reflects its response (`entity_name`, `kpis`,
  `users`, `tools`, `daily_usage`).
- The Tools panel shows "No tool data" when the agent/pipeline used zero tools in the
  range (empty-state branch), and a populated `Tool | Calls` list otherwise.
- Clicking the back arrow returns to the Agent & Pipeline Activity table with no new
  network request (cached).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Analytics → Agents tab | Target page/section loads successfully | step 1 | reused from ELITEA-2310/2320's `navigate()` + `open_agents_pipelines_tab()` | asserted (transit, not this case's own observable — tab-name drift already filed under #1195, not re-filed here) |
| 2 Click on any agent name in the Agent Activity table | Control responds; expected next state is shown | step 1 | `step 1`: table panel replaced by detail view, network+spinner waits (reuses `open_agent_detail_by_row` from ELITEA-2320, which asserted only navigation success — this case asserts the resulting content) | asserted |
| 3 View transitions to agent detail page showing agent name as title with back arrow | Condition holds | step 2 | `step 2`: title text = entity name, back-arrow IconButton present | asserted |
| 4 Five KPI cards shown: Total Events, Unique Users, Avg Latency, Errors, Error Rate | Condition holds | step 3 | `step 3`: live 8-card set + order asserted instead | clarification *(case's 5-card list is stale — no "Error Rate" KPI exists, "Total Events" is really "Total Runs", and Total Cost/Total Tokens/Input Tokens/Output Tokens are omitted. Same stale-count family as ELITEA-2310/2312/2313/2320. Filed elitea-testing-public#1199)* |
| — Errors card red when > 0 (not in case's numbered steps, but implied by the Errors KPI existing) | Condition holds | step 4 | `step 4`: negative branch (errors=0 → default color) live-verified; positive branch source-confirmed only | asserted (negative branch only — see § Blocked Steps for the positive-branch gap) |
| 5 "Daily Usage" chart shown | Condition holds | step 5 | `step 5`: live title "Runs by Day" + conditional-render asserted instead | clarification *(case's "Daily Usage" is stale — live title is "Runs by Day". Filed #1199)* |
| 6 "Users" panel shown listing users with USER, EVENTS, AVG LATENCY, ERRORS columns | Condition holds | step 6 | `step 6`: live columns `User, Runs, Avg Latency, Errors` asserted instead | clarification *(case's "EVENTS" column is stale — live column is "Runs", same drift family as the Activity table's own Events→Runs drift, #1195. Filed #1199)* |
| 7 "Tools" panel shown listing tools with TOOL, CALLS columns | Condition holds | step 7 | `step 7`: live columns `Tool, Calls` asserted, matches case exactly | asserted *(no drift)* |
| 8 If no tools used, "No tool data" message shown | Action completes without error and produces expected UI state | step 8 | `step 8`: empty-state text asserted on a pipeline row with 0 tool usage, matches case exactly | asserted *(no drift)* |
| 9 Click back arrow — navigation returns to Agent Activity table | Control responds; expected next state is shown | step 9 | `step 9`: table panel handles restored, no new network request | asserted |

**Axis 2 — Analyst additions.**
- `step 3` asserts KPI card **order**, not just presence/count — *added: cheap once
  the per-card handle exists, mirrors ELITEA-2313's user-detail KPI-order assertion
  and ELITEA-2310/2312's tab/column-order assertions; catches a silent reorder
  regression.*
- `step 4` asserts the **negative** branch (non-Errors cards + errors=0 stay
  default-colored) explicitly, not just presence of the Errors card — *added: mirrors
  ELITEA-2313's user-detail Errors-color negative-branch addition; a card whose color
  logic accidentally fires unconditionally would pass a presence-only check while
  failing this.*
- `step 8`'s Tools-panel empty-state assertion is not in the case's Users-panel
  parallel (no analogous "0 users" check is requested) but is directly adjacent to
  "shows a count label and a list of items" for the Users panel too — *added, mirrors
  ELITEA-2313's precedent: proves the panel's zero-state renders correctly, not just
  the populated-state, using the same fixture pipeline already needed for the
  populated-Tools-panel assertion in step 7.*
- `step 9`'s "no new network request on back" assertion is not in the case text —
  *added: proves the RTK-Query cache is actually being reused (a regression here
  would silently re-fetch and could reset pagination/search state left in the Agents
  & Pipelines tab); cheap to assert via `page.expect_response` NOT firing within a
  short window, mirrors ELITEA-2313's identical addition for the Users tab.*

## Cleanup
None — read-only navigation into and out of the detail view (two round trips: one row
with tools, one without); no data created or mutated. If the test file shares a
`Page`/`AnalyticsPage` fixture with ELITEA-2320's test, ensure the detail view is
backed out of (click back arrow) before the fixture is reused by a later test, so no
test starts already inside a detail view.

## Concrete Handles (discovered during exploration)

**Provenance note:** `AnalyticsAgentDetailed.jsx` confirmed present on
`automation/testids` (dev server serves it, live-verified 2026-08-05); **zero
pre-existing testids** on the file (mirrors ELITEA-2313's finding for the parallel
`AnalyticsUserDetailed.jsx` and ELITEA-2320's finding for `AnalyticsAgents.jsx`). All
handles below need adding via `add-data-testid`; uniqueness to be re-verified by the
implementer against fresh `origin/main` at implementation time (naming follows the
`analytics-agent-detail-*` prefix, distinct from ELITEA-2313's `analytics-user-detail-*`
and ELITEA-2320's `analytics-agents-*` — same feature, different sub-view).

| Element | Recommended Locator | PROVENANCE | Notes |
|---|---|---|---|
| Back-arrow button | `LocatorDescriptor(testid="analytics-agent-detail-back-button")` | needs-adding | `AnalyticsAgentDetailed.jsx:53-58` — `<IconButton onClick={onBack}><ArrowBackIcon /></IconButton>`. Add directly (local `IconButton` usage, not a shared component's generic prop). |
| Title (agent/pipeline name) | `LocatorDescriptor(testid="analytics-agent-detail-title")` | needs-adding | `AnalyticsAgentDetailed.jsx:59-64` — `<Typography>{entity_name}</Typography>`. No known blank-title gap here (unlike ELITEA-2313's user-email finding) — `entity_name` is always populated for an agent/pipeline row (confirmed on both live rows exercised this run). |
| Loading spinner (this view) | `LocatorDescriptor(testid="analytics-agent-detail-loading-indicator")` | needs-adding | `AnalyticsAgentDetailed.jsx:27-32` — the `isFetching` early-return `CircularProgress`. Used for an absence assertion (wait `state="hidden"`) before asserting rendered content, mirroring `analytics-user-detail-loading-indicator`'s pattern. |
| KPI card (repeated, one per rendered card) | `LocatorDescriptor(testid="analytics-agent-detail-kpi-card")` | needs-adding | **Shared `KPICard.jsx` component** (also used by `AnalyticsOverview`, `AnalyticsCosts`, `AnalyticsUserDetailed`, `AnalyticsToolDetailed`, `UsageSummary` — per `.agents/testing.md` § Locator policy, shared components take a caller-supplied prop, never a hardcoded testid). This exact prop (`testId`) was already added to `KpiCard.jsx` for ELITEA-2313's `analytics-user-detail-kpi-card` — reuse the same prop, pass `testId="analytics-agent-detail-kpi-card"` on all 8 `<KPICard>` call sites inside `AnalyticsAgentDetailed.jsx` only. Do NOT touch the other call sites (scope discipline, `.agents/role-overrides.md`). Read each card's label via `.nth(i).inner_text().split("\n")[0]`. |
| KPI card value (repeated, one per rendered card) | `LocatorDescriptor(testid="analytics-agent-detail-kpi-value")` | needs-adding | Same `KpiCard.jsx`, reuse the `valueTestId` prop added for ELITEA-2313 (wired on the value `Typography` carrying the `color` prop — confirmed by that AFS's exploration that the outer card box does NOT carry the color, only the value Typography does). Pass `valueTestId="analytics-agent-detail-kpi-value"` on all 8 call sites. Read the Errors card's color via `to_have_css("color", "rgb(215, 22, 22)")` (positive branch, source-confirmed only — see § Blocked Steps) and the other 7 via the same check against the resolved default-text color (negative branch, live-verified). |
| Chart title | `LocatorDescriptor(testid="analytics-agent-detail-chart-title")` | needs-adding | `AnalyticsAgentDetailed.jsx:114-119` — `<Typography>Runs by Day</Typography>`, only rendered when `daily_usage.length > 0`. |
| Chart container | `LocatorDescriptor(testid="analytics-agent-detail-chart-container")` | needs-adding | `AnalyticsAgentDetailed.jsx:120-124` — the `Box sx={styles.chartWrapper}` wrapping `ResponsiveContainer`+`AreaChart`. Used for presence only in this case (no hover/tooltip assertion requested by the case text, unlike ELITEA-2313's user-detail chart which has a dedicated sibling case ELITEA-2329 for that depth) — Recharts SVG internals are the #579 third-party-widget exception, scoped to this testid parent, not exercised here. |
| Users panel | `LocatorDescriptor(testid="analytics-agent-detail-users-panel")` | needs-adding | `AnalyticsAgentDetailed.jsx:181-247` — the panel's outer `Box` (`styles.chartCard`, first one). Read via `.inner_text()`, split on `"\n"`: line 0 = "Users", line 1 = "{N} users used this agent / pipeline", remaining lines alternate name/runs/latency/errors per item (or "No runs recorded" when N=0 — not exercised this run, both fixture rows had ≥1 user) — same aggregate-text technique as ELITEA-2313's `get_panel_summary`. |
| Tools panel | `LocatorDescriptor(testid="analytics-agent-detail-tools-panel")` | needs-adding | `AnalyticsAgentDetailed.jsx:248-301` — same pattern, panel 2. Empty-state text is "No tool data" (exercised live on `autotest_test_empty_pipeline_exe...`), populated state is `Tool | Calls` rows (exercised live on `guardrails_test_agent` → `get_issue | 4`). |

**Reused from ELITEA-2320** (already on `main`/`automation/base`, no new work):
`AnalyticsPage.tab_agents_pipelines`, `open_agents_pipelines_tab()`,
`switch_project()`, `agents_rows` (to locate and click a row — full detail-sub-view
content was explicitly out-of-scope for ELITEA-2320's own spec, this case is the
first to exercise it), `open_agent_detail_by_row()` (navigation + response wait
only — this case adds the content assertions and the back-navigation helper),
`agents_table_header` / `agents_activity_title` / `agents_count` (to confirm the
back-navigation lands back on the same table).

**Reused from ELITEA-2313** (component-level prop plumbing, already on
`main`/`automation/base`): the `KpiCard.jsx` `testId`/`valueTestId` prop pair — this
case is a second call site for the same shared-component props, not new component
work.

Uniqueness check deferred to implementation time (per standard practice — the
analyst's naming follows the established `analytics-agent-detail-*` /
`analytics-agents-*` / `analytics-user-detail-*` prefix split, which is
prefix-disjoint from all other `analytics-*` testids catalogued in `_surface.md` and
`analytics_page.py`'s existing fields, so a collision is unlikely but implementer must
re-grep `origin/main` fresh before committing).

## Network Behavior
- `GET /api/v2/elitea_core/analytics_agent_detail/prompt_lib/{project_id}?entity_id={id}&date_from=...&date_to=...`
  — fires once when a row is clicked (`selectedAgent` set); confirmed live: 200 OK, no
  console errors, response shape `{ entity_name, kpis, users, tools, daily_usage }`
  (`AnalyticsAgentDetailed.jsx:22,46`). Live-observed `entity_id=7580` for
  `guardrails_test_agent`.
- No request fires on the back-arrow click (`handleBack` only resets local state) —
  confirmed via source AND live via `browser_network_requests` (request list identical
  before/after the back click); the Agents & Pipelines-tab table's own query
  (`analytics_agents/prompt_lib/`) is not re-triggered because it was never unmounted,
  only hidden.

## Known Defects Found During Exploration
- **[CLARIFICATION]** Case-text drift (not a product defect — reverse-masking guard
  applies), same stale-count family as ELITEA-2310/2312/2313/2320
  (elitea-testing-public#1185/#1188/#1191/#1195 are the sibling issues; filed as its
  own sibling **elitea-testing-public#1199** for this case, per the dedup rule —
  different object, the agent/pipeline detail view's KPI cards/chart title/Users
  columns, not the Users-detail view or the Activity table): case step 4 lists 5 KPI
  cards including a non-existent "Error Rate" KPI, omitting Total Cost/Total
  Tokens/Input Tokens/Output Tokens — live view has 8. Case step 5 says "Daily Usage"
  chart; live title is "Runs by Day". Case step 6 says Users-panel column "EVENTS";
  live column is "Runs". This AFS's steps 3, 5, and 6 assert the live contract. (Case
  step 1's "Agents tab" naming is the identical drift already covered by #1195 for
  ELITEA-2320 and is not re-filed here — see the clarification issue body.)

### Filed Defects
- **elitea-testing-public#1199** — case-text drift clarification (5 vs 8 KPI cards
  incl. non-existent "Error Rate", "Daily Usage" vs "Runs by Day" chart title, "Events"
  vs "Runs" Users-panel column) — labelled `question`, see § Known Defects above.

## Blocked Steps
- **Errors-KPI-card positive branch (`errors > 0` → red/rejected color)**: not
  live-exercisable in this analysis session — all 25 visible rows in the "Private"
  fixture project (default "Last 24h" range) have `errors: 0`, identical to
  ELITEA-2320's own blocked-step finding on the same project/range/table. The negative
  branch (`errors === 0` → default color) is live-verified and should be automated per
  step 4; the positive branch is source-confirmed only
  (`AnalyticsAgentDetailed.jsx:107`, identical rule shape to the Users-tab/user-detail
  Errors cards). If a future run of this suite's "Private" fixture project accumulates
  an agent/pipeline row with `errors > 0`, the implementer should fold the
  positive-branch assertion in at that point (same closure pattern as
  ELITEA-2320's/ELITEA-2312's, see those AFS's § Blocked Steps) — do not block merging
  this case on it.
- **Users-panel empty state ("No runs recorded")**: not live-exercisable — both fixture
  rows exercised this run (`guardrails_test_agent`, `autotest_test_empty_pipeline_exe...`)
  have ≥1 user in the range. Source-confirmed only (`AnalyticsAgentDetailed.jsx:237-244`).
  Not required by the case's own numbered steps (which only ask for the Tools-panel
  empty state, step 8) — left as a documented gap, not a blocker.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Extend `pages/analytics_page.py` (created by ELITEA-2310, extended by
  ELITEA-2312/2313/2320) with this case's `LocatorDescriptor` fields, rather than
  creating a second page object — same page, same URL, same class. Mirror the existing
  `# --- User detail view (ELITEA-2313) ---` section-comment convention with a new
  `# --- Agent/pipeline detail view (ELITEA-2321) ---` section.
- **Suggested new test file**: `automation/tests/ui/admin/test_analytics_agent_detail_view.py`
  (sibling to `test_analytics_user_detail_view.py` and
  `test_analytics_agents_pipelines_tab.py`, not an extension of either — this case's
  observable, the row-click → detail-view → back-arrow flow, was explicitly
  out-of-scope for ELITEA-2320's spec and shares zero assertions with it; a fresh file
  keeps the flows independently readable/runnable, same precedent as ELITEA-2313 vs
  ELITEA-2312). Implementer's call per `.agents/role-overrides.md` if a single file is
  preferred instead — no architectural reason blocks either.
- Wait strategy: reuse `AnalyticsPage.open_agent_detail_by_row()` (already waits on the
  `analytics_agent_detail/prompt_lib/...` GET response), then add a new
  `_wait_for_agent_detail_settled()` waiting on
  `analytics-agent-detail-loading-indicator` hidden (mirrors
  `_wait_for_user_detail_settled()`'s two-step pattern) before asserting content.
- KPI card assertions: use `.count()` on `analytics-agent-detail-kpi-card` for the
  8-card check, `.nth(i).inner_text().split("\n")[0]` for each label in order, and
  `analytics-agent-detail-kpi-value` + `to_have_css("color", ...)` for the Errors-card
  color branch (negative branch on all 8 cards' `.nth(i)` entries — positive branch is
  a documented gap, see § Blocked Steps).
- Panel assertions: reuse `AnalyticsPage.get_panel_summary(panel_locator)` (added for
  ELITEA-2313, generic over any `chartCard`-style panel) against both
  `analytics-agent-detail-users-panel` and `analytics-agent-detail-tools-panel`.
- Back-navigation assertion: mirror `AnalyticsPage.back_to_users_table()`'s shape as a
  new `back_to_agents_table()` — click `analytics-agent-detail-back-button`, assert
  `analytics-agents-table-header` visible again, and assert (via
  `page.expect_response` with a short timeout, expecting it NOT to fire) that no fresh
  `analytics_agents/prompt_lib/` request appears within e.g. 1500ms — the RTK-Query
  cache from the original tab-mount fetch is reused per source, same as
  ELITEA-2313's/ELITEA-2320's precedent.
- Two-row round trip: open the detail view on `guardrails_test_agent` (row 0, exercises
  the populated Tools panel + non-zero KPI values), back out, then open it again on the
  zero-tool-usage pipeline row (exercises the "No tool data" empty state) — both in one
  test, mirroring how this AFS's own exploration session covered both branches without
  needing a second fixture project.
