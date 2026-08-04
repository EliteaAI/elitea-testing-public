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
- Pagination is `limit`/`offset`, sortable by `created_at` — no `search` param
  applied unless `search.length >= 2` (`MIN_SEARCH_LENGTH` in
  `NotificationCenter.jsx`), debounced 600ms.
