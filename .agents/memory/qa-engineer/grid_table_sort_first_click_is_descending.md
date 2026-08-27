---
name: Grid-table first header click sorts DESCENDING (default is already asc)
description: useTableSort defaults to name/asc, so the first click on the default column flips to desc — case texts get this backwards
type: feedback
aliases: [useTableSort, sort direction, column header sort, first click ascending, grid-table sorting, sort arrows]
tags: [area/elitea-ui, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

Every EliteaUI grid table (personal tokens, credentials, secrets, MCPs, notifications)
sorts through the shared `useTableSort`
(`src/[fsd]/entities/grid-table/lib/hooks/useTableSort.hooks.js`). Callers pass
`{ defaultField: 'name', defaultDirection: 'asc' }`, so **the table is already sorted
ascending before any interaction**. The toggle is:

```js
direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc'
```

⇒ the **first** click on the default column yields **descending**; the second yields
ascending. TMS case texts routinely assert the opposite (ELITEA-2279 did) — that is
case-text drift, not a product bug. File a CLARIFICATION and assert the live contract
(#1880 is the worked example).

## What to assert, and what not to

- **Assert row order**, computed relationally: `observed == sorted(observed, key=str.lower)`.
  The hook lower-cases strings (lines 50-53), so a case-*sensitive* `sorted()` builds a
  wrong expectation against a correct product.
- **Null-valued sort fields partition**: `null` goes **last in asc, first in desc**
  (lines 45-47). For a date column with "Never" (= `null`) rows, the durable invariant is
  *dated rows before Never rows in asc, reversed in desc* — not a literal name list.
- ⚠️ **Never assert the sort-arrow rotation.** It is a CSS `transform` behind
  `transition: transform 0.2s ease` (`GridTableHeader.jsx:132-137`); a `getComputedStyle`
  read straight after the click catches it mid-animation
  (observed `matrix(0.907747, 0.419517, ...)`). The active-column `opacity 1 vs 0.7` cue is
  equally unusable — `&:hover` also sets it to 1.
- Sorting is **client-side** — no request fires on a header click. Wait on the reordered
  DOM, never on a response or a sleep.

## Free handles

`columnTestIdPrefix` makes `GridTableHeader` emit BOTH `{prefix}-column-header-{field}`
and `{prefix}-sort-icon-{field}` — the latter only for `sortable: true` columns. So a
sortability case needs **zero** new testids, and gets a natural absence assertion on the
non-sortable columns. (This is the orphan-testid question in issue #1705.)

Related: [[elitea_settings_two_distinct_empty_states]]
