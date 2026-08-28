# Test Case: Tools tab displays Most Popular Tools bar chart and Tool Details table

## Metadata
- **TMS ID**: ELITEA-2322
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost)
- **Analyst**: qa-engineer, batch `settings-w06` (cluster ELITEA-2311/2322/2323/2324/2325)
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (`auth_state` fixture); a project is selected.
- The selected project has **at least one tool call** in the chosen range, otherwise the bar chart
  is not rendered at all (`toolChartData.length > 0` guard, `AnalyticsTools.jsx:77`). The test
  drives `Last 30d`, which live-satisfies this in the default project; the chart assertions are
  additionally guarded on the captured response so an empty project fails loudly with a clear
  precondition message rather than a confusing locator timeout.

## Test Data
### reuse-existing
Whatever tool activity the selected project already has. Live 2026-08-28, project
"Elitea Testing Team", `Last 30d`: 2 tools (`read_file` 3 calls, `list_files` 1 call), both with
`errors == 0`.

## Test Steps

1. Navigate to Settings -> Analytics, click `Last 30d`, then open the **Tools** tab
   (`analytics-tab-tools`) — case step 1 — **capturing the resulting
   `analytics_tools/prompt_lib/` response body** as the oracle for all count assertions.
   - **Verify**: the tab is selected (`aria-selected="true"`), the response is 200, and the
     loading indicator (`analytics-tools-loading-indicator`) has settled to count 0.
2. Verify the "Most Popular Tools" bar chart (case step 2).
   - **Verify**: `analytics-tools-chart-title` has text `Most Popular Tools`.
   - **Verify**: `analytics-tools-chart-subtitle` matches `^Top (\d+) by usage$`, and the captured
     N equals `min(len(response["rows"]), 20)` — the chart series is `rows.slice(0, 20)`.
   - **Verify**: `analytics-tools-chart-container` is visible and its X-axis tick labels equal, in
     order, the `tool_name` of the first N rows of the response.
3. Verify each bar has a distinct colour (case step 3).
   - **Verify**: inside `analytics-tools-chart-container`, the rendered bar `fill` values number N
     and are **all distinct** (`AnalyticsCommonConstants.CHART_COLORS[i % len]` — distinct while
     N <= len(CHART_COLORS)). Live: `#10A37F`, `#4285F4` for the 2 bars.
4. Verify the "Tool Details" table header block (case steps 4 and 7).
   - **Verify**: `analytics-tools-details-title` text is `Tool Details`.
   - **Verify**: `analytics-tools-count` matches `^(\d+) tools$` and the number equals the
     response's `total`.
   - **Verify**: `analytics-tools-search-input` is visible and its `placeholder` is
     `Search by tool name`.
5. Verify the table columns (case step 5).
   - **Verify**: the cells of `analytics-tools-table-header`, in order, read
     `["Tool", "Calls", "Users", "Avg Latency", "Errors"]`.
   - *(The case writes them upper-cased. The DOM text is title-case; the uppercase appearance comes
     from `text-transform: uppercase` in `styles.tableCell`. Same as the already-automated Users
     tab — assert the DOM text, and additionally assert the computed `text-transform` is
     `uppercase` so the visual contract the case describes is still covered.)*
6. Verify the ERRORS column colour rule (case step 6) — as a **two-directional invariant**, not a
   data assumption.
   - **Verify**: for every rendered row (`analytics-tools-row`), the errors cell
     (`analytics-tools-row-errors`) computed `color` equals the theme's `palette.status.rejected`
     red (live `rgb(215, 22, 22)`) **iff** its integer value is `> 0`, and equals the default text
     colour otherwise. Cross-check each row's errors value against the matching response row's
     `errors` field.
7. Verify pagination (case step 8, Expected Final State).
   - **Verify**: `analytics-tools-pagination-rows-select` is visible and shows the default
     `20`; opening it offers `10 / 20 / 50`.
   - **Verify**: `analytics-tools-pagination-range` matches `^\d+–\d+ of \d+$` and its trailing
     total equals the response's `total`.
   - **Verify**: the rendered row count equals `min(total, rowsPerPage)`.
8. No console errors throughout (`utils/console_errors.collect_console_errors`).

