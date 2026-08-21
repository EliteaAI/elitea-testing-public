---
name: Upload-path dialog Cancel button has no testid
description: UploadPathDialog's Cancel is untagged while its Upload sibling is tagged; Escape is only a workaround, not case fidelity
type: reference
aliases: [upload path cancel, artifacts upload modal cancel, UploadPathDialog Cancel]
tags: [area/artifacts, type/handle-gap]
created: 2026-08-21
updated: 2026-08-21
---

## The gap

`../EliteaUI/src/pages/Artifacts/component/UploadPathDialog.jsx` renders two
`Button.BaseBtn`s in its `actions` fragment. The **Upload** one carries
`data-testid="artifacts-upload-path-upload-button"`; the **Cancel** one carries nothing,
and neither does the modal's unlabelled X control. Live enumeration (2026-08-21):
`[('', None), ('Cancel', None), ('Upload', 'artifacts-upload-path-upload-button')]`.

Any case whose step literally says *"Click Cancel"* (ELITEA-1825) needs
`artifacts-upload-path-cancel-button` added — attribute-only, zero functional impact.

## Why Escape is not a substitute

`ArtifactsPage.close_upload_path_dialog()` (added for ELITEA-1824) presses Escape, which
reaches the same `handleCancel` via MUI `BaseModal`'s `onClose`. That is legitimate
**transit** (1824 used it to escape defect #649), but it exercises the key handler, not
the button — so it does not satisfy a case that tests the button.

## Behaviour worth reusing

`handleCancel` = `setFolderPath('') ; onClose()`. So Cancel: fires **zero** network
requests, shows no toast, and **clears the typed Path** — re-opening the dialog shows an
empty editable segment. That last one is a cheap, source-backed way to assert a "discard"
really discarded rather than merely hid the modal.

Related: [[no_playwright_mcp_use_sync_playwright_script]]
