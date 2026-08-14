---
name: Artifacts select-all checkbox testid gap + full progress-sequence polling technique (ELITEA-1841)
description: GridTableHeader.jsx's header "Select all" checkbox is a shared component with zero testid (same shape as GridTableRow's per-row checkbox gap ELITEA-1840 already fixed); MUI's indeterminate state is a real, distinguishable CSS class (MuiCheckbox-indeterminate), not cosmetic; and a page.evaluate polling loop is how to prove a progress counter/bar "progresses through" a full range rather than spot-checking one frame — plus a harmless pre-unmount "0 of 0" reset to not mistake for a bug.
type: feedback
---

## The gap

`GridTableHeader.jsx` (`src/[fsd]/entities/grid-table/ui/GridTableHeader.jsx:26-32`) renders the table
header's "Select all" checkbox as `<Checkbox.BaseCheckbox checked={isAllSelected}
indeterminate={isIndeterminate} onChange={onSelectAll} .../>` with **no `data-testid`/testid-prop threaded
through at all** — confirmed missing on both `origin/main` and `origin/automation/testids`. This is a
**shared component** with 7 consumers (`SecretsTable`, `TokensTable`, `UsersTable`, `BucketAccessTable`,
`DataTable`, `NotificationTable`, `ArtifactTable`) — the exact same shape as `GridTableRow`'s per-row
checkbox gap, which ELITEA-1840 already fixed via a caller-supplied `checkboxTestId` prop wired only at
`ArtifactTable.jsx`'s row-loop call site. The header checkbox needs the identical treatment: a new
`selectAllCheckboxTestId` prop on `GridTableHeader`, threaded to the `Checkbox.BaseCheckbox`'s
`data-testid`, wired only at `ArtifactTable.jsx:520`'s `<GridTableHeader ...>` call as
`selectAllCheckboxTestId="artifacts-select-all-checkbox"` — never at the other 6 consumers (testid-scope
rule: only elements a test actually touches).

**Lesson for future artifacts-table cases**: whenever a case touches ANY checkbox/selection-state element in
this table family (`GridTableHeader`/`GridTableRow`), expect it to be missing a testid on first contact —
check both files' source directly rather than assuming "surely the header checkbox got the same treatment as
the row checkboxes when 1840 shipped." It didn't; 1840 scoped its fix strictly to what its own case touched
(the per-row checkboxes only), per this project's testid-scope rule.

## The indeterminate state is real and distinguishable

MUI applies a `MuiCheckbox-indeterminate` CSS class to the header checkbox's wrapping
`<span class="MuiCheckbox-root">` when `indeterminate={true}` (partial selection) — confirmed live by
partially deselecting after a select-all click. When fully selected (0→all via one header click, no partial
state ever visited), the span carries `Mui-checked` and does NOT carry `MuiCheckbox-indeterminate`. So "is
the header checkbox non-indeterminate" is a real, testable 3-state signal (unchecked / indeterminate /
fully-checked), not a trivial always-true assertion — read it the same way `is_file_checkbox_checked()`
already does (ELITEA-1840 precedent): a class-attribute read off the (once-testid'd) header checkbox's
own testid-anchored `<span>`.

## Proving a progress counter "progresses through the full range," not just one frame

ELITEA-1840's route-delay technique (`page.route()` on `**/artifact/default/**`, delayed
`route.continue_()`) only needed to catch ONE intermediate frame ("1 of 2 files") because with just 2 files
the case text didn't demand more. ELITEA-1841's case text explicitly enumerates the full range
("1 of 6" → "6 of 6"), so a single-frame spot-check under-proves it. The technique that DOES prove it: after
clicking the download button (with the route delay active), run a `page.evaluate` loop that polls the
counter/progress-bar/current-file trio at a short fixed interval (150ms worked reliably against a 600ms
per-request delay) and collects every frame until the dialog element disappears from the DOM. This produces
an actual observed monotonic sequence (`3 of 6 → 4 of 6 → 5 of 6 → 6 of 6` in this run) instead of an
architectural inference from reading the source's `for`-loop.

**Gotcha to remember**: immediately before the dialog unmounts, the counter/progress-bar briefly reset to
`"0 of 0 files"` / `aria-valuenow="NaN"` for exactly one poll tick — a harmless internal state-reset on
teardown (not visible in real, non-delayed runs; not a defect). Don't assert against the dialog's literal
final frame before closure — assert the collected sequence is non-decreasing and its last non-`"0 of 0"`
value is the expected total. Whoever automates a similar multi-item ZIP/bulk-progress dialog in this app
should expect the same teardown-reset artifact and design the assertion around it from the start, not
discover it as a flaky-test surprise later.

## A tooltip-invariance detail worth remembering

The toolbar "Download files" button's tooltip text is a STATIC `"Download files"` string regardless of
whether the current selection is partial or full — unlike the sibling toolbar delete-button, whose tooltip
DOES vary ("Delete selected files" vs "Delete all files" depending on whether every visible row is selected,
per ELITEA-1847's finding). Don't assume all toolbar-icon tooltips in this table follow the same
selection-completeness-aware pattern — check each one live; they don't.
