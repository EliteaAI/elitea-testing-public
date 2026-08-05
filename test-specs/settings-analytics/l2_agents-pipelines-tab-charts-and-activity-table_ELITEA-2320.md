# Test Case: Agents & Pipelines tab loads Most Active chart, Chat Messages chart, and Activity table

## Metadata
- **TMS ID**: ELITEA-2320
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost — no manual login)
- **Analyst**: qa-engineer (analyst slot), batch `elitea-2320`
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (`auth_state` fixture — localhost skips login via `VITE_DEV_TOKEN`).
- A project is selected with at least one agent/pipeline having usage-analytics data in the active
  date range, so `agentChartData.length > 0` and `chat_daily.length > 0` (both charts are
  conditionally rendered — see § Coverage Map / § Known Defects). Confirmed live: the `auth_state`
  fixture's default project **"Private"** (id `399`, same project ELITEA-2312/2313 use) has 25
  agents/pipelines with runs and non-zero `chat_daily` in the default "Last 24h" range — no seeding
  required. **Do not use "UI Testing" (id `400`)** for this case's chart-presence steps — it has
  zero agent/pipeline activity in the default range, so both charts are absent by design (see
  Coverage Map row for the conditional-render finding); "UI Testing" is still useful as a
  *negative*-case fixture (0-activity state, and the "Users" column becomes visible there — see
  below).

## Test Data
### reuse-existing
- No test data required — read-only assertions against the `auth_state` fixture's existing
  "Private" project analytics data (25 agents/pipelines, live 2026-08-05). Exact row values are not
  asserted as fixed numbers; only structural/format contracts (column set, subtitle pattern, chart
  presence) are asserted, mirroring ELITEA-2312's approach.

