---
name: MCP create-form Cancel is a two-step gesture (dialog), and re-mounts the type picker
description: Cancel on /mcps/create/mcp opens a confirm dialog; confirming unmounts the form and re-renders the type picker WITHOUT changing the URL — and re-triggers the #656 console error.
type: reference
aliases: [cancel creation, toolkit-form-cancel-button, cancel confirm dialog, mcp create cancel, discard creation]
tags: [area/mcp, area/toolkits, type/ui-behaviour]
created: 2026-08-24
updated: 2026-08-24
---

## The gesture

`CreateToolkitToolTabBar.jsx` renders the create form's Cancel as the shared
`Button.DiscardButton title="Cancel"`. Clicking it cancels nothing — it opens
`Warning / Are you sure you want to cancel creation of this toolkit? / Cancel / Discard`.
The form stays mounted with its values until the modal's **Discard** is clicked.

Testids, all on `origin/main` ✓ (EliteaAI/EliteaUI@bf4a13ad):
`toolkit-form-cancel-button`, `toolkit-form-cancel-confirm-dialog` (MUI Dialog **root**,
`role="presentation"` → `text_content()` concatenates title + message + both button
labels, assert with `in`), `toolkit-form-cancel-confirm-button`.

## Confirming does NOT navigate

`onCancel` → `setWantToCancel(true)` → effect `onClearEditTool()` + `formik.resetForm()`;
at the MCP call site `onClearEditTool` is `() => setEditToolDetail(null)`
(`CreateToolkit.jsx:141`). No `navigate()` exists in the path. So: form handles unmount,
the type picker re-renders (`mcp-type-picker-heading` == `Choose the MCP type`), and the
**URL stays `/mcps/create/mcp`**. Never assert the URL here — clarification #1747.
Zero POST fires; a cancelled creation is server-side inert.

## The console trap

The MCP type picker emits React's `Each child in a list should have a unique "key" prop`
at **error** level on every mount (`CategorySection.jsx:35` via `ToolkitTypeSelector.jsx:36`,
tracked #656). A cancel flow mounts the picker **twice**, so the
`register-the-listener-after-setup` dodge used by `test_mcp_back_navigation.py` does not
work — filter the signature by message instead (plus the standing `socket.io`
CORS/502/503 noise to `dev.elitea.ai`).

Related: [[mcp_detail_discard_modal]] (the *detail* page's analogous but distinct pair).
