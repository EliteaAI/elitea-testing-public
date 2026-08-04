---
name: Notification Center grid-table testid pattern
description: NotificationTable.jsx testid provenance, the sort_by=created_at vs only_new=true response-predicate gotcha, and the GridTablePagination Next-button prop pattern (ELITEA-2257).
type: feedback
---

## Surface

`Settings → Notifications` (`/settings/notifications`), built on
`src/pages/NotificationCenter/NotificationTable.jsx` + the shared
`src/[fsd]/entities/grid-table/ui/` components (`GridTableBody`,
`GridTableRow`, `GridTablePagination`). Had **zero** pre-existing testids
across the whole notification-rendering tree before ELITEA-2257.

## Testid provenance — check the shared component's props before adding new ones

`GridTableBody` and `GridTableRow` already destructure a `'data-testid':
dataTestId` prop and render it — `NotificationTable.jsx` just never passed
one at its `<GridTableBody>`/`<GridTableRow>` call sites. Wiring these is a
one-line addition per call site, not a component change. `GridTablePagination`
had NO testid threading at all (unlike its siblings) — that one needed an
actual new prop (`nextButtonTestId`, wired only onto the "Next" `IconButton`,
per locator-scope discipline — "Prev" stays untouched since no case exercises
it). **Lesson: grep the shared component's own source for existing
`data-testid`/`TestId` prop destructuring before assuming a new prop is
needed** — `GridTableHeader` has `selectAllCheckboxTestId`/
`columnTestIdPrefix` for the same reason; this family of shared components is
inconsistent about which of them already support it.

## Response-predicate gotcha: two GETs share the same URL prefix

`GET /api/v2/notifications/notifications/prompt_lib/{id}` fires for BOTH:
- an unread-count probe: `?only_new=true&only_total=true&limit=1&offset=0`
  (fires once, early, on page mount — unrelated to what the table renders)
- the actual paginated list fetch the table reads from:
  `?limit=50&offset=0&sort_by=created_at&sort_order=desc`

A response predicate matching only the URL prefix
(`/notifications/notifications/prompt_lib/`) will resolve on the FIRST of the
two — the unread probe — not the list fetch the table body actually needs.
Add `sort_by=created_at` to the predicate (present only on the list fetch) to
avoid a race where `expect_response` returns before the rows have arrived.
See `NotificationCenterPage._is_notifications_list_response()`.

## Data shape confirmed live (2026-08-05, DEV backend, project 399)

67 notifications across 2 pages @ 50/page. All 4 case-named types present
plus extras (`personal_access_token_expiring`, `agent_unpublished`). Index
type renders BOTH "is successfully created: {...}" and "is successfully
reindexed. {...}" variants — either satisfies the AFS's step 5. A 5th
"is failed." index outcome also observed (undocumented by the case,
informational only, not asserted).
