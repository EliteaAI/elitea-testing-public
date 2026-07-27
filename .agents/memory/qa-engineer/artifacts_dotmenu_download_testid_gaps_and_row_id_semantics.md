---
name: Artifacts dot-menu Download/Delete testid gaps + row.id semantics
description: ELITEA-1839 findings on the Artifacts file-row DotMenu — the Download/Delete menu items render data-testid=undefined (ArtifactRowActions.jsx menuItems missing `key`), the ZIP-download progress dialog's BaseModal has no data-testid wired, row.id resolves to the base filename only (never the full path), and the single-file download path is architecturally unreachable from the ZIP flow.
type: feedback
---

## What happens (confirmed live, 2026-07-19, both `origin/main` and `automation/testids`)

`ArtifactRowActions.jsx`'s `menuItems` array (feeds the shared `DotMenu`
component for every file row's 3-dot menu) pushes `{label: 'Download', ...}`
and `{label: 'Delete', ...}` with **no `key`**. `DotMenu.jsx` only renders
`data-testid="${testId}-menuitem"` when `testId` (= `item.key`) is truthy —
confirmed via `document.querySelectorAll('[role="menuitem"]')`: both items'
`data-testid` attribute is literally `null` in the live DOM. Fix is one line
each: `key: 'artifacts-file-download'` / `key: 'artifacts-file-delete'` on the
two `items.push({...})` calls — `DotMenu` auto-derives the `-menuitem` suffix,
same mechanism every other `DotMenu` consumer in the app already relies on.

Separately, `ZipDownloadProgressDialog.jsx`'s `<BaseModal>` doesn't pass the
`data-testid` prop `BaseModal` already supports (same prop ELITEA-1832 used to
add `artifacts-upload-path-dialog`/`artifacts-resolve-duplicates-dialog`) — so
there's no compliant handle to assert this dialog's ABSENCE either.

## row.id / dynamic testid semantics

The per-file dot-menu trigger's dynamic testid is `artifact-actions-{row.id}-menu-button`,
and `row.id = item.name` in `ArtifactTable.jsx:167` (`existingRows.map()`) — **the
base filename only, never the full key/path**, confirmed live for a file nested
inside a subfolder (`artifact-actions-sample.txt-menu-button`, not
`artifact-actions-a1/sample.txt-menu-button`). The actual download request uses
`row.key` (the full path) instead — `onDownload` callback,
`ArtifactTable.jsx:329-343`. Don't conflate the two: testid-scoping uses the
short name, the download URL uses the full key.

## ZIP vs immediate-download semantics (useful context for any future bulk/ZIP case)

The dropdown's Download action (`onDownload`) and the toolbar bulk-download
button's single-selection path (`onDownloadFiles`, `ArtifactTable.jsx` ~L399)
BOTH call the same immediate-download codepath and NEVER call `startZipDownload`.
ZIP only triggers when the toolbar's checkbox-selection has **>1 item OR
includes a folder**. So "no ZIP for single file" is a selection-count/type
semantic, not a dropdown-vs-toolbar semantic — don't design a future case
around "toolbar always ZIPs, dropdown never does."

## Why it matters

Any future Artifacts case touching the per-file dot-menu (Delete flow, rename,
move-to, etc. if added later) will hit the same `data-testid=undefined` gap on
whichever menu item it needs — check `item.key` in `ArtifactRowActions.jsx`'s
`menuItems` array before assuming a testid exists just because the trigger
button's testid does.

## What to do about it

- Don't file these as separate GitHub bugs — per `.agents/role-overrides.md`
  § Analyst slot, a missing testid is implementer work specced via the AFS's
  `testid needed:` row, not a defect ticket.
- AFS with the full spec: `test-specs/artifacts/l2_download-flow-single-file-actions-dropdown_ELITEA-1839.md`.
- Also see `artifact_bucket_fixture_delete_silently_fails_404.md` (already filed
  as #636) for the separate, pre-existing bucket-cleanup defect — don't
  re-diagnose it, just cite #636 in any new case's Cleanup section.
