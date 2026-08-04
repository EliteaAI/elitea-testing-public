---
name: GridTableRow/GridTableBody already accept an unwired data-testid prop
description: Shared grid-table components already support a data-testid prop — check before assuming a full add-data-testid pass is needed on a new grid-table-based surface
type: reference
---

## What was found

While automating ELITEA-2257 (Settings → Notifications, 2026-08-05), the
analyst found that `GridTableRow` and `GridTableBody`
(`EliteaUI/src/[fsd]/entities/grid-table/ui/`) — shared grid-table components
used by more surfaces than just notifications — already accept and render a
`data-testid` prop. It was simply **unwired** at the call site
(`NotificationTable.jsx`): the prop existed on the component, nothing passed
it in.

`GridTablePagination.jsx` did NOT already have this — a new `nextButtonTestId`
prop had to be added there, scoped to the Next `IconButton` only (Prev left
untouched).

## Why this matters for planning

Before dispatching `add-data-testid` work for any OTHER grid-table-based
surface, check whether the shared component already exposes the prop and
only the call site needs wiring (cheap) vs. needing a new prop added to the
shared component itself (same effort as before, but touches a shared file
reviewed as a pattern per `.agents/testing.md`). Grep
`EliteaUI/src/[fsd]/entities/grid-table/` for existing `testId`/`data-testid`
prop plumbing before scoping a new case's testid work as "same as usual".

## Provenance

Case: ELITEA-2257. AFS:
`test-specs/settings-notifications/l2_notification-text-content-renders-correctly_ELITEA-2257.md`.
Testid commit: `EliteaAI/EliteaUI@3b8e55ff`.
