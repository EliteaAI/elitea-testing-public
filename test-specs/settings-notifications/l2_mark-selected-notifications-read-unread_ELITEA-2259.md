# Test Case: Mark selected notifications as read and unread using checkboxes

## Metadata
- **TMS ID**: ELITEA-2259
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch elitea-2259-notifications-read-unread
- **Status**: ready-for-automation

## Preconditions
- User is logged in (`auth_state` fixture — skips login on localhost).
- The logged-in user's personal project (`personal_project_id`, observed `399`
  "Private" on DEV) has at least **2 notifications with `is_seen: false`**
  (unread) at test start. Confirmed live (2026-08-04): 61 of 67 real
  notifications on this account are unread — comfortably above the minimum
  the case needs. **This is existing, not seeded, data** — see § Test Data.

## Test Data
### reuse-existing
- `${TEST_USER}` — logged-in user whose personal project already carries
  dozens of unread notifications (real DEV history, not fixture data). No
  seeding needed: the test discovers 2 unread notifications dynamically via
  the page's own list-fetch response rather than hardcoding notification IDs,
  so it stays valid as this account's real notification history grows/ages.

**Why reuse instead of seeding:** the case doesn't require notifications of
any particular type, only "two unread notifications" — any two satisfy it.
Per `.agents/testing.md` § Test data strategy (prefer read-only assertions
on stable existing data over seeding), and per this case's own design, the
mutation is **self-reverting**: steps 7–11 mark the same two notifications
back to unread, so the account's data ends in the same state it started in
(matches the case's own "Expected Final State" — unread). No separate
cleanup step is needed; the test IS its own cleanup.
**Risk, stated explicitly:** if DEV's notification history is ever purged/reset
to fewer than 2 unread rows, this test will correctly go RED for a genuinely
missing precondition (not flake) — same non-masked-failure principle as
ELITEA-2257's AFS.

## Test Steps

1. Navigate to `${BASE_URL}/settings/notifications` (bare-path nav via the
   page object's `navigate()` helper). Wait for the notifications-list GET
   response (`.../notifications/notifications/prompt_lib/{project_id}?...
   sort_by=created_at...`) to resolve.
   - **Verify**: page loads, page title starts with "Settings: Notifications"
     (confirmed live: `"Settings: Notifications - Private"`); the table body
     is visible and non-empty.
2. From the list-fetch response body (JSON `rows[]`, each row carries
   `id` and `is_seen`), select the **first 2 rows (in display order) where
   `is_seen == false`**. Record their `id`s and the full baseline row set
   (id → `is_seen`) for every OTHER row on the current page — this baseline
   is what step 5's "all other notifications unchanged" check compares
   against.
   - **Verify**: at least 2 unread rows were found (else fail with a clear
     "insufficient unread notifications" message — a missing precondition,
     not a flaky assertion).
3. Check the checkbox for each of the two selected notifications (locate via
   their dynamic per-row checkbox testid, keyed by notification id — see
   § Concrete Handles).
   - **Verify**: both checkboxes are checked; the toolbar's mark-toggle
     button becomes enabled and its accessible name is
     `"Mark selected as read"` (both selected rows are currently unread, so
     the toggle offers "read").
4. Click the toolbar's mark-toggle button ("Mark selected as read").
   Wait for the `PUT .../notifications/notifications/prompt_lib/{project_id}`
   request (body `{"ids": [...], "is_seen": true}`) to resolve 200, then for
   the list to refetch.
   - **Verify**: a success toast reading `"Notifications marked as read"`
     appears (generic app-wide toast component, reused — see § Concrete
     Handles).
   - **Verify**: both checkboxes are unchecked again (selection clears after
     a successful bulk action) and the toolbar mark-toggle button reverts to
     disabled.
5. Re-fetch the list (or read the refetch response already triggered by
   step 4) and verify:
   - **Verify**: both of the two selected notification ids now have
     `is_seen: true` in the response.
   - **Verify**: every OTHER row from step 2's baseline still has the SAME
     `is_seen` value it had before step 4 (no collateral mutation).
6. Reload the page (full navigation, not SPA re-fetch). Wait for the list
   fetch to resolve.
   - **Verify**: the response confirms both notification ids are still
     `is_seen: true` (persisted server-side, survives a fresh page load).
7. Check the checkbox for the SAME two notification ids (now read) again.
   - **Verify**: both checkboxes are checked; the toolbar mark-toggle
     button's accessible name is now `"Mark selected as unread"` (both
     selected rows are currently read, so the toggle offers "unread" — same
     physical button as step 3, different label per the live product's
     single-toggle design, see § Known Defects / case-text note below).
8. Click the toolbar's mark-toggle button ("Mark selected as unread").
   Wait for the `PUT` request (body `{"ids": [...], "is_seen": false}`) to
   resolve 200, then for the list to refetch.
   - **Verify**: a success toast reading `"Notifications marked as unread"`
     appears.
   - **Verify**: both checkboxes are unchecked again and the toolbar
     mark-toggle button reverts to disabled.
9. Verify from the refetch response:
   - **Verify**: both notification ids now have `is_seen: false` again.
   - **Verify**: every OTHER row from step 2's baseline is still unchanged.
10. Reload the page again. Wait for the list fetch to resolve.
    - **Verify**: the response confirms both notification ids are
      `is_seen: false` (persisted — matches the case's own "Expected Final
      State").

## Expected Results
- The two selected notifications toggle from unread → read → unread again,
  each transition confirmed both immediately (post-PUT refetch) and after a
  full page reload (persistence).
- No other notification's `is_seen` state is affected by either bulk action.
- Both bulk actions produce a success toast with the exact text observed
  live (`"Notifications marked as read"` / `"Notifications marked as
  unread"`).
- Every `PUT .../notifications/notifications/prompt_lib/{project_id}` call
  returns 200; every list-fetch `GET` returns 200.
- No console errors during any step.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Notifications | page loads | step 1 | page title + table visible | asserted |
| 2 Check the checkbox on two unread notifications | condition holds | steps 2–3 | dynamic discovery + checkbox state | asserted *(decomposed: discovery step added, see Axis 2)* |
| 3 Click the "Mark as read" button | control responds | step 4 | click + PUT 200 + toast | asserted *(case's "Mark as read" button = the live product's single toggle button, showing "Mark selected as read" in this selection state — clarification filed, see § Known Defects)* |
| 4 Verify only the two checked notifications change to read state | condition holds | step 5 | PUT response + refetch `is_seen` | asserted |
| 5 Verify all other notifications remain in their original state unchanged | condition holds | step 5 | baseline-vs-refetch diff | asserted |
| 6 Reload the page — verify the two notifications remain in read state | action completes, expected UI state | step 6 | reload + refetch `is_seen` | asserted |
| 7 Check the checkbox on the same two notifications (now in read state) | condition holds | step 7 | checkbox state + toggle label | asserted |
| 8 Click the "Mark as unread" button | control responds | step 8 | click + PUT 200 + toast | asserted *(same clarification as row 3)* |
| 9 Verify only the two checked notifications change back to unread state | condition holds | step 9 | PUT response + refetch `is_seen` | asserted |
| 10 Verify all other notifications remain unchanged | condition holds | step 9 | baseline-vs-refetch diff | asserted |
| 11 Reload the page — verify the two notifications remain in unread state | action completes, expected UI state | step 10 | reload + refetch `is_seen` | asserted |
| Expected Final State: two notifications remain unread after final reload | condition holds | step 10 | same as row 11 | asserted |

**Axis 2 — Analyst additions.**
- Step 2 (dynamic unread-notification discovery via the list response) is an
  *added* step — *grounded reason: the case names no specific notifications
  ("two unread notifications"), and this account's notification history is
  real, growing DEV data, not a fixture — hardcoding IDs would make the test
  brittle to data drift. Discovering via the live response is the stable
  substitute, matching the same pattern ELITEA-2257's AFS used for reading
  existing data instead of seeding.*
- Toast-text assertions (steps 4, 8) — *added: side-channel/UX discipline;
  exact strings confirmed by reading `NotificationTable.jsx`'s
  `toastSuccess()` call sites, not guessed.*
- "All other notifications unchanged" is scoped to the CURRENT PAGE's
  baseline (up to 50 rows), not all 67 across both pages — *added scope
  decision: re-paginating through all pages twice per mutation (4 extra
  network round-trips) to check rows nowhere near the two under test adds
  test time without added confidence; the current page comfortably contains
  the 2 target rows and dozens of controls. Documented here rather than
  silently narrowed.*
- No console-error check is listed as a separate case step but is run every
  step per project convention (silent errors are the worst bugs); zero
  observed live throughout the whole 11-step flow.
- (nothing else added beyond the case.)

## Cleanup
- None required — the test is self-reverting by construction (see § Test
  Data). If step 8 (mark-unread) fails partway, the two notifications may be
  left in a read state; that is the natural failure signal for a red test
  and does not require manual cleanup for the next run (the next run
  discovers whichever 2 unread notifications exist at that time — see § Test
  Data risk note for the floor case).

## Concrete Handles (discovered during exploration)

**Locator policy: testid-only** (`.agents/role-overrides.md` +
`.agents/testing.md` § Locator policy). This case reuses handles already
added for ELITEA-2257 (confirmed live in `NotificationTable.jsx` /
`NotificationTableToolbar.jsx` source, 2026-08-04) plus two NEW handles this
case needs that don't exist yet.

| Element | Recommended Locator | Provenance |
|---|---|---|
| Notification table body | `LocatorDescriptor(testid="notification-table-body")` | **on-automation/testids ✓** — added by ELITEA-2257, `NotificationTable.jsx`'s `<GridTableBody data-testid="notification-table-body">` |
| Notification row (generic, repeatable) | `LocatorDescriptor(testid="notification-row")` | **on-automation/testids ✓** — ELITEA-2257, same file's `<GridTableRow data-testid="notification-row" ...>`. NOT per-id (all rows share this literal testid) — insufficient alone to target one of the two specific rows this case needs; see the new per-row checkbox handle below. |
| Notification row checkbox (dynamic, per-id — NEW for this case) | `LocatorDescriptor` not applicable directly (dynamic) — class constant template: `NOTIFICATION_ROW_CHECKBOX = '[data-testid="notification-checkbox-{}"]'`, formatted with the notification's `id` at the call site | **needs-adding** — `GridTableRow.jsx` (`src/[fsd]/entities/grid-table/ui/GridTableRow.jsx:40,70`) ALREADY accepts and renders a `checkboxTestId` prop on its `Checkbox.BaseCheckbox`; `NotificationTable.jsx`'s `<GridTableRow>` call site (`src/pages/NotificationCenter/NotificationTable.jsx`, ~line 251) does not pass it yet. Wiring is a one-line addition: `checkboxTestId={`notification-checkbox-${row.id}`}` — exact precedent already exists in `ArtifactTable.jsx:527` (`checkboxTestId={`artifacts-file-checkbox-${row.id}`}`), so this is "follow an established sibling pattern," not an improvisation. |
| Mark-selected toggle button (single button, toggles read/unread by selection state — NEW for this case) | `LocatorDescriptor(testid="notification-mark-toggle-button")` | **needs-adding** — `NotificationTableToolbar.jsx`'s `BaseBtn` (the mark-toggle button) currently has only a state-dependent `aria-label` (`"Mark selected as read"`/`"Mark selected as unread"`), no `data-testid`. Per role-overrides.md's testid-stability rule, the TESTID itself must stay constant across the read/unread toggle (state goes in the accessible name / assertion text, not the testid) — add ONE static `data-testid="notification-mark-toggle-button"` regardless of `markAsRead` value. |
| Success toast (generic, reused) | `LocatorDescriptor(testid="toast-message")` | **on-main ✓ (pre-existing, app-wide)** — confirmed already used by `artifacts_page.py:353` (`ArtifactsPage.success_toast_message`); ELITEA-1832 established this is the stable app-wide toast handle. No new testid needed — reuse the existing page-object field if one gets added to a shared/base page object, or declare it locally with the same testid value. |

**Naming note:** the checkbox testid follows the SAME dynamic-testid
convention already used for `notification-message-text` (static, ELITEA-2257)
and the sibling `artifacts-file-checkbox-${row.id}` (dynamic, pre-existing) —
`{section}-{element}-{id}` with the id as the format parameter, per
`.agents/testing.md` § Locator policy's dynamic-testid pattern.

**Declared improvisation — toggle button testid stability:** the canon
(`.agents/testing.md` § "Testid = stable identity; state via `data-*`
attributes") governs elements whose testid PRESENCE/VALUE would otherwise
flip with state; this button's `aria-label` (not testid) is what changes
today, and no testid exists at all yet. Adding ONE static testid regardless
of the read/unread toggle state is the direct, canon-compliant application
of that same principle to a not-yet-testid'd element — declaring this
explicitly per `.agents/role-overrides.md` § Declared-improvisation protocol
since the canon doesn't literally cover "adding a first testid to a
state-labelled button," only "don't make an EXISTING testid state-dependent."

**Evidence (live, 2026-08-04, `http://localhost:5173/settings/notifications`,
personal project 399/"Private"):**
- Selected two real unread notifications: id `110096` ("Your personal access
  token Marian will expire...", `personal_access_token_expiring`) and id
  `109821` ("Mariam Hakobyan mentioned you in HI Chat", `chat_user_mentioned`).
- Checked both checkboxes → toolbar button became `"Mark selected as read"`
  (enabled) → clicked → `PUT .../prompt_lib/399` → 200 → refetch showed both
  ids `is_seen: true`, `updated_at` bumped to the click timestamp; a
  representative untouched row (id `109818`) stayed `is_seen: false`,
  `updated_at` unchanged.
- Reloaded (full navigation) → refetch confirmed both ids still `is_seen:
  true`.
- Re-checked both checkboxes → toolbar button became `"Mark selected as
  unread"` (enabled, same physical button/DOM position, only the label
  changed) → clicked → `PUT` → 200 → refetch showed both ids `is_seen:
  false` again, `updated_at` bumped again; other rows still unaffected.
- Reloaded again → refetch confirmed both ids `is_seen: false` — final state
  matches the case's own Expected Final State.
- `browser_console_messages(level=error)` throughout the whole flow: **0
  errors**, all 4 navigation/action cycles.

## Network Behavior
- `GET /api/v2/notifications/notifications/prompt_lib/{personal_project_id}?limit=&offset=&sort_by=created_at&sort_order=desc` —
  the list fetch; each row includes `id` and `is_seen`. Fires on load, on
  reload, and again after each successful bulk-mark `PUT` (cache
  invalidation via the `TAG_NOTIFICATIONS` RTK-Query tag).
- `PUT /api/v2/notifications/notifications/prompt_lib/{personal_project_id}`
  — bulk mark-seen. Body: `{"ids": [<id>, <id>, ...], "is_seen": <bool>}`.
  200 on success; invalidates the list-fetch tag, triggering the automatic
  refetch above. This is the SAME endpoint URL as the paginated list GET
  (differs only by HTTP method) — do not conflate with the separate
  unread-count probe GET (`?only_new=true&only_total=true&limit=1&offset=0`,
  fires once on mount, unrelated to this case).

## Known Defects Found During Exploration
None. Product behavior is correct throughout — see the case-text
clarification below (not a defect).

**Case-text clarification (filed, not a defect — reverse-masking guard
applied per `.agents/role-overrides.md`):** the case's steps 3 and 8 refer to
"the 'Mark as read' button" and "the 'Mark as unread' button" as if they are
two separate, statically-labelled controls. The live product has ONE toggle
button in the table toolbar (`NotificationTableToolbar.jsx`) whose accessible
name flips between `"Mark selected as read"` and `"Mark selected as unread"`
depending on whether the CURRENTLY SELECTED rows include any unread
notification (`shouldMarkAsRead = rows.some(row => selectedRowIds.has(row.id)
&& !row.is_seen)`). This correctly drives the case's own read→unread→unread
flow (the button naturally offers "mark read" when unread rows are selected,
and "mark unread" once they're all read) — the product design is sound, only
the case's description of it is imprecise (and its literal button text,
"Mark as read"/"Mark as unread", actually belongs to a DIFFERENT surface —
the single-notification hover action in the sidebar bell popover /
`NotificationListItem.jsx`, not this table's bulk toolbar). Filed:
[EliteaAI/elitea-testing-public#1166](https://github.com/EliteaAI/elitea-testing-public/issues/1166).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: extend the existing `automation/pages/notification_center_page.py`
  (from ELITEA-2257) rather than creating a new one — add methods for:
  checking a notification's checkbox by id, reading the mark-toggle button's
  accessible name/enabled state, clicking it, and capturing the
  success-toast text. Reuse `NotificationCenterPage.navigate()` and the
  existing `_is_notifications_list_response()` predicate for waits.
- New test file: `automation/tests/ui/admin/test_notification_mark_read_unread.py`
  (same `tests/ui/admin/` convention as ELITEA-2257's test — no dedicated
  `settings/` folder exists yet).
- Markers: `@pytest.mark.p2`, `@pytest.mark.admin` (closest fit — no
  dedicated notifications marker exists), `@pytest.mark.regression`.
- Discovering the two target unread ids: capture the list-fetch response
  (Playwright `expect_response` + `.json()`), filter `rows` for
  `is_seen == False`, take the first 2 — mirror how
  `NotificationCenterPage._is_notifications_list_response()` already
  distinguishes the list fetch from the unread-count probe.
- Bulk-mark wait strategy: wait for the `PUT` response (200), THEN for the
  automatically-triggered list refetch (also via
  `_is_notifications_list_response()`) — not a fixed sleep. The UI clears
  selection and updates the toolbar button optimistically only after the
  mutation's promise resolves (`await bulkMarkSeenNotifications(...).unwrap()`
  in `NotificationTable.jsx`).
- Toast assertion: `toast_page.success_toast_message` (or equivalent) —
  match on exact text `"Notifications marked as read"` /
  `"Notifications marked as unread"` (confirmed via
  `NotificationTable.jsx`'s `toastSuccess()` call sites), not a substring
  guess.
- "All other rows unchanged" check: snapshot `{id: is_seen}` for the current
  page's rows BEFORE the mutation (from step 2's discovery fetch), then diff
  against the post-mutation refetch, asserting equality for every id except
  the two targets.
