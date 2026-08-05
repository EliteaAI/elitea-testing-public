# Test Case: Users tab loads User Activity table with correct columns and pagination

## Metadata
- **TMS ID**: ELITEA-2312
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids` —
  confirmed identical blob to `main` for `AnalyticsContainer.jsx` AND `AnalyticsUsers.jsx`
  (`main:c7b6ff4b...` == `automation/testids:c7b6ff4b...`), so this surface is fully on `main` already)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost — no manual login)
- **Analyst**: qa-engineer (analyst slot), batch `elitea-2312`
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (`auth_state` fixture — localhost skips login via `VITE_DEV_TOKEN`).
- A project is selected with at least one user having usage-analytics data (observed live in
  project "UI Testing": 3 users — `User 6250`, `testbot@elitea.ai`, `levon_dadayan@epam.com` — all
  with `errors: 0`). Read-only assertions against this existing data; no test data creation required.

## Test Data
### reuse-existing
- No test data required — the case only asserts table structure (columns, pagination controls,
  header, search input) against whatever users the currently-selected project already has
  analytics rows for. Exact row count/content is not asserted (see Coverage Map row 2 — asserted
  as "a non-negative integer", not a specific number).

## Test Steps
1. Navigate to Settings → Analytics, then click the "Users" tab (reuse
   `AnalyticsPage.tab_users`, `analytics-tab-users`, already on `main` from ELITEA-2310).
   - **Verify**: the Users tab becomes selected (`aria-selected="true"`) and its panel renders
     without error.
2. Verify the section header shows "User Activity" and a user-count line reading `"{N} users"`
   where N is a non-negative integer matching the actual row/user total.
3. Verify a "Search by email" input is present, positioned in the top-right of the User Activity
   card (same row as the "User Activity" title/count, `justify-content: space-between`).
4. Verify the table header row shows exactly these 9 columns, in this order: `User, Active Days,
   LLM Calls, Tool Calls, Agent/Pipeline Runs, Chat Msg, Errors, Total Tokens, Total Cost`.
   — **Case-text drift** (see § Known Defects): the case's step 4 lists 8 columns including a
   non-existent "EVENTS" column; the live product's real 9-column set above is what this AFS
   asserts (reverse-masking guard — live product is correct, case text is stale).
5. Verify the Errors column's value color: for a row with `errors === 0`, the value renders in
   the table's default text color (NOT the red/rejected status color); the red/rejected color
   applies only when `errors > 0`.
   — **Case-text drift** (see § Known Defects): the case's step 5 says red "when greater or equal
   0", which literally would mean every value (including 0) is red — contradicted by both live
   observation (three `errors: 0` rows render white/default, not red) and source
   (`AnalyticsUsers.jsx:144-151`: `color: u.errors > 0 ? palette.status.rejected : undefined`).
   This AFS asserts the live/source-confirmed `> 0` threshold for the negative case; see
   § Blocked Steps for the positive-case (`errors > 0` → actually red) verification gap.
6. Verify pagination controls are present: a "Rows per page" selector (default value 20, options
   10/20/50), a page-range label matching the pattern `"{from}–{to} of {count}"` (live observed:
   "1–3 of 3" for 3 users on one page), and previous/next page arrow buttons (both disabled when
   there is exactly one page, i.e. `count <= rowsPerPage`).

## Expected Results
- Users tab loads its panel: "User Activity" header + count, search input, 9-column table, and
  pagination controls — all render without console errors.
- The GET `.../analytics_users/prompt_lib/{project_id}?date_from=...&date_to=...&limit=...&offset=...&sort_by=total_events&sort_order=desc`
  request resolves 200 and the table reflects its response (`total`, `rows`).
- Errors column: default color for `errors === 0`, red/rejected color for `errors > 0` — both
  branches live-verified against the `auth_state` fixture's actual project data (see § Blocked
  Steps for the closure note).
- Search input live-filters the table (confirmed: typing "testbot" narrowed 3 rows → 1 row and
  updated the count/pagination label to "1 users" / "1–1 of 1" — no Enter or blur needed, no
  debounce beyond render-time).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Analytics → Users tab | Target page/section loads successfully | step 1 | `step 1`: tab selected + panel renders | asserted |
| 2 Section header shows "User Activity" + user count (e.g. "1 users") | Condition holds | step 2 | `step 2`: title text + count pattern | asserted |
| 3 "Search by email" input present, top right | Condition holds | step 3 | `step 3`: input present + position | asserted |
| 4 Table has columns USER, EVENTS, DAYS, LLM, TOOL, AGENT, CHAT MSG, ERRORS | Condition holds | step 4 | `step 4`: live 9-column set asserted instead | clarification *(case's 8-column list incl. "EVENTS" is stale; live table has 9 columns incl. Total Tokens/Total Cost and no Events column — filed elitea-testing-public#1188)* |
| 5 ERRORS column value shown in red when ≥ 0 | Condition holds | step 5 | `step 5`: both branches asserted live — negative case (`errors===0` → default color) and positive case (`errors>0` → red/rejected color), against the `auth_state` fixture's actual project data | clarification *(case's "≥0" threshold is stale/self-contradictory — literal reading recolors every value; live source confirms `>0`. Filed elitea-testing-public#1188. Positive branch had no live data in the analyst's exploration project ("UI Testing") — originally deferred per § Blocked Steps — but was closed during implementation once the `auth_state` fixture's actual target project ("Private") was found to have rows with `errors > 0`; see § Blocked Steps for the closure note)* |
| 6 Pagination controls present: rows-per-page selector, page range label, prev/next arrows | Condition holds | step 6 | `step 6`: all three control groups asserted, including default rows-per-page value and disabled-when-one-page state | asserted |

**Axis 2 — Analyst additions.**
- `step 1` asserts `aria-selected="true"` on the Users tab (beyond the case's bare "loads
  successfully") — *added: cheap, catches a tab-switch regression using the same handle ELITEA-2310
  already established (`is_tab_selected`).*
- `step 2` asserts the count is a genuine integer that matches the visible row total, not just
  that *some* text matching "N users" is present — *added: catches a stale/hardcoded count
  regression (e.g. count frozen at page-load value while rows update after a search filter).*
- `step 4` asserts exact column **order**, not just presence — *added: order is part of the
  visible UI contract and free to assert once the header handle is captured (mirrors ELITEA-2310's
  tab/preset order assertions).*
- `step 6` asserts the *default* rows-per-page value (20), read directly off
  `analytics-users-pagination-rows-select`'s rendered text — *added: the case only asks for "a
  selector present"; asserting the default value catches a silent regression cheaply, using the
  same locator.*
  — **Implementer amendment (2026-08-05):** the AFS's original wording also proposed asserting the
  exact `rowsPerPageOptions` list (10/20/50) "cheaply, using the same locator." Live exploration
  found this is NOT cheap: MUI's `TablePagination` renders the closed-select's *current* value via
  `slotProps.select`'s testid, but the open-dropdown menu items (the actual 10/20/50 options) are
  generated internally with no per-option testid hook — `TablePagination`'s `slotProps` exposes only
  a single `menuItem` slot applied identically to every option, which cannot disambiguate "the 20
  option" from "the 50 option." Enumerating them would need net-new per-option testid plumbing (not
  in the analyst's original 10-handle Concrete Handles table) — out of proportion to this addition's
  "free" framing and disallowed as a fresh non-testid handle under `.agents/testing.md` § Locator
  policy. Technique gap, not a scope drop: this AFS now asserts only the *default* rows-per-page
  value; the options-list enumeration is left for a future case that scopes the per-option testid
  work explicitly.
- **Search-filter smoke check** (not in the case's numbered steps, but directly adjacent to step 3
  "search input is present" and free to verify with the same handle): typing an existing user's
  email substring narrows the table to matching rows and updates the count/pagination label
  accordingly — *added: proves the input actually functions, not merely that it renders; a
  present-but-inert search box would otherwise pass step 3 while being broken.* Confirmed live
  (`testbot` → 1 matching row, count "1 users", pagination "1–1 of 1"), see
  `test-results/screenshots/ELITEA-2312-step-06-users-table-filtered.png`.

## Cleanup
None — read-only page load and search-filter interaction; no data created or mutated. (If the
search-filter smoke check is implemented, clear the search input at the end of the test so the
Page fixture doesn't leak filtered state into a subsequent test reusing the same page/tab —
`analytics_page.clear_users_search()` should reset via the same input handle.)

## Concrete Handles (discovered during exploration)

**Provenance note:** `AnalyticsUsers.jsx` is confirmed **identical** on `EliteaAI/EliteaUI` `main`
and `automation/testids` (blob `c7b6ff4b68aec5e6f8b72e433cbe8c62126e5d04` on both, verified
2026-08-05 after a fresh `git fetch origin`) — this surface is already on `main`. **Zero
pre-existing testids** on anything in `AnalyticsUsers.jsx` or the shared `SearchInput` component
it uses. All 10 handles below need adding via `add-data-testid`; uniqueness verified against
`origin/main` (0 hits for all 10, fresh fetch 2026-08-05, `EliteaUI@a68b3728`).

| Element | Recommended Locator | PROVENANCE | Notes |
|---|---|---|---|
| "User Activity" title | `LocatorDescriptor(testid="analytics-users-activity-title")` | needs-adding | `AnalyticsUsers.jsx:80-86` — static `<Typography variant="labelMedium">User Activity</Typography>` |
| User count subtitle | `LocatorDescriptor(testid="analytics-users-count")` | needs-adding | `AnalyticsUsers.jsx:87-92` — `<Typography variant="bodySmall">{total} users</Typography>`, dynamic text; read via `.text_content()` and regex-match `r"^(\d+) users$"` |
| "Search by email" input | `LocatorDescriptor(testid="analytics-users-search-input")` | needs-adding | Shared component `src/components/SearchInput.jsx` (no existing `testId` prop) — add a `testId` prop, wire it as `inputProps={{ 'data-testid': testId }}` on the MUI `<Input>` at line ~14, and pass `testId="analytics-users-search-input"` at the call site `AnalyticsUsers.jsx:94-99`. Per `.agents/testing.md` § Locator policy, shared components never hardcode feature-scoped testids — a caller-supplied prop is the compliant shape (same pattern as the `closeButtonTestId`-style props already used elsewhere in the codebase). |
| Table header row | `LocatorDescriptor(testid="analytics-users-table-header")` | needs-adding | `AnalyticsUsers.jsx:102-112` — the `Box` wrapping the 9 header `Typography` cells; add the testid on that wrapping `Box`. Read via `.inner_text()` and split on newline (each `<Typography>` is a block element) to get the 9 ordered labels — no per-column testid needed since only the aggregate header row is asserted (order+labels), never clicked/interacted with individually. |
| Table data row (repeated, one per rendered user) | `LocatorDescriptor(testid="analytics-users-row")` | needs-adding | `AnalyticsUsers.jsx:120-124` — the clickable row `Box` (`key={i}`, `onClick={() => handleUserClick(u.user_id)}`); **same testid value on every row** (list pattern), select via `.nth(i)` — mirrors the existing `artifacts-file-row` convention in `automation/pages/artifacts_page.py`. Used only to count/iterate rows for the Errors-color check below; the row's `onClick` navigates to a user-detail view (`AnalyticsUserDetailed`) which is OUT OF SCOPE for this case — do not click it. |
| Errors cell (repeated, one per row) | `LocatorDescriptor(testid="analytics-users-row-errors")` | needs-adding | `AnalyticsUsers.jsx:144-151` — the Errors `Typography` inside each row (`color: u.errors > 0 ? palette.status.rejected : undefined`); add the testid on this specific `Typography` so its color can be read via `get_attribute`-free `page.eval_on_selector`/Playwright's `expect(locator).to_have_css("color", ...)` rather than a positional child selector off the row (`row.locator("> *").nth(n)`, the pattern used in `artifacts_page.py` — that is tracked tech debt per `.agents/role-overrides.md`, not to be replicated in new code). Same repeated-testid + `.nth(i)` pattern as the row. |
| Rows-per-page selector | `LocatorDescriptor(testid="analytics-users-pagination-rows-select")` | needs-adding | MUI `<TablePagination>` at `AnalyticsUsers.jsx:161-170` — wire via `slotProps={{ select: { 'data-testid': 'analytics-users-pagination-rows-select' } }}` (MUI v7 non-deprecated `slotProps.select`, confirmed present in `node_modules/@mui/material/TablePagination/TablePagination.js`; do NOT use the deprecated `SelectProps`). |
| Page-range label | `LocatorDescriptor(testid="analytics-users-pagination-range")` | needs-adding | Same `<TablePagination>` — wire via `slotProps={{ displayedRows: { 'data-testid': 'analytics-users-pagination-range' } }}` (confirmed slot exists: `useSlot('displayedRows', ...)` in `TablePagination.js`). Read text and assert regex `r"^\d+–\d+ of \d+$"` (or exact "1–3 of 3" against the live 3-user fixture). |
| Previous-page button | `LocatorDescriptor(testid="analytics-users-pagination-prev")` | needs-adding | Same `<TablePagination>` — wire via `slotProps={{ actions: { previousButton: { 'data-testid': 'analytics-users-pagination-prev' } } }}` (non-deprecated form; `backIconButtonProps` is deprecated in favor of this per the same file's propTypes comments). Assert `disabled` when on the only/first page. |
| Next-page button | `LocatorDescriptor(testid="analytics-users-pagination-next")` | needs-adding | Same `<TablePagination>` — wire via `slotProps={{ actions: { nextButton: { 'data-testid': 'analytics-users-pagination-next' } } }}`. Assert `disabled` when `count <= rowsPerPage` (single page, live-observed state with 3 users / 20 rows-per-page). |

**Reused from ELITEA-2310** (already on `main`, no new work): `AnalyticsPage.tab_users`
(`analytics-tab-users`) to navigate to the tab, and `is_tab_selected()` to confirm selection.

Uniqueness verified (2026-08-05, `git fetch origin` fresh, `EliteaUI@a68b3728`):
`git grep -- "<testid>" origin/main -- src/` → **0 hits** for all 10 new testids above.

## Network Behavior
- `GET /api/v2/elitea_core/analytics_users/prompt_lib/{project_id}?date_from=...&date_to=...&limit=20&offset=0&sort_by=total_events&sort_order=desc`
  — fires on Users-tab mount and again (debounced by the query hook, no explicit UI debounce) on
  every `search` keystroke change; confirmed live: 200 OK, no console errors, both on initial tab
  load and after typing into the search input.

## Known Defects Found During Exploration
- **[CLARIFICATION]** Case text drift (not a product defect — reverse-masking guard applies):
  case step 4 lists 8 columns including a non-existent "EVENTS" column; live table has 9 columns
  (`User, Active Days, LLM Calls, Tool Calls, Agent/Pipeline Runs, Chat Msg, Errors, Total Tokens,
  Total Cost`) with no "Events" column. Case step 5 says the Errors value is red "when greater or
  equal 0" (literally: every value, including 0, would be red); live observation (three
  `errors: 0` rows, all rendered in the default/white text color) plus source
  (`AnalyticsUsers.jsx:144-151`, `color: u.errors > 0 ? palette.status.rejected : undefined`)
  confirm the real threshold is `> 0`. Filed: **elitea-testing-public#1188**. This AFS's steps 4–5
  assert the live contract, not the case's stale numbers.

## Blocked Steps
- **(Closed during implementation, 2026-08-05)** Step 5, positive branch (`errors > 0` →
  red/rejected color actually renders): at analysis time, the exploration project ("UI Testing")
  had no user with `errors > 0` in its analytics data, and there was no cheap/available mechanism
  in that environment to seed an error-attributed analytics event for a specific user (would
  require driving a real tool/LLM failure end-to-end and waiting for it to aggregate into the
  analytics pipeline — disproportionate to this case's scope, which is table structure/pagination,
  not analytics-pipeline correctness). The negative branch (`errors === 0` → default color) was
  live-verified and automated per the original step 5 plan; the positive branch was, at that
  point, confirmed only by reading `AnalyticsUsers.jsx:144-151` directly. During implementation,
  the `auth_state` fixture's actual target project ("Private" — distinct from the analyst's
  exploration project "UI Testing") was found to already have two users with `errors > 0`
  (`User 6250`: 78, `testbot@elitea.ai`: 75) live in the default "Last 24h" range — so the positive
  branch is live-exercisable against this suite's real fixture data with no seeding required. The
  implementer folded it into this PR: the shipped test asserts both branches live (see Coverage
  Map row 5, and the test's Step 5 in
  `automation/tests/ui/admin/test_analytics_users_activity_table.py`), iterating every rendered row
  and asserting the default color for `errors === 0` rows and the red/rejected color for
  `errors > 0` rows, with a hard assertion that at least one `errors === 0` row was exercised (the
  `errors > 0` branch is asserted per-row when present but not required as a precondition, since
  live data may legitimately shift to all-zero over time).

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Extend `pages/analytics_page.py` (created by ELITEA-2310) with the Users-tab-specific
  `LocatorDescriptor` fields above, rather than creating a second page object — same page,
  same URL, same class; ELITEA-2310 already covers the page shell (header/tabs/dates), this case
  covers the Users-tab panel content.
- Reuse `AnalyticsPage.navigate()` + `AnalyticsPage.tab_users` + `AnalyticsPage.is_tab_selected()`
  from ELITEA-2310 to reach and confirm the Users tab — do not re-derive tab navigation.
- Wait strategy: wait for the `analytics_users/prompt_lib/...` GET response (`page.expect_response`
  matching the URL substring `/elitea_core/analytics_users/prompt_lib/`) before asserting table
  content, mirroring `AnalyticsPage.navigate()`'s existing `ANALYTICS_QUERY_URL_SUBSTRING` wait
  pattern for the Overview query — add a second URL-substring constant
  (`ANALYTICS_USERS_QUERY_URL_SUBSTRING = "/elitea_core/analytics_users/prompt_lib/"`) rather than
  reusing the Overview one (they're different endpoints).
- Column-header assertion: split `analytics-users-table-header`'s `.inner_text()` on `"\n"` and
  compare the resulting list to the expected 9-label tuple — exact match, not substring/contains.
  **Implementer note (2026-08-05):** `tableCell`'s `sx` applies `text-transform: uppercase` —
  `inner_text()` reflects the CSS-rendered text, so the expected tuple must be the UPPERCASE form
  (`"USER"`, `"ACTIVE DAYS"`, …), not the JSX source's title-case strings. Confirmed live: the
  title-case comparison failed 1/1 (fast infrastructure fix, re-run green after correcting the
  expected tuple's case).
- Errors-color assertion: use Playwright's `expect(locator).to_have_css("color", "rgb(255, 255,
  255)")` (or the theme's actual `palette.text.secondary` resolved value — confirm via
  `getComputedStyle` at implementation time, since `rgb(255, 255, 255)` was observed against the
  currently-active theme and could differ under a different theme/mode) for the `errors === 0`
  case; do NOT hardcode an assumed "red" hex without reading `palette.status.rejected`'s resolved
  value first if/when the positive branch becomes testable (see § Blocked Steps).
