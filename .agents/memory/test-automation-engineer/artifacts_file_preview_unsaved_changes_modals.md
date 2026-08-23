---
name: Artifacts file-preview editor — two DIFFERENT unsaved-changes modals
description: The header Discard button and the X button raise different dialogs, with different components, texts and testids; the revert lags the modal close.
type: project
aliases: [discard warning modal, file preview discard, unsaved changes dialog, artifacts editor close]
tags: [area/artifacts, type/ui-gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## Two modals, not one

The Artifacts file-preview editor guards unsaved changes with **two distinct
dialogs** — different components, different messages, different testids:

| Trigger | Component | Message | Testids |
|---|---|---|---|
| header **Discard** button | `Button.DiscardButton`'s own `Modal.BaseModal` (shared) | `Are you sure you want to discard changes?` | `artifacts-preview-discard-warning-{dialog,title,icon,close-button,cancel-button,confirm-button}` |
| header **X (close)** button | `FilePreviewCanvas`'s `AlertDialog` (`src/components/AlertDialog.jsx`) | `You are editing now. Do you want to discard current changes and continue?` | generic `alert-dialog-content` / `alert-dialog-confirm-button` |

The header Discard button **never discards directly** — it always raises its
modal first. `ArtifactsPage.close_file_preview()` is unusable on a dirty
editor (it waits for the close button to hide, which never happens while the
dialog is up) — use `click_file_preview_close_with_unsaved_changes()`.

## Two timing facts that cost a rerun each

1. **`useCodeMirror` debounces `notifyChange` by 30 ms**, so the parent's
   `hasChanges` lags the typed DOM text. Clicking X inside that window closes
   the editor with **no** warning at all. Always wait on
   `is_file_preview_save_enabled()` / `is_file_preview_discard_enabled()`
   after typing before asserting anything dirty-state dependent.
2. **The revert lags the modal close.** Confirming Discard hides the modal
   immediately, but the editor text is restored one React state round-trip
   later. A one-shot `get_file_preview_content_text()` there still returns the
   EDITED text. Use a web-first `expect(...).not_to_contain_text(...)` first,
   then read for byte-equality.

## Shared-component testid plumbing

`DiscardButton` is under `src/[fsd]/shared/ui/button/` so it carries no
feature-scoped testid — it takes caller-supplied testId props. It already
forwarded `dataTestId` / `modalDataTestId` / `confirmButtonDataTestId`
(legacy `data`-prefixed names); this run added `cancelButtonTestId`,
`closeButtonTestId`, `modalTitleTestId`, `modalTitleIconTestId` using the
compliant `<part>TestId` naming. `Modal.BaseModal` already accepted all of
them — pure attribute plumbing, no DOM/hook changes.

Related: [[project_briefing]]
