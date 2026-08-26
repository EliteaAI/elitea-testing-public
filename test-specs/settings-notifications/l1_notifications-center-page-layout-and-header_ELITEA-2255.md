# Test Case: Notifications Center page loads with correct layout and header

## Metadata
- **TMS ID**: ELITEA-2255
- **Linked Story**: batch `settings-w02` (campaign EliteaAI/elitea-testing-public#1398)
- **Priority**: l1 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend), viewport 1728x861 and 1366x768
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot, 2026-08-26
- **Status**: ready-for-automation

## Preconditions
- User is logged in (`auth_state` fixture — skips login on localhost via `VITE_DEV_TOKEN`).
- The logged-in user's personal project carries at least one notification, so the
  table renders rows rather than the `"No notifications"` empty state. Confirmed
  live 2026-08-26: 89 notifications on `personal_project_id` (project "Private").
  This is the same real, persistent DEV history ELITEA-2257/2259 already rely on
  (see `_surface.md` § Live data available) — read-only, nothing seeded.

## Test Data
### reuse-existing
- `${TEST_USER}` — logged-in user; their existing notification history is read, never mutated.

**Why reuse instead of seeding:** every observable in this case is a *layout* fact
(header text, search field, two toolbar buttons, four table columns, no permanent
loading state). None of them requires fresh state, so `.agents/testing.md`
§ Test data strategy's read-only-by-default applies — zero mutation, zero leak.
**Risk:** if DEV's notification history is ever purged the table renders the
`"No notifications"` empty state and the column-header/row assertions correctly go
RED for a genuinely missing precondition (not flake).

## Test Steps
1. Navigate to `${BASE_URL}/settings/notifications` (bare-path nav via
   `NotificationCenterPage.navigate()`, which waits on the notification list GET).
   - **Verify**: page title starts with `"Settings: Notifications"`; the notification
     table body (`notification-table-body`) is visible.
2. Read the toolbar header.
   - **Verify**: `notifications-center-header` is visible and its text is exactly
     `"Notifications Center"`.
3. Read the toolbar's search field.
   - **Verify**: `notifications-search-input` is visible, is an editable `<input>`, and
     carries `placeholder="Search"`. Confirmed live: `SimpleSearchBar` in
     `NotificationTableToolbar.jsx` with `placeholder="Search"`.
4. Read the toolbar's two action buttons (case steps 4–6 are ONE presence check whose
   step 4 sentence ends in a colon and is enumerated by steps 5 and 6 — see
   § Coverage Map).
   - **Verify**: `notification-mark-toggle-button` is visible (the case's
     "Mark as read (envelope/mail icon)"), and its accessible name is one of
     `"Mark selected as read"` / `"Mark selected as unread"` — ONE physical toggle whose
     label flips with the current selection's read state (documented clarification
     EliteaAI/elitea-testing-public#1166; live default with an empty selection is
     `"Mark selected as unread"`).
   - **Verify**: `notifications-delete-selected-button` is visible (the case's
     "Delete (trash icon)").
   - **Verify**: with no rows selected BOTH buttons are disabled — the product's own
     `isSelectionEmpty` gate (`NotificationTableToolbar.jsx`). Presence is what the case
     asks; the disabled state is recorded as the observed initial state so a future
     regression that makes a bulk action clickable with no selection is caught.
   - **NOT clicked.** The case's Expected Final State is "the page does not remain in a
     permanent loading state"; clicking Delete would destroy real DEV notification
     history and clicking Mark is ELITEA-2259's covered scope.
