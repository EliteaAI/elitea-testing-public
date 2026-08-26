# Test Case: Notifications Center pagination controls are present and functional

## Metadata
- **TMS ID**: ELITEA-2256
- **Linked Story**: batch `settings-w02` (campaign EliteaAI/elitea-testing-public#1398)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot, 2026-08-26
- **Status**: ready-for-automation

## Preconditions
- User is logged in (`auth_state` fixture).
- The logged-in user's personal project carries **more than 10** notifications, so a
  second page exists and "Next" is enabled. Confirmed live 2026-08-26: 89 rows
  (`total: 89` in the list response). Asserted as a loud precondition in step 2, not
  skipped — a silent skip would delete the case.

## Test Data
### reuse-existing
- `${TEST_USER}` — existing notification history, read-only. Pagination changes only
  client-side state (`paginationModel`) plus GET requests; nothing is mutated, so no
  cleanup is required and the test is parallel-safe by construction.

## Test Steps
1. Navigate to `${BASE_URL}/settings/notifications` (`NotificationCenterPage.navigate()`).
   - **Verify**: table body visible; the page-info label is present.
2. Read the pagination footer.
   - **Verify**: the rows-per-page selector (`notifications-pagination-page-size-select`)
     is visible and reads `"50"` (the product default, `pageSize: 50` in
     `NotificationCenter.jsx`); the page-info label
     (`notifications-pagination-page-info`) matches `^(\d+) - (\d+) of (\d+)$`; the prev
     arrow (`notifications-pagination-prev-button`) is visible **and disabled** (page 0)
     and the next arrow (`notifications-pagination-next-button`) is visible.
   - **Verify (precondition)**: the parsed total is > 10, so selecting 10 rows/page
     genuinely yields more than one page; otherwise fail loudly naming the missing
     precondition.
   - Live 2026-08-26: `"1 - 50 of 89"`, prev disabled, next enabled.
3. Open the rows-per-page selector and choose `10`.
   - Click `notifications-pagination-page-size-select-combobox` (MUI `SelectDisplayProps`
     testid — the clickable display node; the bare `…-page-size-select` testid is the
     `Select` root), then click `notifications-page-size-option-10`, waiting on the
     resulting list GET.
   - **Verify**: the request the product issues carries `limit=10` and `offset=0`
     (the response is the oracle — `.agents/testing.md` § How to test a
     NONDETERMINISTIC producer without substituting it).
4. Read the table after the change.
   - **Verify**: exactly 10 `notification-row` elements are rendered, and that count
     equals `len(response["rows"])` — the UI carried the product's own payload through
     faithfully, rather than a number the test chose.
   - **Verify**: the selector now reads `"10"` and the page-info label reads
     `"1 - 10 of {total}"` with the SAME total observed in step 2.
5. Click the next-page arrow (`NotificationCenterPage.click_next_page()`, which waits
   on the next list GET).
   - **Verify**: the request carries `offset=10&limit=10`; the response status is 200.
6. Read the table after paging.
   - **Verify**: the page-info label now reads `"11 - 20 of {total}"` (same total).
   - **Verify**: the rendered row-id set is DISJOINT from page 1's — a genuinely new set
     of notifications, not a re-render of the same rows. Ids are read from the product's
     own response bodies (`rows[].id`) and cross-checked against the rendered
     `notification-checkbox-{id}` testids on the executed path.
   - **Verify**: the prev arrow is now enabled.
7. Assert no unexpected console errors across the flow.

## Expected Results
- Rows-per-page, page-range label and prev/next arrows are all present, and changing
  the page size and paging forward both re-query the backend and re-render the table
  with the corresponding, disjoint slice of the user's notifications.

## Coverage Map

### Axis 1 — every original case element
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Notifications | page loads | step 1 | `step 1`: table body visible | asserted |
| 2 Pagination controls shown at the bottom: "Rows per page" selector, page range label, prev/next arrows | condition holds | step 2 | `step 2`: selector visible + range regex + both arrows visible (prev disabled on page 0) | asserted |
| 3 Change "Rows per page" to a different value (e.g. 10) | action completes | step 3 | `step 3`: option clicked, list GET observed with `limit=10&offset=0` | asserted |
| 4 Table updates to show the selected number of rows | condition holds | step 4 | `step 4`: rendered row count == 10 == `len(response.rows)`; selector reads "10"; range reads "1 - 10 of {total}" | asserted |
| 5 Click the next page arrow | control responds | step 5 | `step 5`: list GET observed with `offset=10&limit=10`, 200 | asserted |
| 6 Page range label updates and a new set of notifications is shown | condition holds | step 6 | `step 6`: range == "11 - 20 of {total}"; page-2 id set disjoint from page-1's; prev now enabled | asserted |
| Preconditions: "User is logged in" | — | § Preconditions | `auth_state` fixture | setup |
| Expected Final State: range label updates + new set shown | condition holds | step 6 | same as element 6 | asserted |

### Axis 2 — additions beyond the case
| Addition | Why it is grounded |
|---|---|
| Prev arrow disabled on page 0, enabled on page 1 | The product's own `isFirstPage` gate; the case names "prev/next arrows" as controls, and their enabled state is the only observable that distinguishes a working prev arrow from a dead one. |
| Request params (`limit`/`offset`) asserted alongside the DOM | Proves the page-size change and the page step reached the backend, not just the client-side label — the difference between a real pagination and a cosmetic one. |
| Disjoint id sets between pages | Makes "a new set of notifications is shown" (case step 6) mechanically checkable instead of eyeballed. |
| No unexpected console errors | Suite-wide convention. |

### Case-text drift (filed, not masked)
| Case text | Live product | Handling |
|---|---|---|
| Page-range label example `"1–50 of 195"` (en dash, 195 total) | `"1 - 50 of 89"` — ASCII hyphen with spaces (`GridTablePagination.jsx`: `` `${startRow} - ${endRow} of ${totalRows}` ``); the total is whatever the account holds | Case says "e.g." — an illustration, not a contract. Asserted by regex + the product's own total, never a hardcoded 195. No clarification needed. |

## Cleanup
None — the page-size/page state is component-local and dies with the browser context.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance |
|---|---|---|
| Rows-per-page select (root) | `LocatorDescriptor(testid="notifications-pagination-page-size-select")` | added by this case via `GridTablePagination`'s already-accepted `pageSizeSelectTestId` prop — `EliteaAI/EliteaUI@7f772acc` on `automation/testids`, NOT yet on `main` |
| Rows-per-page select (clickable display node) | `LocatorDescriptor(testid="notifications-pagination-page-size-select-combobox")` | derived automatically by `SingleSelect.jsx` (`SelectDisplayProps: {'data-testid': `${dataTestId}-combobox`}`) — same commit |
| Rows-per-page option | `PAGE_SIZE_OPTION = '[data-testid="notifications-page-size-option-{}"]'` (class constant, dynamic testid) | added by this case at the `NotificationTable.jsx` call site (`option.testId`, consumed by the pre-existing `SingleSelectMenuItem` line `data-testid={option.testId ?? …}`) — same commit. Caller-supplied, so no other `SingleSelect` in the app gains a testid. |
| Page-info label | `LocatorDescriptor(testid="notifications-pagination-page-info")` | added by this case via `pageInfoTestId` — same commit |
| Prev arrow | `LocatorDescriptor(testid="notifications-pagination-prev-button")` | added by this case via `prevButtonTestId` — same commit |
| Next arrow | `LocatorDescriptor(testid="notifications-pagination-next-button")` | pre-existing (ELITEA-2257) |
| Row / row checkbox | `notification-row` / `NOTIFICATION_ROW_CHECKBOX` | pre-existing (ELITEA-2257 / ELITEA-2259) |

## Network Behavior
- Page-size change → `GET …/prompt_lib/{id}?limit=10&offset=0&sort_by=created_at&sort_order=desc` (200).
- Next page → `GET …?limit=10&offset=10&…` (200).
- Both are discriminated from the unread-count probe by `sort_by=created_at`
  (`NotificationCenterPage._is_notifications_list_response`).

## Known Defects Found During Exploration
None.

## Blocked Steps
None.

## Automation Hints
- Suite: `automation/tests/ui/admin/`; markers `ui`, `admin`, `p2`, `regression`.
- Extend `NotificationCenterPage` additively — `select_page_size()`, `get_page_info()`,
  `get_rendered_row_ids()`; do not modify existing methods (≥2 merged callers).
- No sleeps: every state change is awaited on the product's own list GET.
