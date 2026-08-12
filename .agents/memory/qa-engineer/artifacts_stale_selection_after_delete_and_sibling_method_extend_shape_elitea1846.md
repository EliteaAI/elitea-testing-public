---
name: Artifacts stale row-selection after delete + sibling-method extend-existing shape (ELITEA-1846)
description: Found a real, reproducible MINOR defect (#677) where the toolbar Delete button keeps a stale rowSelectionModel after a successful multi-file delete, showing a misleading "Delete all files" tooltip and staying enabled with 0 rows actually checked; also documents when extend-existing should be a NEW SIBLING test method rather than an insertion into the covering test's own body (data-precondition conflict, not the default "insert" shape from ELITEA-1871's precedent).
type: feedback
---

## The defect (#677, MINOR, non-destructive)

After checking 2 file-row checkboxes (leaving 2 sibling folders unchecked) and deleting them via the toolbar
"Delete selected files" flow, the app correctly refetches and the per-row/header checkboxes correctly render
as unchecked/non-indeterminate. But the toolbar Delete button's tooltip (`aria-label` on
`[data-testid="artifacts-delete-files-button"]`) incorrectly reads **"Delete all files"** and the underlying
`<button>` stays **not disabled** — even though 0 rows are actually checked.

Root cause (source-confirmed): `ArtifactTable.jsx`'s `rowSelectionModel` is never pruned of the just-deleted
rows' ids after the delete mutation succeeds. The per-row checkbox render logic and the toolbar's own
`disabled`/`title` logic (`ArtifactTableToolbar.jsx` — `disabled={!rowSelectionModel.length}`,
`title={rowSelectionModel.length === totalRows ? 'all files' : 'selected files'}`) read the SAME
`rowSelectionModel`, but the per-row checkboxes filter by `rowSelectionModel.includes(row.id)` against
CURRENT rows (so stale ids correctly render as unchecked), while the toolbar's checks use the raw, unfiltered
`rowSelectionModel.length` — coincidentally equal to the new `totalRows` in this repro (2 stale ids == 2
remaining rows), producing the misleading "all files" tooltip.

**Confirmed non-destructive**: clicking through opens a confirmation modal ("Are you sure to delete the all
files?" — also awkward grammar, same root cause) but firing "Delete" produces **zero new network requests**
and a "No items to delete" toast — `onDeleteArtifacts`'s own `sortedRows.filter(row =>
rowSelectionModel.includes(row.id))` computes an empty `selectedItems` list since none of the stale ids match
a current row, so there IS a defensive empty-check downstream, just not one that clears the STALE ids or
disables the button proactively.

Reproduced 2/2 in independent, freshly-seeded buckets + fresh page navigations (no shared session state) —
passed the pristine-repro gate before filing.

## Building blocks that already existed but were never positively exercised

- `is_select_all_checkbox_indeterminate()` (built for ELITEA-1841) was already called in
  `test_artifacts_download_all_files_select_all_zip.py` — but ONLY to assert `False` (select-all → fully
  checked, not indeterminate). ELITEA-1846 is the first case to assert it returns `True` (a genuine partial
  selection). Don't assume a method having an existing caller means its full behavior space is covered —
  check WHICH branch/value the existing caller actually asserts.
- `artifacts-delete-files-button` — ELITEA-1847's own AFS flagged this as `testid needed:` at analysis time.
  Confirmed via fresh `git fetch` this run that the gap has SINCE BEEN CLOSED on `automation/testids` (still
  not on `main`) — always re-verify testid provenance fresh per case, don't trust a sibling AFS's
  gap-at-the-time claim as still current.

## extend-existing: when the shape is a sibling test METHOD, not an insertion

The project's own established default (from ELITEA-1871's precedent,
`extend_existing_means_insert_into_same_test_not_sibling_method.md`) is: insert new steps into the covering
test's own body when the gap is "more states of the same state machine." That memory note's own reusable
check already carves out the exception: "reserve the sibling-method shape for gaps that are a genuinely
separate scenario sharing only setup — e.g., a different entry point, a different data precondition."

ELITEA-1846 hit that exact exception, and it's worth stating plainly since it's easy to default to "insert"
without checking for a conflict first: ELITEA-1847's covering test (`test_delete_subfolder_via_checkbox`)
**deletes `a1` itself** as its own core assertion, with numeric pagination asserts (`"1 - 3 of 3"`) computed
from that fact. ELITEA-1846's own precondition requires `a1`/`folder-a` to SURVIVE. These two end-states are
mutually exclusive within one continuous bucket/test-run — inserting 1846's steps anywhere in 1847's own body
would break 1847's own later numeric assertions. This is NOT a "small number of missing assertions on the same
walk" (ELITEA-1827/1835's own extend shape) — it's a data-precondition conflict, so the correct
`extend-existing` shape here is a NEW sibling `test()` method in the SAME file/class (same fixtures, same page
object, same imports — only the per-test bucket instance and selection/assertion shape differ), not an
insertion. Check for this kind of conflict (does the gap case's OWN required end-state contradict something
the covering test already asserts later in its own body?) before defaulting to "insert."

See `test-specs/artifacts/lextend_delete-flow-multiple-files-partial-selection_ELITEA-1846.md` for the full
AFS, and issue #677 for the filed defect (with 2 embedded screenshots from independent pristine reproductions).
