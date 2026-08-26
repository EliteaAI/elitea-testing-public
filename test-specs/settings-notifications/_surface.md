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
| `notifications-delete-selected-button` | NEW additive `buttonTestId` prop on the inner `IconButton` (`EliteaAI/EliteaUI@30a15ac6`) — see the trap below | `DeleteEntityButton` |
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

**Trap — `DeleteEntityButton`'s `testId` prop lands on the WRAPPER SPAN, not the button.**
`src/components/DeleteEntityButton.jsx` renders `<Tooltip><Box component="span"
data-testid={testId}><IconButton disabled={…}>` — the span wrapper exists because MUI
Tooltip cannot wrap a disabled button. So a locator built on `testId` is a `<span>`:
`is_disabled()` on it is ALWAYS `False` and any enabled/disabled assertion silently
passes-as-enabled. Caught the expensive way during ELITEA-2255 implementation (one
rerun). The fix, now in place for every future caller: an additive `buttonTestId` prop
on the inner `IconButton` (`EliteaAI/EliteaUI@30a15ac6`) — pass `buttonTestId` INSTEAD
of `testId` when the test needs the button's own state, so exactly one testid exists and
it is on the button. Existing `testId` callers are untouched.

## Read/unread VISUAL distinction — confirmed live 2026-08-26 (ELITEA-2258)

