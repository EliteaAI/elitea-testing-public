# Settings → Notifications surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Settings → Notifications
surface (`/settings/notifications`, renders `NotificationCenter`). Not a
substitute for execution — verify a handle as you use it. One writer at a
time; first confirmed by: qa-engineer analyst, ELITEA-2257, 2026-08-04.

## Route & component tree
- `Settings/notifications` tab (`src/[fsd]/pages/settings/index.jsx`) routes to
  `<NotificationCenter />` (`src/pages/NotificationCenter/NotificationCenter.jsx`)
  via `src/[fsd]/app/routes/ProtectedRoutes.jsx:388`. Direct bare-path
  navigation (`page.goto('/settings/notifications')` / page object
  `navigate("/settings/notifications")`) reaches it without clicking through
  the Settings drawer — confirmed live, no auth/redirect friction on
  localhost (`auth_state` already logged in).
- Same underlying list component (`NotificationListItem` /
  `NotificationListItemMessage`) also backs the sidebar bell-icon popover
  (`src/[fsd]/widgets/Notifications/`) via a `context` prop (`'list'` vs
  `'table'` — only affects text variant/clamping, not the message-rendering
  logic). A case on the popover surface would reuse the SAME message-text
  handle once added (see below) — don't re-request it.
- Message text rendering: `NotificationListItemMessage.jsx` parses
  `notification.meta.message` via `parseMessage()`
  (`src/[fsd]/entities/notifications/lib/helpers/notification.helpers.js`) —
  link syntax is `[visible text]()` (empty href), resolved at render time by
  `resolveHref(event_type, meta, projectId)`. A message with NO `meta.message`
  falls back to `LegacyNotificationMessage.jsx` — not observed live on this
  DEV backend's 67 sampled rows (all had `meta.message` populated); flag if a
  future case needs the legacy path exercised.

## Testid status — ZERO anywhere in this component tree (confirmed 2026-08-04)
`grep -n "data-testid\|testId"` across `NotificationCenter.jsx`,
`NotificationTable.jsx`, `NotificationTableToolbar.jsx`,
`NotificationListItem.jsx`, `NotificationListItemMessage.jsx`,
`LegacyNotificationMessage.jsx` → **no hits**. Every locator this surface
needs is `testid needed`.

**Two of the four handles ELITEA-2257 needs are "wire an existing prop", not
"add a new one"** — the shared `GridTableRow`/`GridTableBody`
(`src/[fsd]/entities/grid-table/ui/`) already accept a `'data-testid':
dataTestId` prop and render it (`GridTableRow.jsx:39-41,58`,
`GridTableBody.jsx:6`), but `NotificationTable.jsx`'s call sites don't pass
one yet. Cheaper than a real add — no component-code change, just the call
site. `GridTablePagination.jsx` has NO such prop today (its "Next"/"Prev"
`IconButton`s have no `aria-label` either) — that one IS a real component
change if a case needs to click through pages.

## Live data available (personal project / `personal_project_id`, observed `399` "Private")
DEV backend already carries persistent, real notification history (67 rows,
2 pages @ 50/page as of 2026-08-04) covering every `NotificationType` this
surface renders except ones we didn't look for. Confirmed present with clean
text (no `undefined`, no unresolved `[text]()`, no literal HTML):
`chat_user_mentioned` ("… mentioned you in …"), `chat_user_added` ("… added
you to …"), `bucket_expiration_warning` ("Bucket … will start deleting files
in 24 hours …"), `index_data_changed` (both "is successfully created:
{...}" and "is successfully reindexed. {...}" message variants, plus a
"… is failed." outcome), `personal_access_token_expiring`,
`agent_unpublished`. **Prefer reading this existing history over seeding** —
`bucket_expiration_warning` is backend-cron-only (no on-demand trigger
exists) and `index_data_changed` needs a slow real re-index; only
`chat_user_mentioned`/`chat_user_added` are cheaply triggerable live. Risk:
this is real user history, not fixture data — if DEV ever resets it, tests
relying on it correctly go red for a missing precondition (not flake).

