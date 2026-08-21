---
name: Artifacts row-dropdown delete uses the SINGULAR deleteArtifact endpoint
description: A file row's dropdown Delete hits /artifacts/artifact/...?filename=, so ArtifactsPage.confirm_delete()'s 'artifacts/artifacts' response matcher hangs — use confirm_delete_single_artifact()
type: feedback
aliases: [deleteArtifact vs deleteArtifacts, artifacts delete endpoint, confirm_delete hangs]
tags: [area/artifacts, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## Three delete paths, three endpoints, three toasts

| Path | Endpoint | Success toast |
|---|---|---|
| Row dot-menu -> Delete (a FILE row) | `DELETE /artifacts/artifact/default/{project}/{bucket}?filename={name}` (`deleteArtifact`, `src/api/artifacts.js:125`) | `The {name} file has been successfully deleted.` |
| Row checkbox + toolbar delete icon, or a FOLDER row's dropdown delete | `DELETE /artifacts/artifacts/default/{project}/{bucket}?fname[]=…` (`deleteArtifacts`) | `The selected files have been successfully deleted.` |
| File-preview editor menu -> Delete | (editor path, `FilePreviewCanvas`) | `File deleted successfully` |

`ArtifactTable.jsx:347 onDeleteArtifact` picks singular vs plural by
`row.type` — a folder row's dropdown delete still expands to the plural call.

## Consequence for the page object

`ArtifactsPage.confirm_delete()` wraps its click in
`expect_response(lambda r: "artifacts/artifacts" in r.url …)` — that substring
does **not** match `artifacts/artifact/`, so reusing it on the row-dropdown
path hangs for the full timeout even though the delete succeeds. ELITEA-1844
added the additive sibling `confirm_delete_single_artifact()`
(`"artifacts/artifact/"` matcher); `confirm_delete` / `confirm_delete_bucket`
were left byte-identical.

Also corrected there: the standing comment claiming the shared
`DeleteEntityModal`'s Cancel button has no testid is **stale** —
`delete-confirm-cancel-button` is on `origin/main` (EliteaAI/EliteaUI@bf4a13ad).
