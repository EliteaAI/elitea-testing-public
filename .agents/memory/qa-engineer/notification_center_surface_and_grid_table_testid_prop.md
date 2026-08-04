---
name: Notification Center surface + grid-table shared testid prop
description: Settings→Notifications has zero testids; GridTableRow/Body already accept a data-testid prop, just unwired
type: project
---

Analysed ELITEA-2257 (2026-08-04). Key findings for anyone touching
`/settings/notifications` (`NotificationCenter`) or its sibling sidebar-bell
popover (`widgets/Notifications/`, same `NotificationListItem`/
`NotificationListItemMessage` components via a `context` prop):

- **Zero `data-testid` anywhere** in `NotificationCenter.jsx`,
  `NotificationTable.jsx`, `NotificationTableToolbar.jsx`,
  `NotificationListItem.jsx`, `NotificationListItemMessage.jsx`,
  `LegacyNotificationMessage.jsx`.
- **`GridTableRow`/`GridTableBody`** (`src/[fsd]/entities/grid-table/ui/`,
  used by several list surfaces, not just notifications) **already accept a
  `'data-testid': dataTestId` prop and render it** — but `NotificationTable.jsx`'s
  call sites don't pass one. Adding a testid there is "wire the existing prop
  at the call site", not a component change. Check this pattern before
  assuming a shared grid-table surface needs a full add-data-testid pass —
  it may already be half-wired.
- **`GridTablePagination.jsx` has NO such prop** — its Next/Prev `IconButton`s
  have no `aria-label` either. A real component change if a case needs to
  paginate.
- **Live DEV backend (`personal_project_id` 399 "Private") already carries
  67 real notifications** spanning `chat_user_mentioned`, `chat_user_added`,
  `bucket_expiration_warning` (backend-cron-only, no on-demand trigger),
  `index_data_changed` (both "created"/"reindexed" message variants + a
  "failed" outcome), `personal_access_token_expiring`, `agent_unpublished` —
  all rendering clean text (no `undefined`, no unresolved `[text]()` link
  tokens, no literal HTML). Useful as read-only fixture data for any future
  notification-rendering case instead of trying to seed
  `bucket_expiration_warning`/`index_data_changed` (impractical on demand).
- Message text uses a custom `[visible text]()` markdown-link-lite syntax
  parsed by `parseMessage()` in
  `entities/notifications/lib/helpers/notification.helpers.js` — an
  unresolved `[...]()` token surviving to the DOM would be the concrete
  "broken" rendering failure mode on this surface.

Full AFS: `test-specs/settings-notifications/l2_notification-text-content-renders-correctly_ELITEA-2257.md`,
digest: `test-specs/settings-notifications/_surface.md`.
