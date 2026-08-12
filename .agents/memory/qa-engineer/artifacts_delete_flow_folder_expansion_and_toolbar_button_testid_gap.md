---
name: Artifacts delete flow — folder-to-keys expansion + toolbar delete button has zero testid
description: ELITEA-1847 — checking a folder row's checkbox and confirming bulk delete works via expandFoldersToAllItems/getItemsUnderFolder (key-prefix expansion, no server-side folder object), fires exactly one DELETE with the folder's full underlying file-key list as fname[] params. The toolbar delete icon (DeleteEntityButton) has NO data-testid at all on either branch — genuine gap. MUI Tooltip's dynamic aria-label lands on the wrapping Box, not the IconButton — put a future testid there so one locator serves both tooltip-text read and click.
type: feedback
---

## Context

ELITEA-1847 (delete a subfolder via checkbox, verify folder + contents removed,
siblings untouched) was the FIRST case in this repo to exercise ANY artifacts
delete flow — prior automation only ever checked the per-file dot-menu
"Delete" item's *visibility*, never clicked it (`test_artifacts_download_single_file_dropdown.py`,
ELITEA-1839).

## Finding 1 — folder checkbox delete expands to underlying file keys, not a "folder" key

`ArtifactTable.jsx`'s `onDeleteArtifacts()` → `expandFoldersToAllItems(selectedItems,
bucketContents)` → `getItemsUnderFolder(contents, folderKey)`
(`getItemsAtCurrentLevel.js:81-102`): for a selected row where `item.type ===
FOLDER`, it filters `bucketContents` (the bucket's FULL flat key listing, not
just the current folder-level view) for every key that `startsWith(folderKey)`
and `!== folderKey`, and passes THAT list as `fname[]` to a single
`DELETE /artifacts/artifacts/default/{project}/{bucket}?fname[]=...&fname[]=...`
call. There is no server-side "folder" object in this S3-key-prefix storage —
once no key starts with `{folder}/` any more, the folder simply stops
appearing in any listing/tree render. Confirmed live: selecting a folder with
2 files inside fired exactly one DELETE with both files' full keys
(`fname[]=a1%2Ffile1.txt&fname[]=a1%2Ffile2.txt`), not a bare `a1/` entry.

**Reusable for future cases**: a "delete N files + M folders in one bulk
action" case would still fire exactly ONE DELETE (multi-select expands ALL
selected folders + keeps selected file keys as-is, concatenated) — chunked
only if the combined URL would exceed `DELETE_ARTIFACTS_MAX_PATH_LENGTH`
(`api/artifacts.js:135-167`), executed sequentially, stopping on first error.

## Finding 2 — toolbar delete-icon button has ZERO testid (confirmed absent on both branches)

Unlike its toolbar siblings (`artifacts-upload-files-button`,
`artifacts-download-files-button`, both already testid'd), the delete icon
(`ArtifactTableToolbar.jsx`'s `<DeleteEntityButton ... />` →
`DeleteEntityButton.jsx`'s `<IconButton aria-label="delete entity">`) has
**no `data-testid` prop anywhere** — confirmed via live DOM query
(`getAttribute('data-testid') === null`) AND via `git grep` against fresh
`origin/main` + `origin/automation/testids` (zero hits either branch).
`DeleteEntityButton` is a shared component — the fix is a new caller-supplied
prop (e.g. `testId`), wired only at the artifacts call site, per this
project's shared-component testid ruling.

**Placement matters**: MUI's `Tooltip` clones its dynamic `title` prop
(`"Delete selected files"` / `"Delete all files"`, computed from
`rowSelectionModel.length === totalRows`) onto the WRAPPING
`<Box component="span">` as a static `aria-label` attribute
(`data-mui-internal-clone-element="true"`), NOT onto the inner `IconButton`
(which carries its own fixed, non-dynamic `aria-label="delete entity"`).
Recommended the future testid go on that wrapping `Box`, not the button —
lets one `LocatorDescriptor` serve both the tooltip-text read
(`.get_attribute("aria-label")`) and the click target (`.locator("button")`
scoped inside it), matching this page object's pre-existing (legacy,
pre-testid-policy) `create_bucket_button`/`download_files_button`
wrapper-then-scoped-button shape.

## Finding 3 — confirm dialog's message text is readable via a stable `id`, no testid needed

`DeleteEntityModal.jsx`'s message `<Typography id="alert-dialog-description">`
uses a hand-authored HTML `id` (not a CSS class) — reading
`dialog.querySelector('#alert-dialog-description').textContent` scoped inside
the already-testid'd `delete-confirm-dialog` root is an acceptable "read via
an already-resolved testid element" technique, same shape as reading a
`Mui-checked` class or an `aria-valuenow` attribute elsewhere in this
codebase. Did not flag a `testid needed:` for the message text itself.

## Two wording CLARIFICATIONs (not defects, reverse-masking guard applied)

- Confirm-dialog message is `"Are you sure to delete the selected files?"`
  (live) vs the TMS case's `"Are you sure to delete selected files?"` (no
  "the") — filed [#659](https://github.com/EliteaAI/elitea-testing-public/issues/659).
- Success toast is `"The selected files have been successfully deleted."`
  (live, from `ArtifactTable.jsx`'s `toastSuccess()` call) vs the case's own
  Test Data field `"The artifacts have been deleted successfully"` — filed
  [#660](https://github.com/EliteaAI/elitea-testing-public/issues/660).
  Captured via the established pre-click `MutationObserver` technique
  (ELITEA-1824/1826 precedent) since the toast is short-lived.

## Generalizable takeaway

Before assuming a bulk-action toolbar icon is testid'd just because its
siblings (upload/download) are — check it directly via DOM query
(`getAttribute('data-testid')`), don't infer from the row/pattern. And for
any MUI `Tooltip`-wrapped icon button in this codebase, the DYNAMIC tooltip
text lives on the wrapper span's cloned `aria-label`, not necessarily on the
button's own (possibly fixed/generic) `aria-label`.
