# Test Case (EXTENSION): Users tab search by email filters the User Activity table

## Metadata
- **TMS ID**: ELITEA-2323
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost)
- **Analyst**: qa-engineer, batch `settings-w06` (cluster ELITEA-2311/2322/2323/2324/2325)
- **Status**: extend-existing

## Covering spec (merged to `origin/automation/base`)

`automation/tests/ui/admin/test_analytics_users_activity_table.py:206-241` —
`TestAnalyticsUsersActivityTable::test_users_tab_activity_table_columns_and_pagination`,
**Step 7 "Search-filter smoke check"** (ELITEA-2312).

### Behavioural-overlap argument (what is already proven)

The merged spec already drives the *same* control on the *same* surface with a *real* keystroke
path: it picks an existing user's email, derives a substring, calls
`AnalyticsPage.search_users(term)` (which waits on the real `analytics_users/prompt_lib/` response),
and then asserts that (a) at least one row remains, (b) the `{N} users` count label agrees with the
rendered row count, and (c) the pagination range label still matches its format. It also clears the
search in a `finally` block via `clear_users_search()`.

So ELITEA-2323's **step 2** ("type a partial email — field accepts the input") and the *narrowing*
half of **step 3** are already covered, as is the *mechanics* of **step 4**'s clear. Writing a fresh
spec would re-derive the tab navigation, the search helper, the settle wait and the count-label
regex that all already exist — Rule-6 partial overlap, not fresh implementation.

### Gap assertions (what the covering spec does NOT prove)

1. **"only rows matching the typed email"** — the merged assertion is
   `filtered_row_count >= 1`. It passes even if the filter returned *every* row, i.e. it cannot
   detect a broken filter that narrows nothing. The case's actual observable is the **exclusivity**
   of the result set.
2. **"clear the search — all users are shown again"** — the merged spec clears in `finally` with
   **no assertion at all**. The case's Expected Final State is precisely that restoration.

Both gaps are two short assertions on handles that already exist (no new testids, no page-object
changes) — an append to the covering test, not a near-rewrite.

## Preconditions
- User is authenticated (`auth_state` fixture); a project is selected.
- The selected project's User Activity table has **at least 2 users with an email identifier and a
  search term that matches a proper subset of them**. Live 2026-08-28, project "Elitea Testing Team",
  `Last 30d`: 18 rows, of which 16 carry emails; `"aliaksandr"` matches exactly 2. The gap
  assertions below derive the term from live data rather than hardcoding it, so they hold for any
  project meeting this precondition, and fail with an explicit precondition message otherwise.

## Test Steps (the extension — appended to the covering test's Step 7, in its own `allure.step`)

Let `pre_rows` = the unfiltered row identifiers and `pre_count` = the `{N} users` count label
captured **before** searching (the covering test already has both in scope at that point).

1. **Choose a discriminating term** — from the unfiltered identifiers containing `@`, take the local
   part of the first one and use its first 6+ characters (live: `aliaksandr` from
   `aliaksandr_zhukevich@epam.com`). Assert the term matches **at least one and fewer than all**
   `pre_rows` locally; otherwise fail with the precondition message above.
2. **Type the term** into `analytics-users-search-input` via `AnalyticsPage.search_users()`
   (case step 2), capturing the resulting `analytics_users/prompt_lib/` response body.
   - **Verify** (already covered, keep): the input's `input_value()` equals the term.
3. **GAP 1 — exclusivity** (case step 3):
   - **Verify**: every rendered `analytics-users-row`'s identifier contains the term
     (case-insensitively) — i.e. `all(term.lower() in ident.lower() for ident in rows)`.
   - **Verify**: the rendered identifier set equals `[r["user_email"] for r in response["rows"]]`
     (the response is the oracle) **and** is a **proper subset** of `pre_rows` — strictly fewer
     rows than before, which is the assertion that actually proves filtering happened.
   - **Verify**: the count label equals `f"{len(rows)} users"` and the response's `total`.
4. **GAP 2 — restoration** (case step 4, Expected Final State): clear the input via
   `AnalyticsPage.clear_users_search()`.
   - **Verify**: `input_value()` is `""`.
   - **Verify**: the rendered identifier list equals `pre_rows` **in the same order**, and the count
     label equals `pre_count` — the table is fully restored, not merely non-empty.

## Expected Results
- Typing a partial email narrows the User Activity table to exactly the matching users (a proper,
  fully-matching subset of the unfiltered set) and updates the count label; clearing the input
  restores the complete original row set and count.

## Coverage Map

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Analytics -> Users tab | Page/section loads | covering spec Steps 1-2 | `test_analytics_users_activity_table.py` (tab opened via `open_users_tab()`, header/count asserted) | already-covered |
| 2 Type a partial email into "Search by email"; field accepts input | Field shows the value | covering spec Step 7 + extension step 2 | `search_users()` + `input_value()` assertion | already-covered (kept) |
| 3 Table filters to show ONLY rows matching the typed email | Condition holds | **extension step 3** | every row contains the term; identifier set == response rows; proper subset of `pre_rows`; count label == `total` | **gap — new** |
| 4 / Expected Final State — clear the search, all users shown again | Expected UI state | **extension step 4** | identifier list == `pre_rows` (same order) and count label == `pre_count` | **gap — new** |