## Expected Results
- The Tools tab renders the "Most Popular Tools" bar chart (one distinctly-coloured bar per tool,
  subtitle `Top N by usage`) and the "Tool Details" table with the 5-column header, a
  "Search by tool name" input, a `{N} tools` count matching the response, and MUI pagination
  showing the rows-per-page selector and a page-range label.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Analytics -> Tools tab | Page/section loads | step 1 | tab selected, 200 response, spinner settled | asserted |
| 2 "Most Popular Tools" chart, subtitle "Top N by usage", tool names on X axis | Condition holds | step 2 | title text, subtitle regex + N vs response, X-tick labels vs response `tool_name`s | asserted |
| 3 Each bar has a distinct colour | Condition holds | step 3 | N bar fills, all distinct | asserted |
| 4 "Tool Details" table with count subtitle (e.g. "17 tools") | Condition holds | step 4 | title text + `{N} tools` regex, N vs response `total` | asserted |
| 5 Columns: TOOL, CALLS, USERS, AVG LATENCY, ERRORS | Condition holds | step 5 | header cell tuple + `text-transform: uppercase` | asserted *(DOM text is title-case; uppercase is CSS — asserted both ways)* |
| 6 ERRORS value shown in red when > 0 | Condition holds | step 6 | per-row colour-iff-`errors > 0` invariant, values cross-checked against the response | asserted *(positive branch not present in live data — see § Blocked Steps; the invariant covers both directions honestly)* |
| 7 "Search by tool name" input present | Condition holds | step 4 | input visible + placeholder text | asserted |
| 8 / Expected Final State — paginated with rows-per-page selector and page range label | Condition holds | step 7 | selector default + options, range regex + total vs response, row count vs `min(total, rowsPerPage)` | asserted |

**Axis 2 — Analyst additions.**
- **Every count/label cross-checked against the captured response body** — *added: `"2 tools"`
  matching a regex proves formatting, not correctness; comparing to `total` proves the UI rendered
  the backend's number (`.agents/testing.md` § Fidelity policy).*
- **X-axis tick labels vs response `tool_name`s** (step 2) — *added: the case says "tool names on X
  axis" but names no oracle; the response is the only honest one.*
- **Errors colour asserted as a two-directional invariant** (step 6) — *added: the live data has no
  `errors > 0` row, so a one-directional "is red" assertion would be unwritable; the invariant is
  satisfiable today (proving the negative branch) and automatically covers the positive branch the
  day such data exists. Same shape as the already-merged Users-tab test.*
- **Rows-per-page options `10 / 20 / 50`** (step 7) — *added: one extra read on a control the case
  already requires the test to touch; catches a silently-changed option set.*
- **Console-error check** (step 8) — *standing project convention.*