## Test Steps
1. Navigate to Settings → Analytics, then click the "Agents & Pipelines" tab (reuse
   `AnalyticsPage.tab_agents_pipelines`, `analytics-tab-agents-pipelines`, already on `main` from
   ELITEA-2310).
   - **Verify**: the tab becomes selected (`aria-selected="true"`) and its panel renders without
     console error.
   - **Case-text drift** (see § Known Defects, filed elitea-testing-public#1195): the case's step 1
     calls this the "Agents tab" — the live/source tab label is **"Agents & Pipelines"** (same
     family-wide drift already documented in elitea-testing-public#1185).
2. Verify the "Most Active Agents & Pipelines" bar chart is shown (only when `agentChartData.length
   > 0`, true for the "Private" fixture) with subtitle `"Top {N} by runs"` (N = min(20, number of
   distinct agents/pipelines with activity) and agent/pipeline names on the X axis.
   - **Case-text drift**: case says `"Most Active Agents"` bar chart / subtitle `"Top N by events"` /
     "agent names on X axis". Live: title is **"Most Active Agents & Pipelines"**, subtitle is
     **"Top {N} by runs"** (`dataKey="runs"`, not events), and the X axis shows a MIX of agent AND
     pipeline names (confirmed live: `guardrails_test_agent` alongside
     `autotest_hitl_test_hitl_node_run`, a pipeline). This AFS asserts the live contract.
3. Verify the "Chat Messages" area chart is shown (only when `chat_daily.length > 0`, true for the
   "Private" fixture) with subtitle "User messages per day".
   - **No drift** — case text matches live/source exactly for this chart's title and subtitle.
4. Verify the "Agent & Pipeline Activity" table is shown with a subtitle reading `"{N} agents &
   pipelines"` where N is a non-negative integer matching the actual row/entity total (live
   observed: "25 agents & pipelines" in "Private").
   - **Case-text drift**: case says `"Agent Activity"` table / example subtitle `"2 agents"`. Live:
     title is **"Agent & Pipeline Activity"**, subtitle format is **"{N} agents & pipelines"**.
5. Verify the table header row shows these columns, in this order:
   - **Personal project** (the `auth_state` fixture's "Private", confirmed personal via
     `isPersonalProject`): `Agent / Pipeline, Runs, Cost, Total Tokens, Input Tokens, Output Tokens,
     Avg Latency, Errors` — **8 columns**, "Users" is conditionally absent.
   - **Non-personal project** (confirmed live against "UI Testing"): the same 8 plus **Users**
     inserted right after `Runs` — **9 columns total**.
   - **Case-text drift**: case step 5 lists 5 columns (`AGENT, EVENTS, USERS, AVG LATENCY, ERRORS`)
     and implies a fixed column set. Live: up to 9 columns as above, no "Events" column exists (the
     equivalent is named "Runs"), and "Users" is conditionally rendered per project type, not
     always present. This AFS asserts the live 8-column set against the fixture's actual (personal)
     project.
6. Verify each row is clickable and opens a same-page "agent/pipeline detail" sub-view (mirrors the
   Users-tab → user-detail same-page state-swap pattern established in ELITEA-2313 — no URL change,
   `GET .../analytics_agent_detail/prompt_lib/{project_id}?entity_id={id}&...` fires once, resolves
   200).
   - **Case-text nuance, not a defect**: case step 6 says "agent names in the table are clickable
     links" — live, the entire row (not specifically the name text) is the click target
     (`onClick={() => handleAgentClick(a.entity_id)}` on the row `Box`, not an `<a>` element). This
     functionally satisfies "clickable" and matches the established row-click convention elsewhere
     on this surface (ELITEA-2313); not flagged as a defect. Full detail-sub-view content
     (KPI cards, "Runs by Day" chart, Users/Tools breakdown tables) is OUT OF SCOPE for this case —
     only presence + click-navigates is asserted here, same scoping precedent as ELITEA-2312's
     row → ELITEA-2313's detail view split.
7. Verify a "Search by agent or pipeline name" input is present, positioned in the top-right of the
   Agent & Pipeline Activity card (same row as the title/count).
   - **Case-text drift**: case says `"Search by agent name"`. Live placeholder is **"Search by
     agent or pipeline name"**.

## Expected Results
- Agents & Pipelines tab loads its panel: bar chart, area chart, "Agent & Pipeline Activity"
  table (header + rows + pagination), and search input — all render without console errors.
- `GET .../elitea_core/analytics_agents/prompt_lib/{project_id}?date_from=...&date_to=...&limit=...&offset=...&sort_by=events&sort_order=desc`
  resolves 200 and the chart(s)/table reflect its response (`rows`, `chat_daily`, `total`).
- Column set matches the live/source 8-column (personal project) or 9-column (non-personal project)
  contract — never the case's stale 5-column list.
- Clicking any row navigates (same-page state swap, no URL change) to the agent/pipeline detail
  sub-view; `GET .../analytics_agent_detail/prompt_lib/{project_id}?entity_id=...` fires once,
  resolves 200, no console errors.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Analytics → Agents tab | Target page/section loads successfully | step 1 | `step 1`: tab selected + panel renders | asserted |
| 2 "Chat Messages" area chart shown, subtitle "User messages per day" | Condition holds | step 3 | `step 3`: title + subtitle text, chart container presence | asserted |
| 3 "Most Active Agents" bar chart shown, subtitle "Top N by events", agent names on X axis | Condition holds | step 2 | `step 2`: live title/subtitle/X-axis asserted instead | clarification *(title is "Most Active Agents & Pipelines", subtitle is "Top N by runs" not "by events", X axis mixes agent AND pipeline names — filed elitea-testing-public#1195)* |
| 4 "Agent Activity" table shown, subtitle "2 agents" (example) | Condition holds | step 4 | `step 4`: live title "Agent & Pipeline Activity" + "{N} agents & pipelines" format asserted instead | clarification *(#1195)* |
| 5 Table has columns AGENT, EVENTS, USERS, AVG LATENCY, ERRORS | Condition holds | step 5 | `step 5`: live 8-column (personal project) / 9-column (non-personal, adds Users) set asserted instead | clarification *(no "Events" column exists — real name is "Runs"; "Users" is conditional on project type, not universal; 3 more columns exist (Cost/Total/Input/Output Tokens) the case never mentions — filed #1195)* |
| 6 Agent names in the table are clickable links | Condition holds | step 6 | `step 6`: whole-row click → same-page detail sub-view, live-verified (network + no-console-error) | asserted *(functionally satisfied; "links" phrasing is a row-level onClick, not an `<a>` — not a defect, matches ELITEA-2313's established pattern, noted not filed)* |
| 7 "Search by agent name" input present | Condition holds | step 7 | `step 7`: input present, placeholder text asserted | clarification *(live placeholder is "Search by agent or pipeline name" — #1195)* |

**Axis 2 — Analyst additions.**
- `step 1` asserts `aria-selected="true"` on the tab (beyond the case's bare "loads successfully")
  — *added: cheap, catches a tab-switch regression using the same handle ELITEA-2310 already
  established (`is_tab_selected`).*
- `step 2`/`step 3` assert the charts are conditionally rendered (`agentChartData.length > 0` /
  `chat_daily.length > 0`) — *added: the case's steps assume the charts are unconditionally present;
  live exploration against "UI Testing" (0 activity) showed BOTH charts absent while the table still
  renders (with "0 agents & pipelines"). This is a genuine product behaviour worth locking down, not
  a defect — added as a documented precondition (see § Preconditions) rather than a case step, since
  the case's own numbered steps assume active data.*
- `step 5` asserts the exact column **order**, not just presence — *added: order is part of the
  visible UI contract and free to assert once the header handle is captured (mirrors
  ELITEA-2310/2312's tab/column order assertions).*
- `step 5` also asserts the Users-column conditional visibility across BOTH project types (personal
  vs non-personal) — *added: this is a genuine structural branch in the source
  (`!isPersonalProject &&`) that the case's flat 5-column list doesn't anticipate at all; cheap to
  assert with a project switch already needed to exercise the non-empty "UI Testing" negative case.*
- `step 6` asserts the underlying `analytics_agent_detail` network call resolves 200 with no console
  errors — *added: proves the click actually functions end-to-end, not merely that the row looks
  clickable (cursor: pointer); a present-but-broken click handler would otherwise pass a
  presence-only check.*
- **Errors-column color rule** (not in the case's numbered steps, but directly adjacent to step 5's
  column-presence check and free to verify with the same handle, mirroring ELITEA-2312's Users-tab
  precedent): `AnalyticsAgents.jsx:317`, `color: a.errors > 0 ? palette.status.rejected : undefined`
  — *added: same red-only-when-nonzero rule as the Users tab; all 20 visible "Private" rows have
  `errors: 0` in the default range (negative branch only, live-confirmed default/white color) — see
  § Blocked Steps for the positive-branch gap.*

## Cleanup
None — read-only page load, tab click, and one row-click/back-navigation round trip; no data created
or mutated.

## Concrete Handles (discovered during exploration)

**Provenance note:** `AnalyticsAgents.jsx` confirmed present on `automation/testids` (dev server
serves it); **zero pre-existing testids** anywhere in the file (`git grep -c "data-testid\|testId"`
→ 0). All handles below need adding via `add-data-testid`. The shared `SearchInput.jsx` component
**already accepts a `testId` prop** (added during ELITEA-2312's implementation,
`EliteaAI/EliteaUI@c7f6b326` era) — wiring the search input here is a call-site-only change, not a
new component prop.

| Element | Recommended Locator | PROVENANCE | Notes |
|---|---|---|---|
| Bar chart title | `LocatorDescriptor(testid="analytics-agents-chart-title")` | needs-adding | `AnalyticsAgents.jsx:108` — static `<Typography variant="labelMedium">Most Active Agents & Pipelines</Typography>`, only rendered when `agentChartData.length > 0` |
| Bar chart subtitle | `LocatorDescriptor(testid="analytics-agents-chart-subtitle")` | needs-adding | `AnalyticsAgents.jsx:115` — dynamic `Top {agentChartData.length} by runs`; read via `.text_content()`, regex `r"^Top (\d+) by runs$"` |
| Bar chart container | `LocatorDescriptor(testid="analytics-agents-chart-container")` | needs-adding | `AnalyticsAgents.jsx:124`, the `Box sx={styles.chartWrapper}` wrapping `ResponsiveContainer`+`BarChart` — used for presence only (Recharts SVG internals are out of scope, no #579 exception needed since only presence is asserted) |
| Chat Messages chart title | `LocatorDescriptor(testid="analytics-agents-chat-chart-title")` | needs-adding | `AnalyticsAgents.jsx:174` — static, only rendered when `chat_daily.length > 0` |
| Chat Messages chart subtitle | `LocatorDescriptor(testid="analytics-agents-chat-chart-subtitle")` | needs-adding | `AnalyticsAgents.jsx:181` — static "User messages per day" (no drift, but still needs its own testid — distinct `Typography` node from the bar chart's) |
| Chat Messages chart container | `LocatorDescriptor(testid="analytics-agents-chat-chart-container")` | needs-adding | `AnalyticsAgents.jsx:190`, second `Box sx={styles.chartWrapper}` (chartWrapper style is reused per-chart, testid must be per-instance — two separate `Box` elements at lines 124 and 190) |
| "Agent & Pipeline Activity" title | `LocatorDescriptor(testid="analytics-agents-activity-title")` | needs-adding | `AnalyticsAgents.jsx:239` — static |
| Agents count subtitle | `LocatorDescriptor(testid="analytics-agents-count")` | needs-adding | `AnalyticsAgents.jsx:246` — dynamic `{total} agents & pipelines`; regex `r"^(\d+) agents & pipelines$"` |
| "Search by agent or pipeline name" input | `LocatorDescriptor(testid="analytics-agents-search-input")` | needs-adding (call-site only) | `AnalyticsAgents.jsx:255-260` — add `testId="analytics-agents-search-input"` to the existing `<StyledSearchInput ...>` call; the shared component already wires `testId` → `inputProps={{'data-testid': testId}}` (confirmed `src/components/SearchInput.jsx:8,20`), no component-code change needed |
| Table header row | `LocatorDescriptor(testid="analytics-agents-table-header")` | needs-adding | `AnalyticsAgents.jsx:264`, the `Box sx={styles.tableHeader}` wrapping all header `Typography` cells; read via `.inner_text()` split on `"\n"` (mirrors `AnalyticsPage.get_users_table_column_labels()`'s technique) — column count/order varies by `isPersonalProject` (8 vs 9), assert against the fixture's actual project type, not a hardcoded count |
| Table data row (repeated, one per rendered agent/pipeline) | `LocatorDescriptor(testid="analytics-agents-row")` | needs-adding | `AnalyticsAgents.jsx:282-286`, the clickable row `Box` (`key={i}`, `onClick={() => handleAgentClick(a.entity_id)}`); **same testid on every row** (list pattern, mirrors `analytics-users-row`) — select via `.nth(i)` |
| Errors cell (repeated, one per row) | `LocatorDescriptor(testid="analytics-agents-row-errors")` | needs-adding | `AnalyticsAgents.jsx:312-319`, the Errors `Typography` (`color: a.errors > 0 ? palette.status.rejected : undefined`); same repeated-testid + `.nth(i)` pattern as `analytics-users-row-errors`, add the testid on this specific `Typography` (not a positional child selector) |
| Table loading indicator | `LocatorDescriptor(testid="analytics-agents-loading-indicator")` | needs-adding | `AnalyticsAgents.jsx:276`, `Box sx={styles.loadingState}` shown while `isFetching` — mirrors `analytics-users-loading-indicator`'s response-vs-render-gap wait pattern |
| Rows-per-page selector | `LocatorDescriptor(testid="analytics-agents-pagination-rows-select")` | needs-adding | `AnalyticsAgents.jsx:325-333` `<TablePagination>` — wire via `slotProps={{ select: { 'data-testid': 'analytics-agents-pagination-rows-select' } }}`, same non-deprecated MUI v7 pattern as `analytics-users-pagination-rows-select` |
| Page-range label | `LocatorDescriptor(testid="analytics-agents-pagination-range")` | needs-adding | Same `<TablePagination>` — `slotProps={{ displayedRows: {...} }}` |
| Previous-page button | `LocatorDescriptor(testid="analytics-agents-pagination-prev")` | needs-adding | Same `<TablePagination>` — `slotProps={{ actions: { previousButton: {...} } }}` |
| Next-page button | `LocatorDescriptor(testid="analytics-agents-pagination-next")` | needs-adding | Same `<TablePagination>` — `slotProps={{ actions: { nextButton: {...} } }}` |

**Reused from ELITEA-2310** (already on `main`, no new work): `AnalyticsPage.tab_agents_pipelines`
(`analytics-tab-agents-pipelines`) to navigate to the tab, `is_tab_selected()` to confirm selection.

Uniqueness verified (2026-08-05, live `git grep` against `origin/main` — see below): all 15 new
testids above are net-new, none collide with the Users-tab (`analytics-users-*`) or User-detail
(`analytics-user-detail-*`) namespaces already on `main`.

```bash
cd ../EliteaUI && git fetch origin
for t in analytics-agents-chart-title analytics-agents-chart-subtitle analytics-agents-chart-container \
         analytics-agents-chat-chart-title analytics-agents-chat-chart-subtitle analytics-agents-chat-chart-container \
         analytics-agents-activity-title analytics-agents-count analytics-agents-search-input \
         analytics-agents-table-header analytics-agents-row analytics-agents-row-errors \
         analytics-agents-loading-indicator analytics-agents-pagination-rows-select \
         analytics-agents-pagination-range analytics-agents-pagination-prev analytics-agents-pagination-next; do
  git grep -- "$t" origin/main -- src/ && echo "COLLISION: $t"
done
# (expected: zero output — none of the 16 testids exist on main yet)
```

## Network Behavior
- `GET /api/v2/elitea_core/analytics_agents/prompt_lib/{project_id}?date_from=...&date_to=...&limit=20&offset=0&search=&sort_by=events&sort_order=desc`
  — fires on Agents-tab mount and again on every `search` keystroke change (same live pattern as
  the Users tab's `analytics_users` endpoint); confirmed live: 200 OK, no console errors, in
  "Private" (25 rows) and "UI Testing" (0 rows) alike.
- `GET /api/v2/elitea_core/analytics_agent_detail/prompt_lib/{project_id}?entity_id={id}&date_from=...&date_to=...`
  — fires once when a row is clicked; confirmed live: 200 OK, no console errors, `entity_id=7580`
  observed for `guardrails_test_agent`.

## Known Defects Found During Exploration
- **[CLARIFICATION]** Case text drift (not a product defect — reverse-masking guard applies), same
  stale-case-text family as elitea-testing-public#1185/#1188/#1191/#1192: tab name ("Agents" vs live
  "Agents & Pipelines"), bar-chart title/subtitle ("Most Active Agents"/"Top N by events" vs live
  "Most Active Agents & Pipelines"/"Top N by runs"), table title/subtitle ("Agent Activity"/"2
  agents" example vs live "Agent & Pipeline Activity"/"{N} agents & pipelines"), column list (case's
  5 columns AGENT/EVENTS/USERS/AVG LATENCY/ERRORS vs live 8–9 columns with no "Events" column and a
  conditionally-visible "Users" column), and search placeholder ("Search by agent name" vs live
  "Search by agent or pipeline name"). Filed: **elitea-testing-public#1195**. This AFS's steps
  assert the live/source-confirmed contract throughout, not the case's stale text.

## Blocked Steps
- **Errors-column positive branch (`errors > 0` → red/rejected color)**: not live-exercisable in
  this analysis session — all 20 visible rows in the "Private" fixture project (default "Last 24h"
  range) have `errors: 0`. Unlike ELITEA-2312's Users tab (where the "Private" project's *users*
  table has known `errors > 0` rows — `User 6250`: 78, `testbot@elitea.ai`: 75), the *agent/pipeline*
  Activity table's rows in this same project/range are all error-free at analysis time. The negative
  branch (`errors === 0` → default color) is live-verified and should be automated per step 5's
  Axis-2 addition; the positive branch is source-confirmed only
  (`AnalyticsAgents.jsx:317`, identical rule shape to the Users tab's). If a future run of this
  suite's "Private" fixture project accumulates an agent/pipeline row with `errors > 0` (e.g. via a
  failing toolkit call in an automated test), the implementer should fold the positive-branch
  assertion in at that point (same closure pattern as ELITEA-2312's, see that AFS's § Blocked
  Steps) — do not block merging this case on it.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Extend `pages/analytics_page.py` (created by ELITEA-2310, extended by ELITEA-2312/2313) with the
  Agents-tab-specific `LocatorDescriptor` fields above — same page, same URL, same class.
- Reuse `AnalyticsPage.navigate()` + `AnalyticsPage.tab_agents_pipelines` + `is_tab_selected()` from
  ELITEA-2310 to reach and confirm the tab.
- Wait strategy: wait for the `analytics_agents/prompt_lib/...` GET response
  (`page.expect_response` matching URL substring `/elitea_core/analytics_agents/prompt_lib/`)
  before asserting chart/table content — add a new URL-substring constant
  (`ANALYTICS_AGENTS_QUERY_URL_SUBSTRING = "/elitea_core/analytics_agents/prompt_lib/"`), distinct
  from the Overview and Users endpoints (mirrors the existing per-endpoint-constant convention in
  `analytics_page.py`).
- Column-header assertion: split `analytics-agents-table-header`'s `.inner_text()` on `"\n"`.
  **Apply the same uppercase-CSS gotcha ELITEA-2312's implementer found** (`tableCell`'s `sx`
  applies `text-transform: uppercase` via the SAME shared `tableCell` style object pattern) — verify
  the actual rendered case (uppercase vs title-case) live at implementation time before hardcoding
  the expected tuple; do not assume the JSX source's literal string casing carries through.
- Project-type branch for step 5: use the existing project-switch mechanism (`select-option-399` for
  "Private"/personal, `select-option-400` for "UI Testing"/non-personal — MUI Select auto-generated
  option testids, no dedicated testid on the option itself, confirmed in the settings-analytics
  `_surface.md` digest) to exercise both the 8-column and 9-column header shapes in one test.
- Chart-presence conditional (step 2/3's Axis-2 addition): the "UI Testing" project (id 400) has
  zero agent/pipeline analytics rows in the default "Last 24h" range — use it as the negative
  fixture (both charts absent, table shows "0 agents & pipelines", header still renders with 0
  rows) rather than seeding an artificial empty state.
- Row-click wait strategy (step 6): mirror `AnalyticsPage.open_user_detail_by_row()`'s
  `expect_response` + loading-indicator-hidden pattern exactly — wrap the row click in
  `page.expect_response` against the new `ANALYTICS_AGENT_DETAIL_QUERY_URL_SUBSTRING =
  "/elitea_core/analytics_agent_detail/prompt_lib/"` constant, then wait for the detail view's own
  loading indicator (needs a new testid, e.g. `analytics-agent-detail-loading-indicator`, if the
  implementer chooses to build out return-to-table navigation too — out of scope for this case's
  own assertions, which stop at "click navigates, no error", but worth flagging since a "back"
  button will exist in the detail sub-view mirroring `analytics-user-detail-back-button`).
