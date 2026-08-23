---
name: Artifacts unsupported file types have no preview entry point
description: .xlsx/.zip show no View/Edit icon; the Preview-Not-Available panel is reachable only via ?bucket=&file=
type: project
aliases: [preview not available, unsupported file type, canPreviewFile, PreviewUnavailable]
tags: [area/artifacts, type/product-behaviour]
created: 2026-08-23
updated: 2026-08-23
---

## What

Elitea Artifacts gates file preview on a **filename-extension whitelist**
(`canPreviewFile`, `src/utils/filePreview.js:226` over `PREVIEWABLE_EXTENSIONS`).
`docx` is on it; `xlsx`, `xls`, `zip`, `pdf` are not.

For a non-whitelisted file:
- the row's "View/Edit file" icon is **not rendered at all** (`ArtifactRowActions.jsx`
  gates on `row.canPreview`), hover or no hover;
- `ActionsMenu.jsx`'s "Preview file" item renders `null` (`PREVIEW_TYPES.EMPTY`);
- so there is **no in-app path** to the preview panel.

The `PreviewUnavailable` panel still exists and is reachable through the product's own
preview URL route `/artifacts?bucket=<b>&file=<key>` (the params `Artifacts.jsx` sets on
every preview open and restores on load, without consulting `canPreview`). There it shows
`Preview Not Available` + `Preview is not supported for this file type.` + the supported-
formats sentence + a working Download button, and **Save/Discard are structurally absent**
(`PreviewHeader.jsx` wraps them in `{canPreview && …}`) — unlike images, where they render
disabled.

`ArtifactsPage.open_file_in_editor()` cannot open this branch: it waits on the Save button,
which never renders. Wait on `artifacts-preview-close-button` instead.

## Why it matters

Two TMS cases (ELITEA-1863, ELITEA-1864) are written as if .xlsx had a preview icon and
greyed-out Save/Discard. Filed as case-text clarifications
`EliteaAI/elitea-testing-public#1692` and `#1693`.

Related: [[no_playwright_mcp_use_sync_playwright_script]]