## API
- `GET /api/v2/notifications/notifications/prompt_lib/{personal_project_id}?limit=&offset=&sort_by=created_at&sort_order=desc` —
  page fetch, 200 OK observed for both pages.
- `GET .../prompt_lib/{id}?only_new=true&only_total=true&limit=1&offset=0` —
  unread-count probe, fires once on mount.
- `PUT /api/v2/notifications/notifications/prompt_lib/{personal_project_id}` —
  bulk mark-seen/unseen (ELITEA-2259, confirmed live 2026-08-04). Body:
  `{"ids": [<id>, ...], "is_seen": <bool>}`. 200 on success; invalidates the
  `TAG_NOTIFICATIONS` RTK-Query tag, which auto-triggers a list refetch (no
  manual reload needed to see the change reflected — reload is only needed
  to prove SERVER-SIDE persistence). Each row's `is_seen` flips exactly for
  the ids in the request body; every other row's `is_seen`/`updated_at` is
  untouched — confirmed by diffing full response bodies before/after.
- Pagination is `limit`/`offset`, sortable by `created_at` — no `search` param
  applied unless `search.length >= 2` (`MIN_SEARCH_LENGTH` in
  `NotificationCenter.jsx`), debounced 600ms.

## Read/unread state (`is_seen`) — no visible DOM indicator today
Rows carry `is_seen` in the API response but there is NO dot/bold/badge in
the rendered table distinguishing read from unread (only a subtle
`text.primary` vs `text.secondary` color on the date cell — not usable as a
reliable test signal). **Verify read/unread state via the list-fetch
response body's `is_seen` field, not a DOM attribute check**, unless/until a
future case adds a `data-is-seen` (or similar) attribute to the row.