5. Read the table's column headers.
   - **Verify**: the select-all checkbox (`notifications-select-all-checkbox`) is visible
     — the case's "checkbox" column — and the three data-column headers read exactly
     `"Type"` (`notifications-column-header-event_type`), `"Notification"`
     (`notifications-column-header-notification_text`) and `"Date & Time"`
     (`notifications-column-header-created_at`), in that DOM order.
   - **Verify**: at least one `notification-row` is rendered and at least one
     `notification-message-text` cell is visible — the case's "Notification (text + link)"
     column carries content (its exact templates are ELITEA-2257's scope).
6. Confirm the page is not stuck loading.
   - **Verify**: the pagination page-info label (`notifications-pagination-page-info`)
     matches `^\d+ - \d+ of \d+$` and its total is > 0. `GridTableContainer.jsx` renders
     the loading placeholder, the empty placeholder and the table as three MUTUALLY
     EXCLUSIVE branches (`isLoading ? … : isEmpty ? … : children`), and
     `GridTablePagination` returns `null` when `totalRows === 0` — so a visible table
     body + a real page-info range is a positive proof that `isFetching` resolved to
     false and the data branch rendered. No separate loading testid is needed (and
     adding one to the SHARED `GridTableContainer` would be a blanket add barred by
     `.agents/testing.md` § Locator policy).
7. Assert no unexpected console errors across the whole flow
   (`utils.console_errors.collect_console_errors`, which captures the failing
   resource URL — `.agents/testing.md` § 400-flavor entry).

## Expected Results
- The Notifications Center page renders its header, search field, two toolbar action
  buttons and four-column table, backed by real data, and never remains in the
  loading state.

## Coverage Map

### Axis 1 — every original case element
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Notifications | page loads | step 1 | `step 1`: page title + table body visible | asserted |
| 2 Header shows "Notifications Center" | condition holds | step 2 | `step 2`: exact text on `notifications-center-header` | asserted |
| 3 Search input present top right | condition holds | step 3 | `step 3`: visible + placeholder "Search" | asserted |
| 4 Two action buttons present top right (umbrella, ends in a colon) | condition holds | step 4 | decomposed into the two enumerated buttons below | asserted *(decomposed)* |
| 5 Mark as read (envelope/mail icon) | button present | step 4 | `step 4`: `notification-mark-toggle-button` visible + accessible name in the known pair | asserted *(presence; see drift note)* |
| 6 Delete (trash icon) | button present | step 4 | `step 4`: `notifications-delete-selected-button` visible | asserted *(presence — not clicked, see step 4 rationale)* |
| 7 Table shown with columns: checkbox, Type (icon), Notification (text + link), Date & Time | condition holds | step 5 | `step 5`: select-all checkbox + 3 exact column-header texts in DOM order + ≥1 row with a message cell | asserted |
| 8 Page does not remain in a permanent loading state | condition holds | step 6 | `step 6`: page-info range matches + total > 0 (mutually-exclusive render branches) | asserted |
| Preconditions: "User is logged in" | — | § Preconditions | `auth_state` fixture | setup |
| Expected Final State: page does not remain in permanent loading | condition holds | step 6 | same as element 8 | asserted |

### Axis 2 — additions beyond the case
| Addition | Why it is grounded |
|---|---|
| Both toolbar buttons disabled with an empty selection | The product's own `isSelectionEmpty` gate; recorded so a regression that enables a destructive bulk action with nothing selected fails loudly. |
| No unexpected console errors | Project-wide convention on this suite (`test_notification_text_content.py`, `test_sidebar_notification_badge.py`). |

### Case-text drift (filed, not masked)
| Case text | Live product | Handling |
|---|---|---|
| Step 5 names the button "Mark as read" | ONE toggle button whose accessible name is `"Mark selected as read"` **or** `"Mark selected as unread"` depending on the current selection's read state; with nothing selected it reads `"Mark selected as unread"` | Already tracked as clarification EliteaAI/elitea-testing-public#1166 (filed for ELITEA-2259, same button). Asserted as "name is one of the known pair" — the live contract, per the reverse-masking guard. No duplicate filed. |

## Cleanup
None — read-only. No row is selected, marked, deleted or created.

## Concrete Handles (discovered during exploration)

Locator policy: testid-only (`.agents/testing.md` § Locator policy). Provenance
verified with `cd ../EliteaUI && git fetch origin` on 2026-08-26.

| Element | Recommended Locator | Provenance |
|---|---|---|
| Page header | `LocatorDescriptor(testid="notifications-center-header")` | added by this case — `EliteaAI/EliteaUI@7f772acc` on `automation/testids`, NOT yet on `main` |
| Search input | `LocatorDescriptor(testid="notifications-search-input")` | added by this case (`SimpleSearchBar` already accepts a caller-supplied `data-testid`, threaded onto its `InputBase` `inputProps`) — `EliteaAI/EliteaUI@7f772acc`, not on `main` |
| Delete-selected button | `LocatorDescriptor(testid="notifications-delete-selected-button")` | added by this case (`DeleteEntityButton` already accepts a `testId` prop) — `EliteaAI/EliteaUI@7f772acc`, not on `main` |
| Mark read/unread toggle | `LocatorDescriptor(testid="notification-mark-toggle-button")` | pre-existing (ELITEA-2259) on `automation/testids` |
| Select-all checkbox | `LocatorDescriptor(testid="notifications-select-all-checkbox")` | added by this case via `GridTableHeader`'s already-accepted `selectAllCheckboxTestId` prop — `EliteaAI/EliteaUI@7f772acc`, not on `main` |
| Column headers | `NOTIFICATION_COLUMN_HEADER = '[data-testid="notifications-column-header-{}"]'` (class constant, formatted with `event_type` / `notification_text` / `created_at`) | added by this case via `GridTableHeader`'s already-accepted `columnTestIdPrefix="notifications"` prop — `EliteaAI/EliteaUI@7f772acc`, not on `main` |
| Table body / row / message cell | `notification-table-body` / `notification-row` / `notification-message-text` | pre-existing (ELITEA-2257) on `automation/testids` |
| Pagination page-info label | `LocatorDescriptor(testid="notifications-pagination-page-info")` | added by this case via `GridTablePagination`'s already-accepted `pageInfoTestId` prop — `EliteaAI/EliteaUI@7f772acc`, not on `main` |

## Network Behavior
- `GET /api/v2/notifications/notifications/prompt_lib/{personal_project_id}?limit=50&offset=0&sort_by=created_at&sort_order=desc` — the list fetch the page object waits on (200, `{rows: [...], total: 89}` live 2026-08-26).
- `GET .../prompt_lib/{id}?only_new=true&only_total=true&limit=1&offset=0` — unread-count probe, fires on mount; must NOT be mistaken for the list response (`NotificationCenterPage._is_notifications_list_response` discriminates on `sort_by=created_at`).

## Known Defects Found During Exploration
None. Every step behaved as specified apart from the mark-button naming drift above.

## Blocked Steps
None.

## Automation Hints
- Suite: `automation/tests/ui/admin/` — where the two existing notification specs live.
- Markers: `ui`, `admin`, `p1`, `regression`.
- Reuse `NotificationCenterPage`; extend it additively (it already has ≥2 merged callers).
- Fidelity: zero substitution. Every asserted value is produced by the live product.