**Axis 2 — Analyst additions.**
- **Proper-subset assertion** (step 3) — *added: `all(term in ident)` alone is vacuously true for an
  empty table; pairing it with "strictly fewer than before, and non-empty" makes both failure modes
  (filters nothing / filters everything) detectable.*
- **Rendered set vs response `rows`** (step 3) — *added: the response is the oracle for what the
  filter actually returned (`.agents/testing.md` § Fidelity policy), which distinguishes a UI
  rendering bug from a backend filtering bug.*
- **Order-sensitive restoration** (step 4) — *added: the table is server-sorted
  (`sort_by=total_events&sort_order=desc`); asserting the same order catches a state leak where the
  cleared query returns unsorted or stale-cached data. Costs nothing over a count comparison.*

## Cleanup
The covering test's existing `finally: analytics_page.clear_users_search()` already handles it;
the extension's step 4 performs that clear as an asserted step, so the `finally` becomes a no-op
safety net (it early-returns when `input_value()` is empty).

## Concrete Handles (all pre-existing — no testid work in this case)

| Element | Locator | PROVENANCE |
|---|---|---|
| Users tab | `analytics-tab-users` | on-main ✓ |
| Search-by-email input | `analytics-users-search-input` | on-main ✓ (ELITEA-2312) |
| Table row (repeated) | `analytics-users-row` | on-main ✓ (ELITEA-2312) |
| `{N} users` count | `analytics-users-count` | on-main ✓ (ELITEA-2312) |
| Loading spinner | `analytics-users-loading-indicator` | on-main ✓ (ELITEA-2312) |
| Pagination range | `analytics-users-pagination-range` | on-main ✓ (ELITEA-2312) |

Page-object methods `search_users()`, `clear_users_search()`, `get_users_row_count()`,
`get_user_row_identifier()` already exist in `automation/pages/analytics_page.py` — **no page-object
change is required**, only the two new assertion blocks in the spec.

## Fidelity Declaration
No substitutions. The search is driven through the real input (`.fill()`, which the page object
documents as this app's established shape for `SearchInput.jsx`'s native `onChange`); every asserted
value comes from the live DOM or the live `analytics_users/prompt_lib/` response body.

## Network Behavior
- `GET /api/v2/elitea_core/analytics_users/prompt_lib/{project_id}?...&search={term}&sort_by=total_events&sort_order=desc`
  — fires on every search change. 200 OK.
- Clearing back to `search=""` is frequently an RTK-Query **cache hit** with **no new request** —
  `clear_users_search()` already documents this and deliberately does not `expect_response`. Do not
  "fix" it by adding one.

## Blocked Steps
None.

## Known Defects
- elitea-testing-public#1951 — the count label is not pluralised (`1 users`). The extension's
  assertions use the literal live format `f"{n} users"`, so they stay honest; a product fix needs a
  one-line update here.

## Live Observations (2026-08-28, project "Elitea Testing Team", `Last 30d`)

| Search term | Rows | Identifiers | Count label | Pagination |
|---|---|---|---|---|
| *(none)* | 18 | `testbot@elitea.ai`, `User 6250`, 16 `@epam.com` addresses | `18 users` | `1–18 of 18` |
| `samvel` | 1 | `samvel_simonyan@epam.com` | `1 users` | `1–1 of 1` |
| `aliaksandr` | 2 | `aliaksandr_zhukevich@epam.com`, `aliaksandr_valadzko@epam.com` | `2 users` | — |
| *(cleared)* | 18 | identical list, identical order | `18 users` | `1–18 of 18` |

- The filter is **live, per-keystroke** (server-side on the email field), with no debounce, no
  Enter and no blur required, and there is **no dedicated clear (X) button** — "clear the search
  input" means emptying it.
- `User 6250` (no email) never matches any term, and correctly reappears when the search is cleared.
- Zero console errors throughout.


## Implementation notes / AFS amendments (ELITEA-2323, 2026-08-28 — implementer)

- **Shipped as** the new Step 8 block in
  `automation/tests/ui/admin/test_analytics_users_activity_table.py`
  (`TestAnalyticsUsersActivityTable::test_users_tab_activity_table_columns_and_pagination`), plus
  two additive captures inside the covering Step 7 (`pre_row_identifiers`, `pre_count_text`). No
  existing assertion was changed.
- **AMENDED — "no page-object change is required" is no longer accurate.** One additive change was
  needed for the response-oracle assertion: `AnalyticsPage.search_users()` now RETURNS the captured
  `analytics_users/prompt_lib/` response body (it already wrapped the call in `expect_response`;
  only the return value is new). Its single caller is this spec, and ignoring the return value is
  still valid. Re-searching later to capture the body was NOT viable — RTK-Query serves the repeated
  query from cache with no new request.
- **PRE-EXISTING RED REPAIRED IN THE SAME PR.** The covering spec was failing on
  `automation/base` before this work: the UI team added eight token/cost breakdown columns, so the
  live User Activity header is **17** columns, not the 9 the ELITEA-2312 tuple expected. The tuple
  was updated to the live contract (still an exact ordered tuple — nothing weakened) so the
  extension could be verified. Recorded as a new occurrence on the existing case-text-drift issue
  **elitea-testing-public#1188** rather than filed as a duplicate.
- **Fixed a dead TMS link** on the covering spec's `@allure.issue` (it pointed at a
  `settings-analytics/ELITEA-2312_users-tab-activity-table.md` path that does not exist; the real
  case lives under `settings/analytics/`). A second `@allure.issue` now links ELITEA-2323's own case.
