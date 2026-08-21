---
name: Artifacts bulk delete — select-all branch and modal dismissal
description: The all-selected delete branch renders "the all files"; dismissal (Cancel or X) keeps the selection checked
type: reference
aliases: [delete all files, select all checkbox artifacts, delete confirmation X, delete all files tooltip]
tags: [area/artifacts, type/handle]
created: 2026-08-22
updated: 2026-08-22
---

## The all-vs-partial branch is one prop, two strings

`ArtifactTableToolbar.jsx` passes `name={rowSelectionModel.length === totalRows ? 'all files' :
'selected files'}` to BOTH the tooltip and the shared `DeleteEntityModal`. So a full selection
gives tooltip `Delete all files` + message `Are you sure to delete the all files?` (ungrammatical —
CLARIFICATION #1640), a partial one gives `Delete selected files` + `… the selected files?` (#659).

The **success toast is NOT branched** — `The selected files have been successfully deleted.` fires
for both. Don't expect an "all files" toast variant.

## Dismissing the modal preserves the selection

`DeleteEntityModal` passes ONE `onClose` to both `BaseModal` (X / backdrop / Escape) and the Cancel
button, and it only resets local modal state. Selection lives in `ArtifactTable`'s
`rowSelectionModel`, untouched — so after Cancel or X every previously checked row is still checked
(and the header is still checked / still indeterminate, matching the selection). Zero requests fire.

## Emptying a bucket does not delete it

Delete-all leaves the bucket in the list, with `No files in this bucket` in BOTH panels
(`artifacts-empty-state` right, `artifacts-bucket-tree-empty-label-{bucket}` left — the latter is
runtime-composed, so a bare grep of EliteaUI `main` never finds it).

Related: [[absence_assertion_needs_a_proven_detector]]
