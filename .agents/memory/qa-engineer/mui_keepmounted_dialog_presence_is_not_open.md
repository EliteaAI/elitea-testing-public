---
name: keepMounted MUI dialogs — presence is not openness
description: McpAuthModal (and any <Dialog keepMounted>) is always in the DOM; a closed one reads with empty/default field values that mimic a data bug
type: feedback
aliases: [keepMounted, McpAuthModal, dialog always in DOM, role=dialog false positive]
tags: [area/ui, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## The trap

`EliteaUI/src/[fsd]/features/mcp/ui/modal/McpAuthModal.jsx:370` renders
`<Dialog open={open} keepMounted>`. `document.querySelector('[role="dialog"]')`
therefore **always** returns a node, open or not.

Worse, a *closed* instance holds pre-open state: the `Server:` link renders with
`href=""` and empty text, and the scope input shows the raw form scopes without
the backend's `offline_access` prefix. That reads exactly like "the dialog opened
with the wrong data" — during ELITEA-1982 it started the chase that ended in two
retracted issue filings (see [[mcp_browser_can_wedge_into_dead_clicks]]) before `getComputedStyle(root).visibility === 'hidden'` and a
zero-fetch spy showed the dialog had never opened at all.

## The check that works

```js
const d = document.querySelector('[role="dialog"]');
const root = d && d.closest('.MuiDialog-root');   // MuiModal-hidden when closed
const open = !!root && getComputedStyle(root).visibility !== 'hidden';
```

`offsetParent !== null` is **not** sufficient — it returned truthy on a closed
one. In pytest, Playwright's own `to_be_visible()` respects the hidden
visibility, so `expect(dialog).to_be_visible()` is correct and
`to_have_count(1)` is not. Closing assertions must be `not_to_be_visible()`.

## Generalise

Before concluding "the UI shows wrong data in a modal", prove the modal is open —
and prove the action that should open it actually fired (a `window.fetch` spy
installed before the click is the cheapest oracle).

Related: [[credential_form_save_needs_real_keystrokes]]