- Pagination default-state assertion (3 users, `rowsPerPageOptions=[10,20,50]`, default
  `rowsPerPage=20`): range label "1–3 of 3", both prev/next buttons `disabled` — this is the
  live-observed default; if the exploration project's user count changes, the range label changes
  correspondingly (still single-page while `total <= 20`).
- **Implementer note (2026-08-05) — search-filter smoke check, two root causes found:**
  (1) `press_sequentially` occasionally dropped the leading keystroke on
  `analytics-users-search-input` (a Playwright/React re-render-timing race, not a product defect).
  `SearchInput.jsx` wires `onChange` straight off a plain native `<input>` (no MUI TextField/masking
  layer), and `.fill()` is this codebase's established, working pattern for exactly that shape
  (`agents_list_page.py`'s `search()`/`clear_search()`) — switched to it.
  (2) Independently, `BasePage.wait_for_network()` (wraps `page.wait_for_load_state("networkidle")`)
  is a one-time-per-navigation Playwright lifecycle event — once the page has already reached
  `networkidle` (true well before this method runs), calling it again resolves immediately
  regardless of a request `.fill()` triggers a few ms later, so it never actually waited for the
  search response (reproduced as a false-empty "0 rows after searching 'testbot'" filtered result,
  2/2). Fixed by wrapping `.fill()` in `page.expect_response(...)` against
  `ANALYTICS_USERS_QUERY_URL_SUBSTRING` (the same pattern `open_users_tab()` already uses) instead
  of `wait_for_network()`. Confirmed green after both fixes.
  (3) The response-vs-render lag itself needed its own fix: `expect_response` only confirms the
  network request finished, not that React has re-rendered with the new `data`/`isFetching` state —
  added a testid (`analytics-users-loading-indicator`, `EliteaAI/EliteaUI@00eab214`) on the
  Users-tab's `isFetching` spinner and a `_wait_for_users_settled()` helper (wait for it hidden) to
  close that gap. (4) Clearing the search back to `""` is frequently a cache HIT — RTK-Query already
  ran that exact query at tab-mount — so no new network request fires at all; wrapping the clear in
  `expect_response` timed out waiting for a request that legitimately never happens.
  `clear_users_search()` now relies on `_wait_for_users_settled()` alone (handles both the cached
  and uncached case).
  **Also discovered while debugging:** the `auth_state` fixture's default test project ("Private")
  has richer data than the "Private"-adjacent "UI Testing" project the analyst explored against —
  it has TWO users with `errors > 0` (User 6250: 78, testbot@elitea.ai: 75) live in the default
  "Last 24h" range. This means the AFS § Blocked Steps gap (errors>0 -> red, previously
  source-confirmed only) IS actually live-exercisable in the project this suite's fixtures target.
  Closed during implementation: the positive branch (`errors > 0` → red/rejected color) is now
  asserted live in the same Step 5 as the negative branch, against this real fixture data — see
  Coverage Map row 5 and § Blocked Steps for the closure note.
