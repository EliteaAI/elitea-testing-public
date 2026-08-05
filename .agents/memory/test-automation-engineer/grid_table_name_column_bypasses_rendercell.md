---
name: grid-table name column bypasses renderCell
description: GridTableRow renders the 'name' field via GridTableRowNameCell, not the table's renderCell — a testid added inside renderCell's name branch is dead code
type: feedback
---

Any table built on the shared `entities/grid-table` primitives
(`GridTableRow`/`GridTableBody`/`GridTableHeader`) special-cases the column
whose `field` equals `nameField` (default `'name'`): `GridTableRow.jsx` does
`dataColumns = columns.filter(col => col.field !== nameField && col.field !==
'actions')` and renders that column through `GridTableRowNameCell` →
`DefaultNameCellContent`, **never** through the table's own `renderCell`
callback. So adding `data-testid="foo-name-cell"` inside a
`renderCell`/`column.field === 'name'` branch (the obvious move, mirroring
every other column) compiles, lints clean, and is simply never rendered —
an orphan testid in dead code.

Confirmed live on `TokensTable.jsx` (ELITEA-2280): `token-value-cell` and
`token-expiration-status` worked immediately (real `renderCell` branches);
`token-name-cell` produced a 10s `text_content()` timeout even though
`to_have_count(1)` on the row itself passed — the row existed, the cell
inside it didn't.

**Fix pattern (additive, shared-component safe):** thread a generic
`nameCellTestId` prop through `GridTableRow` → `GridTableRowNameCell` →
`DefaultNameCellContent`, applied to BOTH the loading-state `Typography` and
the `TypographyWithConditionalTooltip` (mutually exclusive branches, same
testid value — not a state-switched testid). The table then passes
`nameCellTestId="token-name-cell"` on its own `<GridTableRow>` call site,
same pattern as the pre-existing `checkboxTestId` prop. Optional prop,
defaults to `undefined` — zero behavior change for every other `GridTableRow`
caller (additive-only, confirmed safe to modify a ~15-consumer shared file).

**Preventive takeaway:** before adding a `data-testid` for any grid-table
name column, check whether the column's `field` matches `nameField` — if so,
skip `renderCell` entirely and thread through `nameCellTestId` instead.
