# Surface digest — Notifications (bell quick panel + Notification Center)

Seeded 2026-07-24 by GAP-077 analysis. Handle cache for both notification
surfaces — the bell quick panel (`context="list"`) and the Notification
Center table at `/settings/notifications` (`context="table"`) — since they
share one entity component. Verify every handle below live before trusting
it; this is a cache, not a substitute for execution.

## Shared component: `NotificationListItem.jsx`

`src/[fsd]/entities/notifications/ui/NotificationListItem.jsx` renders in
exactly two places:
- `src/[fsd]/widgets/Notifications/ui/NotificationList.jsx` — the bell quick
  panel, `context` defaults to `'list'`.
- `src/pages/NotificationCenter/NotificationTable.jsx` — the Notification
  Center table, `context="table"` passed explicitly.

Behavior differs sharply by context:
- `context==='list'` (quick panel): the per-item hover "Mark as read/unread"
  toggle CAN render (`context === 'list' && isHovered` gate,
  `NotificationListItem.jsx:109`).
- `context==='table'`: the same gate is unconditionally false — the toggle
  **never** renders in the table, confirmed live with 66 real notifications
  loaded (mixed read/unread), hovering multiple rows.

## No testids anywhere on either surface (as of 2026-07-24)

Confirmed via live DOM inspection + `git grep` against fresh `origin/main`
and `origin/automation/testids`: **zero** `data-testid` attributes exist on
the bell button, the quick-panel container, any notification row (either
context), the per-row mark-toggle button, "Mark all as read", "View all", or
any Notification Center table row/toolbar control. This entire feature area
is untouched by the testid effort so far — every future case here will need
`add-data-testid` work; check this digest (updated as cases land) before
re-deriving.

### Bell button — non-obvious rendering gate

`NotificationButton.jsx` (`src/[fsd]/widgets/sidebar-root/ui/button/NotificationButton.jsx`)
is only mounted by `SidebarBody.jsx` behind
`{!sideBarCollapsed && <Buttons.NotificationButton />}`. When the sidebar is
collapsed (icon-only rail), the bell — and its only current marker,
`data-tour="sidebar-notifications"` — is **absent from the DOM entirely**,
not just visually hidden. `sideBarCollapsed` comes from
`useSelector(state => state.settings.sideBarCollapsed)`, persisted across
sessions. **Any test that opens the quick panel must first assert/force the
sidebar into its expanded state** (e.g. via the `sidebar-toggle` testid,
which DOES exist — `data-testid="sidebar-toggle"` on the IconButton with
`data-tour="sidebar-logo"`) rather than assuming a fresh session starts
expanded. Confirmed live the hard way this run: clicking a generic `svg`
selector during exploration silently toggled the sidebar into COLLAPSED,
which made the bell vanish from a subsequent DOM query until re-expanded.

- **testid needed**: `notification-bell-button` on the `Box` at
  `NotificationButton.jsx:68` (the `onClick={onClickNotificationButton}`
  wrapper around `BellIcon`). Not a shared/generic component — plain
  hardcode, no `testId` prop indirection needed.

### Quick panel container

MUI `Popover`, `id="notificationList"` (`NotificationList.jsx:86`). The
native `id` is stable/unique but is a raw CSS-id selector, not a compliant
testid-only primary handle per this project's locator policy — no case has
needed a container-level testid yet (every assertion so far routes through
row/toggle-level testids, which are unique on their own). Flag if a future
case needs to assert the panel's own open/closed state directly (e.g. via
the header's "Close notifications" button, itself also untested by testid
today).

### Row identity + read/unread state

