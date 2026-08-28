# Test Case: Health tab displays Requests vs Errors chart and Health by Event Type table

## Metadata
- **TMS ID**: ELITEA-2324
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost)
- **Analyst**: qa-engineer, batch `settings-w06` (cluster ELITEA-2311/2322/2323/2324/2325)
- **Status**: ready-for-automation
- **Case-text drift filed**: elitea-testing-public#1949 (the event-type rows are data-driven, not
  the fixed six the case lists)

## Preconditions
- User is authenticated (`auth_state` fixture); a project is selected.
- The selected project has **activity in the chosen range**. With an empty `health` array the whole
  tab renders the empty state `"No health data available."` instead of the chart and the table
  (`AnalyticsHealth.jsx` early return). The test drives `Last 30d` and asserts the precondition
  explicitly off the captured response, so an empty project fails with a clear message rather than
  a locator timeout.

## Test Data
### reuse-existing
Whatever the selected project already has. Live 2026-08-28, project "Elitea Testing Team",
`Last 30d`: 5 health rows (`llm, api, tool, socketio, rpc`), one of them (`api`) with
`errors = 947 > 0`, so **both** branches of the errors-colour rule are live-exercisable in this
case — unlike the Tools/Agents tabs.

## Test Steps

1. Navigate to Settings -> Analytics, click `Last 30d`, then open the **Health** tab
   (`analytics-tab-health`) — case step 1 — **capturing the `analytics/prompt_lib/` response body**
   as the oracle. (Health shares the Overview endpoint: `needsOverview = activeTab === 0 || 6`.)
   - **Verify**: the tab is selected (`aria-selected="true"`), the response is 200 and its `health`
     array is non-empty (precondition guard), and the page loading indicator
     (`analytics-loading-indicator`) has settled to count 0.
