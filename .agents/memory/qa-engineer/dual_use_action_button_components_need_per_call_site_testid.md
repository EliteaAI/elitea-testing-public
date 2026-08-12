---
name: Dual-use action-button components need per-call-site testid
description: EditUsersButton/DeleteUserButton (Settings → Users) render both as a header batch-action and a per-row action from the same component — one new testId prop, two distinct values needed at two call sites
type: feedback
---

## The situation

Analysing ELITEA-2292 (Settings → Users page layout), found `EditUsersButton.jsx`
and `DeleteUserButton.jsx` (`src/[fsd]/features/settings/ui/users/`) are each
rendered TWICE from the same component: once in `Users.jsx`'s `DrawerPageHeader`
`extraContent` as a batch action (`isBatchEdit`/`useSecondaryButton`, disabled
until a row is selected), and once per row inside `UsersTable.jsx`'s
`renderActions` (plain instance, always enabled once permission-gated). Neither
usage carries any testid today.

## Why it matters

When specifying a testid for a component like this, "add a `testId` prop" is
not enough — the AFS/implementer must name TWO distinct testid values
(`users-header-edit-button` vs `user-row-edit-button`) and confirm BOTH call
sites pass their own value. A single shared constant or a prop default would
make every row's edit icon collide with the header's batch-edit icon (same
testid, multiple elements), breaking every locator that expects exactly one
match.

## The reusable check

When a feature component appears more than once in the same page's component
tree (grep `<ComponentName` count in the page + its children), check whether
each call site needs its own testid value before writing "add a `testId`
prop" as a single line in the AFS handles table — split it into one row per
call site instead, same as this AFS's `users-header-edit-button` /
`user-row-edit-button` pair.

## Where else to expect this

The `GridTableRowDataCell.jsx` shared component (used by `UsersTable`,
`TokensTable`, `SecretsTable`, `BucketAccessTable` and likely other
grid-table consumers) has NO testid prop of any kind — unlike
`GridTableHeader.jsx` (`columnTestIdPrefix`) and `GridTableRow.jsx`
(`nameCellTestId`/`checkboxTestId`/`data-testid`), which already got this
treatment for ELITEA-2277's Personal Tokens work. A future case that needs
to assert row data-cell CONTENT (not just header/name/actions) will need to
add a `dataCellTestIdPrefix` prop mirroring `columnTestIdPrefix`'s
`{prefix}-column-header-{field}` shape as `{prefix}-column-value-{field}` —
this is now spec'd in ELITEA-2292's AFS Concrete Handles table as a
shared-component change (optional prop, additive, doesn't affect other
consumers).
