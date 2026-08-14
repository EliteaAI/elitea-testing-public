---
name: MUI v7 TablePagination testid wiring
description: Use slotProps (select/displayedRows/actions.previousButton/nextButton), not deprecated SelectProps/backIconButtonProps
type: feedback
---

Project is on `@mui/material@^7.0.2`. `TablePagination`'s rows-per-page
selector, page-range label, and prev/next buttons cannot take a plain
`data-testid` prop directly — they're internal slots. Confirmed by reading
`node_modules/@mui/material/TablePagination/TablePagination.js` (ELITEA-2312
analysis, 2026-08-05):

- Rows-per-page `<Select>`: `slotProps={{ select: { 'data-testid': '...' } }}`
  — NOT the deprecated `SelectProps` (still works but flagged deprecated in
  propTypes comments, prefer the current form for new code).
- Page-range label ("1–3 of 3"): `slotProps={{ displayedRows: { 'data-testid':
  '...' } }}` — a dedicated `displayedRows` slot exists (`useSlot('displayedRows',
  ...)`), no need for a custom `labelDisplayedRows` render-prop just to add a
  testid.
- Prev/next buttons: `slotProps={{ actions: { previousButton: { 'data-testid':
  '...' }, nextButton: { 'data-testid': '...' } } }}` — NOT the deprecated
  `backIconButtonProps`/`nextIconButtonProps` (both explicitly say "This prop
  is an alias for `slotProps.actions.*` ... @deprecated" in the source).

All four are on the `<TablePagination>` element itself — no `ActionsComponent`
override needed for testids specifically (only needed if customizing behavior).

Also relevant for pagination tables generally: for a per-row repeated testid
(e.g. `analytics-users-row`) selected via `.nth(i)`, add a SEPARATE testid on
any specific cell you need to read/assert (e.g. `analytics-users-row-errors`)
rather than a positional child selector like `row.locator("> *").nth(n)` — the
latter is the pattern `artifacts_page.py` uses but it's tracked tech debt, not
a pattern to replicate in new page objects.