2. Verify the dual-series area chart (case step 2).
   - **Verify**: `analytics-health-chart-title` text is `Requests vs Errors`; the subtitle
     (`analytics-health-chart-subtitle`) is `Total requests trend with error overlay`.
   - **Verify**: `analytics-health-chart-container` is visible and contains exactly **two** rendered
     area series.
   - **Verify (series identity — the case's actual words)**: hover the chart container; the recharts
     tooltip (`analytics-health-chart-tooltip`) lists both series by name — a line containing
     `Total Requests` and a line containing `Errors` — plus the hovered date. Live text:
     `2026-08-13 | Total Requests: 129 | Errors: 0`.
3. Verify the Health by Event Type table is shown (case step 3).
   - **Verify**: `analytics-health-table-title` text is `Health by Event Type` and
     `analytics-health-table-header` is visible.
4. Verify the event-type rows (case step 4) — as a **membership + oracle** assertion, not a fixed
   list (see #1949).
   - **Verify**: the rendered event-type cells (`analytics-health-row-event-type`), in order, equal
     `[h["event_type"] for h in response["health"]]`.
   - **Verify**: every rendered event type is a member of the known set
     `{api, socketio, llm, tool, agent, rpc}` — the set the case enumerates and the same set the
     Guide tab documents — so an unexpected/garbage event type still fails the test.
   - **Verify**: at least one row is rendered.
5. Verify the table columns (case step 5, Expected Final State).
   - **Verify**: the `analytics-health-table-header-cell` cells, in order, have DOM text
     (`text_content()`, NOT `inner_text()`) `["Event Type", "Total", "Errors", "Error Rate",
     "Avg Latency"]`, and each cell's computed `text-transform` is `uppercase` (the case writes them
     capitalised; the DOM text is as above and the visual casing comes from CSS —
     `styles.tableCell.textTransform`).
6. No console errors throughout (`utils/console_errors.collect_console_errors`).

## Expected Results
- The Health tab renders a two-series area chart titled `Requests vs Errors` whose series are named
  `Total Requests` and `Errors`, plus a `Health by Event Type` table with the five columns above and
  one row per event type present in the analytics response.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Analytics -> Health tab | Page/section loads | step 1 | tab selected, 200 response, `health` non-empty, spinner settled | asserted |
| 2 Dual-series area chart with Total Requests and Errors series | Condition holds | step 2 | title + subtitle text, exactly 2 area series, tooltip naming both series | asserted |
| 3 Health by Event Type table is shown | Condition holds | step 3 | table title text + header visible | asserted |
| 4 Rows listed: api, socketio, llm, tool, agent, rpc | Condition holds | step 4 | rendered event types == response `health` order; every one a member of the known set; ≥1 row | **clarification** — the row set is data-driven; live shows 5 rows and **no `agent`** in a range where agent runs are 0 (#1949). Asserting the fixed six would be a false expectation. |
| 5 / Expected Final State — columns: Event Type, Total, Errors, Error Rate, Avg Latency | Condition holds | step 5 | header cell tuple + `text-transform` | asserted |

**Axis 2 — Analyst additions.**
- **Chart-series identity via the hover tooltip** (step 2) — *added: the case names two series but
  the chart renders **no legend**, so the series names exist in the DOM only inside the tooltip.
  Without the hover, "dual-series with Total Requests and Errors" would degrade to "two coloured
  paths", which would still pass if the series were swapped or renamed. Live-verified to work.*
- **Row set vs the response `health` array** (step 4) — *added: the response is the oracle; this
  turns an unsatisfiable fixed-list assertion into one that proves the UI rendered exactly what the
  backend returned (`.agents/testing.md` § Fidelity policy).*
- **Membership in the known event-type set** (step 4) — *added: keeps the case's intent (only these
  six event types are legitimate) enforceable even though their presence is data-dependent.*
- **Console-error check** (step 6) — *standing project convention.*

Deliberately **not** added: the errors-cell red-colour assertion (`errors > 0`). The Health tab does
carry the same rule (`AnalyticsHealth.jsx` — `color: h.errors > 0 ? palette.status.rejected :
undefined`, plus an `error_rate > 5` variant) and live data would exercise it (`api`: 947 errors,
`rgb(215, 22, 22)`), but this case never asks for it and adding it would require two more testids on
elements the case's own steps never touch (`.agents/testing.md` § Locator policy — scope is
load-bearing; canon #511). Recorded here as a **coverage observation for a future case**, not as
silent scope creep.

## Cleanup
None — read-only.

## Concrete Handles (discovered during exploration)

`AnalyticsHealth.jsx` currently has **ZERO testids** — every handle below except the tab, the preset
and the shared page spinner is new work.

| Element | Locator | PROVENANCE |
|---|---|---|
| Health tab | `analytics-tab-health` | on-main ✓ |
| `Last 30d` preset | `analytics-date-preset-30` | on-main ✓ |
| Page loading spinner | `analytics-loading-indicator` | on-main ✓ |
| Chart title (`Requests vs Errors`) | **testid needed: `analytics-health-chart-title`** | needs-adding |
| Chart subtitle | **testid needed: `analytics-health-chart-subtitle`** | needs-adding |
| Chart container | **testid needed: `analytics-health-chart-container`** | needs-adding — on the `styles.chartWrapper` `<Box>` wrapping the `ResponsiveContainer` |
| Chart hover tooltip | **testid needed: `analytics-health-chart-tooltip`** | needs-adding — **call-site only**: `components/ChartTooltip.jsx` already accepts a `testId` prop (added for ELITEA-2313). Recharts injects `active`/`payload`/`label` at render time, so pass it via the render-prop form already used elsewhere: `content={<ChartTooltip testId="analytics-health-chart-tooltip" />}` |
| Table title (`Health by Event Type`) | **testid needed: `analytics-health-table-title`** | needs-adding |
| Table header row | **testid needed: `analytics-health-table-header`** | needs-adding — on the `styles.tableHeader` `<Box>` |
| Table header CELL (repeated ×5) | **testid needed: `analytics-health-table-header-cell`** | **added during ELITEA-2324 fix round 1** (EliteaAI/EliteaUI@1a1fa5f4) — on each of the five `<Typography sx={[styles.tableCell, …]}>` header cells. Needed because step 5 asserts each column's **DOM text** (title case) separately from the CSS `text-transform` that renders it uppercase; the parent header row only yields the concatenated/CSS-rendered string. |
| Table row (repeated) | **testid needed: `analytics-health-row`** | needs-adding — on the `health.map()` row `<Box>`, mirroring `analytics-users-row` |
| Row event-type cell (repeated) | **testid needed: `analytics-health-row-event-type`** | needs-adding — on the `<Typography variant="bodySmall">{h.event_type}</Typography>` inside the first cell (the cell `<Box>` also holds the colour dot, so the testid goes on the text node to keep the assertion clean) |

**Implementer notes on the testid work.**
- All additions are plain attributes on nodes that already exist — **no new DOM node, no new hook,
  no replaced MUI built-in** (`add-data-testid` § Step 5.5). `AnalyticsHealth.jsx` is
  feature-scoped, not shared, so the `analytics-health-*` naming is correct at the definition site.
- The two `.recharts-area` series paths are library-internal render nodes; count them as **scoped
  raw handles inside the `analytics-health-chart-container` testid parent**
  (`.agents/testing.md` § Locator policy, #579 exception 1), declared in the `AnalyticsPage` method
  docstring — same treatment the date-picker popper methods already document.
- Hover with a real `Locator.hover()` on the chart container (verified live). Never dispatch a
  synthetic `mouseover` via `page.evaluate` — that is exploration-only.
- Page object: extend `automation/pages/analytics_page.py` with class-level `LocatorDescriptor`
  fields and an `open_health_tab()` / settle pair mirroring `open_users_tab()`. The Health tab reuses
  the Overview endpoint predicate `_is_analytics_query_response`, which already exists.

## Fidelity Declaration
No substitutions. The chart, tooltip and table are all rendered by the live product from the live
`analytics/prompt_lib/` response, which the test captures and uses as its oracle
(`.agents/testing.md` § Fidelity policy). No `page.route`, no `route.fulfill`, no injected state,
no synthetic events.

## Network Behavior
- `GET /api/v2/elitea_core/analytics/prompt_lib/{project_id}?date_from=...&date_to=...` — the same
  endpoint the Overview tab uses; `needsOverview` covers Overview **and** Health, so switching to
  Health does not necessarily fire a new request when the range is unchanged (RTK-Query cache hit).
  Capture the response around the **preset click**, then open the tab — the pattern the merged
  ELITEA-2317/2318 specs use.
- 200 OK, no console errors. Wait on the response or the settled spinner, never on `networkidle`
  (#1847).

## Blocked Steps
None. (The case's `agent` row is absent in live data, but that is case-text drift — #1949 — handled
by the membership assertion, not a blocker.)

## Known Defects
None found on this tab. #1949 is a case-text clarification, not a product defect.

## Live Observations (2026-08-28, project "Elitea Testing Team", `Last 30d`)

Chart: title `Requests vs Errors`, subtitle `Total requests trend with error overlay`, 2 area series
(stroke `#29B8F5` = `palette.status.draft` for `Total Requests`, `#D71616` =
`palette.status.rejected` for `Errors`). Hover tooltip: `2026-08-13 | Total Requests: 129 |
Errors: 0`.

Table `Health by Event Type` — header `Event Type | Total | Errors | Error Rate | Avg Latency`:

| Event Type | Total | Errors | Error Rate | Avg Latency |
|---|---|---|---|---|
| llm | 218 | 0 | 0% | 5.0s |
| api | 32.5K | 947 *(red `rgb(215, 22, 22)`)* | 2.92% | 129ms |
| tool | 4 | 0 | 0% | 241ms |
| socketio | 1.2K | 0 | 0% | 128ms |
| rpc | 225 | 0 | 0% | 185ms |

Five rows, no `agent` row (agent runs are 0 in this range). Zero console errors.


## Implementation notes (ELITEA-2324, 2026-08-28 — implementer)

- **Shipped as** `automation/tests/ui/admin/test_analytics_health_tab.py`
  (`TestAnalyticsHealthTab::test_health_tab_chart_and_event_type_table`). All 8 testids added as
  specced — EliteaAI/EliteaUI@bc50bd9d.
- **Confirmed:** opening the Health tab on an unchanged range fires NO request (RTK-Query cache
  hit), exactly as the AFS predicted — `open_health_tab()` therefore waits on rendered content and
  the oracle body is captured around the preset click.
- **Implementation fact — the area-series paths are `.recharts-area-area`** (a `<path class="recharts-curve
  recharts-area-area">` per `<Area>`), and like the Tools bar chart they mount one animation tick
  after the container appears; `get_health_chart_area_series_count()` waits on the first series
  node rather than assuming the container implies them.
- `Locator.hover()` on the chart container reliably raises the tooltip carrying both series names
  (`Total Requests`, `Errors`) — no synthetic event needed, as specced.
- **Live in the `auth_state` fixture project (not the analyst's exploration project):** 5 rows —
  `api, llm, rpc, socketio, tool` — again with no `agent` row, and `api`/`llm`/`rpc`/`tool` all
  carrying `errors > 0`. The membership + response-oracle assertions hold unchanged.