Supersedes the 2026-08-04 note above ("no visible DOM indicator … not usable as a
reliable test signal"): the distinction **is** observable and assertable, just not as an
attribute. Measured on the same row before/after a real mark-read (dark theme):

| Element | Unread | Read |
|---|---|---|
| message `<Typography>` | `rgb(255, 255, 255)` | `rgb(169, 183, 193)` |
| date `<Typography>` | `rgb(255, 255, 255)` | `rgb(169, 183, 193)` |
| in-message `<Link>` | `rgb(41, 184, 245)` | `rgba(41, 184, 245, 0.7)` |

Source: `NotificationTable.jsx:219` (`color={row.is_seen ? 'text.primary' :
'text.secondary'}`) for the date cell, `NotificationListItemMessage.jsx:11,60` for the
message text and link. **Assert the DIFFERENCE, never the literal rgb** — these are
theme tokens.

- ⚠️ `notification-message-text` is the wrapper `<Box>`; its computed `color` is the
  inherited default and does NOT change with `is_seen`. The colour lives on the inner
  `<Typography>`, which has **no testid yet** — ELITEA-2258's AFS specs a caller-supplied
  `messageTestId` → `testId` prop thread (`NotificationTable.renderCell` →
  `NotificationListItem` → `NotificationListItemMessage`) plus a plain
  `notification-date-text` attribute on the call-site date `<Typography>`.
- Read `getComputedStyle` via `locator.evaluate("el => window.getComputedStyle(el).color")`
  — precedent `automation/pages/agent_form_page.py:230`. It is a READ, not a
  substitution; declare it when the reviewer's `\.evaluate\(` grep hits.
- **Clicking a notification row does NOT mark it read** (confirmed: zero
  `/notifications/notifications/prompt_lib/` requests after a row-message click).
  `GridTableRow` has no row-level `onClick` beyond checkbox selection, and the message
  `<Link>` is a plain `target="_blank"` anchor with no mark-seen handler. The only
  in-product transitions are the toolbar toggle (table) and the per-row hover button in
  the sidebar popover (`NotificationListItem`, `context === 'list'` only).
- Page 1 carried **50 of 50 unread** this session — a read row must be produced by the
  test itself (mark one read, restore it in cleanup).

## Search field — confirmed live 2026-08-26 (ELITEA-2264)

- `notifications-search-input` filters **server-side**: the list GET gains `search=<term>`
  (alongside `sort_by=created_at`), debounced 600 ms, and only when the debounced value is
  **≥ 2 chars** (`MIN_SEARCH_LENGTH` in `NotificationCenter.jsx`). A 1-char query fires no
  request and leaves the list unfiltered — verified with `"8"` → still `"1 - 50 of 89"`.
- Worked example: `"182606"` → `"1 - 2 of 2"`, both rendered rows containing the term.
  `search_input.fill("")` (real Playwright fill) correctly clears the React-controlled
  input and restores `"1 - 50 of 89"`.
- Totals this session: **89 notifications** (67 on 2026-08-04, 89 on 2026-08-26 — it grows;
  never hardcode a total or a search term, derive the term from the list response).

## Environment gap blocking index-triggered notifications (ELITEA-2265, 2026-08-26)

The test user's personal project has **zero toolkits** (`/toolkits/all` → `/toolkits/create`)
and **zero credentials** (`/credentials/all` → `/credentials/create-credential`). The
`artifact` toolkit form's vector-store select (`toolkit-credential-select-pgvector-combobox`)
offers only `"None"`, and no `PGVECTOR*` secret exists in `automation/config.py` / `.env.test`.
⇒ no indexable toolkit can be created ⇒ `index_data_changed` notifications cannot be produced
from the test side. Any case whose trigger is an index run is `blocked` until a vector-store
credential + indexable toolkit are provisioned (human/lead decision).

## Resolved/added during ELITEA-2258 + ELITEA-2264 implementation (2026-08-26, test-automation-engineer)

**Testids added — `EliteaAI/EliteaUI@e0d98f4a` on `automation/testids`, NOT yet on `main`.**
Both close the "the colour lives on a node with no testid" gap the ELITEA-2258 analysis
flagged above:

| Testid | How | Component |
|---|---|---|
| `notification-message-typography` | caller-supplied additive prop thread — `NotificationTable.jsx` `renderCell` passes `messageTestId` → `NotificationListItem` forwards it as `testId` → `NotificationListItemMessage` renders `data-testid` on the EXISTING `<Typography sx={{ color: textColor }}>` | shared with the sidebar popover, so caller-supplied: `context='list'` gains nothing |
| `notification-date-text` | plain `data-testid` attribute | `NotificationTable.jsx`'s own `created_at` `renderCell` (page-owned file) |

Prop plumbing only — no new DOM node, no hook, no removed markup.

**Row click: use the DATE cell, not the message cell.** The message `<Typography>` embeds
an inline `<Link target="_blank">`, so a centre-click can land on the anchor and open a
tab (that is the case's *other* branch, "open the linked entity"). The date cell is
link-free and in the same row — an unambiguous row click. Confirmed live: clicking it
issues zero `/notifications/notifications/prompt_lib/` `PUT`s and changes neither colour
nor `is_seen`.

**Clearing the search field issues NO request** (cost one rerun to learn). RTK-Query still
holds the unfiltered query fetched on page load (inside `keepUnusedDataFor`), so the full
list comes back from cache and `expect_response(<unfiltered list GET>)` times out. Wait on
the rendered row count returning to baseline instead; the network evidence worth asserting
is the ABSENCE of a stale `search=`-carrying request. (Typing a term still fires a real
GET, so `search_notifications()` legitimately waits on a response.)

**Proving a request did NOT fire, without a sleep:** `page.expect_request(<predicate>,
timeout=N)` wrapped in `try/except PlaywrightTimeoutError` — the timeout IS the verdict.
Used for both the row-click-no-`PUT` probe and the `MIN_SEARCH_LENGTH` boundary. Bounded
at 4 s, comfortably past the product's 600 ms debounce.

**Read/unread colour polarity (source, not just observation):** both
`NotificationTable.jsx`'s date cell and `NotificationListItemMessage.jsx`'s message text
use `is_seen ? 'text.primary' : 'text.secondary'` — so in this dark theme READ is
`text.primary` = `rgb(169, 183, 193)` and UNREAD is `text.secondary` =
`rgb(255, 255, 255)`. Counterintuitive naming; assert the difference, never the token.

## In-message LINKS — where they point and what clicking one does (ELITEA-2261/2262/2263, confirmed live 2026-08-26)

**Clicking a notification link opens a NEW TAB.** `NotificationListItemMessage.jsx` renders
every link segment as `<Link href={resolvedHref} target="_blank" rel="noopener noreferrer">`
with **no `onClick`**. Consequences for any case on this surface:
- automation must use `page.expect_popup()` / `context.expect_page()` — an in-tab
  `wait_for_url` will hang;
- the notifications page is never left, so a case step saying "navigate back" is drift;
- **no mark-seen mutation fires** — clicking a link does NOT mark the notification read
  (colour identical before/after + reload: `rgb(255,255,255)` both times on notification
  `109821`). Clarification #1786, sibling of #1784 (row click, same behaviour).

**The `<Link>` has NO testid** (not on `main`, not on `automation/testids`). Needed:
`notification-message-link`, added as a **caller-supplied additive prop** (`linkTestId`)
threaded `NotificationTable.jsx` `renderCell` → `NotificationListItem` →
`NotificationListItemMessage`, exactly like the existing `messageTestId`
(EliteaAI/EliteaUI@e0d98f4a). A STATIC value is right — disambiguate by row scoping:
```python
ROW_MESSAGE_LINK = ('[data-testid="notification-row"]:has([data-testid="notification-checkbox-{}"]) '
                    '[data-testid="notification-message-link"]')
```
Every row on this account renders exactly **one** `<a target="_blank">` (checked across all
89 rows' rendered pages), so the scoped selector is unambiguous. `parseMessage()` could emit
several link segments in principle — index the suffix only if a case ever needs it.

**Where each event type's link points** (`resolveHref()` in
`entities/notifications/lib/helpers/notification.helpers.js`, all URLs prefixed with the
notification's OWN `project_id`, not the user's selected project):

| event_type | href shape | Landing URL after the SPA's project switch |
|---|---|---|
| `chat_user_mentioned` / `chat_user_added` | `/{project_id}/chat?conversation={meta.conversation_id}&message_id={meta.message_id}` | `/chat/{conversation_id}` (query rewritten to `?name=…` when it resolves) |
| `index_data_changed` | `/{project_id}/toolkits/indexes/{meta.toolkit_id}?index_name={meta.index_name}` | `/toolkits/indexes/{toolkit_id}` — or silently the LIST when the toolkit is gone |
| `bucket_expiration_warning` | `/{project_id}/artifacts?bucket={meta.bucket_name}` | `/artifacts?bucket={name}` |
| `personal_access_token_expiring` | `/settings/tokens` | |
| `budget_*` | `/{project_id}/settings/usage` (+ `?scope=user` for member budgets) | |
| `agent_unpublished` | `/{project_id}/agents/all/{app_id}/{version_id}?viewMode=owner` | |

**The `/{projectId}` prefix is consumed by the project switcher** — the popup's final URL has
no project segment. Wait for the path to settle (`/chat/\d+`) before asserting; a
`domcontentloaded`-only wait reads the pre-switch URL and lies (cost one probe round).

### ⚠️ Notification targets ROT — liveness must be discovered, never assumed
The history is real user history and the entities it references get deleted. Measured
2026-08-26:

| Type | Rows | Targets still alive |
|---|---|---|
| `chat_user_mentioned` | 12 | some — `5883` ("Hello", 18 msgs) and `4165` ("HI Chat", 29 msgs) open; `7839`, `4205` are gone |
| `bucket_expiration_warning` | 41 | few — most name autotest buckets the retention policy already deleted; `autotest-1816-182606` survives |
| `index_data_changed` | 7 | **none** — toolkits 30/118/137/146 all 400; surviving toolkits in that project are ids 850–890 |

⇒ any "click the link and check the target opened" spec must pick its row by **probing the
product for a live target first** (transit read), and fail loudly when none exists. Picking
"the newest row" is a guaranteed red — the newest bucket warning today targets a deleted
bucket.

### Discriminators — did the target actually open?
| Surface | Opened | Broken/dead target |
|---|---|---|
| Chat | `chat-message-list` visible, `chat-message-item` ≥ 1, **no** `alert-dialog-content` | `alert-dialog-content` present ("Conversation not found — … does not exist in your project or you don't have access to it"), backend `400` on `/elitea_core/conversation/prompt_lib/{proj}/{conv}` |
| Artifacts | `artifacts-bucket-row-{name}` visible **and** the bucket tree expanded (`artifacts-bucket-tree-empty-label-{name}` or a file list) | URL still carries `?bucket=…` but no such bucket row — **URL alone is not an assertion** |
| Toolkit indexes | (never reached — see below) | URL silently falls back to `/toolkits/indexes` (the LIST), **no error message at all**, `400` on `/elitea_core/tool/prompt_lib/{proj}/{toolkit}` |

Note the inconsistency worth knowing: chat shows an explicit not-found dialog, toolkits fail
silently to a list. Not filed as a defect (out of ELITEA-2262's scope), recorded here.

### The `alert-dialog-content` handle
`src/components/AlertDialog.jsx` already carries static `alert-dialog-content` /
`alert-dialog-confirm-button` (both on `main`). It is app-wide/shared, so use it for the
**absence** assertion on the chat popup (canon #511 extension: absence assertions are
references) — there is no chat-specific not-found testid and none is needed.

### Search-cache trap when scripting this surface
Re-typing a term the session already fetched serves from the RTK-Query cache and fires **no**
request — `page.wait_for_response(... "search=")` then times out. Wait on the **rendered row
count** instead (mirrors the existing note about clearing the field). Cost one failed probe.

## Resolved/added during ELITEA-2261 + ELITEA-2263 implementation (2026-08-26, test-automation-engineer)

**Testid added — `EliteaAI/EliteaUI@9733742f` on `automation/testids`, NOT yet on `main`.**
Closes the "the in-message `<Link>` has no testid" gap flagged above:

| Testid | How | Component |
|---|---|---|
| `notification-message-link` | caller-supplied additive prop thread — `NotificationTable.jsx` `renderCell` passes `linkTestId` → `NotificationListItem` forwards it → `NotificationListItemMessage` renders `data-testid={linkTestId}` on the EXISTING `<Link target="_blank">` | shared with the sidebar popover, so caller-supplied (`context='list'` gains nothing) |

Prop plumbing only — no new DOM node, no hook, no removed markup (zero-functional-impact
greps: 0 hits on hooks, 0 on new nodes, the single `-` line is the destructure line itself).
The scoped constant `NotificationCenterPage.ROW_MESSAGE_LINK` is live and unambiguous —
both specs assert `get_row_link_count(id) == 1` before using it, and both passed.

**⚠️ CORRECTION to the "the `/{projectId}` prefix is consumed by the project switcher"
claim above — it is consumed ONLY when a switch is actually required.** Measured live
2026-08-26 across the two implemented cases:

| Case | Notification project | Selected project | Landing URL |
|---|---|---|---|
| ELITEA-2261 (`chat_user_mentioned`) | 406 "Bugs & Features" | 399 "Private" | `/chat/5883?name=Hello` — segment **consumed** |
| ELITEA-2263 (`bucket_expiration_warning`) | 399 "Private" | 399 "Private" | `/399/artifacts?bucket=autotest-1816-182606` — segment **survives** |

⇒ any spec asserting a landing path on this surface must accept BOTH
`{prefix}/<route>` and `{prefix}/{project_id}/<route>` (exactly those two, nothing else) —
asserting only the stripped form is a guaranteed red whenever the notification happens to
belong to the currently-selected project. Cost one rerun to learn.

**Liveness probing is cheap through the existing API clients, no new client needed:**
`ConversationAPI(browser_cookies=_browser_cookies, project_id=<notification.project_id>)
.get_conversation_raw(id).status_code == 200` and
`ArtifactAPI(browser_cookies=_browser_cookies, project_id=…).bucket_exists(name)`. Both
take `project_id` in the constructor, which matters because the notification's project is
NOT necessarily `settings.elitea_project_id`. Precedent for constructing a per-project
client inside a spec: `tests/ui/chat/test_delete_confirmation_modal_ui_validation.py:57`.

**Console capture must be attached to the CONTEXT, not the page** —
`collect_console_errors(page.context)` — because the flow's second half runs in a POPUP
that does not exist yet when the listener is bound. `BrowserContext.on("console")` covers
every page in the context, including popups opened later.

**Resolved/added during ELITEA-2261/2263 implementation (fix round 1, 2026-08-26):**
the popup's known background noise is a `403` on `/api/v2/secrets/secrets/default/{project}`
and a `500` on `/api/v2/elitea_core/project_info/prompt_lib/{id}/project-info`. Any spec
filtering them MUST pair the **status text with the URL marker** — never the URL alone,
which would swallow a future different status on the same resource
(`.agents/testing.md` § Merge gate). Shape:
`KNOWN_BACKGROUND_NOISE_SIGNATURES = (("status of 403", "/secrets/secrets/default/"), …)`,
pinned by `automation/tests/unit/test_notification_link_console_noise_filter_scope.py`.

Also measured live: the bucket page's artifacts reads carry the project as a **query
param**, not a path segment — `GET /artifacts/s3/?project_id=399&format=json` and
`GET /artifacts/s3/{bucket}?project_id=399&format=json`. (The test-side
`ArtifactAPI._buckets_url()` shape `/artifacts/buckets/default/{project_id}` is the API
client's own, NOT what the UI issues.) A `"/artifacts/" in url` response listener also
catches ~35 Vite dev-server module fetches under `/src/[fsd]/features/artifacts/` — filter
with `"/src/" not in url` before using them.

**Live targets that worked this session (they rot — always discover at runtime):**
mention notification `109487` → conversation `5883` ("Hello", project 406);
retention warning `111978` → bucket `autotest-1816-182606` (project 399, empty bucket,
proved OPEN via `artifacts-bucket-tree-empty-label-autotest-1816-182606`).