## Cleanup
None — read-only. If the implementer types into the tool search at any point, clear it in a
`finally` block (the merged Users-tab test's `clear_users_search()` pattern) so tab state does not
leak into a later test in the same session.

## Concrete Handles (discovered during exploration)

| Element | Locator | PROVENANCE |
|---|---|---|
| Tools tab | `analytics-tab-tools` | on-main ✓ |
| `Last 30d` preset | `analytics-date-preset-30` | on-main ✓ |
| Chart subtitle (`Top N by usage`) | `analytics-tools-chart-subtitle` | on-`automation/testids` only (EliteaAI/EliteaUI@b74c4d90) |
| Chart container | `analytics-tools-chart-container` | on-`automation/testids` only (EliteaAI/EliteaUI@b74c4d90) |
| `Tool Details` title | `analytics-tools-details-title` | on-`automation/testids` only (EliteaAI/EliteaUI@22ff73c0) |
| `{N} tools` count | `analytics-tools-count` | on-`automation/testids` only (EliteaAI/EliteaUI@22ff73c0) |
| Table header row | `analytics-tools-table-header` | on-`automation/testids` only (EliteaAI/EliteaUI@22ff73c0) |
| Table row (repeated) | `analytics-tools-row` | on-`automation/testids` only (EliteaAI/EliteaUI@22ff73c0) |
| Loading spinner | `analytics-tools-loading-indicator` | on-`automation/testids` only (EliteaAI/EliteaUI@22ff73c0) |
| Chart title (`Most Popular Tools`) | **testid needed: `analytics-tools-chart-title`** | needs-adding — `AnalyticsTools.jsx` ~line 84, sibling of the already-testid'd subtitle |
| Tool search input | **testid needed: `analytics-tools-search-input`** | needs-adding — **call-site only**: `src/components/SearchInput.jsx` already accepts a `testId` prop (added for ELITEA-2312); pass `testId="analytics-tools-search-input"` at `AnalyticsTools.jsx`'s `<StyledSearchInput>` |
| Row errors cell (repeated) | **testid needed: `analytics-tools-row-errors`** | needs-adding — mirrors the existing `analytics-users-row-errors` |
| Pagination rows-per-page select | **testid needed: `analytics-tools-pagination-rows-select`** | needs-adding — via `TablePagination` `slotProps.select` |
| Pagination range label | **testid needed: `analytics-tools-pagination-range`** | needs-adding — via `TablePagination` `slotProps.displayedRows` |

**Implementer notes on the testid work.**
- The `TablePagination` wiring pattern already exists verbatim in `AnalyticsUsers.jsx:213-220` —
  copy the `slotProps` shape and rename the values. Add **only** `select` and `displayedRows`; this
  case never touches the prev/next buttons (`.agents/testing.md` § Locator policy — "referenced =
  called on the executed path", canon #511).
- All five additions are attribute/prop-only — no new DOM node, no new hook, no replaced MUI
  built-in (`add-data-testid` § Step 5.5).
- Recharts' internal bar `<path>` and X-axis tick nodes cannot carry an app testid (library-internal
  render nodes). Reach them as **scoped raw handles inside the `analytics-tools-chart-container`
  testid parent** — `.agents/testing.md` § Locator policy, #579 exception 1 — and declare the
  exception in the `AnalyticsPage` method docstring, exactly as the date-picker popper methods do.
- Page object: extend `automation/pages/analytics_page.py` — class-level `LocatorDescriptor` fields
  plus an `open_tools_tab()` / `_wait_for_tools_settled()` pair mirroring the existing
  `open_users_tab()` / `_wait_for_users_settled()`.

## Fidelity Declaration
No substitutions. Every asserted value is produced by the live system; the
`analytics_tools/prompt_lib/` response is captured live and used as the oracle for counts, tool
names and error values (`.agents/testing.md` § Fidelity policy). No `page.route`, no
`route.fulfill`, no injected state.

## Network Behavior
- `GET /api/v2/elitea_core/analytics_tools/prompt_lib/{project_id}?date_from=...&date_to=...&limit=...&offset=...&search=...`
  — fires on tab mount, on every search keystroke, and on any pagination change. 200 OK. Body:
  `{total, rows: [{tool_name, calls, users, avg_duration_ms, errors}]}`.
- Wait on that response, never on `networkidle` (#1847 — persistent Socket.IO polling transport).

## Blocked Steps
- **Step 6's positive branch (`errors > 0` renders red) is not live-exercisable** in the default
  project: both tool rows have `errors == 0` (live 2026-08-28). Same gap the merged ELITEA-2320
  Agents-tab AFS recorded for its own errors column. **Not a blocker for this case** — the
  two-directional invariant in step 6 is satisfiable today and would catch a regression in either
  direction; only the red-render path stays source-confirmed rather than live-confirmed. Do NOT
  fabricate a row to exercise it (terminal substitution — `.agents/testing.md` § Fidelity policy).

## Known Defects
- elitea-testing-public#1951 — `analytics-tools-count` is not pluralised (a single tool reads
  `1 tools`). MINOR; the step-4 regex `^(\d+) tools$` deliberately encodes the live format, so the
  test stays honest and needs a one-line update if the product is fixed.

## Live Observations (2026-08-28, project "Elitea Testing Team", `Last 30d`)
- Chart: title `Most Popular Tools`, subtitle `Top 2 by usage`, X ticks `read_file`, `list_files`,
  bar fills `#10A37F` / `#4285F4` (distinct).
- Table: title `Tool Details`, count `2 tools`, header `Tool | Calls | Users | Avg Latency | Errors`,
  rows `read_file 3 1 241ms 0` and `list_files 1 1 240ms 0` (both errors white, i.e. the negative
  branch).
- Search input placeholder `Search by tool name`, no testid.
- Pagination: `Rows per page: 20`, range `1–2 of 2`.
- Zero console errors.
