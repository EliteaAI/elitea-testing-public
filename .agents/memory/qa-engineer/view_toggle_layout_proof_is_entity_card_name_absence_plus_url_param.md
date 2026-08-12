---
name: View toggle layout proof — entity-card-name absence + URL param
description: Table-view column headers carry NO testid on shared list pages; prove layout via entity-card-name count + ?view= param instead
type: project
---

## The pattern (Agents/Pipelines/MCPs/Toolkits/Credentials — any list page using
the shared `ViewToggle.jsx` + `CardList.jsx` + `DataTable.jsx`/`DataCards.jsx`)

Every one of these list pages shares the same view-toggle machinery: a
`ViewToggle` component writing `?view=table`/`?view=cards` to the URL
(`SearchParams.View`, read back by `useIsTableView.js`), driving
`CardList.jsx`'s `shouldRenderTable` ternary between `DataTable` (table) and
`DataCards` (card grid). No XHR fires — pure client-side re-render.

**Don't go looking for a table-row or column-header testid to prove "layout
switched to table format" — it almost certainly doesn't exist.**
`GridTableHeader.jsx` only emits `data-testid` on column header cells when the
caller passes `columnTestIdPrefix`; `DataTable.jsx` only does that for MCPs
(`isMCPs ? 'mcp-table' : undefined`) — every other entity (Pipelines, Agents,
Toolkits, Credentials) gets `undefined`, so the table's headers/rows are
testid-free by default.

**The stable, testid-only proof that actually exists everywhere:** the
`entity-card-name` testid (`Card.jsx:210`) is rendered ONLY by the card-view
`Card` component — `DataTable` never renders it. So:
- Card view active → `entity-card-name` count > 0 (matches the visible entity
  count).
- Table view active → `entity-card-name` count == 0.

Combine with the `?view=table`/`?view=cards` URL query param (a page-URL
check, not a locator — no policy issue) for a belt-and-braces layout
assertion. Confirmed live 2026-08-08 on the Pipelines dashboard (ELITEA-2024):
12 pipelines → `entity-card-name` count 12 in card view, 0 in table view,
back to 12 on switch-back.

If a future case genuinely needs a table-row-level assertion (not just "did
the layout switch"), that's a real testid gap — thread
`columnTestIdPrefix`/a row `data-testid` at the specific `DataTable.jsx` call
site for that entity type via `add-data-testid`, scoped to what the test
actually touches (don't add it "while you're in there").
