---
name: Playwright MCP cannot READ the clipboard; the pytest context can
description: A copy-to-clipboard case is still automatable even though an MCP walk fails to read the clipboard — only the read is blocked, not the write
type: feedback
aliases: [clipboard, NotAllowedError, clipboard-read, copy to clipboard, MCP clipboard]
tags: [area/tooling, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## The fact

In a **Playwright-MCP** browser session, `navigator.clipboard.readText()` throws
`NotAllowedError: Failed to execute 'readText' on 'Clipboard': Read permission denied`
(the MCP context grants no clipboard permission, and Chromium then logs
`ClipboardReadWrite permission has been blocked as the user has ignored the permission
prompt several times`).

The **pytest** context does grant it: `automation/conftest.py:304` passes
`permissions=["clipboard-read", "clipboard-write"]` on every browser context, and
`BasePage.get_clipboard_text()` / `BasePage.clear_clipboard()` already exist.

**Only the READ is blocked in MCP — the WRITE still works.** So a live analyst walk can
confirm the whole copy flow (the app's success toast only fires when `copyToClipboard`
resolves) and leave just the readback to the automated run. Verified end-to-end on
ELITEA-2335 (2026-08-27): the MCP walk hit the `NotAllowedError`, the pytest run asserted
`clipboard == plaintext == reveal-GET value != masked reference` and passed first try.

## Consequence

Never park a copy-to-clipboard case as `blocked` because an MCP session cannot read the
clipboard — write the AFS with the readback specced, say in it that the readback is the
one step the live walk could not observe, and verify it in the build half.

Related: [[secrets_toast_testids_and_durations]]