- **testid needed**: `notification-item-row` (flat, same name across every
  row instance — a repeated-list-item pattern) + a `data-seen` state
  attribute mirroring `notification.is_seen`, per the "testid = stable
  identity, state via `data-*`" rule
  (`data-testid="notification-item-row" data-seen={notification.is_seen}` on
  `NotificationListItem.jsx:89`'s root `Box`). Disambiguate "an unread row" /
  "a read row" via `[data-testid="notification-item-row"][data-seen="false"]`
  / `[data-seen="true"]` + `.first()`.
- This testid will appear in BOTH contexts once added (same shared
  component) — that's expected, not a scope violation, since it's one
  component's own identity, not a feature-scoped leak into a generic
  `shared/` widget.

### Per-row hover mark-toggle button (quick panel only)

- **testid needed**: `notification-item-mark-toggle-button`
  (`NotificationListItem.jsx:115-121`, the `BaseBtn` inside the hover gate).
  Single flat name is correct — only one instance ever renders at a time
  (one row hoverable at once). The testid itself never changes; only its
  `aria-label` (`"Mark as read"`/`"Mark as unread"`) and icon
  (`MarkReadIcon`/`MarkUnreadIcon`) flip with `shouldMarkAsRead`. Assert on
  `aria-label`, never expect the testid itself to differ.

### Structural finding — the "unread → toggle → read" round trip does NOT persist the row in place

Confirmed live (GAP-077): `NotificationList.jsx`'s query hardcodes
`params: { only_new: true }`. The mark-toggle mutation
(`useNotificationBulkMarkSeenMutation`, `invalidatesTags: [TAG_NOTIFICATIONS]`)
triggers an immediate refetch of that same unseen-only query, so a row just
marked read is **removed from the quick panel**, not restyled in place — and
`NotificationList.jsx` never wires `onNotificationSeenChange`, so there's no
optimistic update either. **Practical consequence for any future case on
this surface**: you can never hover an already-read row in the quick panel —
by the time a row is `is_seen:true`, the panel's own query has already
excluded it. The "Mark as unread" branch of the per-item toggle
(`shouldMarkAsRead===false`) is reachable ONLY via a directly-injected
already-seen row that predates the query refetch (i.e. never, through normal
UI flow) — see filed clarification
[EliteaAI/elitea-testing-public#1035](https://github.com/EliteaAI/elitea-testing-public/issues/1035).
Do not write a case assuming a read row persists in the quick panel; route
read↔unread round-trip assertions to the Notification Center's checkbox flow
instead (ELITEA-2259).

### API contract (both surfaces call the same endpoints, `src/api/notifications.js`)

- `GET /notifications/notifications/prompt_lib/{project_id}` — list.
  Params: `limit`, `offset`, `sort_by`, `sort_order`, `search`, plus whatever
  is in `params` (the quick panel always sends `only_new: true`; the
  Notification Center table sends none of these `only_new`-style filters,
  full history).
- `PUT /notifications/notifications/prompt_lib/{project_id}` body
  `{"ids": [...ids], "is_seen": bool}` — bulk mark seen/unseen. Same endpoint
  for: the quick panel's single-row hover toggle (`ids: [one id]`), the quick
  panel's "Mark all as read" (`ids: 'all'`), and the Notification Center
  table's checkbox-driven bulk toggle (`ids: [selected ids]`).
- `DELETE /notifications/notifications/prompt_lib/{project_id}` body
  `{"ids": [...]}` — bulk delete (Notification Center toolbar trash icon,
  not yet exercised by any case as of this digest).
- **Backend parameter-parsing quirk (tangential, but a real trap for fixture
  code)**: passing `only_new=false` as a query string behaves IDENTICALLY to
  `only_new=true` — both return only unseen notifications. Only OMITTING the
  `only_new` parameter entirely returns the full read+unread set. Confirmed
  via a 3-way live comparison this run. Irrelevant to any UI assertion (the
  UI never varies this param), but relevant if you write a test-data seeding
  helper directly against this endpoint: to read the FULL list (to discover
  candidate ids, or to check a specific id's current `is_seen`), omit
  `only_new` — don't pass `only_new=false` expecting the unfiltered set.

## Shared live backend — seeding discipline (important)

The notification list is **real, shared, mutable data** on the DEV backend
tied to `${TEST_USER}`'s personal project — not project-scoped test
fixtures. Multiple concurrent cases in the same batch may need an unread (or
read) notification to exist simultaneously. **Never use a page-wide bulk
action** ("Mark all as read", or any future "mark all as unread") as part of
a test or exploration — GAP-077's own exploration did this once by accident
(a mis-targeted click hit "Mark all as read" instead of the adjacent "View
all" — both are plain `<button>`s with no distinguishing testid, see the
Concrete Handles gap above) and zeroed out all 43 unread notifications
project-wide before the exploration caught it and restored the exact
original ids via a direct API call. **Seed and restore your own specific
notification id(s) via direct `PUT` calls** — read the current `is_seen`
value first, mutate for the test, restore it in teardown.

## Notification Center table (`/settings/notifications`, `NotificationTable.jsx`)

Built on the shared `grid-table` entity (`GridTableRow` etc., already used
by Secrets/Users/Tokens/Artifacts/BucketAccess tables elsewhere in this
codebase) — but `NotificationTable.jsx`'s call site does **not** pass a
`dataTestId`/`checkboxTestId` to `GridTableRow`, so rows and their checkboxes
are testid-less here too (unlike some of `GridTableRow`'s other consumers —
check each call site independently, this prop is opt-in per caller). Not
otherwise explored beyond confirming the hover-toggle absence (GAP-077's
step 8) — ELITEA-2255 through ELITEA-2261 (same batch) cover this page's own
layout/pagination/search/checkbox-toggle/navigation behavior in depth; read
their AFS files once they land rather than re-deriving this page from
scratch.
