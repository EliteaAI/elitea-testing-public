---
name: Notification bulk mark-read/unread is ONE toggle button, not two
description: NotificationTableToolbar has a single mark-toggle button whose label flips by selection state; PUT bulk-mark endpoint + checkbox testid gap (ELITEA-2259)
type: feedback
---

## Surface

`Settings → Notifications` table toolbar (`NotificationTableToolbar.jsx`),
same surface as ELITEA-2257 (`notification_center_surface_and_grid_table_testid_prop.md`).

## Single toggle button, not two separate buttons

`NotificationTable.jsx` computes `shouldMarkAsRead = rows.some(row =>
selectedRowIds.has(row.id) && !row.is_seen)` (true if ANY selected row is
unread) and passes it to the toolbar as `markAsRead`. The toolbar renders
ONE `BaseBtn` whose `aria-label`/icon flip between `"Mark selected as
read"` and `"Mark selected as unread"` based on that boolean — there are
NOT two separate buttons. A TMS case describing "the Mark as read button"
and "the Mark as unread button" as distinct controls is describing this
toggle imprecisely, not a product defect (filed as clarification
EliteaAI/elitea-testing-public#1166). Also distinct from the SIMILAR-but-
different single-notification hover action in `NotificationListItem.jsx`
(sidebar bell popover), whose literal button text IS "Mark as read"/"Mark
as unread" — don't conflate the two surfaces' button copy.

## Bulk mark-seen API

`PUT /api/v2/notifications/notifications/prompt_lib/{project_id}` body
`{"ids": [...], "is_seen": <bool>}` → 200, invalidates the
`TAG_NOTIFICATIONS` RTK-Query tag (auto-refetches the list — no manual
reload needed to see the change; reload is only needed to prove
server-side persistence). Confirmed live: flips exactly the targeted ids'
`is_seen`, every other row's `is_seen`/`updated_at` untouched.

## Testid gaps (as of 2026-08-04, ELITEA-2259 exploration)

- Per-row checkbox: `GridTableRow.jsx` ALREADY accepts a `checkboxTestId`
  prop (wired onto the MUI checkbox's `data-testid`) — `NotificationTable.jsx`
  doesn't pass one at its `<GridTableRow>` call site yet. Precedent for the
  dynamic value: `ArtifactTable.jsx:527` uses
  `checkboxTestId={`artifacts-file-checkbox-${row.id}`}` — same pattern
  applies here (`notification-checkbox-${row.id}`).
- Toolbar mark-toggle button: only has a state-dependent `aria-label` today,
  no `data-testid` at all. New static testid needed
  (`notification-mark-toggle-button`) — value must stay constant across the
  read/unread toggle (only the label/aria-name changes), per the
  testid-stability canon.
- No DOM state indicator for read/unread exists (no dot/bold) — only a
  subtle text-color difference on the date cell. Verify `is_seen` via the
  list-fetch response body, not a DOM attribute, unless a future case adds
  one.

Full AFS: `test-specs/settings-notifications/l2_mark-selected-notifications-read-unread_ELITEA-2259.md`.
