---
name: Artifacts Resolve-duplicates dialog — Skip/Replace/Keep-both testids and copy-naming format
description: The Resolve-duplicates modal (Artifacts upload flow) had testids only for its own dialog/filename/Cancel (ELITEA-1832); Skip/Replace/Keep-both and the message text had none until ELITEA-1828/1829/1831 added them live. Records the confirmed button semantics and the exact "Keep both" rename format, which differs from a common case-text example.
type: feedback
---

## What was added (2026-08-02, ELITEA-1828/1829/1831 cluster)

`EliteaAI/EliteaUI@918b8b22` on `automation/testids`, in
`src/pages/Artifacts/component/DuplicateDialogContent.jsx` and
`DuplicateResolutionDialog.jsx`:

- `artifacts-resolve-duplicates-message-text` — the dialog's label
  `<Typography>`. Text is **singular vs plural** depending on
  `duplicateFilenames.length`: "This file already exists..." for exactly 1,
  "{N} files already exist..." for more than 1. Don't hardcode the singular
  string when a case's duplicate count could be >1.
- `artifacts-resolve-duplicates-skip-button`
- `artifacts-resolve-duplicates-replace-button` (not yet exercised by any
  case as of this writing — only visibility-asserted)
- `artifacts-resolve-duplicates-keep-both-button`

## Confirmed button semantics (live, localhost → DEV backend)

- **Skip**: uploads ONLY the non-duplicate file(s) in the same batch. Exactly
  one `PUT .../artifacts/s3/{bucket}/{non_dup_name}` fires; **zero** PUTs for
  the duplicate. The duplicate's `lastModified`/size are byte-identical
  before/after (confirmed via `ArtifactAPI.get_file_metadata()` — no
  UI-visible timestamp column exists anywhere in this app).
- **Keep both**: uploads the NEW file under a **renamed** key —
  `{baseName} - Copy{extension}` (space, hyphen, space, capitalized "Copy",
  original extension preserved), e.g. `sample.txt` → `sample - Copy.txt`.
  Exactly one PUT fires, for the renamed key; the original `sample.txt` path
  is never re-touched. **This is NOT `sample-copy.txt`** (hyphenated, no
  space) — a shape some TMS case text uses as an illustrative example. If a
  case's Test Data table gives that literal string, treat it as an
  imprecise example (case-text CLARIFICATION, not a defect) unless the case
  explicitly asserts the literal string without a hedge — see
  `EliteaAI/elitea-testing-public#1102`.
- Both Skip and Keep-both show the SAME success toast text: "Your file(s)
  have been successfully uploaded!" (generic app-wide `toast-message`
  testid) — the wording is upload-outcome-generic, not per-button.

## Reuse note

Reuse ELITEA-1832's proven setup/navigation/upload-trigger prefix (same
`artifact_bucket` fixture, `ArtifactAPI.upload_file()`/`get_file_metadata()`,
`upload_files()` → `wait_for_upload_path_dialog()` →
`click_upload_path_upload_button()` → `wait_for_resolve_duplicates_dialog()`)
for any future duplicate-handling case on this dialog — it's confirmed
stable across 4 independent live runs now (1832's 2/2 + this cluster's 2
more).