## Selection + bulk mark-read/unread (ELITEA-2259, confirmed live 2026-08-04)
- `NotificationTable.jsx` uses `useRowSelection` for per-row checkboxes
  (`GridTableRow`'s `Checkbox.BaseCheckbox`, `onChange` → `handleSelectRow`).
- The toolbar (`NotificationTableToolbar.jsx`) has **ONE mark-toggle button**,
  not two — its accessible name flips between `"Mark selected as read"` and
  `"Mark selected as unread"` based on
  `shouldMarkAsRead = rows.some(row => selectedRowIds.has(row.id) &&
  !row.is_seen)` (true if ANY currently-selected row is unread). Case text
  describing "two buttons" is a documented clarification (issue #1166), not
  a defect — the single toggle is correct, testable UX.
- `GridTableRow.jsx` ALREADY accepts a `checkboxTestId` prop (destructured,
  wired onto `Checkbox.BaseCheckbox`'s `data-testid`) — `NotificationTable.jsx`
  doesn't pass one yet. Precedent for the dynamic value shape:
  `ArtifactTable.jsx:527` uses `checkboxTestId={`artifacts-file-checkbox-${row.id}`}`;
  the notification analogue is `notification-checkbox-${row.id}`.
- The toolbar's mark-toggle `BaseBtn` has only a state-dependent `aria-label`
  today, no `data-testid` — needs one NEW static testid
  (`notification-mark-toggle-button`) whose value must NOT itself flip with
  state (only the button's accessible name/label does).
- Success toasts: `"Notifications marked as read"` / `"Notifications marked
  as unread"` (exact strings, from `toastSuccess()` call sites) — use the
  existing app-wide generic `toast-message` testid (already used by
  `artifacts_page.py`), no new toast testid needed.
- 61 of 67 real notifications on the test account are unread as of
  2026-08-04 — comfortably enough for any case needing "N unread
  notifications" without seeding; discover ids dynamically from the list
  response rather than hardcoding, since this is real growing DEV history.

## Notifications Center layout + pagination (ELITEA-2255 / ELITEA-2256, confirmed live 2026-08-26)

**Testids added this session** — `EliteaAI/EliteaUI@7f772acc` on `automation/testids`,
NOT yet on `main` (human cherry-picks). All are call-site wiring of props the shared
`grid-table` / shared-ui components ALREADY accepted, except the two plain attribute
adds in `NotificationTableToolbar.jsx`:

| Testid | How | Component |
|---|---|---|
| `notifications-center-header` | new `data-testid` attribute | `NotificationTableToolbar.jsx` header `<Typography>` |
| `notifications-search-input` | `data-testid` prop (already threaded to `InputBase.inputProps`) | `SimpleSearchBar` call site |
| `notifications-delete-selected-button` | `testId` prop (already accepted) | `DeleteEntityButton` call site |
| `notifications-select-all-checkbox` | `selectAllCheckboxTestId` prop (already accepted) | `GridTableHeader` call site |
| `notifications-column-header-{event_type,notification_text,created_at}` | `columnTestIdPrefix="notifications"` (already accepted) | `GridTableHeader` call site |
| `notifications-pagination-{prev-button,page-info,page-size-select}` | `prevButtonTestId` / `pageInfoTestId` / `pageSizeSelectTestId` (already accepted) | `GridTablePagination` call site |
| `notifications-pagination-page-size-select-combobox` | derived automatically by `SingleSelect.jsx` (`SelectDisplayProps`) — **this is the clickable node**; the bare `…-page-size-select` testid is the `Select` ROOT and clicking it is unreliable | `SingleSelect` |
| `notifications-page-size-option-{5,10,50,100}` | per-option `testId` on the call site's `pageSizeSelectOptions` — consumed by the PRE-EXISTING `SingleSelectMenuItem.jsx` line `data-testid={option.testId ?? \`select-option-${option.value}\`}` | `NotificationTable.jsx` |

⇒ **`SingleSelectMenuItem` already gives every select option a testid** (falling back to
`select-option-{value}`). For a scoped, collision-free handle pass `testId` on the option
object at the call site instead of relying on the generic fallback. No shared-component
edit was needed for the dropdown.

**Pagination facts (live 2026-08-26):** default `pageSize` 50; options `[5, 10, 50, 100]`;
page-info format is `` `${startRow} - ${endRow} of ${totalRows}` `` — ASCII hyphen with
spaces, e.g. `"1 - 50 of 89"` (the case text's `"1–50 of 195"` en-dash example is an
illustration only). `GridTablePagination` returns `null` when `totalRows === 0`.
89 notifications on the test account this session (was 67 on 2026-08-04 — it grows).

**"Permanent loading state" is provable without a loading testid:** `GridTableContainer`
renders loading / empty / table as three MUTUALLY EXCLUSIVE branches
(`isLoading ? … : isEmpty ? … : children`), so a visible `notification-table-body` plus a
real page-info range IS positive proof that `isFetching` resolved false. Do **not** add a
testid to `GridTableContainer`'s loading node — it is shared by every grid table in the
app and that would be a blanket add.

**Toolbar action buttons (live):** exactly TWO — the single mark read/unread toggle
(`notification-mark-toggle-button`, accessible name `"Mark selected as unread"` when the
selection is empty) and the delete button (`aria-label="delete entity"`). Both are
`disabled` until at least one row is selected.

## Settings-drawer Notifications entry (ELITEA-2260, confirmed live 2026-08-26)

- `settings-nav-item-notifications` is the LAST item of the drawer's PERSONAL group and
  needs **no scrolling** at either 1728x861 or the headless test viewport 1366x768:
  `settings-drawer-menu` has `scrollHeight == clientHeight == 617`, `scrollTop == 0`, and
  the entry's box (top 630 / bottom 662) sits inside the menu box (top 61 / bottom 678).
- **There is NO badge of any kind in the Settings drawer** — `SettingsDrawer.jsx` renders
  `icon + label` only; the drawer's innerText contains no digit and there are zero
  `MuiBadge` nodes inside `settings-drawer`. The product's unread indication is a
  **boolean red dot**, not a count, on the app sidebar header bell
  (`sidebar-notifications-bell-icon[data-has-messages]`, ELITEA-2234). ELITEA-2260's
  step 4 ("unread count badge next to Notifications") is therefore case-text drift —
  commented on clarification EliteaAI/elitea-testing-public#1772, not filed as a bug.
