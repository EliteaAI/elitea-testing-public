# Test Case: Notification text content renders correctly for known notification types

## Metadata
- **TMS ID**: ELITEA-2257
- **Linked Story**: EliteaAI/elitea-testing-public#764
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch elitea-2257-notification-text-content
- **Status**: ready-for-automation

## Preconditions
- User is logged in (`auth_state` fixture — skips login on localhost).
- The logged-in user's personal project already has a real, persistent notification
  history spanning all 4 known types the case names. Confirmed live (2026-08-04):
  the DEV backend's `personal_project_id=399` ("Private") project carries 67
  notifications, including — on the FIRST page alone — a `chat_user_mentioned`,
  a `chat_user_added`, and multiple `bucket_expiration_warning` rows, and on the
  SECOND page multiple `index_data_changed` rows (`is successfully created:` and
  `is successfully reindexed.` variants). **This is existing, not seeded, data** —
  see § Test Data for the risk this implies.

## Test Data
### reuse-existing
- `${TEST_USER}` — logged-in user whose personal project (`personal_project_id`,
  observed as `399`/"Private" on DEV) already carries notifications of all 4 case
  types plus 3 more the platform emits (`personal_access_token_expiring`,
  `agent_unpublished`). No seeding needed — see rationale below.

**Why reuse instead of seeding:** two of the four named types (`chat_user_mentioned`,
`chat_user_added`) ARE triggerable live (mention a user / add a participant in
chat), but `index_data_changed` requires a real toolkit re-index (slow, adds
flake) and `bucket_expiration_warning` is a **backend cron job** — there is no
UI/API action that fires it on demand within a test's lifetime. Since the DEV
backend already carries real, persistent examples of all 4 types for the test
user (observed 2026-08-04, see Concrete Handles § evidence), and
`.agents/testing.md` § Test data strategy prefers "read-only assertions on
stable existing data" over seeding when the observable doesn't require fresh
state, this AFS specs read-only verification against that existing history.
**Risk, stated explicitly:** if DEV's notification history is ever purged/reset,
this test will correctly go RED for a genuinely missing precondition — that is
the intended, non-masked behavior (the case's own Pass criterion is "at least
one notification of each type is rendered"), not a flaky test. Flag to the
implementer/lead if this proves to reset between environments.

## Test Steps
1. Navigate to `${BASE_URL}/settings/notifications` (bare-path nav via the page
   object's `navigate()` helper — no click through the Settings drawer needed).
   - **Verify**: page loads, page title becomes "Settings: Notifications - …"
     (confirmed live), the notification table body becomes visible and
     non-empty (`isFetching` false, `rowCount > 0`).
2. Collect every notification row's rendered text across ALL pages (loop:
   read rows, click "Next page" while enabled, cap at a safety bound e.g. 20
   pages — 67 rows / 50-per-page = 2 pages observed live, cap is headroom for
   growth, not an expected trip count).
   - **Verify**: the loop terminates (Next button becomes disabled) before the
     safety cap.
3. Chat mention: assert at least one collected row's text matches the pattern
   `<user> mentioned you in <chat-name>` (case's literal template:
   `"[User] mentioned you in [Chat link]"`).
   - **Verify**: text observed live — `"Mariam Hakobyan mentioned you in HI Chat"`
     — a `<user> mentioned you in` prefix + a link segment with the chat's name.
4. Chat participant added: assert at least one row's text matches
   `<user> added you to <chat-name>` (case's template: `"[User] added you to
   [Chat link]"`).
   - **Verify**: text observed live — `"Mariam Hakobyan added you to HI Chat"`.
5. Index success: assert at least one row's text matches `Index <index-name> is
   successfully created: {"indexed": <N>}` (case's literal template).
   - **Verify**: text observed live — `Index marian is successfully created:
     {"indexed": 60}` — note the embedded `{"indexed": N}` JSON fragment is
     PART OF THE CORRECT rendering for this type (it is literal backend copy,
     not a rendering defect) — do not flag it under step 7's "no raw JSON" check.
     A `is successfully reindexed. {"reindexed": M, "indexed": N}` variant was
     also observed live and is the same type (`index_data_changed`) — either
     satisfies this step.
6. Bucket retention warning: assert at least one row's text matches `Bucket
   <bucket-name> will start deleting files in 24 hours according to its
   retention policy (files are removed based on each file's creation date; the
   bucket itself will remain).` (case's literal template, observed live
   verbatim on multiple rows, e.g. bucket `test-bucket-qa`).
7. For EVERY collected row (not just the 4 named types), assert:
   - **Verify**: text does not contain the literal string `undefined`.
   - **Verify**: text does not contain an unresolved markdown-link token
     `[...]()`  (would indicate `parseMessage()` failed to parse a link segment
     — a real rendering defect distinct from the intentional embedded-JSON
     text in step 5).
   - **Verify**: text does not contain an unescaped/literal HTML tag pattern
     (e.g. `<div`, `<script`, `&lt;` rendered as visible text) — React
     auto-escapes text nodes, so a literal tag string surfacing here would
     indicate `dangerouslySetInnerHTML` or a raw-string leak.

## Expected Results
- All 4 known notification types (chat mention, chat participant added, index
  success, bucket retention warning) each have at least one row present and
  rendering the correct human-readable text per their template.
- No row across the full (paginated) set shows `undefined`, an unresolved
  `[text]()` link token, or a literal/unescaped HTML tag as visible text.
- No console errors during navigation or pagination.
- `GET /api/v2/notifications/notifications/prompt_lib/{personal_project_id}`
  returns 200 for both the initial page and each "Next" page fetch.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Notifications | page loads | step 1 | `step 1`: table body visible + non-empty | asserted |
| 2 "Verify at least one notification of each type is rendered correctly" (umbrella) | condition holds | steps 3–6 | decomposed per type | asserted *(decomposed)* |
| 3 Chat mention template | renders correctly | step 3 | `step 3`: pattern match on collected rows | asserted |
| 4 Chat participant added template | renders correctly | step 4 | `step 4`: pattern match on collected rows | asserted |
| 5 Index success template | renders correctly | step 5 | `step 5`: pattern match on collected rows | asserted |
| 6 Bucket retention warning template | renders correctly | step 6 | `step 6`: pattern match on collected rows | asserted |
| 7 No row shows raw JSON / broken HTML / "undefined" | condition holds | step 7 | `step 7`: per-row negative-content checks | asserted |
| Objective: "no notification row shows raw json, broken html, or undefined text" | condition holds | step 7 | same as above | asserted |

**Axis 2 — Analyst additions.**
- `step 1` asserts no console errors on load — *added: side-channel discipline
  (silent errors are the worst bugs); none observed live, guard prevents
  silent regression.*
- `step 7`'s "unresolved `[text]()` token" check — *added: this is the
  PRECISE mechanical failure mode of `parseMessage()` (entities/notifications/
  lib/helpers/notification.helpers.js) if a future backend message format
  change breaks its regex; the case's prose ("broken html") doesn't name it
  but it is the concrete manifestation on this surface — grounded in reading
  the parser source, not a guess.*
- `step 7` runs across ALL collected rows, not just the 4 named types —
  *added: the case's own step 7 / Expected Final State says "no notification
  row" (unqualified), so the negative-content check is scoped to the full set
  the case itself defines, not narrowed to the 4 named examples.*
- (nothing else added beyond the case.)

## Cleanup
- None. Read-only verification case — no test data is created, modified, or
  deleted.

## Concrete Handles (discovered during exploration)

**Locator policy: testid-only** (`.agents/role-overrides.md` +
`.agents/testing.md` § Locator policy). Confirmed via `grep -n "data-testid\|testId"`
across the entire notification-rendering component tree in `EliteaUI/src` —
**zero hits**:
`src/pages/NotificationCenter/{NotificationCenter,NotificationTable,NotificationTableToolbar}.jsx`,
`src/[fsd]/entities/notifications/ui/{NotificationListItem,NotificationListItemMessage,LegacyNotificationMessage}.jsx`.
Every handle below is `testid needed` — added via `add-data-testid`.

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Notification table body (scope for wait/row-count) | `LocatorDescriptor(testid="notification-table-body")` — wire the ALREADY-EXISTING `data-testid` prop `GridTableBody` (`src/[fsd]/entities/grid-table/ui/GridTableBody.jsx:6`) already accepts; just pass it at the call site in `NotificationTable.jsx`'s `<GridTableBody>` (currently unwired) | testid needed | needs-adding (prop exists, unwired) |
| Notification row (repeatable, one per row) | `LocatorDescriptor(testid="notification-row")` — same pattern: `GridTableRow` (`src/[fsd]/entities/grid-table/ui/GridTableRow.jsx:39-41,58`) already accepts + renders a `data-testid` prop; `NotificationTable.jsx`'s `<GridTableRow>` call (around line 251) doesn't pass it yet | testid needed | needs-adding (prop exists, unwired) |
| Notification message cell (scoped text — excludes the date/type columns so text checks aren't polluted) | `LocatorDescriptor(testid="notification-message-text")` — NEW: add to the `<Box sx={styles.notificationCell}>` wrapper in `NotificationTable.jsx`'s `renderCell` (`column.field === 'notification_text'` branch, ~line 190) | testid needed | needs-adding (new) |
| Pagination "Next page" button | `LocatorDescriptor(testid="notifications-pagination-next-button")` — NEW: `GridTablePagination.jsx`'s second `IconButton` (no `aria-label` today — confirmed live, accessible name is empty) | testid needed | needs-adding (new; SHARED component — `GridTablePagination` has no existing `data-testid` prop threading at all, unlike `GridTableBody`/`GridTableRow`; adding it there follows the same "shared component gets a generic prop" pattern already used by its siblings) |

**Naming note:** `GridTableBody`/`GridTableRow` are shared components
(`src/[fsd]/entities/grid-table/`) — per `.agents/testing.md` §
"Shared components never hardcode feature-scoped testids", the *values*
(`notification-table-body`, `notification-row`) are supplied at the
NotificationTable call site, not hardcoded inside the shared component. This
already matches the existing prop shape (`'data-testid': dataTestId`) — no
component code change needed for those two, only wiring at the call site.
`GridTablePagination` needs the prop ADDED (component change) since it has no
`data-testid` threading today; scope that addition to a `data-testid` prop on
the "Next" `IconButton` only (the "Prev" button is not touched by this test —
per role-overrides.md § locator scope, do not add a testid there).

**Evidence (live, 2026-08-04, `http://localhost:5173/settings/notifications`,
personal project 399/"Private", 67 total notifications across 2 pages @ 50/page):**
- Page 1 rows include, verbatim: `"Mariam Hakobyan mentioned you in" [link "HI Chat"]`,
  `"Mariam Hakobyan added you to" [link "HI Chat"]`,
  `"Bucket" [link "test-bucket-qa"] "will start deleting files in 24 hours according
  to its retention policy (files are removed based on each file's creation date;
  the bucket itself will remain)."`
- Page 2 rows include, verbatim: `"Index" [link "marian"] "is successfully created:
  {\"indexed\": 60}"`, `"Index" [link "RFC"] "is successfully reindexed.
  {\"reindexed\": 0, \"indexed\": 4673}"`, `"Index" [link "broken"] "is failed."`
  (a 5th, undocumented-by-the-case index outcome — informational, not asserted).
- Full-page `grep -in "undefined"` across both captured accessibility snapshots:
  **0 hits**.
- `browser_console_messages(level=error)`: **0 errors**.
- Network: `GET .../notifications/notifications/prompt_lib/399?...` → `200 OK`
  (×3 calls observed: unread-count probe, page-1 fetch, page-2 fetch).

## Network Behavior
- `GET /api/v2/notifications/notifications/prompt_lib/{personal_project_id}?limit=<pageSize>&offset=<page*pageSize>&sort_by=created_at&sort_order=desc` —
  fires on load and on every "Next"/"Prev" click; wait for this response
  (200) before reading a page's rows, not a fixed timeout.

## Known Defects Found During Exploration
None found. All 4 named notification types render their exact expected
templates on the live DEV backend; no raw JSON leak, no broken HTML, no
"undefined" text observed across all 67 rows inspected.

## Blocked Steps
None. `bucket_expiration_warning` and `index_data_changed` could not be
FRESHLY triggered on demand (see § Test Data rationale), but existing live
data covers both — no step is blocked.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- New page object: `automation/pages/notification_center_page.py` (no prior
  page object exists for this surface — confirmed via
  `ls automation/pages/ | grep -i notif` → no hits).
- New test file suggestion: `automation/tests/ui/admin/test_notification_text_content.py`
  (module `settings-notifications`; `tests/ui/admin/` already houses other
  Settings-adjacent cases — guardrails — no dedicated `settings/` folder
  exists yet, and creating one for a single case is the implementer's call).
- Markers: `@pytest.mark.p2`, a feature marker if one gets added for
  notifications (none exists in `pytest.ini` today — `admin` is the closest
  fit), `@pytest.mark.regression`.
- Wait strategy: wait for the `notifications/notifications/prompt_lib/...`
  network response (per § Network Behavior) after navigation and after each
  "Next" click — not a fixed sleep/timeout, and not just DOM-visibility of the
  table body (the table can render its EMPTY state briefly before data
  arrives).
- Pattern-matching the 4 templates: prefer substring/regex assertions on each
  row's `inner_text()` (e.g. `"mentioned you in" in text`) over exact
  full-string equality — the user name and chat/bucket/index name are live
  data and will differ from the evidence captured above.
- `parseMessage()`'s link syntax (`[text]()`) lives in
  `src/[fsd]/entities/notifications/lib/helpers/notification.helpers.js` —
  useful background if a future case needs to assert the *link* itself
  (href, target `_blank`) rather than just the text.
